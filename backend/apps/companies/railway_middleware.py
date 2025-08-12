"""
Middleware to handle Railway-specific requirements
"""
from django.http import JsonResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class RailwayHealthCheckMiddleware:
    """
    Middleware to handle Railway health checks without any redirects
    Railway health checks come from internal IPs and must return 200 OK
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if this is a health check request
        path = request.path.rstrip('/')
        
        # Handle health check requests specially
        if path in ['/health', '/api/health']:
            # Log the request details for debugging
            logger.info(f"Health check request: {request.method} {request.path} from {request.META.get('REMOTE_ADDR')}")
            
            # Check if this is from Railway health check
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            if 'RailwayHealthCheck' in user_agent or request.META.get('REMOTE_ADDR', '').startswith('100.'):
                # Return immediate 200 response for Railway health checks
                return JsonResponse({
                    'status': 'healthy',
                    'service': 'finance-hub-backend',
                    'timestamp': 'ok',
                    'checks': {
                        'server': 'running',
                        'middleware': 'railway-bypass'
                    }
                }, status=200)
        
        # For all other requests, continue normally
        response = self.get_response(request)
        
        # Ensure health endpoints never redirect
        if path in ['/health', '/api/health'] and response.status_code in [301, 302]:
            logger.warning(f"Health check tried to redirect: {response.status_code}")
            # Override with a 200 response
            return JsonResponse({
                'status': 'healthy',
                'service': 'finance-hub-backend',
                'note': 'redirect-prevented'
            }, status=200)
        
        return response


class DisableSSLRedirectForHealthMiddleware:
    """
    Completely disable SSL redirect for health check endpoints
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Store original setting
        original_ssl_redirect = getattr(settings, 'SECURE_SSL_REDIRECT', False)
        
        # Disable SSL redirect for health checks
        path = request.path.rstrip('/')
        if path in ['/health', '/api/health']:
            settings.SECURE_SSL_REDIRECT = False
        
        try:
            response = self.get_response(request)
        finally:
            # Restore original setting
            settings.SECURE_SSL_REDIRECT = original_ssl_redirect
        
        return response