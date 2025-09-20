"""
Basic security middleware for authentication protection
"""
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging
import time

logger = logging.getLogger(__name__)
User = get_user_model()


class SecurityMiddleware(MiddlewareMixin):
    """
    Basic security middleware with essential protection
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Process incoming request for basic security checks
        """
        request.security_start_time = time.time()
        
        # Skip security checks for health checks and static files
        if self._should_skip_security_check(request):
            return None
        
        return None
    
    def process_response(self, request, response):
        """
        Process response and add security headers
        """
        if self._should_skip_security_check(request):
            return response
        
        # Add security headers
        response = self._add_security_headers(response, request)
        
        # Log slow requests
        if hasattr(request, 'security_start_time'):
            request_time = time.time() - request.security_start_time
            if request_time > 5.0:  # Requests taking more than 5 seconds
                # Import get_client_ip from security_logging
                from .security_logging import get_client_ip
                client_ip = get_client_ip(request)
                logger.warning(
                    f"Slow request detected: {request.path} took {request_time:.2f}s from {client_ip}"
                )
        
        return response
    
    def _should_skip_security_check(self, request):
        """
        Check if security checks should be skipped for this request
        """
        skip_paths = [
            '/health/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        
        return any(request.path.startswith(path) for path in skip_paths)
    
    
    def _add_security_headers(self, response, request):
        """
        Add security headers to response
        """
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        if not response.get('X-Frame-Options'):
            response['X-Frame-Options'] = 'DENY'
        
        # XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy for API responses
        if request.path.startswith('/api/'):
            response['Content-Security-Policy'] = "default-src 'none'"

        # Cache control for auth endpoints
        if request.path.startswith('/api/auth/'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response


