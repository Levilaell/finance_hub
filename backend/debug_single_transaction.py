"""
Debug a single transaction import
"""
import os
import sys
import django
import asyncio
import logging

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.banking.models import BankAccount, Transaction
from apps.banking.pluggy_client import PluggyClient
from apps.banking.pluggy_sync_service import pluggy_sync_service
from datetime import datetime, timedelta

# Set up logging to see everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Silence some noisy loggers
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

async def debug_single_transaction():
    print("\n=== DEBUG SINGLE TRANSACTION ===\n")
    
    # Get account
    account = BankAccount.objects.filter(
        external_id__isnull=False,
        status='active'
    ).first()
    
    if not account:
        print("No account found!")
        return
    
    print(f"Using account: {account.bank_provider.name}")
    print(f"External ID: {account.external_id}\n")
    
    # Delete one transaction to reimport it
    tx_to_delete = Transaction.objects.filter(
        bank_account=account,
        external_id__isnull=False
    ).first()
    
    if tx_to_delete:
        deleted_external_id = tx_to_delete.external_id
        print(f"Deleting transaction: {tx_to_delete.description}")
        print(f"External ID: {deleted_external_id}")
        tx_to_delete.delete()
        
        # Now fetch this specific transaction from Pluggy
        async with PluggyClient() as client:
            # Get transactions from last 30 days
            response = await client.get_transactions(
                account.external_id,
                from_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'),
                page=1,
                page_size=200
            )
            
            # Find the deleted transaction
            transactions = response.get('results', [])
            
            for tx in transactions:
                if tx.get('id') == deleted_external_id:
                    print("\nFound transaction in Pluggy response!")
                    print("=" * 60)
                    import json
                    print(json.dumps(tx, indent=2, ensure_ascii=False))
                    print("=" * 60)
                    
                    # Try to create it
                    print("\nCreating transaction...")
                    result = pluggy_sync_service._create_transaction_from_pluggy_data(account, tx)
                    
                    if result:
                        print(f"\nCreated transaction: {result.id}")
                        print(f"Category: {result.category}")
                        print(f"Is AI categorized: {result.is_ai_categorized}")
                    else:
                        print("\nFailed to create transaction!")
                    
                    break
            else:
                print(f"\nCouldn't find transaction {deleted_external_id} in Pluggy response")
                print(f"Total transactions in response: {len(transactions)}")
    else:
        print("No transactions to test with!")

if __name__ == '__main__':
    asyncio.run(debug_single_transaction())