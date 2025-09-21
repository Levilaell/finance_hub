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

# SESSION/CSRF COOKIES - SIMPLIFIED (not used for JWT auth)
SESSION_COOKIE_SAMESITE = 'Lax'   # Standard same-origin policy
SESSION_COOKIE_SECURE = True      # HTTPS only
CSRF_COOKIE_SAMESITE = 'Lax'      # Standard same-origin policy  
CSRF_COOKIE_SECURE = True         # HTTPS only

# JWT Configuration - SIMPLIFIED (HS256 only for maximum compatibility)
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=3),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',  # Simple and reliable
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
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

# Cache Configuration - PRODUCTION FIX (No Redis in Railway)
# Override base.py Redis cache with dummy cache to eliminate connection errors
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Session Configuration - PRODUCTION FIX (JWT-only authentication)
# Use signed_cookies session backend (no external dependencies, no Redis)
# Lightweight sessions stored in browser cookies, no server-side persistence
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_AGE = 300  # 5 minutes (short-lived since JWT is primary auth)

# Middleware Configuration - PRODUCTION FIX (Keep required middleware with dummy backends)
# Django's AuthenticationMiddleware REQUIRES SessionMiddleware to function
# Admin app REQUIRES both SessionMiddleware and MessageMiddleware
# Solution: Keep middleware but use dummy backends (no persistence, no Redis)
MIDDLEWARE = [
    'core.health_middleware.HealthCheckSSLBypassMiddleware',  # Health checks
    'django.middleware.security.SecurityMiddleware',          # Security headers
    'whitenoise.middleware.WhiteNoiseMiddleware',            # Static files
    'corsheaders.middleware.CorsMiddleware',                 # CORS headers
    'django.contrib.sessions.middleware.SessionMiddleware',  # REQUIRED by AuthenticationMiddleware
    'django.middleware.common.CommonMiddleware',             # Common functionality
    'django.middleware.csrf.CsrfViewMiddleware',             # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware', # DRF authentication
    'django.contrib.messages.middleware.MessageMiddleware',  # REQUIRED by admin
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # Clickjacking protection
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
