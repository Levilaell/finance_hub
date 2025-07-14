"""
Test settings
"""
from .base import *

SECRET_KEY = 'test-secret-key'
DEBUG = False
ALLOWED_HOSTS = ['testserver']

# Use SQLite for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Simple cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Celery - run synchronously during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Email
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Frontend URL
FRONTEND_URL = 'http://testserver:3000'

# Test API Keys
OPENAI_API_KEY = 'test-openai-key'
OPEN_BANKING_CLIENT_ID = 'test-client-id'
OPEN_BANKING_CLIENT_SECRET = 'test-client-secret'

# Pluggy API Settings (Test)
PLUGGY_BASE_URL = 'https://api.pluggy.ai'
PLUGGY_CLIENT_ID = 'test-pluggy-client-id'
PLUGGY_CLIENT_SECRET = 'test-pluggy-client-secret'
PLUGGY_USE_SANDBOX = True

# Disable migrations during tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Password hashers - use faster hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Media files
MEDIA_ROOT = '/tmp/test_media/'

# Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# Payment Gateway Settings (Test)
DEFAULT_PAYMENT_GATEWAY = 'stripe'

# Stripe Configuration (Test)
STRIPE_PUBLIC_KEY = 'pk_test_'
STRIPE_SECRET_KEY = 'sk_test_'
STRIPE_WEBHOOK_SECRET = 'whsec_test_'

# MercadoPago Configuration (Test)
MERCADOPAGO_ACCESS_TOKEN = 'TEST-access-token'
MERCADOPAGO_PUBLIC_KEY = 'TEST-public-key'

# Trial Period Settings
DEFAULT_TRIAL_DAYS = 14

# Currency Settings
DEFAULT_CURRENCY = 'BRL'