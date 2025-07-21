"""
Test production sync endpoint directly
"""
import requests
import sys

def test_production_sync(email, password, account_id=None):
    base_url = "https://finance-backend-production-29df.up.railway.app"
    
    # Login
    print("1. Logging in...")
    login_response = requests.post(
        f"{base_url}/api/auth/login/",
        json={"email": email, "password": password}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    tokens = login_response.json()
    print(f"Response: {tokens}")
    access_token = tokens.get('tokens', {}).get('access') or tokens.get('access') or tokens.get('token')
    
    if not access_token:
        print("❌ No access token received")
        print(f"Full response: {tokens}")
        return
    
    print("✅ Login successful")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get accounts
    print("\n2. Getting accounts...")
    accounts_response = requests.get(
        f"{base_url}/api/banking/accounts/",
        headers=headers
    )
    
    if accounts_response.status_code != 200:
        print(f"❌ Failed to get accounts: {accounts_response.status_code}")
        return
    
    accounts_data = accounts_response.json()
    # Handle paginated response
    if isinstance(accounts_data, dict) and 'results' in accounts_data:
        accounts = accounts_data['results']
    elif isinstance(accounts_data, list):
        accounts = accounts_data
    else:
        accounts = []
    
    print(f"✅ Found {len(accounts)} accounts")
    
    # Show accounts
    for acc in accounts:
        if isinstance(acc, str):
            print(f"Unexpected string: {acc}")
            continue
        print(f"\nAccount ID: {acc.get('id')}")
        print(f"  Bank: {acc.get('bank_name', 'N/A')}")
        print(f"  Balance: R$ {acc.get('current_balance', 0)}")
        print(f"  External ID: {acc.get('external_id', 'None')}")
        print(f"  Last sync: {acc.get('last_sync_at', 'Never')}")
    
    # Sync specific account if provided
    if account_id:
        print(f"\n3. Syncing account {account_id}...")
        sync_response = requests.post(
            f"{base_url}/api/banking/pluggy/accounts/{account_id}/sync/",
            headers=headers
        )
        
        print(f"Response status: {sync_response.status_code}")
        print(f"Response: {sync_response.text}")
    
    # Check for Inter account
    inter_accounts = [acc for acc in accounts if 'inter' in acc.get('bank_name', '').lower()]
    if inter_accounts:
        inter_acc = inter_accounts[0]
        print(f"\n4. Inter account found: ID {inter_acc['id']}")
        print(f"   External ID: {inter_acc.get('external_id')}")
        
        if not account_id:
            print(f"\n   To sync this account, run:")
            print(f"   python test_production_sync.py {email} <password> {inter_acc['id']}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_production_sync.py <email> <password> [account_id]")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    account_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    test_production_sync(email, password, account_id)