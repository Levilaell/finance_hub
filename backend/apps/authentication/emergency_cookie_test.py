"""
Emergency cookie test view for Mobile Safari - Ultra simplified
"""
import logging
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .cookie_middleware import _is_mobile_safari

logger = logging.getLogger(__name__)


class EmergencyCookieTestView(APIView):
    """
    Teste de emergência para cookies Mobile Safari
    Testa cookies muito simples primeiro
    """
    permission_classes = (AllowAny,)
    
    def get(self, request):
        """Status dos cookies recebidos"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
        
        # Verificar apenas cookies de teste simples
        test_cookies = {}
        for cookie_name in ['simple_test', 'mobile_test', 'emergency_test']:
            value = request.COOKIES.get(cookie_name)
            test_cookies[cookie_name] = {
                'present': bool(value),
                'value': value
            }
        
        return Response({
            'mobile_safari': is_mobile_safari,
            'user_agent': user_agent[:50],
            'host': request.META.get('HTTP_HOST'),
            'total_cookies': len(request.COOKIES),
            'all_cookie_names': list(request.COOKIES.keys()),
            'test_cookies': test_cookies,
            'settings': {
                'samesite_setting': getattr(settings, 'JWT_COOKIE_SAMESITE', 'not_set'),
                'secure_setting': getattr(settings, 'JWT_COOKIE_SECURE', 'not_set')
            }
        })
    
    def post(self, request):
        """Definir cookies de teste ultra simples"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
        
        response = Response({
            'message': 'Emergency test cookies set',
            'mobile_safari': is_mobile_safari,
            'strategies_applied': []
        })
        
        strategies = []
        
        # Strategy 1: Cookie mais simples possível
        response.set_cookie(
            'simple_test',
            'value123',
            max_age=600,
            secure=False,  # HTTP OK
            httponly=False,  # JS accessible
            samesite=None,  # No SameSite at all
            domain=None,
            path='/'
        )
        strategies.append('simple_no_restrictions')
        
        # Strategy 2: Cookie com SameSite=Lax
        response.set_cookie(
            'mobile_test',
            'mobile456',
            max_age=600,
            secure=True,
            httponly=False,
            samesite='Lax',
            domain=None,
            path='/'
        )
        strategies.append('lax_secure')
        
        # Strategy 3: Cookie de emergência específico para mobile
        if is_mobile_safari:
            response.set_cookie(
                'emergency_test',
                'emergency789',
                max_age=600,
                secure=True,
                httponly=True,
                samesite='Lax',
                domain=None,
                path='/'
            )
            strategies.append('mobile_safari_optimized')
        
        # Strategy 4: Tentar sem domain explícito e sem secure
        response.set_cookie(
            'fallback_test',
            'fallback000',
            max_age=600,
            secure=False,
            httponly=False,
            samesite='Lax'
        )
        strategies.append('insecure_fallback')
        
        response.data['strategies_applied'] = strategies
        
        # Headers de debug
        response['X-Emergency-Test'] = 'true'
        response['X-Mobile-Safari'] = str(is_mobile_safari)
        response['X-Strategies-Count'] = str(len(strategies))
        response['X-Test-Timestamp'] = str(timezone.now().timestamp())
        
        logger.warning(f"🚨 EMERGENCY COOKIE TEST - Mobile Safari: {is_mobile_safari}, Strategies: {len(strategies)}")
        
        return response