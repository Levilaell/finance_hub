"""
JWT Cookie Authentication for secure token handling
"""
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class JWTCookieAuthentication(JWTAuthentication):
    """
    Custom JWT authentication using httpOnly cookies
    """
    
    def authenticate(self, request):
        # Try cookie-based authentication first
        raw_token = self.get_raw_token_from_cookie(request)
        
        if raw_token is None:
            # Fallback to header-based authentication for backwards compatibility
            return super().authenticate(request)
        
        try:
            # Validate the token
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return user, validated_token
        except (InvalidToken, TokenError):
            # Token is invalid/expired - return None to allow other auth methods or AllowAny views
            # This prevents login failures when users have expired tokens in cookies
            return None
    
    def get_raw_token_from_cookie(self, request):
        """
        Extract JWT token from httpOnly cookie
        """
        cookie_name = getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token')
        return request.COOKIES.get(cookie_name)


class JWTRefreshCookieAuthentication(JWTAuthentication):
    """
    Custom JWT refresh authentication using httpOnly cookies
    """
    
    def authenticate(self, request):
        raw_token = self.get_raw_token_from_cookie(request)
        
        if raw_token is None:
            return None
        
        # Validate the refresh token
        from rest_framework_simplejwt.tokens import RefreshToken
        try:
            validated_token = RefreshToken(raw_token)
            user = self.get_user(validated_token)
            return user, validated_token
        except TokenError:
            # Return None instead of raising exception to allow graceful fallback
            return None
    
    def get_raw_token_from_cookie(self, request):
        """
        Extract refresh token from httpOnly cookie
        """
        cookie_name = getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'refresh_token')
        return request.COOKIES.get(cookie_name)