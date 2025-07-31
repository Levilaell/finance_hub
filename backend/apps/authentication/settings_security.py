"""
Enhanced security settings for authentication system
"""
import os
from datetime import timedelta
from cryptography.fernet import Fernet

# JWT Security Configuration
JWT_COOKIE_SETTINGS = {
    # Cookie names
    'JWT_ACCESS_COOKIE_NAME': 'access_token',
    'JWT_REFRESH_COOKIE_NAME': 'refresh_token',
    
    # Cookie security settings
    'JWT_COOKIE_SECURE': not bool(os.environ.get('DEBUG', False)),  # HTTPS only in production
    'JWT_COOKIE_HTTPONLY': True,  # Always True for security
    'JWT_COOKIE_SAMESITE': 'Lax',  # Protection against CSRF
    'JWT_COOKIE_PATH': '/',
    'JWT_COOKIE_DOMAIN': os.environ.get('JWT_COOKIE_DOMAIN', None),
}

# Enhanced JWT Configuration
SIMPLE_JWT_SECURE = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),  # Short-lived for security
    'REFRESH_TOKEN_LIFETIME': timedelta(days=3),     # Reasonable refresh period
    'ROTATE_REFRESH_TOKENS': True,                   # Rotate on each refresh
    'BLACKLIST_AFTER_ROTATION': True,               # Blacklist old tokens
    'UPDATE_LAST_LOGIN': True,                       # Track login activity
    
    # Enhanced security algorithm
    'ALGORITHM': 'RS256',                            # Asymmetric encryption
    'SIGNING_KEY': os.environ.get('JWT_PRIVATE_KEY', None),
    'VERIFYING_KEY': os.environ.get('JWT_PUBLIC_KEY', None),
    
    # Headers and claims
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    # Token validation
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    
    # Sliding tokens disabled for security
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# CSRF Security Configuration
CSRF_SETTINGS = {
    'CSRF_USE_SESSIONS': True,
    'CSRF_COOKIE_SECURE': not bool(os.environ.get('DEBUG', False)),
    'CSRF_COOKIE_HTTPONLY': True,
    'CSRF_COOKIE_SAMESITE': 'Strict',
    'CSRF_COOKIE_NAME': 'csrftoken',
    'CSRF_HEADER_NAME': 'HTTP_X_CSRFTOKEN',
    'CSRF_TRUSTED_ORIGINS': [
        origin.strip() for origin in 
        os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
        if origin.strip()
    ],
}

# Session Security Configuration
SESSION_SECURITY = {
    'SESSION_COOKIE_SECURE': not bool(os.environ.get('DEBUG', False)),
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'SESSION_COOKIE_AGE': 3600,  # 1 hour
    'SESSION_EXPIRE_AT_BROWSER_CLOSE': True,
    'SESSION_SAVE_EVERY_REQUEST': True,
}

# Enhanced Security Headers
SECURITY_HEADERS = {
    'SECURE_BROWSER_XSS_FILTER': True,
    'SECURE_CONTENT_TYPE_NOSNIFF': True,
    'SECURE_HSTS_SECONDS': 31536000,  # 1 year
    'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
    'SECURE_HSTS_PRELOAD': True,
    'SECURE_REFERRER_POLICY': 'strict-origin-when-cross-origin',
    'X_FRAME_OPTIONS': 'DENY',
}

# Request Signing Configuration
REQUEST_SIGNING = {
    'REQUEST_SIGNING_KEY': os.environ.get('REQUEST_SIGNING_KEY', None),
    'REQUEST_SIGNATURE_ALGORITHM': 'PBKDF2-SHA256',
    'REQUEST_SIGNATURE_ITERATIONS': 100000,
    'REQUEST_TIMESTAMP_TOLERANCE': 300,  # 5 minutes
}

# Rate Limiting Configuration
RATE_LIMITING = {
    'AUTH_MAX_LOGIN_ATTEMPTS': 5,
    'AUTH_LOCKOUT_DURATION': 3600,      # 1 hour
    'AUTH_ATTEMPT_RESET_PERIOD': 86400,  # 24 hours
    'AUTH_PROGRESSIVE_DELAY': True,
    'AUTH_SUBNET_PROTECTION': True,
}

# Audit Logging Configuration
AUDIT_LOGGING = {
    'LOG_SUCCESSFUL_AUTH_EVENTS': True,
    'LOG_FAILED_AUTH_EVENTS': True,
    'LOG_2FA_EVENTS': True,
    'LOG_PASSWORD_CHANGES': True,
    'LOG_SECURITY_EVENTS': True,
    'AUDIT_LOG_RETENTION_DAYS': 90,
}

