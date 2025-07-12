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
from .pluggy_client import PluggyClient, PluggyError

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
            # ✅ CORRIGIDO: Buscar dados da conta de forma assíncrona
            account_info = await self._get_account_info(account)
            
            logger.info(f"🔄 Syncing Pluggy account {account_info['id']} - {account_info['bank_name']}")
            
            if not account_info['external_id']:
                logger.warning(f"❌ No Pluggy account ID for account {account_info['id']}")
                return {'account_id': account_info['id'], 'status': 'no_external_id', 'transactions': 0}
            
            # Determine sync date range
            sync_from = self._get_sync_from_date_safe(account_info)
            sync_to = datetime.now().date()
            
            logger.info(f"📅 Syncing transactions from {sync_from} to {sync_to}")
            
            # Fetch and save transactions
            total_transactions = 0
            page = 1
            
            # Use the PluggyClient directly
            async with PluggyClient() as client:
                while True:
                    try:
                        logger.info(f"📊 Fetching page {page} for account {account_info['external_id']}")
                        
                        # Fetch transaction page from Pluggy
                        response = await client.get_transactions(
                            account_info['external_id'],
                            from_date=sync_from.isoformat(),
                            to_date=sync_to.isoformat(),
                            page=page,
                            page_size=self.batch_size
                        )
                        
                        transactions = response.get('results', [])
                        logger.info(f"📋 Found {len(transactions)} transactions on page {page}")
                        
                        if not transactions:
                            logger.info("✅ No more transactions found")
                            break
                        
                        # Process transactions
                        processed = await self._process_transaction_batch(account, transactions)
                        total_transactions += processed
                        
                        logger.info(f"💾 Processed {processed} new transactions")
                        
                        # Check pagination
                        total_pages = response.get('totalPages', 1)
                        current_page = response.get('page', page)
                        
                        logger.info(f"📃 Page {current_page} of {total_pages}")
                        
                        if page >= total_pages:
                            logger.info("✅ Reached last page")
                            break
                        
                        page += 1
                        
                        # Rate limiting between pages
                        await asyncio.sleep(0.2)
                        
                    except PluggyError as e:
                        logger.error(f"❌ Pluggy error for account {account_info['id']}: {e}")
                        if "authentication" in str(e).lower() or "token" in str(e).lower():
                            await self._mark_account_error(account, 'auth_error')
                        break
                    except Exception as e:
                        logger.error(f"❌ Error fetching transactions for account {account_info['id']}: {e}")
                        break
            
            # Update last sync time
            await self._update_account_sync_time(account)
            
            # Update account balance
            await self._update_account_balance(account)
            
            logger.info(f"✅ Synced {total_transactions} transactions for Pluggy account {account_info['id']}")
            
            return {
                'account_id': account_info['id'],
                'status': 'success',
                'transactions': total_transactions
            }
            
        except Exception as e:
            logger.error(f"❌ Error syncing Pluggy account {account.id}: {e}", exc_info=True)
            return {
                'account_id': account.id,
                'status': 'error',
                'error': str(e),
                'transactions': 0
            }
    
    @sync_to_async
    def _get_account_info(self, account: BankAccount) -> Dict[str, Any]:
        """Get account info safely for async context"""
        # Fazer select_related para evitar queries extras
        account_with_provider = BankAccount.objects.select_related('bank_provider').get(
            id=account.id
        )
        
        return {
            'id': account_with_provider.id,
            'external_id': account_with_provider.external_id,
            'bank_name': account_with_provider.bank_provider.name if account_with_provider.bank_provider else 'Unknown',
            'last_sync_at': account_with_provider.last_sync_at
        }
    
    def _get_sync_from_date_safe(self, account_info: Dict) -> datetime.date:
        """Determine the date to sync from using account info dict"""
        last_sync = account_info.get('last_sync_at')
        
        if not last_sync:
            # ✅ PRIMEIRA SYNC: 1 ano no sandbox, 3 meses em produção
            if getattr(settings, 'PLUGGY_USE_SANDBOX', False):
                days = 365  # 1 ano para pegar transações Netflix de 2024
                logger.info(f"🧪 Sandbox: First sync, using {days} days")
            else:
                days = 90   # 3 meses em produção
                logger.info(f"🚀 Production: First sync, using {days} days")
            
            return (timezone.now() - timedelta(days=days)).date()
        else:
            # ✅ SYNC INCREMENTAL: 1 dia de overlap
            days_since_sync = (timezone.now() - last_sync).days
            
            if days_since_sync > 30:
                # Se muito tempo sem sync, buscar 30 dias para não perder nada
                logger.info(f"⚠️ Long gap ({days_since_sync} days), using 30 days")
                return (timezone.now() - timedelta(days=30)).date()
            else:
                # Incremental normal
                logger.info(f"🔄 Incremental sync, {days_since_sync} days since last sync")
                return (last_sync - timedelta(days=1)).date()


    async def _get_accounts_to_sync(self, company_id: int = None) -> List[BankAccount]:
        """Get Pluggy accounts that need synchronization"""
        @sync_to_async
        def get_accounts():
            from django.db import models
            
            queryset = BankAccount.objects.filter(
                status='active',
                external_id__isnull=False,
                # ✅ CORRIGIDO: Filtrar por contas Pluggy usando external_id
                external_id__startswith=''  # Pluggy IDs são UUIDs
            ).select_related('bank_provider', 'company')
            
            if company_id:
                queryset = queryset.filter(company_id=company_id)
            
            # Only sync accounts that haven't been synced recently
            cutoff_time = timezone.now() - timedelta(hours=2)  # Pluggy allows more frequent syncs
            queryset = queryset.filter(
                models.Q(last_sync_at__isnull=True) |
                models.Q(last_sync_at__lt=cutoff_time)
            )
            
            return list(queryset)
        
        return await get_accounts()
    
    async def _process_transaction_batch(self, account: BankAccount, transactions: List[Dict]) -> int:
        """Process a batch of Pluggy transactions"""
        @sync_to_async
        def save_transactions():
            created_count = 0
            
            with transaction.atomic():
                for tx_data in transactions:
                    # Check if transaction already exists
                    external_id = tx_data.get('id')
                    if not external_id:
                        continue
                    
                    # Pluggy uses string IDs
                    if Transaction.objects.filter(
                        bank_account=account,
                        external_id=str(external_id)
                    ).exists():
                        logger.debug(f"Transaction {external_id} already exists, skipping")
                        continue
                    
                    # Create transaction
                    tx = self._create_transaction_from_pluggy_data(account, tx_data)
                    if tx:
                        created_count += 1
                        logger.debug(f"Created transaction: {tx.description} - R$ {tx.amount}")
            
            return created_count
        
        return await save_transactions()
    

    def _create_transaction_from_pluggy_data(self, account: BankAccount, tx_data: Dict) -> Optional[Transaction]:
        """Create Transaction object from Pluggy data"""
        try:
            logger.info(f"🔄 Creating transaction from data: {tx_data}")
            
            # Parse Pluggy transaction data
            amount = Decimal(str(tx_data.get('amount', '0')))
            description = tx_data.get('description', '').strip()
            
            logger.info(f"💰 Amount: {amount}, Description: '{description}'")
            
            # Pluggy provides 'type' field: DEBIT or CREDIT
            transaction_type = 'credit' if tx_data.get('type') == 'CREDIT' else 'debit'
            logger.info(f"📊 Transaction type: {transaction_type} (from Pluggy: {tx_data.get('type')})")
            
            # Parse date (Pluggy uses ISO format)
            date_str = tx_data.get('date')
            if not date_str:
                logger.error(f"❌ Transaction missing date: {tx_data}")
                return None
            
            logger.info(f"📅 Parsing date: '{date_str}'")
            
            # Handle different date formats from Pluggy
            try:
                if 'T' in date_str:
                    # Full datetime
                    tx_datetime = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    tx_date = tx_datetime.date()
                else:
                    # Date only
                    tx_date = datetime.fromisoformat(date_str).date()
                
                logger.info(f"✅ Parsed date: {tx_date}")
            except ValueError as e:
                logger.error(f"❌ Invalid date format in transaction: {date_str} - {e}")
                return None
            
            # Get merchant info
            merchant_info = tx_data.get('merchant', {}) or {}
            merchant_name = ''
            if merchant_info:
                merchant_name = merchant_info.get('name', '')
            
            logger.info(f"🏪 Merchant: '{merchant_name}'")
            
            # Check external_id
            external_id = str(tx_data.get('id'))
            logger.info(f"🆔 External ID: {external_id}")
            
            # ✅ NOVO: Categorização APENAS com dados da Pluggy
            category = self._get_pluggy_category(tx_data)
            if category:
                logger.info(f"🎯 Pluggy category found: {category.name}")
            else:
                logger.info(f"❓ No Pluggy category data available")
            
            # Create transaction
            logger.info(f"💾 Creating transaction in database...")
            
            # Handle balance None case
            balance_value = tx_data.get('balance')
            if balance_value is None or balance_value == '':
                balance_after = Decimal('0')
            else:
                balance_after = Decimal(str(balance_value))
            
            transaction_obj = Transaction.objects.create(
                bank_account=account,
                external_id=external_id,
                description=description,
                amount=amount,
                transaction_type=transaction_type,
                transaction_date=tx_date,
                counterpart_name=merchant_name,
                counterpart_document='',
                balance_after=balance_after,
                category=category,  # ✅ APENAS categoria da Pluggy ou None
                is_ai_categorized=False,  # ✅ Não é IA, é da Pluggy
                status='completed',
                created_at=timezone.now()
            )
            
            category_name = category.name if category else 'Uncategorized'
            logger.info(f"✅ Transaction created: ID={transaction_obj.id}, Description='{transaction_obj.description}', Category='{category_name}'")
            
            return transaction_obj
            
        except Exception as e:
            logger.error(f"❌ Error creating transaction from Pluggy data: {e}", exc_info=True)
            logger.error(f"❌ Transaction data that failed: {tx_data}")
            return None

    def _get_pluggy_category(self, tx_data: Dict) -> Optional['TransactionCategory']:
        """Get category from Pluggy data only"""
        try:
            # ✅ Verificar se a Pluggy forneceu categoria
            pluggy_category = tx_data.get('category')
            pluggy_category_id = tx_data.get('categoryId')
            
            logger.info(f"🔍 Pluggy category data: category='{pluggy_category}', categoryId='{pluggy_category_id}'")
            
            # Se a Pluggy não forneceu categoria, retornar None
            if not pluggy_category and not pluggy_category_id:
                logger.info(f"ℹ️ No category data from Pluggy - will be uncategorized")
                return None
            
            # ✅ Se a Pluggy forneceu categoria, mapear para nossas categorias
            if pluggy_category:
                # Mapear categorias da Pluggy para nossas categorias
                category_mapping = {
                    # Pluggy category name -> nossa categoria
                    'entertainment': 'Entretenimento',
                    'food': 'Alimentação', 
                    'transportation': 'Transporte',
                    'utilities': 'Utilidades',
                    'streaming': 'Streaming',
                    'shopping': 'Compras',
                    'healthcare': 'Saúde',
                    'education': 'Educação',
                    'travel': 'Viagem',
                    'bills': 'Contas',
                    'transfer': 'Transferências'
                }
                
                mapped_category_name = category_mapping.get(pluggy_category.lower())
                if mapped_category_name:
                    # Buscar categoria no nosso sistema
                    from django.db import models
                    category = TransactionCategory.objects.filter(
                        name__iexact=mapped_category_name
                    ).first()
                    
                    if category:
                        logger.info(f"✅ Mapped Pluggy category '{pluggy_category}' to '{category.name}'")
                        return category
                    else:
                        logger.warning(f"⚠️ Category '{mapped_category_name}' not found in our system")
                else:
                    logger.info(f"ℹ️ Pluggy category '{pluggy_category}' not mapped")
            
            # Se chegou até aqui, não conseguiu mapear
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting Pluggy category: {e}")
            return None
    
    async def _update_account_sync_time(self, account: BankAccount):
        """Update account last sync time"""
        @sync_to_async
        def update_sync_time():
            BankAccount.objects.filter(id=account.id).update(
                last_sync_at=timezone.now()
            )
        
        await update_sync_time()
    
    async def _update_account_balance(self, account: BankAccount):
        """Update account balance from Pluggy"""
        try:
            # ✅ CORRIGIDO: Buscar external_id de forma assíncrona
            external_id = await sync_to_async(lambda: account.external_id)()
            
            async with PluggyClient() as client:
                account_data = await client.get_account(external_id)
                
                if account_data:
                    current_balance = Decimal(str(account_data.get('balance', '0')))
                    
                    @sync_to_async
                    def update_balance():
                        BankAccount.objects.filter(id=account.id).update(
                            current_balance=current_balance,
                            available_balance=current_balance  # Pluggy provides one balance
                        )
                    
                    await update_balance()
                    logger.info(f"💰 Updated balance for account {account.id}: R$ {current_balance}")
                    
        except Exception as e:
            logger.error(f"❌ Error updating balance for Pluggy account {account.id}: {e}")
    
    async def _mark_account_error(self, account: BankAccount, error_type: str):
        """Mark account as having an error"""
        @sync_to_async
        def mark_error():
            status_map = {
                'auth_error': 'error',
                'connection_error': 'error',
                'expired': 'expired'
            }
            status = status_map.get(error_type, 'error')
            
            BankAccount.objects.filter(id=account.id).update(
                status=status
            )
        
        await mark_error()
        logger.warning(f"⚠️ Marked Pluggy account {account.id} as {error_type}")


# Global service instance
pluggy_sync_service = PluggyTransactionSyncService()