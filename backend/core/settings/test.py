"""
Test environment settings
"""
import os

# Set environment variables before imports
os.environ.setdefault('OPENAI_API_KEY', 'test-key-not-for-real-use')
os.environ.setdefault('AI_INSIGHTS_ENCRYPTION_KEY', 'test-encryption-key-32-chars-long!!!')
os.environ.setdefault('JWT_SECRET_KEY', 'test-jwt-secret-key')
os.environ.setdefault('PLUGGY_CLIENT_ID', 'test-pluggy-client-id')
os.environ.setdefault('PLUGGY_CLIENT_SECRET', 'test-pluggy-client-secret')

# First import base settings
from .base import *

# Then override problematic imports
import logging.config
logging.config.dictConfig = lambda x: None  # Disable logging configuration

# Override database configuration for tests (use SQLite in memory)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations during tests for speed
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

# Enable this to run without migrations (faster tests)
MIGRATION_MODULES = DisableMigrations()

# Use in-memory cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Disable Celery during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Speed up password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable rate limiting in tests
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []

# Test-specific settings
SECRET_KEY = 'test-secret-key-for-testing-only'
DEBUG = False
ALLOWED_HOSTS = ['*']

# Test environment variables (already set above)

# Pluggy API settings for tests
PLUGGY_BASE_URL = 'https://api.pluggy.ai'
PLUGGY_CLIENT_ID = 'test-pluggy-client-id'
PLUGGY_CLIENT_SECRET = 'test-pluggy-client-secret'
PLUGGY_USE_SANDBOX = True
PLUGGY_CONNECT_URL = 'https://connect.pluggy.ai'
PLUGGY_WEBHOOK_SECRET = 'test-webhook-secret'
PLUGGY_WEBHOOK_URL = 'http://localhost:8000/api/banking/webhooks/pluggy/'

# Disable email sending
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Keep all apps for testing
# INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'apps.ai_insights']

# Use test-specific URL config (excludes ai_insights)
ROOT_URLCONF = 'core.urls_test'

# Disable problematic logging
LOGGING_CONFIG = None
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
    },
}