# Encryption Configuration
ENCRYPTION_SETTINGS = {
    'ENCRYPTION_KEY': os.environ.get('ENCRYPTION_KEY', None),
    'FIELD_ENCRYPTION_KEY': os.environ.get('FIELD_ENCRYPTION_KEY', None),
}

# Generate fallback keys for development (NOT for production)
if not ENCRYPTION_SETTINGS['ENCRYPTION_KEY'] and os.environ.get('DEBUG'):
    ENCRYPTION_SETTINGS['ENCRYPTION_KEY'] = Fernet.generate_key()
    print("Warning: Using generated encryption key for development. Set ENCRYPTION_KEY in production!")

# Content Security Policy
CSP_SETTINGS = {
    'CSP_DEFAULT_SRC': ["'self'"],
    'CSP_SCRIPT_SRC': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
    'CSP_STYLE_SRC': ["'self'", "'unsafe-inline'"],
    'CSP_IMG_SRC': ["'self'", "data:", "https:"],
    'CSP_FONT_SRC': ["'self'", "data:"],
    'CSP_CONNECT_SRC': ["'self'"],
    'CSP_FRAME_ANCESTORS': ["'none'"],
    'CSP_FORM_ACTION': ["'self'"],
    'CSP_BASE_URI': ["'self'"],
    'CSP_OBJECT_SRC': ["'none'"],
    'CSP_MEDIA_SRC': ["'self'"],
}

# Permissions Policy (formerly Feature Policy)
PERMISSIONS_POLICY = {
    'geolocation': [],
    'microphone': [],
    'camera': [],
    'payment': [],
    'usb': [],
    'bluetooth': [],
    'accelerometer': [],
    'gyroscope': [],
    'magnetometer': [],
}

# Authentication Middleware Configuration
AUTH_MIDDLEWARE = [
    'apps.authentication.middleware.SecurityHeadersMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'apps.authentication.middleware.CSRFExemptionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.authentication.middleware.SecureJWTAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Environment-specific security settings
def get_security_settings(debug=False):
    """
    Get security settings based on environment
    """
    settings = {}
    
    # Apply JWT cookie settings
    settings.update(JWT_COOKIE_SETTINGS)
    
    # Apply CSRF settings
    settings.update(CSRF_SETTINGS)
    
    # Apply session security
    settings.update(SESSION_SECURITY)
    
    # Apply security headers
    settings.update(SECURITY_HEADERS)
    
    # Apply rate limiting
    settings.update(RATE_LIMITING)
    
    # Apply audit logging
    settings.update(AUDIT_LOGGING)
    
    # Apply encryption settings
    settings.update(ENCRYPTION_SETTINGS)
    
    # Environment-specific adjustments
    if debug:
        # Development settings
        settings.update({
            'JWT_COOKIE_SECURE': False,
            'CSRF_COOKIE_SECURE': False,
            'SESSION_COOKIE_SECURE': False,
            'SECURE_HSTS_SECONDS': 0,
        })
    else:
        # Production settings
        settings.update({
            'JWT_COOKIE_SECURE': True,
            'CSRF_COOKIE_SECURE': True,
            'SESSION_COOKIE_SECURE': True,
            'SECURE_SSL_REDIRECT': True,
            'SECURE_PROXY_SSL_HEADER': ('HTTP_X_FORWARDED_PROTO', 'https'),
        })
    
    return settings


# Validation functions
def validate_security_configuration():
    """
    Validate security configuration for production readiness
    """
    errors = []
    warnings = []
    
    # Check for required environment variables
    required_vars = [
        'JWT_PRIVATE_KEY',
        'JWT_PUBLIC_KEY', 
        'REQUEST_SIGNING_KEY',
        'ENCRYPTION_KEY',
    ]
    
    for var in required_vars:
        if not os.environ.get(var):
            if not os.environ.get('DEBUG'):
                errors.append(f"Missing required environment variable: {var}")
            else:
                warnings.append(f"Using fallback for {var} in development")
    
    # Check CSRF trusted origins
    if not CSRF_SETTINGS['CSRF_TRUSTED_ORIGINS']:
        warnings.append("No CSRF trusted origins configured")
    
    # Check cookie domain
    if not JWT_COOKIE_SETTINGS['JWT_COOKIE_DOMAIN']:
        warnings.append("JWT cookie domain not configured")
    
    return errors, warnings