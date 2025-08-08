"""Retry service for payment operations and webhooks"""
import logging
from django.utils import timezone
from django.db import transaction, models
from celery import shared_task
from typing import Optional, Dict, Any
import time
import random

logger = logging.getLogger(__name__)


class RetryService:
    """Service for handling retries with exponential backoff"""
    
    # Default retry configuration
    DEFAULT_MAX_RETRIES = 5
    DEFAULT_BASE_DELAY = 1  # seconds
    DEFAULT_MAX_DELAY = 300  # 5 minutes
    DEFAULT_JITTER = True
    
    @classmethod
    def calculate_backoff(cls, attempt: int, base_delay: float = None, 
                         max_delay: float = None, jitter: bool = None) -> float:
        """Calculate exponential backoff with optional jitter"""
        base_delay = base_delay or cls.DEFAULT_BASE_DELAY
        max_delay = max_delay or cls.DEFAULT_MAX_DELAY
        jitter = jitter if jitter is not None else cls.DEFAULT_JITTER
        
        # Exponential backoff: base * 2^attempt
        delay = min(base_delay * (2 ** attempt), max_delay)
        
        # Add jitter to prevent thundering herd
        if jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    @classmethod
    def should_retry(cls, error: Exception) -> bool:
        """Determine if an error is retryable"""
        from ..exceptions import PaymentRetryableException, PaymentException
        import stripe
        
        # Explicitly retryable exceptions
        if isinstance(error, PaymentRetryableException):
            return True
        
        # Non-retryable payment exceptions
        if isinstance(error, PaymentException):
            return False
        
        # Stripe-specific retryable errors
        if isinstance(error, stripe.error.RateLimitError):
            return True
        if isinstance(error, stripe.error.APIConnectionError):
            return True
        if isinstance(error, stripe.error.StripeError):
            # Check for specific error codes
            if hasattr(error, 'code') and error.code in [
                'lock_timeout', 'rate_limit', 'processing_error'
            ]:
                return True
        
        # Network and timeout errors
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True
        
        return False
    
    @classmethod
    def retry_with_backoff(cls, func, max_retries: int = None, **kwargs):
        """Execute function with retry logic"""
        max_retries = max_retries or cls.DEFAULT_MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if not cls.should_retry(e) or attempt == max_retries - 1:
                    raise
                
                delay = cls.calculate_backoff(attempt, **kwargs)
                logger.warning(
                    f"Retry attempt {attempt + 1}/{max_retries} after {delay:.2f}s: {e}"
                )
                time.sleep(delay)
        
        raise Exception("Max retries exceeded")


@shared_task(bind=True, max_retries=3)
def retry_failed_webhook(self, webhook_id: int):
    """Celery task to retry failed webhooks"""
    from ..models import FailedWebhook
    from ..services.webhook_handler import WebhookHandler
    from ..services.payment_gateway import StripeGateway
    
    try:
        webhook = FailedWebhook.objects.get(id=webhook_id)
        
        if not webhook.should_retry():
            logger.warning(f"Webhook {webhook_id} exceeded max retries")
            return
        
        # Process the webhook
        gateway = StripeGateway()
        handler = WebhookHandler(gateway)
        
        with transaction.atomic():
            result = handler.handle_stripe_webhook(webhook.event_data)
            
            # Success - delete the failed webhook record
            webhook.delete()
            logger.info(f"Successfully retried webhook {webhook_id}")
            return result
            
    except FailedWebhook.DoesNotExist:
        logger.error(f"Failed webhook {webhook_id} not found")
        return
        
    except Exception as e:
        logger.error(f"Failed to retry webhook {webhook_id}: {e}")
        
        # Update retry count and schedule next retry
        try:
            webhook.increment_retry()
            
            # Schedule next retry
            if webhook.should_retry():
                retry_after = (webhook.next_retry_at - timezone.now()).total_seconds()
                retry_after = max(retry_after, 60)  # Minimum 1 minute
                
                self.retry(countdown=retry_after)
        except Exception as update_error:
            logger.error(f"Failed to update webhook retry: {update_error}")
        
        raise


@shared_task
def process_webhook_retry_queue():
    """Process all pending webhook retries"""
    from ..models import FailedWebhook
    
    pending_webhooks = FailedWebhook.objects.filter(
        next_retry_at__lte=timezone.now(),
        retry_count__lt=models.F('max_retries')
    ).order_by('next_retry_at')[:10]  # Process 10 at a time
    
    for webhook in pending_webhooks:
        retry_failed_webhook.delay(webhook.id)
    
    return f"Scheduled {len(pending_webhooks)} webhooks for retry"


class PaymentRetryService:
    """Service for retrying payment operations"""
    
    @staticmethod
    def retry_payment(payment_id: int, reason: str = None) -> Dict[str, Any]:
        """Retry a failed payment"""
        from ..models import Payment
        from ..services.payment_gateway import PaymentService
        
        try:
            payment = Payment.objects.get(id=payment_id)
            
            if payment.status not in ['failed', 'processing']:
                return {
                    'success': False,
                    'error': 'Payment cannot be retried in current status'
                }
            
            # Check if payment method is still valid
            if not payment.payment_method or not payment.payment_method.stripe_payment_method_id:
                return {
                    'success': False,
                    'error': 'No valid payment method found'
                }
            
            service = PaymentService()
            
            # Attempt to process payment again
            # This would depend on your specific payment flow
            # For subscriptions, this might involve retrying the invoice
            
            logger.info(f"Retrying payment {payment_id} - {reason}")
            
            # Update payment status
            payment.status = 'processing'
            payment.metadata['retry_reason'] = reason
            payment.metadata['retry_at'] = timezone.now().isoformat()
            payment.save()
            
            return {
                'success': True,
                'payment_id': payment_id
            }
            
        except Payment.DoesNotExist:
            return {
                'success': False,
                'error': 'Payment not found'
            }
        except Exception as e:
            logger.error(f"Failed to retry payment {payment_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


@shared_task
def check_and_retry_failed_payments():
    """Check for failed payments that can be retried"""
    from ..models import Payment
    from datetime import timedelta
    
    # Find recent failed payments
    cutoff_time = timezone.now() - timedelta(hours=24)
    failed_payments = Payment.objects.filter(
        status='failed',
        created_at__gte=cutoff_time,
        payment_method__isnull=False
    ).exclude(
        metadata__contains={'retry_count': 3}  # Max 3 retries
    )
    
    retry_service = PaymentRetryService()
    results = []
    
    for payment in failed_payments[:5]:  # Process 5 at a time
        result = retry_service.retry_payment(
            payment.id, 
            reason='Automated retry for failed payment'
        )
        results.append(result)
    
    return f"Processed {len(results)} failed payments for retry"