"""
Logging configuration for Finance Hub
"""
import os
from pathlib import Path

# Base dir for logs
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = BASE_DIR / 'logs'

# Create logs directory if it doesn't exist
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'detailed': {
            'format': '[{levelname}] {asctime} [{name}:{lineno}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'django.log'),
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'errors.log'),
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'detailed',
        },
        'pluggy_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'pluggy.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed',
        },
        'banking_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'banking.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file'],
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps.banking': {
            'handlers': ['console', 'banking_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.banking.pluggy_client': {
            'handlers': ['console', 'pluggy_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.banking.pluggy_sync_service': {
            'handlers': ['console', 'pluggy_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.banking.pluggy_views': {
            'handlers': ['console', 'pluggy_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.payments': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}