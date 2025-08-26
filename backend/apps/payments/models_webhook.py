"""
Webhook event tracking models for database-level idempotency
"""
from django.db import models
from django.utils import timezone


class WebhookEvent(models.Model):
    """
    Track processed webhook events for idempotency and audit
    """
    EVENT_SOURCES = [
        ('stripe', 'Stripe'),
        ('mercadopago', 'MercadoPago'),  # Future support
        ('paypal', 'PayPal'),  # Future support
    ]
    
    EVENT_TYPES = [
        ('checkout.session.completed', 'Checkout Session Completed'),
        ('invoice.payment_succeeded', 'Invoice Payment Succeeded'),
        ('invoice.payment_failed', 'Invoice Payment Failed'),
        ('customer.subscription.created', 'Subscription Created'),
        ('customer.subscription.updated', 'Subscription Updated'),
        ('customer.subscription.deleted', 'Subscription Deleted'),
        ('payment_intent.succeeded', 'Payment Intent Succeeded'),
        ('payment_intent.payment_failed', 'Payment Intent Failed'),
        ('setup_intent.succeeded', 'Setup Intent Succeeded'),
    ]
    
    PROCESSING_STATUS = [
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('ignored', 'Ignored'),  # Duplicate or irrelevant
    ]
    
    # Event identification
    event_id = models.CharField(
        max_length=255, 
        unique=True, 
        db_index=True,
        help_text="Unique event ID from payment gateway"
    )
    source = models.CharField(
        max_length=20, 
        choices=EVENT_SOURCES,
        default='stripe',
        db_index=True
    )
    event_type = models.CharField(
        max_length=50, 
        choices=EVENT_TYPES,
        db_index=True
    )
    
    # Processing status
    status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS,
        default='received',
        db_index=True
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Event data
    raw_event = models.JSONField(
        help_text="Raw webhook event data (sanitized)"
    )
    processed_data = models.JSONField(
        null=True, 
        blank=True,
        help_text="Extracted/processed data from event"
    )
    
    # Relationships
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='webhook_events'
    )
    subscription = models.ForeignKey(
        'Subscription',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='webhook_events'
    )
    payment = models.ForeignKey(
        'Payment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='webhook_events'
    )
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_webhook_event'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_id', 'source']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['event_type', 'status']),
            models.Index(fields=['company', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.source}:{self.event_type} - {self.event_id}"
    
    def mark_processing(self):
        """Mark event as currently being processed"""
        self.status = 'processing'
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_completed(self, processed_data=None):
        """Mark event as successfully processed"""
        self.status = 'completed'
        self.processed_at = timezone.now()
        if processed_data:
            self.processed_data = processed_data
        self.save(update_fields=['status', 'processed_at', 'processed_data', 'updated_at'])
    
    def mark_failed(self, error_message):
        """Mark event as failed with error message"""
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count', 'updated_at'])
    
    def mark_ignored(self, reason="Duplicate event"):
        """Mark event as ignored (typically duplicates)"""
        self.status = 'ignored'
        self.error_message = reason
        self.save(update_fields=['status', 'error_message', 'updated_at'])
    
    @property
    def is_processed(self):
        """Check if event has been processed (completed or ignored)"""
        return self.status in ['completed', 'ignored']
    
    @property
    def should_retry(self):
        """Check if event should be retried"""
        return self.status == 'failed' and self.retry_count < 3
    
    @classmethod
    def is_duplicate(cls, event_id, source='stripe'):
        """Check if event has already been processed"""
        return cls.objects.filter(
            event_id=event_id,
            source=source,
            status__in=['completed', 'ignored']
        ).exists()
    
    @classmethod
    def create_from_webhook(cls, event_id, event_type, raw_event, source='stripe', ip_address=None, user_agent=None):
        """Create webhook event record from incoming webhook"""
        return cls.objects.create(
            event_id=event_id,
            source=source,
            event_type=event_type,
            raw_event=raw_event,
            ip_address=ip_address,
            user_agent=user_agent
        )


class WebhookDeliveryAttempt(models.Model):
    """
    Track webhook delivery attempts for monitoring and debugging
    """
    webhook_event = models.ForeignKey(
        WebhookEvent,
        on_delete=models.CASCADE,
        related_name='delivery_attempts'
    )
    
    # Attempt details
    attempt_number = models.IntegerField()
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    # Response details
    http_status = models.IntegerField(null=True, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    response_headers = models.JSONField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    
    # Error details
    error_type = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    
    # Success flag
    successful = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'payments_webhook_delivery_attempt'
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['webhook_event', 'attempt_number']),
            models.Index(fields=['successful', 'attempted_at']),
        ]
    
    def __str__(self):
        status = "SUCCESS" if self.successful else "FAILED"
        return f"Attempt {self.attempt_number} - {status} - {self.webhook_event.event_id}"