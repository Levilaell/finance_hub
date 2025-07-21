"""
Check production database directly via Django shell command
"""
import requests
import sys
import base64

def check_production_db(email, password):
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
    company_id = tokens.get('user', {}).get('company', {}).get('id')
    
    print(f"✅ Login successful - Company ID: {company_id}")
    
    # Direct query approach
    print("\n2. Checking via debug endpoint...")
    
    # Create a simple debug script
    debug_script = f"""
from apps.banking.models import BankAccount
from apps.companies.models import Company

company = Company.objects.get(id={company_id})
accounts = BankAccount.objects.filter(company=company)

for acc in accounts:
    print(f"ID: {{acc.id}}")
    print(f"  External ID: {{acc.external_id}}")
    print(f"  Pluggy Item ID: {{acc.pluggy_item_id}}")
    print(f"  Bank: {{acc.bank_provider.name}}")
    print(f"  Created: {{acc.created_at}}")
    print()
"""
    
    # Save script and note for manual execution
    with open('check_production_accounts.txt', 'w') as f:
        f.write("Execute this in production Django shell:\n\n")
        f.write(debug_script)
    
    print("Script saved to check_production_accounts.txt")
    print("\nTo check the database directly, you need to:")
    print("1. SSH into your Railway instance")
    print("2. Run: railway run python manage.py shell")
    print("3. Execute the script in check_production_accounts.txt")
    
    # Alternative: Check if there's a debug endpoint
    print("\n3. Checking transaction details to find external_id...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get account details with transactions
    trans_response = requests.get(
        f"{base_url}/api/banking/accounts/8/transactions/?limit=1",
        headers=headers
    )
    
    if trans_response.status_code == 200:
        print("✅ Can access account transactions")
        trans_data = trans_response.json()
        
        # The external_id might be in the transaction's bank_account field
        if isinstance(trans_data, dict) and 'results' in trans_data and trans_data['results']:
            first_trans = trans_data['results'][0]
            if 'bank_account' in first_trans:
                print(f"Bank account from transaction: {first_trans['bank_account']}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python check_production_db.py <email> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    check_production_db(email, password)