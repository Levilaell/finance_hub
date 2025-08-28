#!/usr/bin/env python
"""
Check all PluggyItems in the database
"""
import os
import sys
import django

# Django setup
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from apps.banking.models import PluggyItem, BankAccount, ItemWebhook
from django.utils import timezone

def main():
    print("🔍 ALL PLUGGY ITEMS IN DATABASE:")
    print("=" * 80)
    
    # Check all PluggyItems
    items = PluggyItem.objects.all().order_by('-created_at')
    
    if items.exists():
        print(f"✅ Found {items.count()} PluggyItem(s):")
        print()
        
        for item in items:
            print(f"📦 Item: {item.pluggy_item_id}")
            print(f"   • Internal ID: {item.id}")
            print(f"   • Status: {item.status}")
            print(f"   • Execution Status: {item.execution_status}")
            print(f"   • Company: {item.company.name}")
            print(f"   • Connector: {item.connector.name}")
            print(f"   • Created: {item.created_at}")
            print(f"   • Updated: {item.pluggy_updated_at}")
            
            # Check accounts for this item
            accounts = BankAccount.objects.filter(item=item)
            print(f"   • Bank Accounts: {accounts.count()}")
            for account in accounts:
                print(f"     - {account.display_name} ({account.type}) - Active: {account.is_active}")
            
            # Check webhooks
            webhooks = ItemWebhook.objects.filter(item=item).count()
            print(f"   • Webhooks: {webhooks}")
            print()
    else:
        print("❌ NO PLUGGY ITEMS found in database")
    
    # Check orphaned webhooks (webhooks without items)
    print("\n🔍 CHECKING FOR ORPHANED WEBHOOKS:")
    print("-" * 50)
    
    all_webhooks = ItemWebhook.objects.all().order_by('-created_at')
    print(f"Total webhooks in database: {all_webhooks.count()}")
    
    if all_webhooks.count() > 0:
        print("\nRecent webhook events:")
        for webhook in all_webhooks[:10]:  # Show last 10
            print(f"   • {webhook.event_type} - {webhook.created_at} - Item: {webhook.item.pluggy_item_id if webhook.item else 'None'}")
    
    # Check for any webhooks mentioning our target item_id in payload
    target_item_id = "3750b128-a12f-4371-8122-7162f8ff490d"
    print(f"\n🔍 SEARCHING FOR WEBHOOKS WITH ITEM_ID: {target_item_id}")
    print("-" * 50)
    
    # This is tricky - we need to search in JSON payload
    # Let's check all webhooks and examine their payloads
    webhooks_with_target = []
    
    for webhook in all_webhooks:
        payload = webhook.payload
        if isinstance(payload, dict):
            # Check various places item_id might be stored
            item_id = None
            
            # Check direct itemId
            if payload.get('itemId') == target_item_id:
                item_id = target_item_id
            
            # Check data.item.id
            elif payload.get('data', {}).get('item', {}).get('id') == target_item_id:
                item_id = target_item_id
            
            # Check if any string in payload contains our item_id
            elif target_item_id in str(payload):
                item_id = target_item_id
            
            if item_id:
                webhooks_with_target.append(webhook)
                print(f"   ✅ Found webhook: {webhook.event_type} - {webhook.created_at}")
                print(f"      Event ID: {webhook.event_id}")
                print(f"      Processed: {webhook.processed}")
                if webhook.error:
                    print(f"      Error: {webhook.error}")
    
    if not webhooks_with_target:
        print(f"   ❌ No webhooks found containing item_id: {target_item_id}")
    
    print("\n" + "=" * 80)
    print("✅ CHECK COMPLETE")

if __name__ == "__main__":
    main()