#!/usr/bin/env python
"""
Diagnostic script for Pluggy sync issues
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.conf import settings
from apps.banking.models import BankAccount, Transaction


def get_pluggy_token():
    """Get Pluggy API token"""
    url = "https://api.pluggy.ai/auth"
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    data = {
        "clientId": settings.PLUGGY_CLIENT_ID,
        "clientSecret": settings.PLUGGY_CLIENT_SECRET
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get('accessToken')
    else:
        raise Exception(f"Failed to authenticate: {response.text}")


def check_sync_issue():
    """Check sync issue"""
    print("🔍 Pluggy Sync Diagnostic")
    print("=" * 80)
    
    # Get account
    account = BankAccount.objects.filter(
        pluggy_item_id__isnull=False,
        is_active=True
    ).first()
    
    if not account:
        print("❌ No active account found")
        return
    
    print(f"\n📊 Account Details:")
    print(f"   Bank: {account.bank_provider.name}")
    print(f"   Item ID: {account.pluggy_item_id}")
    print(f"   External ID: {account.external_id}")
    print(f"   Last sync: {account.last_sync_at}")
    print(f"   Balance: R$ {account.current_balance}")
    
    # Get transaction count
    tx_count = Transaction.objects.filter(bank_account=account).count()
    latest_tx = Transaction.objects.filter(bank_account=account).order_by('-transaction_date').first()
    
    print(f"\n📈 Database Status:")
    print(f"   Total transactions: {tx_count}")
    if latest_tx:
        print(f"   Latest transaction: {latest_tx.transaction_date} - {latest_tx.description[:40]}")
    
    # Get Pluggy data
    print(f"\n🔌 Checking Pluggy API...")
    try:
        token = get_pluggy_token()
        headers = {
            "accept": "application/json",
            "X-API-KEY": token
        }
        
        # Check item status
        item_url = f"https://api.pluggy.ai/items/{account.pluggy_item_id}"
        item_response = requests.get(item_url, headers=headers)
        
        if item_response.status_code == 200:
            item = item_response.json()
            print(f"\n📋 Item Status:")
            print(f"   Status: {item.get('status')}")
            print(f"   Updated: {item.get('updatedAt')}")
            
            # Parse update time
            updated_str = item.get('updatedAt', '')
            if updated_str:
                # Remove milliseconds and Z
                clean_date = updated_str.split('.')[0].replace('Z', '')
                try:
                    updated_dt = datetime.fromisoformat(clean_date)
                    time_diff = datetime.utcnow() - updated_dt
                    print(f"   Last update: {time_diff} ago")
                except:
                    pass
        
        # Get transactions
        print(f"\n📝 Checking Transactions...")
        
        # Try different date ranges
        ranges = [
            ("Today", 0, 1),
            ("Last 2 days", 2, 1),
            ("Last 7 days", 7, 1),
        ]
        
        for range_name, days_back, days_forward in ranges:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            to_date = (datetime.now() + timedelta(days=days_forward)).strftime('%Y-%m-%d')
            
            tx_url = f"https://api.pluggy.ai/transactions"
            params = {
                "accountId": account.external_id,
                "from": from_date,
                "to": to_date,
                "pageSize": 50
            }
            
            tx_response = requests.get(tx_url, headers=headers, params=params)
            
            if tx_response.status_code == 200:
                data = tx_response.json()
                total = data.get('total', 0)
                transactions = data.get('results', [])
                
                print(f"\n   📅 {range_name} ({from_date} to {to_date}):")
                print(f"      Total: {total} transactions")
                
                if range_name == "Today" and transactions:
                    print(f"      Today's transactions:")
                    for tx in transactions[:5]:
                        desc = tx.get('description', '')[:40]
                        amount = tx.get('amount', 0)
                        date = tx.get('date', '')
                        print(f"      - {date}: {desc} - R$ {amount}")
                elif range_name == "Last 2 days":
                    # Group by date
                    by_date = {}
                    for tx in transactions:
                        date = tx.get('date', '')[:10]
                        if date not in by_date:
                            by_date[date] = 0
                        by_date[date] += 1
                    
                    for date in sorted(by_date.keys(), reverse=True):
                        print(f"      {date}: {by_date[date]} transactions")
        
        # Check if update is needed
        if item.get('status') == 'OUTDATED':
            print(f"\n⚠️  Item is OUTDATED - needs update to get latest transactions")
            print(f"   The sync process should trigger an update automatically")
        
    except Exception as e:
        print(f"\n❌ Error checking Pluggy: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n💡 Possible Issues:")
    print(f"   1. Transaction delay: Banks may take minutes/hours to report new transactions")
    print(f"   2. Item needs update: Status OUTDATED means data is stale")
    print(f"   3. Timezone issues: Transaction dates might be in different timezones")
    print(f"   4. Webhook delays: Real-time updates depend on webhook configuration")


if __name__ == "__main__":
    check_sync_issue()