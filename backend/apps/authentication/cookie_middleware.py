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
    Middleware to handle JWT cookies and security headers with mobile browser support
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Add security headers for API responses
        if request.path.startswith('/api/'):
            self._add_security_headers(response)
            self._add_mobile_debug_headers(request, response)
        
        return response
    
    def _add_security_headers(self, response):
        """Add security headers to response"""
        # Prevent caching of sensitive data
        response_data = getattr(response, 'data', {}) or {}
        if hasattr(response, 'data') and 'tokens' in response_data:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
    
    def _add_mobile_debug_headers(self, request, response):
        """Add debug headers for mobile browser troubleshooting"""
        if settings.DEBUG or hasattr(settings, 'ADD_DEBUG_HEADERS'):
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            is_mobile_safari = _is_mobile_safari(user_agent)
            
            response['X-Mobile-Safari-Detected'] = str(is_mobile_safari)
            response['X-User-Agent-Short'] = user_agent[:50] + '...' if len(user_agent) > 50 else user_agent
            
            # Cookie presence debug
            has_access = bool(request.COOKIES.get(getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token')))
            has_refresh = bool(request.COOKIES.get(getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'refresh_token')))
            response['X-Cookie-Access-Present'] = str(has_access)
            response['X-Cookie-Refresh-Present'] = str(has_refresh)


def set_jwt_cookies(response, tokens, request=None, user=None):
    """
    Set JWT tokens as httpOnly cookies - MVP Mobile Safari Fix
    """
    access_token = tokens.get('access')
    refresh_token = tokens.get('refresh')
    
    # MOBILE SAFARI MVP FIX
    is_mobile_safari = False
    if request:
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
    
    # Configure cookies specifically for Mobile Safari
    if is_mobile_safari:
        # Mobile Safari needs SameSite=None + Secure=True
        samesite = 'None'
        secure = True
        logger.info("Mobile Safari detected - using SameSite=None configuration")
    else:
        # Standard configuration for other browsers
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
        logger.info(f"Access token set for user {user_id or 'unknown'} from IP {client_ip}")
    
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
        logger.info(f"Refresh token set for user {user_id or 'unknown'} from IP {client_ip}")
    
    # Simple debug log
    logger.info(f"Cookie config - Mobile Safari: {is_mobile_safari}, SameSite: {samesite}, Secure: {secure}")
    
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


def _is_mobile_safari(user_agent):
    """Detect Mobile Safari browsers that have issues with SameSite=None"""
    user_agent = user_agent.lower()
    
    # Mobile Safari indicators
    is_safari = 'safari' in user_agent and 'chrome' not in user_agent
    is_mobile = any(mobile in user_agent for mobile in [
        'mobile', 'iphone', 'ipad', 'ipod', 'ios'
    ])
    
    # WebKit-based mobile browsers
    is_webkit_mobile = 'webkit' in user_agent and is_mobile
    
    return (is_safari and is_mobile) or is_webkit_mobile


def set_mobile_compatible_cookies(response, tokens, request=None, user=None):
    """
    Alternative cookie setting strategy specifically for mobile browsers
    Uses multiple approaches to ensure compatibility
    """
    if not request:
        return set_jwt_cookies(response, tokens, request, user)
    
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    is_mobile_safari = _is_mobile_safari(user_agent)
    
    if not is_mobile_safari:
        return set_jwt_cookies(response, tokens, request, user)
    
    logger.info(f"Mobile Safari detected - using enhanced cookie strategy")
    
    access_token = tokens.get('access')
    refresh_token = tokens.get('refresh')
    
    # Mobile Safari compatibility now built into settings (SameSite=Lax by default)
    secure = True  # Always secure in production
    samesite = 'Lax'  # Use Lax for mobile compatibility (now matches settings)
    domain = None  # Let browser handle domain
    
    # Log the configuration (should match settings now)
    settings_samesite = getattr(settings, 'JWT_COOKIE_SAMESITE', 'unknown')
    logger.info(f"✅ Mobile Safari compatible cookies - Settings: {settings_samesite}, Applied: {samesite}")
    
    # Strategy 1: Set cookies with explicit path and no domain
    if access_token:
        response.set_cookie(
            key=getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token'),
            value=access_token,
            max_age=int(settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timedelta(minutes=30)).total_seconds()),
            secure=secure,
            httponly=True,
            samesite=samesite,
            domain=domain,
            path='/',
        )
        
        # Strategy 2: Also try setting a fallback cookie with different name
        response.set_cookie(
            key='mobile_access_token',
            value=access_token,
            max_age=int(settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timedelta(minutes=30)).total_seconds()),
            secure=secure,
            httponly=False,  # Make it accessible to JS as fallback
            samesite=samesite,
            domain=domain,
            path='/'
        )
    
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
        
        # Fallback refresh token
        response.set_cookie(
            key='mobile_refresh_token',
            value=refresh_token,
            max_age=int(settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', timedelta(days=3)).total_seconds()),
            secure=secure,
            httponly=False,  # Make it accessible to JS as fallback
            samesite=samesite,
            domain=domain,
            path='/'
        )
    
    # Add debug headers
    response['X-Mobile-Cookie-Strategy'] = 'enhanced'
    response['X-Mobile-Safari-Fallback'] = 'true'
    
    logger.info(f"Mobile Safari cookies set with enhanced strategy - SameSite={samesite}, Secure={secure}")
    
    return response