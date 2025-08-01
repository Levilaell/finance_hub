"""
Consolidated Company models - Using payment app for subscription data
"""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Company(models.Model):
    """
    Simplified company model - Subscription data moved to payments.Subscription
    """
    # Owner
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company')
    name = models.CharField(_('company name'), max_length=200)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Usage tracking - Keep these for quick access and atomic operations
    current_month_transactions = models.IntegerField(default=0)
    current_month_ai_requests = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'companies'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Create company first
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # Create default subscription on company creation
        if is_new:
            from apps.payments.models import Subscription
            Subscription.objects.create(
                company=self,
                status='trial',
                trial_ends_at=timezone.now() + timedelta(days=14)
            )
    
    # Proxy properties to subscription
    @property
    def subscription(self):
        """Get related subscription from payments app"""
        return getattr(self, 'subscription', None)
    
    @property
    def subscription_plan(self):
        """Get subscription plan through subscription"""
        if self.subscription:
            return self.subscription.plan
        return None
    
    @property
    def subscription_status(self):
        """Get subscription status"""
        if self.subscription:
            return self.subscription.status
        return 'trial'
    
    @property
    def billing_cycle(self):
        """Get billing cycle"""
        if self.subscription:
            return self.subscription.billing_period
        return 'monthly'
    
    @property
    def trial_ends_at(self):
        """Get trial end date"""
        if self.subscription:
            return self.subscription.trial_ends_at
        return None
    
    @property
    def subscription_id(self):
        """Get payment gateway subscription ID"""
        if self.subscription:
            return self.subscription.stripe_subscription_id
        return None
    
    @property
    def is_trial_active(self):
        """Check if trial is still active"""
        if self.subscription:
            return self.subscription.is_trial and self.subscription.trial_days_remaining > 0
        return False
    
    @property
    def days_until_trial_ends(self):
        """Calculate days remaining in trial"""
        if self.subscription:
            return self.subscription.trial_days_remaining
        return 0
    
    def can_use_feature(self, feature):
        """Simple feature access check"""
        if self.subscription:
            return self.subscription.can_use_feature(feature)
        return False
    
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