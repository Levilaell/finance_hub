#!/usr/bin/env python
"""
Check for new transactions in Pluggy that are not in the database
"""
import os
import sys
import django
from datetime import datetime, timedelta
import requests
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.conf import settings
from apps.banking.models import BankAccount, Transaction


print("🔍 Checking for New Transactions")
print("=" * 80)

# Get account
account = BankAccount.objects.filter(
    external_id__isnull=False,
    is_active=True
).first()

if not account:
    print("❌ No active account found")
    sys.exit(1)

print(f"\n📊 Account: {account.bank_provider.name}")
print(f"   Last sync: {account.last_sync_at}")

# Get existing transactions
existing_ids = set(
    Transaction.objects.filter(bank_account=account)
    .values_list('external_id', flat=True)
)
print(f"   Transactions in DB: {len(existing_ids)}")

# Get latest transaction date
latest_tx = Transaction.objects.filter(
    bank_account=account
).order_by('-transaction_date').first()

if latest_tx:
    print(f"   Latest transaction: {latest_tx.transaction_date.date()} - {latest_tx.description[:40]}")

# Get token
print(f"\n🔌 Connecting to Pluggy...")
auth_response = requests.post(
    "https://api.pluggy.ai/auth",
    headers={"accept": "application/json", "content-type": "application/json"},
    json={
        "clientId": settings.PLUGGY_CLIENT_ID,
        "clientSecret": settings.PLUGGY_CLIENT_SECRET
    }
)

if auth_response.status_code != 200:
    print(f"❌ Failed to authenticate: {auth_response.text}")
    sys.exit(1)

token = auth_response.json().get('accessToken')
print(f"   ✅ Authenticated successfully")
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "X-API-KEY": token
}

# Check for transactions in the last 7 days
print(f"\n📝 Checking transactions from last 7 days...")
from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
to_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

tx_response = requests.get(
    "https://api.pluggy.ai/transactions",
    headers=headers,
    params={
        "accountId": account.external_id,
        "from": from_date,
        "to": to_date,
        "pageSize": 100
    }
)

if tx_response.status_code != 200:
    print(f"❌ Failed to get transactions: {tx_response.text}")
    sys.exit(1)

data = tx_response.json()
transactions = data.get('results', [])
print(f"   Found {len(transactions)} transactions from Pluggy")

# Check for new transactions
new_transactions = []
for tx in transactions:
    tx_id = str(tx.get('id'))
    if tx_id not in existing_ids:
        new_transactions.append(tx)

if new_transactions:
    print(f"\n✅ Found {len(new_transactions)} NEW transactions not in database:")
    for tx in new_transactions:
        date = tx.get('date', '')[:10]
        desc = tx.get('description', '')[:50]
        amount = tx.get('amount', 0)
        print(f"   - {date}: {desc} - R$ {amount}")
else:
    print(f"\n❌ No new transactions found")
    print(f"   All {len(transactions)} transactions from Pluggy already exist in DB")
    
    # Show most recent transactions from Pluggy
    if transactions:
        print(f"\n📅 Most recent transactions from Pluggy:")
        for tx in sorted(transactions, key=lambda x: x.get('date', ''), reverse=True)[:5]:
            date = tx.get('date', '')
            desc = tx.get('description', '')[:50]
            amount = tx.get('amount', 0)
            tx_id = tx.get('id')
            in_db = "✅" if str(tx_id) in existing_ids else "❌"
            print(f"   {in_db} {date}: {desc} - R$ {amount}")

# Check item status
if account.pluggy_item_id:
    print(f"\n📋 Checking item status...")
    item_response = requests.get(
        f"https://api.pluggy.ai/items/{account.pluggy_item_id}",
        headers=headers
    )
    
    if item_response.status_code == 200:
        item = item_response.json()
        print(f"   Status: {item.get('status')}")
        print(f"   Updated: {item.get('updatedAt')}")
        
        if item.get('status') == 'OUTDATED':
            print(f"   ⚠️  Item is OUTDATED - may need update to see newest transactions")

print(f"\n💡 Notes:")
print(f"   - If you just made a transaction, it may take minutes/hours to appear")
print(f"   - Banks update their APIs at different intervals")
print(f"   - Try again in 5-10 minutes if transaction is very recent")