"""
Enhanced serializers for secure authentication
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models_enhanced import EnhancedUser
from .security.password_policies import password_validator
import re


class LoginSerializer(serializers.Serializer):
    """Enhanced login serializer with security validation"""
    
    email = serializers.EmailField(
        max_length=255,
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Please enter a valid email address.',
            'max_length': 'Email address is too long.'
        }
    )
    
    password = serializers.CharField(
        max_length=255,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Password is required.',
            'max_length': 'Password is too long.'
        }
    )
    
    remember_me = serializers.BooleanField(default=False)
    device_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    trust_device = serializers.BooleanField(default=False)
    
    def validate_email(self, value):
        """Validate email format and normalize"""
        # Normalize email
        value = value.lower().strip()
        
        # Additional email validation
        if len(value) < 5:
            raise serializers.ValidationError("Email address is too short.")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'^[0-9]+@',  # Starts with numbers
            r'\.{2,}',    # Multiple consecutive dots
            r'^\.|\.$',   # Starts or ends with dot
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, value):
                raise serializers.ValidationError("Invalid email format.")
        
        return value
    
    def validate_password(self, value):
        """Basic password validation for login"""
        if len(value) < 1:
            raise serializers.ValidationError("Password cannot be empty.")
        
        if len(value) > 255:
            raise serializers.ValidationError("Password is too long.")
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        # Device name is required if trust_device is True
        if attrs.get('trust_device') and not attrs.get('device_name'):
            raise serializers.ValidationError({
                'device_name': 'Device name is required when trusting device.'
            })
        
        return attrs


class RegisterSerializer(serializers.Serializer):
    """Enhanced registration serializer with comprehensive validation"""
    
    email = serializers.EmailField(
        max_length=255,
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Please enter a valid email address.',
            'max_length': 'Email address is too long.'
        }
    )
    
    password = serializers.CharField(
        max_length=255,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Password is required.',
            'max_length': 'Password is too long.'
        }
    )
    
    password_confirm = serializers.CharField(
        max_length=255,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Password confirmation is required.',
            'max_length': 'Password confirmation is too long.'
        }
    )
    
    first_name = serializers.CharField(
        max_length=150,
        error_messages={
            'required': 'First name is required.',
            'max_length': 'First name is too long.'
        }
    )
    
    last_name = serializers.CharField(
        max_length=150,
        error_messages={
            'required': 'Last name is required.',
            'max_length': 'Last name is too long.'
        }
    )
    
    terms_accepted = serializers.BooleanField(
        error_messages={
            'required': 'You must accept the terms of service.'
        }
    )
    
    def validate_email(self, value):
        """Validate email with enhanced checks"""
        # Normalize email
        value = value.lower().strip()
        
        # Check if email already exists
        if EnhancedUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        
        # Additional validation
        if len(value) < 5:
            raise serializers.ValidationError("Email address is too short.")
        
        # Block disposable email domains (basic list)
        disposable_domains = [
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'temp-mail.org'
        ]
        
        domain = value.split('@')[1] if '@' in value else ''
        if domain.lower() in disposable_domains:
            raise serializers.ValidationError("Disposable email addresses are not allowed.")
        
        return value
    
    def validate_password(self, value):
        """Comprehensive password validation"""
        # Use our enhanced password validator
        validation_result = password_validator.validate_password(value)
        
        if not validation_result['valid']:
            error_message = "Password does not meet security requirements: " + \
                          ", ".join(validation_result['recommendations'])
            raise serializers.ValidationError(error_message)
        
        return value
    
    def validate_first_name(self, value):
        """Validate first name"""
        value = value.strip()
        
        if len(value) < 1:
            raise serializers.ValidationError("First name cannot be empty.")
        
        # Check for invalid characters
        if not re.match(r'^[a-zA-Z\s\-\'\.]+$', value):
            raise serializers.ValidationError("First name contains invalid characters.")
        
        return value
    
    def validate_last_name(self, value):
        """Validate last name"""
        value = value.strip()
        
        if len(value) < 1:
            raise serializers.ValidationError("Last name cannot be empty.")
        
        # Check for invalid characters
        if not re.match(r'^[a-zA-Z\s\-\'\.]+$', value):
            raise serializers.ValidationError("Last name contains invalid characters.")
        
        return value
    
    def validate_terms_accepted(self, value):
        """Validate terms acceptance"""
        if not value:
            raise serializers.ValidationError("You must accept the terms of service to register.")
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        # Password confirmation
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        
        # Remove password_confirm from validated data
        attrs.pop('password_confirm', None)
        
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    """Password reset request serializer"""
    
    email = serializers.EmailField(
        max_length=255,
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Please enter a valid email address.',
            'max_length': 'Email address is too long.'
        }
    )
    
    def validate_email(self, value):
        """Validate and normalize email"""
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirmation serializer"""
    
    token = serializers.CharField(
        max_length=255,
        error_messages={
            'required': 'Reset token is required.',
            'max_length': 'Invalid token format.'
        }
    )
    
    password = serializers.CharField(
        max_length=255,
        style={'input_type': 'password'},
        error_messages={
            'required': 'New password is required.',
            'max_length': 'Password is too long.'
        }
    )
    
    password_confirm = serializers.CharField(
        max_length=255,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Password confirmation is required.',
            'max_length': 'Password confirmation is too long.'
        }
    )
    
    def validate_password(self, value):
        """Validate new password strength"""
        validation_result = password_validator.validate_password(value)
        
        if not validation_result['valid']:
            error_message = "Password does not meet security requirements: " + \
                          ", ".join(validation_result['recommendations'])
            raise serializers.ValidationError(error_message)
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        
        attrs.pop('password_confirm', None)
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Password change serializer for authenticated users"""
    
    current_password = serializers.CharField(
        max_length=255,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Current password is required.',
            'max_length': 'Current password is too long.'
        }
    )
    
    new_password = serializers.CharField(
        max_length=255,
        style={'input_type': 'password'},
        error_messages={
            'required': 'New password is required.',
            'max_length': 'New password is too long.'
        }
    )
    
    new_password_confirm = serializers.CharField(
        max_length=255,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Password confirmation is required.',
            'max_length': 'Password confirmation is too long.'
        }
    )
    
    def validate_current_password(self, value):
        """Validate current password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        
        return value
    
    def validate_new_password(self, value):
        """Validate new password strength and history"""
        user = self.context['request'].user
        
        # Check password strength
        validation_result = password_validator.validate_password(value, user)
        
        if not validation_result['valid']:
            error_message = "Password does not meet security requirements: " + \
                          ", ".join(validation_result['recommendations'])
            raise serializers.ValidationError(error_message)
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })
        
        # Check if new password is same as current
        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                'new_password': 'New password must be different from current password.'
            })
        
        attrs.pop('new_password_confirm', None)
        return attrs


