"""
Production Configuration for AI Insights
Settings and configurations optimized for production deployment
"""

# AI Insights Production Settings
AI_INSIGHTS_PRODUCTION_CONFIG = {
    # Rate Limiting
    'RATE_LIMITS': {
        'ai_operations': '100/hour',  # Max 100 AI operations per hour per user
        'websocket_messages': '60/minute',  # Max 60 WebSocket messages per minute
        'credit_purchases': '10/hour',  # Max 10 credit purchases per hour
    },
    
    # WebSocket Configuration
    'WEBSOCKET': {
        'CONNECTION_TIMEOUT': 300,  # 5 minutes
        'MESSAGE_SIZE_LIMIT': 4000,  # 4KB max message size
        'MAX_CONNECTIONS_PER_USER': 5,  # Max concurrent connections
        'HEARTBEAT_INTERVAL': 30,  # Seconds
    },
    
    # AI Service Configuration
    'AI_SERVICE': {
        'DEFAULT_MODEL': 'gpt-4o-mini',  # Cost-effective default
        'MAX_TOKENS': 2000,  # Response limit
        'TEMPERATURE': 0.7,  # Creativity vs consistency
        'TIMEOUT': 30,  # API timeout in seconds
        'RETRY_ATTEMPTS': 3,  # Retry failed requests
    },
    
    # Credit System
    'CREDITS': {
        'WELCOME_BONUS': 10,  # New user bonus
        'MONTHLY_RESET_DAY': 1,  # Day of month to reset
        'LOW_BALANCE_THRESHOLD': 5,  # Warning threshold
        'EMERGENCY_CREDITS': 3,  # Emergency allocation
    },
    
    # Monitoring & Logging
    'MONITORING': {
        'LOG_LEVEL': 'INFO',
        'ENABLE_METRICS': True,
        'METRIC_RETENTION_DAYS': 90,
        'ERROR_TRACKING': True,
        'PERFORMANCE_MONITORING': True,
    },
    
    # Cache Settings
    'CACHE': {
        'FINANCIAL_CONTEXT_TTL': 1800,  # 30 minutes
        'CREDIT_BALANCE_TTL': 300,  # 5 minutes
        'INSIGHT_CACHE_TTL': 3600,  # 1 hour
        'CONVERSATION_CACHE_TTL': 900,  # 15 minutes
    },
    
    # Security
    'SECURITY': {
        'ENABLE_AUDIT_LOG': True,
        'JWT_TOKEN_VALIDATION': True,
        'IP_WHITELIST_ENABLED': False,  # Set to True in high-security environments
        'REQUIRE_2FA_FOR_PURCHASES': False,  # Can be enabled for additional security
    },
    
    # Performance
    'PERFORMANCE': {
        'DATABASE_CONNECTION_POOLING': True,
        'ASYNC_PROCESSING': True,
        'BATCH_OPERATIONS': True,
        'COMPRESSION_ENABLED': True,
    },
    
    # Feature Flags
    'FEATURES': {
        'AUTOMATED_INSIGHTS': True,
        'EXPORT_FUNCTIONS': True,
        'CONVERSATION_EXPORT': True,
        'REAL_TIME_NOTIFICATIONS': True,
        'ADVANCED_ANALYTICS': True,
    }
}

