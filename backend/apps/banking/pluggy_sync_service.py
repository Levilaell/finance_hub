"""
Pluggy Sync Service - Handles data synchronization with Pluggy API
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.utils.text import slugify

from .models import (
    PluggyConnector, PluggyItem, BankAccount, Transaction, 
    TransactionCategory, PluggyCategory, ItemWebhook
)
from .integrations.pluggy.client import PluggyClient, PluggyError, format_pluggy_date

logger = logging.getLogger('apps.banking.pluggy_sync_service')


class PluggySyncService:
    """
    Service for synchronizing data between our database and Pluggy API
    """
    
    def __init__(self):
        self.client = PluggyClient()
    
    # === CONNECTOR SYNC ===
    
    def sync_connectors(self, include_sandbox: bool = False) -> Dict:
        """Sync connectors from Pluggy API"""
        
        logger.info("Starting connector sync")
        stats = {
            'total_fetched': 0,
            'created': 0,
            'updated': 0,
            'errors': []
        }
        
        try:
            with self.client:
                connectors_data = self.client.get_connectors()
                stats['total_fetched'] = len(connectors_data)
                
                for connector_data in connectors_data:
                    # Skip sandbox if not requested
                    if connector_data.get('sandbox', False) and not include_sandbox:
                        continue
                    
                    try:
                        self._sync_connector(connector_data, stats)
                    except Exception as e:
                        error_msg = f"Failed to sync connector {connector_data.get('id')}: {e}"
                        logger.error(error_msg)
                        stats['errors'].append(error_msg)
                        
        except PluggyError as e:
            error_msg = f"Failed to fetch connectors: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
        
        logger.info(f"Connector sync completed: {stats}")
        return stats
    
    def _sync_connector(self, connector_data: Dict, stats: Dict):
        """Sync individual connector"""
        
        pluggy_id = connector_data['id']
        
        try:
            connector, created = PluggyConnector.objects.update_or_create(
                pluggy_id=pluggy_id,
                defaults={
                    'name': connector_data['name'],
                    'institution_url': connector_data.get('institutionUrl', ''),
                    'image_url': connector_data.get('imageUrl', ''),
                    'primary_color': connector_data.get('primaryColor', '#000000'),
                    'type': connector_data['type'],
                    'country': connector_data.get('country', 'BR'),
                    'has_mfa': connector_data.get('hasMFA', False),
                    'has_oauth': connector_data.get('oauth', False),
                    'is_open_finance': connector_data.get('isOpenFinance', False),
                    'is_sandbox': connector_data.get('sandbox', False),
                    'products': connector_data.get('products', []),
                    'credentials': connector_data.get('credentials', [])
                }
            )
            
            if created:
                stats['created'] += 1
                logger.debug(f"Created connector: {connector.name}")
            else:
                stats['updated'] += 1
                logger.debug(f"Updated connector: {connector.name}")
                
        except Exception as e:
            raise Exception(f"Database error for connector {pluggy_id}: {e}")
    
    # === ITEM SYNC ===
    
    def create_item(
        self, 
        company, 
        connector_id: int, 
        credentials: Dict,
        webhook_url: Optional[str] = None,
        products: Optional[List[str]] = None
    ) -> PluggyItem:
        """Create a new Pluggy item (bank connection)"""
        
        logger.info(f"Creating item for company {company.id} with connector {connector_id}")
        
        try:
            connector = PluggyConnector.objects.get(pluggy_id=connector_id)
        except PluggyConnector.DoesNotExist:
            raise ValueError(f"Connector {connector_id} not found")
        
        # Default products if not specified
        if not products:
            products = ['ACCOUNTS', 'TRANSACTIONS']
            if 'CREDITCARDS' in connector.products:
                products.append('CREDITCARDS')
        
        try:
            with self.client:
                item_data = self.client.create_item(
                    connector_id=connector_id,
                    credentials=credentials,
                    webhook_url=webhook_url,
                    client_user_id=str(company.id),
                    products=products
                )
            
            # Create item in our database
            item = PluggyItem.objects.create(
                company=company,
                connector=connector,
                pluggy_item_id=item_data['id'],
                client_user_id=str(company.id),
                webhook_url=webhook_url or '',
                products=products,
                status=item_data.get('status', 'CREATED'),
                execution_status=item_data.get('executionStatus'),
                pluggy_created_at=format_pluggy_date(item_data['createdAt']),
                pluggy_updated_at=format_pluggy_date(item_data['updatedAt']),
                metadata={'created_via': 'api'}
            )
            
            logger.info(f"Successfully created item {item.id} for {connector.name}")
            return item
            
        except PluggyError as e:
            logger.error(f"Failed to create item: {e}")
            raise
    
    def sync_item_status(self, item: PluggyItem) -> bool:
        """Sync item status from Pluggy"""
        
        try:
            with self.client:
                item_data = self.client.get_item(item.pluggy_item_id)
            
            # Update item status
            item.status = item_data.get('status', item.status)
            item.execution_status = item_data.get('executionStatus', item.execution_status)
            item.pluggy_updated_at = format_pluggy_date(item_data['updatedAt'])
            
            # Handle errors
            if item_data.get('error'):
                item.error_code = item_data['error'].get('code', '')
                item.error_message = item_data['error'].get('message', '')
            
            # Update last successful update if status is good
            if item.status in ['UPDATED', 'UPDATING']:
                item.last_successful_update = timezone.now()
            
            item.save()
            
            logger.debug(f"Updated item {item.id} status to {item.status}")
            return True
            
        except PluggyError as e:
            logger.error(f"Failed to sync item status for {item.id}: {e}")
            return False
    
    def delete_item(self, item: PluggyItem) -> bool:
        """Delete item from Pluggy and mark as inactive"""
        
        try:
            with self.client:
                self.client.delete_item(item.pluggy_item_id)
            
            # Soft delete - mark accounts as inactive
            item.accounts.update(is_active=False)
            
            # Mark item as deleted
            item.delete()
            
            logger.info(f"Successfully deleted item {item.id}")
            return True
            
        except PluggyError as e:
            logger.error(f"Failed to delete item {item.id}: {e}")
            return False
    
    # === ACCOUNT SYNC ===
    
    def sync_accounts(self, item: PluggyItem) -> Dict:
        """Sync accounts for a Pluggy item"""
        
        logger.info(f"Syncing accounts for item {item.id}")
        stats = {
            'fetched': 0,
            'created': 0,
            'updated': 0,
            'errors': []
        }
        
        try:
            with self.client:
                accounts_data = self.client.get_accounts(item.pluggy_item_id)
                stats['fetched'] = len(accounts_data)
                
                for account_data in accounts_data:
                    try:
                        self._sync_account(item, account_data, stats)
                    except Exception as e:
                        error_msg = f"Failed to sync account {account_data.get('id')}: {e}"
                        logger.error(error_msg)
                        stats['errors'].append(error_msg)
                        
        except PluggyError as e:
            error_msg = f"Failed to fetch accounts for item {item.id}: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
        
        logger.info(f"Account sync completed for item {item.id}: {stats}")
        return stats
    
    def _sync_account(self, item: PluggyItem, account_data: Dict, stats: Dict):
        """Sync individual account"""
        
        pluggy_account_id = account_data['id']
        
        try:
            # Prepare account data
            defaults = {
                'type': account_data['type'],
                'subtype': account_data.get('subtype', ''),
                'number': account_data.get('number', ''),
                'name': account_data.get('name', ''),
                'marketing_name': account_data.get('marketingName'),
                'owner': account_data.get('owner'),
                'tax_number': account_data.get('taxNumber'),
                'balance': Decimal(str(account_data.get('balance', 0))),
                'balance_in_account_currency': None,
                'currency_code': account_data.get('currencyCode', 'BRL'),
                'is_active': True,
                'pluggy_created_at': format_pluggy_date(account_data['createdAt']),
                'pluggy_updated_at': format_pluggy_date(account_data['updatedAt']),
            }
            
            # Handle balance in account currency
            if account_data.get('balanceInAccountCurrency'):
                defaults['balance_in_account_currency'] = Decimal(
                    str(account_data['balanceInAccountCurrency'])
                )
            
            # Handle balance date
            if account_data.get('balanceDate'):
                defaults['balance_date'] = format_pluggy_date(account_data['balanceDate'])
            
            # Handle type-specific data
            if account_data['type'] == 'BANK':
                defaults['bank_data'] = account_data.get('bankData', {})
            elif account_data['type'] == 'CREDIT':
                defaults['credit_data'] = account_data.get('creditData', {})
            
            # Create or update account
            account, created = BankAccount.objects.update_or_create(
                company=item.company,
                pluggy_account_id=pluggy_account_id,
                defaults=defaults
            )
            
            # Update item reference if needed
            if account.item != item:
                account.item = item
                account.save(update_fields=['item'])
            
            if created:
                stats['created'] += 1
                logger.debug(f"Created account: {account.name or account.number}")
            else:
                stats['updated'] += 1
                logger.debug(f"Updated account: {account.name or account.number}")
                
        except Exception as e:
            raise Exception(f"Database error for account {pluggy_account_id}: {e}")
    
    # === TRANSACTION SYNC ===
    
    def sync_transactions(
        self, 
        account: BankAccount, 
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict:
        """Sync transactions for a bank account"""
        
        logger.info(f"Syncing transactions for account {account.id}")
        
        # Default date range: last 90 days
        if not from_date:
            from_date = timezone.now() - timedelta(days=90)
        if not to_date:
            to_date = timezone.now()
        
        stats = {
            'fetched': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            with self.client:
                transactions_data = self.client.get_all_transactions_for_account(
                    account_id=account.pluggy_account_id,
                    from_date=from_date,
                    to_date=to_date
                )
                stats['fetched'] = len(transactions_data)
                
                # Process in batches to avoid memory issues
                batch_size = 100
                for i in range(0, len(transactions_data), batch_size):
                    batch = transactions_data[i:i + batch_size]
                    self._sync_transaction_batch(account, batch, stats)
                        
        except PluggyError as e:
            error_msg = f"Failed to fetch transactions for account {account.id}: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
        
        logger.info(f"Transaction sync completed for account {account.id}: {stats}")
        return stats
    
    def _sync_transaction_batch(self, account: BankAccount, transactions_data: List[Dict], stats: Dict):
        """Sync a batch of transactions"""
        
        with transaction.atomic():
            for transaction_data in transactions_data:
                try:
                    self._sync_transaction(account, transaction_data, stats)
                except Exception as e:
                    error_msg = f"Failed to sync transaction {transaction_data.get('id')}: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
    
    def _sync_transaction(self, account: BankAccount, transaction_data: Dict, stats: Dict):
        """Sync individual transaction"""
        
        pluggy_transaction_id = transaction_data['id']
        
        # Check if transaction already exists
        if Transaction.objects.filter(
            pluggy_transaction_id=pluggy_transaction_id,
            is_deleted=False
        ).exists():
            stats['skipped'] += 1
            return
        
        try:
            # Prepare transaction data
            defaults = {
                'company': account.company,
                'account': account,
                'type': transaction_data['type'],
                'status': transaction_data.get('status', 'POSTED'),
                'description': transaction_data['description'][:500],  # Truncate if too long
                'description_raw': transaction_data.get('descriptionRaw'),
                'amount': abs(Decimal(str(transaction_data['amount']))),
                'currency_code': transaction_data.get('currencyCode', 'BRL'),
                'date': format_pluggy_date(transaction_data['date']),
                'provider_code': transaction_data.get('providerCode', ''),
                'provider_id': transaction_data.get('providerId', ''),
                'pluggy_category_id': transaction_data.get('categoryId', ''),
                'pluggy_category_description': transaction_data.get('category', ''),
                'operation_type': transaction_data.get('operationType', ''),
                'payment_method': transaction_data.get('paymentMethod', ''),
                'pluggy_created_at': format_pluggy_date(transaction_data['createdAt']),
                'pluggy_updated_at': format_pluggy_date(transaction_data['updatedAt']),
            }
            
            # Handle optional fields
            if transaction_data.get('amountInAccountCurrency'):
                defaults['amount_in_account_currency'] = abs(Decimal(
                    str(transaction_data['amountInAccountCurrency'])
                ))
            
            if transaction_data.get('balance'):
                defaults['balance'] = Decimal(str(transaction_data['balance']))
            
            if transaction_data.get('merchant'):
                defaults['merchant'] = transaction_data['merchant']
            
            if transaction_data.get('paymentData'):
                defaults['payment_data'] = transaction_data['paymentData']
            
            if transaction_data.get('creditCardMetadata'):
                defaults['credit_card_metadata'] = transaction_data['creditCardMetadata']
            
            # Try to categorize transaction
            category = self._auto_categorize_transaction(transaction_data)
            if category:
                defaults['category'] = category
            
            # Create transaction
            transaction_obj = Transaction.objects.create(
                pluggy_transaction_id=pluggy_transaction_id,
                **defaults
            )
            
            stats['created'] += 1
            logger.debug(f"Created transaction: {transaction_obj.description}")
            
        except IntegrityError:
            # Transaction already exists (race condition)
            stats['skipped'] += 1
        except Exception as e:
            raise Exception(f"Database error for transaction {pluggy_transaction_id}: {e}")
    
    def _auto_categorize_transaction(self, transaction_data: Dict) -> Optional[TransactionCategory]:
        """Auto-categorize transaction based on Pluggy category and description"""
        
        pluggy_category_id = transaction_data.get('categoryId')
        if not pluggy_category_id:
            return None
        
        try:
            pluggy_category = PluggyCategory.objects.get(id=pluggy_category_id)
            if pluggy_category.internal_category:
                return pluggy_category.internal_category
        except PluggyCategory.DoesNotExist:
            pass
        
        # TODO: Implement ML-based categorization
        return None
    
    # === CATEGORY SYNC ===
    
    def sync_categories(self) -> Dict:
        """Sync transaction categories from Pluggy"""
        
        logger.info("Syncing Pluggy categories")
        stats = {
            'fetched': 0,
            'created': 0,
            'updated': 0,
            'errors': []
        }
        
        try:
            with self.client:
                categories_data = self.client.get_categories()
                stats['fetched'] = len(categories_data)
                
                for category_data in categories_data:
                    try:
                        self._sync_category(category_data, stats)
                    except Exception as e:
                        error_msg = f"Failed to sync category {category_data.get('id')}: {e}"
                        logger.error(error_msg)
                        stats['errors'].append(error_msg)
                        
        except PluggyError as e:
            error_msg = f"Failed to fetch categories: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
        
        logger.info(f"Category sync completed: {stats}")
        return stats
    
    def _sync_category(self, category_data: Dict, stats: Dict):
        """Sync individual Pluggy category"""
        
        category_id = category_data['id']
        
        try:
            category, created = PluggyCategory.objects.update_or_create(
                id=category_id,
                defaults={
                    'description': category_data['description'],
                    'parent_id': category_data.get('parentId'),
                    'parent_description': category_data.get('parentDescription', ''),
                }
            )
            
            if created:
                stats['created'] += 1
            else:
                stats['updated'] += 1
                
        except Exception as e:
            raise Exception(f"Database error for category {category_id}: {e}")
    
    # === FULL SYNC OPERATIONS ===
    
    def sync_item_data(self, item: PluggyItem) -> Dict:
        """Complete sync for an item (accounts + transactions)"""
        
        logger.info(f"Starting full sync for item {item.id}")
        start_time = timezone.now()
        
        result = {
            'item_id': str(item.id),
            'status': 'success',
            'accounts_synced': 0,
            'transactions_synced': 0,
            'new_transactions': 0,
            'updated_transactions': 0,
            'errors': [],
            'sync_duration': 0
        }
        
        try:
            # Update item status first
            if not self.sync_item_status(item):
                result['status'] = 'failed'
                result['errors'].append('Failed to sync item status')
                return result
            
            # Check if item is in a good state for syncing
            if not item.is_connected:
                result['status'] = 'skipped'
                result['errors'].append(f'Item status is {item.status}, cannot sync')
                return result
            
            # Sync accounts
            account_stats = self.sync_accounts(item)
            result['accounts_synced'] = account_stats['created'] + account_stats['updated']
            result['errors'].extend(account_stats['errors'])
            
            # Sync transactions for each account
            total_transactions = 0
            for account in item.accounts.filter(is_active=True):
                transaction_stats = self.sync_transactions(account)
                total_transactions += transaction_stats['created']
                result['errors'].extend(transaction_stats['errors'])
            
            result['new_transactions'] = total_transactions
            result['transactions_synced'] = total_transactions
            
            # Update last successful sync
            item.last_successful_update = timezone.now()
            item.save(update_fields=['last_successful_update'])
            
            if result['errors']:
                result['status'] = 'partial'
            
        except Exception as e:
            logger.error(f"Full sync failed for item {item.id}: {e}")
            result['status'] = 'failed'
            result['errors'].append(str(e))
        
        # Calculate duration
        end_time = timezone.now()
        result['sync_duration'] = (end_time - start_time).total_seconds()
        
        logger.info(f"Full sync completed for item {item.id}: {result['status']}")
        return result
    
    def sync_company_data(self, company) -> Dict:
        """Sync all data for a company"""
        
        logger.info(f"Starting company sync for {company.id}")
        start_time = timezone.now()
        
        result = {
            'total_items': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'sync_results': [],
            'total_duration': 0
        }
        
        items = PluggyItem.objects.filter(company=company)
        result['total_items'] = items.count()
        
        for item in items:
            sync_result = self.sync_item_data(item)
            result['sync_results'].append(sync_result)
            
            if sync_result['status'] == 'success':
                result['successful_syncs'] += 1
            else:
                result['failed_syncs'] += 1
        
        # Calculate total duration
        end_time = timezone.now()
        result['total_duration'] = (end_time - start_time).total_seconds()
        
        logger.info(f"Company sync completed for {company.id}: {result}")
        return result
    
    # === HELPER METHODS ===
    
    def get_sync_status(self, item: PluggyItem) -> Dict:
        """Get current sync status for an item"""
        
        return {
            'item_id': str(item.id),
            'status': item.status,
            'execution_status': item.execution_status,
            'is_connected': item.is_connected,
            'has_error': item.has_error,
            'needs_user_action': item.needs_user_action,
            'last_successful_update': item.last_successful_update,
            'error_message': item.error_message,
            'account_count': item.accounts.filter(is_active=True).count(),
            'transaction_count': Transaction.objects.filter(
                account__item=item,
                is_deleted=False
            ).count()
        }
    
    def create_default_categories(self, company) -> List[TransactionCategory]:
        """Create default transaction categories for a company"""
        
        logger.info(f"Creating default categories for company {company.id}")
        
        default_categories = [
            # Income categories
            {'name': 'Salário', 'type': 'income', 'icon': '💰', 'color': '#22c55e'},
            {'name': 'Freelance', 'type': 'income', 'icon': '💼', 'color': '#3b82f6'},
            {'name': 'Investimentos', 'type': 'income', 'icon': '📈', 'color': '#8b5cf6'},
            {'name': 'Outras Receitas', 'type': 'income', 'icon': '💵', 'color': '#10b981'},
            
            # Expense categories
            {'name': 'Alimentação', 'type': 'expense', 'icon': '🍔', 'color': '#f59e0b'},
            {'name': 'Transporte', 'type': 'expense', 'icon': '🚗', 'color': '#ef4444'},
            {'name': 'Moradia', 'type': 'expense', 'icon': '🏠', 'color': '#6366f1'},
            {'name': 'Saúde', 'type': 'expense', 'icon': '💊', 'color': '#ec4899'},
            {'name': 'Educação', 'type': 'expense', 'icon': '🎓', 'color': '#14b8a6'},
            {'name': 'Lazer', 'type': 'expense', 'icon': '🎬', 'color': '#f43f5e'},
            {'name': 'Compras', 'type': 'expense', 'icon': '🛒', 'color': '#a78bfa'},
            {'name': 'Contas e Impostos', 'type': 'expense', 'icon': '📄', 'color': '#64748b'},
            {'name': 'Outras Despesas', 'type': 'expense', 'icon': '💸', 'color': '#94a3b8'},
            
            # Transfer categories
            {'name': 'Transferências', 'type': 'transfer', 'icon': '🔄', 'color': '#6b7280'},
        ]
        
        created_categories = []
        
        for cat_data in default_categories:
            slug = slugify(f"{company.id}-{cat_data['name']}")
            
            category, created = TransactionCategory.objects.get_or_create(
                company=company,
                name=cat_data['name'],
                defaults={
                    'slug': slug,
                    'type': cat_data['type'],
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'is_system': True,
                    'order': len(created_categories)
                }
            )
            
            if created:
                created_categories.append(category)
        
        logger.info(f"Created {len(created_categories)} default categories for company {company.id}")
        return created_categories