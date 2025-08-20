"""
Payment Retry Service
Handles automatic retry logic for failed payments with intelligent backoff
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from .stripe_service import StripeService
from .audit_service import PaymentAuditService
from .notification_service import notification_service
from ..models import Payment, Subscription, PaymentRetry

logger = logging.getLogger(__name__)


class PaymentRetryService:
    """Service for handling payment retries with intelligent backoff and limits"""
    
    # Default retry configuration
    DEFAULT_CONFIG = {
        'max_retries': 3,
        'base_delay_minutes': 60,  # Start with 1 hour
        'max_delay_hours': 24,     # Maximum 24 hours between retries
        'backoff_multiplier': 2.0,  # Exponential backoff
        'retry_window_days': 7,    # Stop retrying after 7 days
    }
    
    # Retry-eligible error codes
    RETRYABLE_ERRORS = {
        'card_declined',
        'insufficient_funds',
        'temporary_failure',
        'processing_error',
        'authentication_required',
        'generic_decline'
    }
    
    # Non-retryable error codes (permanent failures)
    NON_RETRYABLE_ERRORS = {
        'invalid_cvc',
        'expired_card',
        'incorrect_number',
        'stolen_card',
        'lost_card',
        'pickup_card',
        'restricted_card',
        'security_violation'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.stripe_service = StripeService()
        
    @transaction.atomic
    def handle_payment_failure(
        self, 
        payment: Payment, 
        error_code: str, 
        error_message: str,
        stripe_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle a payment failure and determine retry strategy
        
        Args:
            payment: The failed payment
            error_code: Error code from payment gateway
            error_message: Error message from payment gateway
            stripe_data: Additional Stripe data
            
        Returns:
            Dict with retry decision and next action
        """
        
        # Check if error is retryable
        if not self._is_retryable_error(error_code):
            logger.info(f"Payment {payment.id} failed with non-retryable error: {error_code}")
            return self._handle_permanent_failure(payment, error_code, error_message)
        
        # Get or create retry record
        retry_record = self._get_or_create_retry_record(payment)
        
        # Check if we've exceeded retry limits
        if not self._can_retry(retry_record):
            logger.warning(f"Payment {payment.id} exceeded retry limits")
            return self._handle_retry_exhausted(payment, retry_record)
        
        # Calculate next retry time
        next_retry_at = self._calculate_next_retry_time(retry_record)
        
        # Update retry record
        retry_record.attempt_count += 1
        retry_record.last_error_code = error_code
        retry_record.last_error_message = error_message
        retry_record.next_retry_at = next_retry_at
        retry_record.last_attempt_at = timezone.now()
        retry_record.stripe_data = stripe_data or {}
        retry_record.save()
        
        # Log retry scheduling
        PaymentAuditService.log_payment_action(
            action='payment_retry_scheduled',
            company=payment.company,
            subscription_id=payment.subscription.id if payment.subscription else None,
            payment_id=payment.id,
            metadata={
                'attempt_count': retry_record.attempt_count,
                'next_retry_at': next_retry_at.isoformat(),
                'error_code': error_code,
                'error_message': error_message
            }
        )
        
        # Schedule retry
        self._schedule_retry(payment, retry_record)
        
        # Notify user about retry
        self._notify_retry_scheduled(payment, retry_record)
        
        return {
            'action': 'retry_scheduled',
            'next_retry_at': next_retry_at,
            'attempt_count': retry_record.attempt_count,
            'max_retries': self.config['max_retries']
        }
    
    def execute_retry(self, payment_id: int) -> Dict[str, Any]:
        """
        Execute a scheduled payment retry
        
        Args:
            payment_id: ID of the payment to retry
            
        Returns:
            Dict with retry result
        """
        try:
            payment = Payment.objects.select_related('subscription', 'company').get(id=payment_id)
            retry_record = PaymentRetry.objects.filter(payment=payment).first()
            
            if not retry_record:
                return {'success': False, 'error': 'No retry record found'}
            
            if not self._can_retry(retry_record):
                return self._handle_retry_exhausted(payment, retry_record)
            
            logger.info(f"Executing retry for payment {payment.id}, attempt {retry_record.attempt_count + 1}")
            
            # Execute the retry via Stripe
            retry_result = self._execute_stripe_retry(payment, retry_record)
            
            if retry_result['success']:
                # Retry succeeded
                retry_record.status = 'completed'
                retry_record.completed_at = timezone.now()
                retry_record.save()
                
                # Update payment status
                payment.status = 'succeeded'
                payment.paid_at = timezone.now()
                payment.save()
                
                # Log success
                PaymentAuditService.log_payment_action(
                    action='payment_retry_succeeded',
                    company=payment.company,
                    subscription_id=payment.subscription.id if payment.subscription else None,
                    payment_id=payment.id,
                    metadata={
                        'attempt_count': retry_record.attempt_count + 1,
                        'final_attempt': True
                    }
                )
                
                # Notify success
                notification_service.notify_payment_success(
                    payment.company.id,
                    {
                        'payment_id': payment.id,
                        'subscription_id': payment.subscription.id if payment.subscription else None,
                        'amount': float(payment.amount),
                        'currency': payment.currency,
                        'retry_attempt': retry_record.attempt_count + 1
                    }
                )
                
                return {'success': True, 'payment_id': payment.id}
                
            else:
                # Retry failed - schedule next retry or give up
                error_code = retry_result.get('error_code', 'unknown_error')
                error_message = retry_result.get('error_message', 'Unknown error')
                
                return self.handle_payment_failure(
                    payment, 
                    error_code, 
                    error_message,
                    retry_result.get('stripe_data')
                )
                
        except Payment.DoesNotExist:
            logger.error(f"Payment {payment_id} not found for retry")
            return {'success': False, 'error': 'Payment not found'}
        except Exception as e:
            logger.error(f"Error executing payment retry for {payment_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_retry_status(self, payment: Payment) -> Optional[Dict[str, Any]]:
        """
        Get retry status for a payment
        
        Args:
            payment: The payment to check
            
        Returns:
            Dict with retry status or None if no retries
        """
        retry_record = PaymentRetry.objects.filter(payment=payment).first()
        
        if not retry_record:
            return None
        
        return {
            'status': retry_record.status,
            'attempt_count': retry_record.attempt_count,
            'max_retries': self.config['max_retries'],
            'next_retry_at': retry_record.next_retry_at.isoformat() if retry_record.next_retry_at else None,
            'last_error_code': retry_record.last_error_code,
            'last_error_message': retry_record.last_error_message,
            'can_retry': self._can_retry(retry_record)
        }
    
    def cancel_retries(self, payment: Payment, reason: str = "Cancelled by user") -> bool:
        """
        Cancel scheduled retries for a payment
        
        Args:
            payment: The payment to cancel retries for
            reason: Reason for cancellation
            
        Returns:
            True if cancelled, False if no retries to cancel
        """
        retry_record = PaymentRetry.objects.filter(
            payment=payment,
            status='active'
        ).first()
        
        if not retry_record:
            return False
        
        retry_record.status = 'cancelled'
        retry_record.cancelled_at = timezone.now()
        retry_record.save()
        
        # Log cancellation
        PaymentAuditService.log_payment_action(
            action='payment_retry_cancelled',
            company=payment.company,
            subscription_id=payment.subscription.id if payment.subscription else None,
            payment_id=payment.id,
            metadata={
                'reason': reason,
                'attempt_count': retry_record.attempt_count
            }
        )
        
        return True
    
    def _is_retryable_error(self, error_code: str) -> bool:
        """Check if an error code is retryable"""
        if error_code in self.NON_RETRYABLE_ERRORS:
            return False
        
        # If it's explicitly retryable or unknown (be conservative with retries)
        return error_code in self.RETRYABLE_ERRORS
    
    def _get_or_create_retry_record(self, payment: Payment) -> PaymentRetry:
        """Get or create a retry record for a payment"""
        retry_record, created = PaymentRetry.objects.get_or_create(
            payment=payment,
            defaults={
                'status': 'active',
                'attempt_count': 0,
                'created_at': timezone.now()
            }
        )
        return retry_record
    
    def _can_retry(self, retry_record: PaymentRetry) -> bool:
        """Check if a payment can be retried"""
        if retry_record.status != 'active':
            return False
        
        if retry_record.attempt_count >= self.config['max_retries']:
            return False
        
        # Check if we're within the retry window
        retry_window = timedelta(days=self.config['retry_window_days'])
        if timezone.now() > (retry_record.created_at + retry_window):
            return False
        
        return True
    
    def _calculate_next_retry_time(self, retry_record: PaymentRetry) -> datetime:
        """Calculate the next retry time using exponential backoff"""
        base_delay = self.config['base_delay_minutes']
        multiplier = self.config['backoff_multiplier']
        max_delay_hours = self.config['max_delay_hours']
        
        # Calculate delay with exponential backoff
        delay_minutes = base_delay * (multiplier ** retry_record.attempt_count)
        
        # Cap at maximum delay
        delay_minutes = min(delay_minutes, max_delay_hours * 60)
        
        return timezone.now() + timedelta(minutes=delay_minutes)
    
    def _schedule_retry(self, payment: Payment, retry_record: PaymentRetry):
        """Schedule a payment retry using Celery"""
        try:
            from ..tasks import execute_payment_retry
            
            # Schedule the retry task
            execute_payment_retry.apply_async(
                args=[payment.id],
                eta=retry_record.next_retry_at
            )
            
            logger.info(f"Scheduled retry for payment {payment.id} at {retry_record.next_retry_at}")
            
        except Exception as e:
            logger.error(f"Failed to schedule retry for payment {payment.id}: {e}")
            # Continue without Celery - the retry can be executed manually or by cron
    
    def _execute_stripe_retry(self, payment: Payment, retry_record: PaymentRetry) -> Dict[str, Any]:
        """Execute the actual retry via Stripe"""
        try:
            if payment.subscription and payment.subscription.stripe_subscription_id:
                # For subscription payments, trigger a manual payment
                result = self.stripe_service.retry_subscription_payment(
                    payment.subscription.stripe_subscription_id
                )
            else:
                # For one-time payments, create a new payment intent
                result = self.stripe_service.retry_payment_intent(
                    payment.stripe_payment_intent_id,
                    payment.amount,
                    payment.currency
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Stripe retry failed for payment {payment.id}: {e}")
            return {
                'success': False,
                'error_code': 'stripe_error',
                'error_message': str(e)
            }
    
    def _handle_permanent_failure(self, payment: Payment, error_code: str, error_message: str) -> Dict[str, Any]:
        """Handle a permanent payment failure (non-retryable)"""
        payment.status = 'failed'
        payment.save()
        
        # Log permanent failure
        PaymentAuditService.log_payment_action(
            action='payment_failed_permanently',
            company=payment.company,
            subscription_id=payment.subscription.id if payment.subscription else None,
            payment_id=payment.id,
            metadata={
                'error_code': error_code,
                'error_message': error_message,
                'retryable': False
            }
        )
        
        # Notify about permanent failure
        notification_service.notify_payment_failed(
            payment.company.id,
            {
                'payment_id': payment.id,
                'reason': f'Payment failed permanently: {error_message}',
                'retry_available': False,
                'error_code': error_code
            }
        )
        
        return {
            'action': 'permanent_failure',
            'error_code': error_code,
            'error_message': error_message,
            'retry_available': False
        }
    
    def _handle_retry_exhausted(self, payment: Payment, retry_record: PaymentRetry) -> Dict[str, Any]:
        """Handle when all retries have been exhausted"""
        retry_record.status = 'exhausted'
        retry_record.save()
        
        payment.status = 'failed'
        payment.save()
        
        # Log retry exhaustion
        PaymentAuditService.log_payment_action(
            action='payment_retries_exhausted',
            company=payment.company,
            subscription_id=payment.subscription.id if payment.subscription else None,
            payment_id=payment.id,
            metadata={
                'attempt_count': retry_record.attempt_count,
                'max_retries': self.config['max_retries'],
                'last_error_code': retry_record.last_error_code
            }
        )
        
        # Notify about retry exhaustion
        notification_service.notify_payment_failed(
            payment.company.id,
            {
                'payment_id': payment.id,
                'reason': f'Payment failed after {retry_record.attempt_count} retry attempts',
                'retry_available': False,
                'retries_exhausted': True
            }
        )
        
        return {
            'action': 'retries_exhausted',
            'attempt_count': retry_record.attempt_count,
            'max_retries': self.config['max_retries'],
            'retry_available': False
        }
    
    def _notify_retry_scheduled(self, payment: Payment, retry_record: PaymentRetry):
        """Notify user that a retry has been scheduled"""
        notification_service.notify_payment_failed(
            payment.company.id,
            {
                'payment_id': payment.id,
                'reason': f'Payment failed, retry scheduled for {retry_record.next_retry_at.strftime("%H:%M")}',
                'retry_available': True,
                'next_retry_at': retry_record.next_retry_at.isoformat(),
                'attempt_count': retry_record.attempt_count,
                'max_retries': self.config['max_retries']
            }
        )


# Singleton instance
payment_retry_service = PaymentRetryService()