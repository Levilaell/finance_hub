"""
Company Models - PRIMARY MODEL FILE

This is the ACTIVE and PRIMARY model file for the companies app.
DO NOT use models_consolidated.py or legacy/models.py - they are deprecated.

Contains:
- Company: Multi-tenant company management with subscription tracking
- SubscriptionPlan: Subscription plan definitions with limits and features  
- ResourceUsage: Historical usage tracking for billing and analytics

Architecture decisions:
- Subscription logic kept in companies app for simplicity
- Atomic usage tracking with F expressions to prevent race conditions
- Company-scoped data isolation for security
"""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class SubscriptionPlan(models.Model):
    """
    Simple subscription plan model with essential fields only
    """
    # Core identifiers
    name = models.CharField(_('name'), max_length=50)
    slug = models.SlugField(_('slug'), unique=True)
    
    # Pricing
    price_monthly = models.DecimalField(_('monthly price'), max_digits=8, decimal_places=2)
    price_yearly = models.DecimalField(_('yearly price'), max_digits=8, decimal_places=2)
    
    # Essential limits
    max_transactions = models.IntegerField(_('max transactions'), default=500)
    max_bank_accounts = models.IntegerField(_('max bank accounts'), default=1)
    max_ai_requests = models.IntegerField(_('max AI requests'), default=100)
    
    # Feature flags
    has_ai_insights = models.BooleanField(_('AI insights'), default=False)
    has_advanced_reports = models.BooleanField(_('advanced reports'), default=False)
    
    # Payment gateway IDs
    stripe_price_id_monthly = models.CharField(max_length=255, blank=True)
    stripe_price_id_yearly = models.CharField(max_length=255, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'subscription_plans'
        ordering = ['display_order', 'price_monthly']
    
    def __str__(self):
        return f"{self.name} - ${self.price_monthly}/mo"


class Company(models.Model):
    """
    Simplified company model - Essential fields only
    """
    # Owner
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company')
    name = models.CharField(_('company name'), max_length=200)
    
    # Subscription
    subscription_plan = models.ForeignKey(
        SubscriptionPlan, 
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    subscription_status = models.CharField(
        _('status'),
        max_length=20,
        choices=[
            ('trial', 'Trial'),
            ('active', 'Active'),
            ('cancelled', 'Cancelled'),
            ('expired', 'Expired'),
        ],
        default='trial'
    )
    
    # Billing
    billing_cycle = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')],
        default='monthly'
    )
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    subscription_id = models.CharField(max_length=255, blank=True)  # Stripe subscription ID
    
    # Usage tracking
    current_month_transactions = models.IntegerField(default=0)
    current_month_ai_requests = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'companies'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Set trial on creation
        if not self.pk and not self.trial_ends_at:
            self.trial_ends_at = timezone.now() + timedelta(days=14)
            self.subscription_status = 'trial'
        super().save(*args, **kwargs)
    
    @property
    def is_trial_active(self):
        """Check if trial is still active"""
        if self.subscription_status != 'trial':
            return False
        return self.trial_ends_at and timezone.now() < self.trial_ends_at
    
    @property
    def days_until_trial_ends(self):
        """Calculate days remaining in trial"""
        if not self.is_trial_active:
            return 0
        delta = self.trial_ends_at - timezone.now()
        return max(0, delta.days)
    
    def can_use_feature(self, feature):
        """Simple feature access check"""
        if not self.subscription_plan:
            return False
        
        feature_map = {
            'ai_insights': self.subscription_plan.has_ai_insights,
            'advanced_reports': self.subscription_plan.has_advanced_reports,
        }
        
        return feature_map.get(feature, False)
    
    def check_limit(self, limit_type):
        """Check if limit is reached"""
        if not self.subscription_plan:
            return True, "No active plan"
        
        limits = {
            'transactions': (
                self.current_month_transactions,
                self.subscription_plan.max_transactions
            ),
            'bank_accounts': (
                self.bank_accounts.filter(is_active=True).count(),
                self.subscription_plan.max_bank_accounts
            ),
            'ai_requests': (
                self.current_month_ai_requests,
                self.subscription_plan.max_ai_requests
            ),
        }
        
        if limit_type not in limits:
            return False, "Unknown limit type"
        
        current, maximum = limits[limit_type]
        return current >= maximum, f"{current}/{maximum}"
    
    @transaction.atomic
    def increment_usage(self, usage_type):
        """
        Increment usage counters atomically to prevent race conditions.
        Uses F expressions for atomic database operations.
        """
        if usage_type == 'transactions':
            # Use F expression for atomic increment
            Company.objects.filter(pk=self.pk).update(
                current_month_transactions=F('current_month_transactions') + 1
            )
            # Refresh from DB to get updated value
            self.refresh_from_db(fields=['current_month_transactions'])
            
            # Also update ResourceUsage
            self._update_resource_usage('transactions_count', 1)
            
        elif usage_type == 'ai_requests':
            # Use F expression for atomic increment
            Company.objects.filter(pk=self.pk).update(
                current_month_ai_requests=F('current_month_ai_requests') + 1
            )
            # Refresh from DB to get updated value
            self.refresh_from_db(fields=['current_month_ai_requests'])
            
            # Also update ResourceUsage
            self._update_resource_usage('ai_requests_count', 1)
    
    def _update_resource_usage(self, field_name, increment_by=1):
        """Update ResourceUsage record atomically"""
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        
        # Get or create the usage record
        usage, created = ResourceUsage.objects.get_or_create(
            company=self,
            month=month_start,
            defaults={
                'transactions_count': self.current_month_transactions if field_name == 'transactions_count' else 0,
                'ai_requests_count': self.current_month_ai_requests if field_name == 'ai_requests_count' else 0,
            }
        )
        
        # Update atomically if not just created
        if not created:
            ResourceUsage.objects.filter(pk=usage.pk).update(
                **{field_name: F(field_name) + increment_by}
            )
    
    @transaction.atomic
    def reset_monthly_usage(self):
        """Reset monthly counters atomically"""
        Company.objects.filter(pk=self.pk).update(
            current_month_transactions=0,
            current_month_ai_requests=0
        )
        self.refresh_from_db(fields=['current_month_transactions', 'current_month_ai_requests'])


class ResourceUsage(models.Model):
    """
    Track historical usage for billing
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='usage_history')
    month = models.DateField(help_text='First day of the month')
    
    # Counters
    transactions_count = models.IntegerField(default=0)
    ai_requests_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'resource_usage'
        unique_together = ['company', 'month']
        ordering = ['-month']
    
    def __str__(self):
        return f"{self.company.name} - {self.month.strftime('%B %Y')}"
    
    @classmethod
    @transaction.atomic
    def get_or_create_current_month(cls, company):
        """
        Get or create ResourceUsage for current month atomically.
        Ensures thread-safe creation of monthly usage records.
        """
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        
        usage, created = cls.objects.get_or_create(
            company=company,
            month=month_start,
            defaults={
                'transactions_count': company.current_month_transactions,
                'ai_requests_count': company.current_month_ai_requests,
            }
        )
        
        return usage