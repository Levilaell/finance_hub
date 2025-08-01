"""Payment middleware for error handling and security"""
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .exceptions import PaymentException

logger = logging.getLogger(__name__)


class PaymentErrorHandlerMiddleware(MiddlewareMixin):
    """Middleware to handle payment-related exceptions"""
    
    def process_exception(self, request, exception):
        """Process payment exceptions and return appropriate responses"""
        if not isinstance(exception, PaymentException):
            return None
        
        # Log the exception
        logger.error(
            f"Payment error: {exception.error_code} - {exception.message}",
            extra={
                'error_code': exception.error_code,
                'details': exception.details,
                'user_id': getattr(request.user, 'id', None),
                'path': request.path,
                'method': request.method,
            }
        )
        
        # Build response
        response_data = exception.to_dict()
        
        # Add request ID if available
        if hasattr(request, 'id'):
            response_data['request_id'] = request.id
        
        return JsonResponse(
            response_data,
            status=exception.status_code
        )


class PaymentSecurityMiddleware(MiddlewareMixin):
    """Security middleware for payment endpoints"""
    
    PAYMENT_PATHS = [
        '/api/payments/',
        '/api/checkout/',
        '/api/subscription/',
    ]
    
    def process_request(self, request):
        """Add security headers for payment endpoints"""
        if not any(request.path.startswith(path) for path in self.PAYMENT_PATHS):
            return None
        
        # Log payment requests for audit
        logger.info(
            f"Payment request: {request.method} {request.path}",
            extra={
                'user_id': getattr(request.user, 'id', None),
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )
    
    def process_response(self, request, response):
        """Add security headers to payment responses"""
        if not any(request.path.startswith(path) for path in self.PAYMENT_PATHS):
            return response
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # CSP for payment pages
        if '/checkout/' in request.path:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' https://js.stripe.com; "
                "frame-src 'self' https://js.stripe.com https://hooks.stripe.com; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' https: data:; "
                "connect-src 'self' https://api.stripe.com;"
            )
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip