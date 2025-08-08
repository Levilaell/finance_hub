"""Payment-related exceptions with proper error handling"""


class PaymentException(Exception):
    """Base exception for payment-related errors"""
    default_message = "A payment error occurred"
    error_code = "PAYMENT_ERROR"
    status_code = 400
    
    def __init__(self, message=None, details=None, retry_after=None):
        self.message = message or self.default_message
        self.details = details or {}
        self.retry_after = retry_after
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert exception to dictionary for API responses"""
        result = {
            'error': self.error_code,
            'message': self.message,
            'details': self.details
        }
        if self.retry_after:
            result['retry_after'] = self.retry_after
        return result


class StripeException(PaymentException):
    """Stripe-specific payment errors"""
    default_message = "Stripe payment processing error"
    error_code = "STRIPE_ERROR"
    
    @classmethod
    def from_stripe_error(cls, stripe_error):
        """Create exception from Stripe error object"""
        message = getattr(stripe_error, 'user_message', None) or str(stripe_error)
        details = {
            'stripe_error_type': type(stripe_error).__name__,
            'stripe_error_code': getattr(stripe_error, 'code', None),
            'decline_code': getattr(stripe_error, 'decline_code', None),
        }
        return cls(message=message, details=details)


class PaymentMethodException(PaymentException):
    """Payment method related errors"""
    default_message = "Payment method error"
    error_code = "PAYMENT_METHOD_ERROR"


class InvalidPaymentMethodException(PaymentMethodException):
    """Invalid payment method"""
    default_message = "The payment method is invalid or expired"
    error_code = "INVALID_PAYMENT_METHOD"


class PaymentMethodRequiredException(PaymentMethodException):
    """Payment method required but not found"""
    default_message = "A valid payment method is required"
    error_code = "PAYMENT_METHOD_REQUIRED"


class SubscriptionException(PaymentException):
    """Subscription-related errors"""
    default_message = "Subscription error"
    error_code = "SUBSCRIPTION_ERROR"


class SubscriptionNotActiveException(SubscriptionException):
    """Subscription is not active"""
    default_message = "The subscription is not active"
    error_code = "SUBSCRIPTION_NOT_ACTIVE"


class SubscriptionLimitExceededException(SubscriptionException):
    """Subscription limit exceeded"""
    default_message = "Subscription limit exceeded"
    error_code = "SUBSCRIPTION_LIMIT_EXCEEDED"
    
    def __init__(self, limit_type, current, limit, message=None):
        self.limit_type = limit_type
        self.current = current
        self.limit = limit
        details = {
            'limit_type': limit_type,
            'current': current,
            'limit': limit
        }
        message = message or f"{limit_type} limit exceeded: {current}/{limit}"
        super().__init__(message=message, details=details)


class WebhookException(PaymentException):
    """Webhook processing errors"""
    default_message = "Webhook processing error"
    error_code = "WEBHOOK_ERROR"
    status_code = 400


class WebhookSignatureException(WebhookException):
    """Webhook signature verification failed"""
    default_message = "Invalid webhook signature"
    error_code = "INVALID_WEBHOOK_SIGNATURE"
    status_code = 401


class WebhookProcessingException(WebhookException):
    """Webhook processing failed"""
    default_message = "Failed to process webhook"
    error_code = "WEBHOOK_PROCESSING_FAILED"
    status_code = 500
    
    def __init__(self, event_type, event_id, message=None, details=None):
        self.event_type = event_type
        self.event_id = event_id
        details = details or {}
        details.update({
            'event_type': event_type,
            'event_id': event_id
        })
        super().__init__(message=message, details=details)


class PaymentRetryableException(PaymentException):
    """Retryable payment error"""
    default_message = "Payment temporarily failed, please retry"
    error_code = "PAYMENT_RETRYABLE"
    status_code = 503
    
    def __init__(self, message=None, details=None, retry_after=300):
        super().__init__(message=message, details=details, retry_after=retry_after)


class RateLimitExceededException(PaymentException):
    """Rate limit exceeded"""
    default_message = "Too many requests. Please try again later."
    error_code = "RATE_LIMIT_EXCEEDED"
    status_code = 429
    
    def __init__(self, message=None, details=None, retry_after=60):
        super().__init__(message=message, details=details, retry_after=retry_after)


class CustomerPortalException(PaymentException):
    """Customer portal related errors"""
    default_message = "Customer portal error"
    error_code = "CUSTOMER_PORTAL_ERROR"
    status_code = 400


class InvalidRequestException(PaymentException):
    """Invalid request parameters"""
    default_message = "Invalid request parameters"
    error_code = "INVALID_REQUEST"
    status_code = 400
    
    def __init__(self, param=None, message=None, details=None):
        if param and not message:
            message = f"Invalid parameter: {param}"
        details = details or {}
        if param:
            details['param'] = param
        super().__init__(message=message, details=details)


class PaymentAuthenticationRequiredException(PaymentException):
    """Payment requires additional authentication"""
    default_message = "Additional authentication required"
    error_code = "AUTHENTICATION_REQUIRED"
    status_code = 402
    
    def __init__(self, message=None, details=None, authentication_url=None):
        details = details or {}
        if authentication_url:
            details['authentication_url'] = authentication_url
        super().__init__(message=message, details=details)


class InsufficientCreditsException(PaymentException):
    """Insufficient credits for operation"""
    default_message = "Insufficient credits"
    error_code = "INSUFFICIENT_CREDITS"
    status_code = 402
    
    def __init__(self, required=None, available=None, message=None):
        details = {}
        if required is not None:
            details['required'] = required
        if available is not None:
            details['available'] = available
        if not message and required is not None and available is not None:
            message = f"Insufficient credits. Required: {required}, Available: {available}"
        super().__init__(message=message, details=details)


class PaymentConfigurationException(PaymentException):
    """Payment service configuration error"""
    default_message = "Payment service configuration error"
    error_code = "CONFIGURATION_ERROR"
    status_code = 500
    
    def __init__(self, service=None, message=None, details=None):
        if service and not message:
            message = f"{service} configuration error"
        details = details or {}
        if service:
            details['service'] = service
        super().__init__(message=message, details=details)