"""
Async service for transaction synchronization with Pluggy API
"""
import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import BankAccount, Transaction, TransactionCategory, BankProvider
from .pluggy_client import pluggy_service, PluggyError

logger = logging.getLogger(__name__)


class PluggyTransactionSyncService:
    """
    Async service for efficient transaction synchronization with Pluggy
    """
    
    def __init__(self):
        self.batch_size = 500  # Pluggy supports up to 500 per page
        self.max_concurrent_accounts = 3  # Be gentle with Pluggy API
    
    async def sync_all_accounts(self, company_id: int = None) -> Dict[str, Any]:
        """Sync all active Pluggy accounts"""
        try:
            # Get accounts to sync
            accounts = await self._get_accounts_to_sync(company_id)
            
            if not accounts:
                logger.info("No Pluggy accounts to sync")
                return {'total': 0, 'successful': 0, 'failed': 0}
            
            logger.info(f"Starting Pluggy sync for {len(accounts)} accounts")
            
            # Process accounts with rate limiting
            semaphore = asyncio.Semaphore(self.max_concurrent_accounts)
            
            async def sync_account_with_semaphore(account):
                async with semaphore:
                    await asyncio.sleep(0.5)  # Rate limiting
                    return await self.sync_account_transactions(account)
            
            # Run sync tasks concurrently
            tasks = [sync_account_with_semaphore(account) for account in accounts]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analyze results
            successful = sum(1 for r in results if isinstance(r, dict) and r.get('status') == 'success')
            failed = len(results) - successful
            
            logger.info(f"Pluggy sync completed: {successful} successful, {failed} failed")
            
            return {
                'total': len(accounts),
                'successful': successful,
                'failed': failed,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in Pluggy sync_all_accounts: {e}")
            raise
    
    async def sync_account_transactions(self, account: BankAccount) -> Dict[str, Any]:
        """Sync transactions for a specific Pluggy account"""
        try:
            logger.info(f"Syncing Pluggy account {account.id} - {account.bank_provider.name}")
            
            if not account.external_account_id:
                logger.warning(f"No Pluggy account ID for account {account.id}")
                return {'account_id': account.id, 'status': 'no_external_id', 'transactions': 0}
            
            # Determine sync date range
            sync_from = self._get_sync_from_date(account)
            sync_to = datetime.now().date()
            
            # Fetch and save transactions
            total_transactions = 0
            page = 1
            
            while True:
                try:
                    # Fetch transaction page from Pluggy
                    response = await pluggy_service.client.get_transactions(
                        account.external_account_id,
                        from_date=sync_from.isoformat(),
                        to_date=sync_to.isoformat(),
                        page=page,
                        page_size=self.batch_size
                    )
                    
                    transactions = response.get('results', [])\n                    if not transactions:\n                        break\n                    \n                    # Process transactions\n                    processed = await self._process_transaction_batch(account, transactions)\n                    total_transactions += processed\n                    \n                    # Check pagination\n                    total_pages = response.get('totalPages', 1)\n                    if page >= total_pages:\n                        break\n                    \n                    page += 1\n                    \n                    # Rate limiting between pages\n                    await asyncio.sleep(0.2)\n                    \n                except PluggyError as e:\n                    logger.error(f\"Pluggy error for account {account.id}: {e}\")\n                    if \"authentication\" in str(e).lower() or \"token\" in str(e).lower():\n                        await self._mark_account_error(account, 'auth_error')\n                    break\n                except Exception as e:\n                    logger.error(f\"Error fetching transactions for account {account.id}: {e}\")\n                    break\n            \n            # Update last sync time\n            await self._update_account_sync_time(account)\n            \n            # Update account balance\n            await self._update_account_balance(account)\n            \n            logger.info(f\"Synced {total_transactions} transactions for Pluggy account {account.id}\")\n            \n            return {\n                'account_id': account.id,\n                'status': 'success',\n                'transactions': total_transactions\n            }\n            \n        except Exception as e:\n            logger.error(f\"Error syncing Pluggy account {account.id}: {e}\")\n            return {\n                'account_id': account.id,\n                'status': 'error',\n                'error': str(e),\n                'transactions': 0\n            }\n    \n    async def connect_bank_account(\n        self, \n        company_id: int, \n        item_id: str, \n        bank_name: str = None\n    ) -> List[BankAccount]:\n        \"\"\"Connect bank accounts from a Pluggy item\"\"\"\n        try:\n            # Get item details\n            item = await pluggy_service.client.get_item(item_id)\n            \n            if item.get('status') != 'LOGIN_SUCCEEDED':\n                raise PluggyError(f\"Item {item_id} is not ready for sync (status: {item.get('status')})\")\n            \n            # Get accounts for this item\n            accounts_data = await pluggy_service.client.get_accounts(item_id)\n            \n            created_accounts = []\n            \n            for account_data in accounts_data:\n                # Create or update bank account\n                bank_account = await self._create_or_update_account(\n                    company_id, item_id, account_data, bank_name\n                )\n                if bank_account:\n                    created_accounts.append(bank_account)\n            \n            logger.info(f\"Connected {len(created_accounts)} accounts from Pluggy item {item_id}\")\n            \n            return created_accounts\n            \n        except Exception as e:\n            logger.error(f\"Error connecting Pluggy accounts for item {item_id}: {e}\")\n            raise\n    \n    async def _get_accounts_to_sync(self, company_id: int = None) -> List[BankAccount]:\n        \"\"\"Get Pluggy accounts that need synchronization\"\"\"\n        @sync_to_async\n        def get_accounts():\n            queryset = BankAccount.objects.filter(\n                status='active',\n                external_account_id__isnull=False,\n                bank_provider__name__icontains='pluggy'  # Filter for Pluggy accounts\n            ).select_related('bank_provider', 'company')\n            \n            if company_id:\n                queryset = queryset.filter(company_id=company_id)\n            \n            # Only sync accounts that haven't been synced recently\n            cutoff_time = timezone.now() - timedelta(hours=2)  # Pluggy allows more frequent syncs\n            queryset = queryset.filter(\n                models.Q(last_sync_at__isnull=True) |\n                models.Q(last_sync_at__lt=cutoff_time)\n            )\n            \n            return list(queryset)\n        \n        return await get_accounts()\n    \n    def _get_sync_from_date(self, account: BankAccount) -> datetime.date:\n        \"\"\"Determine the date to sync from\"\"\"\n        if account.last_sync_at:\n            # Sync from last sync date minus 1 day for overlap\n            return (account.last_sync_at - timedelta(days=1)).date()\n        else:\n            # First sync - get last 90 days (Pluggy allows more history)\n            return (timezone.now() - timedelta(days=90)).date()\n    \n    async def _process_transaction_batch(self, account: BankAccount, transactions: List[Dict]) -> int:\n        \"\"\"Process a batch of Pluggy transactions\"\"\"\n        @sync_to_async\n        def save_transactions():\n            created_count = 0\n            \n            with transaction.atomic():\n                for tx_data in transactions:\n                    # Check if transaction already exists\n                    external_id = tx_data.get('id')\n                    if not external_id:\n                        continue\n                    \n                    # Pluggy uses string IDs\n                    if Transaction.objects.filter(\n                        bank_account=account,\n                        external_id=str(external_id)\n                    ).exists():\n                        continue\n                    \n                    # Create transaction\n                    tx = self._create_transaction_from_pluggy_data(account, tx_data)\n                    if tx:\n                        created_count += 1\n            \n            return created_count\n        \n        return await save_transactions()\n    \n    def _create_transaction_from_pluggy_data(self, account: BankAccount, tx_data: Dict) -> Optional[Transaction]:\n        \"\"\"Create Transaction object from Pluggy data\"\"\"\n        try:\n            # Parse Pluggy transaction data\n            amount = Decimal(str(tx_data.get('amount', '0')))\n            description = tx_data.get('description', '').strip()\n            \n            # Pluggy provides 'type' field: DEBIT or CREDIT\n            transaction_type = 'credit' if tx_data.get('type') == 'CREDIT' else 'debit'\n            \n            # Parse date (Pluggy uses ISO format)\n            date_str = tx_data.get('date')\n            if not date_str:\n                return None\n            \n            tx_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()\n            \n            # Create transaction\n            transaction_obj = Transaction.objects.create(\n                bank_account=account,\n                external_id=str(tx_data.get('id')),\n                description=description,\n                amount=amount,\n                transaction_type=transaction_type,\n                transaction_date=tx_date,\n                counterpart_name=tx_data.get('merchant', {}).get('name', ''),\n                counterpart_document='',  # Pluggy doesn't always provide this\n                balance_after=Decimal(str(tx_data.get('balance', '0'))),\n                is_ai_categorized=False,\n                created_at=timezone.now()\n            )\n            \n            # Trigger AI categorization\n            from .signals import transaction_created\n            transaction_created.send(sender=Transaction, instance=transaction_obj, created=True)\n            \n            return transaction_obj\n            \n        except Exception as e:\n            logger.error(f\"Error creating transaction from Pluggy data: {e}\")\n            logger.error(f\"Transaction data: {tx_data}\")\n            return None\n    \n    async def _create_or_update_account(\n        self, \n        company_id: int, \n        item_id: str, \n        account_data: Dict,\n        bank_name: str = None\n    ) -> Optional[BankAccount]:\n        \"\"\"Create or update bank account from Pluggy data\"\"\"\n        @sync_to_async\n        def create_account():\n            try:\n                # Get or create bank provider\n                provider_name = bank_name or account_data.get('name', 'Pluggy Bank')\n                bank_provider, _ = BankProvider.objects.get_or_create(\n                    code=f\"pluggy_{item_id}\",\n                    defaults={\n                        'name': provider_name,\n                        'is_open_banking': True,\n                        'color': account_data.get('primaryColor', '#000000'),\n                    }\n                )\n                \n                # Get or create account\n                account, created = BankAccount.objects.get_or_create(\n                    company_id=company_id,\n                    external_account_id=str(account_data.get('id')),\n                    defaults={\n                        'bank_provider': bank_provider,\n                        'account_type': self._map_pluggy_account_type(account_data.get('type')),\n                        'agency': '0001',  # Pluggy doesn't provide agency\n                        'account_number': account_data.get('number', ''),\n                        'current_balance': Decimal(str(account_data.get('balance', '0'))),\n                        'available_balance': Decimal(str(account_data.get('balance', '0'))),\n                        'status': 'active',\n                        'is_active': True,\n                        'nickname': account_data.get('name', ''),\n                    }\n                )\n                \n                if not created:\n                    # Update existing account\n                    account.current_balance = Decimal(str(account_data.get('balance', '0')))\n                    account.available_balance = Decimal(str(account_data.get('balance', '0')))\n                    account.status = 'active'\n                    account.save()\n                \n                return account\n                \n            except Exception as e:\n                logger.error(f\"Error creating/updating account from Pluggy: {e}\")\n                return None\n        \n        return await create_account()\n    \n    def _map_pluggy_account_type(self, pluggy_type: str) -> str:\n        \"\"\"Map Pluggy account type to our account types\"\"\"\n        mapping = {\n            'BANK': 'checking',\n            'CREDIT_CARD': 'credit',\n            'INVESTMENT': 'savings',\n            'LOAN': 'business',\n        }\n        return mapping.get(pluggy_type, 'checking')\n    \n    async def _update_account_sync_time(self, account: BankAccount):\n        \"\"\"Update account last sync time\"\"\"\n        @sync_to_async\n        def update_sync_time():\n            BankAccount.objects.filter(id=account.id).update(\n                last_sync_at=timezone.now()\n            )\n        \n        await update_sync_time()\n    \n    async def _update_account_balance(self, account: BankAccount):\n        \"\"\"Update account balance from Pluggy\"\"\"\n        try:\n            account_data = await pluggy_service.client.get_account(account.external_account_id)\n            \n            if account_data:\n                current_balance = Decimal(str(account_data.get('balance', '0')))\n                \n                @sync_to_async\n                def update_balance():\n                    BankAccount.objects.filter(id=account.id).update(\n                        current_balance=current_balance,\n                        available_balance=current_balance  # Pluggy provides one balance\n                    )\n                \n                await update_balance()\n                \n        except Exception as e:\n            logger.error(f\"Error updating balance for Pluggy account {account.id}: {e}\")\n    \n    async def _mark_account_error(self, account: BankAccount, error_type: str):\n        \"\"\"Mark account as having an error\"\"\"\n        @sync_to_async\n        def mark_error():\n            status_map = {\n                'auth_error': 'error',\n                'connection_error': 'error',\n                'expired': 'expired'\n            }\n            status = status_map.get(error_type, 'error')\n            \n            BankAccount.objects.filter(id=account.id).update(\n                status=status\n            )\n        \n        await mark_error()\n        logger.warning(f\"Marked Pluggy account {account.id} as {error_type}\")\n\n\n# Global service instance\npluggy_sync_service = PluggyTransactionSyncService()