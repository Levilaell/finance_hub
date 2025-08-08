"""
Health Check Service for Payment System
Provides comprehensive health monitoring and status reporting
"""
import logging
from typing import Dict, Any, List, Tuple
from datetime import timedelta
from django.utils import timezone
from django.db import connection, models
from django.conf import settings
from django.core.cache import cache
import stripe
import requests

from ..models import Payment, Subscription, FailedWebhook
from .monitoring_service import MonitoringService

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Comprehensive health check for payment system"""
    
    # Health status levels
    STATUS_HEALTHY = 'healthy'
    STATUS_DEGRADED = 'degraded'
    STATUS_UNHEALTHY = 'unhealthy'
    
    # Component checks
    COMPONENTS = [
        'database',
        'cache',
        'stripe_api',
        'webhook_processing',
        'payment_processing',
        'subscription_management',
        'monitoring',
    ]
    
    @classmethod
    def check_all(cls) -> Dict[str, Any]:
        """
        Run all health checks and return comprehensive status
        
        Returns:
            Dict with overall status and component details
        """
        start_time = timezone.now()
        
        # Run individual checks
        checks = {
            'database': cls._check_database(),
            'cache': cls._check_cache(),
            'stripe_api': cls._check_stripe_api(),
            'webhook_processing': cls._check_webhook_processing(),
            'payment_processing': cls._check_payment_processing(),
            'subscription_management': cls._check_subscription_management(),
            'monitoring': cls._check_monitoring(),
        }
        
        # Calculate overall status
        statuses = [check['status'] for check in checks.values()]
        
        if all(status == cls.STATUS_HEALTHY for status in statuses):
            overall_status = cls.STATUS_HEALTHY
        elif any(status == cls.STATUS_UNHEALTHY for status in statuses):
            overall_status = cls.STATUS_UNHEALTHY
        else:
            overall_status = cls.STATUS_DEGRADED
        
        # Get system metrics
        metrics = cls._get_system_metrics()
        
        # Calculate response time
        response_time_ms = (timezone.now() - start_time).total_seconds() * 1000
        
        return {
            'status': overall_status,
            'timestamp': timezone.now().isoformat(),
            'environment': settings.ENVIRONMENT_NAME,
            'version': getattr(settings, 'VERSION', 'unknown'),
            'response_time_ms': round(response_time_ms, 2),
            'checks': checks,
            'metrics': metrics,
            'alerts': MonitoringService._get_active_alerts()
        }
    
    @classmethod
    def _check_database(cls) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start = timezone.now()
            
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Check recent payments table
            recent_payments = Payment.objects.filter(
                created_at__gte=timezone.now() - timedelta(minutes=5)
            ).count()
            
            response_time = (timezone.now() - start).total_seconds() * 1000
            
            status = cls.STATUS_HEALTHY
            if response_time > 100:  # Slow query
                status = cls.STATUS_DEGRADED
            
            return {
                'status': status,
                'response_time_ms': round(response_time, 2),
                'recent_payments': recent_payments,
                'connection_count': len(connection.queries)
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': cls.STATUS_UNHEALTHY,
                'error': str(e)
            }
    
    @classmethod
    def _check_cache(cls) -> Dict[str, Any]:
        """Check cache connectivity and performance"""
        try:
            test_key = 'health_check_test'
            test_value = timezone.now().isoformat()
            
            start = timezone.now()
            
            # Test cache operations
            cache.set(test_key, test_value, 60)
            retrieved = cache.get(test_key)
            cache.delete(test_key)
            
            response_time = (timezone.now() - start).total_seconds() * 1000
            
            if retrieved != test_value:
                return {
                    'status': cls.STATUS_UNHEALTHY,
                    'error': 'Cache read/write mismatch'
                }
            
            status = cls.STATUS_HEALTHY
            if response_time > 50:  # Slow cache
                status = cls.STATUS_DEGRADED
            
            return {
                'status': status,
                'response_time_ms': round(response_time, 2),
                'backend': cache.__class__.__name__
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                'status': cls.STATUS_UNHEALTHY,
                'error': str(e)
            }
    
    @classmethod
    def _check_stripe_api(cls) -> Dict[str, Any]:
        """Check Stripe API connectivity"""
        try:
            start = timezone.now()
            
            # Test Stripe API with balance retrieval
            stripe.api_key = settings.STRIPE_SECRET_KEY
            balance = stripe.Balance.retrieve()
            
            response_time = (timezone.now() - start).total_seconds() * 1000
            
            # Check API key validity
            if not balance:
                return {
                    'status': cls.STATUS_UNHEALTHY,
                    'error': 'Invalid Stripe API response'
                }
            
            status = cls.STATUS_HEALTHY
            if response_time > 2000:  # Slow API
                status = cls.STATUS_DEGRADED
            
            # Get available balance
            available_balance = sum(
                b['amount'] / 100 for b in balance.available
            )
            
            return {
                'status': status,
                'response_time_ms': round(response_time, 2),
                'livemode': balance.livemode,
                'available_balance': available_balance,
                'currency': balance.available[0]['currency'] if balance.available else 'USD'
            }
            
        except stripe.error.AuthenticationError:
            return {
                'status': cls.STATUS_UNHEALTHY,
                'error': 'Stripe authentication failed - check API keys'
            }
        except Exception as e:
            logger.error(f"Stripe API health check failed: {e}")
            return {
                'status': cls.STATUS_UNHEALTHY,
                'error': str(e)
            }
    
    @classmethod
    def _check_webhook_processing(cls) -> Dict[str, Any]:
        """Check webhook processing health"""
        try:
            # Check for failed webhooks
            failed_webhooks = FailedWebhook.objects.filter(
                retry_count__lt=5,
                next_retry_at__lte=timezone.now()
            ).count()
            
            # Check recent webhook success rate
            since = timezone.now() - timedelta(hours=1)
            
            # Get metrics from cache
            success_count = cache.get('metric:webhook_processed:' + 
                                    since.strftime("%Y%m%d%H"), 0)
            failed_count = cache.get('metric:webhook_failed:' + 
                                   since.strftime("%Y%m%d%H"), 0)
            
            total = success_count + failed_count
            success_rate = (success_count / total * 100) if total > 0 else 100
            
            status = cls.STATUS_HEALTHY
            if failed_webhooks > 10:
                status = cls.STATUS_DEGRADED
            if failed_webhooks > 50 or success_rate < 95:
                status = cls.STATUS_UNHEALTHY
            
            return {
                'status': status,
                'failed_webhooks_pending': failed_webhooks,
                'hourly_success_rate': round(success_rate, 2),
                'processed_last_hour': success_count
            }
            
        except Exception as e:
            logger.error(f"Webhook health check failed: {e}")
            return {
                'status': cls.STATUS_UNHEALTHY,
                'error': str(e)
            }
    
    @classmethod
    def _check_payment_processing(cls) -> Dict[str, Any]:
        """Check payment processing health"""
        try:
            # Check recent payment success rate
            since = timezone.now() - timedelta(hours=1)
            recent_payments = Payment.objects.filter(created_at__gte=since)
            
            total = recent_payments.count()
            succeeded = recent_payments.filter(status='succeeded').count()
            failed = recent_payments.filter(status='failed').count()
            
            success_rate = (succeeded / total * 100) if total > 0 else 100
            
            # Check for stuck payments
            stuck_payments = Payment.objects.filter(
                status='processing',
                created_at__lte=timezone.now() - timedelta(minutes=30)
            ).count()
            
            status = cls.STATUS_HEALTHY
            if success_rate < 95 or stuck_payments > 0:
                status = cls.STATUS_DEGRADED
            if success_rate < 90 or stuck_payments > 5:
                status = cls.STATUS_UNHEALTHY
            
            return {
                'status': status,
                'hourly_success_rate': round(success_rate, 2),
                'payments_last_hour': total,
                'stuck_payments': stuck_payments
            }
            
        except Exception as e:
            logger.error(f"Payment processing health check failed: {e}")
            return {
                'status': cls.STATUS_UNHEALTHY,
                'error': str(e)
            }
    
    @classmethod
    def _check_subscription_management(cls) -> Dict[str, Any]:
        """Check subscription management health"""
        try:
            # Check active subscriptions
            active_subs = Subscription.objects.filter(
                status__in=['active', 'trial']
            ).count()
            
            # Check for subscriptions needing renewal
            needs_renewal = Subscription.objects.filter(
                status='active',
                current_period_end__lte=timezone.now() + timedelta(days=1)
            ).count()
            
            # Check recent cancellations
            recent_cancellations = Subscription.objects.filter(
                cancelled_at__gte=timezone.now() - timedelta(days=1)
            ).count()
            
            status = cls.STATUS_HEALTHY
            if needs_renewal > 10:
                status = cls.STATUS_DEGRADED
            
            return {
                'status': status,
                'active_subscriptions': active_subs,
                'needs_renewal': needs_renewal,
                'daily_cancellations': recent_cancellations
            }
            
        except Exception as e:
            logger.error(f"Subscription health check failed: {e}")
            return {
                'status': cls.STATUS_UNHEALTHY,
                'error': str(e)
            }
    
    @classmethod
    def _check_monitoring(cls) -> Dict[str, Any]:
        """Check monitoring system health"""
        try:
            # Check if monitoring is recording metrics
            test_metric = 'health_check_test'
            cache.set(f'metric:{test_metric}:{timezone.now().strftime("%Y%m%d%H")}', 
                     1, 3600)
            
            # Check for active alerts
            alerts = MonitoringService._get_active_alerts()
            critical_alerts = [a for a in alerts if a.get('severity') == 'critical']
            
            status = cls.STATUS_HEALTHY
            if len(alerts) > 5:
                status = cls.STATUS_DEGRADED
            if len(critical_alerts) > 0:
                status = cls.STATUS_UNHEALTHY
            
            return {
                'status': status,
                'active_alerts': len(alerts),
                'critical_alerts': len(critical_alerts),
                'monitoring_enabled': True
            }
            
        except Exception as e:
            logger.error(f"Monitoring health check failed: {e}")
            return {
                'status': cls.STATUS_UNHEALTHY,
                'error': str(e),
                'monitoring_enabled': False
            }
    
    @classmethod
    def _get_system_metrics(cls) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # Get payment metrics
            since = timezone.now() - timedelta(hours=24)
            
            return {
                'payments_24h': Payment.objects.filter(
                    created_at__gte=since
                ).count(),
                'revenue_24h': float(
                    Payment.objects.filter(
                        created_at__gte=since,
                        status='succeeded'
                    ).aggregate(total=models.Sum('amount'))['total'] or 0
                ),
                'active_subscriptions': Subscription.objects.filter(
                    status__in=['active', 'trial']
                ).count(),
                'failed_webhooks': FailedWebhook.objects.filter(
                    retry_count__lt=5
                ).count(),
                'database_queries': len(connection.queries),
                'cache_hits': cache.get('cache_hits', 0),
                'uptime_hours': cls._calculate_uptime()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}
    
    @classmethod
    def _calculate_uptime(cls) -> float:
        """Calculate system uptime in hours"""
        # Get from cache or estimate based on last restart
        uptime_start = cache.get('system_start_time')
        if not uptime_start:
            # Set current time as start
            cache.set('system_start_time', timezone.now(), None)
            return 0.0
        
        return (timezone.now() - uptime_start).total_seconds() / 3600


def get_health_status() -> Tuple[Dict[str, Any], int]:
    """
    Get health status with appropriate HTTP status code
    
    Returns:
        Tuple of (health_data, http_status_code)
    """
    health_data = HealthCheckService.check_all()
    
    # Map health status to HTTP status codes
    status_map = {
        HealthCheckService.STATUS_HEALTHY: 200,
        HealthCheckService.STATUS_DEGRADED: 200,  # Still operational
        HealthCheckService.STATUS_UNHEALTHY: 503  # Service unavailable
    }
    
    http_status = status_map.get(health_data['status'], 503)
    
    return health_data, http_status