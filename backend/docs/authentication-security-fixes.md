# Authentication Security Fixes Implementation Guide

## Critical Security Fixes (Implement Immediately)

### 1. Encrypt 2FA Secrets at Rest

**File**: `/apps/authentication/models.py`

```python
from django.conf import settings
from django.core import signing
from cryptography.fernet import Fernet
import base64
import os

class User(AbstractBaseUser, PermissionsMixin):
    # Change the field to store encrypted data
    _two_factor_secret_encrypted = models.TextField(
        _('2FA secret encrypted'), 
        blank=True,
        help_text='Encrypted 2FA secret'
    )
    
    # Remove the old plaintext field
    # two_factor_secret = models.CharField(...)  # DELETE THIS
    
    @property
    def two_factor_secret(self):
        """Decrypt and return the 2FA secret."""
        if not self._two_factor_secret_encrypted:
            return None
        
        try:
            # Use Django's signing framework with additional encryption
            fernet = Fernet(settings.ENCRYPTION_KEY)
            decrypted = fernet.decrypt(self._two_factor_secret_encrypted.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt 2FA secret: {str(e)}")
            return None
    
    @two_factor_secret.setter
    def two_factor_secret(self, value):
        """Encrypt and store the 2FA secret."""
        if value:
            fernet = Fernet(settings.ENCRYPTION_KEY)
            encrypted = fernet.encrypt(value.encode())
            self._two_factor_secret_encrypted = encrypted.decode()
        else:
            self._two_factor_secret_encrypted = ''
    
    def rotate_encryption_key(self, old_key, new_key):
        """Rotate encryption keys for 2FA secrets."""
        if self._two_factor_secret_encrypted:
            # Decrypt with old key
            old_fernet = Fernet(old_key)
            decrypted = old_fernet.decrypt(self._two_factor_secret_encrypted.encode())
            
            # Encrypt with new key
            new_fernet = Fernet(new_key)
            self._two_factor_secret_encrypted = new_fernet.encrypt(decrypted).decode()
            self.save(update_fields=['_two_factor_secret_encrypted'])
```

**Settings Update** (`/core/settings/base.py`):
```python
# Generate a key: from cryptography.fernet import Fernet; print(Fernet.generate_key())
ENCRYPTION_KEY = env('ENCRYPTION_KEY', default=Fernet.generate_key())

# Ensure the key is properly formatted
if isinstance(ENCRYPTION_KEY, str):
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()
```

**Migration** (`/apps/authentication/migrations/xxxx_encrypt_2fa_secrets.py`):
```python
from django.db import migrations
from cryptography.fernet import Fernet
from django.conf import settings

def encrypt_existing_secrets(apps, schema_editor):
    User = apps.get_model('authentication', 'User')
    fernet = Fernet(settings.ENCRYPTION_KEY)
    
    for user in User.objects.exclude(two_factor_secret=''):
        if user.two_factor_secret:
            encrypted = fernet.encrypt(user.two_factor_secret.encode())
            user._two_factor_secret_encrypted = encrypted.decode()
            user.save()

def reverse_encryption(apps, schema_editor):
    # This is irreversible for security reasons
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('authentication', 'latest_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='_two_factor_secret_encrypted',
            field=models.TextField(blank=True),
        ),
        migrations.RunPython(encrypt_existing_secrets, reverse_encryption),
        migrations.RemoveField(
            model_name='user',
            name='two_factor_secret',
        ),
    ]
```

### 2. Remove Debug Endpoints

**File**: `/apps/authentication/views.py`

```python
# DELETE ENTIRE CLASS (lines 47-79)
# class DebugRegisterView(APIView):
#     """Temporary debug endpoint for registration validation"""
#     ...

# Also remove from urls.py
# path('debug/register/', DebugRegisterView.as_view(), name='debug-register'),
```

### 3. Fix Token Blacklisting

**File**: `/apps/authentication/views.py`

