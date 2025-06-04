"""
Company and business models
Handles company profiles, subscription plans, and business information
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class SubscriptionPlan(models.Model):
    """
    Available subscription plans (Starter, Pro, Enterprise)
    """
    PLAN_TYPES = [
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    name = models.CharField(_('plan name'), max_length=50)
    slug = models.SlugField(_('slug'), unique=True)
    plan_type = models.CharField(_('plan type'), max_length=20, choices=PLAN_TYPES)
    gateway_plan_id = models.CharField(_('payment gateway plan ID'), max_length=255, blank=True)
    price_monthly = models.DecimalField(_('monthly price'), max_digits=8, decimal_places=2)
    price_yearly = models.DecimalField(_('yearly price'), max_digits=8, decimal_places=2)
    max_transactions = models.IntegerField(_('max transactions per month'), default=500)
    max_bank_accounts = models.IntegerField(_('max bank accounts'), default=1)
    max_users = models.IntegerField(_('max users'), default=1)
    has_ai_categorization = models.BooleanField(_('AI categorization'), default=True)
    has_advanced_reports = models.BooleanField(_('advanced reports'), default=False)
    has_api_access = models.BooleanField(_('API access'), default=False)
    has_accountant_access = models.BooleanField(_('accountant access'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'subscription_plans'
        verbose_name = _('Subscription Plan')
        verbose_name_plural = _('Subscription Plans')
        ordering = ['price_monthly']
    
    def __str__(self):
        return f"{self.name} - R$ {self.price_monthly}/mês"


class Company(models.Model):
    """
    Company profile with business information
    """
    COMPANY_TYPES = [
        ('mei', 'Microempreendedor Individual'),
        ('me', 'Microempresa'),
        ('epp', 'Empresa de Pequeno Porte'),
        ('ltda', 'Sociedade Limitada'),
        ('sa', 'Sociedade Anônima'),
        ('other', 'Outro'),
    ]
    
    BUSINESS_SECTORS = [
        ('retail', 'Comércio'),
        ('services', 'Serviços'),
        ('industry', 'Indústria'),
        ('construction', 'Construção'),
        ('agriculture', 'Agricultura'),
        ('technology', 'Tecnologia'),
        ('healthcare', 'Saúde'),
        ('education', 'Educação'),
        ('food', 'Alimentação'),
        ('beauty', 'Beleza'),
        ('automotive', 'Automotivo'),
        ('real_estate', 'Imobiliário'),
        ('consulting', 'Consultoria'),
        ('other', 'Outro'),
    ]
    
    # Owner and basic info
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company')
    name = models.CharField(_('company name'), max_length=200)
    trade_name = models.CharField(_('trade name'), max_length=200, blank=True)
    
    # Legal information
    cnpj = models.CharField(_('CNPJ'), max_length=18, unique=True, blank=True, null=True)
    company_type = models.CharField(_('company type'), max_length=20, choices=COMPANY_TYPES)
    business_sector = models.CharField(_('business sector'), max_length=50, choices=BUSINESS_SECTORS)
    
    # Contact information
    email = models.EmailField(_('company email'), blank=True)
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    website = models.URLField(_('website'), blank=True)
    
    # Address
    address_street = models.CharField(_('street'), max_length=200, blank=True)
    address_number = models.CharField(_('number'), max_length=20, blank=True)
    address_complement = models.CharField(_('complement'), max_length=100, blank=True)
    address_neighborhood = models.CharField(_('neighborhood'), max_length=100, blank=True)
    address_city = models.CharField(_('city'), max_length=100, blank=True)
    address_state = models.CharField(_('state'), max_length=2, blank=True)
    address_zipcode = models.CharField(_('ZIP code'), max_length=10, blank=True)
    
    # Business metrics
    monthly_revenue = models.DecimalField(
        _('monthly revenue'), 
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    employee_count = models.IntegerField(_('employee count'), default=1)
    
    # Subscription
    subscription_plan = models.ForeignKey(
        SubscriptionPlan, 
        on_delete=models.PROTECT, 
        related_name='companies'
    )
    subscription_status = models.CharField(
        _('subscription status'),
        max_length=20,
        choices=[
            ('trial', 'Trial'),
            ('active', 'Active'),
            ('past_due', 'Past Due'),
            ('cancelled', 'Cancelled'),
            ('suspended', 'Suspended'),
        ],
        default='trial'
    )
    trial_ends_at = models.DateTimeField(_('trial ends at'), blank=True, null=True)
    next_billing_date = models.DateField(_('next billing date'), blank=True, null=True)
    subscription_id = models.CharField(_('subscription ID'), max_length=255, blank=True, null=True)
    subscription_start_date = models.DateTimeField(_('subscription start date'), blank=True, null=True)
    subscription_end_date = models.DateTimeField(_('subscription end date'), blank=True, null=True)
    
    # Company settings
    logo = models.ImageField(_('logo'), upload_to='company_logos/', blank=True, null=True)
    primary_color = models.CharField(_('primary color'), max_length=7, default='#3B82F6')
    currency = models.CharField(_('currency'), max_length=3, default='BRL')
    fiscal_year_start = models.CharField(
        _('fiscal year start'),
        max_length=2,
        choices=[(str(i).zfill(2), f"{i:02d}") for i in range(1, 13)],
        default='01'
    )
    
    # AI and automation preferences
    enable_ai_categorization = models.BooleanField(_('enable AI categorization'), default=True)
    auto_categorize_threshold = models.FloatField(_('auto categorize threshold'), default=0.8)
    enable_notifications = models.BooleanField(_('enable notifications'), default=True)
    enable_email_reports = models.BooleanField(_('enable email reports'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_active = models.BooleanField(_('is active'), default=True)
    
    class Meta:
        db_table = 'companies'
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')
    
    def __str__(self):
        return self.name
    
    @property
    def is_trial(self):
        return self.subscription_status == 'trial'
    
    @property
    def is_subscribed(self):
        return self.subscription_status == 'active'
    
    @property
    def display_name(self):
        return self.trade_name or self.name


class CompanyUser(models.Model):
    """
    Additional users for a company (for Enterprise plans)
    """
    ROLE_CHOICES = [
        ('owner', 'Proprietário'),
        ('admin', 'Administrador'),
        ('manager', 'Gerente'),
        ('accountant', 'Contador'),
        ('viewer', 'Visualizador'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_memberships')
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES)
    permissions = models.JSONField(_('permissions'), default=dict)
    is_active = models.BooleanField(_('is active'), default=True)
    invited_at = models.DateTimeField(_('invited at'), auto_now_add=True)
    joined_at = models.DateTimeField(_('joined at'), blank=True, null=True)
    
    class Meta:
        db_table = 'company_users'
        verbose_name = _('Company User')
        verbose_name_plural = _('Company Users')
        unique_together = ('company', 'user')
    
    def __str__(self):
        return f"{self.user.full_name} - {self.company.name} ({self.role})"