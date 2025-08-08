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
    plan_type = models.CharField(_('plan type'), max_length=20, default='standard')
    trial_days = models.IntegerField(_('trial days'), default=14)
    
    # Pricing
    price_monthly = models.DecimalField(_('monthly price'), max_digits=8, decimal_places=2)
    price_yearly = models.DecimalField(_('yearly price'), max_digits=8, decimal_places=2)
    
    # Essential limits
    max_transactions = models.IntegerField(_('max transactions'), default=500)
    max_bank_accounts = models.IntegerField(_('max bank accounts'), default=1)
    max_ai_requests_per_month = models.IntegerField(_('max AI requests per month'), default=100)
    
    # Feature flags
    has_ai_categorization = models.BooleanField(_('AI categorization'), default=False)
    enable_ai_insights = models.BooleanField(_('AI insights'), default=False)
    enable_ai_reports = models.BooleanField(_('AI reports'), default=False)
    has_advanced_reports = models.BooleanField(_('advanced reports'), default=False)
    has_api_access = models.BooleanField(_('API access'), default=False)
    has_accountant_access = models.BooleanField(_('accountant access'), default=False)
    has_priority_support = models.BooleanField(_('priority support'), default=False)
    
    # Payment gateway IDs
    stripe_price_id_monthly = models.CharField(max_length=255, blank=True)
    stripe_price_id_yearly = models.CharField(max_length=255, blank=True)
    mercadopago_plan_id = models.CharField(max_length=255, blank=True)
    
    # Display and status
    display_order = models.IntegerField(_('display order'), default=0)
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'subscription_plans'
        ordering = ['display_order', 'price_monthly']
    
    def __str__(self):
        return f"{self.name} - ${self.price_monthly}/mo"


class Company(models.Model):
    """
    Complete company model matching database schema
    """
    # Owner
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company')
    
    # Company Information
    name = models.CharField(_('company name'), max_length=200)
    trade_name = models.CharField(_('trade name'), max_length=200)
    cnpj = models.CharField(_('CNPJ'), max_length=18, blank=True, unique=True, null=True)
    company_type = models.CharField(_('company type'), max_length=20, default='LTDA')
    business_sector = models.CharField(_('business sector'), max_length=50, default='Technology')
    
    # Contact Information
    email = models.EmailField(_('email'), max_length=254, default='')
    phone = models.CharField(_('phone'), max_length=20, default='')
    website = models.URLField(_('website'), max_length=200, blank=True, default='')
    
    # Address
    address_street = models.CharField(_('street'), max_length=200, default='')
    address_number = models.CharField(_('number'), max_length=20, default='')
    address_complement = models.CharField(_('complement'), max_length=100, blank=True, default='')
    address_neighborhood = models.CharField(_('neighborhood'), max_length=100, default='')
    address_city = models.CharField(_('city'), max_length=100, default='')
    address_state = models.CharField(_('state'), max_length=2, default='')
    address_zipcode = models.CharField(_('zipcode'), max_length=10, default='')
    
    # Business Data
    monthly_revenue = models.DecimalField(_('monthly revenue'), max_digits=12, decimal_places=2, null=True, blank=True)
    employee_count = models.IntegerField(_('employee count'), default=1)
    
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
    next_billing_date = models.DateField(null=True, blank=True)
    subscription_id = models.CharField(max_length=255, blank=True)  # Stripe subscription ID
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    
    # Usage tracking
    current_month_transactions = models.IntegerField(default=0)
    current_month_ai_requests = models.IntegerField(default=0)
    last_usage_reset = models.DateTimeField(auto_now_add=True)
    
    # AI Credits
    ai_credits_balance = models.IntegerField(default=0, help_text='Current AI credits balance')
    
    # Notification flags
    notified_80_percent = models.BooleanField(default=False)
    notified_90_percent = models.BooleanField(default=False)
    
    # Branding
    logo = models.ImageField(_('logo'), upload_to='company_logos/', blank=True, null=True)
    primary_color = models.CharField(_('primary color'), max_length=7, default='#007bff')
    
    # Localization
    currency = models.CharField(_('currency'), max_length=3, default='BRL')
    fiscal_year_start = models.CharField(_('fiscal year start'), max_length=2, default='01')
    
    # Feature flags
    enable_ai_categorization = models.BooleanField(_('enable AI categorization'), default=True)
    auto_categorize_threshold = models.FloatField(_('auto categorize threshold'), default=0.8)
    enable_notifications = models.BooleanField(_('enable notifications'), default=True)
    enable_email_reports = models.BooleanField(_('enable email reports'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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
            'ai_insights': self.subscription_plan.enable_ai_insights,
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
                self.subscription_plan.max_ai_requests_per_month
            ),
        }
        
        if limit_type not in limits:
            return False, "Unknown limit type"
        
        current, maximum = limits[limit_type]
        return current >= maximum, f"{current}/{maximum}"
    
    def check_plan_limits(self, limit_type):
        """Check plan limits - alias for check_limit for compatibility"""
        return self.check_limit(limit_type)
    
    def can_add_bank_account(self):
        """Check if company can add more bank accounts"""
        if not self.subscription_plan:
            return False
        
        current_count = self.bank_accounts.filter(is_active=True).count()
        return current_count < self.subscription_plan.max_bank_accounts
    
    def can_use_ai_insight(self):
        """Check if company can use AI insights"""
        if not self.subscription_plan:
            return False, "No active subscription plan"
        
        # Check if AI insights are enabled for the plan
        if not self.subscription_plan.enable_ai_insights:
            return False, "AI insights not available in your plan"
        
        # Check usage limits
        if self.current_month_ai_requests >= self.subscription_plan.max_ai_requests_per_month:
            return False, "Monthly AI request limit reached"
        
        return True, "AI insights available"
    
    def get_usage_percentage(self, usage_type):
        """Get usage percentage for a specific limit type"""
        if not self.subscription_plan:
            return 0
        
        if usage_type == 'transactions':
            if self.subscription_plan.max_transactions == 0:
                return 0
            return (self.current_month_transactions / self.subscription_plan.max_transactions) * 100
        elif usage_type == 'ai_requests':
            if self.subscription_plan.max_ai_requests_per_month == 0:
                return 0
            return (self.current_month_ai_requests / self.subscription_plan.max_ai_requests_per_month) * 100
        
        return 0
    
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
    
    def increment_ai_requests(self):
        """Helper method to increment AI requests"""
        self.increment_usage('ai_requests')
    
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
    reports_generated = models.IntegerField(default=0)  # Added to match database
    
    # Notification tracking
    notified_80_percent = models.BooleanField(default=False, help_text='80% usage notification sent')
    notified_90_percent = models.BooleanField(default=False, help_text='90% usage notification sent')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Added to match database
    
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