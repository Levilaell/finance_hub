"""
Comprehensive Error Handling Service
Provides unified error handling, circuit breaker, and monitoring
"""
import logging
import time
from typing import Dict, Any, Optional, Callable, Type
from functools import wraps
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import stripe

from ..exceptions import (
    PaymentException, StripeException, PaymentRetryableException,
    PaymentMethodException, SubscriptionException, WebhookException
)

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls
    Prevents cascading failures and provides graceful degradation
    """
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Type[Exception] = Exception):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception types to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self._failure_count = 0
        self._last_failure_time = None
        self._state = 'closed'  # closed, open, half-open
    
    @property
    def state(self):
        """Get current circuit state"""
        if self._state == 'open':
            if self._last_failure_time and \
               time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = 'half-open'
        return self._state
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == 'open':
            raise PaymentRetryableException(
                message="Service temporarily unavailable",
                details={"circuit_breaker": "open"},
                retry_after=self.recovery_timeout
            )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call"""
        self._failure_count = 0
        self._state = 'closed'
    
    def _on_failure(self):
        """Handle failed call"""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.failure_threshold:
            self._state = 'open'
            logger.error(f"Circuit breaker opened after {self._failure_count} failures")


class ErrorHandler:
    """Comprehensive error handling service"""
    
    # Circuit breakers for different services
    _stripe_circuit = CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=stripe.error.APIConnectionError
    )
    
    # Error code to user message mapping
    ERROR_MESSAGES = {
        'card_declined': 'Your card was declined. Please use a different payment method.',
        'insufficient_funds': 'Your card has insufficient funds.',
        'expired_card': 'Your card has expired. Please update your payment information.',
        'incorrect_cvc': 'The CVC code is incorrect. Please check and try again.',
        'processing_error': 'An error occurred while processing your payment. Please try again.',
        'rate_limit': 'Too many requests. Please wait a moment and try again.',
        'authentication_required': 'Your bank requires additional authentication.',
        'invalid_request': 'Invalid request. Please check your information and try again.',
        'api_connection_error': 'Connection error. Please check your internet and try again.',
        'invalid_payment_method': 'This payment method is invalid or no longer available.',
    }
    
    @classmethod
    def handle_stripe_error(cls, error: stripe.error.StripeError) -> PaymentException:
        """
        Convert Stripe error to appropriate PaymentException
        
        Args:
            error: Stripe error object
            
        Returns:
            Appropriate PaymentException subclass
        """
        # Log the error details
        logger.error(f"Stripe error: {type(error).__name__} - {str(error)}", 
                    extra={
                        'error_type': type(error).__name__,
                        'error_code': getattr(error, 'code', None),
                        'error_message': str(error),
                        'http_status': getattr(error, 'http_status', None),
                        'request_id': getattr(error, 'request_id', None),
                    })
        
        # Map Stripe errors to our exceptions
        if isinstance(error, stripe.error.CardError):
            # Get user-friendly message
            code = getattr(error, 'code', 'card_declined')
            message = cls.ERROR_MESSAGES.get(code, str(error))
            
            return PaymentMethodException(
                message=message,
                details={
                    'code': code,
                    'decline_code': getattr(error, 'decline_code', None),
                    'param': getattr(error, 'param', None),
                }
            )
        
        elif isinstance(error, stripe.error.RateLimitError):
            return PaymentRetryableException(
                message=cls.ERROR_MESSAGES.get('rate_limit'),
                retry_after=60
            )
        
        elif isinstance(error, stripe.error.InvalidRequestError):
            return PaymentException(
                message=cls.ERROR_MESSAGES.get('invalid_request'),
                details={'param': getattr(error, 'param', None)}
            )
        
        elif isinstance(error, stripe.error.AuthenticationError):
            logger.critical("Stripe authentication error - check API keys")
            return PaymentException(
                message="Payment service configuration error",
                details={'config_error': True}
            )
        
        elif isinstance(error, stripe.error.APIConnectionError):
            return PaymentRetryableException(
                message=cls.ERROR_MESSAGES.get('api_connection_error'),
                retry_after=30
            )
        
        elif isinstance(error, stripe.error.StripeError):
            # Generic Stripe error
            return StripeException.from_stripe_error(error)
        
        # Unknown error
        return PaymentException(
            message="An unexpected payment error occurred",
            details={'original_error': str(error)}
        )
    
    @classmethod
    def handle_exception(cls, error: Exception) -> PaymentException:
        """
        Handle any exception and convert to PaymentException
        
        Args:
            error: Any exception
            
        Returns:
            PaymentException instance
        """
        # If already a PaymentException, return as-is
        if isinstance(error, PaymentException):
            return error
        
        # Handle Stripe errors
        if isinstance(error, stripe.error.StripeError):
            return cls.handle_stripe_error(error)
        
        # Handle other known error types
        if isinstance(error, (ConnectionError, TimeoutError)):
            return PaymentRetryableException(
                message="Connection timeout. Please try again.",
                retry_after=30
            )
        
        if isinstance(error, ValueError):
            return PaymentException(
                message="Invalid input data",
                details={'validation_error': str(error)}
            )
        
        # Unknown error - log and return generic message
        logger.exception("Unexpected error in payment processing")
        return PaymentException(
            message="An unexpected error occurred. Please try again later.",
            details={'error_type': type(error).__name__}
        )
    
    @classmethod
    def with_circuit_breaker(cls, service: str = 'stripe'):
        """
        Decorator to apply circuit breaker to functions
        
        Args:
            service: Service name for circuit breaker
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                circuit = getattr(cls, f'_{service}_circuit', None)
                if circuit:
                    return circuit.call(func, *args, **kwargs)
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @classmethod
    def safe_execute(cls, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Safely execute a function with comprehensive error handling
        
        Args:
            func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Dict with 'success' and either 'result' or 'error'
        """
        try:
            result = func(*args, **kwargs)
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            error = cls.handle_exception(e)
            return {
                'success': False,
                'error': error.to_dict()
            }
    
    @classmethod
    def log_error(cls, 
                  error: Exception,
                  context: Dict[str, Any] = None,
                  user_id: Optional[int] = None,
                  company_id: Optional[int] = None):
        """
        Log error with structured context
        
        Args:
            error: Exception to log
            context: Additional context
            user_id: User ID if available
            company_id: Company ID if available
        """
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'user_id': user_id,
            'company_id': company_id,
            'timestamp': timezone.now().isoformat(),
        }
        
        if context:
            error_data.update(context)
        
        # Log based on error severity
        if isinstance(error, (stripe.error.AuthenticationError, stripe.error.PermissionError)):
            logger.critical("Critical payment error", extra=error_data)
        elif isinstance(error, PaymentRetryableException):
            logger.warning("Retryable payment error", extra=error_data)
        else:
            logger.error("Payment error", extra=error_data)
    
    @classmethod
    def get_error_metrics(cls, hours: int = 24) -> Dict[str, Any]:
        """
        Get error metrics for monitoring
        
        Args:
            hours: Hours to look back
            
        Returns:
            Dict with error metrics
        """
        cache_key = f'payment_error_metrics_{hours}h'
        metrics = cache.get(cache_key)
        
        if not metrics:
            # Calculate metrics (in production, query from logs/monitoring)
            metrics = {
                'total_errors': 0,
                'error_types': {},
                'circuit_breaker_state': cls._stripe_circuit.state,
                'retry_queue_size': 0,
                'last_updated': timezone.now().isoformat()
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, metrics, 300)
        
        return metrics


