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

        logger.info(f"Received webhook: {event_type} for item {item_id}")
        logger.debug(f"Webhook payload: {payload}")

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
        elif event_type == 'connector/status_update':
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
    """
    connector_id = payload.get('connectorId')
    status_info = payload.get('status')

    logger.info(f"Connector {connector_id} status update: {status_info}")

    # TODO: Implement connector status tracking if needed
    # This could be used to notify users about bank maintenance, outages, etc.


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