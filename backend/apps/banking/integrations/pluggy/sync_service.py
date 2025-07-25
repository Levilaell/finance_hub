"""
Async service for transaction synchronization with Pluggy API
"""
import asyncio
from .category_mapper import pluggy_category_mapper

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
import json

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from ...models import BankAccount, Transaction, TransactionCategory, BankProvider
from .client import PluggyClient, PluggyError

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
    
    async def force_item_update(self, item_id: str) -> Dict[str, Any]:
        """Force a Pluggy item to update
        
        This triggers Pluggy to fetch the latest data from the bank.
        Should be called before syncing to ensure we get the most recent transactions.
        """
        try:
            async with PluggyClient() as client:
                logger.info(f"🔄 Forcing update for Pluggy item {item_id}")
                
                # First check item status
                item = await client.get_item(item_id)
                current_status = item.get('status')
                logger.info(f"📋 Current item status: {current_status}")
                
                # Check if it's Open Finance
                is_open_finance = item.get('connector', {}).get('isOpenFinance', False)
                logger.info(f"📊 Is Open Finance: {is_open_finance}")
                
                if current_status not in ['ACTIVE', 'UPDATED', 'OUTDATED']:
                    logger.warning(f"⚠️ Cannot update item in status {current_status}")
                    return {
                        'success': False,
                        'status': current_status,
                        'message': f'Item must be ACTIVE, UPDATED or OUTDATED to force update, current status: {current_status}'
                    }
                
                # Check for Open Finance rate limits
                if is_open_finance and item.get('statusDetail'):
                    for product, details in item['statusDetail'].items():
                        if isinstance(details, dict) and details.get('warnings'):
                            for warning in details['warnings']:
                                if '423' in str(warning.get('code', '')) or 'rate limit' in str(warning).lower():
                                    logger.warning(f"⚠️ Rate limit reached for {product}")
                                    return {
                                        'success': False,
                                        'status': 'rate_limited',
                                        'message': f'Rate limit reached for {product}. Try again next month.',
                                        'product': product
                                    }
                
                # Use the sync_item method to trigger update
                update_response = await client.sync_item(item_id)
                
                new_status = update_response.get('status')
                logger.info(f"✅ Item update triggered, new status: {new_status}")
                
                return {
                    'success': True,
                    'status': new_status,
                    'previous_status': current_status,
                    'item_id': item_id,
                    'is_open_finance': is_open_finance
                }
                
        except Exception as e:
            logger.error(f"❌ Error forcing item update: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def sync_account_transactions(self, account: BankAccount, force_extended_window: bool = False) -> Dict[str, Any]:
        """Sync transactions for a specific Pluggy account
        
        IMPORTANTE: A API da Pluggy pode ter um delay de alguns minutos para disponibilizar
        transações muito recentes. Por isso, usamos janelas de tempo maiores em syncs frequentes
        para garantir que pegamos todas as transações, mesmo as que foram processadas com delay.
        """
        try:
            # Get account info asynchronously
            account_info = await self._get_account_info(account)
            
            logger.info(f"🔄 Syncing Pluggy account {account_info['id']} - {account_info['bank_name']}")
            
            if not account_info['external_id']:
                logger.warning(f"❌ No Pluggy account ID for account {account_info['id']}")
                return {'account_id': account_info['id'], 'status': 'no_external_id', 'transactions': 0}
            
            # Check if it's Open Finance
            is_open_finance = account_info.get('metadata', {}).get('is_open_finance', False)
            logger.info(f"📊 Open Finance account: {is_open_finance}")
            
            # Check item status before syncing
            pluggy_item_id = await sync_to_async(lambda: account.pluggy_item_id)()
            if pluggy_item_id:
                try:
                    async with PluggyClient() as client:
                        item = await client.get_item(pluggy_item_id)
                        item_status = item.get('status')
                        logger.info(f"📋 Item {pluggy_item_id} status: {item_status}")
                        
                        # Check for Open Finance specific errors
                        if is_open_finance:
                            if item_status == 'USER_AUTHORIZATION_REVOKED':
                                logger.warning(f"⚠️ Open Finance consent revoked")
                                return {
                                    'account_id': account_info['id'],
                                    'status': 'consent_revoked',
                                    'message': 'Consentimento Open Finance revogado',
                                    'transactions': 0
                                }
                            
                            # Check rate limits
                            status_detail = item.get('statusDetail', {})
                            for product, details in status_detail.items():
                                if isinstance(details, dict) and not details.get('isUpdated', True):
                                    warnings = details.get('warnings', [])
                                    for warning in warnings:
                                        if '423' in str(warning.get('code', '')):
                                            logger.warning(f"⚠️ Rate limit hit for {product}")
                                            return {
                                                'account_id': account_info['id'],
                                                'status': 'rate_limited',
                                                'message': f'Limite de requisições atingido para {product}',
                                                'transactions': 0
                                            }
                        
                        if item_status == 'WAITING_USER_ACTION':
                            logger.warning(f"⚠️ Item requires user action, cannot sync")
                            return {
                                'account_id': account_info['id'], 
                                'status': 'waiting_user_action',
                                'message': 'Item requires user authentication',
                                'transactions': 0
                            }
                        elif item_status == 'LOGIN_ERROR':
                            logger.warning(f"⚠️ Item has login error")
                            return {
                                'account_id': account_info['id'],
                                'status': 'login_error', 
                                'message': 'Invalid credentials',
                                'transactions': 0
                            }
                        elif item_status == 'OUTDATED':
                            # Don't try to update OUTDATED items automatically
                            # as it may trigger WAITING_USER_ACTION
                            logger.warning(f"⚠️ Item is OUTDATED but continuing with sync")
                            logger.info(f"📝 Note: New transactions may not be available until item is updated")
                except Exception as e:
                    logger.warning(f"⚠️ Could not check item status: {e}")
            
            # Determine sync date range (different for Open Finance)
            sync_from = self._get_sync_from_date_safe(account_info, force_extended_window, is_open_finance)
            # Buscar 1 dia no futuro para pegar transações com timezone issues
            sync_to = (timezone.now() + timedelta(days=1)).date()
            
            logger.info(f"📅 Syncing transactions from {sync_from} to {sync_to} (incluindo 1 dia futuro para timezone)")
            
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
                        
                        # Rate limiting between pages (slower for Open Finance)
                        if is_open_finance:
                            await asyncio.sleep(0.5)
                        else:
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
            
            # Clear any error status
            await sync_to_async(lambda: BankAccount.objects.filter(id=account.id).update(
                sync_status='active',
                sync_error_message=''
            ))()
            
            # Update account balance
            await self._update_account_balance(account)
            
            # Always update transaction counter to ensure accuracy
            logger.info(f"📊 Calling _update_transaction_counter for account {account.id}")
            try:
                await self._update_transaction_counter(account, total_transactions)
            except Exception as e:
                logger.error(f"❌ Error updating transaction counter: {e}", exc_info=True)
            
            logger.info(f"✅ Synced {total_transactions} transactions for Pluggy account {account_info['id']}")
            
            # Adicionar informações sobre a janela de tempo usada
            sync_info = {
                'account_id': account_info['id'],
                'status': 'success',
                'transactions': total_transactions,
                'sync_from': sync_from.isoformat(),
                'sync_to': sync_to.isoformat(),
                'days_searched': (sync_to - sync_from).days,
                'is_open_finance': is_open_finance
            }
            
            # Se não encontrou transações, adicionar mensagem informativa
            if total_transactions == 0:
                if pluggy_item_id:
                    try:
                        async with PluggyClient() as client:
                            item = await client.get_item(pluggy_item_id)
                            item_status = item.get('status')
                            if item_status == 'OUTDATED':
                                sync_info['message'] = 'Nenhuma transação nova encontrada. A conexão com o banco pode estar desatualizada.'
                                sync_info['item_status'] = item_status
                            else:
                                sync_info['message'] = f'Nenhuma transação nova nos últimos {(sync_to - sync_from).days} dias.'
                    except:
                        sync_info['message'] = f'Nenhuma transação nova nos últimos {(sync_to - sync_from).days} dias.'
                else:
                    sync_info['message'] = f'Nenhuma transação nova nos últimos {(sync_to - sync_from).days} dias.'
            
            return sync_info
            
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
            'last_sync_at': account_with_provider.last_sync_at,
            'metadata': account_with_provider.metadata or {}
        }
    
    def _get_sync_from_date_safe(self, account_info: Dict, force_extended_window: bool = False, is_open_finance: bool = False) -> datetime.date:
        """Determine the date to sync from using account info dict"""
        last_sync = account_info.get('last_sync_at')
        
        if not last_sync:
            # PRIMEIRA SYNC: período baseado no modo e tipo de conector
            if is_open_finance:
                days = 365  # Open Finance suporta 1 ano completo
                logger.info(f"🏛️ Open Finance: First sync, using {days} days")
            else:
                sandbox_mode = getattr(settings, 'PLUGGY_USE_SANDBOX', False)
                if sandbox_mode:
                    days = 365  # 1 ano para sandbox
                    logger.info(f"🧪 Sandbox: First sync, using {days} days")
                else:
                    days = 90   # 3 meses em produção/trial
                    logger.info(f"🚀 Production/Trial: First sync, using {days} days")
            
            return (timezone.now() - timedelta(days=days)).date()
        else:
            # SYNC INCREMENTAL: janela maior para capturar transações recentes
            days_since_sync = (timezone.now() - last_sync).days
            hours_since_sync = (timezone.now() - last_sync).total_seconds() / 3600
            
            # Se forçar janela estendida (sync manual), usar período maior
            if force_extended_window:
                days_back = 30  # Sempre buscar 30 dias em sync manual
                logger.info(f"🔄 Manual sync requested, using extended {days_back} days window")
                return (timezone.now() - timedelta(days=days_back)).date()
            
            # Open Finance: considerar limites de rate
            if is_open_finance:
                # Para Open Finance, ser mais conservador com syncs frequentes
                if hours_since_sync < 24:
                    days_back = 1  # Só buscar 1 dia se sincronizou hoje
                    logger.info(f"🏛️ Open Finance: Recent sync, using minimal {days_back} day window")
                elif days_since_sync <= 7:
                    days_back = 7  # Buscar 7 dias se sincronizou na última semana
                    logger.info(f"🏛️ Open Finance: Weekly sync, using {days_back} days window")
                else:
                    days_back = 30  # Máximo de 30 dias para não gastar rate limit
                    logger.info(f"🏛️ Open Finance: Monthly sync, using {days_back} days window")
                
                return (timezone.now() - timedelta(days=days_back)).date()
            
            # Conectores diretos (não Open Finance)
            if days_since_sync > 30:
                # Se muito tempo sem sync, buscar 30 dias para não perder nada
                logger.info(f"⚠️ Long gap ({days_since_sync} days), using 30 days")
                return (timezone.now() - timedelta(days=30)).date()
            else:
                # OTIMIZAÇÃO: Buscar desde a última sincronização com margem de segurança
                # Margem de 2 dias para cobrir:
                # - Transações com data retroativa
                # - Delays de processamento da Pluggy
                # - Diferenças de timezone
                # - Finais de semana e feriados
                margin_days = 2
                
                # Se sincronizou há menos de 1 dia, usar janela mínima de 3 dias
                if hours_since_sync < 24:
                    days_back = 3
                    logger.info(f"📅 Recent sync ({hours_since_sync:.1f} hours ago), using minimum {days_back} days window")
                else:
                    # Buscar desde a última sync + margem
                    days_back = days_since_sync + margin_days
                    logger.info(f"📅 Incremental sync: {days_since_sync} days since last sync + {margin_days} days margin = {days_back} days window")
                
                return (timezone.now() - timedelta(days=days_back)).date()

    async def _get_accounts_to_sync(self, company_id: int = None) -> List[BankAccount]:
        """Get Pluggy accounts that need synchronization"""
        @sync_to_async
        def get_accounts():
            from django.db import models
            
            queryset = BankAccount.objects.filter(
                status='active',
                external_id__isnull=False,
                # Filter for Pluggy accounts (have external_id)
                external_id__startswith=''  # Pluggy IDs são UUIDs
            ).select_related('bank_provider', 'company')
            
            if company_id:
                queryset = queryset.filter(company_id=company_id)
            
            # Only sync accounts that haven't been synced recently
            # Different intervals for Open Finance vs Direct connectors
            cutoff_time_direct = timezone.now() - timedelta(hours=2)  # Direct connectors: 2 hours
            cutoff_time_of = timezone.now() - timedelta(hours=24)    # Open Finance: 24 hours
            
            # Separate query for Open Finance and Direct connectors
            direct_accounts = queryset.filter(
                metadata__is_open_finance__isnull=True
            ).filter(
                models.Q(last_sync_at__isnull=True) |
                models.Q(last_sync_at__lt=cutoff_time_direct)
            )
            
            of_accounts = queryset.filter(
                metadata__is_open_finance=True
            ).filter(
                models.Q(last_sync_at__isnull=True) |
                models.Q(last_sync_at__lt=cutoff_time_of)
            )
            
            # Combine both querysets
            all_accounts = list(direct_accounts) + list(of_accounts)
            
            return all_accounts
        
        return await get_accounts()
    
    async def _process_transaction_batch(self, account: BankAccount, transactions: List[Dict]) -> int:
        """Process a batch of Pluggy transactions"""
        @sync_to_async
        def save_transactions():
            created_count = 0
            
            logger.info(f"🔍 Processing batch of {len(transactions)} transactions")
            
            with transaction.atomic():
                for idx, tx_data in enumerate(transactions):
                    # Check if transaction already exists
                    external_id = tx_data.get('id')
                    if not external_id:
                        logger.warning(f"Transaction #{idx} has no ID, skipping")
                        continue
                    
                    # Log transaction details
                    tx_date = tx_data.get('date', 'no date')
                    tx_desc = tx_data.get('description', 'no description')[:50]
                    tx_amount = tx_data.get('amount', 0)
                    logger.info(f"📝 Transaction #{idx}: ID={external_id}, Date={tx_date}, Amount={tx_amount}, Desc='{tx_desc}'")
                    
                    # Pluggy uses string IDs
                    if Transaction.objects.filter(
                        bank_account=account,
                        external_id=str(external_id)
                    ).exists():
                        logger.info(f"⏭️  Transaction {external_id} already exists, skipping")
                        continue
                    
                    # Create transaction
                    tx = self._create_transaction_from_pluggy_data(account, tx_data)
                    if tx:
                        created_count += 1
                        logger.info(f"✅ Created new transaction: {external_id} - {tx.description} - R$ {tx.amount}")
                    else:
                        logger.warning(f"❌ Failed to create transaction: {external_id}")
            
            logger.info(f"📊 Batch processing complete: {created_count} new transactions created out of {len(transactions)} total")
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
                
                # Categorização com dados da Pluggy
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
                
                # Build metadata with Open Finance specific fields
                metadata = {
                    'pluggy_category': tx_data.get('category'),
                    'payment_method': tx_data.get('paymentMethod'),
                    'merchant': merchant_info,
                    'operation_type': tx_data.get('operationType'),  # Open Finance
                    'provider_id': tx_data.get('providerId')  # Open Finance
                }
                
                # Add payment data if available (Open Finance)
                payment_data = tx_data.get('paymentData')
                if payment_data:
                    metadata['payment_data'] = payment_data
                    # Extract counterpart info
                    if payment_data.get('receiver', {}).get('name'):
                        merchant_name = payment_data['receiver']['name']
                    elif payment_data.get('payer', {}).get('name'):
                        merchant_name = payment_data['payer']['name']
                
                # Add credit card metadata if available
                credit_card_metadata = tx_data.get('creditCardMetadata')
                if credit_card_metadata:
                    metadata['credit_card_metadata'] = credit_card_metadata
                
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
                    category=category,  # Categoria da Pluggy ou None
                    status='completed' if tx_data.get('status') == 'POSTED' else 'pending',
                    created_at=timezone.now(),
                    metadata=metadata
                )
                
                category_name = category.name if category else 'Uncategorized'
                logger.info(f"✅ Transaction created: ID={transaction_obj.id}, Description='{transaction_obj.description}', Category='{category_name}'")
                
                return transaction_obj
                
            except Exception as e:
                logger.error(f"❌ Error creating transaction from Pluggy data: {e}", exc_info=True)
                logger.error(f"❌ Transaction data that failed: {tx_data}")
                return None

    def _get_pluggy_category(self, tx_data: Dict) -> Optional['TransactionCategory']:
        """Get category from Pluggy data using mapper"""
        try:
            # Pluggy envia a categoria no campo 'category'
            pluggy_category = tx_data.get('category')
            
            # Log detalhado para debug
            logger.info(f"🔍 Looking for Pluggy category in transaction data...")
            logger.info(f"📦 Transaction data keys: {list(tx_data.keys())}")
            logger.info(f"🏷️ Category field value: '{pluggy_category}'")
            
            # Verificar também se há categoria em outros campos possíveis
            if not pluggy_category:
                # Tentar campos alternativos
                pluggy_category = tx_data.get('categoryId') or tx_data.get('categoryName')
                if pluggy_category:
                    logger.info(f"🔄 Found category in alternative field: '{pluggy_category}'")
            
            if not pluggy_category:
                logger.info(f"❌ No category field found in Pluggy data")
                return None
                
            # Determinar tipo da transação
            transaction_type = 'credit' if tx_data.get('type') == 'CREDIT' else 'debit'
            
            # Usar o mapper
            category = pluggy_category_mapper.map_category(
                pluggy_category, 
                transaction_type
            )
            
            if category:
                logger.info(f"✅ Mapped Pluggy category '{pluggy_category}' to '{category.name}'")
            else:
                logger.info(f"❓ No mapping for Pluggy category '{pluggy_category}'")
                # Tentar criar uma nova categoria se não encontrar mapeamento
                category = pluggy_category_mapper.get_or_create_category(
                    pluggy_category,
                    transaction_type
                )
                if category:
                    logger.info(f"🆕 Created new category from Pluggy: '{category.name}'")
                
            return category
            
        except Exception as e:
            logger.error(f"❌ Error getting Pluggy category: {e}")
            return None
    
    async def _update_account_sync_time(self, account: BankAccount):
        """Update account last sync time"""
        @sync_to_async
        def update_sync_time():
            now = timezone.now()
            rows_updated = BankAccount.objects.filter(id=account.id).update(
                last_sync_at=now
            )
            logger.info(f"🕐 Updated last_sync_at to {now} for account {account.id} (rows updated: {rows_updated})")
            return rows_updated
        
        rows_updated = await update_sync_time()
        if rows_updated == 0:
            logger.warning(f"⚠️ Failed to update last_sync_at for account {account.id}")
        
        # Also refresh the account instance to ensure it has the latest data
        await sync_to_async(account.refresh_from_db)()
    
    async def _update_account_balance(self, account: BankAccount):
        """Update account balance from Pluggy"""
        try:
            # Get external_id asynchronously
            external_id = await sync_to_async(lambda: account.external_id)()
            
            async with PluggyClient() as client:
                account_data = await client.get_account(external_id)
                
                if account_data:
                    current_balance = Decimal(str(account_data.get('balance', '0')))
                    
                    # For credit cards, also get available limit
                    available_balance = current_balance
                    if account_data.get('creditData'):
                        credit_data = account_data['creditData']
                        available_limit = credit_data.get('availableCreditLimit', 0)
                        available_balance = Decimal(str(available_limit))
                    
                    @sync_to_async
                    def update_balance():
                        BankAccount.objects.filter(id=account.id).update(
                            current_balance=current_balance,
                            available_balance=available_balance
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
                'expired': 'expired',
                'consent_revoked': 'consent_revoked'
            }
            status = status_map.get(error_type, 'error')
            
            BankAccount.objects.filter(id=account.id).update(
                status=status
            )
        
        await mark_error()
        logger.warning(f"⚠️ Marked Pluggy account {account.id} as {error_type}")
    
    async def _update_transaction_counter(self, account: BankAccount, new_transactions: int):
        """Update company transaction counter after sync"""
        @sync_to_async
        def update_counter():
            from apps.companies.models import Company, ResourceUsage
            from ....models import Transaction
            from django.utils import timezone
            from datetime import datetime
            
            company = account.company
            if not company:
                logger.warning(f"⚠️ No company found for account {account.id}")
                return
            
            # Get current month start
            now = timezone.now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Count ALL transactions for current month based on transaction_date
            # This ensures we have the correct total even if transactions were imported out of order
            current_month_count = Transaction.objects.filter(
                bank_account__company=company,
                transaction_date__gte=month_start
            ).count()
            
            logger.info(f"📊 Recalculating transaction counter for {company.name}")
            logger.info(f"   - Previous count: {company.current_month_transactions}")
            logger.info(f"   - New total count: {current_month_count}")
            logger.info(f"   - New transactions in this sync: {new_transactions}")
            
            # Update company counter with actual count
            if company.current_month_transactions != current_month_count:
                company.current_month_transactions = current_month_count
                company.save(update_fields=['current_month_transactions'])
                logger.info(f"✅ Updated company counter to {current_month_count}")
            
            # Update ResourceUsage with actual count
            usage = ResourceUsage.get_or_create_current_month(company)
            if usage.transactions_count != current_month_count:
                usage.transactions_count = current_month_count
                usage.save(update_fields=['transactions_count'])
                logger.info(f"✅ Updated ResourceUsage counter to {current_month_count}")
            
            # Check if limit reached
            limit_reached, usage_info = company.check_plan_limits('transactions')
            if limit_reached:
                logger.warning(f"⚠️ Transaction limit reached for company {company.name}: {usage_info}")
            elif company.subscription_plan:
                usage_percentage = company.get_usage_percentage('transactions')
                if usage_percentage >= 90:
                    logger.warning(f"⚠️ High usage alert: {usage_percentage:.1f}% of transaction limit used")
                elif usage_percentage >= 80:
                    logger.info(f"📈 Usage at {usage_percentage:.1f}% of transaction limit")
        
        await update_counter()


# Global service instance
pluggy_sync_service = PluggyTransactionSyncService()