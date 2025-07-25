"""
Celery tasks for banking app - Pluggy Integration
Handles async processing of bank data synchronization
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict

from celery import shared_task
from django.db import transaction as db_transaction
from django.utils import timezone

from .models import (
    PluggyItem, BankAccount, Transaction,
    TransactionCategory, ItemWebhook, PluggyCategory
)
from .integrations.pluggy.client import PluggyClient, PluggyError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_bank_account(self, item_id: str, account_id: Optional[str] = None):
    """
    Sync bank account data from Pluggy
    
    Args:
        item_id: PluggyItem ID
        account_id: Optional specific account ID to sync
    """
    try:
        item = PluggyItem.objects.get(id=item_id)
        logger.info(f"Starting sync for item {item.pluggy_id}")
        
        with PluggyClient() as client:
            # Update item status
            item_data = client.get_item(item.pluggy_id)
            
            # Update item
            item.status = item_data['status']
            item.execution_status = item_data.get('executionStatus', '')
            item.updated_at = item_data['updatedAt']
            item.status_detail = item_data.get('statusDetail', {})
            
            if item_data.get('error'):
                item.error_code = item_data['error'].get('code', '')
                item.error_message = item_data['error'].get('message', '')
            
            item.save()
            
            # Check if we can sync
            if item.status not in ['UPDATED', 'OUTDATED']:
                logger.warning(f"Item {item.pluggy_id} not ready for sync: {item.status}")
                return {
                    'success': False,
                    'reason': f'Item status: {item.status}'
                }
            
            # Get accounts to sync
            if account_id:
                accounts = BankAccount.objects.filter(
                    id=account_id,
                    item=item
                )
            else:
                accounts = item.accounts.filter(is_active=True)
            
            # Sync each account
            sync_results = []
            
            for account in accounts:
                result = _sync_account(client, account)
                sync_results.append(result)
            
            # Update last successful update
            if any(r['success'] for r in sync_results):
                item.last_successful_update = timezone.now()
                item.save()
            
            return {
                'success': True,
                'item_id': str(item.id),
                'accounts_synced': len(sync_results),
                'results': sync_results
            }
            
    except PluggyItem.DoesNotExist:
        logger.error(f"Item {item_id} not found")
        return {'success': False, 'error': 'Item not found'}
        
    except PluggyError as e:
        logger.error(f"Pluggy API error: {e}")
        # Retry for temporary errors
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        return {'success': False, 'error': str(e)}
        
    except Exception as e:
        logger.error(f"Unexpected error syncing item {item_id}: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


def _sync_account(client: PluggyClient, account: BankAccount) -> Dict:
    """
    Sync single account data
    """
    try:
        logger.info(f"Syncing account {account.pluggy_id}")
        
        # Update account info
        account_data = client.get_account(account.pluggy_id)
        
        account.balance = Decimal(str(account_data.get('balance', 0)))
        account.balance_date = timezone.now()
        account.updated_at = account_data.get('updatedAt')
        
        if account_data.get('bankData'):
            account.bank_data = account_data['bankData']
        if account_data.get('creditData'):
            account.credit_data = account_data['creditData']
        
        account.save()
        
        # Sync transactions
        transactions_synced = _sync_transactions(client, account)
        
        return {
            'success': True,
            'account_id': str(account.id),
            'balance': float(account.balance),
            'transactions_synced': transactions_synced
        }
        
    except Exception as e:
        logger.error(f"Error syncing account {account.pluggy_id}: {e}")
        return {
            'success': False,
            'account_id': str(account.id),
            'error': str(e)
        }


def _sync_transactions(client: PluggyClient, account: BankAccount) -> int:
    """
    Sync transactions for an account
    """
    # Determine sync period
    last_transaction = account.transactions.order_by('-date').first()
    
    if last_transaction:
        # Sync from last transaction date minus 7 days (for updates)
        from_date = last_transaction.date - timedelta(days=7)
    else:
        # Initial sync - get last 365 days for Open Finance, 90 for others
        days_back = 365 if account.item.connector.is_open_finance else 90
        from_date = timezone.now() - timedelta(days=days_back)
    
    to_date = timezone.now()
    
    logger.info(
        f"Syncing transactions for {account.pluggy_id} "
        f"from {from_date.date()} to {to_date.date()}"
    )
    
    # Fetch transactions
    page = 1
    total_synced = 0
    
    while True:
        try:
            result = client.get_transactions(
                account.pluggy_id,
                from_date=from_date,
                to_date=to_date,
                page=page
            )
            
            transactions = result.get('results', [])
            if not transactions:
                break
            
            # Process transactions
            with db_transaction.atomic():
                for trans_data in transactions:
                    transaction, created = _process_transaction(account, trans_data)
                    if created:
                        total_synced += 1
            
            # Check if more pages
            if page >= result.get('totalPages', 1):
                break
                
            page += 1
            
        except Exception as e:
            logger.error(f"Error fetching transactions page {page}: {e}")
            break
    
    logger.info(f"Synced {total_synced} new transactions for {account.pluggy_id}")
    return total_synced


def _process_transaction(account: BankAccount, trans_data: Dict):
    """
    Process single transaction
    """
    # Parse date
    date_str = trans_data.get('date')
    if date_str:
        trans_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    else:
        trans_date = timezone.now()
    
    # Get category
    category = None
    if trans_data.get('category'):
        category = _get_or_create_category(trans_data['category'])
    
    # Extract merchant
    merchant = trans_data.get('merchant', {})
    
    # Create or update transaction
    transaction, created = Transaction.objects.update_or_create(
        pluggy_id=trans_data['id'],
        defaults={
            'account': account,
            'type': trans_data['type'],
            'status': trans_data.get('status', 'POSTED'),
            'description': trans_data.get('description', '')[:500],
            'amount': Decimal(str(trans_data.get('amount', 0))),
            'currency_code': trans_data.get('currencyCode', 'BRL'),
            'date': trans_date,
            'merchant': merchant,
            'payment_data': trans_data.get('paymentData', {}),
            'pluggy_category_id': trans_data.get('category', ''),
            'pluggy_category_description': trans_data.get('categoryDescription', ''),
            'category': category,
            'operation_type': trans_data.get('operationType', ''),
            'payment_method': trans_data.get('paymentMethod', ''),
            'credit_card_metadata': trans_data.get('creditCardMetadata', {}),
            'metadata': {
                'provider_code': trans_data.get('providerCode', ''),
                'account_id': trans_data.get('accountId', '')
            },
            'created_at': trans_data.get('createdAt'),
            'updated_at': trans_data.get('updatedAt')
        }
    )
    
    return transaction, created


def _get_or_create_category(category_str: str) -> Optional[TransactionCategory]:
    """
    Get or create category from Pluggy category string
    """
    if not category_str:
        return None
    
    # Parse Pluggy category (format: "parent_description > description")
    parts = category_str.split(' > ')
    
    if len(parts) == 2:
        parent_desc, desc = parts
        
        # Get or create Pluggy category
        pluggy_cat, _ = PluggyCategory.objects.get_or_create(
            id=category_str,
            defaults={
                'description': desc,
                'parent_description': parent_desc
            }
        )
        
        # Return mapped internal category if exists
        if pluggy_cat.internal_category:
            return pluggy_cat.internal_category
        
        # Otherwise create new category
        parent_cat, _ = TransactionCategory.objects.get_or_create(
            slug=parent_desc.lower().replace(' ', '-'),
            defaults={
                'name': parent_desc,
                'type': 'both',
                'is_system': True
            }
        )
        
        category, _ = TransactionCategory.objects.get_or_create(
            slug=desc.lower().replace(' ', '-'),
            parent=parent_cat,
            defaults={
                'name': desc,
                'type': 'both',
                'is_system': True,
                'parent': parent_cat
            }
        )
        
        # Map to Pluggy category
        pluggy_cat.internal_category = category
        pluggy_cat.save()
        
        return category
    
    else:
        # Single level category
        pluggy_cat, _ = PluggyCategory.objects.get_or_create(
            id=category_str,
            defaults={
                'description': category_str
            }
        )
        
        if pluggy_cat.internal_category:
            return pluggy_cat.internal_category
        
        category, _ = TransactionCategory.objects.get_or_create(
            slug=category_str.lower().replace(' ', '-'),
            defaults={
                'name': category_str,
                'type': 'both',
                'is_system': True
            }
        )
        
        pluggy_cat.internal_category = category
        pluggy_cat.save()
        
        return category


@shared_task
def process_webhook_event(event_type: str, event_data: Dict):
    """
    Process webhook event from Pluggy
    """
    try:
        logger.info(f"Processing webhook event: {event_type}")
        
        # Get item
        item_id = event_data.get('id')
        if not item_id:
            logger.error(f"No item ID in webhook data: {event_data}")
            return
        
        # Save webhook record
        webhook = ItemWebhook.objects.create(
            item_id=item_id,
            event_type=event_type,
            event_id=event_data.get('eventId', ''),
            payload=event_data
        )
        
        try:
            # Process based on event type
            if event_type == 'item.updated':
                _handle_item_updated(event_data)
            elif event_type == 'item.error':
                _handle_item_error(event_data)
            elif event_type == 'item.deleted':
                _handle_item_deleted(event_data)
            elif event_type == 'item.waiting_user_input':
                _handle_item_waiting_input(event_data)
            elif event_type == 'transactions.created':
                _handle_transactions_created(event_data)
            elif event_type == 'consent.revoked':
                _handle_consent_revoked(event_data)
            
            # Mark as processed
            webhook.processed = True
            webhook.processed_at = timezone.now()
            webhook.save()
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            webhook.error = str(e)
            webhook.save()
            raise
            
    except Exception as e:
        logger.error(f"Failed to process webhook event: {e}", exc_info=True)


def _handle_item_updated(data: Dict):
    """Handle item updated event"""
    try:
        item = PluggyItem.objects.get(pluggy_id=data['id'])
        
        # Queue sync
        sync_bank_account.delay(str(item.id))
        
    except PluggyItem.DoesNotExist:
        logger.warning(f"Item {data['id']} not found for update event")


def _handle_item_error(data: Dict):
    """Handle item error event"""
    try:
        item = PluggyItem.objects.get(pluggy_id=data['id'])
        
        # Update status
        item.status = 'ERROR'
        item.error_code = data.get('error', {}).get('code', '')
        item.error_message = data.get('error', {}).get('message', '')
        item.save()
        
    except PluggyItem.DoesNotExist:
        logger.warning(f"Item {data['id']} not found for error event")


def _handle_item_deleted(data: Dict):
    """Handle item deleted event"""
    try:
        item = PluggyItem.objects.get(pluggy_id=data['id'])
        
        # Soft delete accounts
        item.accounts.update(is_active=False)
        
        # Update item status
        item.status = 'DELETED'
        item.save()
        
    except PluggyItem.DoesNotExist:
        logger.warning(f"Item {data['id']} not found for delete event")


def _handle_item_waiting_input(data: Dict):
    """Handle item waiting for user input"""
    try:
        item = PluggyItem.objects.get(pluggy_id=data['id'])
        
        # Update status
        item.status = 'WAITING_USER_INPUT'
        item.save()
        
        # TODO: Send notification to user
        
    except PluggyItem.DoesNotExist:
        logger.warning(f"Item {data['id']} not found for waiting input event")


def _handle_transactions_created(data: Dict):
    """Handle new transactions event"""
    # Queue sync for affected accounts
    account_ids = data.get('accountIds', [])
    
    for account_id in account_ids:
        try:
            account = BankAccount.objects.get(pluggy_id=account_id)
            sync_bank_account.delay(
                str(account.item.id),
                account_id=str(account.id)
            )
        except BankAccount.DoesNotExist:
            logger.warning(f"Account {account_id} not found for transactions event")


def _handle_consent_revoked(data: Dict):
    """Handle consent revoked (Open Finance)"""
    try:
        item = PluggyItem.objects.get(pluggy_id=data['id'])
        
        # Update status
        item.status = 'CONSENT_REVOKED'
        item.consent_expires_at = None
        item.save()
        
        # Deactivate accounts
        item.accounts.update(is_active=False)
        
    except PluggyItem.DoesNotExist:
        logger.warning(f"Item {data['id']} not found for consent revoked event")


@shared_task
def cleanup_old_webhooks():
    """
    Clean up old processed webhooks
    """
    cutoff_date = timezone.now() - timedelta(days=30)
    
    deleted = ItemWebhook.objects.filter(
        processed=True,
        created__lt=cutoff_date
    ).delete()
    
    logger.info(f"Deleted {deleted[0]} old webhooks")


@shared_task
def check_items_health():
    """
    Check health of all active items
    """
    # Get items that haven't been updated in 24 hours
    cutoff_time = timezone.now() - timedelta(hours=24)
    
    stale_items = PluggyItem.objects.filter(
        status__in=['UPDATED', 'OUTDATED'],
        last_successful_update__lt=cutoff_time
    )
    
    for item in stale_items:
        sync_bank_account.delay(str(item.id))
    
    logger.info(f"Queued sync for {stale_items.count()} stale items")