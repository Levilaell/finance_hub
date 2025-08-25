"""
APM (Application Performance Monitoring) Integration
Provides integration with monitoring tools like DataDog, New Relic, etc.
"""
import time
import functools
from typing import Dict, Any, Optional, Callable
from django.conf import settings
from django.db import connection
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class APMIntegration:
    """Base class for APM integrations"""
    
    def __init__(self):
        self.enabled = self._is_enabled()
    
    def _is_enabled(self) -> bool:
        """Check if APM is enabled"""
        return not settings.DEBUG and hasattr(settings, 'APM_ENABLED') and settings.APM_ENABLED
    
    def trace_operation(self, operation_name: str, operation_type: str = 'custom',
                       tags: Optional[Dict[str, Any]] = None):
        """Trace an operation"""
        raise NotImplementedError
    
    def record_metric(self, metric_name: str, value: float, 
                     tags: Optional[Dict[str, Any]] = None):
        """Record a metric"""
        raise NotImplementedError
    
    def trace_error(self, error: Exception, tags: Optional[Dict[str, Any]] = None):
        """Trace an error"""
        raise NotImplementedError


class DataDogAPM(APMIntegration):
    """DataDog APM integration"""
    
    def __init__(self):
        super().__init__()
        if self.enabled:
            try:
                from ddtrace import tracer, patch_all
                patch_all()  # Auto-instrument libraries
                self.tracer = tracer
                self.tracer.configure(
                    hostname=settings.DATADOG_AGENT_HOST,
                    port=settings.DATADOG_AGENT_PORT,
                    env=getattr(settings, 'ENVIRONMENT_NAME', 'production'),
                    service='finance-hub-payments',
                    version=settings.VERSION
                )
            except ImportError:
                logger.warning("DataDog APM library not installed")
                self.enabled = False
    
    def trace_operation(self, operation_name: str, operation_type: str = 'custom',
                       tags: Optional[Dict[str, Any]] = None):
        """Create a DataDog trace span"""
        if not self.enabled:
            return nullcontext()
        
        span = self.tracer.trace(operation_name, service='payments', 
                                resource=operation_type)
        
        # Add tags
        if tags:
            for key, value in tags.items():
                span.set_tag(key, value)
        
        # Add default tags
        span.set_tag('environment', getattr(settings, 'ENVIRONMENT_NAME', 'production'))
        
        return span
    
    def record_metric(self, metric_name: str, value: float,
                     tags: Optional[Dict[str, Any]] = None):
        """Send metric to DataDog"""
        if not self.enabled:
            return
        
        try:
            from datadog import statsd
            tag_list = [f"{k}:{v}" for k, v in (tags or {}).items()]
            statsd.gauge(f'payments.{metric_name}', value, tags=tag_list)
        except Exception as e:
            logger.error(f"Failed to send DataDog metric: {e}")
    
    def trace_error(self, error: Exception, tags: Optional[Dict[str, Any]] = None):
        """Send error to DataDog"""
        if not self.enabled:
            return
        
        try:
            span = self.tracer.current_span()
            if span:
                span.set_exc_info(type(error), error, error.__traceback__)
                if tags:
                    for key, value in tags.items():
                        span.set_tag(key, value)
        except Exception as e:
            logger.error(f"Failed to trace error in DataDog: {e}")


class NewRelicAPM(APMIntegration):
    """New Relic APM integration"""
    
    def __init__(self):
        super().__init__()
        if self.enabled:
            try:
                import newrelic.agent
                self.nr = newrelic.agent
                # Initialize New Relic
                if hasattr(settings, 'NEW_RELIC_CONFIG_FILE'):
                    self.nr.initialize(settings.NEW_RELIC_CONFIG_FILE)
            except ImportError:
                logger.warning("New Relic APM library not installed")
                self.enabled = False
    
    def trace_operation(self, operation_name: str, operation_type: str = 'custom',
                       tags: Optional[Dict[str, Any]] = None):
        """Create a New Relic transaction"""
        if not self.enabled:
            return nullcontext()
        
        # Use function trace for operations
        return self.nr.function_trace(
            name=operation_name,
            group=f'Payment/{operation_type}'
        )
    
    def record_metric(self, metric_name: str, value: float,
                     tags: Optional[Dict[str, Any]] = None):
        """Send custom metric to New Relic"""
        if not self.enabled:
            return
        
        try:
            self.nr.record_custom_metric(f'Custom/Payments/{metric_name}', value)
            
            # Add custom attributes for tags
            if tags:
                for key, value in tags.items():
                    self.nr.add_custom_attribute(key, value)
        except Exception as e:
            logger.error(f"Failed to send New Relic metric: {e}")
    
    def trace_error(self, error: Exception, tags: Optional[Dict[str, Any]] = None):
        """Send error to New Relic"""
        if not self.enabled:
            return
        
        try:
            self.nr.notice_error()
            if tags:
                for key, value in tags.items():
                    self.nr.add_custom_attribute(key, value)
        except Exception as e:
            logger.error(f"Failed to trace error in New Relic: {e}")


