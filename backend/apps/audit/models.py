import json
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = get_user_model()


class AuditLog(models.Model):
    """
    Model to store audit logs for compliance and security
    """
    
    # Event types
    EVENT_TYPES = [
        ('AUTH_LOGIN', 'User Login'),
        ('AUTH_LOGOUT', 'User Logout'),
        ('AUTH_FAILED_LOGIN', 'Failed Login Attempt'),
        ('AUTH_PASSWORD_CHANGE', 'Password Changed'),
        ('AUTH_PASSWORD_RESET', 'Password Reset'),
        ('AUTH_2FA_ENABLED', '2FA Enabled'),
        ('AUTH_2FA_DISABLED', '2FA Disabled'),
        
        ('USER_CREATED', 'User Created'),
        ('USER_UPDATED', 'User Updated'),
        ('USER_DELETED', 'User Deleted'),
        
        ('COMPANY_CREATED', 'Company Created'),
        ('COMPANY_UPDATED', 'Company Updated'),
        ('COMPANY_DELETED', 'Company Deleted'),
        
        ('PAYMENT_CREATED', 'Payment Created'),
        ('PAYMENT_SUCCESS', 'Payment Successful'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('PAYMENT_REFUNDED', 'Payment Refunded'),
        
        ('SUBSCRIPTION_CREATED', 'Subscription Created'),
        ('SUBSCRIPTION_UPDATED', 'Subscription Updated'),
        ('SUBSCRIPTION_CANCELLED', 'Subscription Cancelled'),
        
        ('BANK_ACCOUNT_CONNECTED', 'Bank Account Connected'),
        ('BANK_ACCOUNT_DISCONNECTED', 'Bank Account Disconnected'),
        ('BANK_SYNC_STARTED', 'Bank Sync Started'),
        ('BANK_SYNC_COMPLETED', 'Bank Sync Completed'),
        ('BANK_SYNC_FAILED', 'Bank Sync Failed'),
        
        ('TRANSACTION_CREATED', 'Transaction Created'),
        ('TRANSACTION_UPDATED', 'Transaction Updated'),
        ('TRANSACTION_DELETED', 'Transaction Deleted'),
        ('TRANSACTION_CATEGORIZED', 'Transaction Categorized'),
        
        ('REPORT_GENERATED', 'Report Generated'),
        ('REPORT_EXPORTED', 'Report Exported'),
        
        ('AI_REQUEST', 'AI Request Made'),
        ('AI_RESPONSE', 'AI Response Received'),
        
        ('DATA_EXPORT', 'Data Exported'),
        ('DATA_IMPORT', 'Data Imported'),
        
        ('SECURITY_ALERT', 'Security Alert'),
        ('PERMISSION_DENIED', 'Permission Denied'),
        ('RATE_LIMIT_EXCEEDED', 'Rate Limit Exceeded'),
    ]
    
    # Basic fields
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # User information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    company = models.ForeignKey('companies.Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    
    # Request information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=255, blank=True)
    
    # Object being acted upon (generic relation)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Event details
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Status
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['company', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.user} - {self.timestamp}"
