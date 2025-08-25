"""
Logging Configuration for Payment System
Sets up structured logging with proper formatters and handlers
"""
import logging
import logging.config
from pythonjsonlogger import jsonlogger
from django.conf import settings


class PaymentLogFilter(logging.Filter):
    """Add payment-specific context to log records"""
    
    def filter(self, record):
        # Add app context
        record.app = 'payments'
        record.environment = getattr(settings, 'ENVIRONMENT_NAME', 'development')
        
        # Add request context if available
        if hasattr(record, 'request'):
            request = record.request
            record.user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
            record.session_id = request.session.session_key if hasattr(request, 'session') else None
            record.request_id = getattr(request, 'id', None)
        
        return True


class SensitiveDataFilter(logging.Filter):
    """Filter out sensitive payment data from logs"""
    
    SENSITIVE_FIELDS = [
        'card_number', 'cvv', 'cvc', 'exp_month', 'exp_year',
        'account_number', 'routing_number', 'stripe_secret_key',
        'api_key', 'webhook_secret', 'password', 'token'
    ]
    
    def filter(self, record):
        # Redact sensitive fields in log messages
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            for field in self.SENSITIVE_FIELDS:
                if field in msg.lower():
                    record.msg = self._redact_field(msg, field)
        
        # Redact sensitive fields in extra data
        for field in self.SENSITIVE_FIELDS:
            if hasattr(record, field):
                setattr(record, field, '[REDACTED]')
        
        return True
    
    def _redact_field(self, text: str, field: str) -> str:
        """Redact sensitive field in text"""
        import re
        # Simple pattern to find field:value patterns
        pattern = rf'{field}["\']?\s*[:=]\s*["\']?([^"\'\s,}}]+)'
        return re.sub(pattern, f'{field}=[REDACTED]', text, flags=re.IGNORECASE)


def get_logging_config():
    """Get logging configuration for payment system"""
    
    # Base log level from settings
    log_level = getattr(settings, 'PAYMENT_LOG_LEVEL', 'INFO')
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        
        'formatters': {
            'json': {
                '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(timestamp)s %(level)s %(name)s %(message)s'
            },
            'detailed': {
                'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            }
        },
        
        'filters': {
            'payment_context': {
                '()': 'apps.payments.logging_config.PaymentLogFilter'
            },
            'sensitive_data': {
                '()': 'apps.payments.logging_config.SensitiveDataFilter'
            }
        },
        
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'detailed' if settings.DEBUG else 'json',
                'filters': ['payment_context', 'sensitive_data']
            },
            
            'payment_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/payments.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'json',
                'filters': ['payment_context', 'sensitive_data']
            },
            
            'transaction_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/payment_transactions.log',
                'maxBytes': 52428800,  # 50MB
                'backupCount': 10,
                'formatter': 'json',
                'filters': ['payment_context', 'sensitive_data']
            },
            
            'audit_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/payment_audit.log',
                'maxBytes': 52428800,  # 50MB
                'backupCount': 30,  # Keep 30 days
                'formatter': 'json',
                'filters': ['payment_context', 'sensitive_data']
            },
            
            'security_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/payment_security.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'formatter': 'json',
                'filters': ['payment_context']  # Don't filter security logs
            },
            
            'performance_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/payment_performance.log',
                'maxBytes': 52428800,  # 50MB
                'backupCount': 5,
                'formatter': 'json',
                'filters': ['payment_context']
            },
            
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/payment_errors.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'formatter': 'json',
                'filters': ['payment_context', 'sensitive_data'],
                'level': 'ERROR'
            }
        },
        
        'loggers': {
            # Main payment logger
            'apps.payments': {
                'handlers': ['console', 'payment_file', 'error_file'],
                'level': log_level,
                'propagate': False
            },
            
            # Transaction logger
            'payments.transactions': {
                'handlers': ['transaction_file'],
                'level': 'INFO',
                'propagate': False
            },
            
            # Audit logger
            'payments.audit': {
                'handlers': ['audit_file'],
                'level': 'INFO',
                'propagate': False
            },
            
            # Security logger
            'payments.security': {
                'handlers': ['console', 'security_file'],
                'level': 'WARNING',
                'propagate': False
            },
            
            # Performance logger
            'payments.performance': {
                'handlers': ['performance_file'],
                'level': 'INFO',
                'propagate': False
            },
            
            # Stripe library logger
            'stripe': {
                'handlers': ['payment_file'],
                'level': 'WARNING',
                'propagate': False
            }
        }
    }
    
    # Add Sentry handler in production
    if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
        config['handlers']['sentry'] = {
            'class': 'sentry_sdk.integrations.logging.SentryHandler',
            'level': 'ERROR',
            'filters': ['payment_context', 'sensitive_data']
        }
        
        # Add Sentry to all loggers
        for logger_config in config['loggers'].values():
            if 'handlers' in logger_config:
                logger_config['handlers'].append('sentry')
    
    # Add CloudWatch handler if configured
    if hasattr(settings, 'AWS_CLOUDWATCH_LOG_GROUP') and settings.AWS_CLOUDWATCH_LOG_GROUP:
        config['handlers']['cloudwatch'] = {
            'class': 'watchtower.CloudWatchLogHandler',
            'log_group': settings.AWS_CLOUDWATCH_LOG_GROUP,
            'stream_name': f'payments-{getattr(settings, "ENVIRONMENT_NAME", "production")}',
            'formatter': 'json',
            'filters': ['payment_context', 'sensitive_data']
        }
        
        # Add CloudWatch to production loggers
        if not settings.DEBUG:
            for logger_name, logger_config in config['loggers'].items():
                if logger_name != 'payments.security':  # Keep security logs separate
                    logger_config['handlers'].append('cloudwatch')
    
    return config


def setup_payment_logging():
    """Setup payment logging configuration"""
    logging.config.dictConfig(get_logging_config())
    
    # Configure Sentry if available
    if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
        
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                DjangoIntegration(),
                sentry_logging
            ],
            environment=getattr(settings, 'ENVIRONMENT_NAME', 'production'),
            traces_sample_rate=0.1,  # 10% of transactions
            send_default_pii=False,  # Don't send PII
            before_send=filter_sensitive_data
        )


def filter_sensitive_data(event, hint):
    """Filter sensitive data from Sentry events"""
    # Remove sensitive data from request
    if 'request' in event and 'data' in event['request']:
        data = event['request']['data']
        for field in SensitiveDataFilter.SENSITIVE_FIELDS:
            if field in data:
                data[field] = '[REDACTED]'
    
    # Remove sensitive data from extra context
    if 'extra' in event:
        for field in SensitiveDataFilter.SENSITIVE_FIELDS:
            if field in event['extra']:
                event['extra'][field] = '[REDACTED]'
    
    return event


# Usage example for views
def get_payment_logger(name: str = 'apps.payments') -> logging.Logger:
    """Get configured logger for payment operations"""
    return logging.getLogger(name)