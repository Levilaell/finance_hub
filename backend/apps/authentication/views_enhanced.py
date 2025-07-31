"""
Enhanced authentication views with comprehensive security features
"""
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
import pyotp
import qrcode
import io
import base64
import secrets
import logging

# Internal imports
from .models_enhanced import (
    EnhancedUser, EmailVerificationToken, PasswordResetToken, 
    OAuth2Connection, RememberMeToken
)
from .security.rate_limiting import (
    ProgressiveRateLimiter, IPBasedRateLimiter, AccountLockoutManager, get_client_ip
)
from .security.anomaly_detection import AnomalyDetector
from .security.password_policies import password_validator, password_generator
from .security.session_management import (
    device_manager, session_manager, remember_me_manager
)
from .security.audit_logger import audit_logger
from .oauth.providers import oauth_manager
from .serializers_enhanced import (
    LoginSerializer, RegisterSerializer, PasswordResetSerializer,
    PasswordChangeSerializer, TwoFactorSetupSerializer
)

logger = logging.getLogger(__name__)


class SecurityEnhancedAPIView(APIView):
    """Base class for security-enhanced API views"""
    
    def __init__(self):
        super().__init__()
        self.rate_limiter = ProgressiveRateLimiter()
        self.ip_limiter = IPBasedRateLimiter()
        self.anomaly_detector = AnomalyDetector()
        self.lockout_manager = AccountLockoutManager()
    
    def get_client_identifier(self, request):
        """Get unique client identifier for rate limiting"""
        import hashlib
        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        raw = f"{ip}:{user_agent}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
    
    def check_rate_limits(self, request, action='auth') -> tuple:
        """Check all rate limits"""
        identifier = self.get_client_identifier(request)
        ip_address = get_client_ip(request)
        
        # Check progressive rate limiting
        delay, reason = self.rate_limiter.get_delay(identifier)
        if delay > 0:
            return False, {'error': reason, 'retry_after': delay}
        
        # Check IP-based rate limiting
        allowed, retry_after = self.ip_limiter.check_rate_limit(ip_address, action)
        if not allowed:
            return False, {'error': f'Too many requests. Try again in {retry_after} seconds.', 'retry_after': retry_after}
        
        return True, {}
    
    def record_attempt(self, request, success, action='auth'):
        """Record authentication attempt"""
        identifier = self.get_client_identifier(request)
        ip_address = get_client_ip(request)
        
        self.rate_limiter.record_attempt(identifier, success)
        self.ip_limiter.record_request(ip_address, action)