class ElasticAPM(APMIntegration):
    """Elastic APM integration"""
    
    def __init__(self):
        super().__init__()
        if self.enabled:
            try:
                import elasticapm
                from elasticapm.contrib.django import DjangoAPMClient
                
                self.client = DjangoAPMClient({
                    'SERVICE_NAME': 'finance-hub-payments',
                    'SECRET_TOKEN': settings.ELASTIC_APM_SECRET_TOKEN,
                    'SERVER_URL': settings.ELASTIC_APM_SERVER_URL,
                    'ENVIRONMENT': getattr(settings, 'ENVIRONMENT_NAME', 'production'),
                })
                self.elasticapm = elasticapm
            except ImportError:
                logger.warning("Elastic APM library not installed")
                self.enabled = False
    
    def trace_operation(self, operation_name: str, operation_type: str = 'custom',
                       tags: Optional[Dict[str, Any]] = None):
        """Create an Elastic APM transaction"""
        if not self.enabled:
            return nullcontext()
        
        transaction = self.elasticapm.begin_transaction(operation_type)
        self.elasticapm.set_transaction_name(operation_name)
        
        if tags:
            for key, value in tags.items():
                self.elasticapm.label(**{key: value})
        
        return transaction
    
    def record_metric(self, metric_name: str, value: float,
                     tags: Optional[Dict[str, Any]] = None):
        """Send metric to Elastic APM"""
        if not self.enabled:
            return
        
        try:
            self.client.capture_message(
                f'metric.{metric_name}',
                custom={
                    'metric_name': metric_name,
                    'metric_value': value,
                    'tags': tags or {}
                }
            )
        except Exception as e:
            logger.error(f"Failed to send Elastic APM metric: {e}")
    
    def trace_error(self, error: Exception, tags: Optional[Dict[str, Any]] = None):
        """Send error to Elastic APM"""
        if not self.enabled:
            return
        
        try:
            self.client.capture_exception(
                exc_info=(type(error), error, error.__traceback__),
                extra=tags or {}
            )
        except Exception as e:
            logger.error(f"Failed to trace error in Elastic APM: {e}")


# APM Manager to handle multiple integrations
class APMManager:
    """Manages multiple APM integrations"""
    
    _instance = None
    _integrations = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize configured APM integrations"""
        if hasattr(settings, 'APM_PROVIDERS'):
            for provider in settings.APM_PROVIDERS:
                if provider == 'datadog':
                    self._integrations.append(DataDogAPM())
                elif provider == 'newrelic':
                    self._integrations.append(NewRelicAPM())
                elif provider == 'elastic':
                    self._integrations.append(ElasticAPM())
    
    def trace_operation(self, operation_name: str, operation_type: str = 'custom',
                       tags: Optional[Dict[str, Any]] = None):
        """Trace operation across all APM providers"""
        spans = []
        for integration in self._integrations:
            if integration.enabled:
                try:
                    span = integration.trace_operation(operation_name, operation_type, tags)
                    spans.append(span)
                except Exception as e:
                    logger.error(f"Failed to trace in {integration.__class__.__name__}: {e}")
        
        return MultiSpanContext(spans)
    
    def record_metric(self, metric_name: str, value: float,
                     tags: Optional[Dict[str, Any]] = None):
        """Record metric across all APM providers"""
        for integration in self._integrations:
            if integration.enabled:
                try:
                    integration.record_metric(metric_name, value, tags)
                except Exception as e:
                    logger.error(f"Failed to record metric in {integration.__class__.__name__}: {e}")
    
    def trace_error(self, error: Exception, tags: Optional[Dict[str, Any]] = None):
        """Trace error across all APM providers"""
        for integration in self._integrations:
            if integration.enabled:
                try:
                    integration.trace_error(error, tags)
                except Exception as e:
                    logger.error(f"Failed to trace error in {integration.__class__.__name__}: {e}")


class MultiSpanContext:
    """Context manager for multiple APM spans"""
    
    def __init__(self, spans):
        self.spans = spans
    
    def __enter__(self):
        for span in self.spans:
            if hasattr(span, '__enter__'):
                span.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for span in self.spans:
            if hasattr(span, '__exit__'):
                span.__exit__(exc_type, exc_val, exc_tb)


class nullcontext:
    """Null context manager for when APM is disabled"""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


# Decorators for easy APM integration
def trace_payment_operation(operation_type: str = 'payment'):
    """Decorator to trace payment operations"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            apm = APMManager()
            
            # Extract context from arguments
            tags = {
                'function': func.__name__,
                'module': func.__module__,
            }
            
            # Try to extract payment context
            for arg in args:
                if hasattr(arg, 'company_id'):
                    tags['company_id'] = arg.company_id
                if hasattr(arg, 'amount'):
                    tags['amount'] = float(arg.amount)
                if hasattr(arg, 'currency'):
                    tags['currency'] = arg.currency
            
            with apm.trace_operation(func.__name__, operation_type, tags):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Record success metrics
                    duration = (time.time() - start_time) * 1000
                    apm.record_metric(f'{operation_type}.duration', duration, tags)
                    apm.record_metric(f'{operation_type}.success', 1, tags)
                    
                    return result
                    
                except Exception as e:
                    # Record failure metrics
                    duration = (time.time() - start_time) * 1000
                    apm.record_metric(f'{operation_type}.duration', duration, tags)
                    apm.record_metric(f'{operation_type}.failure', 1, tags)
                    
                    # Trace the error
                    apm.trace_error(e, tags)
                    
                    raise
        
        return wrapper
    return decorator


def monitor_db_queries(func: Callable):
    """Decorator to monitor database queries in a function"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        apm = APMManager()
        
        # Get initial query count
        initial_queries = len(connection.queries)
        
        with apm.trace_operation(f'db.{func.__name__}', 'database'):
            result = func(*args, **kwargs)
        
        # Calculate query metrics
        query_count = len(connection.queries) - initial_queries
        
        if query_count > 0:
            # Record metrics
            tags = {
                'function': func.__name__,
                'query_count': query_count
            }
            
            apm.record_metric('database.queries', query_count, tags)
            
            # Log slow query warnings
            if query_count > 10:
                logger.warning(f"High query count in {func.__name__}: {query_count} queries")
        
        return result
    
    return wrapper


# Initialize APM on module load
apm_manager = APMManager()