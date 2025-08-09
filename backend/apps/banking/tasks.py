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
from django.db import IntegrityError
from django.utils import timezone

from .models import (
    PluggyItem, BankAccount, Transaction,
    TransactionCategory, ItemWebhook, PluggyCategory
)
from .integrations.pluggy.client import PluggyClient, PluggyError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def sync_bank_account(self, item_id: str, account_id: Optional[str] = None, force_update: bool = False):
    """
    Sync bank account data from Pluggy
    
    Args:
        item_id: PluggyItem ID
        account_id: Optional specific account ID to sync
        force_update: Force update even if item status is not ideal
        
    Retry strategy:
        - Max 5 retries with exponential backoff
        - Different retry behavior based on error type
    """
    try:
        item = PluggyItem.objects.get(id=item_id)
        logger.info(f"Starting sync for item {item.pluggy_item_id} (attempt {self.request.retries + 1}/{self.max_retries + 1})")
        
        with PluggyClient() as client:
            # Update item status
            try:
                item_data = client.get_item(item.pluggy_item_id)
            except PluggyError as e:
                # Handle API errors with retry
                if 'RATE_LIMIT' in str(e):
                    # Rate limit - retry with longer delay
                    raise self.retry(exc=e, countdown=300)  # 5 minutes
                elif 'TIMEOUT' in str(e) or 'CONNECTION' in str(e):
                    # Temporary network issue - retry with exponential backoff
                    raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
                else:
                    # Other API errors - log and don't retry
                    logger.error(f"Pluggy API error: {e}")
                    return {'success': False, 'error': str(e)}
            
            # Update item
            item.status = item_data['status']
            item.execution_status = item_data.get('executionStatus', '')
            item.pluggy_updated_at = item_data['updatedAt']
            item.status_detail = item_data.get('statusDetail', {})
            
            if item_data.get('error'):
                item.error_code = item_data['error'].get('code', '')
                item.error_message = item_data['error'].get('message', '')
            
            item.save()
            
            # Handle different item statuses
            if item.status in ['LOGIN_ERROR', 'INVALID_CREDENTIALS']:
                # Credential errors - don't retry
                logger.error(f"Item {item.pluggy_item_id} has credential error: {item.status}")
                return {
                    'success': False,
                    'reason': f'Invalid credentials: {item.status}',
                    'requires_reconnection': True,
                    'error_code': item.error_code,
                    'error_message': item.error_message
                }
            
            elif item.status == 'WAITING_USER_INPUT':
                # MFA required - don't retry
                logger.info(f"Item {item.pluggy_item_id} requires user input")
                return {
                    'success': False,
                    'reason': 'MFA required',
                    'requires_mfa': True,
                    'error_code': 'MFA_REQUIRED'
                }
            
            elif item.status == 'ERROR':
                # Generic error - check if recoverable
                if item.error_code in ['SITE_NOT_AVAILABLE', 'CONNECTION_ERROR']:
                    # Temporary error - retry
                    logger.warning(f"Temporary error for item {item.pluggy_item_id}: {item.error_code}")
                    raise self.retry(
                        exc=Exception(f"Temporary error: {item.error_code}"),
                        countdown=120 * (self.request.retries + 1)
                    )
                else:
                    # Permanent error - don't retry
                    logger.error(f"Permanent error for item {item.pluggy_item_id}: {item.error_code}")
                    return {
                        'success': False,
                        'reason': f'Item error: {item.error_code}',
                        'error_message': item.error_message
                    }
            
            # Check if we can sync
            if not force_update and item.status not in ['UPDATED', 'OUTDATED', 'UPDATING']:
                logger.warning(f"Item {item.pluggy_item_id} not ready for sync: {item.status}")
                
                # For other states, don't retry
                return {
                    'success': False,
                    'reason': f'Item status: {item.status}',
                    'requires_reconnection': False
                }
            
            if force_update:
                logger.info(f"Force update enabled, proceeding regardless of status: {item.status}")
            
            # For UPDATING status, check if data is actually available
            if item.status == 'UPDATING':
                # Check statusDetail to see if data is ready
                status_detail = item.status_detail or {}
                
                # Check if accounts and transactions are updated
                accounts_ready = status_detail.get('accounts', {}).get('isUpdated', False)
                transactions_ready = status_detail.get('transactions', {}).get('isUpdated', False)
                
                if accounts_ready and transactions_ready:
                    logger.info(f"Item {item.pluggy_item_id} is UPDATING but data is available, proceeding with sync")
                    # Allow sync to proceed - data is available even though status is UPDATING
                else:
                    logger.info(f"Item {item.pluggy_item_id} is still UPDATING, will retry")
                    # Retry with exponential backoff
                    raise self.retry(
                        exc=Exception(f"Item still processing: {item.status}"),
                        countdown=60 * (self.request.retries + 1),
                        max_retries=10
                    )
            
            # Get accounts to sync
            if account_id:
                accounts = BankAccount.objects.filter(
                    id=account_id,
                    item=item
                )
                logger.info(f"Syncing specific account {account_id}")
            else:
                accounts = item.accounts.filter(is_active=True)
                logger.info(f"Syncing all active accounts for item {item.id}")
            
            logger.info(f"Found {accounts.count()} accounts to sync")
            
            # Sync each account
            sync_results = []
            
            for account in accounts:
                logger.info(f"Starting sync for account {account.id} ({account.pluggy_account_id})")
                result = _sync_account(client, account)
                sync_results.append(result)
                logger.info(f"Sync result for account {account.id}: {result}")
            
            # Update last successful update
            if any(r['success'] for r in sync_results):
                item.last_successful_update = timezone.now()
                
                # Update status to UPDATED if sync was successful and we're in UPDATING status
                if item.status == 'UPDATING':
                    # Check with Pluggy API for latest status
                    try:
                        latest_item_data = client.get_item(item.pluggy_item_id)
                        item.status = latest_item_data.get('status', item.status)
                        item.execution_status = latest_item_data.get('executionStatus', item.execution_status)
                        logger.info(f"Updated item status from API: {item.status}, execution: {item.execution_status}")
                    except Exception as e:
                        logger.warning(f"Failed to get latest status from API: {e}")
                        # If we can't get from API but sync was successful, update to UPDATED
                        if item.execution_status in ['SUCCESS', 'PARTIAL_SUCCESS']:
                            item.status = 'UPDATED'
                            logger.info(f"Updated item status to UPDATED based on successful sync")
                
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
        
        # First check if item is in a syncable state
        try:
            item_data = client.get_item(account.item.pluggy_item_id)
            item_status = item_data.get('status')
            execution_status = item_data.get('executionStatus', '')
            error_code = item_data.get('error', {}).get('code', '')
            
            # Update item status
            account.item.status = item_status
            account.item.execution_status = execution_status
            account.item.error_code = error_code
            account.item.save()
            
            # Check for timeout or errors that prevent sync
            if execution_status == 'USER_INPUT_TIMEOUT' or error_code == 'USER_INPUT_TIMEOUT':
                logger.warning(f"Cannot sync account {account.pluggy_account_id} - item has USER_INPUT_TIMEOUT")
                return {
                    'success': False,
                    'account_id': str(account.id),
                    'error': 'Authentication timeout - reconnection required',
                    'error_code': 'USER_INPUT_TIMEOUT',
                    'reconnection_required': True
                }
            
            if item_status in ['LOGIN_ERROR', 'INVALID_CREDENTIALS', 'ERROR', 'OUTDATED']:
                logger.warning(f"Cannot sync account {account.pluggy_account_id} - item status: {item_status}")
                return {
                    'success': False,
                    'account_id': str(account.id),
                    'error': f'Item in error state: {item_status}',
                    'reconnection_required': True
                }
                
        except Exception as e:
            logger.warning(f"Could not check item status: {e}")
            # Continue with sync attempt
        
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
    logger.info(f"Account Django ID: {account.id}, Company: {account.company.id}")
    
    # Check if company has reached transaction limit
    company = account.company
    limit_reached, usage_info = company.check_limit('transactions')
    if limit_reached:
        logger.warning(
            f"Transaction limit reached for company {company.id} ({company.name}). "
            f"Usage: {usage_info}. Skipping transaction sync."
        )
        
        # Send notification about limit reached
        try:
            from apps.notifications.email_service import EmailService
            EmailService.send_usage_limit_reached(
                email=company.owner.email,
                company_name=company.name,
                limit_type='transactions',
                usage_info=usage_info
            )
        except Exception as e:
            logger.error(f"Failed to send limit notification: {e}")
        
        # Return 0 to indicate no transactions were synced
        return 0
    
    # Determine sync period
    last_transaction = account.transactions.order_by('-date').first()
    
    if last_transaction:
        # Sync from last transaction date minus 7 days (for updates)
        # But also ensure we check at least the last 3 days for very recent transactions
        from_date = last_transaction.date - timedelta(days=7)
        min_from_date = timezone.now() - timedelta(days=3)
        
        # Use the more recent date to ensure we don't miss new transactions
        if min_from_date > from_date:
            from_date = min_from_date
            logger.info(f"Using minimum sync window of 3 days from today")
        else:
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
                    # Check limit before each transaction creation
                    limit_reached, usage_info = company.check_limit('transactions')
                    if limit_reached:
                        logger.warning(
                            f"Transaction limit reached during sync. "
                            f"Processed {total_synced} transactions before hitting limit. "
                            f"Usage: {usage_info}"
                        )
                        # Exit the loop, don't process more transactions
                        break
                    
                    try:
                        transaction, created = _process_transaction(account, trans_data)
                        if created:
                            total_synced += 1
                            logger.info(f"Created new transaction: {trans_data.get('description', 'No description')} - {trans_data.get('amount', 0)} - ID: {trans_data.get('id')}")
                            
                            # Check for usage notifications (80% and 90%)
                            _check_and_send_usage_notifications(company)
                        else:
                            logger.info(f"Updated existing transaction: {trans_data.get('id')}")
                    except Exception as e:
                        logger.error(f"Error processing transaction {trans_data.get('id')}: {e}", exc_info=True)
                        logger.error(f"Transaction data: {trans_data}")
                        raise
            
            # Check if more pages
            if page >= result.get('totalPages', 1):
                break
            
            # Move to next page
            page += 1
            
        except Exception as e:
            logger.error(f"Error fetching transactions page {page}: {e}")
            break
    
    logger.info(f"Synced {total_synced} new transactions for {account.pluggy_account_id}")
    return total_synced


