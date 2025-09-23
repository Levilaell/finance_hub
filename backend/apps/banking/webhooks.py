"""
Pluggy webhook handlers
"""
import json
import logging
import hmac
import hashlib
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone

from .models import PluggyItem, ItemWebhook
from .integrations.pluggy.sync_service import PluggySyncService

logger = logging.getLogger('apps.banking.webhooks')


def verify_webhook_signature(request):
    """Verify Pluggy webhook signature"""
    webhook_secret = getattr(settings, 'PLUGGY_WEBHOOK_SECRET', '')
    
    if not webhook_secret:
        logger.warning("PLUGGY_WEBHOOK_SECRET not configured, skipping signature verification")
        return True
    
    signature = request.headers.get('X-Pluggy-Signature')
    if not signature:
        logger.error("Missing X-Pluggy-Signature header")
        return False
    
    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
        signature = signature[7:]
    
    # Calculate expected signature
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        request.body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    if not hmac.compare_digest(signature, expected_signature):
        logger.error(f"Invalid webhook signature. Expected: {expected_signature}, Got: {signature}")
        return False
    
    return True


@method_decorator(csrf_exempt, name='dispatch')
class PluggyWebhookView(View):
    """
    Handle Pluggy webhook events
    """
    
    def post(self, request):
        """Process incoming webhook"""
        
        # Verify signature
        if not verify_webhook_signature(request):
            return HttpResponseBadRequest("Invalid signature")
        
        try:
            # Parse JSON payload
            payload = json.loads(request.body)
            
            # Extract event data
            event_type = payload.get('event')
            event_id = payload.get('id')
            data = payload.get('data', {})
            
            if not event_type or not event_id:
                logger.error(f"Invalid webhook payload: {payload}")
                return HttpResponseBadRequest("Invalid payload")
            
            logger.info(f"Received webhook: {event_type} ({event_id})")
            
            # Find the item
            item_id = data.get('itemId')
            if not item_id:
                logger.error(f"No itemId in webhook data: {data}")
                return HttpResponseBadRequest("Missing itemId")
            
            try:
                item = PluggyItem.objects.get(pluggy_item_id=item_id)
            except PluggyItem.DoesNotExist:
                logger.warning(f"Item {item_id} not found in database")
                # Return 200 to prevent retries for unknown items
                return HttpResponse("Item not found", status=200)
            
            # Create webhook record
            webhook = ItemWebhook.objects.create(
                item=item,
                event_type=event_type,
                event_id=event_id,
                payload=payload,
                triggered_by='CLIENT'
            )
            
            # Process the webhook
            success = self.process_webhook(webhook, item, event_type, data)
            
            if success:
                webhook.mark_as_processed()
                return HttpResponse("OK")
            else:
                webhook.mark_as_processed(error="Processing failed")
                return HttpResponse("Processing failed", status=500)
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            return HttpResponseBadRequest("Invalid JSON")
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return HttpResponse("Internal error", status=500)
    
    def process_webhook(self, webhook, item, event_type, data):
        """Process specific webhook event"""
        
        try:
            sync_service = PluggySyncService()
            
            if event_type == 'item.created':
                return self.handle_item_created(sync_service, item, data)
            
            elif event_type == 'item.updated':
                return self.handle_item_updated(sync_service, item, data)
            
            elif event_type == 'item.error':
                return self.handle_item_error(sync_service, item, data)
            
            elif event_type == 'item.login_succeeded':
                return self.handle_login_succeeded(sync_service, item, data)
            
            elif event_type == 'item.waiting_user_input':
                return self.handle_waiting_user_input(sync_service, item, data)
            
            elif event_type == 'transactions.created':
                return self.handle_transactions_created(sync_service, item, data)
            
            elif event_type == 'transactions.updated':
                return self.handle_transactions_updated(sync_service, item, data)
            
            elif event_type == 'transactions.deleted':
                return self.handle_transactions_deleted(sync_service, item, data)
            
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return True  # Mark as processed even if we don't handle it
                
        except Exception as e:
            logger.error(f"Error processing webhook {event_type}: {e}")
            return False
    
    def handle_item_created(self, sync_service, item, data):
        """Handle item.created event"""
        logger.info(f"Item {item.id} created successfully")
        
        # Update item status
        sync_service.sync_item_status(item)
        
        return True
    
    def handle_item_updated(self, sync_service, item, data):
        """Handle item.updated event"""
        logger.info(f"Item {item.id} updated, syncing data")
        
        # Sync item status and data
        sync_service.sync_item_status(item)
        
        # If item is in good state, sync accounts and transactions
        if item.is_connected:
            try:
                # Sync accounts first
                sync_service.sync_accounts(item)
                
                # Then sync recent transactions for all accounts
                for account in item.accounts.filter(is_active=True):
                    sync_service.sync_transactions(
                        account=account,
                        from_date=timezone.now() - timezone.timedelta(days=7)
                    )
                    
            except Exception as e:
                logger.error(f"Failed to sync data for item {item.id}: {e}")
                return False
        
        return True
    
    def handle_item_error(self, sync_service, item, data):
        """Handle item.error event"""
        logger.warning(f"Item {item.id} has error")
        
        # Update item status to capture error details
        sync_service.sync_item_status(item)
        
        return True
    
    def handle_login_succeeded(self, sync_service, item, data):
        """Handle item.login_succeeded event"""
        logger.info(f"Login succeeded for item {item.id}")
        
        # Update status and start syncing data
        sync_service.sync_item_status(item)
        
        return True
    
    def handle_waiting_user_input(self, sync_service, item, data):
        """Handle item.waiting_user_input event"""
        logger.info(f"Item {item.id} waiting for user input")
        
        # Update status
        sync_service.sync_item_status(item)
        
        # TODO: Notify user that action is required
        
        return True
    
    def handle_transactions_created(self, sync_service, item, data):
        """Handle transactions.created event"""
        logger.info(f"New transactions created for item {item.id}")
        
        # Sync recent transactions
        try:
            for account in item.accounts.filter(is_active=True):
                sync_service.sync_transactions(
                    account=account,
                    from_date=timezone.now() - timezone.timedelta(days=7)
                )
        except Exception as e:
            logger.error(f"Failed to sync new transactions for item {item.id}: {e}")
            return False
        
        return True
    
    def handle_transactions_updated(self, sync_service, item, data):
        """Handle transactions.updated event"""
        logger.info(f"Transactions updated for item {item.id}")
        
        # Sync recent transactions
        try:
            for account in item.accounts.filter(is_active=True):
                sync_service.sync_transactions(
                    account=account,
                    from_date=timezone.now() - timezone.timedelta(days=30)
                )
        except Exception as e:
            logger.error(f"Failed to sync updated transactions for item {item.id}: {e}")
            return False
        
        return True
    
    def handle_transactions_deleted(self, sync_service, item, data):
        """Handle transactions.deleted event"""
        logger.info(f"Transactions deleted for item {item.id}")
        
        # TODO: Implement transaction deletion logic
        # For now, we'll do a full resync to ensure consistency
        try:
            for account in item.accounts.filter(is_active=True):
                sync_service.sync_transactions(
                    account=account,
                    from_date=timezone.now() - timezone.timedelta(days=90)
                )
        except Exception as e:
            logger.error(f"Failed to resync transactions for item {item.id}: {e}")
            return False
        
        return True


# Create the webhook view instance
pluggy_webhook_view = PluggyWebhookView.as_view()


@csrf_exempt
@require_http_methods(["POST"])
def pluggy_webhook(request):
    """
    Simple function-based webhook handler
    """
    return pluggy_webhook_view(request)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def webhook_test(request):
    """
    Test endpoint for webhook validation
    """
    if request.method == 'GET':
        # Pluggy might send GET requests to validate the endpoint
        return HttpResponse("Webhook endpoint active")
    
    # For POST, just log and return OK
    logger.info(f"Test webhook received: {request.body}")
    return HttpResponse("Test webhook received")


# Webhook URL patterns
def get_webhook_urls():
    """Get webhook URL patterns"""
    from django.urls import path
    
    return [
        path('webhooks/pluggy/', pluggy_webhook, name='pluggy-webhook'),
        path('webhooks/test/', webhook_test, name='webhook-test'),
    ]