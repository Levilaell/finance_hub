"""Audit models for payment tracking and compliance"""
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.utils import timezone

User = get_user_model()


class PaymentAuditLog(models.Model):
    """Comprehensive audit log for payment-related activities"""
    
    ACTION_TYPES = [
        # Subscription actions
        ('subscription_created', 'Subscription Created'),
        ('subscription_activated', 'Subscription Activated'),
        ('subscription_cancelled', 'Subscription Cancelled'),
        ('subscription_expired', 'Subscription Expired'),
        ('subscription_plan_changed', 'Subscription Plan Changed'),
        
        # Payment actions
        ('payment_initiated', 'Payment Initiated'),
        ('payment_succeeded', 'Payment Succeeded'),
        ('payment_failed', 'Payment Failed'),
        ('payment_refunded', 'Payment Refunded'),
        ('payment_disputed', 'Payment Disputed'),
        
        # Payment method actions
        ('payment_method_added', 'Payment Method Added'),
        ('payment_method_updated', 'Payment Method Updated'),
        ('payment_method_removed', 'Payment Method Removed'),
        ('payment_method_set_default', 'Payment Method Set as Default'),
        
        # Webhook actions
        ('webhook_received', 'Webhook Received'),
        ('webhook_processed', 'Webhook Processed'),
        ('webhook_failed', 'Webhook Failed'),
        
        # Security actions
        ('suspicious_activity', 'Suspicious Activity Detected'),
        ('fraud_detected', 'Fraud Detected'),
        ('access_denied', 'Access Denied'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    # Core fields
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='info')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # User and company context
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey('companies.Company', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment context
    subscription_id = models.IntegerField(null=True, blank=True)
    payment_id = models.IntegerField(null=True, blank=True)
    payment_method_id = models.IntegerField(null=True, blank=True)
    
    # Request context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_id = models.CharField(max_length=255, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    # Compliance fields
    data_retention_date = models.DateTimeField(null=True, blank=True)
    is_pii_redacted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'action']),
            models.Index(fields=['company', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['severity', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.timestamp} - {self.action} - {self.severity}"
    
    def redact_pii(self):
        """Redact personally identifiable information for compliance"""
        if self.is_pii_redacted:
            return
        
        # Redact sensitive fields
        redacted_metadata = self.metadata.copy()
        sensitive_keys = ['card_number', 'cvv', 'email', 'phone', 'ssn', 'tax_id']
        
        for key in sensitive_keys:
            if key in redacted_metadata:
                redacted_metadata[key] = '[REDACTED]'
        
        # Redact nested sensitive data
        if 'payment_method' in redacted_metadata:
            pm = redacted_metadata['payment_method']
            if isinstance(pm, dict):
                if 'card' in pm:
                    pm['card'] = {
                        'brand': pm['card'].get('brand', '[REDACTED]'),
                        'last4': pm['card'].get('last4', '[REDACTED]'),
                        'exp_month': '[REDACTED]',
                        'exp_year': '[REDACTED]'
                    }
        
        self.metadata = redacted_metadata
        self.is_pii_redacted = True
        self.save()


class PaymentActivitySummary(models.Model):
    """Daily summary of payment activities for reporting"""
    
    date = models.DateField(db_index=True)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    
    # Transaction counts
    total_payments = models.IntegerField(default=0)
    successful_payments = models.IntegerField(default=0)
    failed_payments = models.IntegerField(default=0)
    
    # Amount totals
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    successful_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    failed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Subscription metrics
    new_subscriptions = models.IntegerField(default=0)
    cancelled_subscriptions = models.IntegerField(default=0)
    plan_changes = models.IntegerField(default=0)
    
    # Security metrics
    suspicious_activities = models.IntegerField(default=0)
    blocked_transactions = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['date', 'company']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.company.name} - {self.date}"