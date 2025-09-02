"""
Production settings for CaixaHub - SIMPLIFIED VERSION
"""
import os
from urllib.parse import urlparse
from django.core.exceptions import ImproperlyConfigured
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
    'healthcheck.railway.app',  # Railway health check
    '*.railway.app',  # Any Railway subdomain
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

# JWT Configuration - SIMPLIFIED (HS256 only for maximum compatibility)
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=3),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',  # Simple and reliable
    'SIGNING_KEY': os.environ.get('JWT_SECRET_KEY', SECRET_KEY),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# JWT Cookie Configuration - FIX for refresh token functionality
JWT_ACCESS_COOKIE_NAME = 'access_token'
JWT_REFRESH_COOKIE_NAME = 'refresh_token'
JWT_COOKIE_SECURE = True      # HTTPS only
JWT_COOKIE_HTTPONLY = True    # Prevent XSS
JWT_COOKIE_SAMESITE = 'None'  # Mobile Safari cross-origin support
JWT_COOKIE_DOMAIN = None      # Browser manages domain
JWT_COOKIE_PATH = '/'         # Available site-wide

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

# Email Configuration - Support multiple backends
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

# Resend Email Backend Configuration
if 'ResendEmailBackend' in EMAIL_BACKEND:
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@caixahub.com.br')
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'suporte@caixahub.com.br')
    print("✅ Using Resend Email Backend")

# SMTP Email Backend Configuration (fallback)
elif EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
    print("✅ Using SMTP Email Backend")

# Console Backend (development fallback)
else:
    print("✅ Using Console Email Backend")

# Rate Limiting Configuration - PRODUCTION FIX
# Disable django_ratelimit in production (too aggressive: 10/min)
# Use DRF throttling instead (10/hour, Redis-backed)
RATELIMIT_ENABLE = False

# Cache Configuration - PRODUCTION FIX (No Redis in Railway)
# Override base.py Redis cache with dummy cache to eliminate connection errors
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Session Configuration - PRODUCTION FIX (JWT-only authentication)
# Disable Django sessions to avoid corruption issues and Redis dependencies
# Use only JWT tokens for authentication (stateless)
SESSION_ENGINE = 'django.contrib.sessions.backends.dummy'
SESSION_SAVE_EVERY_REQUEST = False

# Middleware Configuration - PRODUCTION FIX (Remove session dependencies)
# Override base.py middleware to remove session and message middleware
# Keep only essential middleware for JWT-based authentication
MIDDLEWARE = [
    'core.health_middleware.HealthCheckSSLBypassMiddleware',  # Health checks
    'django.middleware.security.SecurityMiddleware',          # Security headers
    'whitenoise.middleware.WhiteNoiseMiddleware',            # Static files
    'corsheaders.middleware.CorsMiddleware',                 # CORS headers
    'django.middleware.common.CommonMiddleware',             # Common functionality
    'django.middleware.csrf.CsrfViewMiddleware',             # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware', # DRF authentication
    'apps.authentication.middleware.SecurityMiddleware',     # Custom security
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # Clickjacking protection
    # Removed: SessionMiddleware, MessageMiddleware (causes Redis dependency)
]

# Open Banking - Pluggy API Configuration
PLUGGY_BASE_URL = os.environ.get('PLUGGY_BASE_URL', 'https://api.pluggy.ai')
PLUGGY_CLIENT_ID = os.environ.get('PLUGGY_CLIENT_ID', '')
PLUGGY_CLIENT_SECRET = os.environ.get('PLUGGY_CLIENT_SECRET', '')
PLUGGY_USE_SANDBOX = os.environ.get('PLUGGY_USE_SANDBOX', 'false').lower() == 'true'
PLUGGY_CONNECT_URL = os.environ.get('PLUGGY_CONNECT_URL', 'https://connect.pluggy.ai')

# Webhook settings for Pluggy
PLUGGY_WEBHOOK_SECRET = os.environ.get('PLUGGY_WEBHOOK_SECRET', '')
PLUGGY_WEBHOOK_URL = os.environ.get('PLUGGY_WEBHOOK_URL', 'https://your-backend.railway.app/api/banking/webhooks/pluggy/')
