"""
Webhook handlers for Pluggy events
"""
import json
import logging
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

from .models import BankConnection, SyncHistory
from .integrations.pluggy.client import PluggyClient
from .tasks import sync_bank_connection, process_webhook_event

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def pluggy_webhook(request):
    """
    Endpoint to receive Pluggy webhook notifications
    
    Events handled:
    - item/created
    - item/updated
    - item/deleted
    - item/error
    - transactions/created
    - transactions/updated
    - transactions/deleted
    """
    try:
        # Parse request body
        payload = request.body.decode('utf-8')
        data = json.loads(payload)
        
        # Validate webhook signature
        signature = request.headers.get('X-Pluggy-Signature', '')
        client = PluggyClient()
        
        if not client.validate_webhook(signature, payload):
            logger.warning(f"Invalid webhook signature from {request.META.get('REMOTE_ADDR')}")
            return HttpResponseBadRequest("Invalid signature")
        
        # Extract event data
        event_type = data.get('event')
        item_id = data.get('itemId')
        
        logger.info(f"Received webhook event: {event_type} for item: {item_id}")
        
        # Process event asynchronously
        process_webhook_event.delay(event_type, data)
        
        # Return immediate response
        return JsonResponse({"status": "accepted"}, status=200)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return HttpResponseBadRequest("Invalid JSON")
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JsonResponse({"error": "Internal error"}, status=500)


def handle_item_updated(data):
    """Handle item/updated webhook event"""
    item_id = data.get('itemId')
    
    try:
        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        
        # Check item status from Pluggy
        client = PluggyClient()
        item_data = client.get_item(item_id)
        
        # Update connection status
        old_status = connection.status
        connection.status = item_data.get('status', 'ERROR')
        connection.save()
        
        # If status changed to UPDATED, trigger sync
        if old_status != 'UPDATED' and connection.status == 'UPDATED':
            sync_bank_connection.delay(connection.id)
            
        # Create sync history entry
        SyncHistory.objects.create(
            connection=connection,
            status='SUCCESS',
            sync_type='WEBHOOK',
            details={
                'event': 'item/updated',
                'old_status': old_status,
                'new_status': connection.status
            }
        )
        
    except BankConnection.DoesNotExist:
        logger.warning(f"Connection not found for item: {item_id}")


def handle_item_error(data):
    """Handle item/error webhook event"""
    item_id = data.get('itemId')
    error_data = data.get('error', {})
    
    try:
        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        
        # Update connection with error
        connection.status = 'ERROR'
        connection.error_message = error_data.get('message', 'Unknown error')
        connection.save()
        
        # Create sync history entry
        SyncHistory.objects.create(
            connection=connection,
            status='FAILED',
            sync_type='WEBHOOK',
            error_message=connection.error_message,
            details={
                'event': 'item/error',
                'error': error_data
            }
        )
        
    except BankConnection.DoesNotExist:
        logger.warning(f"Connection not found for item: {item_id}")


def handle_transactions_webhook(event_type, data):
    """Handle transaction webhook events"""
    item_id = data.get('itemId')
    
    try:
        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        
        # Trigger sync to update transactions
        sync_bank_connection.delay(connection.id)
        
        # Log webhook event
        SyncHistory.objects.create(
            connection=connection,
            status='SUCCESS',
            sync_type='WEBHOOK',
            details={
                'event': event_type,
                'trigger': 'transaction_change'
            }
        )
        
    except BankConnection.DoesNotExist:
        logger.warning(f"Connection not found for item: {item_id}")