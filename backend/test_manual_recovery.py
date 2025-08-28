#!/usr/bin/env python
"""
Test manual recovery for existing Inter bank item
"""
import os
import sys
import django

# Django setup
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from apps.banking.tasks import retry_account_fetch
from apps.banking.models import PluggyItem

def main():
    print("🔧 MANUAL RECOVERY TEST")
    print("=" * 60)
    
    # Get the Inter item that has 0 accounts
    inter_item_id = "f1f40504-32c4-44c2-9181-5d38cc2cfc8d"
    
    try:
        item = PluggyItem.objects.get(pluggy_item_id=inter_item_id)
        print(f"✅ Found Inter item: {item.id}")
        print(f"   • Status: {item.status}/{item.execution_status}")
        print(f"   • Current accounts: {item.accounts.count()}")
        print(f"   • Connector: {item.connector.name}")
        print(f"   • Is Open Finance: {item.connector.is_open_finance}")
        
        print(f"\n🔄 Running manual retry task...")
        
        # Run the retry task synchronously for testing
        result = retry_account_fetch(str(item.id))
        
        print(f"✅ Retry task result: {result}")
        
        # Check if accounts were created
        item.refresh_from_db()
        final_count = item.accounts.count()
        print(f"🏦 Final account count: {final_count}")
        
        if final_count > 0:
            print("✅ SUCCESS: Accounts were created!")
            for account in item.accounts.all():
                print(f"   • {account.display_name} ({account.type}) - Active: {account.is_active}")
        else:
            print("⚠️ Still no accounts - may need more time or different approach")
            
    except PluggyItem.DoesNotExist:
        print(f"❌ PluggyItem not found for pluggy_item_id: {inter_item_id}")
    except Exception as e:
        print(f"❌ Error during recovery: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()