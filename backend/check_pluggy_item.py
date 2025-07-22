import os
import sys
import django
import asyncio
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.banking.pluggy_client import PluggyClient
from apps.banking.models import BankAccount
from apps.companies.models import Company

async def check_item():
    # Get account
    company = Company.objects.filter(owner__email='levilaelsilvaa@gmail.com').first()
    if not company:
        print("❌ Company not found")
        return
        
    account = BankAccount.objects.filter(
        company=company,
        is_active=True,
        external_id__isnull=False
    ).first()
    
    if not account:
        print("❌ Account not found")
        return
    
    print(f"✅ Account found:")
    print(f"   - ID: {account.id}")
    print(f"   - External ID: {account.external_id}")
    print(f"   - Item ID: {account.pluggy_item_id}")
    
    if not account.pluggy_item_id:
        print("❌ No Pluggy item ID")
        return
    
    async with PluggyClient() as client:
        # Check item status
        print(f"\n📡 Checking Pluggy item...")
        try:
            item = await client.get_item(account.pluggy_item_id)
            print(f"\n📋 Item details:")
            print(f"   - ID: {item.get('id')}")
            print(f"   - Status: {item.get('status')}")
            print(f"   - Created: {item.get('createdAt')}")
            print(f"   - Updated: {item.get('updatedAt')}")
            print(f"   - Last update request: {item.get('lastUpdateRequest')}")
            print(f"   - Error: {item.get('error')}")
            
            # Check executionStatus
            exec_status = item.get('executionStatus')
            if exec_status:
                print(f"\n🔄 Execution status:")
                print(f"   - {exec_status}")
            
            # Check if needs update
            status = item.get('status')
            if status != 'ACTIVE':
                print(f"\n⚠️ Item is not ACTIVE (status: {status})")
                print("   This means automatic webhooks won't fire")
                print("   Manual sync is required")
            
            # Try to trigger update
            if status in ['UPDATED', 'LOGIN_ERROR']:
                print(f"\n🔄 Triggering item update...")
                try:
                    update_response = await client.update_item(account.pluggy_item_id)
                    print(f"✅ Update triggered successfully")
                    print(f"   Response: {update_response}")
                except Exception as e:
                    print(f"❌ Failed to trigger update: {e}")
                    
        except Exception as e:
            print(f"❌ Error checking item: {e}")
            
        # Check account directly
        print(f"\n📊 Checking account directly...")
        try:
            acc_data = await client.get_account(account.external_id)
            print(f"\n💳 Account details:")
            print(f"   - Name: {acc_data.get('name')}")
            print(f"   - Type: {acc_data.get('type')}")
            print(f"   - Balance: R$ {acc_data.get('balance')}")
            print(f"   - Item ID: {acc_data.get('itemId')}")
            
        except Exception as e:
            print(f"❌ Error checking account: {e}")

if __name__ == "__main__":
    print("🔍 Checking Pluggy Item Status")
    print("=" * 60)
    asyncio.run(check_item())