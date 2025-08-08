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


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class SecurityMiddleware(MiddlewareMixin):
    """
    Basic security middleware with essential protection
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.start_time = time.time()
    
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
    
    def _is_auth_endpoint(self, path):
        """
        Check if path is an authentication endpoint
        """
        auth_paths = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/refresh/',
            '/api/auth/password-reset/',
            '/api/auth/2fa/',
        ]
        
        return any(path.startswith(auth_path) for auth_path in auth_paths)
    
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
        
        # Cache control for sensitive endpoints
        if self._is_auth_endpoint(request.path):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Basic session security middleware
    """
    
    def process_request(self, request):
        """
        Validate basic session security
        """
        if not request.user.is_authenticated:
            return None
        
        user = request.user
        client_ip = get_client_ip(request)
        
        # Update user's last activity
        if hasattr(user, 'last_login_ip'):
            user.last_login_ip = client_ip
            user.save(update_fields=['last_login_ip'])
        
        return None