class TwoFactorSetupSerializer(serializers.Serializer):
    """2FA setup serializer"""
    
    totp_code = serializers.CharField(
        max_length=6,
        min_length=6,
        error_messages={
            'required': 'TOTP code is required.',
            'min_length': 'TOTP code must be 6 digits.',
            'max_length': 'TOTP code must be 6 digits.'
        }
    )
    
    def validate_totp_code(self, value):
        """Validate TOTP code format"""
        if not value.isdigit():
            raise serializers.ValidationError("TOTP code must contain only digits.")
        
        return value


class TwoFactorVerifySerializer(serializers.Serializer):
    """2FA verification serializer"""
    
    temp_token = serializers.CharField(
        max_length=255,
        error_messages={
            'required': 'Temporary token is required.',
            'max_length': 'Invalid token format.'
        }
    )
    
    totp_code = serializers.CharField(
        max_length=6,
        min_length=6,
        required=False,
        allow_blank=True,
        error_messages={
            'min_length': 'TOTP code must be 6 digits.',
            'max_length': 'TOTP code must be 6 digits.'
        }
    )
    
    backup_code = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        error_messages={
            'max_length': 'Invalid backup code format.'
        }
    )
    
    remember_me = serializers.BooleanField(default=False)
    trust_device = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        """Ensure either TOTP code or backup code is provided"""
        totp_code = attrs.get('totp_code')
        backup_code = attrs.get('backup_code')
        
        if not totp_code and not backup_code:
            raise serializers.ValidationError(
                "Either TOTP code or backup code is required."
            )
        
        if totp_code and backup_code:
            raise serializers.ValidationError(
                "Provide either TOTP code or backup code, not both."
            )
        
        # Validate TOTP code format
        if totp_code and not totp_code.isdigit():
            raise serializers.ValidationError({
                'totp_code': 'TOTP code must contain only digits.'
            })
        
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """Email verification serializer"""
    
    token = serializers.CharField(
        max_length=255,
        error_messages={
            'required': 'Verification token is required.',
            'max_length': 'Invalid token format.'
        }
    )


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    
    class Meta:
        model = EnhancedUser
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone', 'date_of_birth', 'preferred_language', 'timezone',
            'is_email_verified', 'is_phone_verified', 'is_two_factor_enabled',
            'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = [
            'id', 'email', 'username', 'is_email_verified', 'is_phone_verified',
            'created_at', 'updated_at', 'last_login'
        ]
    
    def validate_phone(self, value):
        """Validate phone number"""
        if value:
            # Remove all non-digit characters
            cleaned = re.sub(r'\D', '', value)
            
            # Basic validation
            if len(cleaned) < 10 or len(cleaned) > 15:
                raise serializers.ValidationError("Invalid phone number format.")
        
        return value
    
    def validate_first_name(self, value):
        """Validate first name"""
        if value:
            value = value.strip()
            if not re.match(r'^[a-zA-Z\s\-\'\.]+$', value):
                raise serializers.ValidationError("First name contains invalid characters.")
        
        return value
    
    def validate_last_name(self, value):
        """Validate last name"""
        if value:
            value = value.strip()
            if not re.match(r'^[a-zA-Z\s\-\'\.]+$', value):
                raise serializers.ValidationError("Last name contains invalid characters.")
        
        return value


