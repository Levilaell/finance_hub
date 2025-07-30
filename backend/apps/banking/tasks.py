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
        logger.info(f"Starting sync for item {item.pluggy_item_id}")
        
        with PluggyClient() as client:
            # Update item status
            item_data = client.get_item(item.pluggy_item_id)
            
            # Update item
            item.status = item_data['status']
            item.execution_status = item_data.get('executionStatus', '')
            item.pluggy_updated_at = item_data['updatedAt']
            item.status_detail = item_data.get('statusDetail', {})
            
            if item_data.get('error'):
                item.error_code = item_data['error'].get('code', '')
                item.error_message = item_data['error'].get('message', '')
            
            item.save()
            
            # Check if we can sync
            if item.status not in ['UPDATED', 'OUTDATED']:
                logger.warning(f"Item {item.pluggy_item_id} not ready for sync: {item.status}")
                
                # If item is still processing, retry later
                if item.status in ['LOGIN_IN_PROGRESS', 'UPDATING']:
                    logger.info(f"Item {item.pluggy_item_id} is still processing, will retry")
                    # Retry with exponential backoff
                    raise self.retry(
                        exc=Exception(f"Item still processing: {item.status}"),
                        countdown=60 * (self.request.retries + 1),
                        max_retries=5
                    )
                
                # For error states, don't retry
                return {
                    'success': False,
                    'reason': f'Item status: {item.status}',
                    'requires_reconnection': item.status in ['LOGIN_ERROR', 'INVALID_CREDENTIALS']
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
            
            # Calculate total transactions synced
            total_transactions = sum(r.get('transactions_synced', 0) for r in sync_results if r['success'])
            
            return {
                'success': True,
                'item_id': str(item.id),
                'accounts_synced': len(sync_results),
                'transactions_synced': total_transactions,
                'results': sync_results,
                'message': f'Synced {total_transactions} transactions from {len(sync_results)} accounts'
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
        logger.info(f"Syncing account {account.pluggy_account_id}")
        
        # Update account info
        account_data = client.get_account(account.pluggy_account_id)
        
        account.balance = Decimal(str(account_data.get('balance', 0)))
        account.balance_date = timezone.now()
        account.pluggy_updated_at = account_data.get('updatedAt')
        
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
        logger.error(f"Error syncing account {account.pluggy_account_id}: {e}")
        return {
            'success': False,
            'account_id': str(account.id),
            'error': str(e)
        }


def _sync_transactions(client: PluggyClient, account: BankAccount) -> int:
    """
    Sync transactions for an account
    """
    logger.info(f"=== Starting transaction sync for account {account.pluggy_account_id} ===")
    logger.info(f"Account: {account.display_name} (Type: {account.type})")
    logger.info(f"Current balance: {account.balance}")
    
    # Determine sync period
    last_transaction = account.transactions.order_by('-date').first()
    
    if last_transaction:
        # Sync from last transaction date minus 7 days (for updates)
        from_date = last_transaction.date - timedelta(days=7)
        logger.info(f"Found last transaction dated {last_transaction.date}, syncing from {from_date.date()}")
    else:
        # Initial sync - get last 365 days for Open Finance, 90 for others
        days_back = 365
        from_date = timezone.now() - timedelta(days=days_back)
        logger.info(f"No transactions found, initial sync for {days_back} days")
    
    to_date = timezone.now()
    
    logger.info(
        f"Syncing transactions for account {account.pluggy_account_id} ({account.display_name}) "
        f"from {from_date.date()} to {to_date.date()}"
    )
    
    # Fetch transactions
    page = 1
    total_synced = 0
    
    # Format dates as strings in ISO format for Pluggy API
    from_date_str = from_date.date().isoformat()
    to_date_str = to_date.date().isoformat()
    
    logger.info(f"Calling Pluggy API with dates: from={from_date_str}, to={to_date_str}")
    
    while True:
        try:
            logger.info(f"Fetching transactions page {page}...")
            result = client.get_transactions(
                account.pluggy_account_id,
                from_date=from_date_str,
                to_date=to_date_str,
                page=page
            )
            
            logger.info(f"API response page {page}: {result}")
            logger.info(f"Total transactions: {result.get('total', 0)}, This page: {len(result.get('results', []))}")
            
            transactions = result.get('results', [])
            if not transactions:
                break
            
            # Process transactions
            with db_transaction.atomic():
                for trans_data in transactions:
                    transaction, created = _process_transaction(account, trans_data)
                    if created:
                        total_synced += 1
                        logger.debug(f"Created new transaction: {trans_data.get('description', 'No description')} - {trans_data.get('amount', 0)}")
                    else:
                        logger.debug(f"Updated existing transaction: {trans_data.get('id')}")
            
            # Check if more pages
            if page >= result.get('totalPages', 1):
                break
                
            page += 1
            
        except Exception as e:
            logger.error(f"Error fetching transactions page {page}: {e}")
            break
    
    logger.info(f"Synced {total_synced} new transactions for {account.pluggy_account_id}")
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
        pluggy_transaction_id=trans_data['id'],
        defaults={
            'account': account,
            'company': account.company,  # Add company field
            'type': trans_data['type'],
            'status': trans_data.get('status', 'POSTED'),
            'description': trans_data.get('description', '')[:500],
            'description_raw': trans_data.get('descriptionRaw') or '',  # Use existing field
            'amount': Decimal(str(trans_data.get('amount', 0))),
            'amount_in_account_currency': Decimal(str(trans_data.get('amountInAccountCurrency', 0))) if trans_data.get('amountInAccountCurrency') else None,
            'balance': Decimal(str(trans_data.get('balance', 0))) if trans_data.get('balance') else None,
            'currency_code': trans_data.get('currencyCode', 'BRL'),
            'date': trans_date,
            'provider_code': trans_data.get('providerCode') or '',
            'provider_id': trans_data.get('providerId') or '',
            'merchant': merchant if merchant else None,  # Handle None case
            'payment_data': trans_data.get('paymentData') or {},
            'pluggy_category_id': trans_data.get('categoryId') or '',  # Use categoryId
            'pluggy_category_description': trans_data.get('category') or '',  # Use category
            'category': category,
            'credit_card_metadata': trans_data.get('creditCardMetadata') or {},
            'notes': '',  # Initialize empty
            'tags': [],  # Initialize empty
            'pluggy_created_at': trans_data.get('createdAt'),
            'pluggy_updated_at': trans_data.get('updatedAt')
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
        item = PluggyItem.objects.get(pluggy_item_id=data['id'])
        
        # Queue sync
        sync_bank_account.delay(str(item.id))
        
    except PluggyItem.DoesNotExist:
        logger.warning(f"Item {data['id']} not found for update event")


def _handle_item_error(data: Dict):
    """Handle item error event"""
    try:
        item = PluggyItem.objects.get(pluggy_item_id=data['id'])
        
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
        item = PluggyItem.objects.get(pluggy_item_id=data['id'])
        
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
        item = PluggyItem.objects.get(pluggy_item_id=data['id'])
        
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
            account = BankAccount.objects.get(pluggy_account_id=account_id)
            sync_bank_account.delay(
                str(account.item.id),
                account_id=str(account.id)
            )
        except BankAccount.DoesNotExist:
            logger.warning(f"Account {account_id} not found for transactions event")


def _handle_consent_revoked(data: Dict):
    """Handle consent revoked (Open Finance)"""
    try:
        item = PluggyItem.objects.get(pluggy_item_id=data['id'])
        
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