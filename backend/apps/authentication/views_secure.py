"""
Secure authentication views with enhanced security measures
"""
import secrets
import hashlib
import logging
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django_ratelimit.decorators import ratelimit

from .models import EmailVerification, PasswordReset
from .serializers import (
    ChangePasswordSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .utils import (
    verify_totp_token,
    verify_backup_code,
)
from .security.rate_limiting import ProgressiveRateLimiter, get_client_ip
from .security.audit_logger import SecurityAuditLogger

logger = logging.getLogger(__name__)
User = get_user_model()

# Initialize security components
rate_limiter = ProgressiveRateLimiter('secure_auth', base_delay=2, max_delay=1800)
audit_logger = SecurityAuditLogger()


class SecureTokenMixin:
    """
    Mixin to handle secure token operations with httpOnly cookies
    """
    
    def set_auth_cookies(self, response, user, access_token=None, refresh_token=None):
        """
        Set secure httpOnly cookies for JWT tokens
        """
        if not access_token or not refresh_token:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
        
        # Cookie settings from Django settings
        from django.conf import settings
        
        access_cookie_name = getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token')
        refresh_cookie_name = getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'refresh_token')
        cookie_path = getattr(settings, 'JWT_COOKIE_PATH', '/')
        cookie_domain = getattr(settings, 'JWT_COOKIE_DOMAIN', None)
        cookie_secure = getattr(settings, 'JWT_COOKIE_SECURE', not settings.DEBUG)
        cookie_samesite = getattr(settings, 'JWT_COOKIE_SAMESITE', 'Lax')
        
        # Access token lifetime (30 minutes)
        access_max_age = 30 * 60
        # Refresh token lifetime (3 days)
        refresh_max_age = 3 * 24 * 60 * 60
        
        # Set access token cookie
        response.set_cookie(
            access_cookie_name,
            access_token,
            max_age=access_max_age,
            path=cookie_path,
            domain=cookie_domain,
            secure=cookie_secure,
            httponly=True,  # Always httpOnly for security
            samesite=cookie_samesite
        )
        
        # Set refresh token cookie
        response.set_cookie(
            refresh_cookie_name,
            refresh_token,
            max_age=refresh_max_age,
            path=cookie_path,
            domain=cookie_domain,
            secure=cookie_secure,
            httponly=True,  # Always httpOnly for security
            samesite=cookie_samesite
        )
        
        logger.info(f"Set secure auth cookies for user {user.email}")
    
    def clear_auth_cookies(self, response):
        """
        Clear authentication cookies
        """
        from django.conf import settings
        
        access_cookie_name = getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token')
        refresh_cookie_name = getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'refresh_token')
        cookie_path = getattr(settings, 'JWT_COOKIE_PATH', '/')
        cookie_domain = getattr(settings, 'JWT_COOKIE_DOMAIN', None)
        
        response.delete_cookie(
            access_cookie_name,
            path=cookie_path,
            domain=cookie_domain
        )
        response.delete_cookie(
            refresh_cookie_name,
            path=cookie_path,
            domain=cookie_domain
        )
        
        logger.info("Cleared auth cookies")


