"""
Production settings for CaixaHub - SIMPLIFIED VERSION
"""
import os
from urllib.parse import urlparse
from .base import *

# Security
DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY environment variable is required!")

# Database
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    import dj_database_url
    DATABASES['default'] = dj_database_url.parse(DATABASE_URL)
else:
    raise ImproperlyConfigured("DATABASE_URL environment variable is required!")

# Allowed Hosts
ALLOWED_HOSTS = [
    'financehub-production.up.railway.app',
    'caixahub.com.br',
    'www.caixahub.com.br',
]

# CORS - SIMPLIFIED
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://caixahub.com.br')
CORS_ALLOWED_ORIGINS = [
    FRONTEND_URL,
    'https://caixahub.com.br',
    'https://www.caixahub.com.br',
]
CORS_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()

# MOBILE SAFARI COMPATIBLE COOKIES - SIMPLE AND CONSISTENT
# All cookies use the same policy for consistency
SESSION_COOKIE_SAMESITE = 'None'  # Required for mobile Safari cross-origin
SESSION_COOKIE_SECURE = True      # Required when SameSite=None
CSRF_COOKIE_SAMESITE = 'None'     # Consistent with session
CSRF_COOKIE_SECURE = True         # Consistent with session

# JWT FORCED HS256 - COMPLETELY IGNORE RSA KEYS FROM ENVIRONMENT
# CRITICAL: Override any RSA key configuration that might be in environment variables
# Railway cache invalidation timestamp: 2025-09-01T12:30:00Z
from datetime import timedelta

# POISON PILL: Ensure no RSA keys are used even if present in environment
_jwt_private_key = os.environ.get('JWT_PRIVATE_KEY_B64', '')
_jwt_public_key = os.environ.get('JWT_PUBLIC_KEY_B64', '')
if _jwt_private_key or _jwt_public_key:
    import sys
    print("🚨 CRITICAL ERROR: RSA keys detected in environment!")
    print(f"JWT_PRIVATE_KEY_B64: {'PRESENT' if _jwt_private_key else 'ABSENT'}")
    print(f"JWT_PUBLIC_KEY_B64: {'PRESENT' if _jwt_public_key else 'ABSENT'}")
    print("FORCING HS256 ONLY - RSA keys will be ignored!")

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=3),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',  # FORCED - Never use RS256
    'SIGNING_KEY': os.environ.get('JWT_SECRET_KEY', SECRET_KEY),  # Use HS256 key only
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    # EXPLICITLY DISABLE RSA KEYS
    'VERIFYING_KEY': None,  # Disable RS256 verifying key
    'SIGNING_KEY': os.environ.get('JWT_SECRET_KEY', SECRET_KEY),  # Override any RSA key
}

# Static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging - SIMPLIFIED
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# Security Headers
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Email (if needed)
if os.environ.get('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