class RateLimitHandler:
    """Handle rate limiting with intelligent backoff"""
    
    @staticmethod
    def handle_rate_limit(user_id: int, 
                         endpoint: str,
                         limit: int = 60,
                         window: int = 60) -> Optional[int]:
        """
        Check and enforce rate limits
        
        Args:
            user_id: User making request
            endpoint: API endpoint
            limit: Max requests allowed
            window: Time window in seconds
            
        Returns:
            None if allowed, seconds until retry if limited
        """
        cache_key = f'rate_limit:{endpoint}:{user_id}'
        
        # Get current count
        current = cache.get(cache_key, 0)
        
        if current >= limit:
            # Calculate time until window resets
            ttl = cache.ttl(cache_key)
            return ttl if ttl > 0 else window
        
        # Increment counter
        cache.set(cache_key, current + 1, window)
        return None
    
    @staticmethod
    def get_rate_limit_headers(user_id: int, 
                              endpoint: str,
                              limit: int = 60) -> Dict[str, str]:
        """Get rate limit headers for response"""
        cache_key = f'rate_limit:{endpoint}:{user_id}'
        current = cache.get(cache_key, 0)
        
        return {
            'X-RateLimit-Limit': str(limit),
            'X-RateLimit-Remaining': str(max(0, limit - current)),
            'X-RateLimit-Reset': str(int(time.time()) + cache.ttl(cache_key))
        }


def payment_error_handler(func):
    """
    Decorator for automatic error handling on payment views
    
    Usage:
        @payment_error_handler
        def my_payment_view(request):
            # Your code here
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Get request object
            request = args[0] if args else None
            
            # Handle the error
            error = ErrorHandler.handle_exception(e)
            
            # Log the error with context
            ErrorHandler.log_error(
                error,
                context={
                    'view': func.__name__,
                    'method': getattr(request, 'method', 'Unknown'),
                    'path': getattr(request, 'path', 'Unknown'),
                },
                user_id=getattr(request.user, 'id', None) if request else None
            )
            
            # Return error response
            from rest_framework.response import Response
            return Response(
                error.to_dict(),
                status=error.status_code
            )
    
    return wrapper