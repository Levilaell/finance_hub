"""
Production-Grade Monitoring Service for Payment Operations
Provides comprehensive logging, metrics, and alerting
"""
import logging
import time
import json
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
import sentry_sdk
from sentry_sdk import capture_message, capture_exception

from ..models import Payment, Subscription, PaymentMethod, CreditTransaction
from ..exceptions import PaymentException

logger = logging.getLogger(__name__)

# Structured logger for payment events
payment_logger = logging.getLogger('payments.transactions')
audit_logger = logging.getLogger('payments.audit')
security_logger = logging.getLogger('payments.security')
performance_logger = logging.getLogger('payments.performance')


class PaymentMetrics:
    """Tracks and reports payment metrics"""
    
    # Metric types
    METRIC_TYPES = {
        'payment_success': 'counter',
        'payment_failure': 'counter',
        'payment_amount': 'gauge',
        'payment_duration': 'histogram',
        'subscription_created': 'counter',
        'subscription_cancelled': 'counter',
        'webhook_processed': 'counter',
        'webhook_failed': 'counter',
        'api_request_duration': 'histogram',
        'credit_purchase': 'counter',
        'credit_usage': 'counter',
    }
    
    @classmethod
    def record_metric(cls, metric_name: str, value: float = 1.0, 
                     tags: Optional[Dict[str, str]] = None):
        """
        Record a metric value
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Additional tags for the metric
        """
        tags = tags or {}
        
        # Add environment tag
        tags['environment'] = settings.ENVIRONMENT_NAME
        
        # Log to structured logger
        performance_logger.info(
            f"metric.{metric_name}",
            extra={
                'metric_name': metric_name,
                'metric_value': value,
                'metric_type': cls.METRIC_TYPES.get(metric_name, 'gauge'),
                'tags': tags,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Send to monitoring service (DataDog, CloudWatch, etc.)
        if hasattr(settings, 'DATADOG_ENABLED') and settings.DATADOG_ENABLED:
            cls._send_to_datadog(metric_name, value, tags)
        
        # Update cache for real-time dashboards
        cache_key = f'metric:{metric_name}:{timezone.now().strftime("%Y%m%d%H")}'
        current = cache.get(cache_key, 0)
        cache.set(cache_key, current + value, 3600)
    
    @classmethod
    def _send_to_datadog(cls, metric_name: str, value: float, tags: Dict[str, str]):
        """Send metric to DataDog"""
        try:
            from datadog import statsd
            tag_list = [f"{k}:{v}" for k, v in tags.items()]
            
            metric_type = cls.METRIC_TYPES.get(metric_name, 'gauge')
            if metric_type == 'counter':
                statsd.increment(f'finance_hub.payments.{metric_name}', value, tags=tag_list)
            elif metric_type == 'gauge':
                statsd.gauge(f'finance_hub.payments.{metric_name}', value, tags=tag_list)
            elif metric_type == 'histogram':
                statsd.histogram(f'finance_hub.payments.{metric_name}', value, tags=tag_list)
        except Exception as e:
            logger.error(f"Failed to send metric to DataDog: {e}")


class MonitoringService:
    """Comprehensive monitoring for payment operations"""
    
    # Alert thresholds
    ALERT_THRESHOLDS = {
        'payment_failure_rate': 0.05,      # 5% failure rate
        'webhook_failure_rate': 0.01,      # 1% webhook failure
        'api_response_time': 2.0,          # 2 seconds
        'subscription_churn_rate': 0.10,   # 10% monthly churn
        'credit_depletion_rate': 0.90,     # 90% credits used
    }
    
    @classmethod
    def log_payment_transaction(cls, 
                              payment: 'Payment',
                              action: str,
                              success: bool,
                              duration_ms: Optional[float] = None,
                              metadata: Optional[Dict[str, Any]] = None):
        """
        Log payment transaction with structured data
        
        Args:
            payment: Payment instance
            action: Action performed (created, processed, failed, etc.)
            success: Whether action succeeded
            duration_ms: Operation duration in milliseconds
            metadata: Additional metadata
        """
        log_data = {
            'payment_id': payment.id,
            'company_id': payment.company_id,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'status': payment.status,
            'gateway': payment.gateway,
            'action': action,
            'success': success,
            'timestamp': timezone.now().isoformat()
        }
        
        if duration_ms:
            log_data['duration_ms'] = duration_ms
        
        if metadata:
            log_data['metadata'] = metadata
        
        # Log to structured logger
        payment_logger.info(
            f"payment.{action}",
            extra=log_data
        )
        
        # Record metrics
        if success:
            PaymentMetrics.record_metric('payment_success', tags={'action': action})
        else:
            PaymentMetrics.record_metric('payment_failure', tags={'action': action})
        
        if duration_ms:
            PaymentMetrics.record_metric('payment_duration', duration_ms, 
                                       tags={'action': action})
        
        # Check for alerts
        if not success:
            cls._check_payment_failure_rate()
    
    @classmethod
    def log_subscription_event(cls,
                             subscription: 'Subscription',
                             event: str,
                             metadata: Optional[Dict[str, Any]] = None):
        """Log subscription lifecycle events"""
        log_data = {
            'subscription_id': subscription.id,
            'company_id': subscription.company_id,
            'plan': subscription.plan.name,
            'status': subscription.status,
            'event': event,
            'timestamp': timezone.now().isoformat()
        }
        
        if metadata:
            log_data['metadata'] = metadata
        
        payment_logger.info(
            f"subscription.{event}",
            extra=log_data
        )
        
        # Record metrics
        PaymentMetrics.record_metric(f'subscription_{event}', 
                                   tags={'plan': subscription.plan.name})
        
        # Check for churn alerts
        if event == 'cancelled':
            cls._check_churn_rate()
    
    @classmethod
    def track_api_performance(cls, endpoint: str, duration_ms: float, 
                            status_code: int, user_id: Optional[int] = None):
        """Track API endpoint performance"""
        performance_logger.info(
            f"api.request",
            extra={
                'endpoint': endpoint,
                'duration_ms': duration_ms,
                'status_code': status_code,
                'user_id': user_id,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Record metrics
        PaymentMetrics.record_metric('api_request_duration', duration_ms,
                                   tags={'endpoint': endpoint, 
                                         'status': str(status_code)})
        
        # Check for performance alerts
        if duration_ms > cls.ALERT_THRESHOLDS['api_response_time'] * 1000:
            cls._send_alert(
                'slow_api_response',
                f"Slow API response on {endpoint}: {duration_ms}ms",
                severity='warning',
                context={'endpoint': endpoint, 'duration_ms': duration_ms}
            )
    
    @classmethod
    def log_security_event(cls, event_type: str, description: str,
                         user_id: Optional[int] = None,
                         ip_address: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None):
        """Log security-related events"""
        log_data = {
            'event_type': event_type,
            'description': description,
            'user_id': user_id,
            'ip_address': ip_address,
            'timestamp': timezone.now().isoformat()
        }
        
        if metadata:
            log_data['metadata'] = metadata
        
        security_logger.warning(
            f"security.{event_type}",
            extra=log_data
        )
        
        # Send to Sentry for critical security events
        if event_type in ['suspicious_activity', 'unauthorized_access', 'webhook_forgery']:
            capture_message(
                f"Security Event: {event_type}",
                level='warning',
                extra=log_data
            )
    
    @classmethod
    def monitor_credit_usage(cls, company_id: int):
        """Monitor AI credit usage and alert on depletion"""
        from apps.companies.models import Company
        
        try:
            company = Company.objects.get(id=company_id)
            
            if hasattr(company, 'ai_credit'):
                total_credits = company.ai_credit.balance + company.ai_credit.bonus_credits
                total_capacity = company.ai_credit.monthly_allowance + company.ai_credit.total_purchased
                
                if total_capacity > 0:
                    usage_rate = 1 - (total_credits / total_capacity)
                    
                    if usage_rate > cls.ALERT_THRESHOLDS['credit_depletion_rate']:
                        cls._send_alert(
                            'credit_depletion',
                            f"Company {company.name} has used {usage_rate*100:.1f}% of credits",
                            severity='warning',
                            context={
                                'company_id': company_id,
                                'credits_remaining': total_credits,
                                'usage_rate': usage_rate
                            }
                        )
        except Exception as e:
            logger.error(f"Failed to monitor credit usage: {e}")
    
    @classmethod
    def get_payment_dashboard_metrics(cls, hours: int = 24) -> Dict[str, Any]:
        """Get metrics for payment dashboard"""
        since = timezone.now() - timedelta(hours=hours)
        
        # Payment metrics
        payments = Payment.objects.filter(created_at__gte=since)
        successful_payments = payments.filter(status='succeeded')
        failed_payments = payments.filter(status='failed')
        
        # Subscription metrics
        subscriptions = Subscription.objects.filter(created_at__gte=since)
        cancelled_subs = subscriptions.filter(status='cancelled')
        
        # Calculate metrics
        metrics = {
            'payments': {
                'total': payments.count(),
                'successful': successful_payments.count(),
                'failed': failed_payments.count(),
                'success_rate': (successful_payments.count() / payments.count() * 100) 
                               if payments.count() > 0 else 0,
                'total_revenue': float(successful_payments.aggregate(
                    Sum('amount'))['amount__sum'] or 0),
                'average_amount': float(successful_payments.aggregate(
                    Avg('amount'))['amount__avg'] or 0),
            },
            'subscriptions': {
                'new': subscriptions.count(),
                'cancelled': cancelled_subs.count(),
                'active': Subscription.objects.filter(
                    status__in=['active', 'trial']).count(),
                'churn_rate': (cancelled_subs.count() / 
                             Subscription.objects.filter(status='active').count() * 100)
                             if Subscription.objects.filter(status='active').count() > 0 else 0,
            },
            'performance': {
                'avg_response_time': cls._get_avg_response_time(hours),
                'webhook_success_rate': cls._get_webhook_success_rate(hours),
            },
            'alerts': cls._get_active_alerts(),
            'period_hours': hours,
            'last_updated': timezone.now().isoformat()
        }
        
        return metrics
    
    @classmethod
    def _check_payment_failure_rate(cls):
        """Check if payment failure rate exceeds threshold"""
        # Calculate failure rate for last hour
        since = timezone.now() - timedelta(hours=1)
        payments = Payment.objects.filter(created_at__gte=since)
        
        if payments.count() >= 10:  # Only check if we have enough data
            failure_rate = payments.filter(
                status='failed').count() / payments.count()
            
            if failure_rate > cls.ALERT_THRESHOLDS['payment_failure_rate']:
                cls._send_alert(
                    'high_payment_failure_rate',
                    f"Payment failure rate is {failure_rate*100:.1f}%",
                    severity='critical',
                    context={'failure_rate': failure_rate}
                )
    
    @classmethod
    def _check_churn_rate(cls):
        """Check if churn rate exceeds threshold"""
        # Calculate monthly churn
        since = timezone.now() - timedelta(days=30)
        
        active_start = Subscription.objects.filter(
            created_at__lt=since,
            status__in=['active', 'trial']
        ).count()
        
        if active_start > 0:
            cancelled = Subscription.objects.filter(
                cancelled_at__gte=since
            ).count()
            
            churn_rate = cancelled / active_start
            
            if churn_rate > cls.ALERT_THRESHOLDS['subscription_churn_rate']:
                cls._send_alert(
                    'high_churn_rate',
                    f"Monthly churn rate is {churn_rate*100:.1f}%",
                    severity='warning',
                    context={'churn_rate': churn_rate, 'cancelled': cancelled}
                )
    
    @classmethod
    def _send_alert(cls, alert_type: str, message: str, 
                   severity: str = 'warning',
                   context: Optional[Dict[str, Any]] = None):
        """Send alert to monitoring systems"""
        alert_data = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'context': context or {},
            'timestamp': timezone.now().isoformat()
        }
        
        # Log alert
        logger.warning(f"ALERT: {alert_type} - {message}", extra=alert_data)
        
        # Send to Sentry
        if severity in ['critical', 'error']:
            capture_message(message, level=severity, extra=alert_data)
        
        # Store in cache for dashboard
        cache_key = f'alert:{alert_type}'
        cache.set(cache_key, alert_data, 3600)  # Keep for 1 hour
        
        # Send to notification service (Slack, PagerDuty, etc.)
        if hasattr(settings, 'SLACK_WEBHOOK_URL') and severity == 'critical':
            cls._send_slack_alert(alert_type, message, context)
    
    @classmethod
    def _send_slack_alert(cls, alert_type: str, message: str, 
                         context: Optional[Dict[str, Any]] = None):
        """Send alert to Slack"""
        try:
            import requests
            
            payload = {
                'text': f'🚨 Payment Alert: {alert_type}',
                'blocks': [
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': f'*{alert_type}*\n{message}'
                        }
                    }
                ]
            }
            
            if context:
                payload['blocks'].append({
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f'```{json.dumps(context, indent=2)}```'
                    }
                })
            
            requests.post(settings.SLACK_WEBHOOK_URL, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    @classmethod
    def _get_avg_response_time(cls, hours: int) -> float:
        """Get average API response time from cache"""
        total_time = 0
        total_count = 0
        
        for i in range(hours):
            timestamp = (timezone.now() - timedelta(hours=i)).strftime("%Y%m%d%H")
            time_sum = cache.get(f'metric:api_request_duration:{timestamp}', 0)
            count = cache.get(f'metric:api_request_count:{timestamp}', 0)
            
            total_time += time_sum
            total_count += count
        
        return total_time / total_count if total_count > 0 else 0
    
    @classmethod
    def _get_webhook_success_rate(cls, hours: int) -> float:
        """Get webhook success rate from cache"""
        success_count = 0
        total_count = 0
        
        for i in range(hours):
            timestamp = (timezone.now() - timedelta(hours=i)).strftime("%Y%m%d%H")
            success = cache.get(f'metric:webhook_processed:{timestamp}', 0)
            failed = cache.get(f'metric:webhook_failed:{timestamp}', 0)
            
            success_count += success
            total_count += success + failed
        
        return (success_count / total_count * 100) if total_count > 0 else 100
    
    @classmethod
    def _get_active_alerts(cls) -> List[Dict[str, Any]]:
        """Get active alerts from cache"""
        alerts = []
        alert_types = [
            'high_payment_failure_rate',
            'high_churn_rate',
            'slow_api_response',
            'credit_depletion'
        ]
        
        for alert_type in alert_types:
            alert_data = cache.get(f'alert:{alert_type}')
            if alert_data:
                alerts.append(alert_data)
        
        return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)


def monitor_performance(func):
    """
    Decorator to monitor function performance
    
    Usage:
        @monitor_performance
        def my_function():
            # Your code
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            success = True
            return result
        except Exception as e:
            success = False
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            performance_logger.info(
                f"function.performance",
                extra={
                    'function': func.__name__,
                    'module': func.__module__,
                    'duration_ms': duration_ms,
                    'success': success,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Alert on slow functions
            if duration_ms > 5000:  # 5 seconds
                MonitoringService._send_alert(
                    'slow_function',
                    f"Function {func.__name__} took {duration_ms}ms",
                    severity='warning',
                    context={'function': func.__name__, 'duration_ms': duration_ms}
                )
    
    return wrapper