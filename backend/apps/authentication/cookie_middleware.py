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
    Set JWT tokens as httpOnly cookies with mobile browser compatibility
    
    Args:
        response: Django response object
        tokens: Dict containing 'access' and 'refresh' tokens
        request: Django request object (optional, for IP logging)
        user: User object (optional, for accurate logging)
    """
    access_token = tokens.get('access')
    refresh_token = tokens.get('refresh')
    
    # Get cookie settings from Django settings
    secure = getattr(settings, 'JWT_COOKIE_SECURE', not settings.DEBUG)
    samesite = getattr(settings, 'JWT_COOKIE_SAMESITE', 'Lax')
    
    # Mobile Safari Compatibility: Detect mobile browsers and adjust SameSite
    if request:
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
        
        if is_mobile_safari:
            # Mobile Safari blocks SameSite=None even with Secure=True
            # Fallback to Lax for better compatibility
            original_samesite = samesite
            samesite = 'Lax'
            logger.info(f"Mobile Safari detected - SameSite changed from {original_samesite} to {samesite}")
    
    # Convert Python None to string "None" for SameSite attribute
    if samesite is None:
        samesite = 'None'
    
    # Special handling for development: Chrome allows Secure=False with SameSite=None on localhost
    if settings.DEBUG and samesite == 'None':
        # In development, we can use SameSite=None without Secure for localhost
        # This allows cross-origin requests between localhost:3000 and localhost:8000
        pass  # Keep secure as configured
    domain = getattr(settings, 'JWT_COOKIE_DOMAIN', None)
    
    # Determine user ID for logging (prefer passed user over request.user)
    user_id = None
    client_ip = get_client_ip(request) if request else 'unknown'
    
    # Debug logging to identify the issue
    if user:
        try:
            user_id = user.id
            logger.info(f"Cookie middleware: Using passed user object, ID={user_id}, email={getattr(user, 'email', 'unknown')}")
        except Exception as e:
            logger.error(f"Cookie middleware: Error accessing user.id: {e}")
            user_id = None
    elif request and hasattr(request, 'user') and hasattr(request.user, 'id'):
        try:
            user_id = request.user.id
            logger.info(f"Cookie middleware: Using request.user, ID={user_id}")
        except Exception as e:
            logger.error(f"Cookie middleware: Error accessing request.user.id: {e}")
            user_id = None
    else:
        logger.warning(f"Cookie middleware: No user available - passed user: {user}, request.user: {getattr(request, 'user', 'missing')}")
    
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
        
        # Log token issuance with accurate user ID
        logger.info(f"Access token issued for user {user_id or 'unknown'} from IP {client_ip}")
    
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
        
        # Log refresh token issuance with accurate user ID
        logger.info(f"Refresh token issued for user {user_id or 'unknown'} from IP {client_ip}")
    
    # Add comprehensive debug headers for cookie troubleshooting
    if request and (settings.DEBUG or hasattr(settings, 'ADD_DEBUG_HEADERS')):
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
        
        # Basic cookie info
        response['X-Cookie-Set-For-Mobile-Safari'] = str(is_mobile_safari)
        response['X-Cookie-SameSite-Used'] = samesite
        response['X-Cookie-Secure-Used'] = str(secure)
        response['X-Cookie-Domain-Used'] = str(domain) if domain else 'None'
        response['X-Cookie-Path-Used'] = '/'
        
        # Request origin info
        response['X-Request-Origin'] = request.META.get('HTTP_ORIGIN', 'None')
        response['X-Request-Host'] = request.META.get('HTTP_HOST', 'None')
        response['X-Request-Referer'] = request.META.get('HTTP_REFERER', 'None')[:100]
        
        # Token size info (for debugging large cookie issues)
        if access_token:
            response['X-Access-Token-Length'] = str(len(access_token))
        if refresh_token:
            response['X-Refresh-Token-Length'] = str(len(refresh_token))
        
        # Current cookies in request (to see what browser is sending back)
        current_cookies = request.COOKIES.keys()
        response['X-Current-Cookies-Count'] = str(len(current_cookies))
        response['X-Current-Cookies'] = ','.join(list(current_cookies)[:5])  # First 5 only
        
        logger.info(f"Cookie debug info - Mobile: {is_mobile_safari}, SameSite: {samesite}, Secure: {secure}, Domain: {domain}, Origin: {request.META.get('HTTP_ORIGIN')}")
        
        # Add cookie size warning if tokens are too large
        if access_token and len(access_token) > 4000:
            logger.warning(f"Access token very large ({len(access_token)} chars) - may cause mobile cookie issues")
        if refresh_token and len(refresh_token) > 4000:
            logger.warning(f"Refresh token very large ({len(refresh_token)} chars) - may cause mobile cookie issues")
    
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
    
    # Mobile Safari Specific Configuration
    secure = True  # Always secure in production
    samesite = 'Lax'  # Force Lax for mobile Safari
    domain = None  # Let browser handle domain
    
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