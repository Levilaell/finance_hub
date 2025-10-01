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

os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'testserver', 'bunny-bitterish-photodynamically.ngrok-free.dev', 'unnumerously-unchampioned-karla.ngrok-free.dev']

# Security settings that depend on DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Database with connection pooling and encoding fix
# Use environment variable to switch between PostgreSQL and SQLite for development

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='caixahub_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'options': '-c client_encoding=UTF8',
        },
    }
}


# Cache
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')


# Celery
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default=REDIS_URL)
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default=REDIS_URL)
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=False, cast=bool)

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

# Frontend URL
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

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

# Stripe Configuration
STRIPE_LIVE_MODE = config('STRIPE_LIVE_MODE', default=False, cast=bool)
STRIPE_TEST_SECRET_KEY = config('STRIPE_TEST_SECRET_KEY', default='')
STRIPE_LIVE_SECRET_KEY = config('STRIPE_LIVE_SECRET_KEY', default='')
STRIPE_TEST_PUBLIC_KEY = config('STRIPE_TEST_PUBLIC_KEY', default='')
STRIPE_LIVE_PUBLIC_KEY = config('STRIPE_LIVE_PUBLIC_KEY', default='')

# Legacy support (backwards compatibility)
STRIPE_PUBLIC_KEY = STRIPE_TEST_PUBLIC_KEY if not STRIPE_LIVE_MODE else STRIPE_LIVE_PUBLIC_KEY
STRIPE_SECRET_KEY = STRIPE_TEST_SECRET_KEY if not STRIPE_LIVE_MODE else STRIPE_LIVE_SECRET_KEY
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# dj-stripe configuration
DJSTRIPE_WEBHOOK_SECRET = config('DJSTRIPE_WEBHOOK_SECRET', default=STRIPE_WEBHOOK_SECRET)
DJSTRIPE_FOREIGN_KEY_TO_FIELD = 'id'
DJSTRIPE_USE_NATIVE_JSONFIELD = True
DJSTRIPE_SUBSCRIBER_MODEL = 'authentication.User'

# Stripe Default Price ID
STRIPE_DEFAULT_PRICE_ID = config('STRIPE_DEFAULT_PRICE_ID', default='')

# Validate Stripe Configuration (Warning only in development)
def warn_stripe_configuration():
    """
    Warn about missing Stripe settings in development.
    Only shows warnings - doesn't block development.
    """
    import sys

    required_stripe_settings = {
        'STRIPE_TEST_SECRET_KEY': STRIPE_TEST_SECRET_KEY,
        'STRIPE_TEST_PUBLIC_KEY': STRIPE_TEST_PUBLIC_KEY,
        'DJSTRIPE_WEBHOOK_SECRET': DJSTRIPE_WEBHOOK_SECRET,
    }

    missing_settings = [name for name, value in required_stripe_settings.items() if not value]

    if missing_settings and 'runserver' in sys.argv:
        print("\n⚠️  STRIPE CONFIGURATION WARNING:")
        print("   Missing Stripe environment variables:", ', '.join(missing_settings))
        print("   Payment functionality will be limited.")
        print("   Add to .env file or set environment variables:")
        for setting in missing_settings:
            if setting == 'STRIPE_TEST_PUBLIC_KEY':
                print("   STRIPE_TEST_PUBLIC_KEY=pk_test_...")
            elif setting == 'STRIPE_TEST_SECRET_KEY':
                print("   STRIPE_TEST_SECRET_KEY=sk_test_...")
            elif setting == 'DJSTRIPE_WEBHOOK_SECRET':
                print("   DJSTRIPE_WEBHOOK_SECRET=whsec_...")
        print()

# Show warning for missing Stripe config
warn_stripe_configuration()

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

# Site Configuration
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

