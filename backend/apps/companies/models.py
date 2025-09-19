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
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

User = get_user_model()


class SubscriptionPlan(models.Model):
    """
    Simple subscription plan model with essential fields only
    """
    # Billing period choices
    BILLING_PERIODS = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
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
        return f"{self.name} - R$ {self.price_monthly}/mês"
    
    def get_price(self, billing_period='monthly'):
        """Get price based on billing period"""
        if billing_period == 'yearly':
            return self.price_yearly
        return self.price_monthly
    
    def get_stripe_price_id(self, billing_period='monthly'):
        """Get Stripe price ID based on billing period"""
        if billing_period == 'yearly':
            return self.stripe_price_id_yearly
        return self.stripe_price_id_monthly
    
    def has_stripe_ids(self):
        """Check if Stripe price IDs are configured"""
        return bool(self.stripe_price_id_monthly and self.stripe_price_id_yearly)
    
    @property
    def display_name(self):
        """Get display name for UI"""
        return self.name
    
    @property
    def monthly_discount_percentage(self):
        """Calculate discount percentage for yearly billing"""
        if self.price_monthly == 0:
            return 0
        yearly_monthly = self.price_yearly / 12
        discount = ((self.price_monthly - yearly_monthly) / self.price_monthly) * 100
        return round(discount, 0)


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
            ('early_access', 'Early Access'),
        ],
        default='trial'
    )
    
    # Early Access
    is_early_access = models.BooleanField(_('is early access'), default=False)
    early_access_expires_at = models.DateTimeField(_('early access expires at'), null=True, blank=True)
    used_invite_code = models.CharField(_('used invite code'), max_length=20, blank=True)
    
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
        if self.subscription_status == 'early_access':
            return self.is_early_access_active
        if self.subscription_status != 'trial':
            return False
        return self.trial_ends_at and timezone.now() < self.trial_ends_at
    
    @property
    def is_early_access_active(self):
        """Check if early access is still active"""
        if not self.is_early_access:
            return False
        return self.early_access_expires_at and timezone.now() < self.early_access_expires_at
    
    @property
    def days_until_trial_ends(self):
        """Calculate days remaining in trial or early access"""
        if self.subscription_status == 'early_access' and self.is_early_access_active:
            delta = self.early_access_expires_at - timezone.now()
            return max(0, delta.days)
        elif not self.is_trial_active:
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
    

    def reset_transaction_usage(self, count):
        """
        Reset transaction usage counter by reducing the count
        
        Args:
            count: Number of transactions to subtract from current usage
        """
        from django.db import transaction as db_transaction
        from django.db.models import F
        
        with db_transaction.atomic():
            # Usar select_for_update para evitar race conditions
            company = Company.objects.select_for_update().get(pk=self.pk)
            
            # Reduzir o contador
            new_count = max(0, company.current_month_transactions - count)
            company.current_month_transactions = new_count
            company.save(update_fields=['current_month_transactions'])
            
            logger.info(
                f"Reset transaction usage for company {self.id}: "
                f"reduced by {count}, new total: {new_count}"
            )
            
            return new_count


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
    
    def get_usage_summary(self):
        """Get comprehensive usage summary for the company"""
        if not self.subscription_plan:
            return {
                'transactions': {'used': 0, 'limit': 0, 'percentage': 0},
                'ai_requests': {'used': 0, 'limit': 0, 'percentage': 0},
                'bank_accounts': {'used': 0, 'limit': 0, 'percentage': 0}
            }
        
        bank_accounts_count = self.bank_accounts.filter(is_active=True).count()
        
        return {
            'transactions': {
                'used': self.current_month_transactions,
                'limit': self.subscription_plan.max_transactions,
                'percentage': self.get_usage_percentage('transactions')
            },
            'ai_requests': {
                'used': self.current_month_ai_requests,
                'limit': self.subscription_plan.max_ai_requests_per_month,
                'percentage': self.get_usage_percentage('ai_requests')
            },
            'bank_accounts': {
                'used': bank_accounts_count,
                'limit': self.subscription_plan.max_bank_accounts,
                'percentage': (bank_accounts_count / self.subscription_plan.max_bank_accounts * 100) 
                             if self.subscription_plan.max_bank_accounts > 0 else 0
            }
        }
    
    @transaction.atomic
    def increment_usage_safe(self, usage_type):
        """
        Safely increment usage counters with atomic verification.
        Prevents race conditions and enforces plan limits.
        Returns tuple (success: bool, message: str)
        """
        from django.db import transaction
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Lock the company row for update to prevent race conditions
        company = Company.objects.select_for_update().get(pk=self.pk)
        
        if not company.subscription_plan:
            return False, "No active subscription plan"
        
        # Check limits based on usage type
        if usage_type == 'transactions':
            current = company.current_month_transactions
            limit = company.subscription_plan.max_transactions
            field_name = 'current_month_transactions'
            resource_field = 'transactions_count'
        elif usage_type == 'ai_requests':
            current = company.current_month_ai_requests
            limit = company.subscription_plan.max_ai_requests_per_month
            field_name = 'current_month_ai_requests'
            resource_field = 'ai_requests_count'
        else:
            return False, f"Unknown usage type: {usage_type}"
        
        # Check if limit would be exceeded
        if current >= limit:
            logger.warning(
                f"Usage limit reached for company {company.id}: "
                f"{usage_type} = {current}/{limit}"
            )
            return False, f"Limit reached: {current}/{limit}"
        
        # Safe to increment - do it atomically
        Company.objects.filter(pk=company.pk).update(
            **{field_name: F(field_name) + 1}
        )
        
        # Update ResourceUsage
        self._update_resource_usage(resource_field, 1)
        
        # Refresh instance
        self.refresh_from_db(fields=[field_name])
        
        # Log successful increment
        new_value = getattr(self, field_name)
        logger.info(
            f"Usage incremented for company {company.id}: "
            f"{usage_type} = {new_value}/{limit}"
        )
        
        # Check if we should send usage warnings
        percentage = (new_value / limit) * 100 if limit > 0 else 0
        if percentage >= 90 and not company.notified_90_percent:
            self._send_usage_warning(90, usage_type, new_value, limit)
            company.notified_90_percent = True
            company.save(update_fields=['notified_90_percent'])
        elif percentage >= 80 and not company.notified_80_percent:
            self._send_usage_warning(80, usage_type, new_value, limit)
            company.notified_80_percent = True
            company.save(update_fields=['notified_80_percent'])
        
        return True, f"Usage incremented: {new_value}/{limit}"
    

    @transaction.atomic
    def increment_usage(self, usage_type):
        """
        Increment usage counters atomically to prevent race conditions.
        Uses F expressions for atomic database operations.
        DEPRECATED: Use increment_usage_safe() for limit checking
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


class EarlyAccessInvite(models.Model):
    """
    Early Access Invites for MVP testing
    """
    # Core identification
    invite_code = models.CharField(_('invite code'), max_length=20, unique=True)
    
    # Global expiration date for all invites
    expires_at = models.DateTimeField(_('expires at'), help_text='Date when early access ends')
    
    # Usage tracking
    is_used = models.BooleanField(_('is used'), default=False)
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_invite')
    used_at = models.DateTimeField(_('used at'), null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_invites')
    notes = models.TextField(_('notes'), blank=True, help_text='Internal notes about this invite')
    
    class Meta:
        db_table = 'early_access_invites'
        ordering = ['-created_at']
        verbose_name = _('Early Access Invite')
        verbose_name_plural = _('Early Access Invites')
    
    def __str__(self):
        status = "Used" if self.is_used else "Available"
        return f"Invite {self.invite_code} - {status}"
    
    def mark_as_used(self, user):
        """Mark invite as used by a specific user"""
        self.is_used = True
        self.used_by = user
        self.used_at = timezone.now()
        self.save(update_fields=['is_used', 'used_by', 'used_at'])
    
    @property
    def is_valid(self):
        """Check if invite is still valid (not used and not expired)"""
        return not self.is_used and timezone.now() < self.expires_at
    
    @property
    def days_until_expiry(self):
        """Get days remaining until expiry"""
        if timezone.now() >= self.expires_at:
            return 0
        delta = self.expires_at - timezone.now()
        return delta.days


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