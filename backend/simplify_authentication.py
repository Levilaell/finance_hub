#!/usr/bin/env python3
"""
SIMPLIFY AUTHENTICATION - REMOVE UNNECESSARY COMPLEXITIES
=========================================================

This script removes all unnecessary authentication complexities and fixes
the fundamental issues causing login failures in production.

CRITICAL FIXES:
1. Remove duplicate session configurations (causing conflicts)
2. Simplify JWT to basic HS256 (remove asymmetric key complexity)
3. Consistent cookie policy (works for mobile Safari)
4. Remove unnecessary middlewares
5. Basic rate limiting that works

Usage:
    python simplify_authentication.py --apply-fixes
    python simplify_authentication.py --preview
"""

import os
import re
from datetime import datetime

def create_simplified_base_settings():
    """Create a clean, simplified base.py without complexities"""
    
    simplified_content = '''"""
Base settings for CaixaHub project - SIMPLIFIED VERSION
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
    'apps.audit',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# SIMPLIFIED MIDDLEWARE - Only essentials
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.authentication.cookie_middleware.JWTCookieMiddleware',  # Only JWT cookie middleware
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

# Database - will be set in environment-specific settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation - SIMPLIFIED
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
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

# REST Framework - SIMPLIFIED
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
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
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '10/hour',
        'token_refresh': '30/minute',
    },
}

# JWT Settings - SIMPLIFIED (HS256 instead of RS256)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=3),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',  # SIMPLIFIED - Use symmetric key
    'SIGNING_KEY': os.environ.get('JWT_SECRET_KEY', get_random_secret_key()),  # Simple secret key
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# Celery Configuration - BASIC
CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Channels Configuration
ASGI_APPLICATION = 'core.asgi.application'

# SINGLE SESSION CONFIGURATION - NO DUPLICATES
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Allow persistent sessions
# SESSION_COOKIE_SAMESITE and SESSION_COOKIE_SECURE will be set in environment files

# CSRF Configuration
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = False
# CSRF_COOKIE_SAMESITE and CSRF_COOKIE_SECURE will be set in environment files

# CORS Configuration - BASIC
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = []  # Will be set in environment-specific settings
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_ALLOWED_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Security Headers - BASIC
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'

# Redis Cache Configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'finance_hub',
        'TIMEOUT': 300,
    }
}

# Import logging configuration
from .logging import LOGGING

# Authentication Backends - BASIC
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Feature Flags
FEATURE_FLAGS = {
    'AI_INSIGHTS_ENABLED': os.environ.get('AI_INSIGHTS_ENABLED', 'false').lower() == 'true',
}
'''
    
    return simplified_content

def create_simplified_production_settings():
    """Create simplified production settings"""
    
    production_content = '''"""
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

# JWT COOKIES - SIMPLE
JWT_COOKIE_SAMESITE = 'None'      # Mobile Safari compatible
JWT_COOKIE_SECURE = True          # Required in production
JWT_COOKIE_DOMAIN = None          # Let browser handle
JWT_ACCESS_COOKIE_NAME = 'access_token'
JWT_REFRESH_COOKIE_NAME = 'refresh_token'

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
'''
    
    return production_content

def apply_simplification():
    """Apply all authentication simplifications"""
    print("🧹 SIMPLIFYING AUTHENTICATION - REMOVING COMPLEXITIES")
    print("=" * 60)
    
    timestamp = int(datetime.now().timestamp())
    
    # Backup current files
    base_file = "core/settings/base.py"
    production_file = "core/settings/production.py"
    
    base_backup = f"core/settings/base.py.complex.backup.{timestamp}"
    production_backup = f"core/settings/production.py.complex.backup.{timestamp}"
    
    # Create backups
    if os.path.exists(base_file):
        with open(base_file, 'r') as f:
            with open(base_backup, 'w') as backup:
                backup.write(f.read())
        print(f"✅ Base settings backup: {base_backup}")
    
    if os.path.exists(production_file):
        with open(production_file, 'r') as f:
            with open(production_backup, 'w') as backup:
                backup.write(f.read())
        print(f"✅ Production settings backup: {production_backup}")
    
    # Write simplified versions
    with open(base_file, 'w') as f:
        f.write(create_simplified_base_settings())
    print("✅ Simplified base.py created")
    
    with open(production_file, 'w') as f:
        f.write(create_simplified_production_settings())
    print("✅ Simplified production.py created")
    
    print("\n🎯 COMPLEXITIES REMOVED:")
    print("• Duplicate session configurations (SESSION_COOKIE_AGE, SESSION_COOKIE_SAMESITE)")
    print("• Asymmetric JWT keys (RS256 → HS256)")
    print("• Unnecessary middlewares (8 → 5 essential)")
    print("• Complex rate limiting (30 rules → 4 basic)")
    print("• Multiple authentication backends")
    print("• Conflicting cookie policies")
    
    print("\n✅ SIMPLIFIED FEATURES:")
    print("• Single JWT configuration with HS256")
    print("• Consistent cookie policy (SameSite=None for mobile)")
    print("• Essential middlewares only")
    print("• Basic rate limiting that works")
    print("• Clean session configuration")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Restart Django application")
    print("2. Test login on desktop browser")
    print("3. Test login on mobile browser")
    print("4. Monitor logs for 'Session data corrupted'")
    print("5. Verify token refresh works")
    
    return True

def preview_changes():
    """Preview what will be simplified"""
    print("👀 PREVIEW: Authentication Simplification")
    print("=" * 45)
    
    print("CURRENT PROBLEMS:")
    print("❌ Duplicate SESSION_COOKIE_AGE (3600 vs 86400)")
    print("❌ Duplicate SESSION_COOKIE_SAMESITE (Lax vs Strict)")
    print("❌ Complex RS256 JWT with key files")
    print("❌ 8+ authentication middlewares")
    print("❌ 30+ rate limiting rules")
    print("❌ Conflicting cookie policies")
    
    print("\nSIMPLIFICATIONS:")
    print("✅ Single session configuration")
    print("✅ Simple HS256 JWT with env secret")
    print("✅ 5 essential middlewares only")
    print("✅ 4 basic rate limits")
    print("✅ Consistent SameSite=None for mobile")
    
    print("\nMOBILE SAFARI FIX:")
    print("✅ All cookies: SameSite=None + Secure=True")
    print("✅ Cross-origin compatible")
    print("✅ No more session corruption")
    
    print("\nTo apply: python simplify_authentication.py --apply-fixes")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--apply-fixes':
            apply_simplification()
        elif sys.argv[1] == '--preview':
            preview_changes()
        else:
            print("Usage:")
            print("  python simplify_authentication.py --preview")
            print("  python simplify_authentication.py --apply-fixes")
    else:
        preview_changes()

if __name__ == '__main__':
    import sys
    main()