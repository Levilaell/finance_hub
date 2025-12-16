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

from .models import User, UserActivityLog, UserSettings
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    TokenResponseSerializer,
    UserSettingsSerializer
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

        # Log signup event
        UserActivityLog.log_event(
            user=user,
            event_type='signup',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            signup_price_id=user.signup_price_id,
            acquisition_angle=user.acquisition_angle
        )

        # Log automatic login after registration
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


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_settings_view(request):
    """
    Get or update user settings.
    GET /api/auth/settings/ - Get current settings
    PATCH /api/auth/settings/ - Update settings
    """
    settings = UserSettings.get_or_create_for_user(request.user)

    if request.method == 'GET':
        serializer = UserSettingsSerializer(settings)
        return Response(serializer.data)

    elif request.method == 'PATCH':
        serializer = UserSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.update(settings, serializer.validated_data)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_page_view(request):
    """
    Track page view for analytics.
    POST /api/auth/track-page-view/
    Body: {"page": "/dashboard", "referrer": "/login"}
    """
    page = request.data.get('page', '')
    referrer = request.data.get('referrer', '')

    if not page:
        return Response(
            {'error': 'page is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    UserActivityLog.log_event(
        user=request.user,
        event_type='page_view',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        page=page,
        referrer=referrer
    )

    return Response({'status': 'ok'})