# Django Settings Integration
def configure_ai_insights_production(settings_dict):
    """
    Configure Django settings for AI Insights production deployment
    
    Args:
        settings_dict: Django settings dictionary to update
    """
    config = AI_INSIGHTS_PRODUCTION_CONFIG
    
    # Throttling Configuration
    if 'REST_FRAMEWORK' not in settings_dict:
        settings_dict['REST_FRAMEWORK'] = {}
    
    if 'DEFAULT_THROTTLE_CLASSES' not in settings_dict['REST_FRAMEWORK']:
        settings_dict['REST_FRAMEWORK']['DEFAULT_THROTTLE_CLASSES'] = []
    
    settings_dict['REST_FRAMEWORK']['DEFAULT_THROTTLE_CLASSES'].extend([
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'apps.ai_insights.views.AIInsightsRateThrottle',
    ])
    
    if 'DEFAULT_THROTTLE_RATES' not in settings_dict['REST_FRAMEWORK']:
        settings_dict['REST_FRAMEWORK']['DEFAULT_THROTTLE_RATES'] = {}
    
    settings_dict['REST_FRAMEWORK']['DEFAULT_THROTTLE_RATES'].update({
        'anon': '100/hour',
        'user': '1000/hour',
        'ai_operations': config['RATE_LIMITS']['ai_operations'],
    })
    
    # Logging Configuration
    if 'LOGGING' not in settings_dict:
        settings_dict['LOGGING'] = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                    'style': '{',
                },
            },
            'handlers': {
                'file': {
                    'level': 'INFO',
                    'class': 'logging.FileHandler',
                    'filename': 'ai_insights.log',
                    'formatter': 'verbose',
                },
                'console': {
                    'level': 'INFO',
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose',
                },
            },
            'loggers': {
                'apps.ai_insights': {
                    'handlers': ['file', 'console'],
                    'level': config['MONITORING']['LOG_LEVEL'],
                    'propagate': True,
                },
            },
        }
    
    # Channel Layers for WebSocket
    if 'CHANNEL_LAYERS' not in settings_dict:
        settings_dict['CHANNEL_LAYERS'] = {
            'default': {
                'BACKEND': 'channels_redis.core.RedisChannelLayer',
                'CONFIG': {
                    'hosts': [('127.0.0.1', 6379)],
                    'capacity': 1500,  # Maximum messages per channel
                    'expiry': 60,      # Message expiry in seconds
                },
            },
        }
    
    # Cache Configuration
    if 'CACHES' not in settings_dict or 'ai_insights' not in settings_dict['CACHES']:
        if 'CACHES' not in settings_dict:
            settings_dict['CACHES'] = {}
        
        settings_dict['CACHES']['ai_insights'] = {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/2',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'ai_insights',
            'TIMEOUT': config['CACHE']['FINANCIAL_CONTEXT_TTL'],
        }
    
    # AI Insights specific settings
    settings_dict['AI_INSIGHTS_CONFIG'] = config
    
    return settings_dict


# Health Check Endpoints
HEALTH_CHECKS = {
    'database': {
        'check': 'apps.ai_insights.health.check_database',
        'timeout': 5,
    },
    'redis': {
        'check': 'apps.ai_insights.health.check_redis',
        'timeout': 3,
    },
    'openai': {
        'check': 'apps.ai_insights.health.check_openai_connection',
        'timeout': 10,
    },
    'websocket': {
        'check': 'apps.ai_insights.health.check_websocket_layer',
        'timeout': 5,
    },
}

# Performance Monitoring
PERFORMANCE_METRICS = [
    'ai_insights.api.response_time',
    'ai_insights.websocket.connection_count',
    'ai_insights.credits.usage_rate',
    'ai_insights.openai.api_calls',
    'ai_insights.insights.generation_rate',
    'ai_insights.conversations.active_count',
]

# Error Tracking Configuration
ERROR_TRACKING_CONFIG = {
    'EXCLUDED_ERRORS': [
        'InsufficientCreditsError',  # Business logic, not system error
        'ValidationError',           # Expected validation errors
    ],
    'SAMPLING_RATE': 1.0,  # Track all errors in production
    'ENVIRONMENT': 'production',
    'TAGS': {
        'component': 'ai_insights',
        'version': '1.0.0',
    }
}

# Deployment Checklist
PRODUCTION_CHECKLIST = [
    'OPENAI_API_KEY is configured',
    'Redis is running and accessible',
    'Database migrations are applied',
    'Static files are collected',
    'SSL/TLS certificates are valid',
    'Monitoring is configured',
    'Error tracking is enabled',
    'Rate limiting is active',
    'WebSocket layer is configured',
    'Cache is functioning',
    'Health checks are passing',
    'Security headers are configured',
    'CORS settings are correct',
    'Backup procedures are in place',
]