"""
Middleware for handling database deadlocks and retries
"""
import time
import logging
from django.db import OperationalError, transaction
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class DeadlockRetryMiddleware:
    """
    Middleware to automatically retry requests that fail due to database deadlocks.
    This is particularly important for webhook processing where multiple concurrent
    requests might try to create the same objects.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.max_retries = 3
        self.retry_delay = 0.1  # 100ms initial delay

    def __call__(self, request):
        # Only apply retry logic to webhook endpoints
        if '/webhook/' not in request.path and '/stripe/' not in request.path:
            return self.get_response(request)

        for attempt in range(self.max_retries):
            try:
                # Clear any existing atomic blocks
                if transaction.get_autocommit():
                    response = self.get_response(request)
                else:
                    # If we're in a transaction, rollback and retry
                    transaction.set_rollback(True)
                    transaction.set_autocommit(True)
                    response = self.get_response(request)

                return response

            except OperationalError as e:
                # Check if it's a deadlock error
                if 'deadlock detected' in str(e).lower() or 'impasse detectado' in str(e).lower():
                    if attempt < self.max_retries - 1:
                        # Exponential backoff
                        delay = self.retry_delay * (2 ** attempt)
                        logger.warning(
                            f"Deadlock detected on attempt {attempt + 1}/{self.max_retries}. "
                            f"Retrying in {delay}s... Path: {request.path}"
                        )
                        time.sleep(delay)

                        # Rollback any partial transaction
                        try:
                            transaction.rollback()
                        except:
                            pass

                        continue
                    else:
                        logger.error(
                            f"Deadlock persisted after {self.max_retries} attempts. "
                            f"Path: {request.path}"
                        )
                        return JsonResponse({
                            'error': 'Database deadlock - please retry',
                            'detail': 'The request could not be processed due to database contention'
                        }, status=503)
                else:
                    # Not a deadlock, re-raise
                    raise

        # Should never reach here, but just in case
        return self.get_response(request)


class WebhookSerializationMiddleware:
    """
    Middleware to add a small delay between webhook processing to reduce concurrent access.
    This helps prevent deadlocks when multiple webhooks arrive simultaneously.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.last_webhook_time = {}
        self.min_interval = 0.15  # 150ms between webhooks to reduce deadlock risk

    def __call__(self, request):
        # Only apply to Stripe webhooks
        if '/stripe/webhook/' in request.path:
            # Extract webhook endpoint from path
            endpoint_id = request.path.split('/webhook/')[-1].rstrip('/')

            # Check if we need to wait
            if endpoint_id in self.last_webhook_time:
                elapsed = time.time() - self.last_webhook_time[endpoint_id]
                if elapsed < self.min_interval:
                    wait_time = self.min_interval - elapsed
                    logger.debug(f"Delaying webhook processing by {wait_time:.3f}s to prevent deadlock")
                    time.sleep(wait_time)

            # Update last webhook time
            self.last_webhook_time[endpoint_id] = time.time()

        return self.get_response(request)
