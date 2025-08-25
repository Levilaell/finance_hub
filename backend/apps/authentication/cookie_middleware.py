"""
Cookie-based authentication middleware
"""
import logging
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

logger = logging.getLogger('security')


class JWTCookieMiddleware:
    """
    Middleware to handle JWT cookies and security headers
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Add security headers for API responses
        if request.path.startswith('/api/'):
            self._add_security_headers(response)
            self._add_debug_headers(request, response)
        
        return response
    
    def _add_security_headers(self, response):
        """Add security headers to response"""
        # Prevent caching of sensitive data
        response_data = getattr(response, 'data', {}) or {}
        if hasattr(response, 'data') and 'tokens' in response_data:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
    
    def _add_debug_headers(self, request, response):
        """Add debug headers for troubleshooting"""
        if settings.DEBUG or hasattr(settings, 'ADD_DEBUG_HEADERS'):
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            response['X-User-Agent-Short'] = user_agent[:50] + '...' if len(user_agent) > 50 else user_agent
            
            # Cookie presence debug
            has_access = bool(request.COOKIES.get(getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token')))
            has_refresh = bool(request.COOKIES.get(getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'refresh_token')))
            response['X-Cookie-Access-Present'] = str(has_access)
            response['X-Cookie-Refresh-Present'] = str(has_refresh)


def set_jwt_cookies(response, tokens, request=None, user=None):
    """
    Set JWT tokens as httpOnly cookies - SIMPLE VERSION
    """
    access_token = tokens.get('access')
    refresh_token = tokens.get('refresh')
    
    # Standard configuration for ALL browsers - no special cases
    samesite = 'Lax'
    secure = getattr(settings, 'JWT_COOKIE_SECURE', not settings.DEBUG)
    domain = getattr(settings, 'JWT_COOKIE_DOMAIN', None)
    
    # Simple logging
    user_id = getattr(user, 'id', None) if user else None
    client_ip = get_client_ip(request) if request else 'unknown'
    
    # Set access token cookie
    if access_token:
        response.set_cookie(
            key=getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token'),
            value=access_token,
            max_age=int(settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timedelta(minutes=30)).total_seconds()),
            secure=secure,
            httponly=True,
            samesite=samesite,
            domain=domain,
            path='/'
        )
        logger.info(f"Access token set for user {user_id or 'unknown'}")
    
    # Set refresh token cookie
    if refresh_token:
        response.set_cookie(
            key=getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'refresh_token'),
            value=refresh_token,
            max_age=int(settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', timedelta(days=3)).total_seconds()),
            secure=secure,
            httponly=True,
            samesite=samesite,
            domain=domain,
            path='/'
        )
        logger.info(f"Refresh token set for user {user_id or 'unknown'}")
    
    return response


def clear_jwt_cookies(response):
    """
    Clear JWT cookies on logout
    """
    secure = getattr(settings, 'JWT_COOKIE_SECURE', not settings.DEBUG)
    samesite = getattr(settings, 'JWT_COOKIE_SAMESITE', 'Lax')
    
    # Convert Python None to string "None" for SameSite attribute
    if samesite is None:
        samesite = 'None'
    
    domain = getattr(settings, 'JWT_COOKIE_DOMAIN', None)
    
    # Clear access token
    response.set_cookie(
        key=getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token'),
        value='',
        max_age=0,
        secure=secure,
        httponly=True,
        samesite=samesite,
        domain=domain,
        path='/'
    )
    
    # Clear refresh token
    response.set_cookie(
        key=getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'refresh_token'),
        value='',
        max_age=0,
        secure=secure,
        httponly=True,
        samesite=samesite,
        domain=domain,
        path='/'
    )
    
    return response


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


