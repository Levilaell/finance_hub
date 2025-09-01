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

# JWT simplified - using standard Bearer tokens only

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
