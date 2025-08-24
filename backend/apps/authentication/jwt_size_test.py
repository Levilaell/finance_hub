"""
Teste de tamanho de tokens JWT - pode ser o problema real
"""
import logging
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .cookie_middleware import _is_mobile_safari

logger = logging.getLogger(__name__)
User = get_user_model()


class JWTSizeTestView(APIView):
    """
    Testa tamanho dos tokens JWT vs limites de cookies móveis
    """
    permission_classes = (AllowAny,)
    
    def get(self, request):
        """Análise de tokens JWT reais"""
        user = User.objects.first()
        if not user:
            return Response({'error': 'No users available for testing'})
            
        # Gerar tokens JWT reais
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
        
        # Limites conhecidos de cookies por browser
        cookie_limits = {
            'safari_mobile': 4093,  # bytes
            'safari_desktop': 4093,
            'chrome_mobile': 4093,
            'chrome_desktop': 4093,
            'general_safe_limit': 4000
        }
        
        access_size = len(access_token.encode('utf-8'))
        refresh_size = len(refresh_token.encode('utf-8'))
        total_size = access_size + refresh_size
        
        analysis = {
            'mobile_safari_detected': is_mobile_safari,
            'user_agent': user_agent[:100],
            'token_sizes': {
                'access_token_bytes': access_size,
                'refresh_token_bytes': refresh_size,  
                'total_bytes': total_size,
                'access_token_chars': len(access_token),
                'refresh_token_chars': len(refresh_token)
            },
            'cookie_limits': cookie_limits,
            'size_analysis': {
                'access_exceeds_safe_limit': access_size > cookie_limits['general_safe_limit'],
                'refresh_exceeds_safe_limit': refresh_size > cookie_limits['general_safe_limit'],
                'total_exceeds_safe_limit': total_size > cookie_limits['general_safe_limit'],
                'likely_mobile_safari_issue': is_mobile_safari and (access_size > 4000 or refresh_size > 4000)
            },
            'recommendations': []
        }
        
        # Gerar recomendações baseadas no tamanho
        if access_size > 4000:
            analysis['recommendations'].append('Access token muito grande para Mobile Safari - implementar token splitting')
            
        if refresh_size > 4000:
            analysis['recommendations'].append('Refresh token muito grande para Mobile Safari - usar sessões server-side')
            
        if total_size > 8000:
            analysis['recommendations'].append('CRÍTICO: Total de cookies muito grande - usar sessionStorage + headers')
            
        if is_mobile_safari and total_size > 3000:
            analysis['recommendations'].append('Mobile Safari: Considerar fallback para localStorage/sessionStorage')
            
        # Log dos resultados
        logger.warning(f"JWT Size Analysis - Mobile Safari: {is_mobile_safari}, Access: {access_size}B, Refresh: {refresh_size}B, Total: {total_size}B")
        
        return Response(analysis)
    
    def post(self, request):
        """Testar cookies de tamanhos diferentes"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile_safari = _is_mobile_safari(user_agent)
        
        # Gerar strings de tamanhos diferentes para teste
        test_sizes = [100, 1000, 2000, 4000, 6000]  # bytes
        
        response = Response({
            'message': 'Testing different cookie sizes',
            'mobile_safari': is_mobile_safari,
            'sizes_tested': test_sizes,
            'test_timestamp': timezone.now().isoformat()
        })
        
        # Definir cookies de tamanhos diferentes
        for size in test_sizes:
            cookie_name = f'size_test_{size}'
            cookie_value = 'X' * (size - len(cookie_name) - 20)  # Ajustar para tamanho aproximado
            
            try:
                response.set_cookie(
                    cookie_name,
                    cookie_value,
                    max_age=300,
                    secure=True,
                    httponly=False,  # Acessível por JS para debug
                    samesite='Lax'
                )
                logger.info(f"Set cookie {cookie_name} with ~{size} bytes")
            except Exception as e:
                logger.error(f"Failed to set cookie {cookie_name}: {e}")
        
        # Definir um cookie muito pequeno como controle
        response.set_cookie(
            'control_small',
            'small',
            max_age=300,
            secure=False,  # Sem secure para máxima compatibilidade
            httponly=False,
            samesite='Lax'
        )
        
        response['X-Test-Mobile-Safari'] = str(is_mobile_safari)
        response['X-Sizes-Tested'] = ','.join(map(str, test_sizes))
        
        return response