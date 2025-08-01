"""
Production monitoring and alerting system for payments
"""
import logging
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Payment, Subscription, FailedWebhook
from .services.audit_service import PaymentAuditService

logger = logging.getLogger(__name__)


@dataclass
class MonitoringConfig:
    """Configuration for payment monitoring thresholds"""
    # Payment failure rate thresholds
    failure_rate_warning: float = 0.05  # 5%
    failure_rate_critical: float = 0.10  # 10%
    minimum_payments_for_rate: int = 10
    
    # Webhook failure thresholds
    webhook_failures_warning: int = 5
    webhook_failures_critical: int = 20
    webhook_check_period_hours: int = 1
    
    # Subscription churn thresholds
    churn_warning: int = 10
    churn_critical: int = 25
    churn_check_period_hours: int = 24
    
    # Response time thresholds (milliseconds)
    response_time_warning: int = 1000
    response_time_critical: int = 3000
    
    # Alert cooldown periods (minutes)
    alert_cooldown_warning: int = 30
    alert_cooldown_critical: int = 15


class PaymentMonitor:
    """Central monitoring system for payment operations"""
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or MonitoringConfig()
        self.alert_cache = {}  # Simple in-memory cache for alert cooldowns
    
    def check_all_alerts(self) -> List[Dict]:
        """Run all monitoring checks and return any alerts"""
        alerts = []
        
        # Payment failure rate check
        failure_alert = self.check_payment_failure_rate()
        if failure_alert:
            alerts.append(failure_alert)
        
        # Webhook failure check
        webhook_alert = self.check_webhook_failures()
        if webhook_alert:
            alerts.append(webhook_alert)
        
        # Subscription churn check
        churn_alert = self.check_subscription_churn()
        if churn_alert:
            alerts.append(churn_alert)
        
        # Process and send alerts
        for alert in alerts:
            self.process_alert(alert)
        
        return alerts
    
    def check_payment_failure_rate(self) -> Optional[Dict]:
        """Check payment failure rates"""
        try:
            # Check last hour for immediate issues
            last_hour = timezone.now() - timedelta(hours=1)
            recent_payments = Payment.objects.filter(created_at__gte=last_hour)
            
            if recent_payments.count() < self.config.minimum_payments_for_rate:
                return None
            
            failed_count = recent_payments.filter(status='failed').count()
            total_count = recent_payments.count()
            failure_rate = failed_count / total_count
            
            severity = None
            if failure_rate >= self.config.failure_rate_critical:
                severity = 'critical'
            elif failure_rate >= self.config.failure_rate_warning:
                severity = 'warning'
            
            if severity:
                alert_key = f"payment_failure_rate_{severity}"
                if self.should_send_alert(alert_key, severity):
                    return {
                        'type': 'payment_failure_rate',
                        'severity': severity,
                        'message': f'Payment failure rate is {failure_rate:.2%} ({failed_count}/{total_count})',
                        'metrics': {
                            'failure_rate': failure_rate,
                            'failed_payments': failed_count,
                            'total_payments': total_count,
                            'period': 'last_hour'
                        },
                        'timestamp': timezone.now().isoformat(),
                        'action_required': severity == 'critical'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking payment failure rate: {e}")
            return None
    
    def check_webhook_failures(self) -> Optional[Dict]:
        """Check webhook failure rates"""
        try:
            check_period = timezone.now() - timedelta(hours=self.config.webhook_check_period_hours)
            failed_webhooks = FailedWebhook.objects.filter(
                created_at__gte=check_period,
                retry_count__gte=2
            ).count()
            
            severity = None
            if failed_webhooks >= self.config.webhook_failures_critical:
                severity = 'critical'
            elif failed_webhooks >= self.config.webhook_failures_warning:
                severity = 'warning'
            
            if severity:
                alert_key = f"webhook_failures_{severity}"
                if self.should_send_alert(alert_key, severity):
                    return {
                        'type': 'webhook_failures',
                        'severity': severity,
                        'message': f'{failed_webhooks} webhooks failed in the last {self.config.webhook_check_period_hours} hour(s)',
                        'metrics': {
                            'failed_webhooks': failed_webhooks,
                            'period_hours': self.config.webhook_check_period_hours
                        },
                        'timestamp': timezone.now().isoformat(),
                        'action_required': severity == 'critical'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking webhook failures: {e}")
            return None
    
    def check_subscription_churn(self) -> Optional[Dict]:
        """Check subscription cancellation rates"""
        try:
            check_period = timezone.now() - timedelta(hours=self.config.churn_check_period_hours)
            cancelled_subscriptions = Subscription.objects.filter(
                cancelled_at__gte=check_period
            ).count()
            
            severity = None
            if cancelled_subscriptions >= self.config.churn_critical:
                severity = 'critical'
            elif cancelled_subscriptions >= self.config.churn_warning:
                severity = 'warning'
            
            if severity:
                alert_key = f"subscription_churn_{severity}"
                if self.should_send_alert(alert_key, severity):
                    return {
                        'type': 'subscription_churn',
                        'severity': severity,
                        'message': f'{cancelled_subscriptions} subscriptions cancelled in the last {self.config.churn_check_period_hours} hour(s)',
                        'metrics': {
                            'cancelled_subscriptions': cancelled_subscriptions,
                            'period_hours': self.config.churn_check_period_hours
                        },
                        'timestamp': timezone.now().isoformat(),
                        'action_required': severity == 'critical'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking subscription churn: {e}")
            return None
    
    def should_send_alert(self, alert_key: str, severity: str) -> bool:
        """Check if we should send an alert based on cooldown periods"""
        now = timezone.now()
        
        if alert_key in self.alert_cache:
            last_sent = self.alert_cache[alert_key]
            cooldown_minutes = (
                self.config.alert_cooldown_critical 
                if severity == 'critical' 
                else self.config.alert_cooldown_warning
            )
            
            if now < last_sent + timedelta(minutes=cooldown_minutes):
                return False
        
        # Update cache
        self.alert_cache[alert_key] = now
        return True
    
    def process_alert(self, alert: Dict):
        """Process and send alert notifications"""
        try:
            # Log the alert
            logger.error(f"Payment Alert [{alert['severity'].upper()}]: {alert['message']}")
            
            # Log to audit system
            PaymentAuditService.log_payment_action(
                action='monitoring_alert',
                severity=alert['severity'],
                metadata={
                    'alert_type': alert['type'],
                    'message': alert['message'],
                    'metrics': alert.get('metrics', {}),
                    'action_required': alert.get('action_required', False)
                }
            )
            
            # Send email notifications
            if self.should_send_email_alert(alert):
                self.send_email_alert(alert)
            
            # Send webhook notifications (if configured)
            if self.should_send_webhook_alert(alert):
                self.send_webhook_alert(alert)
            
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
    
    def should_send_email_alert(self, alert: Dict) -> bool:
        """Determine if email should be sent for this alert"""
        # Send email for critical alerts or during business hours for warnings
        if alert['severity'] == 'critical':
            return True
        
        # For warnings, only send during business hours (9 AM - 6 PM Brazil time)
        now = timezone.now()
        if 9 <= now.hour <= 18:
            return True
        
        return False
    
    def send_email_alert(self, alert: Dict):
        """Send email alert to administrators"""
        try:
            recipients = getattr(settings, 'PAYMENT_ALERT_EMAILS', [
                'admin@financehub.com',
                'tech@financehub.com'
            ])
            
            if not recipients:
                return
            
            subject = f"[{alert['severity'].upper()}] Payment System Alert: {alert['type']}"
            
            # Create email content
            context = {
                'alert': alert,
                'timestamp': timezone.now(),
                'environment': 'production' if not settings.DEBUG else 'development'
            }
            
            message = f"""
Payment System Alert - {alert['severity'].upper()}

Type: {alert['type']}
Message: {alert['message']}
Timestamp: {alert['timestamp']}
Environment: {context['environment']}

Metrics:
{json.dumps(alert.get('metrics', {}), indent=2)}

Action Required: {'Yes' if alert.get('action_required') else 'No'}

This is an automated alert from the Finance Hub payment monitoring system.
"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False
            )
            
            logger.info(f"Email alert sent for {alert['type']} to {len(recipients)} recipients")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def should_send_webhook_alert(self, alert: Dict) -> bool:
        """Determine if webhook should be sent for this alert"""
        # Send webhook for all alerts if configured
        webhook_url = getattr(settings, 'PAYMENT_ALERT_WEBHOOK_URL', None)
        return webhook_url is not None
    
    def send_webhook_alert(self, alert: Dict):
        """Send webhook alert to external monitoring system"""
        try:
            webhook_url = getattr(settings, 'PAYMENT_ALERT_WEBHOOK_URL', None)
            if not webhook_url:
                return
            
            import requests
            
            payload = {
                'alert': alert,
                'service': 'finance_hub_payments',
                'environment': 'production' if not settings.DEBUG else 'development',
                'timestamp': timezone.now().isoformat()
            }
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            logger.info(f"Webhook alert sent for {alert['type']}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")


# Global monitor instance
payment_monitor = PaymentMonitor()


def run_monitoring_check():
    """Run monitoring checks - can be called from management command or celery task"""
    return payment_monitor.check_all_alerts()


# Celery task for periodic monitoring
try:
    from celery import shared_task
    
    @shared_task
    def check_payment_system_health():
        """Celery task to check payment system health"""
        logger.info("Running payment system health check")
        alerts = run_monitoring_check()
        
        return {
            'timestamp': timezone.now().isoformat(),
            'alerts_found': len(alerts),
            'alerts': alerts
        }
        
except ImportError:
    # Celery not available
    pass