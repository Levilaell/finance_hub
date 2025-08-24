"""
Mobile Safari Debug Endpoint
Helps frontend developers test token-based authentication
"""
import logging
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .cookie_middleware import _is_mobile_safari

logger = logging.getLogger(__name__)


class MobileSafariDebugView(APIView):
    """
    Debug endpoint to help frontend developers test Mobile Safari authentication
    """
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """
        Test token authentication from multiple sources
        Expected body: {"access_token": "your_token_here"}
        """
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
        
        # Get token from different sources
        sources_tested = {}
        
        # 1. Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token_from_header = auth_header[7:]
            sources_tested['authorization_header'] = self._test_token(token_from_header, 'header')
        else:
            sources_tested['authorization_header'] = {'present': False}
        
        # 2. Cookies
        access_cookie = request.COOKIES.get(
            getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token')
        )
        if access_cookie:
            sources_tested['cookies'] = self._test_token(access_cookie, 'cookie')
        else:
            sources_tested['cookies'] = {'present': False}
        
        # 3. Request body
        token_from_body = request.data.get('access_token')
        if token_from_body:
            sources_tested['request_body'] = self._test_token(token_from_body, 'body')
        else:
            sources_tested['request_body'] = {'present': False}
        
        # 4. Query parameter (emergency fallback)
        token_from_query = request.GET.get('auth_token')
        if token_from_query:
            sources_tested['query_parameter'] = self._test_token(token_from_query, 'query')
        else:
            sources_tested['query_parameter'] = {'present': False}
        
        # Determine best working source
        working_sources = [
            source for source, result in sources_tested.items() 
            if result.get('valid', False)
        ]
        
        response_data = {
            'mobile_safari_detected': is_mobile_safari,
            'user_agent': user_agent[:100],
            'sources_tested': sources_tested,
            'working_sources': working_sources,
            'recommendation': self._get_recommendation(working_sources, is_mobile_safari),
            'debug_info': {
                'request_path': request.path,
                'request_method': request.method,
                'origin': request.META.get('HTTP_ORIGIN', 'None'),
                'referer': request.META.get('HTTP_REFERER', 'None')[:100]
            }
        }
        
        return Response(response_data)
    
    def _test_token(self, token, source):
        """Test if a token is valid"""
        try:
            # Validate token structure and signature
            UntypedToken(token)
            
            # Extract user info
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            user_id = access_token.payload.get('user_id')
            
            return {
                'present': True,
                'valid': True,
                'user_id': user_id,
                'token_length': len(token),
                'source': source
            }
            
        except (InvalidToken, TokenError) as e:
            return {
                'present': True,
                'valid': False,
                'error': str(e),
                'token_length': len(token) if token else 0,
                'source': source
            }
    
    def _get_recommendation(self, working_sources, is_mobile_safari):
        """Get recommendation based on test results"""
        if not working_sources:
            if is_mobile_safari:
                return {
                    'status': 'critical',
                    'message': 'NO working authentication found for Mobile Safari',
                    'action': 'Check that login response includes tokens in body and headers',
                    'next_steps': [
                        'Verify login response contains mobile_fallback.detected: true',
                        'Check that tokens are stored in sessionStorage after login',
                        'Ensure Authorization header is added to API calls'
                    ]
                }
            else:
                return {
                    'status': 'warning', 
                    'message': 'No authentication found',
                    'action': 'Login first or provide valid token'
                }
        
        if 'authorization_header' in working_sources:
            return {
                'status': 'excellent',
                'message': 'Authorization header working perfectly',
                'action': 'This is the ideal authentication method - continue using'
            }
        
        if 'cookies' in working_sources and not is_mobile_safari:
            return {
                'status': 'good',
                'message': 'Cookies working (desktop browser)',
                'action': 'Cookies work well for desktop browsers'
            }
        
        if 'cookies' in working_sources and is_mobile_safari:
            return {
                'status': 'warning',
                'message': 'Cookies working in Mobile Safari (unusual)',
                'action': 'This may not work consistently - implement header fallback'
            }
        
        return {
            'status': 'info',
            'message': f'Authentication working via: {", ".join(working_sources)}',
            'action': 'Consider using Authorization header for best compatibility'
        }


class QuickAuthTestView(APIView):
    """
    Quick test endpoint - just checks if user is authenticated
    """
    # Note: This uses default DRF authentication, so it will test current auth state
    
    def get(self, request):
        """Quick auth status check"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
        
        # Check authentication status
        is_authenticated = hasattr(request, 'user') and request.user.is_authenticated
        
        response_data = {
            'authenticated': is_authenticated,
            'user_id': request.user.id if is_authenticated else None,
            'user_email': request.user.email if is_authenticated else None,
            'mobile_safari': is_mobile_safari,
            'timestamp': f"{timezone.now().isoformat()}",
            'auth_method_detected': self._detect_auth_method(request)
        }
        
        if is_authenticated:
            logger.info(f"Auth test SUCCESS for user {request.user.email} (Mobile Safari: {is_mobile_safari})")
        else:
            logger.warning(f"Auth test FAILED - no user authenticated (Mobile Safari: {is_mobile_safari})")
        
        return Response(response_data)
    
    def _detect_auth_method(self, request):
        """Detect which auth method was likely used"""
        # Check for Authorization header
        if request.META.get('HTTP_AUTHORIZATION'):
            return 'authorization_header'
        
        # Check for cookies
        from django.conf import settings
        access_cookie = request.COOKIES.get(
            getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token')
        )
        if access_cookie:
            return 'cookies'
        
        return 'unknown'