"""
Base settings for CaixaHub project
"""
import os
from datetime import timedelta
from pathlib import Path
from django.core.management.utils import get_random_secret_key

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Custom User Model
AUTH_USER_MODEL = 'authentication.User'

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_yasg',
    'storages',
    'django_celery_beat',
    'django_celery_results',
    'channels',
]

LOCAL_APPS = [
    'apps.authentication',
    'apps.companies',
    'apps.banking',
    'apps.payments',
    'apps.reports',
    'apps.notifications',
    'apps.ai_insights',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'apps.authentication.middleware.SecurityHeadersMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'apps.authentication.middleware.CSRFExemptionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.authentication.middleware.SecureJWTAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # Use ISO 8601 format for dates (default)
    # 'DATETIME_FORMAT': '%d/%m/%Y %H:%M:%S',
    # 'DATE_FORMAT': '%d/%m/%Y',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/minute',
        'register': '3/minute', 
        'password_reset': '5/hour',
        'ai_requests': '10/minute',
        'bank_sync': '20/hour',
        'payment_operations': '30/hour',
        'webhook': '200/hour'
    },
    'EXCEPTION_HANDLER': 'core.error_handlers.custom_exception_handler'
}

# JWT Settings - Enhanced Security
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),  # Reduced for security
    'REFRESH_TOKEN_LIFETIME': timedelta(days=3),     # Reduced for security
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'RS256',  # Enhanced security with asymmetric keys
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_OBTAIN_SERIALIZER': 'apps.authentication.serializers.CustomTokenObtainSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'apps.authentication.serializers.CustomTokenRefreshSerializer',
}

# Celery Configuration
CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Channels Configuration
ASGI_APPLICATION = 'core.asgi.application'

# Enhanced Security Settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_USE_SESSIONS = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'

# JWT Cookie Configuration
JWT_ACCESS_COOKIE_NAME = 'access_token'
JWT_REFRESH_COOKIE_NAME = 'refresh_token'
JWT_COOKIE_SECURE = not DEBUG
JWT_COOKIE_HTTPONLY = True
JWT_COOKIE_SAMESITE = 'Lax'
JWT_COOKIE_PATH = '/'
JWT_COOKIE_DOMAIN = os.environ.get('JWT_COOKIE_DOMAIN', None)

# Request Signing
REQUEST_SIGNING_KEY = os.environ.get('REQUEST_SIGNING_KEY', SECRET_KEY)

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Import logging configuration
from .logging import LOGGING

# JWT Key Configuration
try:
    from core.security import get_jwt_private_key, get_jwt_public_key
    SIMPLE_JWT.update({
        'SIGNING_KEY': get_jwt_private_key(),
        'VERIFYING_KEY': get_jwt_public_key(),
    })
except Exception as e:
    # Fallback to environment variable during development
    import os
    jwt_secret = os.environ.get('JWT_SECRET_KEY')
    if not jwt_secret:
        # Generate a temporary secret for development
        jwt_secret = get_random_secret_key()
        print(f"Warning: Using temporary JWT secret. Set JWT_SECRET_KEY environment variable.")
    
    SIMPLE_JWT.update({
        'ALGORITHM': 'HS256',  # Fallback to symmetric key
        'SIGNING_KEY': jwt_secret,
    })

# Enhanced Security Settings
AUTHENTICATION_BACKENDS = [
    'apps.authentication.backends.EnhancedAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Session Security
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

# Enhanced Password Validation
AUTH_PASSWORD_VALIDATORS.extend([
    {
        'NAME': 'apps.authentication.validators.ComprehensivePasswordValidator',
    },
])

# Rate Limiting Configuration
RATELIMIT_CACHE_BACKEND = 'default'
RATELIMIT_ENABLE = True

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Enhanced Authentication Settings
AUTH_MAX_LOGIN_ATTEMPTS = 3
AUTH_LOCKOUT_DURATION = 3600  # 1 hour
AUTH_ATTEMPT_RESET_PERIOD = 86400  # 24 hours
MAX_SESSIONS_PER_USER = 3
VALIDATE_SESSION_IP = False  # Set to True in production if needed
SESSION_TIMEOUT = 3600  # 1 hour
SESSION_ABSOLUTE_TIMEOUT = 86400  # 24 hours
REMEMBER_ME_LIFETIME = 2592000  # 30 days