"""
Company and business models
Handles company profiles, subscription plans, and business information
"""
from decimal import Decimal
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class SubscriptionPlan(models.Model):
    """
    Available subscription plans (Starter, Professional, Enterprise)
    NO FREE PLAN - Only paid plans with 14-day trial
    """
    PLAN_TYPES = [
        ('starter', 'Inicial'),
        ('professional', 'Profissional'),  
        ('enterprise', 'Empresarial'),
    ]
    
    name = models.CharField(_('plan name'), max_length=50)
    slug = models.SlugField(_('slug'), unique=True)
    plan_type = models.CharField(_('plan type'), max_length=20, choices=PLAN_TYPES)
    trial_days = models.IntegerField(default=14)

    # Gateway IDs
    stripe_price_id = models.CharField(_('Stripe price ID'), max_length=255, blank=True)
    mercadopago_plan_id = models.CharField(_('MercadoPago plan ID'), max_length=255, blank=True)
    gateway_plan_id = models.CharField(
        _('payment gateway plan ID'), 
        max_length=255, 
        blank=True,
        help_text='ID do plano/preço no gateway de pagamento (Stripe/MercadoPago)'
    )
    price_monthly = models.DecimalField(_('monthly price'), max_digits=8, decimal_places=2)
    price_yearly = models.DecimalField(_('yearly price'), max_digits=8, decimal_places=2)
    
    # Limites do plano
    max_transactions = models.IntegerField(_('max transactions per month'), default=500)
    max_bank_accounts = models.IntegerField(_('max bank accounts'), default=1)
    max_users = models.IntegerField(_('max users'), default=1)
    
    # AI Features
    has_ai_categorization = models.BooleanField(_('AI categorization'), default=True)
    enable_ai_insights = models.BooleanField(_('AI insights'), default=True)
    enable_ai_reports = models.BooleanField(_('AI reports'), default=False)
    max_ai_requests_per_month = models.IntegerField(_('max AI requests per month'), default=100)
    
    # Other features
    has_advanced_reports = models.BooleanField(_('advanced reports'), default=False)
    has_api_access = models.BooleanField(_('API access'), default=False)
    has_accountant_access = models.BooleanField(_('accountant access'), default=False)
    has_priority_support = models.BooleanField(_('priority support'), default=False)
    
    display_order = models.IntegerField(_('display order'), default=0)
    
    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'subscription_plans'
        verbose_name = _('Subscription Plan')
        verbose_name_plural = _('Subscription Plans')
        ordering = ['display_order', 'price_monthly']
    
    def __str__(self):
        return f"{self.name} - R$ {self.price_monthly}/mês"

    def clean(self):
        # Ensure no free plans
        if self.price_monthly <= 0 or self.price_yearly <= 0:
            raise ValidationError('Todos os planos devem ter preço maior que zero')
        
        # Validate plan type
        if self.plan_type not in ['starter', 'professional', 'enterprise']:
            raise ValidationError('Tipo de plano inválido')
        
    def get_yearly_discount_percentage(self):
        """Calcula o percentual de desconto no plano anual"""
        if self.price_monthly == 0:
            return 0
        monthly_total = self.price_monthly * 12
        return int(((monthly_total - self.price_yearly) / monthly_total) * 100)


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
        related_name='companies',
        null=True,
        blank=True
    )
    subscription_status = models.CharField(
        _('subscription status'),
        max_length=20,
        choices=[
            ('trial', 'Período de Teste'),
            ('active', 'Ativa'),
            ('past_due', 'Em Atraso'),
            ('cancelled', 'Cancelada'),
            ('suspended', 'Suspensa'),
            ('expired', 'Expirada'),
        ],
        default='trial'
    )
    
    # Billing information
    billing_cycle = models.CharField(
        _('billing cycle'),
        max_length=20,
        choices=[
            ('monthly', 'Mensal'),
            ('yearly', 'Anual'),
        ],
        default='monthly'
    )
    trial_ends_at = models.DateTimeField(_('trial ends at'), blank=True, null=True)
    next_billing_date = models.DateField(_('next billing date'), blank=True, null=True)
    subscription_id = models.CharField(_('subscription ID'), max_length=255, blank=True, null=True)
    subscription_start_date = models.DateTimeField(_('subscription start date'), blank=True, null=True)
    subscription_end_date = models.DateTimeField(_('subscription end date'), blank=True, null=True)
    
    # Usage counters
    current_month_transactions = models.IntegerField(
        _('current month transactions'), 
        default=0
    )
    current_month_ai_requests = models.IntegerField(
        _('current month AI requests'), 
        default=0
    )
    last_usage_reset = models.DateTimeField(
        _('last usage reset'), 
        auto_now_add=True
    )
    
    # Usage notifications flags
    notified_80_percent = models.BooleanField(default=False)
    notified_90_percent = models.BooleanField(default=False)
    
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

    def can_use_ai_insight(self) -> tuple[bool, str]:
        """Check if company can make an AI request"""
        if not self.subscription_plan:
            return False, "Plano não encontrado"
        
        # Check if subscription is active
        if self.subscription_status not in ['trial', 'active']:
            return False, "Assinatura não está ativa. Configure o pagamento para continuar."
        
        # Starter não tem IA
        if self.subscription_plan.plan_type == 'starter':
            return False, "Upgrade para Professional para acessar insights de IA"
        
        # Enterprise tem IA ilimitada
        if self.subscription_plan.plan_type == 'enterprise':
            return True, "IA ilimitada disponível"
        
        # Professional tem limite mensal
        if self.subscription_plan.plan_type == 'professional':
            if self.current_month_ai_requests >= self.subscription_plan.max_ai_requests_per_month:
                return False, f"Limite de {self.subscription_plan.max_ai_requests_per_month} requisições de IA atingido este mês"
            return True, f"{self.subscription_plan.max_ai_requests_per_month - self.current_month_ai_requests} requisições restantes"
        
        return False, "Plano não reconhecido"
    
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
    
    @property
    def days_until_trial_ends(self):
        """Calculate days remaining in trial"""
        if not self.trial_ends_at or self.subscription_status != 'trial':
            return None
        
        from django.utils import timezone
        delta = self.trial_ends_at - timezone.now()
        return max(0, delta.days)
    
    @property
    def trial_has_expired(self):
        """Check if trial has expired"""
        if not self.trial_ends_at or self.subscription_status != 'trial':
            return False
        
        from django.utils import timezone
        return timezone.now() > self.trial_ends_at
    
    def check_plan_limits(self, limit_type='transactions'):
        """Check if company has reached plan limits"""
        if not self.subscription_plan:
            return False, "Sem plano ativo"
        
        if limit_type == 'transactions':
            limit_reached = self.current_month_transactions >= self.subscription_plan.max_transactions
            usage_info = f"{self.current_month_transactions}/{self.subscription_plan.max_transactions} transações"
            return limit_reached, usage_info
            
        elif limit_type == 'bank_accounts':
            count = self.bank_accounts.filter(is_active=True).count()
            limit_reached = count >= self.subscription_plan.max_bank_accounts
            usage_info = f"{count}/{self.subscription_plan.max_bank_accounts} contas"
            return limit_reached, usage_info
            
        elif limit_type == 'users':
            count = self.company_users.filter(is_active=True).count() + 1  # +1 for owner
            limit_reached = count >= self.subscription_plan.max_users
            usage_info = f"{count}/{self.subscription_plan.max_users} usuários"
            return limit_reached, usage_info
            
        elif limit_type == 'ai_requests':
            limit_reached = self.current_month_ai_requests >= self.subscription_plan.max_ai_requests_per_month
            usage_info = f"{self.current_month_ai_requests}/{self.subscription_plan.max_ai_requests_per_month} requisições IA"
            return limit_reached, usage_info
        
        return False, "Tipo de limite inválido"
    
    def get_usage_percentage(self, limit_type='transactions'):
        """Get usage percentage for a specific limit"""
        if not self.subscription_plan:
            return 0
        
        if limit_type == 'transactions':
            if self.subscription_plan.max_transactions == 0:
                return 0
            return (self.current_month_transactions / self.subscription_plan.max_transactions) * 100
            
        elif limit_type == 'bank_accounts':
            count = self.bank_accounts.filter(is_active=True).count()
            if self.subscription_plan.max_bank_accounts == 0:
                return 0
            return (count / self.subscription_plan.max_bank_accounts) * 100
            
        elif limit_type == 'users':
            count = self.company_users.filter(is_active=True).count() + 1
            if self.subscription_plan.max_users == 0:
                return 0
            return (count / self.subscription_plan.max_users) * 100
            
        elif limit_type == 'ai_requests':
            if self.subscription_plan.max_ai_requests_per_month == 0:
                return 0
            return (self.current_month_ai_requests / self.subscription_plan.max_ai_requests_per_month) * 100
        
        return 0
    
    def increment_transaction_count(self):
        """Increment transaction counter"""
        self.current_month_transactions += 1
        self.save(update_fields=['current_month_transactions'])
        
        # Check if limit reached
        limit_reached, usage_info = self.check_plan_limits('transactions')
        if limit_reached:
            # Send notification
            from apps.notifications.email_service import EmailService
            EmailService.send_limit_reached_notification(
                email=self.owner.email,
                company_name=self.name,
                limit_type='transações',
                usage_info=usage_info
            )
    
    def increment_ai_request_count(self):
        """Increment AI request counter"""
        self.current_month_ai_requests += 1
        self.save(update_fields=['current_month_ai_requests'])
        
        # Check if limit reached
        limit_reached, usage_info = self.check_plan_limits('ai_requests')
        if limit_reached:
            # Send notification
            from apps.notifications.email_service import EmailService
            EmailService.send_limit_reached_notification(
                email=self.owner.email,
                company_name=self.name,
                limit_type='requisições de IA',
                usage_info=usage_info
            )
    
    def reset_monthly_usage(self):
        """Reset monthly usage counters"""
        from django.utils import timezone
        self.current_month_transactions = 0
        self.current_month_ai_requests = 0
        self.notified_80_percent = False
        self.notified_90_percent = False
        self.last_usage_reset = timezone.now()
        self.save(update_fields=[
            'current_month_transactions', 
            'current_month_ai_requests',
            'notified_80_percent',
            'notified_90_percent',
            'last_usage_reset'
        ])
    
    def can_add_bank_account(self):
        """Check if company can add more bank accounts"""
        if not self.subscription_plan:
            return False
        
        current_count = self.bank_accounts.filter(is_active=True).count()
        return current_count < self.subscription_plan.max_bank_accounts
    
    def can_add_user(self):
        """Check if company can add more users"""
        if not self.subscription_plan:
            return False
        
        current_count = self.company_users.filter(is_active=True).count() + 1  # +1 for owner
        return current_count < self.subscription_plan.max_users
    
    def get_usage_summary(self):
        """Get complete usage summary"""
        if not self.subscription_plan:
            return None
        
        bank_accounts_count = self.bank_accounts.filter(is_active=True).count()
        users_count = self.company_users.filter(is_active=True).count() + 1
        
        return {
            'transactions': {
                'used': self.current_month_transactions,
                'limit': self.subscription_plan.max_transactions,
                'percentage': self.get_usage_percentage('transactions'),
            },
            'bank_accounts': {
                'used': bank_accounts_count,
                'limit': self.subscription_plan.max_bank_accounts,
                'percentage': self.get_usage_percentage('bank_accounts'),
            },
            'users': {
                'used': users_count,
                'limit': self.subscription_plan.max_users,
                'percentage': self.get_usage_percentage('users'),
            },
            'ai_requests': {
                'used': self.current_month_ai_requests,
                'limit': self.subscription_plan.max_ai_requests_per_month,
                'percentage': self.get_usage_percentage('ai_requests'),
            },
        }
    
    def save(self, *args, **kwargs):
        # Set trial end date for new companies - ALWAYS 14 DAYS
        if not self.pk:
            from django.utils import timezone
            self.trial_ends_at = timezone.now() + timedelta(days=14)
            self.subscription_status = 'trial'
        
        super().save(*args, **kwargs)


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


