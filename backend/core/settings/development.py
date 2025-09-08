"""
Development settings
"""
from decouple import config

from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')

# JWT Secret Key for development
import os
if not os.environ.get('JWT_SECRET_KEY'):
    os.environ['JWT_SECRET_KEY'] = 'dev-jwt-secret-key-for-development-only-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'testserver']

# Security settings that depend on DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Database with connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='finance_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling - keep connections alive for 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=read\ committed',
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
        },
        'ATOMIC_REQUESTS': True,  # Wrap each request in a transaction
    }
}

# Cache
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default=REDIS_URL)
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default=REDIS_URL)
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=False, cast=bool)

# Celery Beat Schedule for development
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-trial-expirations': {
        'task': 'apps.companies.tasks.check_trial_expirations',
        'schedule': crontab(hour=9, minute=0),  # 9 AM daily
    },
    'reset-monthly-usage': {
        'task': 'apps.companies.tasks.reset_monthly_usage_counters',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),  # First day of month
    },
    'check-usage-limits': {
        'task': 'apps.companies.tasks.check_usage_limits',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

# Override all CORS settings for development
CORS_ALLOW_ALL_HEADERS = True
CORS_ALLOW_ALL_ORIGINS = False  # Keep security, but use explicit origins

# Ensure cache-control header is explicitly allowed
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'cache-control',  # This is the problematic header
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-request-id',
    'pragma',
    'expires',
]

# Force CORS to allow all headers in development
import os
os.environ['CORS_ALLOW_ALL_HEADERS'] = 'True'

# Add CSRF trusted origins for development
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# Email settings
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=1025, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@caixahub.com.br')
SUPPORT_EMAIL = config('SUPPORT_EMAIL', default='suporte@caixahub.com.br')

# Frontend URL
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

# JWT simplified - using standard Bearer tokens only

# OpenAI API
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')

# Open Banking - Pluggy API
PLUGGY_BASE_URL = config('PLUGGY_BASE_URL', default='https://api.pluggy.ai')
PLUGGY_CLIENT_ID = config('PLUGGY_CLIENT_ID', default='')
PLUGGY_CLIENT_SECRET = config('PLUGGY_CLIENT_SECRET', default='')
PLUGGY_USE_SANDBOX = config('PLUGGY_USE_SANDBOX', default=True, cast=bool)
PLUGGY_CONNECT_URL = config('PLUGGY_CONNECT_URL', default='https://connect.pluggy.ai')

# Webhook settings
PLUGGY_WEBHOOK_SECRET = config('PLUGGY_WEBHOOK_SECRET', default='')
PLUGGY_WEBHOOK_URL = config('PLUGGY_WEBHOOK_URL', default='http://localhost:8000/api/banking/webhooks/pluggy/')

# Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
        },
    },
}

# Debug Toolbar
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']

# ===== PAYMENT GATEWAY SETTINGS =====
DEFAULT_PAYMENT_GATEWAY = config('DEFAULT_PAYMENT_GATEWAY', default='stripe')

# Stripe Configuration
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# Validate Stripe Configuration (Warning only in development)
def warn_stripe_configuration():
    """
    Warn about missing Stripe settings in development.
    Only shows warnings - doesn't block development.
    """
    import sys
    
    required_stripe_settings = {
        'STRIPE_PUBLIC_KEY': STRIPE_PUBLIC_KEY,
        'STRIPE_SECRET_KEY': STRIPE_SECRET_KEY, 
        'STRIPE_WEBHOOK_SECRET': STRIPE_WEBHOOK_SECRET,
    }
    
    missing_settings = [name for name, value in required_stripe_settings.items() if not value]
    
    if missing_settings and 'runserver' in sys.argv:
        print("\n⚠️  STRIPE CONFIGURATION WARNING:")
        print("   Missing Stripe environment variables:", ', '.join(missing_settings))
        print("   Payment functionality will be limited.")
        print("   Add to .env file or set environment variables:")
        for setting in missing_settings:
            if setting == 'STRIPE_PUBLIC_KEY':
                print("   STRIPE_PUBLIC_KEY=pk_test_...")
            elif setting == 'STRIPE_SECRET_KEY': 
                print("   STRIPE_SECRET_KEY=sk_test_...")
            elif setting == 'STRIPE_WEBHOOK_SECRET':
                print("   STRIPE_WEBHOOK_SECRET=whsec_...")
        print()

# Show warning for missing Stripe config
warn_stripe_configuration()

# Payment Gateway - Stripe Only (MercadoPago removed for PCI DSS compliance)
# MERCADOPAGO_ACCESS_TOKEN = config('MERCADOPAGO_ACCESS_TOKEN', default='')
# MERCADOPAGO_PUBLIC_KEY = config('MERCADOPAGO_PUBLIC_KEY', default='')
# MERCADOPAGO_WEBHOOK_SECRET = config('MERCADOPAGO_WEBHOOK_SECRET', default='')

# Trial Period Settings
TRIAL_PERIOD_DAYS = config('TRIAL_PERIOD_DAYS', default=14, cast=int)

