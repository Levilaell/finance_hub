"""
Debug production account details
"""
import requests
import sys
import json

def debug_production_account(email, password):
    base_url = "https://finance-backend-production-29df.up.railway.app"
    
    # Login
    print("1. Logging in...")
    login_response = requests.post(
        f"{base_url}/api/auth/login/",
        json={"email": email, "password": password}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    tokens = login_response.json()
    access_token = tokens.get('tokens', {}).get('access')
    print("✅ Login successful")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get detailed account info
    print("\n2. Getting detailed account info...")
    
    # Try different endpoints
    endpoints = [
        "/api/banking/accounts/",
        "/api/banking/accounts/?expand=bank_provider",
        "/api/banking/accounts/8/"
    ]
    
    for endpoint in endpoints:
        print(f"\nTrying endpoint: {endpoint}")
        response = requests.get(f"{base_url}{endpoint}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Status: {response.status_code}")
    
    # Check transactions
    print("\n3. Checking recent transactions...")
    trans_response = requests.get(
        f"{base_url}/api/banking/transactions/?limit=5",
        headers=headers
    )
    
    if trans_response.status_code == 200:
        trans_data = trans_response.json()
        
        if isinstance(trans_data, dict) and 'results' in trans_data:
            transactions = trans_data['results']
        else:
            transactions = trans_data if isinstance(trans_data, list) else []
        
        print(f"\nFound {len(transactions)} recent transactions")
        for trans in transactions[:5]:
            if isinstance(trans, dict):
                print(f"- {trans.get('transaction_date')}: {trans.get('description', 'N/A')[:50]} (R$ {trans.get('amount')})")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python debug_production_account.py <email> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    debug_production_account(email, password)