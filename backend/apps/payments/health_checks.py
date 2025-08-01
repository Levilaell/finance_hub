"""
Health checks for payment system monitoring
"""
import logging
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from django.db import connection, models
from django.conf import settings
from datetime import timedelta, datetime
import stripe
import redis
from .models import Payment, Subscription, FailedWebhook, UsageRecord
from .services.payment_gateway import StripeGateway
from .services.audit_service import PaymentAuditService

logger = logging.getLogger(__name__)


class PaymentHealthCheckView(View):
    """Comprehensive health check for payment system"""
    
    def get(self, request):
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': getattr(settings, 'APP_VERSION', '1.0.0'),
            'environment': settings.DEBUG and 'development' or 'production',
            'checks': {}
        }
        
        overall_healthy = True
        
        # Database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            overall_healthy = False
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}'
            }
        
        # Redis connectivity (if configured)
        try:
            redis_url = getattr(settings, 'REDIS_URL', None)
            if redis_url:
                r = redis.from_url(redis_url)
                r.ping()
                health_status['checks']['redis'] = {
                    'status': 'healthy',
                    'message': 'Redis connection successful'
                }
            else:
                health_status['checks']['redis'] = {
                    'status': 'skipped',
                    'message': 'Redis not configured'
                }
        except Exception as e:
            overall_healthy = False
            health_status['checks']['redis'] = {
                'status': 'unhealthy',
                'message': f'Redis connection failed: {str(e)}'
            }
        
        # Stripe API connectivity
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe.Account.retrieve()
            health_status['checks']['stripe'] = {
                'status': 'healthy',
                'message': 'Stripe API connection successful'
            }
        except Exception as e:
            overall_healthy = False
            health_status['checks']['stripe'] = {
                'status': 'unhealthy',
                'message': f'Stripe API connection failed: {str(e)}'
            }
        
        # Payment processing health
        payment_health = self.check_payment_health()
        health_status['checks']['payments'] = payment_health
        if payment_health['status'] != 'healthy':
            overall_healthy = False
        
        # Webhook processing health
        webhook_health = self.check_webhook_health()
        health_status['checks']['webhooks'] = webhook_health
        if webhook_health['status'] != 'healthy':
            overall_healthy = False
        
        # Subscription health
        subscription_health = self.check_subscription_health()
        health_status['checks']['subscriptions'] = subscription_health
        if subscription_health['status'] != 'healthy':
            overall_healthy = False
        
        # Update overall status
        health_status['status'] = 'healthy' if overall_healthy else 'unhealthy'
        
        # Return appropriate HTTP status
        status_code = 200 if overall_healthy else 503
        
        return JsonResponse(health_status, status=status_code)
    
    def check_payment_health(self):
        """Check payment processing health"""
        try:
            # Check recent payment success rate
            last_hour = timezone.now() - timedelta(hours=1)
            recent_payments = Payment.objects.filter(created_at__gte=last_hour)
            
            if recent_payments.count() == 0:
                return {
                    'status': 'healthy',
                    'message': 'No recent payments to analyze',
                    'metrics': {
                        'total_payments': 0,
                        'success_rate': 1.0
                    }
                }
            
            successful_payments = recent_payments.filter(status='succeeded').count()
            total_payments = recent_payments.count()
            success_rate = successful_payments / total_payments
            
            # Alert if success rate < 95%
            if success_rate < 0.95:
                return {
                    'status': 'unhealthy',
                    'message': f'Payment success rate too low: {success_rate:.2%}',
                    'metrics': {
                        'total_payments': total_payments,
                        'successful_payments': successful_payments,
                        'success_rate': success_rate
                    }
                }
            
            return {
                'status': 'healthy',
                'message': f'Payment success rate: {success_rate:.2%}',
                'metrics': {
                    'total_payments': total_payments,
                    'successful_payments': successful_payments,
                    'success_rate': success_rate
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Payment health check failed: {str(e)}'
            }
    
    def check_webhook_health(self):
        """Check webhook processing health"""
        try:
            # Check for failed webhooks in last hour
            last_hour = timezone.now() - timedelta(hours=1)
            failed_webhooks = FailedWebhook.objects.filter(
                created_at__gte=last_hour,
                retry_count__gte=3  # Webhooks that have failed multiple times
            ).count()
            
            if failed_webhooks > 10:  # Alert if more than 10 failed webhooks per hour
                return {
                    'status': 'unhealthy',
                    'message': f'Too many failed webhooks: {failed_webhooks} in the last hour',
                    'metrics': {
                        'failed_webhooks': failed_webhooks
                    }
                }
            
            return {
                'status': 'healthy',
                'message': f'Webhook processing healthy: {failed_webhooks} failed webhooks in last hour',
                'metrics': {
                    'failed_webhooks': failed_webhooks
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Webhook health check failed: {str(e)}'
            }
    
    def check_subscription_health(self):
        """Check subscription health"""
        try:
            # Check for subscriptions that should be active but aren't synced
            active_subscriptions = Subscription.objects.filter(status='active').count()
            trial_subscriptions = Subscription.objects.filter(status='trial').count()
            
            # Check for subscriptions with overdue payments
            overdue_count = 0
            try:
                overdue_subscriptions = Subscription.objects.filter(
                    status='active',
                    current_period_end__lt=timezone.now() - timedelta(days=1)
                )
                overdue_count = overdue_subscriptions.count()
            except Exception:
                pass  # Field might not exist in all configurations
            
            return {
                'status': 'healthy',
                'message': 'Subscription system operational',
                'metrics': {
                    'active_subscriptions': active_subscriptions,
                    'trial_subscriptions': trial_subscriptions,
                    'overdue_subscriptions': overdue_count
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Subscription health check failed: {str(e)}'
            }


class PaymentMetricsView(View):
    """Detailed payment metrics for monitoring"""
    
    def get(self, request):
        try:
            # Time periods
            now = timezone.now()
            last_hour = now - timedelta(hours=1)
            last_24h = now - timedelta(days=1)
            last_week = now - timedelta(days=7)
            
            metrics = {
                'timestamp': now.isoformat(),
                'periods': {
                    'last_hour': self.get_period_metrics(last_hour, now),
                    'last_24h': self.get_period_metrics(last_24h, now),
                    'last_week': self.get_period_metrics(last_week, now),
                },
                'current_status': {
                    'active_subscriptions': Subscription.objects.filter(status='active').count(),
                    'trial_subscriptions': Subscription.objects.filter(status='trial').count(),
                    'failed_webhooks_pending': FailedWebhook.objects.filter(
                        retry_count__lt=3
                    ).count(),
                }
            }
            
            return JsonResponse(metrics)
            
        except Exception as e:
            logger.error(f"Payment metrics error: {e}")
            return JsonResponse({
                'error': 'Failed to generate payment metrics',
                'message': str(e)
            }, status=500)
    
    def get_period_metrics(self, start_time, end_time):
        """Get metrics for a specific time period"""
        payments = Payment.objects.filter(
            created_at__gte=start_time,
            created_at__lte=end_time
        )
        
        total_payments = payments.count()
        successful_payments = payments.filter(status='succeeded').count()
        failed_payments = payments.filter(status='failed').count()
        processing_payments = payments.filter(status='processing').count()
        
        total_amount = sum(p.amount for p in payments.filter(status='succeeded'))
        
        return {
            'total_payments': total_payments,
            'successful_payments': successful_payments,
            'failed_payments': failed_payments,
            'processing_payments': processing_payments,
            'success_rate': successful_payments / total_payments if total_payments > 0 else 1.0,
            'total_amount': float(total_amount),
            'average_amount': float(total_amount / successful_payments) if successful_payments > 0 else 0.0,
        }


class PaymentAlertsView(View):
    """Check for conditions that should trigger alerts"""
    
    def get(self, request):
        alerts = []
        
        # High failure rate alert
        failure_alert = self.check_failure_rate()
        if failure_alert:
            alerts.append(failure_alert)
        
        # Webhook processing alert
        webhook_alert = self.check_webhook_failures()
        if webhook_alert:
            alerts.append(webhook_alert)
        
        # Subscription churn alert
        churn_alert = self.check_subscription_churn()
        if churn_alert:
            alerts.append(churn_alert)
        
        # Usage limit alert
        usage_alert = self.check_usage_limits()
        if usage_alert:
            alerts.append(usage_alert)
        
        return JsonResponse({
            'timestamp': timezone.now().isoformat(),
            'alert_count': len(alerts),
            'alerts': alerts
        })
    
    def check_failure_rate(self):
        """Check for high payment failure rate"""
        last_hour = timezone.now() - timedelta(hours=1)
        recent_payments = Payment.objects.filter(created_at__gte=last_hour)
        
        if recent_payments.count() < 10:  # Need minimum volume to be meaningful
            return None
        
        failed_count = recent_payments.filter(status='failed').count()
        failure_rate = failed_count / recent_payments.count()
        
        if failure_rate > 0.05:  # Alert if > 5% failure rate
            return {
                'type': 'payment_failure_rate',
                'severity': 'high' if failure_rate > 0.10 else 'medium',
                'message': f'High payment failure rate: {failure_rate:.2%}',
                'metrics': {
                    'failure_rate': failure_rate,
                    'failed_payments': failed_count,
                    'total_payments': recent_payments.count()
                }
            }
        
        return None
    
    def check_webhook_failures(self):
        """Check for webhook processing issues"""
        last_hour = timezone.now() - timedelta(hours=1)
        failed_webhooks = FailedWebhook.objects.filter(
            created_at__gte=last_hour,
            retry_count__gte=2
        ).count()
        
        if failed_webhooks > 5:
            return {
                'type': 'webhook_failures',
                'severity': 'high' if failed_webhooks > 20 else 'medium',
                'message': f'High webhook failure rate: {failed_webhooks} failed webhooks in last hour',
                'metrics': {
                    'failed_webhooks': failed_webhooks
                }
            }
        
        return None
    
    def check_subscription_churn(self):
        """Check for unusual subscription cancellation patterns"""
        last_24h = timezone.now() - timedelta(days=1)
        cancelled_subscriptions = Subscription.objects.filter(
            cancelled_at__gte=last_24h
        ).count()
        
        if cancelled_subscriptions > 10:  # Adjust threshold based on your normal volume
            return {
                'type': 'subscription_churn',
                'severity': 'medium',
                'message': f'High subscription cancellation rate: {cancelled_subscriptions} in last 24h',
                'metrics': {
                    'cancelled_subscriptions': cancelled_subscriptions
                }
            }
        
        return None
    
    def check_usage_limits(self):
        """Check for companies approaching usage limits"""
        high_usage_count = UsageRecord.objects.filter(
            count__gte=models.F('company__subscription__plan__max_transactions') * 0.9
        ).count()
        
        if high_usage_count > 0:
            return {
                'type': 'usage_limits',
                'severity': 'low',
                'message': f'{high_usage_count} companies approaching usage limits',
                'metrics': {
                    'companies_near_limit': high_usage_count
                }
            }
        
        return None