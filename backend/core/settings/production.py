"""
Production settings
"""
import os

from decouple import config

from .base import *

# Import sentry only if configured
try:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

# Security
# Check if we have a SECRET_KEY, provide helpful error if not
SECRET_KEY = config('DJANGO_SECRET_KEY', default=None)
if not SECRET_KEY:
    # Generate a temporary key for collectstatic and health checks
    if os.environ.get('DJANGO_COLLECT_STATIC') == '1':
        SECRET_KEY = 'temporary-key-for-collectstatic-only'
    else:
        import sys
        print("ERROR: DJANGO_SECRET_KEY environment variable is required in production!")
        print("Please set it in Railway dashboard under Variables section.")
        print("You can generate one with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'")
        # Use a temporary key to allow health checks to work
        SECRET_KEY = 'INSECURE-TEMPORARY-KEY-PLEASE-SET-DJANGO_SECRET_KEY'
        
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')  # Allow all hosts temporarily

# Database - Correção principal aqui!
import dj_database_url

DATABASE_URL = config('DATABASE_URL', default=None)
if not DATABASE_URL:
    # Check if this is during collectstatic
    if os.environ.get('DJANGO_COLLECT_STATIC') == '1':
        DATABASE_URL = 'postgres://dummy:dummy@dummy:5432/dummy'
    else:
        print("WARNING: DATABASE_URL environment variable is not set!")
        print("Using a dummy database URL - database operations will fail.")
        print("Please set DATABASE_URL in Railway dashboard.")
        DATABASE_URL = 'postgres://dummy:dummy@localhost:5432/dummy'

DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Redis
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379')

# Cache configuration
if REDIS_URL and REDIS_URL != 'redis://localhost:6379':
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
            }
        }
    }
    # Celery
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
else:
    # Use dummy cache if Redis not available
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

# Static files - WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files - AWS S3 (optional)
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
if AWS_ACCESS_KEY_ID:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = None
    AWS_S3_VERIFY = True
else:
    # Use local media storage if AWS not configured
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    MEDIA_URL = '/media/'

# Security - Ajustado para Railway
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Importante para Railway!

# CORS - Production Security Configuration
cors_origins = config('CORS_ALLOWED_ORIGINS', default='')
if cors_origins:
    # Only allow HTTPS origins in production
    allowed_origins = []
    for origin in cors_origins.split(','):
        origin = origin.strip()
        if origin and origin.startswith('https://'):
            allowed_origins.append(origin)
        elif origin and not origin.startswith('http'):
            # Allow domain without protocol, assume HTTPS
            allowed_origins.append(f'https://{origin}')
    
    CORS_ALLOWED_ORIGINS = allowed_origins
else:
    CORS_ALLOWED_ORIGINS = []

# Never allow all origins in production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

# Additional CORS security for production
# CORS_REPLACE_HTTPS_REFERER = True  # Removed - deprecated in django-cors-headers
CORS_ORIGIN_ALLOW_ALL = False

# CSRF - Secure configuration for production
csrf_origins = config('CORS_ALLOWED_ORIGINS', default='')
if csrf_origins:
    # Only allow HTTPS origins for CSRF
    trusted_origins = []
    for origin in csrf_origins.split(','):
        origin = origin.strip()
        if origin and origin.startswith('https://'):
            trusted_origins.append(origin)
        elif origin and not origin.startswith('http'):
            trusted_origins.append(f'https://{origin}')
    
    CSRF_TRUSTED_ORIGINS = trusted_origins
else:
    CSRF_TRUSTED_ORIGINS = []

# Email settings
EMAIL_HOST = config('EMAIL_HOST', default='')
if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = config('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@caixahub.com.br')
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
else:
    # Use console backend for development/testing
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@caixahub.com.br'
    SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Frontend URL
FRONTEND_URL = config('FRONTEND_URL', default='https://finance-frontend-production-24be.up.railway.app')

# OpenAI API
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')

# Open Banking API
OPEN_BANKING_CLIENT_ID = config('OPEN_BANKING_CLIENT_ID', default='')
OPEN_BANKING_CLIENT_SECRET = config('OPEN_BANKING_CLIENT_SECRET', default='')

# Pluggy API Settings
PLUGGY_BASE_URL = config('PLUGGY_BASE_URL', default='https://api.pluggy.ai')
PLUGGY_CLIENT_ID = config('PLUGGY_CLIENT_ID', default='')
PLUGGY_CLIENT_SECRET = config('PLUGGY_CLIENT_SECRET', default='')
PLUGGY_USE_SANDBOX = config('PLUGGY_USE_SANDBOX', default=False, cast=bool)
PLUGGY_CONNECT_URL = config('PLUGGY_CONNECT_URL', default='https://connect.pluggy.ai')

# Webhook settings
PLUGGY_WEBHOOK_SECRET = config('PLUGGY_WEBHOOK_SECRET', default='')
PLUGGY_WEBHOOK_URL = config('PLUGGY_WEBHOOK_URL', default='')

# Sentry
if SENTRY_AVAILABLE and config('SENTRY_DSN', default=''):
    sentry_sdk.init(
        dsn=config('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )

# Channels
if REDIS_URL and REDIS_URL != 'redis://localhost:6379':
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [REDIS_URL],
                "capacity": 1500,
                "expiry": 10,
            },
        },
    }
else:
    # Use in-memory channel layer if Redis not available
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# Logging - Ajustado para Railway
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
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.security.DisallowedHost': {
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

# Performance
CONN_MAX_AGE = 60

# ===== PAYMENT GATEWAY SETTINGS =====
# Payment Gateway Settings
DEFAULT_PAYMENT_GATEWAY = config('DEFAULT_PAYMENT_GATEWAY', default='stripe')

# Stripe Configuration
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# Payment Gateway - Stripe Only (MercadoPago removed for PCI DSS compliance)
# MERCADOPAGO_ACCESS_TOKEN = config('MERCADOPAGO_ACCESS_TOKEN', default='')
# MERCADOPAGO_PUBLIC_KEY = config('MERCADOPAGO_PUBLIC_KEY', default='')

# Trial Period Settings
DEFAULT_TRIAL_DAYS = config('TRIAL_PERIOD_DAYS', default=14, cast=int)

# Currency Settings
DEFAULT_CURRENCY = config('DEFAULT_CURRENCY', default='BRL')

# Railway specific settings
if os.environ.get('RAILWAY_ENVIRONMENT'):
    # Force HTTPS for all requests
    SECURE_SSL_REDIRECT = True
    # Trust Railway's proxy headers
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True