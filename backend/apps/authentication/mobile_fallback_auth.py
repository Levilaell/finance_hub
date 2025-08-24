"""
Mobile Safari Authentication Fallback System
Provides multiple authentication strategies when cookies fail
"""
import logging
from django.http import JsonResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .cookie_middleware import _is_mobile_safari, set_jwt_cookies

logger = logging.getLogger(__name__)


class MobileAuthFallbackView(APIView):
    """
    Provides multiple authentication strategies for Mobile Safari
    """
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """
        Set authentication tokens using multiple strategies:
        1. Cookies (primary)
        2. Response body for sessionStorage (fallback 1) 
        3. Response headers for localStorage (fallback 2)
        """
        # Get authentication data from request
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=400)
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
        
        # Prepare response data
        response_data = {
            'success': True,
            'mobile_safari_detected': is_mobile_safari,
            'auth_strategies': {
                'cookies_set': True,
                'tokens_in_body': True,
                'tokens_in_headers': True
            },
            'fallback_instructions': {
                'strategy_1': 'Use cookies (automatic)',
                'strategy_2': 'Store tokens from body in sessionStorage',
                'strategy_3': 'Store tokens from headers in localStorage'
            },
            # Strategy 2: Tokens in response body for sessionStorage
            'tokens': {
                'access': access_token,
                'refresh': refresh_token,
                'expires_in': int(settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME').total_seconds()),
                'token_type': 'Bearer'
            }
        }
        
        response = Response(response_data)
        
        # Strategy 1: Set cookies (primary method)
        response = set_jwt_cookies(response, {
            'access': access_token,
            'refresh': refresh_token
        }, request, user)
        
        # Strategy 3: Set tokens in headers for localStorage fallback
        response['X-Access-Token'] = access_token
        response['X-Refresh-Token'] = refresh_token
        response['X-Token-Type'] = 'Bearer'
        response['X-Expires-In'] = str(int(settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME').total_seconds()))
        
        # Allow frontend to access custom headers
        response['Access-Control-Expose-Headers'] = 'X-Access-Token, X-Refresh-Token, X-Token-Type, X-Expires-In'
        
        logger.info(f"Multi-strategy authentication set for user {user.id} - Mobile Safari: {is_mobile_safari}")
        
        return response
    
    def get(self, request):
        """
        Check which authentication strategies are working
        """
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
        
        # Check cookie authentication
        access_cookie = request.COOKIES.get(getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token'))
        refresh_cookie = request.COOKIES.get(getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'refresh_token'))
        
        # Check header authentication  
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        has_bearer_token = auth_header.startswith('Bearer ')
        
        strategy_status = {
            'mobile_safari_detected': is_mobile_safari,
            'user_agent': user_agent[:50] + '...' if len(user_agent) > 50 else user_agent,
            'authentication_strategies': {
                'cookies': {
                    'access_token_present': bool(access_cookie),
                    'refresh_token_present': bool(refresh_cookie),
                    'total_cookies': len(request.COOKIES),
                    'working': bool(access_cookie and refresh_cookie)
                },
                'headers': {
                    'authorization_present': bool(auth_header),
                    'bearer_format': has_bearer_token,
                    'working': has_bearer_token
                }
            },
            'recommended_strategy': 'cookies' if access_cookie else 'headers' if has_bearer_token else 'none_working'
        }
        
        return Response(strategy_status)


class TokenValidationView(APIView):
    """
    Validate tokens from any source (cookies, headers, body)
    """
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """
        Validate an access token from any source
        """
        # Try to get token from multiple sources
        token = None
        source = None
        
        # 1. Try Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            source = 'header'
        
        # 2. Try cookies
        if not token:
            token = request.COOKIES.get(getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token'))
            if token:
                source = 'cookie'
        
        # 3. Try request body
        if not token:
            token = request.data.get('access_token')
            if token:
                source = 'body'
        
        if not token:
            return Response({
                'valid': False,
                'error': 'No token found in headers, cookies, or body',
                'sources_checked': ['Authorization header', 'cookies', 'request body']
            }, status=400)
        
        # Validate token
        try:
            from rest_framework_simplejwt.tokens import UntypedToken
            from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
            
            UntypedToken(token)  # This will raise an exception if token is invalid
            
            # If we get here, token is valid
            return Response({
                'valid': True,
                'source': source,
                'token_length': len(token),
                'message': f'Token successfully validated from {source}'
            })
            
        except (InvalidToken, TokenError) as e:
            return Response({
                'valid': False,
                'source': source,
                'error': str(e),
                'message': f'Token from {source} is invalid'
            }, status=400)