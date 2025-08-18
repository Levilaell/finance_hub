from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

# Import SubscriptionPlan from companies to avoid duplication
from apps.companies.models import SubscriptionPlan


class Subscription(models.Model):
    """Company subscription status"""
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('past_due', 'Past Due'),
    ]
    
    company = models.OneToOneField(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    billing_period = models.CharField(
        max_length=10, 
        choices=SubscriptionPlan.BILLING_PERIODS,
        default='monthly'
    )
    
    # Payment gateway references
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Dates
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.company.name} - {self.plan.display_name} ({self.status})"
    
    @property
    def is_active(self):
        return self.status in ['active', 'trial']
    
    @property
    def is_trial(self):
        return self.status == 'trial'
    
    @property
    def trial_days_remaining(self):
        if not self.trial_ends_at:
            return 0
        delta = self.trial_ends_at - timezone.now()
        return max(0, delta.days)
    
    def can_use_feature(self, feature_name):
        """Check if subscription allows feature usage"""
        if not self.is_active:
            return False
        return self.plan.features.get(feature_name, False)


class PaymentMethod(models.Model):
    """Stored payment methods"""
    PAYMENT_TYPES = [
        ('card', 'Credit/Debit Card'),
        ('bank_account', 'Bank Account'),
        ('pix', 'PIX'),
    ]
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    is_default = models.BooleanField(default=False)
    
    # Payment gateway references
    stripe_payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    # mercadopago_card_id = models.CharField(max_length=255, blank=True, null=True)  # Removed - Stripe only
    
    # Display info
    brand = models.CharField(max_length=50, blank=True)  # visa, mastercard, etc
    last4 = models.CharField(max_length=4, blank=True)
    exp_month = models.IntegerField(null=True, blank=True)
    exp_year = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        if self.type == 'card':
            return f"{self.brand} ****{self.last4}"
        return f"{self.get_type_display()}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default per company
        if self.is_default:
            PaymentMethod.objects.filter(
                company=self.company,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Payment transaction record"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    
    # Transaction details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='BRL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    description = models.CharField(max_length=255)
    
    # Payment gateway references
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_invoice_id = models.CharField(max_length=255, blank=True, null=True)
    # mercadopago_payment_id = models.CharField(max_length=255, blank=True, null=True)  # Removed - Stripe only
    
    # Metadata
    gateway = models.CharField(max_length=20, default='stripe')  # Stripe only - MercadoPago removed
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.company.name} - {self.amount} {self.currency} ({self.status})"
    
    @property
    def is_successful(self):
        return self.status == 'succeeded'


class UsageRecord(models.Model):
    """Track feature usage for billing and limits"""
    USAGE_TYPES = [
        ('transaction', 'Transaction'),
        ('bank_account', 'Bank Account'),
        ('ai_request', 'AI Request'),
        ('ai_operation', 'AI Operation'),
        ('custom', 'Custom Usage'),
    ]
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='usage_records'
    )
    usage_type = models.CharField(max_length=20, choices=USAGE_TYPES, db_column='type')
    quantity = models.IntegerField(default=1)
    unit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    description = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Legacy fields for backward compatibility
    count = models.IntegerField(default=0)
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'usage_type', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.company.name} - {self.usage_type} - {self.quantity}"
    
    def __str__(self):
        return f"{self.company.name} - {self.type}: {self.count}"
    
    @classmethod
    def get_current_usage(cls, company, usage_type):
        """Get current billing period usage"""
        now = timezone.now()
        record, created = cls.objects.get_or_create(
            company=company,
            usage_type=usage_type,
            period_start__lte=now,
            period_end__gte=now,
            defaults={
                'period_start': now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                'period_end': (now.replace(day=1) + timezone.timedelta(days=31)).replace(day=1) - timezone.timedelta(seconds=1),
                'count': 0
            }
        )
        return record
    
    def increment(self, amount=1):
        """Increment usage count"""
        from django.db.models import F
        # Use F() expression for atomic update
        self.__class__.objects.filter(pk=self.pk).update(
            count=F('count') + amount,
            updated_at=timezone.now()
        )
        # Refresh from database
        self.refresh_from_db()
        return self.count


class FailedWebhook(models.Model):
    """Store failed webhooks for retry"""
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    event_data = models.JSONField()
    error_message = models.TextField()
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=5)
    next_retry_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['next_retry_at']
        indexes = [
            models.Index(fields=['next_retry_at', 'retry_count']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.event_id} (retry {self.retry_count})"
    
    def should_retry(self):
        return self.retry_count < self.max_retries and timezone.now() >= self.next_retry_at
    
    def increment_retry(self):
        """Increment retry count and set next retry time"""
        self.retry_count += 1
        # Exponential backoff: 5min, 15min, 45min, 2hr, 6hr
        backoff_minutes = [5, 15, 45, 120, 360]
        minutes = backoff_minutes[min(self.retry_count - 1, len(backoff_minutes) - 1)]
        self.next_retry_at = timezone.now() + timezone.timedelta(minutes=minutes)
        self.save()


class CreditTransaction(models.Model):
    """Track AI credit purchases and consumption"""
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('usage', 'Usage'),
        ('refund', 'Refund'),
        ('adjustment', 'Adjustment'),
        ('expiry', 'Expiry'),
    ]
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='payment_credit_transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    credits = models.IntegerField()  # Positive for additions, negative for usage
    balance_before = models.IntegerField(default=0)
    balance_after = models.IntegerField(default=0)
    description = models.CharField(max_length=255)
    
    # Related payment for purchases
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_transactions'
    )
    
    # Metadata for tracking
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'transaction_type', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        action = '+' if self.credits > 0 else ''
        return f"{self.company.name} - {action}{self.credits} credits - {self.transaction_type}"
    
    @property
    def is_credit(self):
        """Check if this transaction adds credits"""
        return self.credits > 0
    
    @property
    def is_debit(self):
        """Check if this transaction removes credits"""
        return self.credits < 0


