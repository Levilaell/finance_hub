"""
Security utilities and middleware
"""
import logging
import time
import uuid
from typing import Optional

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to all responses"""
    
    def process_response(self, request, response):
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        if not settings.DEBUG:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.stripe.com https://api.mercadopago.com https://api.pluggy.ai;"
            )
            response['Content-Security-Policy'] = csp
        
        # Permissions Policy
        response['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), '
            'magnetometer=(), gyroscope=(), fullscreen=(self), payment=*'
        )
        
        return response


class RequestIDMiddleware(MiddlewareMixin):
    """Add unique request ID to each request for tracking"""
    
    def process_request(self, request):
        request.id = str(uuid.uuid4())
        request.META['HTTP_X_REQUEST_ID'] = request.id
    
    def process_response(self, request, response):
        if hasattr(request, 'id'):
            response['X-Request-ID'] = request.id
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Global rate limiting middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Configure rate limits
        self.rate_limits = {
            'default': (100, 60),  # 100 requests per minute
            'api': (1000, 60),     # 1000 API requests per minute
            'auth': (10, 60),      # 10 auth attempts per minute
        }
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def process_request(self, request):
        # Skip rate limiting in DEBUG mode
        if settings.DEBUG:
            return None
        
        # Determine rate limit type
        path = request.path
        if path.startswith('/api/auth/'):
            limit_type = 'auth'
        elif path.startswith('/api/'):
            limit_type = 'api'
        else:
            limit_type = 'default'
        
        # Get rate limit config
        max_requests, window = self.rate_limits[limit_type]
        
        # Get client identifier
        client_ip = self.get_client_ip(request)
        if request.user.is_authenticated:
            client_id = f"user_{request.user.id}"
        else:
            client_id = f"ip_{client_ip}"
        
        # Create cache key
        cache_key = f"rate_limit:{limit_type}:{client_id}"
        
        # Check rate limit
        current_requests = cache.get(cache_key, 0)
        if current_requests >= max_requests:
            logger.warning(f"Rate limit exceeded for {client_id} on {limit_type}")
            return HttpResponseForbidden("Rate limit exceeded. Please try again later.")
        
        # Increment counter
        cache.set(cache_key, current_requests + 1, window)
        
        return None


class AuditLogMiddleware(MiddlewareMixin):
    """Log all sensitive operations for audit trail"""
    
    SENSITIVE_OPERATIONS = [
        '/api/banking/connect/',
        '/api/banking/sync/',
        '/api/banking/transactions/',
        '/api/auth/login/',
        '/api/auth/register/',
        '/api/companies/subscription/',
        '/api/payments/',
    ]
    
    def process_request(self, request):
        request._start_time = time.time()
    
    def process_response(self, request, response):
        # Check if this is a sensitive operation
        for path in self.SENSITIVE_OPERATIONS:
            if request.path.startswith(path):
                self._log_audit_event(request, response)
                break
        
        return response
    
    def _log_audit_event(self, request, response):
        """Log audit event"""
        duration = time.time() - getattr(request, '_start_time', 0)
        
        audit_data = {
            'timestamp': time.time(),
            'request_id': getattr(request, 'id', 'unknown'),
            'user_id': request.user.id if request.user.is_authenticated else None,
            'ip_address': self._get_client_ip(request),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration': duration,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # Log to audit logger
        audit_logger = logging.getLogger('audit')
        audit_logger.info(f"AUDIT: {audit_data}")
        
        # In production, also send to audit storage (e.g., dedicated database)
        if not settings.DEBUG:
            self._store_audit_event(audit_data)
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _store_audit_event(self, audit_data):
        """Store audit event in persistent storage"""
        # TODO: Implement audit storage (e.g., separate database, S3, etc.)
        pass


class IPWhitelistMiddleware(MiddlewareMixin):
    """IP whitelist for admin and sensitive endpoints"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Get whitelist from settings
        self.whitelist = getattr(settings, 'IP_WHITELIST', [])
        self.protected_paths = [
            '/admin/',
            '/api/admin/',
            '/api/banking/webhook/',
            '/api/payments/webhook/',
        ]
    
    def process_request(self, request):
        # Skip in DEBUG mode
        if settings.DEBUG:
            return None
        
        # Check if path needs protection
        needs_protection = any(
            request.path.startswith(path) 
            for path in self.protected_paths
        )
        
        if not needs_protection:
            return None
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check whitelist
        if client_ip not in self.whitelist:
            logger.warning(f"Blocked access from {client_ip} to {request.path}")
            return HttpResponseForbidden("Access denied")
        
        return None
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def sanitize_user_input(data: dict) -> dict:
    """Sanitize user input to prevent XSS and injection attacks"""
    import bleach
    
    allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    allowed_attributes = {}
    
    def clean_value(value):
        if isinstance(value, str):
            # Remove any HTML tags except allowed ones
            return bleach.clean(value, tags=allowed_tags, attributes=allowed_attributes, strip=True)
        elif isinstance(value, dict):
            return sanitize_user_input(value)
        elif isinstance(value, list):
            return [clean_value(item) for item in value]
        else:
            return value
    
    return {key: clean_value(value) for key, value in data.items()}


def validate_cpf(cpf: str) -> bool:
    """Validate Brazilian CPF"""
    # Remove non-digits
    cpf = ''.join(filter(str.isdigit, cpf))
    
    # CPF must have 11 digits
    if len(cpf) != 11:
        return False
    
    # Check for known invalid patterns
    if cpf in ['00000000000', '11111111111', '22222222222', '33333333333',
               '44444444444', '55555555555', '66666666666', '77777777777',
               '88888888888', '99999999999']:
        return False
    
    # Validate check digits
    # First digit
    sum_digit = sum(int(cpf[i]) * (10 - i) for i in range(9))
    first_digit = 11 - (sum_digit % 11)
    if first_digit >= 10:
        first_digit = 0
    
    if int(cpf[9]) != first_digit:
        return False
    
    # Second digit
    sum_digit = sum(int(cpf[i]) * (11 - i) for i in range(10))
    second_digit = 11 - (sum_digit % 11)
    if second_digit >= 10:
        second_digit = 0
    
    return int(cpf[10]) == second_digit


def validate_cnpj(cnpj: str) -> bool:
    """Validate Brazilian CNPJ"""
    # Remove non-digits
    cnpj = ''.join(filter(str.isdigit, cnpj))
    
    # CNPJ must have 14 digits
    if len(cnpj) != 14:
        return False
    
    # Check for known invalid patterns
    if cnpj == '00000000000000':
        return False
    
    # Validate check digits
    # First digit
    weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_digit = sum(int(cnpj[i]) * weights[i] for i in range(12))
    first_digit = 11 - (sum_digit % 11)
    if first_digit >= 10:
        first_digit = 0
    
    if int(cnpj[12]) != first_digit:
        return False
    
    # Second digit
    weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_digit = sum(int(cnpj[i]) * weights[i] for i in range(13))
    second_digit = 11 - (sum_digit % 11)
    if second_digit >= 10:
        second_digit = 0
    
    return int(cnpj[13]) == second_digit