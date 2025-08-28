#!/usr/bin/env python
"""
Test Pluggy API directly to understand the account fetching issue
"""
import os
import sys
import django

# Django setup
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from apps.banking.integrations.pluggy.client import PluggyClient

def test_item_and_accounts(item_id, description):
    """Test a specific item ID"""
    print(f"\n🔍 TESTING {description}")
    print(f"Item ID: {item_id}")
    print("-" * 60)
    
    try:
        with PluggyClient() as client:
            # Test item fetch
            print("1. Fetching item details...")
            try:
                item_data = client.get_item(item_id)
                print(f"   ✅ Item Status: {item_data.get('status')}")
                print(f"   ✅ Execution Status: {item_data.get('executionStatus')}")
                print(f"   ✅ Created: {item_data.get('createdAt')}")
                print(f"   ✅ Updated: {item_data.get('updatedAt')}")
                
                error = item_data.get('error')
                if error:
                    print(f"   ⚠️ Error: {error.get('code')} - {error.get('message')}")
                
            except Exception as e:
                print(f"   ❌ Failed to fetch item: {e}")
                return
            
            # Test accounts fetch
            print("\n2. Fetching accounts...")
            try:
                accounts_data = client.get_accounts(item_id)
                print(f"   ✅ Found {len(accounts_data)} account(s)")
                
                for i, account in enumerate(accounts_data, 1):
                    print(f"   📦 Account {i}:")
                    print(f"      • ID: {account.get('id')}")
                    print(f"      • Name: {account.get('name', 'No name')}")
                    print(f"      • Type: {account.get('type')}")
                    print(f"      • Subtype: {account.get('subtype', 'None')}")
                    print(f"      • Balance: {account.get('currencyCode', 'BRL')} {account.get('balance', 0)}")
                    print(f"      • Number: {account.get('number', 'No number')}")
                    print()
                
                if len(accounts_data) == 0:
                    print("   ❌ NO ACCOUNTS RETURNED - This explains the issue!")
                    
                    # Try to get more details about why no accounts
                    print("\n3. Checking for detailed account info...")
                    try:
                        # Sometimes accounts are in different endpoints or have different statuses
                        print(f"      Item status allows accounts: {item_data.get('status') in ['UPDATED', 'LOGIN_SUCCEEDED', 'PARTIAL_SUCCESS']}")
                        
                        # Check if this is an Open Finance item that might need more time
                        connector_id = item_data.get('connector', {}).get('id')
                        if connector_id:
                            connector_data = client.get_connector(connector_id)
                            print(f"      Connector type: {connector_data.get('type')}")
                            print(f"      Is Open Finance: {connector_data.get('isOpenFinance')}")
                            print(f"      Products: {connector_data.get('products', [])}")
                            
                    except Exception as detail_error:
                        print(f"      Error getting details: {detail_error}")
                
            except Exception as e:
                print(f"   ❌ Failed to fetch accounts: {e}")
                print(f"   ❌ Error type: {type(e).__name__}")
                print(f"   ❌ This is likely why BankAccounts aren't created!")
    
    except Exception as e:
        print(f"❌ Client connection failed: {e}")

def main():
    print("🔍 PLUGGY API DIRECT TESTING")
    print("=" * 80)
    
    # Test the existing Inter item that has 0 accounts
    inter_item_id = "f1f40504-32c4-44c2-9181-5d38cc2cfc8d"
    test_item_and_accounts(inter_item_id, "EXISTING INTER ITEM (0 accounts in DB)")
    
    # Test the target item that was never saved
    target_item_id = "3750b128-a12f-4371-8122-7162f8ff490d"
    test_item_and_accounts(target_item_id, "TARGET ITEM (never saved to DB)")
    
    # Test a working item for comparison
    working_item_id = "8a4fed93-307f-4e5c-851e-85026aa6ac25"  # Nubank with 1 account
    test_item_and_accounts(working_item_id, "WORKING NUBANK ITEM (1 account in DB)")
    
    print("\n" + "=" * 80)
    print("✅ API TESTING COMPLETE")

if __name__ == "__main__":
    main()