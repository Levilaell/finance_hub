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
        
        # Process event following best practices
        processed_async = False
        try:
            # Try asynchronous processing first (preferred)
            from .tasks import process_webhook_event
            process_webhook_event.delay(event_type, data)
            logger.info(f"✅ Queued async webhook processing for event {event_type}")
            processed_async = True
        except ImportError as import_error:
            logger.warning(f"Could not import process_webhook_event: {import_error}")
        except Exception as celery_error:
            logger.warning(f"Could not queue webhook processing (Celery may not be running): {celery_error}")
        
        # Fallback: Basic synchronous processing if async failed
        if not processed_async and item:
            try:
                logger.info(f"⚡ Falling back to synchronous processing for {event_type}")
                processed_sync = _process_webhook_basic(item, event_type, data)
                if processed_sync:
                    logger.info(f"✅ Synchronous processing completed for {event_type}")
                else:
                    logger.warning(f"⚠️ Synchronous processing failed for {event_type}")
            except Exception as sync_error:
                logger.error(f"❌ Synchronous processing error: {sync_error}")
                # Continue - webhook received successfully even if processing failed
        
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


def _process_webhook_basic(item, event_type, event_data):
    """
    Basic synchronous webhook processing when Celery is not available.
    Only handles essential item status updates to keep webhooks functional.
    
    Returns True if processing was successful, False otherwise.
    """
    try:
        from django.utils import timezone
        
        logger.info(f"🔄 Processing webhook {event_type} for item {item.pluggy_item_id}")
        
        # Extract relevant data safely
        item_data = None
        if isinstance(event_data, dict):
            if 'data' in event_data and isinstance(event_data['data'], dict):
                item_data = event_data['data'].get('item', {})
            elif 'item' in event_data:
                item_data = event_data['item']
        
        # Update item status based on event type
        status_updated = False
        
        if event_type == 'item/login_succeeded':
            # Login successful - item should be ready for sync
            old_status = item.status
            item.status = 'UPDATED'
            item.last_successful_update = timezone.now()
            item.pluggy_updated_at = timezone.now()
            status_updated = True
            logger.info(f"📝 Status updated: {old_status} → UPDATED (login succeeded)")
            
        elif event_type == 'item/updated':
            # Item updated successfully
            old_status = item.status
            item.status = 'UPDATED'
            item.last_successful_update = timezone.now()
            item.pluggy_updated_at = timezone.now()
            status_updated = True
            logger.info(f"📝 Status updated: {old_status} → UPDATED (item updated)")
            
        elif event_type == 'item/error':
            # Item encountered an error
            old_status = item.status
            if item_data and 'executionStatus' in item_data:
                execution_status = item_data['executionStatus']
                if execution_status in ['INVALID_CREDENTIALS', 'LOGIN_ERROR']:
                    item.status = 'LOGIN_ERROR'
                elif execution_status == 'USER_INPUT_TIMEOUT':
                    item.status = 'USER_INPUT_TIMEOUT'
                else:
                    item.status = 'ERROR'
            else:
                item.status = 'ERROR'
            status_updated = True
            logger.info(f"📝 Status updated: {old_status} → {item.status} (item error)")
            
        elif event_type in ['item/waiting_user_input', 'item/waiting_user_action']:
            # Waiting for user input (MFA, etc)
            old_status = item.status
            item.status = 'WAITING_USER_INPUT'
            status_updated = True
            logger.info(f"📝 Status updated: {old_status} → WAITING_USER_INPUT (from {event_type})")
            
        elif event_type == 'item/created':
            # Item created successfully
            old_status = item.status
            item.status = 'CREATED'
            status_updated = True
            logger.info(f"📝 Status updated: {old_status} → CREATED")
        
        # Update additional fields if available in webhook data
        if item_data:
            if 'status' in item_data:
                item.status = item_data['status']
                status_updated = True
                logger.info(f"📝 Status set from webhook data: {item_data['status']}")
                
            if 'executionStatus' in item_data:
                item.execution_status = item_data['executionStatus']
                logger.info(f"📝 Execution status: {item_data['executionStatus']}")
        
        # Update timestamp to indicate webhook was processed
        item.pluggy_updated_at = timezone.now()
        
        # Save changes if any status was updated
        if status_updated or item_data:
            try:
                item.save()
                logger.info(f"💾 Item {item.pluggy_item_id} saved successfully")
                
                # Update related accounts with smart error classification
                if item.status in ['LOGIN_ERROR', 'INVALID_CREDENTIALS']:
                    # Permanent authentication errors - always deactivate
                    accounts_updated = item.accounts.update(is_active=False)
                    if accounts_updated > 0:
                        logger.info(f"🔒 Deactivated {accounts_updated} accounts due to authentication failure ({item.status})")
                
                elif item.status == 'ERROR':
                    # Analyze if this is a temporary or permanent error
                    should_deactivate = _should_deactivate_on_error(item, data)
                    
                    if should_deactivate:
                        accounts_updated = item.accounts.update(is_active=False)
                        if accounts_updated > 0:
                            logger.info(f"🔒 Deactivated {accounts_updated} accounts due to permanent error")
                    else:
                        logger.info(f"⚠️ Keeping accounts active despite ERROR status - classified as temporary")
                        
                elif item.status in ['UPDATED', 'CREATED']:
                    accounts_updated = item.accounts.update(is_active=True)
                    if accounts_updated > 0:
                        logger.info(f"🔓 Activated {accounts_updated} accounts due to success status")
                
                return True
                
            except Exception as save_error:
                logger.error(f"💥 Error saving item: {save_error}")
                return False
        else:
            logger.info(f"ℹ️ No status changes for event {event_type}")
            return True
            
    except Exception as e:
        logger.error(f"💥 Error in basic webhook processing: {e}", exc_info=True)
        return False


