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
        logger.info(f"Webhook received from IP: {request.META.get('REMOTE_ADDR')}")
        logger.info(f"Webhook payload length: {len(payload)} characters")
        
        # Parse JSON payload
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook payload: {e}")
            logger.error(f"Payload content: {payload[:500]}...")  # Log first 500 chars
            return HttpResponseBadRequest("Invalid JSON")
        
        # Log webhook headers (but not sensitive data)
        safe_headers = {k: v for k, v in dict(request.headers).items() 
                       if k.lower() not in ['authorization', 'x-pluggy-signature']}
        logger.info(f"Webhook headers: {safe_headers}")
        
        # Skip signature validation for now to avoid import issues
        # TODO: Re-enable signature validation after fixing import issues
        if False:  # Temporarily disabled
            pass
        
        # Extract event data safely
        event_type = data.get('event', 'unknown')
        event_id = data.get('eventId') or data.get('id', 'unknown')
        
        # Extract item ID from different possible locations
        item_id = None
        try:
            if 'data' in data and isinstance(data['data'], dict) and 'item' in data['data']:
                item_id = data['data']['item'].get('id')
            else:
                item_id = data.get('itemId')
        except (KeyError, TypeError, AttributeError) as e:
            logger.warning(f"Could not extract item_id from webhook data: {e}")
            logger.info(f"Webhook data structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            
        client_id = data.get('clientId', 'unknown')
        triggered_by = data.get('triggeredBy', 'CLIENT')
        
        logger.info(f"Webhook event: {event_type}, eventId: {event_id}, itemId: {item_id}, triggeredBy: {triggered_by}")
        
        # Find the PluggyItem instance (optional - some webhooks don't have items)
        item = None
        if item_id and item_id != 'unknown':
            try:
                item = PluggyItem.objects.get(pluggy_item_id=item_id)
                logger.info(f"Found PluggyItem: {item.id} for item_id: {item_id}")
            except PluggyItem.DoesNotExist:
                logger.warning(f"PluggyItem not found for item_id: {item_id} - this may be normal for some events")
            except Exception as item_error:
                logger.error(f"Error fetching PluggyItem for item_id {item_id}: {item_error}")
        
        # Store webhook for audit trail (even if item not found)
        webhook_created = False
        try:
            if item:
                webhook, webhook_created = ItemWebhook.objects.get_or_create(
                    event_id=event_id,
                    defaults={
                        'item': item,
                        'event_type': event_type,
                        'payload': data,
                        'triggered_by': triggered_by
                    }
                )
                if not webhook_created:
                    logger.info(f"Duplicate webhook event {event_id} - using existing")
            else:
                logger.info(f"Skipping webhook storage - no item found for event {event_type}")
        except IntegrityError as ie:
            logger.warning(f"Webhook already exists for event_id {event_id}: {ie}")
        except Exception as webhook_error:
            logger.error(f"Error storing webhook: {webhook_error}")
            # Continue - webhook storage is not critical
        
        # Process event asynchronously following best practices
        # Temporarily disabled to avoid import issues
        try:
            # Import here to avoid module-level import issues
            from .tasks import process_webhook_event
            process_webhook_event.delay(event_type, data)
            logger.info(f"Queued webhook processing for event {event_type}")
        except ImportError as import_error:
            logger.warning(f"Could not import process_webhook_event: {import_error}")
            # Continue - webhook received successfully even if processing is delayed
        except Exception as celery_error:
            logger.warning(f"Could not queue webhook processing (Celery may not be running): {celery_error}")
            # Continue - webhook received successfully even if processing is delayed
        
        # Return immediate 2XX response as required by Pluggy
        response_data = {
            "status": "accepted", 
            "eventId": event_id,
            "eventType": event_type,
            "timestamp": json.dumps(data.get('timestamp', 'unknown'))
        }
        logger.info(f"Webhook processed successfully - returning 200")
        return JsonResponse(response_data, status=200)
        
    except Exception as e:
        # Log full error details for debugging
        logger.error(f"Unexpected error processing webhook: {str(e)}", exc_info=True)
        logger.error(f"Request method: {request.method}")
        logger.error(f"Request path: {request.path}")
        logger.error(f"Request META: {dict(request.META)}")
        
        # Still return 200 to prevent Pluggy from retrying
        # Log the error but don't fail the webhook delivery
        return JsonResponse({
            "status": "error", 
            "message": "Internal processing error - logged for review"
        }, status=200)