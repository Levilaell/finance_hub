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