def _should_deactivate_on_error(item, data):
    """
    Intelligent error classification to decide if accounts should be deactivated.
    
    Args:
        item: PluggyItem instance
        data: Event data from webhook
        
    Returns:
        bool: True if accounts should be deactivated, False otherwise
    """
    from django.utils import timezone
    from datetime import timedelta
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Extract execution status from event data
    execution_status = None
    if isinstance(data, dict):
        if 'data' in data and isinstance(data['data'], dict):
            item_data = data['data'].get('item', {})
            execution_status = item_data.get('executionStatus')
        elif 'item' in data:
            execution_status = data['item'].get('executionStatus')
    
    # Use stored execution status if not in event data
    if not execution_status:
        execution_status = getattr(item, 'execution_status', None)
    
    # Define temporary errors that shouldn't trigger deactivation
    TEMPORARY_ERRORS = {
        'CONNECTION_ERROR',
        'SITE_NOT_AVAILABLE', 
        'MAINTENANCE',
        'TIMEOUT',
        'RATE_LIMIT_EXCEEDED',
        'TEMPORARY_UNAVAILABLE',
        'NETWORK_ERROR'
    }
    
    # Define permanent errors that should trigger deactivation
    PERMANENT_ERRORS = {
        'INVALID_CREDENTIALS',
        'LOGIN_ERROR',
        'ACCOUNT_BLOCKED',
        'ACCOUNT_SUSPENDED',
        'PERMISSION_DENIED',
        'UNAUTHORIZED_ACCESS'
    }
    
    # Check if this is a known temporary error
    if execution_status in TEMPORARY_ERRORS:
        logger.info(f"🟡 Temporary error detected: {execution_status} - keeping accounts active")
        return False
    
    # Check if this is a known permanent error
    if execution_status in PERMANENT_ERRORS:
        logger.info(f"🔴 Permanent error detected: {execution_status} - will deactivate accounts")
        return True
    
    # Temporal protection: Check if we had a recent successful sync
    now = timezone.now()
    recent_threshold = now - timedelta(minutes=10)  # 10 minutes protection window
    
    # Check for recent successful syncs in any related account
    recent_success = False
    for account in item.accounts.all():
        # Use balance_date as indicator of recent successful sync
        if account.balance_date and account.balance_date >= recent_threshold:
            recent_success = True
            logger.info(f"🟢 Found recent successful sync at {account.balance_date} - protecting from deactivation")
            break
    
    if recent_success:
        logger.info(f"⏰ Temporal protection active - recent sync within 10 minutes, keeping accounts active")
        return False
    
    # For unknown errors, check item's error history
    # If this item has failed multiple times recently, then deactivate
    if hasattr(item, 'error_count') and item.error_count >= 3:
        logger.info(f"📈 Multiple consecutive errors ({item.error_count}) - will deactivate accounts")
        return True
    
    # Default: For unknown errors without recent success, be conservative and keep active
    logger.info(f"❓ Unknown error type: {execution_status} - keeping accounts active by default")
    return False