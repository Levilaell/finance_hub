#!/usr/bin/env python
"""
Test script to verify Pluggy sync fixes
"""
import os
import sys
import django
import asyncio
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from apps.banking.models import BankAccount
from apps.banking.pluggy_sync_service import PluggyTransactionSyncService
from apps.banking.pluggy_client import PluggyClient


async def test_sync_fixes():
    """Test the sync fixes"""
    print("🧪 Testing Pluggy sync fixes...")
    print("=" * 50)
    
    # Get first active account with Pluggy item
    account = BankAccount.objects.filter(
        pluggy_item_id__isnull=False,
        is_active=True
    ).first()
    
    if not account:
        print("❌ No active account with Pluggy item found")
        return
    
    print(f"\n📊 Testing with account:")
    print(f"   ID: {account.id}")
    print(f"   Bank: {account.bank_provider.name}")
    print(f"   External ID: {account.external_id}")
    print(f"   Item ID: {account.pluggy_item_id}")
    print(f"   Sync Status: {account.sync_status}")
    print(f"   Sync Error: {account.sync_error_message}")
    
    # Check item status
    print(f"\n🔍 Checking item status...")
    try:
        async with PluggyClient() as client:
            item = await client.get_item(account.pluggy_item_id)
            print(f"   Item Status: {item.get('status')}")
            print(f"   Last Updated: {item.get('updatedAt')}")
            
            if item.get('status') == 'WAITING_USER_ACTION':
                print("   ⚠️  Item requires user action!")
                print("   This is expected - the sync will handle this properly now")
    except Exception as e:
        print(f"   ❌ Error checking item: {e}")
    
    # Test sync
    print(f"\n🔄 Testing sync...")
    sync_service = PluggyTransactionSyncService()
    
    try:
        result = await sync_service.sync_account_transactions(account)
        print(f"\n✅ Sync completed:")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message', '')}")
        print(f"   Transactions: {result.get('transactions', 0)}")
        
        # Check updated account status
        account.refresh_from_db()
        print(f"\n📊 Updated account status:")
        print(f"   Sync Status: {account.sync_status}")
        print(f"   Sync Error: {account.sync_error_message}")
        print(f"   Last Sync: {account.last_sync_at}")
        
    except Exception as e:
        print(f"\n❌ Sync error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_sync_fixes())