class EnhancedLoginView(SecurityEnhancedAPIView):
    """Enhanced login with comprehensive security features"""
    
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True))
    def post(self, request):
        try:
            # Rate limit check
            allowed, error_response = self.check_rate_limits(request, 'login')
            if not allowed:
                return Response(error_response, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Validate input
            serializer = LoginSerializer(data=request.data)
            if not serializer.is_valid():
                self.record_attempt(request, False, 'login')
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            remember_me = serializer.validated_data.get('remember_me', False)
            device_name = serializer.validated_data.get('device_name', '')
            
            # Check if user exists
            try:
                user = EnhancedUser.objects.get(email=email)
            except EnhancedUser.DoesNotExist:
                self.record_attempt(request, False, 'login')
                audit_logger.log_login_failure(
                    None, request, 'User not found', {'email': email}
                )
                return Response(
                    {'error': 'Invalid credentials'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Check account lockout
            if user.is_account_locked():
                self.record_attempt(request, False, 'login')
                audit_logger.log_login_failure(
                    user, request, 'Account locked', {'locked_until': user.locked_until}
                )
                return Response(
                    {'error': 'Account is locked. Please try again later.'}, 
                    status=status.HTTP_423_LOCKED
                )
            
            # Authenticate user
            if not user.check_password(password):
                user.increment_failed_login()
                self.record_attempt(request, False, 'login')
                
                # Check if account should be locked
                if self.lockout_manager.should_lock_account(user):
                    self.lockout_manager.lock_account(user)
                    audit_logger.log_account_locked(user, request, 'Too many failed attempts')
                
                audit_logger.log_login_failure(user, request, 'Invalid password')
                return Response(
                    {'error': 'Invalid credentials'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Check if email is verified
            if not user.is_email_verified:
                return Response(
                    {'error': 'Please verify your email before logging in.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Perform anomaly detection
            anomaly_result = self.anomaly_detector.analyze_login_attempt(user, request, True)
            risk_score = anomaly_result['risk_score']
            
            # Reset failed login attempts on successful authentication
            user.reset_failed_login()
            
            # Device and location tracking
            device_info = device_manager.get_device_info(request)
            is_trusted_device = device_manager.is_device_trusted(user, device_info['device_id'])
            
            # Check if 2FA is required
            requires_2fa = (
                user.is_two_factor_enabled or 
                risk_score > 0.5 or 
                not is_trusted_device
            )
            
            if requires_2fa and user.is_two_factor_enabled:
                # Generate temporary token for 2FA verification
                temp_token = self._generate_2fa_temp_token(user)
                
                return Response({
                    'requires_2fa': True,
                    'temp_token': temp_token,
                    'risk_score': risk_score,
                    'backup_codes_available': len(user.backup_codes or []) > 0,
                }, status=status.HTTP_200_OK)
            
            # Complete login
            return self._complete_login(user, request, device_info, remember_me, device_name, anomaly_result)
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An error occurred during login'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_2fa_temp_token(self, user):
        """Generate temporary token for 2FA verification"""
        temp_token = secrets.token_urlsafe(32)
        cache.set(f"2fa_temp:{temp_token}", user.id, 300)  # 5 minutes
        return temp_token
    
    def _complete_login(self, user, request, device_info, remember_me, device_name, anomaly_result):
        """Complete the login process"""
        try:
            with transaction.atomic():
                # Update user login info
                user.last_login = timezone.now()
                user.last_login_ip = get_client_ip(request)
                user.last_login_device = device_manager.get_device_name(device_info)
                
                # Update location if available
                if anomaly_result.get('location'):
                    location = anomaly_result['location']
                    user.last_login_location = f"{location.get('city', '')}, {location.get('country', '')}"
                
                user.save()
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                
                # Create session
                session_key = session_manager.create_session(user, request, remember_me)
                
                # Create remember me token if requested
                remember_token = None
                if remember_me:
                    remember_token = remember_me_manager.create_remember_token(user, request)
                
                # Add device as trusted if requested
                trust_device = request.data.get('trust_device', False)
                if trust_device:
                    device_manager.add_trusted_device(user, device_info)
                    audit_logger.log_device_trusted(user, request, device_info)
                
                # Record successful attempt
                self.record_attempt(request, True, 'login')
                
                # Log successful login
                audit_logger.log_login_success(user, request, {
                    'device_info': device_info,
                    'remember_me': remember_me,
                    'trust_device': trust_device,
                    'risk_score': anomaly_result['risk_score'],
                    'anomalies': anomaly_result.get('anomalies', []),
                })
                
                response_data = {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_two_factor_enabled': user.is_two_factor_enabled,
                    },
                    'session_key': session_key,
                    'risk_score': anomaly_result['risk_score'],
                    'new_device': 'new_device' in anomaly_result.get('anomalies', []),
                    'new_location': 'new_location' in anomaly_result.get('anomalies', []),
                }
                
                if remember_token:
                    response_data['remember_token'] = remember_token
                
                return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Login completion error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An error occurred completing login'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TwoFactorVerifyView(SecurityEnhancedAPIView):
    """2FA verification endpoint"""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            temp_token = request.data.get('temp_token')
            totp_code = request.data.get('totp_code')
            backup_code = request.data.get('backup_code')
            remember_me = request.data.get('remember_me', False)
            trust_device = request.data.get('trust_device', False)
            
            if not temp_token:
                return Response({'error': 'Temporary token required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user from temp token
            user_id = cache.get(f"2fa_temp:{temp_token}")
            if not user_id:
                return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                user = EnhancedUser.objects.get(id=user_id)
            except EnhancedUser.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Verify 2FA code
            verified = False
            used_backup = False
            
            if totp_code:
                # Verify TOTP code
                totp = pyotp.TOTP(user.two_factor_secret)
                if totp.verify(totp_code, valid_window=1):
                    verified = True
            elif backup_code:
                # Verify backup code
                backup_codes = user.backup_codes or []
                if backup_code in backup_codes:
                    verified = True
                    used_backup = True
                    # Remove used backup code
                    backup_codes.remove(backup_code)
                    user.backup_codes = backup_codes
                    user.save()
            
            if not verified:
                audit_logger.log_2fa_failure(user, request, 'Invalid 2FA code')
                return Response({'error': 'Invalid 2FA code'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Clear temp token
            cache.delete(f"2fa_temp:{temp_token}")
            
            # Complete login
            device_info = device_manager.get_device_info(request)
            anomaly_result = self.anomaly_detector.analyze_login_attempt(user, request, True)
            
            # Log successful 2FA
            audit_logger.log_2fa_success(user, request, {
                'used_backup_code': used_backup,
                'backup_codes_remaining': len(user.backup_codes or [])
            })
            
            return self._complete_2fa_login(user, request, device_info, remember_me, trust_device, anomaly_result)
            
        except Exception as e:
            logger.error(f"2FA verification error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An error occurred during 2FA verification'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _complete_2fa_login(self, user, request, device_info, remember_me, trust_device, anomaly_result):
        """Complete login after 2FA verification"""
        try:
            with transaction.atomic():
                # Update user info
                user.last_login = timezone.now()
                user.last_login_ip = get_client_ip(request)
                user.last_login_device = device_manager.get_device_name(device_info)
                user.save()
                
                # Generate tokens
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                
                # Create session
                session_key = session_manager.create_session(user, request, remember_me)
                
                # Create remember me token
                remember_token = None
                if remember_me:
                    remember_token = remember_me_manager.create_remember_token(user, request)
                
                # Trust device if requested
                if trust_device:
                    device_manager.add_trusted_device(user, device_info)
                    audit_logger.log_device_trusted(user, request, device_info)
                
                # Log successful login
                audit_logger.log_login_success(user, request, {
                    '2fa_verified': True,
                    'device_info': device_info,
                    'trust_device': trust_device,
                })
                
                response_data = {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_two_factor_enabled': user.is_two_factor_enabled,
                    },
                    'session_key': session_key,
                    'backup_codes_remaining': len(user.backup_codes or []),
                }
                
                if remember_token:
                    response_data['remember_token'] = remember_token
                
                return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"2FA login completion error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An error occurred completing 2FA login'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EnhancedRegisterView(SecurityEnhancedAPIView):
    """Enhanced user registration with security features"""
    
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='3/m', method='POST', block=True))
    def post(self, request):
        try:
            # Rate limit check
            allowed, error_response = self.check_rate_limits(request, 'register')
            if not allowed:
                return Response(error_response, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            serializer = RegisterSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            first_name = serializer.validated_data['first_name']
            last_name = serializer.validated_data['last_name']
            
            # Check if user already exists
            if EnhancedUser.objects.filter(email=email).exists():
                return Response(
                    {'error': 'User with this email already exists'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate password
            validation_result = password_validator.validate_password(password)
            if not validation_result['valid']:
                return Response({
                    'error': 'Password does not meet security requirements',
                    'details': validation_result['recommendations']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create user
            with transaction.atomic():
                # Generate username from email
                username = email.split('@')[0]
                counter = 1
                original_username = username
                while EnhancedUser.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = EnhancedUser.objects.create(
                    email=email,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    password=make_password(password),
                    is_active=True,
                    is_email_verified=False,
                    password_changed_at=timezone.now()
                )
                
                # Add password to history
                user.add_to_password_history(user.password)
                
                # Create email verification token
                verification_token = EmailVerificationToken(user=user)
                token = verification_token.generate_token()
                verification_token.save()
                
                # Log registration
                audit_logger.log_authentication_event(
                    'user_registered',
                    user=user,
                    request=request,
                    success=True,
                    additional_data={
                        'password_strength': validation_result['strength']['strength'],
                        'password_score': validation_result['strength']['score']
                    }
                )
                
                # TODO: Send verification email
                # send_verification_email(user, token)
                
                return Response({
                    'message': 'Registration successful. Please check your email for verification.',
                    'user_id': user.id,
                    'verification_required': True
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Registration error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An error occurred during registration'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EnhancedLogoutView(SecurityEnhancedAPIView):
    """Enhanced logout with session cleanup"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            
            # Get refresh token
            refresh_token = request.data.get('refresh_token')
            
            # Invalidate JWT token
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except TokenError:
                    pass
            
            # Invalidate session
            session_key = request.data.get('session_key')
            if session_key:
                session_manager.invalidate_session(session_key, user)
            
            # Invalidate remember me token if provided
            remember_token = request.data.get('remember_token')
            if remember_token:
                try:
                    user_from_token, valid = remember_me_manager.validate_remember_token(remember_token)
                    if valid and user_from_token == user:
                        device_info = device_manager.get_device_info(request)
                        remember_me_manager.invalidate_remember_token(user, device_info['device_id'])
                except Exception:
                    pass
            
            # Log logout
            audit_logger.log_logout(user, request)
            
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An error occurred during logout'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LogoutAllSessionsView(SecurityEnhancedAPIView):
    """Logout from all sessions"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            
            # Invalidate all sessions
            session_count = session_manager.invalidate_all_sessions(user)
            
            # Invalidate all remember me tokens
            remember_count = remember_me_manager.invalidate_remember_token(user)
            
            # Log logout all
            audit_logger.log_authentication_event(
                'logout_all_sessions',
                user=user,
                request=request,
                success=True,
                additional_data={
                    'sessions_invalidated': session_count,
                    'remember_tokens_invalidated': remember_count
                }
            )
            
            return Response({
                'message': f'Successfully logged out from {session_count} sessions',
                'sessions_invalidated': session_count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Logout all error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An error occurred during logout'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetRequestView(SecurityEnhancedAPIView):
    """Request password reset"""
    
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='3/h', method='POST', block=True))
    def post(self, request):
        try:
            email = request.data.get('email')
            if not email:
                return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                user = EnhancedUser.objects.get(email=email)
                
                # Create password reset token
                reset_token = PasswordResetToken(user=user)
                token = reset_token.generate_token()
                reset_token.save()
                
                # Log password reset request
                audit_logger.log_password_reset_request(user, request)
                
                # TODO: Send password reset email
                # send_password_reset_email(user, token)
                
            except EnhancedUser.DoesNotExist:
                # Don't reveal if user exists or not
                pass
            
            return Response({
                'message': 'If an account with that email exists, a password reset link has been sent.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Password reset request error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An error occurred processing password reset request'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# OAuth2 Views
class OAuth2InitView(APIView):
    """Initiate OAuth2 flow"""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        provider_id = request.data.get('provider')
        
        if not provider_id:
            return Response({'error': 'Provider is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        auth_url, state = oauth_manager.initiate_oauth_flow(provider_id)
        
        if not auth_url:
            return Response({'error': 'Invalid provider'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Store state in session/cache for verification
        cache.set(f"oauth_state:{state}", provider_id, 600)  # 10 minutes
        
        return Response({
            'auth_url': auth_url,
            'state': state
        }, status=status.HTTP_200_OK)


class OAuth2CallbackView(SecurityEnhancedAPIView):
    """Handle OAuth2 callback"""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            code = request.data.get('code')
            state = request.data.get('state')
            
            if not code or not state:
                return Response({'error': 'Code and state are required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify state
            provider_id = cache.get(f"oauth_state:{state}")
            if not provider_id:
                return Response({'error': 'Invalid state'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Complete OAuth flow
            oauth_result = oauth_manager.complete_oauth_flow(provider_id, code, state)
            if not oauth_result:
                return Response({'error': 'OAuth authentication failed'}, status=status.HTTP_400_BAD_REQUEST)
            
            user_info = oauth_result['user_info']
            token_data = oauth_result['token_data']
            
            # Find or create user
            user = None
            created = False
            
            if user_info['email']:
                try:
                    user = EnhancedUser.objects.get(email=user_info['email'])
                except EnhancedUser.DoesNotExist:
                    # Create new user
                    username = user_info['email'].split('@')[0]
                    counter = 1
                    original_username = username
                    while EnhancedUser.objects.filter(username=username).exists():
                        username = f"{original_username}{counter}"
                        counter += 1
                    
                    user = EnhancedUser.objects.create(
                        email=user_info['email'],
                        username=username,
                        first_name=user_info.get('first_name', ''),
                        last_name=user_info.get('last_name', ''),
                        is_email_verified=user_info.get('email_verified', True),
                        is_active=True
                    )
                    created = True
            
            if not user:
                return Response({'error': 'Unable to create user account'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create or update OAuth connection
            OAuth2Connection.objects.update_or_create(
                user=user,
                provider_id=provider_id,
                provider_user_id=user_info['provider_user_id'],
                defaults={
                    'access_token_encrypted': token_data.get('access_token', ''),
                    'refresh_token_encrypted': token_data.get('refresh_token', ''),
                    'profile_data': user_info,
                    'last_used': timezone.now()
                }
            )
            
            # Complete login
            device_info = device_manager.get_device_info(request)
            anomaly_result = self.anomaly_detector.analyze_login_attempt(user, request, True)
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token_jwt = str(refresh)
            
            # Create session
            session_key = session_manager.create_session(user, request, False)
            
            # Log OAuth login
            audit_logger.log_oauth_login(
                user, request, provider_id, user_info['provider_user_id'],
                {'created_account': created, 'provider': oauth_result['provider_name']}
            )
            
            return Response({
                'access_token': access_token,
                'refresh_token': refresh_token_jwt,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_two_factor_enabled': user.is_two_factor_enabled,
                },
                'session_key': session_key,
                'created_account': created,
                'provider': oauth_result['provider_name']
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An error occurred during OAuth authentication'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )