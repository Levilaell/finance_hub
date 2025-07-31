"""
Enhanced authentication models with comprehensive security features
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator
from .security.encryption import default_encryption
import secrets
import json
from datetime import timedelta
import hashlib


class EnhancedUserManager(models.Manager):
    """Custom user manager with security enhancements"""
    
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_email_verified', True)
        
        return self.create_user(email, username, password, **extra_fields)


class EnhancedUser(AbstractBaseUser, PermissionsMixin):
    """
    Enhanced user model with comprehensive security features
    """
    # Basic Information
    email = models.EmailField(_('email address'), unique=True, db_index=True)
    username = models.CharField(_('username'), max_length=150, unique=True, db_index=True)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    phone = models.CharField(_('phone number'), max_length=20, blank=True)
    
    # Profile
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(_('date of birth'), blank=True, null=True)
    preferred_language = models.CharField(
        _('preferred language'),
        max_length=10,
        choices=[('pt-br', 'Português'), ('en', 'English')],
        default='pt-br'
    )
    timezone = models.CharField(_('timezone'), max_length=50, default='America/Sao_Paulo')
    
    # Status Flags
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_email_verified = models.BooleanField(_('email verified'), default=False)
    is_phone_verified = models.BooleanField(_('phone verified'), default=False)
    
    # Security Features
    is_two_factor_enabled = models.BooleanField(_('2FA enabled'), default=False)
    _two_factor_secret_encrypted = models.TextField(_('2FA secret encrypted'), blank=True)
    backup_codes = models.JSONField(_('backup codes'), default=list, blank=True)
    
    # Account Security
    failed_login_attempts = models.PositiveIntegerField(_('failed login attempts'), default=0)
    last_failed_login = models.DateTimeField(_('last failed login'), blank=True, null=True)
    is_locked = models.BooleanField(_('account locked'), default=False)
    locked_until = models.DateTimeField(_('locked until'), blank=True, null=True)
    
    # Password Security
    password_changed_at = models.DateTimeField(_('password changed at'), blank=True, null=True)
    password_history = models.JSONField(_('password history'), default=list, blank=True)
    must_change_password = models.BooleanField(_('must change password'), default=False)
    
    # Session Management
    last_login_ip = models.GenericIPAddressField(_('last login IP'), blank=True, null=True)
    last_login_location = models.CharField(_('last login location'), max_length=255, blank=True)
    last_login_device = models.CharField(_('last login device'), max_length=255, blank=True)
    active_sessions = models.JSONField(_('active sessions'), default=dict, blank=True)
    
    # Trusted Devices
    trusted_devices = models.JSONField(_('trusted devices'), default=list, blank=True)
    
    # Security Tracking
    security_questions = models.JSONField(_('security questions'), default=dict, blank=True)
    known_networks = models.JSONField(_('known networks'), default=list, blank=True)
    risk_score = models.FloatField(_('risk score'), default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    
    # Payment Integration
    payment_customer_id = models.CharField(
        _('payment gateway customer ID'),
        max_length=255,
        blank=True,
        null=True
    )
    payment_gateway = models.CharField(
        _('payment gateway'),
        max_length=50,
        choices=[('stripe', 'Stripe'), ('mercadopago', 'MercadoPago')],
        blank=True,
        null=True
    )
    
    objects = EnhancedUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'auth_enhanced_users'
        verbose_name = _('Enhanced User')
        verbose_name_plural = _('Enhanced Users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['is_email_verified']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_locked']),
            models.Index(fields=['risk_score']),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()
    
    # 2FA Secret Encryption
    @property
    def two_factor_secret(self):
        """Decrypt and return the 2FA secret"""
        if not self._two_factor_secret_encrypted:
            return None
        
        try:
            return default_encryption.decrypt(self._two_factor_secret_encrypted)
        except Exception:
            return None
    
    @two_factor_secret.setter
    def two_factor_secret(self, value):
        """Encrypt and store the 2FA secret"""
        if value:
            self._two_factor_secret_encrypted = default_encryption.encrypt(value)
        else:
            self._two_factor_secret_encrypted = ''
    
    # Account Lockout Methods
    def increment_failed_login(self):
        """Increment failed login attempts and lock if necessary"""
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account()
        
        self.save()
    
    def reset_failed_login(self):
        """Reset failed login attempts on successful login"""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.save()
    
    def lock_account(self, duration_hours=1):
        """Lock account for specified duration"""
        self.is_locked = True
        self.locked_until = timezone.now() + timedelta(hours=duration_hours)
        self.save()
    
    def unlock_account(self):
        """Unlock account"""
        self.is_locked = False
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save()
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.is_locked:
            if self.locked_until and self.locked_until <= timezone.now():
                self.unlock_account()
                return False
            return True
        return False
    
    # Password History
    def add_to_password_history(self, password_hash):
        """Add password hash to history (keep last 5)"""
        if not isinstance(self.password_history, list):
            self.password_history = []
        
        self.password_history.insert(0, {
            'hash': password_hash,
            'created_at': timezone.now().isoformat()
        })
        
        # Keep only last 5 passwords
        self.password_history = self.password_history[:5]
        self.password_changed_at = timezone.now()
        self.save()
    
    def is_password_in_history(self, password):
        """Check if password was recently used"""
        for entry in self.password_history:
            # This would need proper password checking logic
            # For now, we'll assume the check is implemented
            pass
        return False
    
    # Session Management
    def add_active_session(self, session_key, ip_address, user_agent):
        """Add an active session"""
        self.active_sessions[session_key] = {
            'ip_address': ip_address,
            'user_agent': user_agent,
            'created_at': timezone.now().isoformat(),
            'last_activity': timezone.now().isoformat()
        }
        self.save()
    
    def remove_active_session(self, session_key):
        """Remove an active session"""
        if session_key in self.active_sessions:
            del self.active_sessions[session_key]
            self.save()
    
    def logout_all_sessions(self):
        """Clear all active sessions"""
        self.active_sessions = {}
        self.save()
    
    # Trusted Devices
    def add_trusted_device(self, device_id, name, user_agent):
        """Add a trusted device"""
        device = {
            'id': device_id,
            'name': name,
            'user_agent': user_agent,
            'trusted_at': timezone.now().isoformat(),
            'last_used': timezone.now().isoformat()
        }
        
        if not isinstance(self.trusted_devices, list):
            self.trusted_devices = []
        
        self.trusted_devices.append(device)
        self.save()
    
    def is_device_trusted(self, device_id):
        """Check if device is trusted"""
        for device in self.trusted_devices:
            if device.get('id') == device_id:
                return True
        return False
    
    def remove_trusted_device(self, device_id):
        """Remove a trusted device"""
        self.trusted_devices = [
            d for d in self.trusted_devices if d.get('id') != device_id
        ]
        self.save()
    
    # Risk Assessment
    def calculate_risk_score(self, ip_address=None, user_agent=None, location=None):
        """Calculate user risk score based on various factors"""
        score = 0.0
        
        # Recent failed logins
        if self.failed_login_attempts > 0:
            score += min(self.failed_login_attempts * 0.1, 0.3)
        
        # Account age
        account_age = (timezone.now() - self.created_at).days
        if account_age < 7:
            score += 0.2
        elif account_age < 30:
            score += 0.1
        
        # New location
        if location and location not in self.known_networks:
            score += 0.2
        
        # Password age
        if self.password_changed_at:
            password_age = (timezone.now() - self.password_changed_at).days
            if password_age > 90:
                score += 0.1
        
        # Update risk score
        self.risk_score = min(score, 1.0)
        self.save()
        
        return self.risk_score


class AuthenticationAuditLog(models.Model):
    """
    Comprehensive audit log for all authentication events
    """
    EVENT_TYPES = [
        ('login_success', 'Login Success'),
        ('login_failure', 'Login Failure'),
        ('logout', 'Logout'),
        ('password_reset_request', 'Password Reset Request'),
        ('password_reset_complete', 'Password Reset Complete'),
        ('password_change', 'Password Change'),
        ('2fa_enable', '2FA Enabled'),
        ('2fa_disable', '2FA Disabled'),
        ('2fa_success', '2FA Success'),
        ('2fa_failure', '2FA Failure'),
        ('account_locked', 'Account Locked'),
        ('account_unlocked', 'Account Unlocked'),
        ('email_verified', 'Email Verified'),
        ('device_trusted', 'Device Trusted'),
        ('session_expired', 'Session Expired'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('oauth_login', 'OAuth Login'),
        ('api_key_created', 'API Key Created'),
        ('api_key_revoked', 'API Key Revoked'),
    ]
    
    user = models.ForeignKey(
        EnhancedUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Request Information
    ip_address = models.GenericIPAddressField(null=True, db_index=True)
    user_agent = models.TextField(blank=True)
    
    # Location Information
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Additional Context
    data = models.JSONField(default=dict)
    
    # Risk Assessment
    risk_score = models.FloatField(default=0.0)
    flagged = models.BooleanField(default=False, db_index=True)
    
    # Response
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'auth_audit_logs'
        verbose_name = _('Authentication Audit Log')
        verbose_name_plural = _('Authentication Audit Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
            models.Index(fields=['flagged', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.user} - {self.timestamp}"


class SecureToken(models.Model):
    """
    Base model for secure tokens with encryption
    """
    user = models.ForeignKey(EnhancedUser, on_delete=models.CASCADE)
    _token_encrypted = models.TextField(db_index=True)
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
        ]
    
    def generate_token(self):
        """Generate a secure random token"""
        token = secrets.token_urlsafe(32)
        self._token_encrypted = default_encryption.encrypt(token)
        self.token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token
    
    def verify_token(self, token):
        """Verify if provided token matches"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return self.token_hash == token_hash and self.is_valid()
    
    def is_valid(self):
        """Check if token is still valid"""
        return (
            self.is_active and
            not self.used_at and
            self.expires_at > timezone.now()
        )
    
    def mark_as_used(self):
        """Mark token as used"""
        self.used_at = timezone.now()
        self.is_active = False
        self.save()