class SecureRequestSigningMixin:
    """
    Mixin to handle request signing for critical operations
    """
    
    def generate_request_signature(self, request_data, timestamp, nonce):
        """
        Generate request signature for critical operations
        """
        from django.conf import settings
        
        # Get signing key from settings
        signing_key = getattr(settings, 'REQUEST_SIGNING_KEY', settings.SECRET_KEY)
        
        # Create signature payload
        payload = f"{request_data}|{timestamp}|{nonce}"
        
        # Generate HMAC signature
        signature = hashlib.pbkdf2_hmac(
            'sha256',
            payload.encode(),
            signing_key.encode(),
            100000  # iterations
        ).hex()
        
        return signature
    
    def verify_request_signature(self, request):
        """
        Verify request signature for critical operations
        """
        signature = request.META.get('HTTP_X_REQUEST_SIGNATURE')
        timestamp = request.META.get('HTTP_X_REQUEST_TIMESTAMP')
        nonce = request.META.get('HTTP_X_REQUEST_NONCE')
        
        if not all([signature, timestamp, nonce]):
            return False, "Missing signature headers"
        
        # Check timestamp (must be within 5 minutes)
        try:
            request_time = datetime.fromtimestamp(int(timestamp))
            if abs((timezone.now() - request_time).total_seconds()) > 300:
                return False, "Request timestamp expired"
        except (ValueError, TypeError):
            return False, "Invalid timestamp"
        
        # Verify signature
        expected_signature = self.generate_request_signature(
            request.body.decode() if request.body else "",
            timestamp,
            nonce
        )
        
        if signature != expected_signature:
            return False, "Invalid signature"
        
        return True, "Valid signature"


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST'), name='dispatch')
class SecureLoginView(APIView, SecureTokenMixin):
    """
    Secure login view with enhanced security measures
    """
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer
    
    def post(self, request):
        client_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check rate limiting
        delay, reason = rate_limiter.get_delay(client_ip)
        if delay > 0:
            audit_logger.log_failed_login(
                None, client_ip, user_agent, 
                f"Rate limited: {reason}"
            )
            return Response({
                'error': 'Too many login attempts. Please try again later.',
                'retry_after': delay
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer = self.serializer_class(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            
            # Update last login
            user.last_login = timezone.now()
            user.last_login_ip = client_ip
            user.save(update_fields=['last_login', 'last_login_ip'])
            
            # Check if 2FA is enabled
            if user.is_two_factor_enabled:
                two_fa_code = request.data.get('two_fa_code')
                if not two_fa_code:
                    # Record partial login attempt
                    rate_limiter.record_attempt(client_ip, success=False)
                    audit_logger.log_2fa_required(user, client_ip, user_agent)
                    
                    return Response({
                        'requires_2fa': True,
                        'message': 'Código de autenticação de dois fatores necessário'
                    }, status=status.HTTP_200_OK)
                
                # Verify 2FA code
                if not verify_totp_token(user.two_factor_secret, two_fa_code):
                    # Try backup code
                    if not verify_backup_code(user, two_fa_code):
                        rate_limiter.record_attempt(client_ip, success=False)
                        audit_logger.log_failed_2fa(user, client_ip, user_agent, two_fa_code[:2] + '****')
                        
                        return Response({
                            'error': 'Código de autenticação inválido'
                        }, status=status.HTTP_400_BAD_REQUEST)
            
            # Successful login
            rate_limiter.record_attempt(client_ip, success=True)
            audit_logger.log_successful_login(user, client_ip, user_agent)
            
            # Create response with user data (no tokens in body)
            response_data = {
                'user': UserSerializer(user).data,
                'message': 'Login realizado com sucesso'
            }
            
            response = Response(response_data, status=status.HTTP_200_OK)
            
            # Set secure httpOnly cookies
            self.set_auth_cookies(response, user)
            
            return response
            
        except Exception as e:
            # Record failed attempt
            rate_limiter.record_attempt(client_ip, success=False)
            
            # Try to get email from request for logging
            email = request.data.get('email', 'unknown')
            audit_logger.log_failed_login(email, client_ip, user_agent, str(e))
            
            return Response({
                'error': 'Credenciais inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)


@method_decorator(csrf_protect, name='dispatch')
class SecureLogoutView(APIView, SecureTokenMixin):
    """
    Secure logout view with CSRF protection
    """
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        user = request.user
        client_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Log logout
        audit_logger.log_logout(user, client_ip, user_agent)
        
        response = Response({
            'message': 'Logout realizado com sucesso'
        }, status=status.HTTP_200_OK)
        
        # Clear auth cookies
        self.clear_auth_cookies(response)
        
        return response


@method_decorator(csrf_protect, name='dispatch')
class SecureChangePasswordView(generics.UpdateAPIView, SecureRequestSigningMixin):
    """
    Secure password change view with request signing
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer
    
    def update(self, request, *args, **kwargs):
        client_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Verify request signature for critical operation
        is_valid, message = self.verify_request_signature(request)
        if not is_valid:
            audit_logger.log_security_event(
                'INVALID_REQUEST_SIGNATURE',
                request.user,
                client_ip,
                user_agent,
                {'operation': 'password_change', 'error': message}
            )
            return Response({
                'error': 'Invalid request signature'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set new password
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Log password change
        audit_logger.log_password_change(user, client_ip, user_agent)
        
        return Response({'message': 'Senha alterada com sucesso'})


class SecureTokenRefreshView(APIView, SecureTokenMixin):
    """
    Secure token refresh view using httpOnly cookies
    """
    permission_classes = (AllowAny,)
    
    def post(self, request):
        from django.conf import settings
        
        refresh_cookie_name = getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'refresh_token')
        refresh_token = request.COOKIES.get(refresh_cookie_name)
        
        if not refresh_token:
            return Response({
                'error': 'Refresh token not found'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = refresh.access_token
            
            # Get user for the new token
            user_id = new_access_token.payload.get('user_id')
            user = User.objects.get(id=user_id)
            
            response_data = {
                'message': 'Token refreshed successfully',
                'user': UserSerializer(user).data
            }
            
            response = Response(response_data, status=status.HTTP_200_OK)
            
            # Set new cookies (refresh token may be rotated)
            self.set_auth_cookies(response, user, str(new_access_token), str(refresh))
            
            # Log token refresh
            client_ip = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            audit_logger.log_token_refresh(user, client_ip, user_agent)
            
            return response
            
        except Exception as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            
            response = Response({
                'error': 'Invalid refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Clear cookies on failure
            self.clear_auth_cookies(response)
            
            return response


# Enhanced registration view with security measures
@method_decorator(ratelimit(key='ip', rate='5/m', method='POST'), name='dispatch')
class SecureRegisterView(generics.CreateAPIView, SecureTokenMixin):
    """
    Secure registration view with enhanced validation
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        client_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check rate limiting
        delay, reason = rate_limiter.get_delay(f"register_{client_ip}")
        if delay > 0:
            audit_logger.log_security_event(
                'REGISTRATION_RATE_LIMITED',
                None,
                client_ip, 
                user_agent,
                {'reason': reason}
            )
            return Response({
                'error': 'Too many registration attempts. Please try again later.',
                'retry_after': delay
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            
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
            
            # Log successful registration
            audit_logger.log_user_registration(user, client_ip, user_agent)
            rate_limiter.record_attempt(f"register_{client_ip}", success=True)
            
            response_data = {
                'user': UserSerializer(user).data,
                'message': 'Cadastro realizado com sucesso. Por favor, verifique seu e-mail para confirmar sua conta.'
            }
            
            response = Response(response_data, status=status.HTTP_201_CREATED)
            
            # Set secure httpOnly cookies for immediate login
            self.set_auth_cookies(response, user)
            
            return response
            
        except Exception as e:
            rate_limiter.record_attempt(f"register_{client_ip}", success=False)
            raise