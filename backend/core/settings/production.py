"""
Production settings
"""
import os
import sys

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
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', None)
if not SECRET_KEY:
    # Generate a temporary key for collectstatic and health checks
    if os.environ.get('DJANGO_COLLECT_STATIC') == '1':
        SECRET_KEY = 'temporary-key-for-collectstatic-only'
    else:
        print("ERROR: DJANGO_SECRET_KEY environment variable is required in production!")
        print("Please set it in Railway dashboard under Variables section.")
        print("You can generate one with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'")
        # Use a temporary key to allow health checks to work
        SECRET_KEY = 'INSECURE-TEMPORARY-KEY-PLEASE-SET-DJANGO_SECRET_KEY'

# Debug mode - always False in production unless explicitly set
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')

# Allowed hosts - Parse from environment and add Railway-specific hosts
allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', '*')
if allowed_hosts_env == '*':
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',') if host.strip()]

# Always allow Railway health check host
ALLOWED_HOSTS.extend([
    'healthcheck.railway.app',  # Railway health check
    '.railway.app',  # All Railway subdomains
    'localhost',  # For local testing
    '127.0.0.1',  # For local testing
])

# Database - Correção principal aqui!
import dj_database_url

DATABASE_URL = os.environ.get('DATABASE_URL', None)

# Check if DATABASE_URL contains unresolved Railway template variables
if DATABASE_URL and '{{' in DATABASE_URL:
    print("ERROR: DATABASE_URL contains unresolved Railway template variables!")
    print(f"Current value: {DATABASE_URL}")
    print("This usually means the reference variable isn't configured correctly.")
    print("Please check Railway dashboard and ensure the database service reference is set properly.")
    DATABASE_URL = None

if not DATABASE_URL:
    # Check if this is during collectstatic
    if os.environ.get('DJANGO_COLLECT_STATIC') == '1':
        DATABASE_URL = 'postgres://dummy:dummy@dummy:5432/dummy'
    else:
        print("WARNING: DATABASE_URL environment variable is not set or invalid!")
        print("Using a dummy database URL - database operations will fail.")
        print("Please set DATABASE_URL in Railway dashboard.")
        print("Use the reference button to link to your database service.")
        DATABASE_URL = 'postgres://dummy:dummy@localhost:5432/dummy'

DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Redis
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')

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

# Static files - WhiteNoise with fallback
try:
    # Try compressed storage first
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
except Exception:
    # Fallback to basic WhiteNoise if compression fails
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Media files - AWS S3 (optional)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
if AWS_ACCESS_KEY_ID:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
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
# Disable SSL redirect completely - Railway handles SSL termination at the edge
# Health checks from Railway come via HTTP internally
SECURE_SSL_REDIRECT = False  # Never redirect to HTTPS - Railway handles this
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() in ('true', '1', 'yes')
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'True').lower() in ('true', '1', 'yes')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Importante para Railway!

# CORS - Production Security Configuration
cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
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
csrf_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
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
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@caixahub.com.br')
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
else:
    # Use console backend for development/testing
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@caixahub.com.br'
    SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Frontend URL (updated above with JWT cookie configuration)

# OpenAI API
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# AI Insights Encryption Key
AI_INSIGHTS_ENCRYPTION_KEY = os.environ.get('AI_INSIGHTS_ENCRYPTION_KEY', '')

# Open Banking API
OPEN_BANKING_CLIENT_ID = os.environ.get('OPEN_BANKING_CLIENT_ID', '')
OPEN_BANKING_CLIENT_SECRET = os.environ.get('OPEN_BANKING_CLIENT_SECRET', '')

# Pluggy API Settings
PLUGGY_BASE_URL = os.environ.get('PLUGGY_BASE_URL', 'https://api.pluggy.ai')
PLUGGY_CLIENT_ID = os.environ.get('PLUGGY_CLIENT_ID', '')
PLUGGY_CLIENT_SECRET = os.environ.get('PLUGGY_CLIENT_SECRET', '')
PLUGGY_USE_SANDBOX = os.environ.get('PLUGGY_USE_SANDBOX', 'False').lower() in ('true', '1', 'yes')
PLUGGY_CONNECT_URL = os.environ.get('PLUGGY_CONNECT_URL', 'https://connect.pluggy.ai')

# Webhook settings
PLUGGY_WEBHOOK_SECRET = os.environ.get('PLUGGY_WEBHOOK_SECRET', '')
PLUGGY_WEBHOOK_URL = os.environ.get('PLUGGY_WEBHOOK_URL', '')

# Sentry
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
if SENTRY_AVAILABLE and SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )

# Session configuration - use database backend in production
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400 * 7  # 7 days
SESSION_SAVE_EVERY_REQUEST = True

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
DEFAULT_PAYMENT_GATEWAY = os.environ.get('DEFAULT_PAYMENT_GATEWAY', 'stripe')

# Stripe Configuration
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# Validate Stripe Configuration
def validate_stripe_configuration():
    """
    Validate that all required Stripe settings are configured.
    Raises ImproperlyConfigured if any required settings are missing.
    """
    from django.core.exceptions import ImproperlyConfigured
    
    required_stripe_settings = {
        'STRIPE_PUBLIC_KEY': STRIPE_PUBLIC_KEY,
        'STRIPE_SECRET_KEY': STRIPE_SECRET_KEY,
        'STRIPE_WEBHOOK_SECRET': STRIPE_WEBHOOK_SECRET,
    }
    
    missing_settings = []
    invalid_settings = []
    
    for setting_name, setting_value in required_stripe_settings.items():
        if not setting_value:
            missing_settings.append(setting_name)
        elif setting_name == 'STRIPE_SECRET_KEY' and not setting_value.startswith('sk_'):
            invalid_settings.append(f"{setting_name} should start with 'sk_'")
        elif setting_name == 'STRIPE_PUBLIC_KEY' and not setting_value.startswith('pk_'):
            invalid_settings.append(f"{setting_name} should start with 'pk_'")
        elif setting_name == 'STRIPE_WEBHOOK_SECRET' and not setting_value.startswith('whsec_'):
            invalid_settings.append(f"{setting_name} should start with 'whsec_'")
    
    errors = []
    if missing_settings:
        errors.append(f"Missing required Stripe environment variables: {', '.join(missing_settings)}")
    if invalid_settings:
        errors.append(f"Invalid Stripe configuration: {', '.join(invalid_settings)}")
    
    if errors:
        error_message = "\n".join([
            "❌ STRIPE CONFIGURATION ERROR:",
            *[f"   • {error}" for error in errors],
            "",
            "📋 Required environment variables:",
            "   • STRIPE_PUBLIC_KEY=pk_test_... or pk_live_...",
            "   • STRIPE_SECRET_KEY=sk_test_... or sk_live_...",
            "   • STRIPE_WEBHOOK_SECRET=whsec_...",
            "",
            "💡 Set these in your Railway dashboard under Variables section",
            "   or in your .env file for local development"
        ])
        raise ImproperlyConfigured(error_message)

# Only validate Stripe in production if not running collectstatic
if not os.environ.get('DJANGO_COLLECT_STATIC') and DEFAULT_PAYMENT_GATEWAY == 'stripe':
    validate_stripe_configuration()

# Payment Gateway - Stripe Only (MercadoPago removed for PCI DSS compliance)
# MERCADOPAGO_ACCESS_TOKEN = os.environ.get('MERCADOPAGO_ACCESS_TOKEN', '')
# MERCADOPAGO_PUBLIC_KEY = os.environ.get('MERCADOPAGO_PUBLIC_KEY', '')

# Trial Period Settings
DEFAULT_TRIAL_DAYS = int(os.environ.get('TRIAL_PERIOD_DAYS', '14'))

# Currency Settings
DEFAULT_CURRENCY = os.environ.get('DEFAULT_CURRENCY', 'BRL')

# Railway specific settings
if os.environ.get('RAILWAY_ENVIRONMENT'):
    # Force HTTPS for all requests
    SECURE_SSL_REDIRECT = True
    # Trust Railway's proxy headers
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True

# ===== JWT COOKIE CONFIGURATION FOR CROSS-ORIGIN =====
# Configure JWT cookies for cross-origin requests in production
# Frontend and backend are on different Railway subdomains
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://financehub-frontend-production.up.railway.app')
BACKEND_URL = os.environ.get('BACKEND_URL', 'https://financehub-production.up.railway.app')

# Check if frontend and backend are on different domains
from urllib.parse import urlparse
try:
    frontend_domain = urlparse(FRONTEND_URL).netloc
    backend_domain = urlparse(BACKEND_URL).netloc
    is_cross_origin = frontend_domain != backend_domain
    
    if is_cross_origin:
        # Cross-origin setup requires SameSite=None and Secure=True
        JWT_COOKIE_SAMESITE = 'None'
        JWT_COOKIE_SECURE = True
        JWT_COOKIE_DOMAIN = None  # Let browser handle domain
        
        print(f"✅ Cross-origin JWT cookies configured:")
        print(f"   Frontend: {frontend_domain}")
        print(f"   Backend: {backend_domain}")
        print(f"   SameSite: None, Secure: True")
    else:
        # Same-origin setup can use more restrictive settings
        JWT_COOKIE_SAMESITE = 'Lax'
        JWT_COOKIE_SECURE = True
        JWT_COOKIE_DOMAIN = None
        
        print(f"✅ Same-origin JWT cookies configured:")
        print(f"   Domain: {frontend_domain}")
        print(f"   SameSite: Lax, Secure: True")
        
except Exception as e:
    # Fallback to cross-origin settings for safety
    JWT_COOKIE_SAMESITE = 'None'
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_DOMAIN = None
    print(f"⚠️  URL parsing failed, using cross-origin defaults: {e}")

# JWT Cookie Names
JWT_ACCESS_COOKIE_NAME = 'access_token'
JWT_REFRESH_COOKIE_NAME = 'refresh_token'

# ===== SECURITY VALIDATION =====
# Validate security configuration on startup
if not os.environ.get('DJANGO_COLLECT_STATIC'):
    try:
        from core.security_validator import validate_security_on_startup
        validate_security_on_startup()
    except ImportError:
        print("⚠️  Security validator not available")