# Security - Admin endpoints
SEED_PLANS_SECRET = config('SEED_PLANS_SECRET', default='')

# Billing Configuration
ENABLE_AUTO_RENEWAL = config('ENABLE_AUTO_RENEWAL', default=True, cast=bool)
PAYMENT_RETRY_ATTEMPTS = config('PAYMENT_RETRY_ATTEMPTS', default=3, cast=int)
PAYMENT_RETRY_INTERVAL_HOURS = config('PAYMENT_RETRY_INTERVAL_HOURS', default=24, cast=int)

# Email notifications
SEND_PAYMENT_RECEIPTS = config('SEND_PAYMENT_RECEIPTS', default=True, cast=bool)
SEND_TRIAL_EXPIRATION_WARNINGS = config('SEND_TRIAL_EXPIRATION_WARNINGS', default=True, cast=bool)
TRIAL_WARNING_DAYS = [int(x) for x in config('TRIAL_WARNING_DAYS', default='3,7').split(',')]

# Currency Settings
DEFAULT_CURRENCY = config('DEFAULT_CURRENCY', default='BRL')

# Tax settings
APPLY_TAX = config('APPLY_TAX', default=False, cast=bool)
TAX_RATE = config('TAX_RATE', default=0.0, cast=float)

# ===== ADICIONAR MIDDLEWARE DE TRIAL =====
# Adicione após o AuthenticationMiddleware
MIDDLEWARE += [
    'apps.companies.middleware.TrialExpirationMiddleware',
]

# Webhook Security
WEBHOOK_IP_WHITELIST = config('WEBHOOK_IP_WHITELIST', default='').split(',')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Feature Flags
ENABLE_AI_INSIGHTS = config('NEXT_PUBLIC_ENABLE_AI_INSIGHTS', default=True, cast=bool)
ENABLE_OPEN_BANKING = config('NEXT_PUBLIC_ENABLE_OPEN_BANKING', default=True, cast=bool)

# AI Insights Encryption Configuration
if ENABLE_AI_INSIGHTS:
    try:
        from apps.ai_insights.encryption_settings import configure_ai_insights_encryption
        configure_ai_insights_encryption(locals())
    except ImportError:
        # Handle case where AI insights app is not available
        AI_INSIGHTS_ENCRYPTION_KEY = config('AI_INSIGHTS_ENCRYPTION_KEY', default='')

# Site Configuration
SITE_NAME = config('SITE_NAME', default='CaixaHub')
LANGUAGE_CODE = config('LANGUAGE_CODE', default='pt-br')
TIME_ZONE = config('TIME_ZONE', default='America/Sao_Paulo')

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ===== DISABLE RATE LIMITING IN DEVELOPMENT =====
# Override REST_FRAMEWORK settings to disable throttling
from .base import REST_FRAMEWORK
REST_FRAMEWORK = REST_FRAMEWORK.copy()
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []  # Disable all throttling in development

# Optional: Keep specific throttles but with much higher rates
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '10000/hour',
    'user': '10000/hour',
    'api': '10000/hour',
    'burst': '1000/minute',
    'login': '100/hour',
    'registration': '100/hour',
    'report_generation': '100/hour',
    'bank_sync': '200/hour',
    'ai_requests': '1000/month',
    'password_reset': '30/hour',
    'token_refresh': '300/minute',
    '2fa_attempt': '50/minute',
    'email_verification': '30/hour',
    'account_deletion': '10/hour',
    'payment_operations': '300/hour',
    'webhook': '2000/hour'
}

# Enable verbose logging for authentication issues
LOGGING['loggers']['apps.authentication'] = {
    'handlers': ['console', 'file'],
    'level': 'DEBUG',
    'propagate': False,
}
# ===== APLICAR CORREÇÕES DE AUTENTICAÇÃO MVP =====
# Configurações JWT simplificadas para resolver erro de token inválido
from datetime import timedelta

# Sobrescrever configuração JWT existente
SIMPLE_JWT = {
    # Tokens mais longos para reduzir problemas de refresh
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),  # 2 horas ao invés de 30min
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # 7 dias ao invés de 3
    
    # Simplificar rotação de tokens - desabilitar para MVP
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    
    # Algoritmo mais simples e confiável
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': str(SECRET_KEY),  # Garantir que seja string
    
    # Headers mais simples
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # Remover complexidades desnecessárias
    'UPDATE_LAST_LOGIN': False,
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# Aplicar throttles mais permissivos para MVP
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_RATES': {
        'login': '50/hour',        # Mais permissivo
        'api': '2000/hour',        # Menos restritivo
        'burst': '100/minute',     # Permitir mais requisições
        'anon': '10000/hour',
        'user': '10000/hour',
        'report_generation': '100/hour',
        'bank_sync': '200/hour',
        'ai_requests': '1000/month',
        'password_reset': '30/hour',
        'token_refresh': '300/minute',
        '2fa_attempt': '50/minute',
        'email_verification': '30/hour',
        'account_deletion': '10/hour',
        'payment_operations': '300/hour',
        'webhook': '2000/hour'
    }
})

print("✅ Aplicadas correções de autenticação MVP (JWT simplificado)")
