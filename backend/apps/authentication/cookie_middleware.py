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
        
        return response
    
    def _add_security_headers(self, response):
        """Add security headers to response"""
        # Prevent caching of sensitive data
        response_data = getattr(response, 'data', {}) or {}
        if hasattr(response, 'data') and 'tokens' in response_data:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'


def set_jwt_cookies(response, tokens, request=None):
    """
    Set JWT tokens as httpOnly cookies
    """
    access_token = tokens.get('access')
    refresh_token = tokens.get('refresh')
    
    # Get cookie settings from Django settings
    secure = getattr(settings, 'JWT_COOKIE_SECURE', not settings.DEBUG)
    samesite = getattr(settings, 'JWT_COOKIE_SAMESITE', 'Lax')
    
    # Convert Python None to string "None" for SameSite attribute
    if samesite is None:
        samesite = 'None'
    
    # Special handling for development: Chrome allows Secure=False with SameSite=None on localhost
    if settings.DEBUG and samesite == 'None':
        # In development, we can use SameSite=None without Secure for localhost
        # This allows cross-origin requests between localhost:3000 and localhost:8000
        pass  # Keep secure as configured
    domain = getattr(settings, 'JWT_COOKIE_DOMAIN', None)
    
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
        
        # Log token issuance
        if request and hasattr(request, 'user'):
            logger.info(
                f"Access token issued for user {getattr(request.user, 'id', 'unknown')} "
                f"from IP {get_client_ip(request)}"
            )
    
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
            path='/'  # Make refresh token available globally for token refresh
        )
        
        # Log refresh token issuance
        if request and hasattr(request, 'user'):
            logger.info(
                f"Refresh token issued for user {getattr(request.user, 'id', 'unknown')} "
                f"from IP {get_client_ip(request)}"
            )
    
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