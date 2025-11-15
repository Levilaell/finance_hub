"""
Authentication views
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .models import User, UserActivityLog
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    TokenResponseSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    Registro de usuário
    POST /api/auth/register/
    """
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        # Criar usuário
        user = serializer.save()

        # Gerar tokens JWT automaticamente
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Atualizar último login
        user.last_login = timezone.now()
        user.last_login_ip = get_client_ip(request)
        user.save(update_fields=['last_login', 'last_login_ip'])

        # Log registration and automatic login
        UserActivityLog.log_event(
            user=user,
            event_type='login',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            login_method='registration'
        )

        return Response({
            'message': 'Usuário criado com sucesso!',
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login de usuário
    POST /api/auth/login/
    """
    serializer = LoginSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        user = serializer.validated_data['user']

        # Gerar tokens JWT
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Atualizar último login
        user.last_login = timezone.now()
        # Opcional: salvar IP do usuário
        user.last_login_ip = get_client_ip(request)
        user.save(update_fields=['last_login', 'last_login_ip'])

        # Log login activity
        UserActivityLog.log_event(
            user=user,
            event_type='login',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            login_method='jwt_api'
        )

        return Response({
            'message': 'Login realizado com sucesso!',
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    Dados do usuário logado
    GET /api/auth/profile/
    """
    user = request.user
    serializer = UserSerializer(user)
    
    return Response({
        'user': serializer.data
    }, status=status.HTTP_200_OK)


class RefreshView(TokenRefreshView):
    """
    Renovar access token
    POST /api/auth/refresh/
    Body: {"refresh": "token_here"}
    """
    
    def post(self, request, *args, **kwargs):
        try:
            # Usar a implementação padrão do DRF
            response = super().post(request, *args, **kwargs)
            
            return Response({
                'message': 'Token renovado com sucesso!',
                'tokens': response.data
            }, status=status.HTTP_200_OK)
            
        except TokenError as e:
            return Response({
                'error': 'Token de refresh inválido ou expirado.',
                'detail': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)


# Função auxiliar para pegar IP do cliente
def get_client_ip(request):
    """Pegar IP real do cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip