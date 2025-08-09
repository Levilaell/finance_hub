"""
Middleware to bypass SSL redirect for health check endpoints
"""
from django.conf import settings


class HealthCheckSSLBypassMiddleware:
    """
    Bypass SSL redirect for health check endpoints to prevent 301 redirects
    that can cause health checks to fail
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # List of paths that should bypass SSL redirect
        bypass_paths = ['/health/', '/api/health/', '/']
        
        # Check if this is a health check request
        is_health_check = (
            request.path in bypass_paths or
            request.META.get('HTTP_USER_AGENT', '').startswith('RailwayHealthCheck')
        )
        
        # Temporarily disable SSL redirect for health checks
        if is_health_check and hasattr(settings, 'SECURE_SSL_REDIRECT'):
            # Store original value
            original_ssl_redirect = settings.SECURE_SSL_REDIRECT
            
            # Disable SSL redirect
            settings.SECURE_SSL_REDIRECT = False
            
            try:
                response = self.get_response(request)
            finally:
                # Restore original value
                settings.SECURE_SSL_REDIRECT = original_ssl_redirect
        else:
            response = self.get_response(request)
        
        return response