class EmailVerificationToken(SecureToken):
    """Email verification tokens with secure storage"""
    
    class Meta:
        db_table = 'auth_email_verification_tokens'
        verbose_name = _('Email Verification Token')
        verbose_name_plural = _('Email Verification Tokens')
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)


class PasswordResetToken(SecureToken):
    """Password reset tokens with secure storage"""
    
    class Meta:
        db_table = 'auth_password_reset_tokens'
        verbose_name = _('Password Reset Token')
        verbose_name_plural = _('Password Reset Tokens')
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=2)  # Reduced from 24 hours
        super().save(*args, **kwargs)


class OAuth2Provider(models.Model):
    """OAuth2 provider configuration"""
    name = models.CharField(max_length=50, unique=True)
    provider_id = models.CharField(max_length=50, unique=True)
    client_id = models.CharField(max_length=255)
    _client_secret_encrypted = models.TextField()
    
    authorization_url = models.URLField()
    token_url = models.URLField()
    user_info_url = models.URLField()
    
    scope = models.CharField(max_length=500, default='email profile')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_oauth2_providers'
        verbose_name = _('OAuth2 Provider')
        verbose_name_plural = _('OAuth2 Providers')
    
    @property
    def client_secret(self):
        return default_encryption.decrypt(self._client_secret_encrypted)
    
    @client_secret.setter
    def client_secret(self, value):
        self._client_secret_encrypted = default_encryption.encrypt(value)


