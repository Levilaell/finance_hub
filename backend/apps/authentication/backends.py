"""
Enhanced authentication backends with security features
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
import logging

from .security.rate_limiting import ProgressiveRateLimiter
from .security.anomaly_detection import AuthenticationAnomalyDetector
from .security.audit_logger import SecurityAuditLogger

logger = logging.getLogger(__name__)
User = get_user_model()


class EnhancedAuthenticationBackend(ModelBackend):
    """
    Enhanced authentication backend with security features:
    - Rate limiting
    - Anomaly detection
    - Security audit logging
    - Account lockout protection
    """
    
    def __init__(self):
        self.rate_limiter = ProgressiveRateLimiter('auth_login')
        self.anomaly_detector = AuthenticationAnomalyDetector()
        self.audit_logger = SecurityAuditLogger()
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Enhanced authentication with security controls
        """
        if username is None or password is None:
            return None
        
        # Get client information
        client_ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        
        # Check rate limiting first
        delay, reason = self.rate_limiter.get_delay(client_ip)
        if delay > 0:
            self.audit_logger.log_security_event(
                event_type='rate_limit_exceeded',
                ip_address=client_ip,
                user_agent=user_agent,
                data={'delay': delay, 'reason': reason},
                severity='medium'
            )
            logger.warning(f"Rate limit exceeded for IP {client_ip}: {reason}")
            return None
        
        try:
            # Get user by email (username field)
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            # Record failed attempt for rate limiting
            self.rate_limiter.record_attempt(client_ip, success=False)
            
            # Log failed login attempt
            self.audit_logger.log_authentication_attempt(
                user=None,
                success=False,
                ip_address=client_ip,
                user_agent=user_agent,
                error_message='User not found'
            )
            
            return None
        
        # Check if account is locked
        if hasattr(user, 'is_account_locked') and user.is_account_locked():
            self.audit_logger.log_authentication_attempt(
                user=user,
                success=False,
                ip_address=client_ip,
                user_agent=user_agent,
                error_message='Account locked'
            )
            return None
        
        # Check password
        if not user.check_password(password):
            # Record failed login attempt
            if hasattr(user, 'increment_failed_login'):
                user.increment_failed_login()
            
            # Record rate limiting attempt
            self.rate_limiter.record_attempt(client_ip, success=False)
            
            # Log failed authentication
            self.audit_logger.log_authentication_attempt(
                user=user,
                success=False,
                ip_address=client_ip,
                user_agent=user_agent,
                error_message='Invalid password'
            )
            
            # Run anomaly detection
            if request:
                anomaly_score = self.anomaly_detector.analyze_login_attempt(
                    user=user,
                    request=request,
                    success=False
                )
                
                if anomaly_score > 0.7:  # High anomaly score
                    self.audit_logger.log_security_event(
                        event_type='suspicious_login',
                        user=user,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        data={'anomaly_score': anomaly_score},
                        severity='high'
                    )
            
            return None
        
        # Successful authentication
        if hasattr(user, 'reset_failed_login'):
            user.reset_failed_login()
        
        # Reset rate limiting
        self.rate_limiter.record_attempt(client_ip, success=True)
        
        # Update last login information
        user.last_login = timezone.now()
        if hasattr(user, 'last_login_ip'):
            user.last_login_ip = client_ip
        user.save(update_fields=['last_login', 'last_login_ip'])
        
        # Log successful authentication
        self.audit_logger.log_authentication_attempt(
            user=user,
            success=True,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Run anomaly detection for successful login
        if request:
            anomaly_score = self.anomaly_detector.analyze_login_attempt(
                user=user,
                request=request,
                success=True
            )
            
            if anomaly_score > 0.5:  # Medium anomaly score for successful login
                self.audit_logger.log_security_event(
                    event_type='unusual_login_pattern',
                    user=user,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    data={'anomaly_score': anomaly_score},
                    severity='medium'
                )
        
        return user
    
    def get_user(self, user_id):
        """
        Get user by ID with additional security checks
        """
        try:
            user = User.objects.get(pk=user_id)
            
            # Check if account is still active and not locked
            if not user.is_active:
                return None
            
            if hasattr(user, 'is_account_locked') and user.is_account_locked():
                return None
            
            return user
        except User.DoesNotExist:
            return None
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        if not request:
            return '127.0.0.1'
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        return ip


class TwoFactorAuthenticationBackend(ModelBackend):
    """
    Backend for two-factor authentication validation
    """
    
    def authenticate(self, request, username=None, password=None, totp_token=None, **kwargs):
        """
        Authenticate with 2FA token
        """
        # First authenticate with regular backend
        user = super().authenticate(request, username, password, **kwargs)
        
        if user and hasattr(user, 'is_two_factor_enabled') and user.is_two_factor_enabled:
            if not totp_token:
                return None
            
            from .utils import verify_totp_token, verify_backup_code
            
            # Verify TOTP token
            if verify_totp_token(user.two_factor_secret, totp_token):
                return user
            
            # Try backup code
            if verify_backup_code(user, totp_token):
                return user
            
            # 2FA verification failed
            return None
        
        return user


class APIKeyAuthenticationBackend(ModelBackend):
    """
    Backend for API key authentication
    """
    
    def authenticate(self, request, api_key=None, **kwargs):
        """
        Authenticate using API key
        """
        if not api_key:
            return None
        
        try:
            from .models import APIKey
            api_key_obj = APIKey.objects.select_related('user').get(
                key_hash=APIKey.hash_key(api_key),
                is_active=True,
                expires_at__gt=timezone.now()
            )
            
            # Update last used
            api_key_obj.last_used = timezone.now()
            api_key_obj.save(update_fields=['last_used'])
            
            return api_key_obj.user
            
        except APIKey.DoesNotExist:
            return None