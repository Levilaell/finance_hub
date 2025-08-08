"""Payment middleware for error handling and security"""
import logging
import json
from typing import Optional
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.cache import cache

from .exceptions import PaymentException
from .services.error_handler import ErrorHandler, RateLimitHandler

logger = logging.getLogger(__name__)


class PaymentErrorHandlerMiddleware(MiddlewareMixin):
    """Middleware to handle payment-related exceptions with comprehensive error handling"""
    
    def process_exception(self, request, exception):
        """Process payment exceptions and return appropriate responses"""
        # Only handle payment-related paths
        if not request.path.startswith('/api/payments/'):
            return None
        
        # Convert exception to PaymentException if needed
        if isinstance(exception, PaymentException):
            error = exception
        else:
            try:
                error = ErrorHandler.handle_exception(exception)
            except Exception:
                # If error handling fails, let Django handle it
                logger.exception("Error in payment error handler")
                return None
        
        # Log the error with comprehensive context
        ErrorHandler.log_error(
            error,
            context={
                'path': request.path,
                'method': request.method,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': self.get_client_ip(request),
                'error_code': error.error_code,
                'details': error.details,
            },
            user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            company_id=getattr(request.user, 'current_company_id', None) if hasattr(request, 'user') else None
        )
        
        # Build response
        response_data = error.to_dict()
        
        # Add request ID if available
        if hasattr(request, 'id'):
            response_data['request_id'] = request.id
        
        # Create response
        response = JsonResponse(
            response_data,
            status=error.status_code,
            json_dumps_params={'indent': 2} if settings.DEBUG else {}
        )
        
        # Add retry header if applicable
        if error.retry_after:
            response['Retry-After'] = str(error.retry_after)
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip


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
        
        # Prevent caching of sensitive payment data
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Strict Transport Security (if HTTPS)
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # CSP for payment pages
        if '/checkout/' in request.path or '/portal/' in request.path:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' https://js.stripe.com https://checkout.stripe.com; "
                "frame-src 'self' https://js.stripe.com https://hooks.stripe.com https://checkout.stripe.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' https: data: blob:; "
                "connect-src 'self' https://api.stripe.com https://checkout.stripe.com; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self' https://checkout.stripe.com; "
                "frame-ancestors 'none';"
            )
        else:
            # Stricter CSP for non-checkout pages
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none';"
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


class PaymentRateLimitMiddleware(MiddlewareMixin):
    """Middleware to enforce rate limiting on payment endpoints"""
    
    # Rate limit configuration per endpoint (requests, window_seconds)
    RATE_LIMITS = {
        '/api/payments/checkout/': (10, 3600),           # 10 per hour
        '/api/payments/methods/': (30, 3600),            # 30 per hour
        '/api/payments/credits/purchase/': (5, 3600),    # 5 per hour
        '/api/payments/portal/': (20, 3600),             # 20 per hour
        '/api/payments/cancel/': (5, 3600),              # 5 per hour
        '/api/payments/webhooks/stripe/': (1000, 60),    # 1000 per minute
    }
    
    def process_request(self, request):
        """Check rate limits before processing request"""
        # Skip rate limiting for internal IPs in debug mode
        if settings.DEBUG and self._is_internal_ip(request):
            return None
        
        # Skip for webhook signatures (they have their own validation)
        if request.path == '/api/payments/webhooks/stripe/':
            return None
        
        # Check if path has rate limit
        for path_prefix, (limit, window) in self.RATE_LIMITS.items():
            if request.path.startswith(path_prefix):
                # Get user identifier
                if hasattr(request, 'user') and request.user.is_authenticated:
                    identifier = f'user:{request.user.id}'
                else:
                    identifier = f'ip:{self._get_client_ip(request)}'
                
                # Check rate limit
                retry_after = RateLimitHandler.handle_rate_limit(
                    identifier,
                    path_prefix,
                    limit=limit,
                    window=window
                )
                
                if retry_after:
                    # Rate limit exceeded
                    logger.warning(
                        f"Rate limit exceeded for {identifier} on {path_prefix}",
                        extra={
                            'identifier': identifier,
                            'path': path_prefix,
                            'limit': limit,
                            'window': window,
                            'retry_after': retry_after
                        }
                    )
                    
                    response = JsonResponse(
                        {
                            'error': 'RATE_LIMIT_EXCEEDED',
                            'message': 'Too many requests. Please try again later.',
                            'retry_after': retry_after
                        },
                        status=429
                    )
                    response['Retry-After'] = str(retry_after)
                    
                    # Add rate limit headers
                    headers = RateLimitHandler.get_rate_limit_headers(
                        identifier,
                        path_prefix,
                        limit=limit
                    )
                    for header, value in headers.items():
                        response[header] = value
                    
                    return response
        
        return None
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
    
    def _is_internal_ip(self, request) -> bool:
        """Check if request is from internal IP"""
        ip = self._get_client_ip(request)
        return ip in ['127.0.0.1', 'localhost', '::1']