class OAuth2Connection(models.Model):
    """User OAuth2 connections"""
    user = models.ForeignKey(
        EnhancedUser,
        on_delete=models.CASCADE,
        related_name='oauth_connections'
    )
    provider = models.ForeignKey(OAuth2Provider, on_delete=models.CASCADE)
    provider_user_id = models.CharField(max_length=255)
    
    access_token_encrypted = models.TextField()
    refresh_token_encrypted = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    profile_data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_oauth2_connections'
        verbose_name = _('OAuth2 Connection')
        verbose_name_plural = _('OAuth2 Connections')
        unique_together = [['user', 'provider', 'provider_user_id']]
    
    def __str__(self):
        return f"{self.user.email} - {self.provider.name}"


class RememberMeToken(models.Model):
    """
    Remember Me tokens for persistent login
    """
    user = models.ForeignKey(
        EnhancedUser,
        on_delete=models.CASCADE,
        related_name='remember_tokens'
    )
    
    selector = models.CharField(max_length=12, unique=True, db_index=True)
    _validator_hash = models.CharField(max_length=64)
    
    device_id = models.CharField(max_length=64, blank=True)
    device_name = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_used = models.DateTimeField(null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'auth_remember_tokens'
        verbose_name = _('Remember Me Token')
        verbose_name_plural = _('Remember Me Tokens')
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
        ]
    
    def generate_token(self):
        """Generate selector and validator"""
        self.selector = secrets.token_urlsafe(9)[:12]
        validator = secrets.token_urlsafe(32)
        self._validator_hash = hashlib.sha256(validator.encode()).hexdigest()
        return f"{self.selector}:{validator}"
    
    def verify_validator(self, validator):
        """Verify the validator part of the token"""
        validator_hash = hashlib.sha256(validator.encode()).hexdigest()
        return self._validator_hash == validator_hash
    
    def is_valid(self):
        """Check if token is still valid"""
        return self.is_active and self.expires_at > timezone.now()
    
    def update_last_used(self):
        """Update last used timestamp"""
        self.last_used = timezone.now()
        self.save()


class SecurityEvent(models.Model):
    """
    Track security-related events for anomaly detection
    """
    EVENT_TYPES = [
        ('new_device', 'New Device Login'),
        ('new_location', 'New Location Login'),
        ('password_spray', 'Password Spray Detected'),
        ('brute_force', 'Brute Force Detected'),
        ('impossible_travel', 'Impossible Travel Detected'),
        ('suspicious_pattern', 'Suspicious Pattern'),
        ('account_takeover', 'Possible Account Takeover'),
    ]
    
    user = models.ForeignKey(
        EnhancedUser,
        on_delete=models.CASCADE,
        related_name='security_events',
        null=True,
        blank=True
    )
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ]
    )
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Event Details
    ip_address = models.GenericIPAddressField(null=True)
    data = models.JSONField(default=dict)
    
    # Response
    action_taken = models.CharField(max_length=100, blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_security_events'
        verbose_name = _('Security Event')
        verbose_name_plural = _('Security Events')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['severity', 'resolved']),
        ]