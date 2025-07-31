"""
Enhanced authentication settings for Django
"""
from datetime import timedelta
import os
from cryptography.fernet import Fernet

# Enhanced Authentication Settings

# User Model
AUTH_USER_MODEL = 'authentication.EnhancedUser'

# Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'email', 'first_name', 'last_name'),
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.environ.get('JWT_SECRET_KEY', 'your-secret-key'),
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}

# Encryption Settings
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    # Generate a key for development (NOT for production)
    ENCRYPTION_KEY = Fernet.generate_key()
    print("Warning: Using generated encryption key. Set ENCRYPTION_KEY in production!")

# Session Settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SECURE = True  # Set to False for development
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Rate Limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Authentication Settings
AUTH_MAX_LOGIN_ATTEMPTS = 5
AUTH_LOCKOUT_DURATION = 3600  # 1 hour
AUTH_ATTEMPT_RESET_PERIOD = 86400  # 24 hours
MAX_SESSIONS_PER_USER = 5
SESSION_TIMEOUT = 86400  # 24 hours
SESSION_ABSOLUTE_TIMEOUT = 86400 * 7  # 7 days
REMEMBER_ME_LIFETIME = 86400 * 30  # 30 days
VALIDATE_SESSION_IP = False  # Set to True for stricter security

# Password Policy
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL_CHARS = True
PASSWORD_HISTORY_COUNT = 5
PASSWORD_MAX_AGE_DAYS = 90
PASSWORD_CHECK_BREACHES = True

# Audit Logging
AUDIT_LOGGING_ENABLED = True
LOG_SUCCESSFUL_AUTH_EVENTS = True
LOG_FAILED_AUTH_EVENTS = True
AUDIT_LOG_RETENTION_DAYS = 365
SECURITY_EVENT_RETENTION_DAYS = 730

# OAuth2 Provider Settings
OAUTH2_PROVIDERS = {
    'google': {
        'client_id': os.environ.get('GOOGLE_OAUTH_CLIENT_ID'),
        'client_secret': os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET'),
        'redirect_uri': os.environ.get('GOOGLE_OAUTH_REDIRECT_URI'),
    },
    'facebook': {
        'client_id': os.environ.get('FACEBOOK_OAUTH_CLIENT_ID'),
        'client_secret': os.environ.get('FACEBOOK_OAUTH_CLIENT_SECRET'),
        'redirect_uri': os.environ.get('FACEBOOK_OAUTH_REDIRECT_URI'),
    },
    'github': {
        'client_id': os.environ.get('GITHUB_OAUTH_CLIENT_ID'),
        'client_secret': os.environ.get('GITHUB_OAUTH_CLIENT_SECRET'),
        'redirect_uri': os.environ.get('GITHUB_OAUTH_REDIRECT_URI'),
    },
    'linkedin': {
        'client_id': os.environ.get('LINKEDIN_OAUTH_CLIENT_ID'),
        'client_secret': os.environ.get('LINKEDIN_OAUTH_CLIENT_SECRET'),
        'redirect_uri': os.environ.get('LINKEDIN_OAUTH_REDIRECT_URI'),
    },
}

# GeoIP Settings (for location detection)
GEOIP_PATH = os.path.join(os.path.dirname(__file__), 'geoip')

# Email Settings for Authentication
EMAIL_VERIFICATION_LIFETIME = timedelta(days=7)
PASSWORD_RESET_LIFETIME = timedelta(hours=2)

# 2FA Settings
TOTP_ISSUER_NAME = os.environ.get('TOTP_ISSUER_NAME', 'Finance Hub')
BACKUP_CODES_COUNT = 10

# Device Trust Settings
DEVICE_TRUST_LIFETIME = timedelta(days=30)
MAX_TRUSTED_DEVICES = 10

# Anomaly Detection Thresholds
RISK_SCORE_THRESHOLDS = {
    'low': 0.3,
    'medium': 0.5,
    'high': 0.7,
    'critical': 0.9,
}

# Security Alert Settings
SECURITY_ALERT_EMAIL = os.environ.get('SECURITY_ALERT_EMAIL')
SECURITY_ALERT_SLACK_WEBHOOK = os.environ.get('SECURITY_ALERT_SLACK_WEBHOOK')

# Logging Configuration for Authentication
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'auth_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/authentication.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/audit.log',
            'maxBytes': 52428800,  # 50MB
            'backupCount': 20,
            'formatter': 'json',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.authentication': {
            'handlers': ['auth_file', 'security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.authentication.security': {
            'handlers': ['security_file', 'audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.authentication.audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Cache Configuration for Authentication
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'finance_hub_auth',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Celery Configuration for Async Tasks
CELERY_TASK_ROUTES = {
    'apps.authentication.tasks.send_verification_email': {'queue': 'auth'},
    'apps.authentication.tasks.send_password_reset_email': {'queue': 'auth'},
    'apps.authentication.tasks.cleanup_expired_tokens': {'queue': 'maintenance'},
    'apps.authentication.tasks.generate_security_report': {'queue': 'reports'},
}

# API Throttling for Authentication
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '10/min',
        'register': '5/min',
        'password_reset': '3/hour',
        '2fa': '20/min',
    }
}

# Security Headers Middleware
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_TLS = True

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = ("'self'",)
CSP_FONT_SRC = ("'self'",)
CSP_BASE_URI = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)

# Additional Security Settings
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

# Database Settings for Authentication
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'finance_hub'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'prefer',
        },
    }
}

# Time Zone
USE_TZ = True
TIME_ZONE = 'UTC'

# Internationalization
USE_I18N = True
USE_L10N = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(os.path.dirname(__file__), 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Default Auto Field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'