class PaymentMethod(models.Model):
    """
    Payment methods for companies (credit cards, bank accounts, etc.)
    """
    PAYMENT_TYPES = [
        ('credit_card', 'Cartão de Crédito'),
        ('debit_card', 'Cartão de Débito'),
        ('pix', 'PIX'),
        ('bank_transfer', 'Transferência Bancária'),
    ]
    
    CARD_BRANDS = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
        ('elo', 'Elo'),
        ('dinners', 'Dinners Club'),
        ('discover', 'Discover'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(_('payment type'), max_length=20, choices=PAYMENT_TYPES)
    
    # Credit/Debit card fields
    card_brand = models.CharField(_('card brand'), max_length=20, choices=CARD_BRANDS, blank=True)
    last_four = models.CharField(_('last four digits'), max_length=4, blank=True)
    exp_month = models.IntegerField(_('expiry month'), blank=True, null=True)
    exp_year = models.IntegerField(_('expiry year'), blank=True, null=True)
    cardholder_name = models.CharField(_('cardholder name'), max_length=200, blank=True)
    
    # Gateway-specific fields
    stripe_payment_method_id = models.CharField(_('Stripe payment method ID'), max_length=255, blank=True)
    mercadopago_card_id = models.CharField(_('MercadoPago card ID'), max_length=255, blank=True)
    
    # Status
    is_default = models.BooleanField(_('is default'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'payment_methods'
        verbose_name = _('Payment Method')
        verbose_name_plural = _('Payment Methods')
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        if self.payment_type in ['credit_card', 'debit_card']:
            return f"{self.card_brand} **** {self.last_four}"
        return self.get_payment_type_display()
    
    def save(self, *args, **kwargs):
        # Ensure only one default payment method per company
        if self.is_default:
            PaymentMethod.objects.filter(
                company=self.company, 
                is_default=True
            ).update(is_default=False)
        super().save(*args, **kwargs)


class PaymentHistory(models.Model):
    """
    Payment history and invoices for companies
    """
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('failed', 'Falhou'),
        ('canceled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
        ('partially_refunded', 'Parcialmente Reembolsado'),
    ]
    
    TRANSACTION_TYPES = [
        ('subscription', 'Assinatura'),
        ('upgrade', 'Upgrade de Plano'),
        ('refund', 'Reembolso'),
        ('adjustment', 'Ajuste'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payment_history')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Transaction details
    transaction_type = models.CharField(_('transaction type'), max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('currency'), max_length=3, default='BRL')
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES)
    description = models.TextField(_('description'))
    
    # Gateway transaction IDs
    stripe_payment_intent_id = models.CharField(_('Stripe payment intent ID'), max_length=255, blank=True)
    stripe_invoice_id = models.CharField(_('Stripe invoice ID'), max_length=255, blank=True)
    mercadopago_payment_id = models.CharField(_('MercadoPago payment ID'), max_length=255, blank=True)
    
    # Invoice details
    invoice_number = models.CharField(_('invoice number'), max_length=50, unique=True, blank=True)
    invoice_url = models.URLField(_('invoice URL'), blank=True)
    invoice_pdf_path = models.CharField(_('invoice PDF path'), max_length=500, blank=True)
    
    # Dates
    transaction_date = models.DateTimeField(_('transaction date'))
    due_date = models.DateField(_('due date'), blank=True, null=True)
    paid_at = models.DateTimeField(_('paid at'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'payment_history'
        verbose_name = _('Payment History')
        verbose_name_plural = _('Payment History')
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.company.name} - {self.description} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Generate invoice number if not provided
        if not self.invoice_number and self.status in ['paid', 'pending']:
            from datetime import datetime
            prefix = self.company.name[:3].upper()
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.invoice_number = f"{prefix}-{timestamp}"
        super().save(*args, **kwargs)


class ResourceUsage(models.Model):
    """
    Track resource usage for companies
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='resource_usage'
    )
    
    # Usage tracking
    month = models.DateField(_('month'), help_text='First day of the month')
    transactions_count = models.IntegerField(_('transactions count'), default=0)
    ai_requests_count = models.IntegerField(_('AI requests count'), default=0)
    reports_generated = models.IntegerField(_('reports generated'), default=0)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'resource_usage'
        verbose_name = _('Resource Usage')
        verbose_name_plural = _('Resource Usage')
        unique_together = ['company', 'month']
        ordering = ['-month']
    
    def __str__(self):
        return f"{self.company.name} - {self.month.strftime('%B %Y')}"
    
    @property
    def total_ai_usage(self):
        """Total AI usage including categorizations and reports"""
        return self.ai_requests_count + self.reports_generated
    
    @classmethod
    def get_or_create_current_month(cls, company):
        """Get or create usage record for current month"""
        from django.utils import timezone
        now = timezone.now()
        month_start = now.replace(day=1).date()
        
        usage, created = cls.objects.get_or_create(
            company=company,
            month=month_start,
            defaults={
                'transactions_count': 0,
                'ai_requests_count': 0,
                'reports_generated': 0
            }
        )
        return usage