"""
Authentication views
"""
import secrets
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import EmailVerification, PasswordReset
from .serializers import (
    ChangePasswordSerializer,
    DeleteAccountSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    TokenSerializer,
    UserSerializer,
)
from .utils import (
    generate_2fa_secret,
    generate_backup_codes,
    hash_backup_codes,
    get_totp_uri,
    generate_qr_code,
    verify_totp_token,
    verify_backup_code,
)

User = get_user_model()


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST'), name='dispatch')
class RegisterView(generics.CreateAPIView):
    """User registration with company creation"""
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Create email verification token
        verification_token = secrets.token_urlsafe(32)
        EmailVerification.objects.create(
            user=user,
            token=verification_token,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Send verification email
        from apps.notifications.email_service import send_verification_email_task
        from django.conf import settings
        
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        send_verification_email_task.delay(user.id, verification_url)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Cadastro realizado com sucesso. Por favor, verifique seu e-mail para confirmar sua conta.'
        }, status=status.HTTP_201_CREATED)


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST'), name='dispatch')
class LoginView(APIView):
    """User login"""
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Update last login
        user.last_login = timezone.now()
        user.last_login_ip = request.META.get('REMOTE_ADDR')
        user.save(update_fields=['last_login', 'last_login_ip'])
        
        # Check if 2FA is enabled
        if user.is_two_factor_enabled:
            # Require 2FA code
            two_fa_code = request.data.get('two_fa_code')
            if not two_fa_code:
                return Response({
                    'requires_2fa': True,
                    'message': 'Código de autenticação de dois fatores necessário'
                }, status=status.HTTP_200_OK)
            
            # Verify 2FA code
            if not verify_totp_token(user.two_factor_secret, two_fa_code):
                # Try backup code
                if not verify_backup_code(user, two_fa_code):
                    return Response({
                        'error': 'Código de autenticação inválido'
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class LogoutView(APIView):
    """User logout (blacklist refresh token)"""
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    # Try to blacklist if method exists
                    if hasattr(token, 'blacklist'):
                        token.blacklist()
                    else:
                        # Alternative: just mark as used (this invalidates the token)
                        token.set_jti()
                        token.set_exp()
                except Exception:
                    # If token processing fails, still return success
                    # (frontend should remove token anyway)
                    pass
            return Response({'message': 'Logout realizado com sucesso'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile view"""
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """Change password view"""
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set new password
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Senha alterada com sucesso'})


@method_decorator(ratelimit(key='ip', rate='3/h', method='POST'), name='dispatch')
class PasswordResetRequestView(APIView):
    """Request password reset"""
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetRequestSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Create reset token
        reset_token = secrets.token_urlsafe(32)
        PasswordReset.objects.create(
            user=user,
            token=reset_token,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Send password reset email
        from apps.notifications.email_service import send_password_reset_email_task
        from django.conf import settings
        
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        send_password_reset_email_task.delay(user.id, reset_url)
        
        return Response({
            'message': 'Link de redefinição de senha foi enviado para seu e-mail.'
        })


class PasswordResetConfirmView(APIView):
    """Confirm password reset"""
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetConfirmSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        
        # Find valid reset token
        reset = PasswordReset.objects.filter(
            token=token,
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if not reset:
            return Response({
                'error': 'Token de redefinição inválido ou expirado.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset password
        user = reset.user
        user.set_password(password)
        user.save()
        
        # Mark token as used
        reset.is_used = True
        reset.save()
        
        return Response({'message': 'Senha redefinida com sucesso.'})


class EmailVerificationView(APIView):
    """Verify email address"""
    permission_classes = (AllowAny,)
    serializer_class = EmailVerificationSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        
        # Find valid verification token
        verification = EmailVerification.objects.filter(
            token=token,
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if not verification:
            return Response({
                'error': 'Token de verificação inválido ou expirado.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify email
        user = verification.user
        user.is_email_verified = True
        user.save()
        
        # Mark token as used
        verification.is_used = True
        verification.save()
        
        return Response({'message': 'E-mail verificado com sucesso.'})


class ResendVerificationView(APIView):
    """Resend email verification"""
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        user = request.user
        
        if user.is_email_verified:
            return Response({
                'message': 'E-mail já foi verificado.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new verification token
        verification_token = secrets.token_urlsafe(32)
        EmailVerification.objects.create(
            user=user,
            token=verification_token,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Send verification email  
        from apps.notifications.email_service import send_verification_email_task
        from django.conf import settings
        
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        send_verification_email_task.delay(user.id, verification_url)
        
        return Response({
            'message': 'E-mail de verificação foi enviado.'
        })


class CustomTokenRefreshView(APIView):
    """Custom token refresh view"""
    permission_classes = (AllowAny,)
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'error': 'Token de atualização é obrigatório'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Validate and refresh the token
            refresh = RefreshToken(refresh_token)
            
            # Generate new access token
            access_token = refresh.access_token
            
            # Return both tokens
            return Response({
                'access': str(access_token),
                'refresh': str(refresh),
            })
            
        except Exception as e:
            return Response(
                {'error': 'Token de atualização inválido'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )


# Health check endpoint removed - not used by frontend
# @api_view(['GET'])
# @permission_classes([AllowAny])
# def health_check(request):
#     """Health check endpoint"""
#     return Response({
#         'status': 'healthy',
#         'timestamp': timezone.now()
#     })


@method_decorator(ratelimit(key='user', rate='5/h', method='GET'), name='dispatch')
class Setup2FAView(APIView):
    """Setup 2FA for user"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Generate secret if not exists
        if not user.two_factor_secret:
            user.two_factor_secret = generate_2fa_secret()
            user.save()
        
        # Generate QR code
        uri = get_totp_uri(user, user.two_factor_secret)
        qr_code = generate_qr_code(uri)
        
        return Response({
            'qr_code': qr_code,
            'backup_codes_count': len(user.backup_codes) if user.backup_codes else 0,
            'setup_complete': False
        })


@method_decorator(ratelimit(key='user', rate='10/h', method='POST'), name='dispatch')
class Enable2FAView(APIView):
    """Enable 2FA after verification"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        token = request.data.get('token')
        
        if not token:
            return Response({
                'error': 'Token de verificação necessário'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.two_factor_secret:
            return Response({
                'error': 'Por favor, configure a 2FA primeiro'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify token
        if not verify_totp_token(user.two_factor_secret, token):
            return Response({
                'error': 'Token de verificação inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Enable 2FA and generate hashed backup codes
        backup_codes = generate_backup_codes()
        user.is_two_factor_enabled = True
        user.backup_codes = hash_backup_codes(backup_codes)
        user.save()
        
        # Return the plain text codes only once
        return Response({
            'message': '2FA ativada com sucesso',
            'backup_codes': backup_codes  # Show plain codes only once
        })
        


class Disable2FAView(APIView):
    """Disable 2FA"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        password = request.data.get('password')
        
        if not password:
            return Response({
                'error': 'Senha necessária'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.check_password(password):
            return Response({
                'error': 'Senha inválida'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Disable 2FA
        user.is_two_factor_enabled = False
        user.two_factor_secret = ''
        user.backup_codes = []
        user.save()
        
        return Response({
            'message': '2FA desativada com sucesso'
        })


# BackupCodesView removed - not used by frontend
# class BackupCodesView(APIView):
#     """Regenerate backup codes"""
#     permission_classes = [IsAuthenticated]
#     
#     def post(self, request):
#         user = request.user
#         
#         if not user.is_two_factor_enabled:
#             return Response({
#                 'error': '2FA não está ativada'
#             }, status=status.HTTP_400_BAD_REQUEST)
#         
#         # Regenerate hashed backup codes
#         backup_codes = generate_backup_codes()
#         user.backup_codes = hash_backup_codes(backup_codes)
#         user.save()
#         
#         return Response({
#             'backup_codes': backup_codes,  # Show plain codes only once
#             'message': 'Novos códigos de backup gerados. Por favor, guarde-os com segurança.'
#         })


@method_decorator(ratelimit(key='user', rate='3/h', method='POST'), name='dispatch')
class DeleteAccountView(APIView):
    """Delete user account with password verification"""
    permission_classes = [IsAuthenticated]
    serializer_class = DeleteAccountSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Additional safety check - ensure user is not a superuser
        if user.is_superuser:
            return Response({
                'error': 'Contas de administrador não podem ser deletadas.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Log the account deletion for audit purposes
        print(f"Deleting account for user: {user.email} (ID: {user.id})")
        
        try:
            # Delete user and all related data (CASCADE should handle this)
            user.delete()
            
            return Response({
                'message': 'Conta deletada com sucesso.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Error deleting user account {user.id}: {str(e)}")
            return Response({
                'error': 'Erro interno do servidor. Tente novamente mais tarde.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)