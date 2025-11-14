"""
Sentry configuration for error tracking and performance monitoring.
Ref: https://docs.sentry.io/platforms/python/guides/django/
"""
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from decouple import config


def init_sentry():
    """
    Initialize Sentry SDK for error tracking.

    This function should be called in settings.py to enable:
    - Automatic error capture
    - Performance monitoring
    - Release tracking
    - User context
    """
    sentry_dsn = config('SENTRY_DSN', default=None)

    if not sentry_dsn:
        # Sentry is disabled if no DSN is provided
        return

    environment = config('DJANGO_ENV', default='development')

    sentry_sdk.init(
        dsn=sentry_dsn,

        # Integrations
        integrations=[
            DjangoIntegration(
                # Capture transactions for performance monitoring
                transaction_style='url',
                # Capture middleware spans
                middleware_spans=True,
                # Capture signals
                signals_spans=True,
            ),
            CeleryIntegration(
                # Monitor Celery tasks
                monitor_beat_tasks=True,
                # Exclude successful tasks from transactions
                exclude_beat_tasks=False,
            ),
            RedisIntegration(),
        ],

        # Environment
        environment=environment,

        # Performance Monitoring
        # Set traces_sample_rate to 1.0 to capture 100% of transactions
        # Lower in production to reduce overhead
        traces_sample_rate=0.1 if environment == 'production' else 1.0,

        # Error Sampling
        # Capture 100% of errors (recommended)
        sample_rate=1.0,

        # Send default PII (Personally Identifiable Information)
        # Set to False in production if you have privacy concerns
        send_default_pii=True,

        # Profiles
        # Enable profiling to get detailed performance data
        profiles_sample_rate=0.1 if environment == 'production' else 1.0,

        # Before send hook - Filter sensitive data
        before_send=before_send_handler,

        # Ignore common errors
        ignore_errors=[
            # Django's SuspiciousOperation errors
            'django.core.exceptions.SuspiciousOperation',
            # Permission denied errors (expected)
            'rest_framework.exceptions.PermissionDenied',
            # Not authenticated (expected)
            'rest_framework.exceptions.NotAuthenticated',
            # Throttled requests (rate limiting)
            'rest_framework.exceptions.Throttled',
        ],

        # Attach stack traces to messages
        attach_stacktrace=True,

        # Max breadcrumbs (events before error)
        max_breadcrumbs=50,

        # Request bodies
        # Capture request bodies for debugging
        request_bodies='medium',  # 'never', 'small', 'medium', 'always'
    )


def before_send_handler(event, hint):
    """
    Filter/modify events before sending to Sentry.

    Use this to:
    - Remove sensitive data
    - Add custom context
    - Filter out specific errors
    """
    # Remove sensitive headers
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']

        # Remove authorization tokens
        if 'Authorization' in headers:
            headers['Authorization'] = '[Filtered]'

        # Remove cookies
        if 'Cookie' in headers:
            headers['Cookie'] = '[Filtered]'

    # Remove sensitive POST data
    if 'request' in event and 'data' in event['request']:
        data = event['request']['data']

        sensitive_fields = [
            'password', 'token', 'secret', 'api_key',
            'credit_card', 'ssn', 'credentials'
        ]

        for field in sensitive_fields:
            if field in data:
                data[field] = '[Filtered]'

    # Add custom context
    if 'extra' not in event:
        event['extra'] = {}

    # Example: Add deployment info
    event['extra']['deployment'] = {
        'environment': config('DJANGO_ENV', default='development'),
        'version': config('APP_VERSION', default='unknown'),
    }

    return event


def set_user_context(user):
    """
    Set user context for Sentry events.

    Call this in authentication middleware or after login.

    Args:
        user: Django User instance
    """
    if user and user.is_authenticated:
        sentry_sdk.set_user({
            'id': str(user.id),
            'email': user.email,
            'username': user.get_full_name() or user.email,
        })
    else:
        sentry_sdk.set_user(None)


def set_transaction_context(name, op='http.server'):
    """
    Set transaction context for performance monitoring.

    Args:
        name: Transaction name (e.g., 'webhook_handler')
        op: Operation type (e.g., 'http.server', 'celery.task')
    """
    sentry_sdk.set_context('transaction', {
        'name': name,
        'op': op,
    })


def capture_exception(error, **kwargs):
    """
    Manually capture an exception to Sentry.

    Args:
        error: Exception instance
        **kwargs: Additional context

    Example:
        try:
            risky_operation()
        except Exception as e:
            capture_exception(e, extra={'item_id': item_id})
    """
    sentry_sdk.capture_exception(error, **kwargs)


def capture_message(message, level='info', **kwargs):
    """
    Capture a message to Sentry.

    Args:
        message: Message string
        level: 'debug', 'info', 'warning', 'error', 'fatal'
        **kwargs: Additional context

    Example:
        capture_message('Webhook processed successfully', level='info')
    """
    sentry_sdk.capture_message(message, level=level, **kwargs)


def add_breadcrumb(message, category='default', level='info', data=None):
    """
    Add a breadcrumb (event trail before error).

    Args:
        message: Breadcrumb message
        category: Category (e.g., 'http', 'db', 'webhook')
        level: 'debug', 'info', 'warning', 'error'
        data: Additional data dict

    Example:
        add_breadcrumb(
            message='Webhook received',
            category='webhook',
            data={'event_type': 'item/updated'}
        )
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )
