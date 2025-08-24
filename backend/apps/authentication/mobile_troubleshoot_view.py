"""
View simplificada para troubleshooting de cookies mobile em tempo real
"""
import logging
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .cookie_middleware import _is_mobile_safari, set_mobile_compatible_cookies

logger = logging.getLogger(__name__)
User = get_user_model()


class MobileTroubleshootView(APIView):
    """
    Endpoint simplificado para troubleshooting de cookies mobile
    GET: Retorna info sobre cookies recebidos
    POST: Testa definição de cookies
    """
    permission_classes = (AllowAny,)
    
    def get(self, request):
        """Diagnóstico de cookies recebidos"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
        
        # Verificar todos os cookies possíveis
        cookie_status = {}
        cookie_names = [
            'access_token', 'refresh_token', 'mobile_access_token', 
            'mobile_refresh_token', 'fallback_access_token', 'test_mobile_cookie'
        ]
        
        for cookie_name in cookie_names:
            cookie_value = request.COOKIES.get(cookie_name)
            cookie_status[cookie_name] = {
                'present': bool(cookie_value),
                'length': len(cookie_value) if cookie_value else 0,
                'value_start': cookie_value[:20] if cookie_value else None
            }
        
        diagnosis = {
            'timestamp': timezone.now().isoformat(),
            'browser_info': {
                'user_agent': user_agent[:100],
                'is_mobile_safari': is_mobile_safari,
                'host': request.META.get('HTTP_HOST'),
                'origin': request.META.get('HTTP_ORIGIN'),
                'referer': request.META.get('HTTP_REFERER'),
                'x_forwarded_proto': request.META.get('HTTP_X_FORWARDED_PROTO'),
            },
            'cookies': {
                'total_received': len(request.COOKIES),
                'all_names': list(request.COOKIES.keys()),
                'auth_cookies': cookie_status
            },
            'settings': {
                'jwt_cookie_secure': getattr(settings, 'JWT_COOKIE_SECURE', None),
                'jwt_cookie_samesite': getattr(settings, 'JWT_COOKIE_SAMESITE', None),
                'jwt_cookie_domain': getattr(settings, 'JWT_COOKIE_DOMAIN', None),
                'debug': settings.DEBUG
            }
        }
        
        # Logging para análise
        logger.info(f"Mobile troubleshoot GET - Mobile Safari: {is_mobile_safari}, Cookies: {len(request.COOKIES)}, Auth cookies present: {sum(1 for c in cookie_status.values() if c['present'])}")
        
        response = Response(diagnosis)
        
        # Headers adicionais para debugging
        response['X-Mobile-Safari'] = str(is_mobile_safari)
        response['X-Cookies-Total'] = str(len(request.COOKIES))
        response['X-Auth-Cookies-Present'] = str(sum(1 for c in cookie_status.values() if c['present']))
        
        return response
    
    def post(self, request):
        """Testar definição de cookies com diferentes estratégias"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
        
        # Para teste, usar primeiro usuário disponível
        user = User.objects.first()
        if not user:
            return Response({
                'error': 'No users available for testing'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Gerar tokens de teste
        refresh = RefreshToken.for_user(user)
        tokens = {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }
        
        test_info = {
            'timestamp': timezone.now().isoformat(),
            'message': 'Test cookies set with multiple strategies',
            'browser_info': {
                'user_agent': user_agent[:100],
                'is_mobile_safari': is_mobile_safari,
                'host': request.META.get('HTTP_HOST'),
                'origin': request.META.get('HTTP_ORIGIN')
            },
            'test_user': {
                'id': user.id,
                'email': user.email
            },
            'tokens': {
                'access_length': len(tokens['access']),
                'refresh_length': len(tokens['refresh'])
            }
        }
        
        response = Response(test_info)
        
        # Aplicar estratégia mobile se necessário
        if is_mobile_safari:
            set_mobile_compatible_cookies(response, tokens, request, user)
            response['X-Strategy-Used'] = 'mobile_compatible'
        else:
            # Usar estratégia padrão + alguns fallbacks
            response.set_cookie(
                'test_access_token',
                tokens['access'],
                max_age=300,  # 5 minutos
                secure=True,
                httponly=True,
                samesite='Lax',
                path='/'
            )
            response.set_cookie(
                'test_refresh_token',
                tokens['refresh'],
                max_age=300,
                secure=True,
                httponly=True,
                samesite='Lax',
                path='/'
            )
            response['X-Strategy-Used'] = 'standard_with_fallback'
        
        # Headers de debug
        response['X-Test-Timestamp'] = str(timezone.now().timestamp())
        response['X-Mobile-Safari-Detected'] = str(is_mobile_safari)
        
        logger.info(f"Mobile troubleshoot POST - Mobile Safari: {is_mobile_safari}, Strategy: {'mobile' if is_mobile_safari else 'standard'}, User: {user.email}")
        
        return response