```python
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            
            # Always blacklist - no fallback
            token.blacklist()
            
            # Log the logout event
            logger.info(
                f"User logged out successfully",
                extra={
                    'user_id': request.user.id,
                    'email': request.user.email,
                    'ip_address': get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                }
            )
            
            return Response(
                {'detail': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )
            
        except TokenError as e:
            logger.warning(
                f"Invalid token during logout attempt",
                extra={
                    'error': str(e),
                    'ip_address': get_client_ip(request),
                }
            )
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during logout",
                extra={'error': str(e)},
                exc_info=True
            )
            return Response(
                {'error': 'An error occurred during logout'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

### 4. Replace Print Statements with Proper Logging

**File**: `/apps/authentication/views.py`

```python
import logging
import structlog

# Configure structured logging
logger = structlog.get_logger(__name__)

# Replace all print statements
# OLD: print(f"Deleting account for user: {user.email} (ID: {user.id})")
# NEW:
logger.info(
    "account_deletion_initiated",
    user_id=user.id,
    email=user.email,
    timestamp=timezone.now().isoformat(),
)

# Example structured logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.processors.JSONRenderer(),
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/authentication.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'json',
        },
    },
    'loggers': {
        'authentication': {
            'handlers': ['file', 'security'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

## High Priority Security Enhancements

### 1. Strengthen Rate Limiting

**File**: `/apps/authentication/views.py`

```python
from django.core.cache import cache
from django.utils import timezone
import hashlib

class ProgressiveRateLimiter:
    """Implement progressive delays for failed attempts."""
    
    def __init__(self, key_prefix='auth_attempt'):
        self.key_prefix = key_prefix
    
    def get_delay(self, identifier):
        """Get progressive delay in seconds based on failed attempts."""
        key = f"{self.key_prefix}:{identifier}"
        attempts = cache.get(key, 0)
        
        # Progressive delay: 0, 1, 2, 4, 8, 16, 32, 64 seconds
        delay = min(2 ** max(0, attempts - 1), 64)
        return delay if attempts > 0 else 0
    
    def record_attempt(self, identifier, success=False):
        """Record an authentication attempt."""
        key = f"{self.key_prefix}:{identifier}"
        
        if success:
            cache.delete(key)
        else:
            attempts = cache.get(key, 0) + 1
            cache.set(key, attempts, 3600)  # Reset after 1 hour
            
            # Log suspicious activity
            if attempts >= 5:
                logger.warning(
                    "multiple_failed_login_attempts",
                    identifier=identifier,
                    attempts=attempts,
                    timestamp=timezone.now().isoformat(),
                )

# Update LoginView
class LoginView(APIView):
    throttle_classes = [LoginRateThrottle]
    
    def post(self, request):
        # Get identifier (IP + user agent hash)
        identifier = self._get_identifier(request)
        
        # Check progressive delay
        limiter = ProgressiveRateLimiter()
        delay = limiter.get_delay(identifier)
        
        if delay > 0:
            return Response(
                {
                    'error': f'Too many failed attempts. Please wait {delay} seconds.',
                    'retry_after': delay
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # ... existing login logic ...
        
        # Record attempt result
        if login_successful:
            limiter.record_attempt(identifier, success=True)
        else:
            limiter.record_attempt(identifier, success=False)
    
    def _get_identifier(self, request):
        """Create unique identifier for rate limiting."""
        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        raw = f"{ip}:{user_agent}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
```

### 2. Implement Comprehensive Audit Logging

**File**: `/apps/authentication/audit.py`

```python
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()

class AuthenticationAuditLog(models.Model):
    """Comprehensive audit log for authentication events."""
    
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
        ('suspicious_activity', 'Suspicious Activity'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='auth_audit_logs'
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    
    # Additional context
    data = models.JSONField(default=dict)
    
    # Geographic data
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Risk assessment
    risk_score = models.FloatField(default=0.0)
    flagged = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.user} - {self.timestamp}"


class AuditLogger:
    """Helper class for logging authentication events."""
    
    @staticmethod
    def log_event(event_type, request=None, user=None, **extra_data):
        """Log an authentication event."""
        log_data = {
            'event_type': event_type,
            'timestamp': timezone.now(),
            'data': extra_data,
        }
        
        if user:
            log_data['user'] = user
        
        if request:
            log_data['ip_address'] = get_client_ip(request)
            log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
            
            # Add geographic data if available
            # This would integrate with a GeoIP service
            # log_data['country'] = get_country_from_ip(ip)
            # log_data['city'] = get_city_from_ip(ip)
        
        # Calculate risk score
        log_data['risk_score'] = calculate_risk_score(log_data)
        log_data['flagged'] = log_data['risk_score'] > 0.7
        
        # Create audit log
        audit_log = AuthenticationAuditLog.objects.create(**log_data)
        
        # Alert on high-risk events
        if audit_log.flagged:
            alert_security_team(audit_log)
        
        return audit_log


def calculate_risk_score(log_data):
    """Calculate risk score based on various factors."""
    score = 0.0
    
    # Failed login attempts
    if log_data['event_type'] == 'login_failure':
        recent_failures = AuthenticationAuditLog.objects.filter(
            ip_address=log_data.get('ip_address'),
            event_type='login_failure',
            timestamp__gte=timezone.now() - timezone.timedelta(hours=1)
        ).count()
        score += min(recent_failures * 0.1, 0.5)
    
    # New location
    if log_data.get('user') and log_data.get('country'):
        known_countries = AuthenticationAuditLog.objects.filter(
            user=log_data['user'],
            event_type='login_success'
        ).values_list('country', flat=True).distinct()
        
        if log_data['country'] not in known_countries:
            score += 0.3
    
    # Suspicious patterns
    if 'tor' in log_data.get('user_agent', '').lower():
        score += 0.2
    
    return min(score, 1.0)


def alert_security_team(audit_log):
    """Send alert for high-risk authentication events."""
    # Send email/SMS/Slack notification
    pass
```

### 3. Reduce Password Reset Token Lifetime

**File**: `/apps/authentication/models.py`

```python
class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            # Reduced from 24 hours to 2 hours
            self.expires_at = timezone.now() + timedelta(hours=2)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return not self.used and self.expires_at > timezone.now()
    
    def mark_as_used(self):
        self.used = True
        self.save()
        
        # Log password reset completion
        AuditLogger.log_event(
            'password_reset_complete',
            user=self.user,
            ip_address=self.ip_address,
            user_agent=self.user_agent
        )
```

## Implementation Testing Checklist

- [ ] Test 2FA secret encryption/decryption
- [ ] Verify debug endpoints are removed
- [ ] Test token blacklisting without fallback
- [ ] Verify all logging is structured
- [ ] Test progressive rate limiting
- [ ] Verify audit logs are created
- [ ] Test reduced token lifetimes
- [ ] Run security scanner (Bandit)
- [ ] Perform penetration testing
- [ ] Load test rate limiting

## Deployment Steps

1. **Pre-deployment**
   - Generate and securely store encryption key
   - Run migrations in staging environment
   - Test all authentication flows
   - Backup database

2. **Deployment**
   - Deploy code changes
   - Run migrations
   - Verify encryption key is loaded
   - Monitor error logs

3. **Post-deployment**
   - Verify all users can still login
   - Check 2FA functionality
   - Monitor security logs
   - Run security scan

## Monitoring and Alerts

Set up alerts for:
- Multiple failed login attempts (>5 in 10 minutes)
- Login from new country
- High risk score events (>0.7)
- Token decryption failures
- Rate limit violations

## Security Contact

For security issues or questions:
- Security Team: security@financehub.com
- Emergency: +1-xxx-xxx-xxxx
- PGP Key: [public key]