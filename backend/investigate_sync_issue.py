#!/usr/bin/env python
"""
Script to investigate why new transactions are not being synced
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

from django.utils import timezone
from asgiref.sync import sync_to_async
from apps.banking.models import BankAccount, Transaction
from apps.banking.pluggy_client import PluggyClient
from apps.banking.pluggy_sync_service import PluggyTransactionSyncService


async def investigate_sync_issue():
    """Investigate sync issue with detailed analysis"""
    print("🔍 Investigating Pluggy Sync Issue")
    print("=" * 80)
    
    # Get the most recently synced account
    account = await sync_to_async(
        lambda: BankAccount.objects.filter(
            pluggy_item_id__isnull=False,
            is_active=True,
            last_sync_at__isnull=False
        ).order_by('-last_sync_at').first()
    )()
    
    if not account:
        print("❌ No active account with sync history found")
        return
    
    print(f"\n📊 Account Details:")
    print(f"   ID: {account.id}")
    print(f"   Bank: {account.bank_provider.name}")
    print(f"   Item ID: {account.pluggy_item_id}")
    print(f"   Last Sync: {account.last_sync_at}")
    print(f"   Balance: R$ {account.current_balance}")
    
    # Get transaction count
    tx_count = await sync_to_async(
        lambda: Transaction.objects.filter(bank_account=account).count()
    )()
    print(f"   Transactions in DB: {tx_count}")
    
    async with PluggyClient() as client:
        # 1. Check item status and last update
        print(f"\n📋 Checking Item Status...")
        item = await client.get_item(account.pluggy_item_id)
        print(f"   Status: {item.get('status')}")
        print(f"   Last Updated: {item.get('updatedAt')}")
        print(f"   Created: {item.get('createdAt')}")
        
        # Parse updatedAt to see how recent it is
        updated_at_str = item.get('updatedAt')
        if updated_at_str:
            # Remove milliseconds and Z
            clean_date = updated_at_str.split('.')[0].replace('Z', '')
            updated_at = datetime.fromisoformat(clean_date)
            time_since_update = datetime.utcnow() - updated_at
            print(f"   Time since last update: {time_since_update}")
        
        # 2. Get current balance from Pluggy
        print(f"\n💰 Checking Account Balance...")
        pluggy_account = await client.get_account(account.external_id)
        pluggy_balance = Decimal(str(pluggy_account.get('balance', 0)))
        print(f"   Pluggy Balance: R$ {pluggy_balance}")
        print(f"   DB Balance: R$ {account.current_balance}")
        if pluggy_balance != account.current_balance:
            print(f"   ⚠️  BALANCE MISMATCH! Difference: R$ {pluggy_balance - account.current_balance}")
        
        # 3. Check transactions for different date ranges
        print(f"\n🔍 Checking Transactions in Different Time Windows...")
        
        date_ranges = [
            ("Last 24 hours", 1),
            ("Last 2 days", 2),
            ("Last 3 days", 3),
            ("Last 7 days", 7),
            ("Last 30 days", 30)
        ]
        
        for range_name, days in date_ranges:
            from_date = (datetime.now() - timedelta(days=days)).date()
            to_date = (datetime.now() + timedelta(days=1)).date()  # Include tomorrow for timezone issues
            
            response = await client.get_transactions(
                account.external_id,
                from_date=from_date.isoformat(),
                to_date=to_date.isoformat(),
                page=1,
                page_size=100
            )
            
            transactions = response.get('results', [])
            total = response.get('total', 0)
            
            print(f"\n   📅 {range_name} ({from_date} to {to_date}):")
            print(f"      Total transactions: {total}")
            
            # Group by date
            by_date = {}
            for tx in transactions:
                tx_date = tx.get('date', '')[:10]  # Get just the date part
                if tx_date not in by_date:
                    by_date[tx_date] = []
                by_date[tx_date].append(tx)
            
            # Show summary by date
            for date in sorted(by_date.keys(), reverse=True)[:5]:  # Show last 5 days
                txs = by_date[date]
                total_amount = sum(Decimal(str(tx.get('amount', 0))) for tx in txs)
                print(f"      {date}: {len(txs)} transactions, Total: R$ {total_amount}")
                
                # Show individual transactions for today
                if date == str(datetime.now().date()):
                    print(f"         Today's transactions:")
                    for tx in txs[:5]:  # Show up to 5
                        desc = tx.get('description', '')[:40]
                        amount = tx.get('amount', 0)
                        tx_time = tx.get('date', '')
                        print(f"         - {tx_time}: {desc} - R$ {amount}")
        
        # 4. Force update the item and check again
        print(f"\n🔄 Forcing Item Update...")
        if item.get('status') in ['OUTDATED', 'UPDATED']:
            try:
                update_result = await client.sync_item(account.pluggy_item_id)
                print(f"   Update triggered successfully")
                print(f"   Waiting 5 seconds for update to process...")
                await asyncio.sleep(5)
                
                # Check item status again
                item_after = await client.get_item(account.pluggy_item_id)
                print(f"   New status: {item_after.get('status')}")
                print(f"   New updatedAt: {item_after.get('updatedAt')}")
                
                # Check if new transactions appeared
                print(f"\n   Checking for new transactions after update...")
                response_after = await client.get_transactions(
                    account.external_id,
                    from_date=(datetime.now() - timedelta(days=1)).date().isoformat(),
                    to_date=(datetime.now() + timedelta(days=1)).date().isoformat(),
                    page=1,
                    page_size=50
                )
                
                new_count = response_after.get('total', 0)
                print(f"   Transactions after update: {new_count}")
                
            except Exception as e:
                print(f"   ❌ Could not update item: {e}")
        
        # 5. Show webhook configuration
        print(f"\n🔔 Webhook Status:")
        print(f"   Check if webhooks are properly configured to receive real-time updates")
        print(f"   This would eliminate the need for manual syncing")


if __name__ == "__main__":
    asyncio.run(investigate_sync_issue())