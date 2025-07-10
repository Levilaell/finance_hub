"""
Development settings
"""
from decouple import config

from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'testserver']

# Database - SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Optional PostgreSQL for development (uncomment if you have PostgreSQL running locally)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME', default='caixa_digital'),
#         'USER': config('DB_USER', default='postgres'),
#         'PASSWORD': config('DB_PASSWORD', default='postgres'),
#         'HOST': config('DB_HOST', default='localhost'),
#         'PORT': config('DB_PORT', default='5432'),
#     }
# }

# Cache - Simple cache for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Optional Redis for development (uncomment if you have Redis running locally)
# REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': REDIS_URL,
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         }
#     }
# }

# Celery - Disabled for development
# CELERY_BROKER_URL = REDIS_URL
# CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_ALWAYS_EAGER = True

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://frontend:3000",
]

CORS_ALLOW_CREDENTIALS = True

# Email settings (console backend for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Frontend URL
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

# OpenAI API
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')

# Open Banking API (Mock)
OPEN_BANKING_CLIENT_ID = config('OPEN_BANKING_CLIENT_ID', default='mock-client-id')
OPEN_BANKING_CLIENT_SECRET = config('OPEN_BANKING_CLIENT_SECRET', default='mock-client-secret')

# Pluggy API Settings (Sandbox)
PLUGGY_BASE_URL = config('PLUGGY_BASE_URL', default='https://api.pluggy.ai')
PLUGGY_CLIENT_ID = config('PLUGGY_CLIENT_ID', default='test-client-id')
PLUGGY_CLIENT_SECRET = config('PLUGGY_CLIENT_SECRET', default='test-client-secret')

# Channels - In-memory for development
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Debug Toolbar
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']

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
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}