"""Audit service for payment activity logging and compliance"""
import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime, timedelta
from ..services.monitoring_service import MonitoringService, PaymentMetrics
from ..apm_integration import trace_payment_operation, monitor_db_queries

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger('payments.audit')
security_logger = logging.getLogger('payments.security')


class PaymentAuditService:
    """Service for logging payment-related activities for audit and compliance"""
    
    @staticmethod
    @trace_payment_operation('audit')
    def log_payment_action(
        action: str,
        user=None,
        company=None,
        subscription_id=None,
        payment_id=None,
        payment_method_id=None,
        metadata: Dict[str, Any] = None,
        severity='info',
        ip_address=None,
        user_agent=None,
        request_id=None,
        error_message=None
    ):
        """Log a payment-related action with monitoring integration"""
        from ..models_audit import PaymentAuditLog
        
        # Log to structured logger
        log_data = {
            'action': action,
            'severity': severity,
            'user_id': user.id if user else None,
            'company_id': company.id if company else None,
            'subscription_id': subscription_id,
            'payment_id': payment_id,
            'payment_method_id': payment_method_id,
            'ip_address': ip_address,
            'request_id': request_id,
            'metadata': metadata or {},
            'timestamp': timezone.now().isoformat()
        }
        
        audit_logger.info(f"audit.{action}", extra=log_data)
        
        # Log security events to security logger
        if action in ['suspicious_activity', 'access_denied', 'fraud_detected']:
            security_logger.warning(f"security.{action}", extra=log_data)
            
            # Send security alert
            MonitoringService.log_security_event(
                event_type=action,
                description=metadata.get('description', f'Security event: {action}'),
                user_id=user.id if user else None,
                ip_address=ip_address,
                metadata=metadata
            )
        
        # Record metrics
        PaymentMetrics.record_metric(f'audit_{action}', 1, 
                                   tags={'severity': severity})
        
        try:
            audit_log = PaymentAuditLog.objects.create(
                action=action,
                severity=severity,
                user=user,
                company=company,
                subscription_id=subscription_id,
                payment_id=payment_id,
                payment_method_id=payment_method_id,
                ip_address=ip_address,
                user_agent=user_agent or '',
                request_id=request_id or '',
                metadata=metadata or {},
                error_message=error_message or '',
                timestamp=timezone.now()
            )
            
            # Set data retention date (e.g., 7 years for financial records)
            audit_log.data_retention_date = timezone.now() + timedelta(days=365 * 7)
            audit_log.save()
            
            logger.info(
                f"Audit log created: {action} for company {company.id if company else 'N/A'}"
            )
            
            return audit_log
            
        except Exception as e:
            error_msg = str(e)
            if 'relation "payments_paymentauditlog" does not exist' in error_msg:
                logger.warning(f"PaymentAuditLog table not ready yet - skipping audit log for action: {action}")
            else:
                logger.error(f"Failed to create audit log: {e}")
            # Don't raise exception - audit logging should not break the flow
            return None
    
    @staticmethod
    def log_subscription_created(subscription, user=None, **kwargs):
        """Log subscription creation"""
        return PaymentAuditService.log_payment_action(
            action='subscription_created',
            user=user,
            company=subscription.company,
            subscription_id=subscription.id,
            metadata={
                'plan': subscription.plan.name,
                'billing_period': subscription.billing_period,
                'status': subscription.status,
                'trial_ends_at': subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None
            },
            **kwargs
        )
    
    @staticmethod
    def log_payment_attempt(payment, user=None, **kwargs):
        """Log payment attempt"""
        action = 'payment_initiated'
        severity = 'info'
        
        if payment.status == 'succeeded':
            action = 'payment_succeeded'
        elif payment.status == 'failed':
            action = 'payment_failed'
            severity = 'warning'
        
        return PaymentAuditService.log_payment_action(
            action=action,
            severity=severity,
            user=user,
            company=payment.company,
            payment_id=payment.id,
            subscription_id=payment.subscription.id if payment.subscription else None,
            metadata={
                'amount': str(payment.amount),
                'currency': payment.currency,
                'gateway': payment.gateway,
                'status': payment.status,
                'description': payment.description
            },
            **kwargs
        )
    
    @staticmethod
    def log_payment_method_action(action_type, payment_method, user=None, **kwargs):
        """Log payment method related actions"""
        return PaymentAuditService.log_payment_action(
            action=f'payment_method_{action_type}',
            user=user,
            company=payment_method.company,
            payment_method_id=payment_method.id,
            metadata={
                'type': payment_method.type,
                'brand': payment_method.brand,
                'last4': payment_method.last4,
                'is_default': payment_method.is_default
            },
            **kwargs
        )
    
    @staticmethod
    def log_webhook_event(event_type, event_id, status='processed', error=None, **kwargs):
        """Log webhook processing"""
        action = 'webhook_processed' if status == 'processed' else 'webhook_failed'
        severity = 'info' if status == 'processed' else 'error'
        
        return PaymentAuditService.log_payment_action(
            action=action,
            severity=severity,
            metadata={
                'event_type': event_type,
                'event_id': event_id,
                'status': status
            },
            error_message=error,
            **kwargs
        )
    
    @staticmethod
    def log_suspicious_activity(activity_type, user=None, company=None, details=None, **kwargs):
        """Log suspicious payment activity"""
        return PaymentAuditService.log_payment_action(
            action='suspicious_activity',
            severity='warning',
            user=user,
            company=company,
            metadata={
                'activity_type': activity_type,
                'details': details or {}
            },
            **kwargs
        )
    
    @staticmethod
    def log_security_event(event_type, user=None, company=None, details=None, **kwargs):
        """Log security-related events"""
        severity_map = {
            'access_denied': 'warning',
            'fraud_detected': 'critical',
            'rate_limit_exceeded': 'warning',
            'invalid_signature': 'error'
        }
        
        return PaymentAuditService.log_payment_action(
            action=event_type,
            severity=severity_map.get(event_type, 'warning'),
            user=user,
            company=company,
            metadata={
                'event_type': event_type,
                'details': details or {}
            },
            **kwargs
        )
    
    @staticmethod
    def log_payment_validated(company, user=None, metadata=None, **kwargs):
        """Log payment validation event"""
        return PaymentAuditService.log_payment_action(
            action='payment_validated',
            severity='info',
            user=user,
            company=company,
            status='success',
            metadata=metadata or {},
            **kwargs
        )
    
    @staticmethod
    @transaction.atomic
    def update_daily_summary(company, date=None):
        """Update daily payment activity summary"""
        from ..models_audit import PaymentActivitySummary
        from ..models import Payment, Subscription
        
        if not date:
            date = timezone.now().date()
        
        # Get or create summary for the day
        summary, created = PaymentActivitySummary.objects.get_or_create(
            company=company,
            date=date
        )
        
        # Calculate payment metrics
        daily_payments = Payment.objects.filter(
            company=company,
            created_at__date=date
        )
        
        summary.total_payments = daily_payments.count()
        summary.successful_payments = daily_payments.filter(status='succeeded').count()
        summary.failed_payments = daily_payments.filter(status='failed').count()
        
        summary.total_amount = sum(p.amount for p in daily_payments)
        summary.successful_amount = sum(
            p.amount for p in daily_payments.filter(status='succeeded')
        )
        summary.failed_amount = sum(
            p.amount for p in daily_payments.filter(status='failed')
        )
        
        # Calculate subscription metrics
        daily_subscriptions = Subscription.objects.filter(
            company=company,
            created_at__date=date
        )
        
        summary.new_subscriptions = daily_subscriptions.count()
        summary.cancelled_subscriptions = Subscription.objects.filter(
            company=company,
            cancelled_at__date=date
        ).count()
        
        # Calculate security metrics from audit logs
        from ..models_audit import PaymentAuditLog
        
        summary.suspicious_activities = PaymentAuditLog.objects.filter(
            company=company,
            timestamp__date=date,
            action='suspicious_activity'
        ).count()
        
        summary.blocked_transactions = PaymentAuditLog.objects.filter(
            company=company,
            timestamp__date=date,
            action='access_denied'
        ).count()
        
        summary.save()
        
        return summary
    
    @staticmethod
    def cleanup_old_logs(days_to_keep=2555):  # 7 years default
        """Clean up old audit logs past retention period"""
        from ..models_audit import PaymentAuditLog
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # First redact PII from logs older than 90 days
        recent_cutoff = timezone.now() - timedelta(days=90)
        logs_to_redact = PaymentAuditLog.objects.filter(
            timestamp__lt=recent_cutoff,
            is_pii_redacted=False
        )
        
        for log in logs_to_redact.iterator():
            log.redact_pii()
        
        # Delete logs past retention period
        deleted_count = PaymentAuditLog.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old audit logs")
        
        return deleted_count
    
    @staticmethod
    def get_audit_report(company, start_date, end_date, action_filter=None):
        """Generate audit report for a date range"""
        from ..models_audit import PaymentAuditLog
        
        queryset = PaymentAuditLog.objects.filter(
            company=company,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        if action_filter:
            queryset = queryset.filter(action__in=action_filter)
        
        # Group by action and severity
        report = {
            'total_events': queryset.count(),
            'by_action': {},
            'by_severity': {
                'info': 0,
                'warning': 0,
                'error': 0,
                'critical': 0
            },
            'suspicious_activities': [],
            'failed_payments': []
        }
        
        for log in queryset:
            # Count by action
            if log.action not in report['by_action']:
                report['by_action'][log.action] = 0
            report['by_action'][log.action] += 1
            
            # Count by severity
            report['by_severity'][log.severity] += 1
            
            # Collect suspicious activities
            if log.action == 'suspicious_activity':
                report['suspicious_activities'].append({
                    'timestamp': log.timestamp,
                    'metadata': log.metadata,
                    'user_id': log.user_id
                })
            
            # Collect failed payments
            if log.action == 'payment_failed':
                report['failed_payments'].append({
                    'timestamp': log.timestamp,
                    'payment_id': log.payment_id,
                    'amount': log.metadata.get('amount'),
                    'error': log.error_message
                })
        
        return report