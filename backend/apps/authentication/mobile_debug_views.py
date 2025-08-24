"""
Mobile debugging views for cookie authentication issues
"""
import logging
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .cookie_middleware import _is_mobile_safari

logger = logging.getLogger(__name__)


class MobileCookieDebugView(APIView):
    """
    Debug endpoint to test cookie compatibility for mobile browsers
    """
    permission_classes = (AllowAny,)
    
    def get(self, request):
        """Get cookie debug information"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
        
        # Check for existing cookies
        access_cookie = request.COOKIES.get(getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token'))
        refresh_cookie = request.COOKIES.get(getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'refresh_token'))
        mobile_access = request.COOKIES.get('mobile_access_token')
        mobile_refresh = request.COOKIES.get('mobile_refresh_token')
        
        debug_info = {
            'user_agent': user_agent[:100] + '...' if len(user_agent) > 100 else user_agent,
            'is_mobile_safari': is_mobile_safari,
            'cookies_received': {
                'access_token': bool(access_cookie),
                'refresh_token': bool(refresh_cookie),
                'mobile_access_token': bool(mobile_access),
                'mobile_refresh_token': bool(mobile_refresh),
            },
            'cookie_values': {
                'access_token': access_cookie[:20] + '...' if access_cookie else None,
                'refresh_token': refresh_cookie[:20] + '...' if refresh_cookie else None,
                'mobile_access_token': mobile_access[:20] + '...' if mobile_access else None,
                'mobile_refresh_token': mobile_refresh[:20] + '...' if mobile_refresh else None,
            },
            'headers': {
                'origin': request.META.get('HTTP_ORIGIN'),
                'referer': request.META.get('HTTP_REFERER'),
                'forwarded_for': request.META.get('HTTP_X_FORWARDED_FOR'),
                'forwarded_proto': request.META.get('HTTP_X_FORWARDED_PROTO'),
            },
            'settings_debug': {
                'jwt_cookie_secure': getattr(settings, 'JWT_COOKIE_SECURE', 'not_set'),
                'jwt_cookie_samesite': getattr(settings, 'JWT_COOKIE_SAMESITE', 'not_set'),
                'jwt_cookie_domain': getattr(settings, 'JWT_COOKIE_DOMAIN', 'not_set'),
                'debug_mode': settings.DEBUG,
            }
        }
        
        return Response(debug_info)
    
    def post(self, request):
        """Test cookie setting with different strategies"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
        
        test_value = 'test_cookie_value_12345'
        
        response = Response({
            'message': 'Test cookies set',
            'is_mobile_safari': is_mobile_safari,
            'timestamp': str(timezone.now())
        })
        
        # Strategy 1: Standard cookies
        response.set_cookie(
            'test_standard',
            test_value,
            max_age=300,  # 5 minutes
            secure=True,
            httponly=True,
            samesite='None' if not is_mobile_safari else 'Lax',
            path='/'
        )
        
        # Strategy 2: Lax cookies  
        response.set_cookie(
            'test_lax',
            test_value,
            max_age=300,
            secure=True,
            httponly=True,
            samesite='Lax',
            path='/'
        )
        
        # Strategy 3: Accessible cookies (for mobile fallback)
        response.set_cookie(
            'test_accessible',
            test_value,
            max_age=300,
            secure=True,
            httponly=False,  # Accessible to JS
            samesite='Lax',
            path='/'
        )
        
        # Strategy 4: Same-origin only
        response.set_cookie(
            'test_strict',
            test_value,
            max_age=300,
            secure=True,
            httponly=True,
            samesite='Strict',
            path='/'
        )
        
        logger.info(f"Test cookies set for {'Mobile Safari' if is_mobile_safari else 'Other browser'}")
        
        return response


class MobileAuthTestView(APIView):
    """
    Test authentication specifically for mobile browsers
    """
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """Test login with mobile-specific cookie handling"""
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.contrib.auth import get_user_model
        from .cookie_middleware import set_mobile_compatible_cookies
        
        User = get_user_model()
        
        # For demo purposes, create a test token
        # In real implementation, this would be after successful authentication
        test_user_id = request.data.get('test_user_id')
        if not test_user_id:
            return Response({
                'error': 'test_user_id required for testing'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=test_user_id)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Generate test tokens
        refresh = RefreshToken.for_user(user)
        
        response = Response({
            'message': 'Test authentication successful',
            'user_id': user.id,
            'mobile_strategy_used': True
        })
        
        # Use mobile-compatible cookie setting
        set_mobile_compatible_cookies(response, {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, request, user)
        
        return response