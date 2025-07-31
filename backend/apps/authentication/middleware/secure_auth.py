"""
Secure authentication middleware for httpOnly cookie-based JWT tokens
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

logger = logging.getLogger(__name__)
User = get_user_model()


class SecureJWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to handle JWT authentication via secure httpOnly cookies
    Replaces token-based authentication for enhanced security
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Cookie configuration
        self.access_cookie_name = getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token')
        self.refresh_cookie_name = getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'refresh_token')
        self.cookie_path = getattr(settings, 'JWT_COOKIE_PATH', '/')
        self.cookie_domain = getattr(settings, 'JWT_COOKIE_DOMAIN', None)
        self.cookie_secure = getattr(settings, 'JWT_COOKIE_SECURE', not settings.DEBUG)
        self.cookie_httponly = True  # Always True for security
        self.cookie_samesite = getattr(settings, 'JWT_COOKIE_SAMESITE', 'Lax')
        
        # Token lifetimes
        self.access_token_lifetime = getattr(settings, 'SIMPLE_JWT', {}).get(
            'ACCESS_TOKEN_LIFETIME', timedelta(minutes=30)
        )
        self.refresh_token_lifetime = getattr(settings, 'SIMPLE_JWT', {}).get(
            'REFRESH_TOKEN_LIFETIME', timedelta(days=3)
        )

    def process_request(self, request):
        """
        Extract JWT tokens from httpOnly cookies and set in request
        """
        # Skip for non-API requests
        if not request.path.startswith('/api/'):
            return None
            
        # Skip for auth endpoints that don't need authentication
        auth_endpoints = ['/api/auth/login/', '/api/auth/register/', '/api/auth/refresh/']
        if any(request.path.startswith(endpoint) for endpoint in auth_endpoints):
            return None
            
        access_token = request.COOKIES.get(self.access_cookie_name)
        
        if access_token:
            try:
                # Validate access token
                token = AccessToken(access_token)
                user_id = token.payload.get('user_id')
                
                if user_id:
                    try:
                        user = User.objects.get(id=user_id)
                        request.user = user
                        request.jwt_token = token
                        
                        # Log successful authentication
                        logger.debug(f"JWT authentication successful for user {user.email}")
                        
                    except User.DoesNotExist:
                        logger.warning(f"JWT token contains invalid user_id: {user_id}")
                        return self._clear_auth_cookies_response(request)
                        
            except (TokenError, InvalidToken) as e:
                logger.debug(f"Invalid access token: {str(e)}")
                # Try to refresh token automatically
                return self._attempt_token_refresh(request)
                
        return None

    def _attempt_token_refresh(self, request) -> Optional[HttpResponse]:
        """
        Attempt to refresh access token using refresh token
        """
        refresh_token = request.COOKIES.get(self.refresh_cookie_name)
        
        if not refresh_token:
            return self._clear_auth_cookies_response(request)
            
        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = refresh.access_token
            
            # Get user for the new token
            user_id = new_access_token.payload.get('user_id')
            user = User.objects.get(id=user_id)
            
            # Create response with new tokens
            response_data = {
                'message': 'Token refreshed successfully',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            }
            
            response = JsonResponse(response_data)
            
            # Set new access token cookie
            self._set_token_cookies(response, str(new_access_token), str(refresh))
            
            # Set user in request for this request
            request.user = user
            request.jwt_token = new_access_token
            
            logger.info(f"Token refreshed successfully for user {user.email}")
            return None  # Continue processing the request
            
        except (TokenError, InvalidToken, User.DoesNotExist) as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            return self._clear_auth_cookies_response(request)

    def _clear_auth_cookies_response(self, request) -> HttpResponse:
        """
        Return response that clears authentication cookies
        """
        response = JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Clear auth cookies
        response.delete_cookie(
            self.access_cookie_name,
            path=self.cookie_path,
            domain=self.cookie_domain
        )
        response.delete_cookie(
            self.refresh_cookie_name,
            path=self.cookie_path,
            domain=self.cookie_domain
        )
        
        return response

    def _set_token_cookies(self, response: HttpResponse, access_token: str, refresh_token: str):
        """
        Set secure JWT token cookies on response
        """
        # Set access token cookie
        response.set_cookie(
            self.access_cookie_name,
            access_token,
            max_age=int(self.access_token_lifetime.total_seconds()),
            path=self.cookie_path,
            domain=self.cookie_domain,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite
        )
        
        # Set refresh token cookie
        response.set_cookie(
            self.refresh_cookie_name,
            refresh_token,
            max_age=int(self.refresh_token_lifetime.total_seconds()),
            path=self.cookie_path,
            domain=self.cookie_domain,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite
        )

    def process_response(self, request, response):
        """
        Process response to handle token setting for auth endpoints
        """
        # Handle login response
        if (request.path == '/api/auth/login/' and 
            request.method == 'POST' and 
            response.status_code == 200):
            
            try:
                response_data = json.loads(response.content.decode('utf-8'))
                tokens = response_data.get('tokens', {})
                
                if tokens.get('access') and tokens.get('refresh'):
                    # Set secure cookies
                    self._set_token_cookies(
                        response,
                        tokens['access'],
                        tokens['refresh']
                    )
                    
                    # Remove tokens from response body for security
                    response_data.pop('tokens', None)
                    response.content = json.dumps(response_data).encode('utf-8')
                    
                    logger.info(f"Set secure auth cookies for user login")
                    
            except (json.JSONDecodeError, KeyError):
                pass  # Not a JSON response or missing expected data
        
        # Handle logout response
        elif (request.path == '/api/auth/logout/' and 
              request.method == 'POST'):
            
            # Clear auth cookies on logout
            response.delete_cookie(
                self.access_cookie_name,
                path=self.cookie_path,
                domain=self.cookie_domain
            )
            response.delete_cookie(
                self.refresh_cookie_name,
                path=self.cookie_path,
                domain=self.cookie_domain
            )
            
            logger.info("Cleared auth cookies on logout")
        
        return response


class CSRFExemptionMiddleware(MiddlewareMixin):
    """
    Middleware to handle CSRF exemptions for JWT-authenticated API calls
    while ensuring CSRF protection for session-based requests
    """
    
    def process_request(self, request):
        """
        Exempt CSRF for JWT-authenticated API requests
        """
        # Only apply to API endpoints
        if not request.path.startswith('/api/'):
            return None
            
        # Check if request has valid JWT token
        if hasattr(request, 'jwt_token') and request.jwt_token:
            # Mark as CSRF exempt for JWT-authenticated requests
            setattr(request, '_dont_enforce_csrf_checks', True)
            
        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add comprehensive security headers
    """
    
    def process_response(self, request, response):
        """
        Add security headers to response
        """
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'"
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Other security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # HSTS for HTTPS
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response