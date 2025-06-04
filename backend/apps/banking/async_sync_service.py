"""
Async service for transaction synchronization with Open Banking
"""
import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import BankAccount, Transaction, TransactionCategory
from .open_banking_client import open_banking_service, OpenBankingError

logger = logging.getLogger(__name__)


class AsyncTransactionSyncService:
    """
    Async service for efficient transaction synchronization
    """
    
    def __init__(self):
        self.batch_size = 100
        self.max_concurrent_accounts = 5
    
    async def sync_all_accounts(self, company_id: int = None):
        """Sync all active accounts, optionally filtered by company"""
        try:
            # Get accounts to sync
            accounts = await self._get_accounts_to_sync(company_id)
            
            if not accounts:
                logger.info("No accounts to sync")
                return
            
            logger.info(f"Starting sync for {len(accounts)} accounts")
            
            # Process accounts in batches to avoid overwhelming APIs
            semaphore = asyncio.Semaphore(self.max_concurrent_accounts)
            
            async def sync_account_with_semaphore(account):
                async with semaphore:
                    return await self.sync_account_transactions(account)
            
            # Run sync tasks concurrently
            tasks = [sync_account_with_semaphore(account) for account in accounts]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            successful = sum(1 for r in results if not isinstance(r, Exception))
            failed = len(results) - successful
            
            logger.info(f"Sync completed: {successful} successful, {failed} failed")
            
            return {
                'total': len(accounts),
                'successful': successful,
                'failed': failed,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in sync_all_accounts: {e}")
            raise
    
    async def sync_account_transactions(self, account: BankAccount) -> Dict[str, Any]:
        """Sync transactions for a specific account"""
        try:
            logger.info(f"Syncing account {account.id} - {account.bank_provider.name}")
            
            # Check if account has valid tokens
            if not account.access_token:
                logger.warning(f"No access token for account {account.id}")
                return {'account_id': account.id, 'status': 'no_token', 'transactions': 0}
            
            # Get Open Banking client
            client = open_banking_service.get_client(account.bank_provider.code)
            
            # Determine sync date range
            sync_from = self._get_sync_from_date(account)
            sync_to = datetime.now().date()
            
            # Fetch and save transactions
            total_transactions = 0
            page = 1
            
            while True:
                try:
                    # Fetch transaction page
                    response = await client.get_transactions(\n                        account.access_token,\n                        account.external_account_id,\n                        from_date=sync_from.isoformat(),\n                        to_date=sync_to.isoformat(),\n                        page=page,\n                        page_size=self.batch_size\n                    )\n                    \n                    transactions = response.get('data', [])\n                    if not transactions:\n                        break\n                    \n                    # Process transactions\n                    processed = await self._process_transaction_batch(account, transactions)\n                    total_transactions += processed\n                    \n                    # Check if there are more pages\n                    meta = response.get('meta', {})\n                    if page >= meta.get('totalPages', 1):\n                        break\n                    \n                    page += 1\n                    \n                    # Rate limiting\n                    await asyncio.sleep(0.1)\n                    \n                except OpenBankingError as e:\n                    logger.error(f\"Open Banking error for account {account.id}: {e}\")\n                    if \"token\" in str(e).lower():\n                        await self._mark_account_token_expired(account)\n                    break\n                except Exception as e:\n                    logger.error(f\"Error fetching transactions for account {account.id}: {e}\")\n                    break\n            \n            # Update last sync time\n            await self._update_account_sync_time(account)\n            \n            # Update account balance\n            await self._update_account_balance(account, client)\n            \n            logger.info(f\"Synced {total_transactions} transactions for account {account.id}\")\n            \n            return {\n                'account_id': account.id,\n                'status': 'success',\n                'transactions': total_transactions\n            }\n            \n        except Exception as e:\n            logger.error(f\"Error syncing account {account.id}: {e}\")\n            return {\n                'account_id': account.id,\n                'status': 'error',\n                'error': str(e),\n                'transactions': 0\n            }\n    \n    async def _get_accounts_to_sync(self, company_id: int = None) -> List[BankAccount]:\n        \"\"\"Get accounts that need synchronization\"\"\"\n        @sync_to_async\n        def get_accounts():\n            queryset = BankAccount.objects.filter(\n                status='active',\n                access_token__isnull=False\n            ).select_related('bank_provider', 'company')\n            \n            if company_id:\n                queryset = queryset.filter(company_id=company_id)\n            \n            # Only sync accounts that haven't been synced recently\n            cutoff_time = timezone.now() - timedelta(hours=1)\n            queryset = queryset.filter(\n                models.Q(last_sync_at__isnull=True) |\n                models.Q(last_sync_at__lt=cutoff_time)\n            )\n            \n            return list(queryset)\n        \n        return await get_accounts()\n    \n    def _get_sync_from_date(self, account: BankAccount) -> datetime.date:\n        \"\"\"Determine the date to sync from\"\"\"\n        if account.last_sync_at:\n            # Sync from last sync date minus 1 day for overlap\n            return (account.last_sync_at - timedelta(days=1)).date()\n        else:\n            # First sync - get last 30 days\n            return (timezone.now() - timedelta(days=30)).date()\n    \n    async def _process_transaction_batch(self, account: BankAccount, transactions: List[Dict]) -> int:\n        \"\"\"Process a batch of transactions\"\"\"\n        @sync_to_async\n        def save_transactions():\n            created_count = 0\n            \n            with transaction.atomic():\n                for tx_data in transactions:\n                    # Check if transaction already exists\n                    external_id = tx_data.get('transactionId')\n                    if not external_id:\n                        continue\n                    \n                    if Transaction.objects.filter(\n                        bank_account=account,\n                        external_id=external_id\n                    ).exists():\n                        continue\n                    \n                    # Create transaction\n                    tx = self._create_transaction_from_data(account, tx_data)\n                    if tx:\n                        created_count += 1\n            \n            return created_count\n        \n        return await save_transactions()\n    \n    def _create_transaction_from_data(self, account: BankAccount, tx_data: Dict) -> Transaction:\n        \"\"\"Create Transaction object from Open Banking data\"\"\"\n        try:\n            # Parse transaction data according to Open Banking Brasil standard\n            amount = Decimal(str(tx_data.get('amount', '0')))\n            description = tx_data.get('description', '').strip()\n            \n            # Determine transaction type\n            credit_debit = tx_data.get('creditDebitType', 'DEBIT')\n            transaction_type = 'credit' if credit_debit == 'CREDIT' else 'debit'\n            \n            # Parse date\n            tx_date_str = tx_data.get('completedAuthorisedPaymentDate')\n            if not tx_date_str:\n                tx_date_str = tx_data.get('valueDate')\n            \n            tx_date = datetime.fromisoformat(tx_date_str.replace('Z', '+00:00')).date()\n            \n            # Create transaction\n            transaction_obj = Transaction.objects.create(\n                bank_account=account,\n                external_id=tx_data.get('transactionId'),\n                description=description,\n                amount=amount,\n                transaction_type=transaction_type,\n                transaction_date=tx_date,\n                counterpart_name=tx_data.get('creditorName', ''),\n                counterpart_document=tx_data.get('creditorAccount', {}).get('number', ''),\n                is_ai_categorized=False,\n                created_at=timezone.now()\n            )\n            \n            # Trigger AI categorization asynchronously\n            from .signals import transaction_created\n            transaction_created.send(sender=Transaction, instance=transaction_obj, created=True)\n            \n            return transaction_obj\n            \n        except Exception as e:\n            logger.error(f\"Error creating transaction from data: {e}\")\n            logger.error(f\"Transaction data: {tx_data}\")\n            return None\n    \n    async def _update_account_sync_time(self, account: BankAccount):\n        \"\"\"Update account last sync time\"\"\"\n        @sync_to_async\n        def update_sync_time():\n            BankAccount.objects.filter(id=account.id).update(\n                last_sync_at=timezone.now()\n            )\n        \n        await update_sync_time()\n    \n    async def _update_account_balance(self, account: BankAccount, client):\n        \"\"\"Update account balance from Open Banking\"\"\"\n        try:\n            balance_data = await client.get_account_balance(\n                account.access_token,\n                account.external_account_id\n            )\n            \n            if balance_data:\n                current_balance = Decimal(str(balance_data.get('amount', '0')))\n                available_balance = Decimal(str(balance_data.get('availableAmount', '0')))\n                \n                @sync_to_async\n                def update_balance():\n                    BankAccount.objects.filter(id=account.id).update(\n                        current_balance=current_balance,\n                        available_balance=available_balance\n                    )\n                \n                await update_balance()\n                \n        except Exception as e:\n            logger.error(f\"Error updating balance for account {account.id}: {e}\")\n    \n    async def _mark_account_token_expired(self, account: BankAccount):\n        \"\"\"Mark account as having expired token\"\"\"\n        @sync_to_async\n        def mark_expired():\n            BankAccount.objects.filter(id=account.id).update(\n                status='expired'\n            )\n        \n        await mark_expired()\n        logger.warning(f\"Marked account {account.id} as expired due to token issues\")\n\n\n# Global service instance\nasync_sync_service = AsyncTransactionSyncService()