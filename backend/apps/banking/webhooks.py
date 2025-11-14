"""
Webhook handlers for Pluggy notifications.
Ref: https://docs.pluggy.ai/docs/webhooks
"""

import json
import hmac
import hashlib
import logging
import time
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

from . import tasks

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
    Handle webhooks from Pluggy - ASYNC VERSION WITH CELERY.
    Ref: https://docs.pluggy.ai/reference/webhooks-list

    CRITICAL REQUIREMENTS:
    - Pluggy requires 2XX response within 5 seconds or retries up to 3 times
    - After 3 retries, the webhook is PERMANENTLY LOST

    This handler:
    1. Validates signature and payload (< 100ms)
    2. Checks idempotency via eventId caching
    3. Returns 200 OK IMMEDIATELY
    4. Delegates processing to Celery async tasks

    Processing happens asynchronously in background workers.
    """
    start_time = time.time()

    # Log incoming webhook
    logger.info(f"Webhook received - Headers: {dict(request.headers)}")
    logger.info(f"Webhook body: {request.body[:500]}")  # Log first 500 chars

    # Verify signature if provided
    signature = request.headers.get('X-Webhook-Signature', '')
    if signature and not verify_webhook_signature(request.body, signature):
        logger.warning("Invalid webhook signature")
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"Webhook rejected (invalid signature) - Response time: {elapsed:.2f}ms")
        return HttpResponse(status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        event_type = payload.get('event')
        item_id = payload.get('itemId')
        event_id = payload.get('eventId')

        logger.info(f"Received webhook: {event_type} for item {item_id} (eventId: {event_id})")

        # Idempotency: Check if event was already processed
        # Ref: https://docs.pluggy.ai/docs/webhooks (use eventId for deduplication)
        if event_id:
            cache_key = f"pluggy_event_{event_id}"
            if cache.get(cache_key):
                elapsed = (time.time() - start_time) * 1000
                logger.info(
                    f"Duplicate webhook detected - Event {event_id} ({event_type}) already processed. "
                    f"Skipping to prevent duplicate processing (idempotency). Item: {item_id}. "
                    f"Response time: {elapsed:.2f}ms"
                )
                return JsonResponse({'status': 'ok', 'processed': False, 'reason': 'duplicate'})

            # Mark event as processed (expires in 7 days)
            cache.set(cache_key, True, timeout=60*60*24*7)

        # Dispatch to appropriate Celery task based on event type
        # This happens asynchronously - the task is queued and we return immediately
        task_dispatched = False

        if event_type == 'item/updated':
            tasks.process_item_updated.delay(item_id, payload)
            task_dispatched = True
        elif event_type == 'item/created':
            tasks.process_item_created.delay(item_id, payload)
            task_dispatched = True
        elif event_type == 'item/error':
            tasks.process_item_error.delay(item_id, payload)
            task_dispatched = True
        elif event_type == 'item/deleted':
            tasks.process_item_deleted.delay(item_id, payload)
            task_dispatched = True
        elif event_type == 'item/waiting_user_input':
            tasks.process_item_mfa.delay(item_id, payload)
            task_dispatched = True
        elif event_type == 'item/login_succeeded':
            tasks.process_item_login_succeeded.delay(item_id, payload)
            task_dispatched = True
        elif event_type == 'transactions/created':
            tasks.process_transactions_created.delay(item_id, payload)
            task_dispatched = True
        elif event_type == 'transactions/updated':
            tasks.process_transactions_updated.delay(item_id, payload)
            task_dispatched = True
        elif event_type == 'transactions/deleted':
            tasks.process_transactions_deleted.delay(item_id, payload)
            task_dispatched = True
        elif event_type == 'connector/status_updated':
            tasks.process_connector_status.delay(payload)
            task_dispatched = True
        else:
            logger.warning(f"Unknown webhook event type: {event_type}")
            # Still return OK for unknown events

        elapsed = (time.time() - start_time) * 1000
        logger.info(
            f"Webhook {event_type} accepted and queued for processing. "
            f"Task dispatched: {task_dispatched}. Response time: {elapsed:.2f}ms"
        )

        return JsonResponse({
            'status': 'ok',
            'processed': True,
            'async': True,
            'event_type': event_type,
            'response_time_ms': round(elapsed, 2)
        })

    except json.JSONDecodeError:
        elapsed = (time.time() - start_time) * 1000
        logger.error(f"Invalid JSON in webhook payload - Response time: {elapsed:.2f}ms")
        return HttpResponse(status=400)
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        logger.error(f"Error processing webhook: {e} - Response time: {elapsed:.2f}ms")
        # IMPORTANT: Return 200 OK even on error to prevent unnecessary retries
        # The error is logged and can be investigated later
        return JsonResponse({
            'status': 'ok',
            'processed': False,
            'error': 'internal_error',
            'response_time_ms': round(elapsed, 2)
        })
