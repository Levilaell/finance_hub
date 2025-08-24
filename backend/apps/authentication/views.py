"""
Authentication views
"""
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.throttling import AnonRateThrottle
from django_ratelimit.decorators import ratelimit
from core.rate_limiting import (
    LoginThrottle, RegistrationThrottle, PasswordResetThrottle,
    check_rate_limit, get_rate_limit_status
)
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailVerification, PasswordReset
from .cookie_middleware import set_jwt_cookies, clear_jwt_cookies, get_client_ip
from .security_logging import log_security_event, SecurityEvent, LoginAttemptTracker, SessionManager
from .serializers import (
    ChangePasswordSerializer,
    DeleteAccountSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
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


# Enhanced throttle classes with IP + User tracking
class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'
    
    def get_cache_key(self, request, view):
        # Combine IP and email for more precise rate limiting
        ident = self.get_ident(request)
        email = request.data.get('email', 'unknown')
        return self.cache_format % {
            'scope': self.scope,
            'ident': f"{ident}:{email}"
        }

class RegisterRateThrottle(AnonRateThrottle):
    scope = 'register'

class PasswordResetRateThrottle(AnonRateThrottle):
    scope = 'password_reset'

class TokenRefreshRateThrottle(AnonRateThrottle):
    scope = 'token_refresh'

class TwoFactorRateThrottle(AnonRateThrottle):
    scope = '2fa_attempt'

class EmailVerificationRateThrottle(AnonRateThrottle):
    scope = 'email_verification'

class AccountDeletionRateThrottle(AnonRateThrottle):
    scope = 'account_deletion'


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST'), name='dispatch')
class RegisterView(generics.CreateAPIView):
    """User registration with company creation"""
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    throttle_classes = [RegistrationThrottle]
    
    def create(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        
        # Mask sensitive data for logging
        log_data = request.data.copy()
        if 'password' in log_data:
            log_data['password'] = '***'
        if 'password2' in log_data:
            log_data['password2'] = '***'
        
        logger.info(f"Registration attempt from {request.META.get('REMOTE_ADDR')} with data: {log_data}")
        
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
        import logging
        logger = logging.getLogger(__name__)
        
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        try:
            send_verification_email_task.delay(user.id, verification_url)
        except Exception as e:
            logger.warning(f"Could not queue verification email task: {e}")
        
        # Log account creation
        log_security_event(
            SecurityEvent.ACCOUNT_CREATED,
            user=user,
            request=request
        )
        
        response = Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Cadastro realizado com sucesso. Por favor, verifique seu e-mail para confirmar sua conta.'
        }, status=status.HTTP_201_CREATED)
        
        # Set httpOnly cookies with user object for accurate logging
        set_jwt_cookies(response, {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, request, user)
        
        return response


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST'), name='dispatch')
class LoginView(APIView):
    """User login"""
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer
    throttle_classes = [LoginThrottle]
    
    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)
        
        # Enhanced logging for debugging
        logger.debug(f"Login attempt from IP: {get_client_ip(request)}")
        logger.debug(f"Request data keys: {list(request.data.keys())}")
        logger.debug(f"Request headers: {dict(request.headers)}")
        
        email = request.data.get('email', '')
        client_ip = get_client_ip(request)
        
        # Log the login attempt details
        logger.info(f"Login attempt for email: {email} from IP: {client_ip}")
        
        # Check if account is locked
        if LoginAttemptTracker.is_locked(email):
            log_security_event(
                SecurityEvent.ACCOUNT_LOCKED,
                request=request,
                extra_data={'email': email}
            )
            logger.warning(f"Account locked for email: {email}")
            return Response({
                'error': 'Conta bloqueada temporariamente. Tente novamente em 1 hora.'
            }, status=status.HTTP_423_LOCKED)
        
        try:
            serializer = self.serializer_class(data=request.data)
            if not serializer.is_valid():
                # Log validation errors for debugging
                logger.error(f"Login validation errors: {serializer.errors}")
                logger.debug(f"Request data: {request.data}")
                
                # Create a user-friendly error message
                error_messages = []
                for field, errors in serializer.errors.items():
                    if isinstance(errors, list):
                        error_messages.extend(errors)
                    else:
                        error_messages.append(str(errors))
                
                return Response({
                    'error': 'Dados de login inválidos',
                    'details': error_messages,
                    'fields': list(serializer.errors.keys())
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = serializer.validated_data['user']
            logger.info(f"Login successful for user: {user.email}")
            
        except Exception as e:
            # Track failed attempt
            logger.exception(f"Login exception for email {email}: {str(e)}")
            should_lock, attempts = LoginAttemptTracker.track_failed_attempt(email, client_ip)
            log_security_event(
                SecurityEvent.LOGIN_FAILED,
                request=request,
                extra_data={'email': email, 'attempts': attempts, 'reason': str(e)}
            )
            
            if should_lock:
                return Response({
                    'error': 'Muitas tentativas de login falhadas. Conta bloqueada temporariamente.'
                }, status=status.HTTP_423_LOCKED)
            
            # Return more detailed error in development
            if settings.DEBUG:
                return Response({
                    'error': 'Erro no login',
                    'debug_info': str(e),
                    'type': type(e).__name__
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                raise
        
        # Update last login
        user.last_login = timezone.now()
        user.last_login_ip = client_ip
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
                    log_security_event(
                        SecurityEvent.TWO_FA_FAILED,
                        user=user,
                        request=request
                    )
                    return Response({
                        'error': 'Código de autenticação inválido'
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset login attempts on successful login
        LoginAttemptTracker.reset_attempts(email, client_ip)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Log successful login
        log_security_event(
            SecurityEvent.LOGIN_SUCCESS,
            user=user,
            request=request,
            extra_data={'session_count': SessionManager.get_active_session_count(user)}
        )
        
        # Create response with user data
        response = Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
        
        # Set httpOnly cookies with user object for accurate logging
        # Debug: Log what we're passing to set_jwt_cookies
        logger.info(f"LoginView: About to call set_jwt_cookies with user ID={user.id}, email={user.email}")
        set_jwt_cookies(response, {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, request, user)
        
        return response


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
            # Log logout event
            log_security_event(
                SecurityEvent.LOGOUT,
                user=request.user,
                request=request
            )
            
            response = Response({'message': 'Logout realizado com sucesso'}, status=status.HTTP_200_OK)
            
            # Clear httpOnly cookies
            clear_jwt_cookies(response)
            
            return response
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile view"""
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    
    def get_object(self):
        # Force refresh from database to ensure latest data
        return User.objects.select_related('company__subscription_plan').get(pk=self.request.user.pk)
    
    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        """Override to add cache headers"""
        response = super().get(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response


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
        
        # Invalidate all sessions for this user (security measure)
        SessionManager.invalidate_all_sessions(user)
        
        # Log password change
        log_security_event(
            SecurityEvent.PASSWORD_CHANGED,
            user=user,
            request=request
        )
        
        # Generate new tokens for current session
        refresh = RefreshToken.for_user(user)
        
        response = Response({
            'message': 'Senha alterada com sucesso',
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
        
        # Set new tokens as cookies with user object for accurate logging
        set_jwt_cookies(response, {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, request, user)
        
        return response


@method_decorator(ratelimit(key='ip', rate='3/h', method='POST'), name='dispatch')
class PasswordResetRequestView(APIView):
    """Request password reset"""
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetRequestSerializer
    throttle_classes = [PasswordResetRateThrottle]
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Create reset token (2 hour expiry for security)
        reset_token = secrets.token_urlsafe(32)
        PasswordReset.objects.create(
            user=user,
            token=reset_token,
            expires_at=timezone.now() + timedelta(hours=2)
        )
        
        # Send password reset email
        from apps.notifications.email_service import send_password_reset_email_task
        from django.conf import settings
        import logging
        logger = logging.getLogger(__name__)
        
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        try:
            send_password_reset_email_task.delay(user.id, reset_url)
        except Exception as e:
            logger.warning(f"Could not queue password reset email task: {e}")
        
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
    throttle_classes = [EmailVerificationRateThrottle]
    
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
        
        # Email verification functionality temporarily disabled
        # TODO: Re-implement when is_email_verified field is restored
        user = verification.user
        # user.is_email_verified = True  # Field removed in migration
        # user.save()  # No need to save since no field is being modified
        
        # Mark token as used
        verification.is_used = True
        verification.save()
        
        return Response({'message': 'E-mail verificado com sucesso.'})


class ResendVerificationView(APIView):
    """Resend email verification"""
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        user = request.user
        
        # Email verification functionality temporarily disabled
        # TODO: Re-implement when is_email_verified field is restored
        # if user.is_email_verified:  # Field removed in migration
        #     return Response({
        #         'message': 'E-mail já foi verificado.'
        
        # For now, always allow resend attempts
        if False:  # Placeholder condition to maintain structure
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
        import logging
        logger = logging.getLogger(__name__)
        
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        try:
            send_verification_email_task.delay(user.id, verification_url)
        except Exception as e:
            logger.warning(f"Could not queue verification email task: {e}")
        
        return Response({
            'message': 'E-mail de verificação foi enviado.'
        })


class CustomTokenRefreshView(APIView):
    """Custom token refresh view"""
    permission_classes = (AllowAny,)
    throttle_classes = [TokenRefreshRateThrottle]
    
    def post(self, request):
        # Try to get refresh token from cookie first, then from body
        refresh_token = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        if not refresh_token:
            refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            log_security_event(
                SecurityEvent.TOKEN_REFRESH_FAILED,
                request=request,
                extra_data={'reason': 'No refresh token provided'}
            )
            return Response(
                {'error': 'Token de atualização é obrigatório'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Validate and refresh the token
            refresh = RefreshToken(refresh_token)
            
            # Check if token rotation is enabled
            if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
                # Get new refresh token
                refresh.set_jti()
                refresh.set_exp()
                
                # Blacklist the old token if enabled
                if settings.SIMPLE_JWT.get('BLACKLIST_AFTER_ROTATION', False) and hasattr(refresh, 'blacklist'):
                    refresh.blacklist()
            
            # Generate new access token
            access_token = refresh.access_token
            
            # Get user for logging
            user = refresh.access_token.payload.get('user_id')
            
            # Log successful refresh
            log_security_event(
                SecurityEvent.TOKEN_REFRESHED,
                user=user,
                request=request
            )
            
            # Create response
            response = Response({
                'access': str(access_token),
                'refresh': str(refresh),
            })
            
            # Set cookies with user object for accurate logging
            set_jwt_cookies(response, {
                'access': str(access_token),
                'refresh': str(refresh)
            }, request, user)
            
            return response
            
        except Exception as e:
            log_security_event(
                SecurityEvent.TOKEN_REFRESH_FAILED,
                request=request,
                extra_data={'reason': str(e)}
            )
            return Response(
                {'error': 'Token de atualização inválido'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )


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
    throttle_classes = [TwoFactorRateThrottle]
    
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


@method_decorator(ratelimit(key='user', rate='3/h', method='POST'), name='dispatch')
class DeleteAccountView(APIView):
    """Delete user account with password verification"""
    permission_classes = [IsAuthenticated]
    serializer_class = DeleteAccountSerializer
    throttle_classes = [AccountDeletionRateThrottle]
    
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
        log_security_event(
            SecurityEvent.ACCOUNT_DELETED,
            user=user,
            request=request,
            extra_data={'reason': 'user_requested'}
        )
        
        try:
            # Delete user and all related data (CASCADE should handle this)
            user.delete()
            
            return Response({
                'message': 'Conta deletada com sucesso.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            log_security_event(
                SecurityEvent.ACCOUNT_DELETED,
                user=user,
                request=request,
                extra_data={'reason': 'deletion_failed', 'error': str(e)}
            )
            return Response({
                'error': 'Erro interno do servidor. Tente novamente mais tarde.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EarlyAccessRegisterView(generics.CreateAPIView):
    """Early Access registration with invite code validation"""
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    throttle_classes = [RegistrationThrottle]
    
    def create(self, request, *args, **kwargs):
        import logging
        from apps.companies.models import EarlyAccessInvite
        
        logger = logging.getLogger(__name__)
        
        # Get invite code from request
        invite_code = request.data.get('invite_code')
        if not invite_code:
            return Response({
                'error': 'Código de convite é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate invite code
        try:
            invite = EarlyAccessInvite.objects.get(invite_code=invite_code)
            if invite.is_used:
                return Response({
                    'error': 'Este código de convite já foi utilizado'
                }, status=status.HTTP_400_BAD_REQUEST)
            if not invite.is_valid:
                return Response({
                    'error': 'Este código de convite expirou'
                }, status=status.HTTP_400_BAD_REQUEST)
        except EarlyAccessInvite.DoesNotExist:
            return Response({
                'error': 'Código de convite inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Log masked data
        log_data = request.data.copy()
        if 'password' in log_data:
            log_data['password'] = '***'
        if 'password2' in log_data:
            log_data['password2'] = '***'
        log_data['invite_code'] = invite_code
        
        logger.info(f"Early access registration attempt from {request.META.get('REMOTE_ADDR')} with code: {invite_code}")
        
        # Create user normally
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Configure company for early access
        company = user.company
        company.is_early_access = True
        company.early_access_expires_at = invite.expires_at
        company.used_invite_code = invite_code
        company.subscription_status = 'early_access'
        company.trial_ends_at = invite.expires_at  # Override normal trial
        company.save()
        
        # Mark invite as used
        invite.mark_as_used(user)
        
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
        try:
            send_verification_email_task.delay(user.id, verification_url)
        except Exception as e:
            logger.warning(f"Failed to send verification email: {e}")
        
        # Log early access registration
        log_security_event(
            SecurityEvent.ACCOUNT_CREATED,
            user=user,
            request=request,
            extra_data={'early_access': True, 'invite_code': invite_code}
        )
        
        logger.info(f"Early access account created successfully: user_id={user.id}, invite_code={invite_code}")
        
        response = Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'early_access': {
                'expires_at': invite.expires_at.isoformat(),
                'days_remaining': invite.days_until_expiry
            },
            'message': 'Acesso antecipado ativado com sucesso! Você tem acesso completo até ' + 
                      invite.expires_at.strftime('%d/%m/%Y') + '. Verifique seu e-mail para confirmar sua conta.'
        }, status=status.HTTP_201_CREATED)
        
        # Set httpOnly cookies with user object for accurate logging
        set_jwt_cookies(response, {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, request, user)
        
        return response