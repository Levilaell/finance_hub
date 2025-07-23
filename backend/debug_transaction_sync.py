#!/usr/bin/env python
"""
Debug script to check transaction sync issues
"""
import os
import sys
import django
import asyncio
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.banking.models import BankAccount, Transaction
from apps.banking.pluggy_client import PluggyClient
from decimal import Decimal


async def debug_transaction_sync():
    """Debug transaction sync"""
    print("🔍 Debugging Pluggy transaction sync...")
    print("=" * 50)
    
    # Get account
    account = BankAccount.objects.filter(
        pluggy_item_id__isnull=False,
        is_active=True
    ).first()
    
    if not account:
        print("❌ No active account with Pluggy item found")
        return
    
    print(f"\n📊 Account details:")
    print(f"   ID: {account.id}")
    print(f"   Bank: {account.bank_provider.name}")
    print(f"   External ID: {account.external_id}")
    print(f"   Item ID: {account.pluggy_item_id}")
    print(f"   Last sync: {account.last_sync_at}")
    
    # Get existing transactions count
    existing_count = Transaction.objects.filter(bank_account=account).count()
    print(f"\n📈 Existing transactions in DB: {existing_count}")
    
    # Get latest transactions from DB
    latest_txs = Transaction.objects.filter(
        bank_account=account
    ).order_by('-transaction_date', '-created_at')[:5]
    
    print(f"\n📝 Latest transactions in DB:")
    for tx in latest_txs:
        print(f"   {tx.transaction_date} - {tx.description[:50]} - R$ {tx.amount} - ID: {tx.external_id}")
    
    async with PluggyClient() as client:
        # Check item status
        print(f"\n🔍 Checking item status...")
        item = await client.get_item(account.pluggy_item_id)
        print(f"   Status: {item.get('status')}")
        print(f"   Last Updated: {item.get('updatedAt')}")
        print(f"   Created: {item.get('createdAt')}")
        
        # Get transactions from Pluggy
        print(f"\n🔍 Fetching transactions from Pluggy API...")
        from_date = (datetime.now() - timedelta(days=7)).date()
        to_date = (datetime.now() + timedelta(days=1)).date()
        
        print(f"   Date range: {from_date} to {to_date}")
        
        response = await client.get_transactions(
            account.external_id,
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            page=1,
            page_size=20
        )
        
        transactions = response.get('results', [])
        print(f"\n📊 Found {len(transactions)} transactions from Pluggy")
        
        # Show transactions from Pluggy
        print(f"\n📝 Transactions from Pluggy API:")
        for idx, tx in enumerate(transactions[:10]):  # Show first 10
            tx_date = tx.get('date', 'no date')
            tx_desc = tx.get('description', 'no description')[:50]
            tx_amount = tx.get('amount', 0)
            tx_id = tx.get('id')
            
            # Check if exists in DB
            exists = Transaction.objects.filter(
                bank_account=account,
                external_id=str(tx_id)
            ).exists()
            
            status = "✅ EXISTS" if exists else "🆕 NEW"
            print(f"   {idx+1}. {tx_date} - {tx_desc} - R$ {tx_amount} - ID: {tx_id} - {status}")
        
        # Check for today's transactions specifically
        print(f"\n🔍 Checking for today's transactions...")
        today = datetime.now().date()
        today_txs = [tx for tx in transactions if tx.get('date', '').startswith(str(today))]
        print(f"   Found {len(today_txs)} transactions for today ({today})")
        
        if today_txs:
            print(f"\n📝 Today's transactions:")
            for tx in today_txs:
                tx_desc = tx.get('description', 'no description')[:50]
                tx_amount = tx.get('amount', 0)
                tx_id = tx.get('id')
                tx_time = tx.get('date')
                print(f"   {tx_time} - {tx_desc} - R$ {tx_amount} - ID: {tx_id}")


if __name__ == "__main__":
    asyncio.run(debug_transaction_sync())