"""
Company Models
"""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import models
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
    plan_type = models.CharField(_('plan type'), max_length=20, default='Pro')
    trial_days = models.IntegerField(_('trial days'), default=14)
    
    # Pricing
    price_monthly = models.DecimalField(_('monthly price'), max_digits=8, decimal_places=2)
    price_yearly = models.DecimalField(_('yearly price'), max_digits=8, decimal_places=2)
    
    # Essential limits
    max_bank_accounts = models.IntegerField(_('max bank accounts'), default=1)
    
    # Payment gateway IDs
    stripe_price_id_monthly = models.CharField(max_length=255, blank=True)
    stripe_price_id_yearly = models.CharField(max_length=255, blank=True)
    
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
    

class Company(models.Model):
    """
    Complete company model matching database schema
    """
    # Owner
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company')
    
    # Company Information
    name = models.CharField(_('company name'), max_length=200)

    cnpj = models.CharField(_('CNPJ'), max_length=18, unique=True, default='default')
    company_type = models.CharField(
        _('company type'), 
        max_length=20,
        choices=[
            ('mei', 'MEI'),
            ('me', 'Microempresa'),
            ('epp', 'Empresa de Pequeno Porte'),
            ('ltda', 'Limitada'),
            ('sa', 'Sociedade Anônima'),
            ('other', 'Outros'),
        ], 
        default='default'
    )
    business_sector = models.CharField(
        _('business sector'),
        max_length=50,
        choices=[
            ('retail', 'Comércio'),
            ('services', 'Serviços'),
            ('industry', 'Indústria'),
            ('technology', 'Tecnologia'),
            ('healthcare', 'Saúde'),
            ('education', 'Educação'),
            ('food', 'Alimentação'),
            ('construction', 'Construção'),
            ('automotive', 'Automotivo'),
            ('agriculture', 'Agricultura'),
            ('other', 'Outros'),
        ],
        default='default'
    )
    
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
    

    def can_add_bank_account(self):
        """Check if company can add more bank accounts"""
        if not self.subscription_plan:
            return False
        
        current_count = self.bank_accounts.filter(is_active=True).count()
        return current_count < self.subscription_plan.max_bank_accounts
