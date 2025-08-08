"""
Webhook handlers for Pluggy events
Following official documentation: https://docs.pluggy.ai/docs/webhooks
"""
import json
import logging
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.db import IntegrityError
# timezone imported if needed for future use

from .models import BankAccount, ItemWebhook, PluggyItem
from .integrations.pluggy.client import PluggyClient
from .tasks import sync_bank_account, process_webhook_event

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def pluggy_webhook(request):
    """
    Endpoint to receive Pluggy webhook notifications
    
    Following best practices from https://docs.pluggy.ai/docs/webhooks:
    - Respond with 2XX immediately
    - Process webhook data asynchronously
    - Retrieve latest item data via GET request after receiving webhook
    
    Main events handled:
    - item/created: Item successfully connected
    - item/updated: Item synced successfully  
    - item/deleted: Item deleted
    - item/error: Item encountered an error
    - item/waiting_user_input: MFA or additional auth required
    - transactions/created: New transactions available
    - transactions/updated: Transactions modified
    - transactions/deleted: Transactions removed
    - connector/status_updated: Connector status change
    """
    try:
        # Parse request body
        payload = request.body.decode('utf-8')
        data = json.loads(payload)
        
        # Log webhook receipt
        logger.info(f"Received webhook from IP: {request.META.get('REMOTE_ADDR')}")
        logger.info(f"Webhook headers: {dict(request.headers)}")
        
        # Validate webhook signature if configured
        if hasattr(settings, 'PLUGGY_WEBHOOK_SECRET') and settings.PLUGGY_WEBHOOK_SECRET:
            signature = request.headers.get('X-Pluggy-Signature', '')
            client = PluggyClient()
            
            if not client.validate_webhook(signature, payload):
                logger.warning(f"Invalid webhook signature from {request.META.get('REMOTE_ADDR')}")
                return JsonResponse({"error": "Invalid signature"}, status=401)
        
        # Extract event data
        event_type = data.get('event')
        event_id = data.get('eventId') or data.get('id')  # Some events use 'id' field
        
        # Extract item ID from different possible locations
        item_id = None
        if 'data' in data and 'item' in data['data']:
            item_id = data['data']['item'].get('id')
        else:
            item_id = data.get('itemId')
            
        client_id = data.get('clientId')
        triggered_by = data.get('triggeredBy')  # USER, CLIENT, SYNC, INTERNAL
        
        logger.info(f"Webhook event: {event_type}, eventId: {event_id}, itemId: {item_id}, triggeredBy: {triggered_by}")
        
        # Find the PluggyItem instance
        try:
            item = PluggyItem.objects.get(pluggy_item_id=item_id) if item_id else None
        except PluggyItem.DoesNotExist:
            logger.warning(f"PluggyItem not found for item_id: {item_id}")
            return JsonResponse({"error": "Item not found"}, status=404)
        
        # Store webhook for audit trail
        webhook_created = False
        if item:
            webhook, webhook_created = ItemWebhook.objects.get_or_create(
                event_id=event_id or '',
                defaults={
                    'item': item,
                    'event_type': event_type or '',
                    'payload': data,
                    'triggered_by': triggered_by or 'CLIENT'  # Default to CLIENT if not specified
                }
            )
            if not webhook_created:
                logger.info(f"Duplicate webhook event {event_id} - using existing")
        
        # Process event asynchronously following best practices
        # The task will fetch latest data from Pluggy API instead of relying on webhook payload
        process_webhook_event.delay(event_type, data)
        
        # Return immediate 2XX response as required by Pluggy
        return JsonResponse({"status": "accepted", "eventId": event_id}, status=200)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return HttpResponseBadRequest("Invalid JSON")
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JsonResponse({"error": "Internal error"}, status=500)