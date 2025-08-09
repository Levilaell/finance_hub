"""
Middleware to bypass SSL redirect for health check endpoints
"""
from django.conf import settings
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


class HealthCheckSSLBypassMiddleware:
    """
    Bypass SSL redirect for health check endpoints to prevent 301 redirects
    that can cause health checks to fail. Also directly handles Railway health checks.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Normalize path (remove trailing slash for comparison)
        path = request.path.rstrip('/')
        
        # List of paths that should bypass SSL redirect
        bypass_paths = ['/health', '/api/health', '']
        
        # Check if this is a health check request
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        remote_addr = request.META.get('REMOTE_ADDR', '')
        
        is_health_check = (
            path in bypass_paths or
            'RailwayHealthCheck' in user_agent or
            remote_addr.startswith('100.')  # Railway internal IPs
        )
        
        # Special handling for Railway health checks - return immediate response
        if path in ['/health', '/api/health'] and 'RailwayHealthCheck' in user_agent:
            logger.info(f"Railway health check detected: {request.method} {request.path}")
            return JsonResponse({
                'status': 'healthy',
                'service': 'finance-hub-backend',
                'middleware': 'health-check-bypass',
                'path': request.path,
                'method': request.method
            }, status=200)
        
        # Temporarily disable SSL redirect for health checks
        if is_health_check:
            # Store original value
            original_ssl_redirect = getattr(settings, 'SECURE_SSL_REDIRECT', False)
            
            # Force disable SSL redirect
            settings.SECURE_SSL_REDIRECT = False
            
            try:
                response = self.get_response(request)
                
                # If response is still a redirect for health endpoints, override it
                if path in ['/health', '/api/health'] and response.status_code in [301, 302]:
                    logger.warning(f"Health check still trying to redirect: {response.status_code}, overriding with 200")
                    from apps.companies.health import health_check
                    response = health_check(request)
                    
            finally:
                # Restore original value
                settings.SECURE_SSL_REDIRECT = original_ssl_redirect
        else:
            response = self.get_response(request)
        
        return response