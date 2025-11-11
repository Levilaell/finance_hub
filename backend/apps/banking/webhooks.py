"""
Webhook handlers for Pluggy notifications.
Ref: https://docs.pluggy.ai/docs/webhooks
"""

import json
import hmac
import hashlib
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

from .models import BankConnection, SyncLog
from .services import BankConnectionService, TransactionService

logger = logging.getLogger(__name__)


def verify_webhook_signature(request_body: bytes, signature: str) -> bool:
    """
    Verify webhook signature for security.
    Ref: https://docs.pluggy.ai/docs/webhooks-security
    """
    webhook_secret = settings.PLUGGY_WEBHOOK_SECRET if hasattr(settings, 'PLUGGY_WEBHOOK_SECRET') else None

    if not webhook_secret:
        logger.warning("No webhook secret configured, skipping verification")
        return True

    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        request_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


@csrf_exempt
@require_POST
def pluggy_webhook_handler(request):
    """
    Handle webhooks from Pluggy.
    Ref: https://docs.pluggy.ai/reference/webhooks-list

    IMPORTANT: Pluggy requires 2XX response within 5 seconds or retries up to 3 times.
    - This handler responds immediately (200 OK) and processes synchronously
    - Idempotency is handled via eventId caching (7 days)
    - Failed webhooks (after 3 retries) are lost and won't be re-sent

    Best practices:
    1. Always respond with 2XX quickly
    2. Use eventId for deduplication
    3. Processing happens synchronously but should be fast
    4. For heavy operations, consider async tasks in the future
    """
    # Log incoming webhook
    logger.info(f"Webhook received - Headers: {dict(request.headers)}")
    logger.info(f"Webhook body: {request.body[:500]}")  # Log first 500 chars

    # Verify signature if provided
    signature = request.headers.get('X-Webhook-Signature', '')
    if signature and not verify_webhook_signature(request.body, signature):
        logger.warning("Invalid webhook signature")
        return HttpResponse(status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        event_type = payload.get('event')
        item_id = payload.get('itemId')
        event_id = payload.get('eventId')

        logger.info(f"Received webhook: {event_type} for item {item_id}")
        logger.debug(f"Webhook payload: {payload}")

        # Idempotency: Check if event was already processed
        # Ref: https://docs.pluggy.ai/docs/webhooks (use eventId for deduplication)
        if event_id:
            cache_key = f"pluggy_event_{event_id}"
            if cache.get(cache_key):
                logger.info(
                    f"Duplicate webhook detected - Event {event_id} ({event_type}) already processed. "
                    f"Skipping to prevent duplicate processing (idempotency). Item: {item_id}"
                )
                return JsonResponse({'status': 'ok', 'processed': False, 'reason': 'duplicate'})

            # Mark event as processed (expires in 7 days)
            cache.set(cache_key, True, timeout=60*60*24*7)

        # Handle different event types
        if event_type == 'item/updated':
            handle_item_updated(item_id, payload)
        elif event_type == 'item/created':
            handle_item_created(item_id, payload)
        elif event_type == 'item/error':
            handle_item_error(item_id, payload)
        elif event_type == 'item/deleted':
            handle_item_deleted(item_id, payload)
        elif event_type == 'item/waiting_user_input':
            handle_item_mfa(item_id, payload)
        elif event_type == 'item/login_succeeded':
            handle_item_login_succeeded(item_id, payload)
        elif event_type == 'transactions/created':
            handle_transactions_created(item_id, payload)
        elif event_type == 'transactions/updated':
            handle_transactions_updated(item_id, payload)
        elif event_type == 'transactions/deleted':
            handle_transactions_deleted(item_id, payload)
        elif event_type == 'connector/status_updated':
            handle_connector_status(payload)
        else:
            logger.warning(f"Unknown webhook event type: {event_type}")
            # Still return OK for unknown events

        return JsonResponse({'status': 'ok'})

    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return HttpResponse(status=500)


def handle_item_updated(item_id: str, payload: dict):
    """
    Handle item update events.
    This is triggered when an item's data has been successfully updated.
    """
    try:
        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        service = BankConnectionService()

        # Update connection status
        service.update_connection_status(connection)

        # Sync accounts if status is good
        if connection.status == 'UPDATED':
            service.sync_accounts(connection)

            # Sync transactions for all accounts
            tx_service = TransactionService()
            # Don't trigger update from webhook since it's already updated
            tx_service.sync_all_accounts_transactions(connection, trigger_update=False)

        logger.info(f"Successfully processed update for connection {connection.id}")

    except BankConnection.DoesNotExist:
        logger.warning(f"Connection not found for item {item_id}")
    except Exception as e:
        logger.error(f"Error handling item update: {e}")


def handle_item_created(item_id: str, payload: dict):
    """
    Handle item creation events.
    """
    try:
        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        connection.status = 'UPDATING'
        connection.save()

        # Initial sync will happen when status becomes 'UPDATED'
        logger.info(f"Item created for connection {connection.id}")

    except BankConnection.DoesNotExist:
        logger.warning(f"Connection not found for new item {item_id}")
    except Exception as e:
        logger.error(f"Error handling item creation: {e}")


def handle_item_error(item_id: str, payload: dict):
    """
    Handle item error events.
    """
    try:
        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        error = payload.get('error', {})

        connection.status = 'ERROR'
        connection.status_detail = {
            'code': error.get('code'),
            'message': error.get('message'),
            'details': error.get('details')
        }
        connection.save()

        # Log sync failure
        SyncLog.objects.create(
            connection=connection,
            sync_type='FULL',
            status='FAILED',
            error_message=error.get('message', 'Unknown error'),
            completed_at=timezone.now()
        )

        logger.error(f"Item error for connection {connection.id}: {error}")

    except BankConnection.DoesNotExist:
        logger.warning(f"Connection not found for errored item {item_id}")
    except Exception as e:
        logger.error(f"Error handling item error: {e}")


def handle_item_deleted(item_id: str, payload: dict):
    """
    Handle item deletion events.
    """
    try:
        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        connection.is_active = False
        connection.save()

        logger.info(f"Item deleted for connection {connection.id}")

    except BankConnection.DoesNotExist:
        logger.warning(f"Connection not found for deleted item {item_id}")
    except Exception as e:
        logger.error(f"Error handling item deletion: {e}")


def handle_item_mfa(item_id: str, payload: dict):
    """
    Handle MFA (Multi-Factor Authentication) required events.
    """
    try:
        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        connection.status = 'WAITING_USER_INPUT'
        connection.status_detail = {
            'mfa_required': True,
            'parameter': payload.get('parameter'),
            'message': payload.get('message', 'MFA required')
        }
        connection.save()

        logger.info(f"MFA required for connection {connection.id}")

        # TODO: Implement notification to user about MFA requirement
        # This could be done via email, push notification, or in-app notification

    except BankConnection.DoesNotExist:
        logger.warning(f"Connection not found for MFA item {item_id}")
    except Exception as e:
        logger.error(f"Error handling MFA requirement: {e}")


def handle_connector_status(payload: dict):
    """
    Handle connector status update events.
    This is triggered when a connector's status changes (ONLINE, UNSTABLE, OFFLINE).
    Ref: https://docs.pluggy.ai/docs/webhooks
    """
    connector_id = payload.get('connectorId')
    data = payload.get('data', {})
    status = data.get('status')

    logger.info(f"Connector {connector_id} status changed to: {status}")

    # Log connector status for monitoring
    # This can be used to track bank maintenance, outages, etc.
    # Status values: ONLINE, UNSTABLE, OFFLINE

    if status == 'OFFLINE':
        logger.warning(f"Connector {connector_id} is OFFLINE - bank may be unavailable")
    elif status == 'UNSTABLE':
        logger.warning(f"Connector {connector_id} is UNSTABLE - connection issues may occur")
    else:
        logger.info(f"Connector {connector_id} is back {status}")

    # TODO: Optionally notify users about their affected connections
    # For example, if a user has connections using this connector, we could:
    # 1. Update connection status to reflect connector issues
    # 2. Send notification to user about potential sync delays
    # 3. Disable auto-sync until connector is back online


def handle_item_login_succeeded(item_id: str, payload: dict):
    """
    Handle successful login events.
    This is triggered when an item successfully logs into the financial institution.
    """
    try:
        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        connection.status = 'UPDATING'
        connection.last_updated_at = timezone.now()
        connection.save()

        logger.info(f"Login succeeded for connection {connection.id}")

    except BankConnection.DoesNotExist:
        logger.warning(f"Connection not found for item {item_id}")
    except Exception as e:
        logger.error(f"Error handling login success: {e}")


def handle_transactions_created(item_id: str, payload: dict):
    """
    Handle new transactions created events.
    This is triggered when new transactions are available for an item.
    """
    try:
        connection = BankConnection.objects.get(pluggy_item_id=item_id)

        # Log the event
        logger.info(f"New transactions available for connection {connection.id}")

        # First ensure accounts are synced
        service = BankConnectionService()

        # Update connection status first
        service.update_connection_status(connection)

        # Sync accounts if needed
        if connection.accounts.count() == 0:
            logger.info(f"No accounts found, syncing accounts for connection {connection.id}")
            service.sync_accounts(connection)

        # Now sync transactions for all accounts
        tx_service = TransactionService()
        # Don't trigger update since transactions are already available
        tx_service.sync_all_accounts_transactions(connection, trigger_update=False)

    except BankConnection.DoesNotExist:
        logger.warning(f"Connection not found for item {item_id}")
    except Exception as e:
        logger.error(f"Error handling transactions created: {e}")


def handle_transactions_updated(item_id: str, payload: dict):
    """
    Handle transactions updated events.
    This is triggered when transactions have been updated for an item.
    """
    try:
        connection = BankConnection.objects.get(pluggy_item_id=item_id)

        logger.info(f"Processing transactions update for connection {connection.id}")

        # Update connection status
        service = BankConnectionService()
        service.update_connection_status(connection)

        # Sync accounts first to ensure they exist
        if connection.accounts.count() == 0:
            logger.info(f"No accounts found, syncing accounts for connection {connection.id}")
            service.sync_accounts(connection)
        else:
            # Update existing accounts with latest data
            service.sync_accounts(connection)

        # Sync transactions for all accounts
        tx_service = TransactionService()
        # Don't trigger update since transactions are already updated
        tx_service.sync_all_accounts_transactions(connection, trigger_update=False)

        logger.info(f"Transactions updated for connection {connection.id}")

    except BankConnection.DoesNotExist:
        logger.warning(f"Connection not found for item {item_id}")
    except Exception as e:
        logger.error(f"Error handling transactions update: {e}")


def handle_transactions_deleted(item_id: str, payload: dict):
    """
    Handle transactions deleted events.
    This is triggered when transactions are deleted by the financial institution.
    Ref: https://docs.pluggy.ai/docs/webhooks
    """
    try:
        from .models import Transaction

        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        transaction_ids = payload.get('transactionIds', [])

        if not transaction_ids:
            logger.warning(f"No transaction IDs provided in delete event for item {item_id}")
            return

        # Delete transactions by their Pluggy IDs
        deleted_count = Transaction.objects.filter(
            pluggy_transaction_id__in=transaction_ids,
            account__connection=connection
        ).delete()[0]

        logger.info(
            f"Deleted {deleted_count} transactions for connection {connection.id}. "
            f"Transaction IDs: {transaction_ids}"
        )

    except BankConnection.DoesNotExist:
        logger.warning(f"Connection not found for item {item_id}")
    except Exception as e:
        logger.error(f"Error handling transactions deletion: {e}")