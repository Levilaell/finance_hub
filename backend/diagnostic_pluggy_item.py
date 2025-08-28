#!/usr/bin/env python
"""
Diagnostic script for Pluggy bank connection issue
Analyzes the specific item_id: 3750b128-a12f-4371-8122-7162f8ff490d
"""
import os
import sys
import django

# Django setup
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from apps.banking.models import PluggyItem, BankAccount, ItemWebhook
from apps.banking.integrations.pluggy.client import PluggyClient
from django.db.models import Q

def main():
    target_item_id = "3750b128-a12f-4371-8122-7162f8ff490d"
    
    print(f"🔍 DIAGNOSTIC REPORT for Pluggy Item ID: {target_item_id}")
    print("=" * 80)
    
    # 1. Check if PluggyItem exists in database
    print("\n1. CHECKING PLUGGY ITEM IN DATABASE:")
    print("-" * 50)
    
    try:
        pluggy_item = PluggyItem.objects.get(pluggy_item_id=target_item_id)
        print(f"✅ PluggyItem found!")
        print(f"   • Internal ID: {pluggy_item.id}")
        print(f"   • Status: {pluggy_item.status}")
        print(f"   • Execution Status: {pluggy_item.execution_status}")
        print(f"   • Company: {pluggy_item.company.name} (ID: {pluggy_item.company.id})")
        print(f"   • Connector: {pluggy_item.connector.name} (ID: {pluggy_item.connector.pluggy_id})")
        print(f"   • Created: {pluggy_item.created_at}")
        print(f"   • Last Updated: {pluggy_item.pluggy_updated_at}")
        print(f"   • Error Code: {pluggy_item.error_code}")
        print(f"   • Error Message: {pluggy_item.error_message}")
        
    except PluggyItem.DoesNotExist:
        print(f"❌ PluggyItem NOT FOUND for item_id: {target_item_id}")
        
        # Check if there are any similar item IDs
        similar_items = PluggyItem.objects.filter(
            pluggy_item_id__icontains=target_item_id[-8:]  # Last 8 chars
        )
        if similar_items.exists():
            print("🔍 Found similar item IDs:")
            for item in similar_items:
                print(f"   • {item.pluggy_item_id} - {item.connector.name} - {item.status}")
        
        return
    
    # 2. Check BankAccounts for this item
    print("\n2. CHECKING BANK ACCOUNTS:")
    print("-" * 50)
    
    bank_accounts = BankAccount.objects.filter(item=pluggy_item)
    
    if bank_accounts.exists():
        print(f"✅ Found {bank_accounts.count()} bank account(s):")
        for account in bank_accounts:
            print(f"   • Account ID: {account.id}")
            print(f"   • Pluggy Account ID: {account.pluggy_account_id}")
            print(f"   • Name: {account.name or 'No name'}")
            print(f"   • Type: {account.type}")
            print(f"   • Balance: {account.currency_code} {account.balance}")
            print(f"   • Active: {account.is_active}")
            print(f"   • Created: {account.created_at}")
            print()
    else:
        print("❌ NO BANK ACCOUNTS found for this PluggyItem")
        print("   This explains why cards don't appear in /accounts!")
    
    # 3. Check webhook events for this item
    print("\n3. CHECKING WEBHOOK EVENTS:")
    print("-" * 50)
    
    webhooks = ItemWebhook.objects.filter(item=pluggy_item).order_by('-created_at')
    
    if webhooks.exists():
        print(f"✅ Found {webhooks.count()} webhook event(s):")
        for webhook in webhooks:
            print(f"   • Event: {webhook.event_type}")
            print(f"   • Event ID: {webhook.event_id}")
            print(f"   • Processed: {webhook.processed}")
            print(f"   • Created: {webhook.created_at}")
            print(f"   • Triggered by: {webhook.triggered_by}")
            if webhook.error:
                print(f"   • Error: {webhook.error}")
            print()
    else:
        print("⚠️ NO WEBHOOK EVENTS found for this item")
    
    # 4. Try to fetch current status from Pluggy API
    print("\n4. FETCHING CURRENT STATUS FROM PLUGGY API:")
    print("-" * 50)
    
    try:
        with PluggyClient() as client:
            # Get item details
            print("🔄 Fetching item details...")
            item_data = client.get_item(target_item_id)
            
            print(f"✅ Current Pluggy API Status:")
            print(f"   • Status: {item_data.get('status', 'Unknown')}")
            print(f"   • Execution Status: {item_data.get('executionStatus', 'Unknown')}")
            print(f"   • Created At: {item_data.get('createdAt', 'Unknown')}")
            print(f"   • Updated At: {item_data.get('updatedAt', 'Unknown')}")
            
            error_data = item_data.get('error')
            if error_data:
                print(f"   • Error Code: {error_data.get('code', 'Unknown')}")
                print(f"   • Error Message: {error_data.get('message', 'Unknown')}")
            else:
                print(f"   • No errors reported")
            
            # Get accounts from API
            print("\n🔄 Fetching accounts from API...")
            try:
                accounts_data = client.get_accounts(target_item_id)
                
                if accounts_data:
                    print(f"✅ Found {len(accounts_data)} account(s) in Pluggy API:")
                    for acc in accounts_data:
                        print(f"   • Account ID: {acc.get('id')}")
                        print(f"   • Name: {acc.get('name', 'No name')}")
                        print(f"   • Type: {acc.get('type')}")
                        print(f"   • Balance: {acc.get('currencyCode', 'BRL')} {acc.get('balance', 0)}")
                        print(f"   • Number: {acc.get('number', 'No number')}")
                        print()
                else:
                    print("❌ NO ACCOUNTS found in Pluggy API")
                    
            except Exception as e:
                print(f"❌ Error fetching accounts from API: {e}")
            
    except Exception as e:
        print(f"❌ Error fetching from Pluggy API: {e}")
    
    # 5. Analyze the problem
    print("\n5. PROBLEM ANALYSIS:")
    print("-" * 50)
    
    # Check if callback was called but failed to create accounts
    if bank_accounts.count() == 0:
        print("🔴 ROOT CAUSE IDENTIFIED:")
        print("   • PluggyItem exists in database")
        print("   • But NO BankAccounts were created")
        print("   • This indicates callback was partially successful")
        print("   • But account creation step failed")
        
        print("\n🔧 LIKELY CAUSES:")
        print("   1. Callback view error after item creation")
        print("   2. API accounts fetch failed during callback")
        print("   3. BankAccount.objects.update_or_create() failed")
        print("   4. Database transaction rolled back")
        print("   5. Item status prevents account creation")
        
        print(f"\n📋 CURRENT ITEM STATUS: {pluggy_item.status}")
        if pluggy_item.status not in ['UPDATED', 'CREATED', 'LOGIN_SUCCEEDED']:
            print("   ⚠️ Item status may prevent proper functionality")
    
    # 6. Recommendations
    print("\n6. RECOMMENDED ACTIONS:")
    print("-" * 50)
    
    print("🔧 IMMEDIATE FIXES:")
    print("   1. Check Django logs during callback processing")
    print("   2. Test callback endpoint with this specific item_id")
    print("   3. Manually create BankAccounts from Pluggy API data")
    print("   4. Check if item status needs updating")
    
    print("\n💡 DEBUGGING STEPS:")
    print(f"   1. curl -X POST http://localhost:8000/api/banking/pluggy/callback/ -H 'Content-Type: application/json' -d '{{\"item_id\": \"{target_item_id}\"}}'")
    print("   2. Check logs: tail -f logs/django.log")
    print("   3. Run sync manually: python manage.py shell")
    print("      >>> from apps.banking.tasks import sync_bank_account")  
    print(f"      >>> sync_bank_account('{pluggy_item.id}')")
    
    # 7. Check company and user access
    print("\n7. ACCESS CONTROL CHECK:")
    print("-" * 50)
    
    company = pluggy_item.company
    print(f"✅ Company: {company.name}")
    print(f"   • Active: {company.is_active}")
    print(f"   • Plan: {company.subscription_plan.name if company.subscription_plan else 'No plan'}")
    
    # Check users in this company
    users = company.users.all()
    print(f"   • Users: {users.count()}")
    for user in users:
        print(f"     - {user.email} ({'active' if user.is_active else 'inactive'})")
    
    print("\n" + "=" * 80)
    print("✅ DIAGNOSTIC COMPLETE")

if __name__ == "__main__":
    main()