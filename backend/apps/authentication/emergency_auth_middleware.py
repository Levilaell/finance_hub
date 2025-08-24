"""
Emergency Authentication Middleware for Mobile Safari
Allows authentication via query parameter as last resort fallback
"""
import logging
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class EmergencyAuthMiddleware:
    """
    Emergency authentication middleware that checks for tokens in:
    1. Authorization header (standard)
    2. Cookies (standard)
    3. Query parameter 'auth_token' (emergency fallback for Mobile Safari)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only process API requests
        if request.path.startswith('/api/'):
            self._try_emergency_auth(request)
        
        response = self.get_response(request)
        return response
    
    def _try_emergency_auth(self, request):
        """
        Try emergency authentication via query parameter if other methods fail
        """
        # Skip if already authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            return
        
        # Skip if Authorization header is present (let DRF handle it)
        if request.META.get('HTTP_AUTHORIZATION'):
            return
        
        # Skip if cookies are present (let DRF handle it)
        from django.conf import settings
        access_cookie = request.COOKIES.get(
            getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token')
        )
        if access_cookie:
            return
        
        # Emergency fallback: Check query parameter
        auth_token = request.GET.get('auth_token')
        if not auth_token:
            return
        
        try:
            # Validate token
            UntypedToken(auth_token)
            
            # Extract user from token
            from rest_framework_simplejwt.tokens import AccessToken
            token = AccessToken(auth_token)
            user_id = token.payload['user_id']
            
            user = User.objects.get(id=user_id)
            request.user = user
            
            # Log emergency auth usage
            logger.warning(f"Emergency auth used for user {user.email} on {request.path}")
            
            # Add debug header
            if hasattr(request, '_emergency_auth_used'):
                request._emergency_auth_used = True
        
        except (InvalidToken, TokenError, User.DoesNotExist, KeyError) as e:
            logger.warning(f"Emergency auth failed: {e}")
            # Don't modify request.user - let it remain anonymous
            pass