def _process_transaction(account: BankAccount, trans_data: Dict):
    """
    Process single transaction with duplicate prevention
    """
    try:
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
        
        # Use atomic transaction to prevent race conditions
        with db_transaction.atomic():
            # Try to get existing transaction first
            try:
                transaction = Transaction.objects.select_for_update().get(
                    pluggy_transaction_id=trans_data['id']
                )
                created = False
                
                # Update existing transaction
                transaction.account = account
                transaction.company = account.company
                transaction.type = trans_data['type']
                transaction.status = trans_data.get('status', 'POSTED')
                transaction.description = trans_data.get('description', '')[:500]
                transaction.description_raw = trans_data.get('descriptionRaw') or ''
                transaction.amount = Decimal(str(trans_data.get('amount', 0)))
                transaction.amount_in_account_currency = Decimal(str(trans_data.get('amountInAccountCurrency', 0))) if trans_data.get('amountInAccountCurrency') else None
                transaction.balance = Decimal(str(trans_data.get('balance', 0))) if trans_data.get('balance') else None
                transaction.currency_code = trans_data.get('currencyCode', 'BRL')
                transaction.date = trans_date
                transaction.provider_code = trans_data.get('providerCode') or ''
                transaction.provider_id = trans_data.get('providerId') or ''
                transaction.merchant = merchant if merchant else None
                transaction.payment_data = trans_data.get('paymentData') or {}
                transaction.pluggy_category_id = trans_data.get('categoryId') or ''
                transaction.pluggy_category_description = trans_data.get('category') or ''
                transaction.category = category
                transaction.credit_card_metadata = trans_data.get('creditCardMetadata') or {}
                transaction.pluggy_created_at = trans_data.get('createdAt')
                transaction.pluggy_updated_at = trans_data.get('updatedAt')
                transaction.save()
                
            except Transaction.DoesNotExist:
                # Create new transaction
                transaction = Transaction.objects.create(
                    pluggy_transaction_id=trans_data['id'],
                    account=account,
                    company=account.company,
                    type=trans_data['type'],
                    status=trans_data.get('status', 'POSTED'),
                    description=trans_data.get('description', '')[:500],
                    description_raw=trans_data.get('descriptionRaw') or '',
                    amount=Decimal(str(trans_data.get('amount', 0))),
                    amount_in_account_currency=Decimal(str(trans_data.get('amountInAccountCurrency', 0))) if trans_data.get('amountInAccountCurrency') else None,
                    balance=Decimal(str(trans_data.get('balance', 0))) if trans_data.get('balance') else None,
                    currency_code=trans_data.get('currencyCode', 'BRL'),
                    date=trans_date,
                    provider_code=trans_data.get('providerCode') or '',
                    provider_id=trans_data.get('providerId') or '',
                    merchant=merchant if merchant else None,
                    payment_data=trans_data.get('paymentData') or {},
                    pluggy_category_id=trans_data.get('categoryId') or '',
                    pluggy_category_description=trans_data.get('category') or '',
                    category=category,
                    credit_card_metadata=trans_data.get('creditCardMetadata') or {},
                    notes='',
                    tags=[],
                    pluggy_created_at=trans_data.get('createdAt'),
                    pluggy_updated_at=trans_data.get('updatedAt')
                )
                created = True
        
        return transaction, created
        
    except IntegrityError as e:
        # Handle race condition where another process created the transaction
        logger.warning(f"IntegrityError for transaction {trans_data['id']}: {e}")
        
        # Try to get the existing transaction
        try:
            transaction = Transaction.objects.get(pluggy_transaction_id=trans_data['id'])
            return transaction, False
        except Transaction.DoesNotExist:
            # Re-raise if we still can't find it
            raise


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
    Following best practices from: https://docs.pluggy.ai/docs/webhooks
    
    IMPORTANT: Per Pluggy documentation, we should always fetch the latest
    data from the API instead of relying on webhook payload data.
    """
    try:
        logger.info(f"Processing webhook event: {event_type}")
        
        # Extract event ID for idempotency
        event_id = event_data.get('eventId', '')
        if not event_id:
            # Generate a deterministic event_id from the payload for webhooks without eventId
            import hashlib
            import json
            payload_str = json.dumps(event_data, sort_keys=True)
            event_id = hashlib.sha256(f"{event_type}:{payload_str}".encode()).hexdigest()[:32]
            logger.warning(f"No eventId in webhook, generated: {event_id}")
        
        # Check for idempotency - if already processed, skip
        existing_webhook = ItemWebhook.objects.filter(
            event_id=event_id,
            event_type=event_type,
            processed=True
        ).first()
        
        if existing_webhook:
            logger.info(f"Webhook {event_id} already processed at {existing_webhook.processed_at}, skipping")
            return {'status': 'already_processed', 'event_id': event_id}
        
        logger.info(f"Event data: {event_data}")
        
        # Get item ID based on event type
        # Some events have 'id' field, others use 'itemId'
        item_id = event_data.get('id') or event_data.get('itemId')
        
        # Some events like connector status updates might not have item ID
        if not item_id and event_type not in ['transactions.created', 'connector.status_updated']:
            logger.error(f"No item ID in webhook data for event {event_type}: {event_data}")
            return
        
        # Get or create webhook record for processing
        webhook, created = ItemWebhook.objects.get_or_create(
            event_id=event_id,
            event_type=event_type,
            defaults={
                'item_id': item_id if item_id else None,
                'payload': event_data,
                'processed': False
            }
        )
        
        if not created and webhook.processed:
            logger.info(f"Webhook {event_id} already processed, skipping duplicate")
            return {'status': 'already_processed', 'event_id': event_id}
        
        try:
            # Process based on event type - according to Pluggy documentation
            if event_type == 'item.created':
                _handle_item_created(event_data)
            elif event_type == 'item.updated':
                _handle_item_updated(event_data)
            elif event_type == 'item.error':
                _handle_item_error(event_data)
            elif event_type == 'item.deleted':
                _handle_item_deleted(event_data)
            elif event_type == 'item.waiting_user_input':
                _handle_item_waiting_input(event_data)
            elif event_type == 'item.login_succeeded':
                _handle_item_login_succeeded(event_data)
            elif event_type == 'transactions.created':
                _handle_transactions_created(event_data)
            elif event_type == 'transactions.updated':
                _handle_transactions_updated(event_data)
            elif event_type == 'transactions.deleted':
                _handle_transactions_deleted(event_data)
            elif event_type == 'consent.revoked':
                _handle_consent_revoked(event_data)
            elif event_type == 'accounts.created':
                _handle_accounts_created(event_data)
            elif event_type == 'accounts.updated':
                _handle_accounts_updated(event_data)
            else:
                logger.warning(f"Unknown webhook event type: {event_type}")
            
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
    """
    Handle item updated event
    
    Best practice: Fetch latest item data from API instead of relying on webhook payload
    """
    try:
        item = PluggyItem.objects.get(pluggy_item_id=data['id'])
        
        # Fetch latest item data from Pluggy API
        try:
            with PluggyClient() as client:
                logger.info(f"Fetching latest data for item {item.pluggy_item_id}")
                item_data = client.get_item(item.pluggy_item_id)
                
                # Update item with latest data from API
                old_status = item.status
                item.status = item_data.get('status', item.status)
                item.execution_status = item_data.get('executionStatus', '')
                item.error_code = item_data.get('error', {}).get('code', '')
                item.error_message = item_data.get('error', {}).get('message', '')
                item.pluggy_updated_at = item_data.get('updatedAt', item.pluggy_updated_at)
                
                # Update additional fields if available
                if 'parameter' in item_data:
                    item.set_mfa_parameter(item_data['parameter'])
                if 'webhookUrl' in item_data:
                    item.webhook_url = item_data['webhookUrl']
                    
                item.save()
                
                status_changed = old_status != item.status
                logger.info(f"Item {item.pluggy_item_id} updated - Status: {old_status} -> {item.status}")
                
        except Exception as e:
            logger.error(f"Failed to fetch item data from API: {e}")
            # Fall back to webhook data if API call fails
            if 'status' in data:
                old_status = item.status
                item.status = data['status']
                status_changed = old_status != item.status
                item.save()
                logger.info(f"Item {item.pluggy_item_id} status updated from webhook: {old_status} -> {item.status}")
        
        # Queue sync if status indicates data is available
        if item.status in ['UPDATED', 'OUTDATED'] or (item.status == 'UPDATING' and status_changed):
            logger.info(f"Queuing sync for item {item.pluggy_item_id} with status {item.status}")
            sync_bank_account.delay(str(item.id))
        
    except PluggyItem.DoesNotExist:
        logger.warning(f"Item {data['id']} not found for update event")


def _handle_item_error(data: Dict):
    """
    Handle item error event
    
    Fetch latest error details from API for accuracy
    """
    try:
        item = PluggyItem.objects.get(pluggy_item_id=data['id'])
        
        # Try to fetch latest item data from API for complete error details
        try:
            with PluggyClient() as client:
                logger.info(f"Fetching latest error data for item {item.pluggy_item_id}")
                item_data = client.get_item(item.pluggy_item_id)
                
                # Update with latest error information
                item.status = item_data.get('status', 'ERROR')
                item.error_code = item_data.get('error', {}).get('code', '')
                item.error_message = item_data.get('error', {}).get('message', '')
                item.execution_status = item_data.get('executionStatus', '')
                item.pluggy_updated_at = item_data.get('updatedAt', item.pluggy_updated_at)
                
        except Exception as e:
            logger.error(f"Failed to fetch item error data from API: {e}")
            # Fall back to webhook data
            item.status = 'ERROR'
            item.error_code = data.get('error', {}).get('code', '')
            item.error_message = data.get('error', {}).get('message', '')
        
        item.save()
        logger.error(f"Item {item.pluggy_item_id} error: {item.error_code} - {item.error_message}")
        
        # Notify user about the error
        try:
            from apps.notifications.services import NotificationService
            NotificationService.create_notification(
                event_type='sync_error',
                event_data={
                    'id': str(item.id),
                    'connector_name': item.connector.name if hasattr(item, 'connector') else 'Financial Institution',
                    'status': item.status,
                    'error_message': item.error_message or 'Connection error',
                    'action_url': f'/accounts/reconnect/{item.id}',
                },
                company=item.company,
                user=None,
                broadcast=True
            )
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
        
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
        
        # Update status and parameter info
        item.status = 'WAITING_USER_INPUT'
        
        # Extract parameter information from webhook data
        if 'parameter' in data:
            item.set_mfa_parameter(data['parameter'])
            logger.info(f"Item {item.pluggy_item_id} requires parameter: {data['parameter'].get('name', 'unknown')}")
        elif 'data' in data and 'parameter' in data['data']:
            item.set_mfa_parameter(data['data']['parameter'])
            logger.info(f"Item {item.pluggy_item_id} requires parameter: {data['data']['parameter'].get('name', 'unknown')}")
        else:
            # Default parameter for MFA
            default_param = {
                'name': 'token',
                'type': 'text',
                'label': 'Código de verificação',
                'placeholder': 'Digite o código recebido',
                'assistiveText': 'Verifique seu aplicativo bancário ou SMS'
            }
            item.set_mfa_parameter(default_param)
            logger.warning(f"No parameter info in webhook, using default token parameter")
        
        item.save()
        
        # Send notification to user with detailed MFA info
        try:
            from apps.notifications.services import NotificationService
            
            parameter_type = item.parameter.get('name', 'token')
            parameter_label = item.parameter.get('label', 'Código de verificação')
            
            NotificationService.create_notification(
                event_type='mfa_required',
                event_data={
                    'id': str(item.id),
                    'connector_name': item.connector.name if hasattr(item, 'connector') else 'Financial Institution',
                    'action_url': f'/accounts/mfa/{item.id}',
                    'parameter_type': parameter_type,
                    'parameter_label': parameter_label,
                    'message': f'{item.connector.name if hasattr(item, "connector") else "Banco"} está solicitando: {parameter_label}'
                },
                company=item.company,
                user=None,
                broadcast=True
            )
            logger.info(f"MFA notification sent for item {item.id}")
        except Exception as e:
            logger.error(f"Failed to send MFA notification: {e}")
        
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


def _handle_item_created(data: Dict):
    """Handle item created event"""
    logger.info(f"Item created event for {data.get('id')}")
    # Usually we create items through our API, so this is just for logging


def _handle_item_login_succeeded(data: Dict):
    """Handle successful login - queue sync"""
    try:
        item = PluggyItem.objects.get(pluggy_item_id=data['id'])
        
        # Update status
        item.status = 'UPDATING'
        item.save()
        
        # Queue sync
        sync_bank_account.delay(str(item.id))
        
    except PluggyItem.DoesNotExist:
        logger.warning(f"Item {data['id']} not found for login succeeded event")


def _handle_transactions_updated(data: Dict):
    """
    Handle updated transactions event
    
    Transactions were modified (category, description, etc.)
    """
    transaction_ids = data.get('transactionIds', [])
    item_id = data.get('itemId')
    
    logger.info(f"Transactions updated - Item: {item_id}, Count: {len(transaction_ids)}")
    
    # Queue sync to update modified transactions
    if item_id:
        try:
            item = PluggyItem.objects.get(pluggy_item_id=item_id)
            sync_bank_account.delay(str(item.id))
        except PluggyItem.DoesNotExist:
            logger.warning(f"Item {item_id} not found for transactions updated event")


def _handle_transactions_deleted(data: Dict):
    """
    Handle deleted transactions event
    
    Transactions were removed from the account
    """
    transaction_ids = data.get('transactionIds', [])
    item_id = data.get('itemId')
    
    logger.info(f"Transactions deleted - Item: {item_id}, Count: {len(transaction_ids)}")
    
    # Mark transactions as deleted if we have the IDs
    if transaction_ids:
        # Instead of hard deleting, we soft delete to maintain history
        deleted_count = Transaction.objects.filter(
            pluggy_transaction_id__in=transaction_ids
        ).update(is_deleted=True, deleted_at=timezone.now())
        
        logger.info(f"Marked {deleted_count} transactions as deleted")
    
    # Queue sync to ensure consistency
    if item_id:
        try:
            item = PluggyItem.objects.get(pluggy_item_id=item_id)
            sync_bank_account.delay(str(item.id))
        except PluggyItem.DoesNotExist:
            logger.warning(f"Item {item_id} not found for transactions deleted event")


def _handle_accounts_created(data: Dict):
    """
    Handle accounts created event
    
    New accounts were added to an existing item
    """
    item_id = data.get('itemId')
    account_ids = data.get('accountIds', [])
    
    logger.info(f"Accounts created - Item: {item_id}, Account count: {len(account_ids)}")
    
    if item_id:
        try:
            item = PluggyItem.objects.get(pluggy_item_id=item_id)
            # Queue sync to fetch new accounts
            logger.info(f"Queuing sync to fetch new accounts for item {item_id}")
            sync_bank_account.delay(str(item.id))
        except PluggyItem.DoesNotExist:
            logger.warning(f"Item {item_id} not found for accounts created event")


def _handle_accounts_updated(data: Dict):
    """
    Handle accounts updated event
    
    Account information was modified (balance, name, etc.)
    """
    item_id = data.get('itemId')
    account_ids = data.get('accountIds', [])
    
    logger.info(f"Accounts updated - Item: {item_id}, Account count: {len(account_ids)}")
    
    if item_id:
        try:
            item = PluggyItem.objects.get(pluggy_item_id=item_id)
            # Sync to update account information
            sync_bank_account.delay(str(item.id))
        except PluggyItem.DoesNotExist:
            logger.warning(f"Item {item_id} not found for accounts updated event")


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


def _check_and_send_usage_notifications(company):
    """Check usage percentage and send notifications at 80% and 90%"""
    try:
        usage_percentage = company.get_usage_percentage('transactions')
        
        # Get the notification flags from ResourceUsage
        from ..companies.models import ResourceUsage
        current_month = timezone.now().replace(day=1).date()
        usage_record, _ = ResourceUsage.objects.get_or_create(
            company=company,
            month=current_month,
            defaults={
                'transactions_count': company.current_month_transactions,
                'ai_requests_count': company.current_month_ai_requests
            }
        )
        
        # Check 90% threshold
        if usage_percentage >= 90 and not usage_record.notified_90_percent:
            from apps.notifications.email_service import EmailService
            EmailService.send_usage_limit_warning(
                email=company.owner.email,
                company_name=company.name,
                limit_type='transações',
                percentage=90,
                current=company.current_month_transactions,
                limit=company.subscription_plan.max_transactions if company.subscription_plan else 100
            )
            usage_record.notified_90_percent = True
            usage_record.save(update_fields=['notified_90_percent'])
            logger.info(f"Sent 90% usage notification for company {company.id}")
            
        # Check 80% threshold
        elif usage_percentage >= 80 and not usage_record.notified_80_percent:
            from apps.notifications.email_service import EmailService
            EmailService.send_usage_limit_warning(
                email=company.owner.email,
                company_name=company.name,
                limit_type='transações',
                percentage=80,
                current=company.current_month_transactions,
                limit=company.subscription_plan.max_transactions if company.subscription_plan else 100
            )
            usage_record.notified_80_percent = True
            usage_record.save(update_fields=['notified_80_percent'])
            logger.info(f"Sent 80% usage notification for company {company.id}")
            
    except Exception as e:
        logger.error(f"Error checking/sending usage notifications: {e}")