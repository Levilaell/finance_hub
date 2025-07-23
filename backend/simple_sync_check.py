#!/usr/bin/env python
"""
Simple script to check Pluggy sync status
"""
import os
import sys
import django
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import connection
from apps.banking.models import BankAccount, Transaction
from apps.banking.pluggy_client import PluggyClient


def get_account():
    """Get account synchronously"""
    return BankAccount.objects.filter(
        pluggy_item_id__isnull=False,
        is_active=True
    ).first()


def get_transaction_count(account):
    """Get transaction count synchronously"""
    return Transaction.objects.filter(bank_account=account).count()


async def check_sync():
    """Check sync status"""
    print("🔍 Checking Pluggy Sync Status")
    print("=" * 80)
    
    # Get account
    account = get_account()
    if not account:
        print("❌ No active account found")
        return
    
    print(f"\n📊 Account: {account.bank_provider.name}")
    print(f"   Last sync: {account.last_sync_at}")
    print(f"   Transactions in DB: {get_transaction_count(account)}")
    
    async with PluggyClient() as client:
        # Check item
        print(f"\n📋 Item Status:")
        item = await client.get_item(account.pluggy_item_id)
        print(f"   Status: {item.get('status')}")
        print(f"   Updated: {item.get('updatedAt')}")
        
        # Check recent transactions
        print(f"\n📝 Recent Transactions from Pluggy:")
        
        # Last 7 days
        from_date = (datetime.now() - timedelta(days=7)).date()
        to_date = (datetime.now() + timedelta(days=1)).date()
        
        response = await client.get_transactions(
            account.external_id,
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            page=1,
            page_size=50
        )
        
        transactions = response.get('results', [])
        print(f"   Found {len(transactions)} transactions in last 7 days")
        
        # Group by date
        by_date = {}
        for tx in transactions:
            date = tx.get('date', '')[:10]
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(tx)
        
        # Show last 3 days
        for date in sorted(by_date.keys(), reverse=True)[:3]:
            txs = by_date[date]
            print(f"\n   {date}: {len(txs)} transactions")
            for tx in txs[:3]:  # Show up to 3 per day
                desc = tx.get('description', '')[:40]
                amount = tx.get('amount', 0)
                tx_id = tx.get('id')
                print(f"      - {desc}: R$ {amount} (ID: {tx_id})")
        
        # Update item if OUTDATED
        if item.get('status') == 'OUTDATED':
            print(f"\n🔄 Item is OUTDATED, updating...")
            try:
                await client.sync_item(account.pluggy_item_id)
                print("   ✅ Update triggered")
                print("   Wait a few seconds and run again to see new transactions")
            except Exception as e:
                print(f"   ❌ Update failed: {e}")


if __name__ == "__main__":
    # Close any existing connections
    connection.close()
    
    # Run async function
    asyncio.run(check_sync())