class SecuritySettingsSerializer(serializers.Serializer):
    """Security settings serializer"""
    
    is_two_factor_enabled = serializers.BooleanField(read_only=True)
    failed_login_attempts = serializers.IntegerField(read_only=True)
    last_login_ip = serializers.IPAddressField(read_only=True)
    last_login_location = serializers.CharField(read_only=True)
    last_login_device = serializers.CharField(read_only=True)
    password_changed_at = serializers.DateTimeField(read_only=True)
    risk_score = serializers.FloatField(read_only=True)
    trusted_devices_count = serializers.SerializerMethodField()
    active_sessions_count = serializers.SerializerMethodField()
    
    def get_trusted_devices_count(self, obj):
        """Get count of trusted devices"""
        return len(obj.trusted_devices or [])
    
    def get_active_sessions_count(self, obj):
        """Get count of active sessions"""
        return len(obj.active_sessions or {})


class SessionSerializer(serializers.Serializer):
    """Session information serializer"""
    
    session_key = serializers.CharField(read_only=True)
    device_name = serializers.CharField(read_only=True)
    ip_address = serializers.IPAddressField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    last_activity = serializers.DateTimeField(read_only=True)
    current = serializers.BooleanField(read_only=True)


class TrustedDeviceSerializer(serializers.Serializer):
    """Trusted device serializer"""
    
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    browser = serializers.DictField(read_only=True)
    os = serializers.DictField(read_only=True)
    trusted_at = serializers.DateTimeField(read_only=True)
    last_used = serializers.DateTimeField(read_only=True)


class OAuth2ProviderSerializer(serializers.Serializer):
    """OAuth2 provider serializer"""
    
    provider_id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    auth_url = serializers.URLField(read_only=True)


class AuditLogSerializer(serializers.Serializer):
    """Audit log serializer"""
    
    id = serializers.IntegerField(read_only=True)
    event_type = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    ip_address = serializers.IPAddressField(read_only=True)
    success = serializers.BooleanField(read_only=True)
    risk_score = serializers.FloatField(read_only=True)
    flagged = serializers.BooleanField(read_only=True)
    country = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    error_message = serializers.CharField(read_only=True)


class SecurityEventSerializer(serializers.Serializer):
    """Security event serializer"""
    
    id = serializers.IntegerField(read_only=True)
    event_type = serializers.CharField(read_only=True)
    severity = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    ip_address = serializers.IPAddressField(read_only=True)
    resolved = serializers.BooleanField(read_only=True)
    action_taken = serializers.CharField(read_only=True)