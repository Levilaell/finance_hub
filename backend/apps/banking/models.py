"""
Banking and financial transaction models
Core financial data handling with AI categorization support
"""
import uuid
import re
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.encryption import EncryptedTextField

User = get_user_model()


class BankProvider(models.Model):
    """
    Supported bank providers for Open Banking integration
    """
    name = models.CharField(_('bank name'), max_length=100)
    code = models.CharField(_('bank code'), max_length=10, unique=True)
    logo = models.ImageField(_('logo'), upload_to='bank_logos/', blank=True, null=True)
    color = models.CharField(_('brand color'), max_length=7, default='#000000')
    is_open_banking = models.BooleanField(_('supports Open Banking'), default=True)
    api_endpoint = models.URLField(_('API endpoint'), blank=True)
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Integration settings
    requires_agency = models.BooleanField(_('requires agency'), default=True)
    requires_account = models.BooleanField(_('requires account'), default=True)
    supports_pix = models.BooleanField(_('supports PIX'), default=True)
    supports_ted = models.BooleanField(_('supports TED'), default=True)
    supports_doc = models.BooleanField(_('supports DOC'), default=True)
    
    class Meta:
        db_table = 'bank_providers'
        verbose_name = _('Bank Provider')
        verbose_name_plural = _('Bank Providers')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class BankAccount(models.Model):
    """
    Company bank accounts connected via Open Banking
    """
    ACCOUNT_TYPES = [
        ('checking', 'Conta Corrente'),
        ('savings', 'Conta Poupança'),
        ('business', 'Conta Empresarial'),
        ('digital', 'Conta Digital'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Ativa'),
        ('inactive', 'Inativa'),
        ('pending', 'Pendente'),
        ('error', 'Erro de Conexão'),
        ('expired', 'Token Expirado'),
    ]
    
    # Basic information
    company = models.ForeignKey(
        'companies.Company', 
        on_delete=models.CASCADE, 
        related_name='bank_accounts'
    )
    bank_provider = models.ForeignKey(BankProvider, on_delete=models.PROTECT)
    
    # Account details
    account_type = models.CharField(_('account type'), max_length=20, choices=ACCOUNT_TYPES)
    agency = models.CharField(_('agency'), max_length=10)
    account_number = models.CharField(_('account number'), max_length=20)
    account_digit = models.CharField(_('account digit'), max_length=2, blank=True)
    
    # Open Banking integration
    external_account_id = models.CharField(_('external account ID'), max_length=100, blank=True)
    pluggy_item_id = models.CharField(_('Pluggy item ID'), max_length=255, blank=True, null=True)
    
    # Encrypted token storage
    _access_token_encrypted = models.TextField(_('encrypted access token'), blank=True)
    _refresh_token_encrypted = models.TextField(_('encrypted refresh token'), blank=True)
    token_expires_at = models.DateTimeField(_('token expires at'), blank=True, null=True)
    
    # Encrypted token descriptors
    access_token = EncryptedTextField('access_token')
    refresh_token = EncryptedTextField('refresh_token')
    
    # Account status and balance
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    current_balance = models.DecimalField(
        _('current balance'), 
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    available_balance = models.DecimalField(
        _('available balance'), 
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    last_sync_at = models.DateTimeField(_('last sync at'), blank=True, null=True)
    sync_frequency = models.IntegerField(_('sync frequency (hours)'), default=4)
    
    # Account settings
    nickname = models.CharField(_('nickname'), max_length=100, blank=True)
    is_primary = models.BooleanField(_('is primary account'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'bank_accounts'
        verbose_name = _('Bank Account')
        verbose_name_plural = _('Bank Accounts')
        unique_together = ('company', 'bank_provider', 'agency', 'account_number', 'account_type')
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['bank_provider', 'external_account_id']),
            models.Index(fields=['last_sync_at']),
        ]
    
    def __str__(self):
        return f"{self.bank_provider.name} - {self.agency}/{self.account_number}"
    
    @property
    def masked_account(self):
        """Return masked account number for security"""
        if len(self.account_number) > 4:
            return f"****{self.account_number[-4:]}"
        return self.account_number
    
    def save(self, *args, **kwargs):
        """Custom save method for validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def clean(self):
        """Custom validation for Brazilian bank accounts"""
        super().clean()
        
        # Validate agency format (Brazilian format: 0000-0 or 0000)
        if self.agency:
            if not self._validate_brazilian_agency(self.agency):
                raise ValidationError({
                    'agency': 'Agência deve estar no formato brasileiro (ex: 0001, 1234-5)'
                })
        
        # Validate account number format (Brazilian format: numbers + optional letter)
        if self.account_number:
            if not self._validate_brazilian_account(self.account_number):
                raise ValidationError({
                    'account_number': 'Número da conta deve estar no formato brasileiro (ex: 12345-6, 123456-X)'
                })
    
    def _validate_brazilian_agency(self, agency: str) -> bool:
        """Validate Brazilian agency format"""
        # Remove common separators
        clean_agency = agency.replace('-', '').replace('.', '').strip()
        
        # Brazilian agencies: 3-5 digits, sometimes with check digit
        pattern = r'^\d{3,5}$'
        return bool(re.match(pattern, clean_agency)) and len(clean_agency) <= 5
    
    def _validate_brazilian_account(self, account: str) -> bool:
        """Validate Brazilian account number format"""
        # Remove common separators
        clean_account = account.replace('-', '').replace('.', '').strip()
        
        # Brazilian accounts: digits + optional check digit (letter or number)
        # Examples: 123456, 1234567, 123456X, 123456-7
        pattern = r'^\d{4,12}[A-Z0-9]?$'
        return bool(re.match(pattern, clean_account.upper()))
    
    @property
    def display_name(self):
        """Return display name for the account"""
        if self.nickname:
            return f"{self.nickname} ({self.bank_provider.name})"
        return f"{self.bank_provider.name} - {self.masked_account}"


class TransactionCategory(models.Model):
    """
    Categories for transaction classification
    """
    CATEGORY_TYPES = [
        ('income', 'Receita'),
        ('expense', 'Despesa'),
        ('transfer', 'Transferência'),
    ]
    
    name = models.CharField(_('category name'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True)
    category_type = models.CharField(_('category type'), max_length=20, choices=CATEGORY_TYPES)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='subcategories')
    
    # Visual settings
    icon = models.CharField(_('icon'), max_length=50, default='💰')
    color = models.CharField(_('color'), max_length=7, default='#3B82F6')
    
    # AI training data
    keywords = models.JSONField(_('keywords for AI'), default=list, help_text="Keywords for AI categorization")
    confidence_threshold = models.FloatField(_('confidence threshold'), default=0.7)
    
    # Settings
    is_system = models.BooleanField(_('is system category'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    order = models.IntegerField(_('order'), default=0)
    
    class Meta:
        db_table = 'transaction_categories'
        verbose_name = _('Transaction Category')
        verbose_name_plural = _('Transaction Categories')
        ordering = ['category_type', 'order', 'name']
        indexes = [
            models.Index(fields=['category_type', 'is_active']),
            models.Index(fields=['is_system', 'category_type']),
            models.Index(fields=['parent', 'order']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    @property
    def full_name(self):
        """Return full category path"""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Transaction(models.Model):
    """
    Financial transactions from bank accounts
    """
    TRANSACTION_TYPES = [
        ('debit', 'Débito'),
        ('credit', 'Crédito'),
        ('transfer_in', 'Transferência Recebida'),
        ('transfer_out', 'Transferência Enviada'),
        ('pix_in', 'PIX Recebido'),
        ('pix_out', 'PIX Enviado'),
        ('fee', 'Taxa'),
        ('interest', 'Juros'),
        ('adjustment', 'Ajuste'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('completed', 'Concluída'),
        ('failed', 'Falhou'),
        ('cancelled', 'Cancelada'),
    ]
    
    # Basic transaction info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    external_id = models.CharField(_('external transaction ID'), max_length=100, blank=True)
    
    # Transaction details
    transaction_type = models.CharField(_('transaction type'), max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(_('amount'), max_digits=15, decimal_places=2)
    description = models.CharField(_('description'), max_length=500)
    transaction_date = models.DateTimeField(_('transaction date'))
    posted_date = models.DateTimeField(_('posted date'), blank=True, null=True)
    
    # Counterpart information
    counterpart_name = models.CharField(_('counterpart name'), max_length=200, blank=True)
    counterpart_document = models.CharField(_('counterpart document'), max_length=20, blank=True)
    counterpart_bank = models.CharField(_('counterpart bank'), max_length=100, blank=True)
    counterpart_agency = models.CharField(_('counterpart agency'), max_length=10, blank=True)
    counterpart_account = models.CharField(_('counterpart account'), max_length=20, blank=True)
    
    # Categorization
    category = models.ForeignKey(
        TransactionCategory, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='transactions'
    )
    subcategory = models.ForeignKey(
        TransactionCategory, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='subcategory_transactions'
    )
    
    # AI categorization data
    ai_category_confidence = models.FloatField(
        _('AI confidence'), 
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    ai_suggested_category = models.ForeignKey(
        TransactionCategory,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='ai_suggested_transactions'
    )
    is_ai_categorized = models.BooleanField(_('categorized by AI'), default=False)
    is_manually_reviewed = models.BooleanField(_('manually reviewed'), default=False)
    
    # Additional metadata
    reference_number = models.CharField(_('reference number'), max_length=100, blank=True)
    pix_key = models.CharField(_('PIX key'), max_length=100, blank=True)
    notes = models.TextField(_('notes'), blank=True)
    tags = models.JSONField(_('tags'), default=list)
    
    # Status and processing
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='completed')
    balance_after = models.DecimalField(
        _('balance after transaction'), 
        max_digits=15, 
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Reconciliation
    is_reconciled = models.BooleanField(_('is reconciled'), default=False)
    reconciled_at = models.DateTimeField(_('reconciled at'), blank=True, null=True)
    reconciled_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='reconciled_transactions'
    )
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'transactions'
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            # Primary filtering indexes
            models.Index(fields=['bank_account', 'transaction_date', 'category']),
            models.Index(fields=['bank_account', 'transaction_type', 'transaction_date']),
            models.Index(fields=['bank_account', 'status', 'transaction_date']),
            
            # Dashboard and reporting indexes
            models.Index(fields=['transaction_date', 'category', 'amount']),
            models.Index(fields=['counterpart_name', 'transaction_date']),
            models.Index(fields=['external_id', 'bank_account']),
            
            # AI categorization indexes
            models.Index(fields=['is_ai_categorized', 'category']),
            models.Index(fields=['ai_category_confidence', 'is_manually_reviewed']),
            
            # Reconciliation indexes
            models.Index(fields=['is_reconciled', 'reconciled_at']),
            
            # Performance indexes for aggregations
            # Note: Company-level filtering will use joins, not direct indexing
            models.Index(fields=['external_id']),
        ]
    
    def __str__(self):
        return f"{self.description} - R$ {self.amount} ({self.transaction_date.strftime('%d/%m/%Y')})"
    
    @property
    def is_income(self):
        """Check if transaction is income"""
        return self.transaction_type in ['credit', 'transfer_in', 'pix_in'] and self.amount > 0
    
    @property
    def is_expense(self):
        """Check if transaction is expense"""
        return self.transaction_type in ['debit', 'transfer_out', 'pix_out', 'fee'] or self.amount < 0
    
    @property
    def formatted_amount(self):
        """Return formatted amount with currency"""
        return f"R$ {abs(self.amount):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def amount_with_sign(self):
        """Return amount with proper sign for display"""
        if self.is_income:
            return abs(self.amount)
        else:
            return -abs(self.amount)


class RecurringTransaction(models.Model):
    """
    Recurring transaction patterns for prediction and alerts
    """
    FREQUENCY_CHOICES = [
        ('daily', 'Diário'),
        ('weekly', 'Semanal'),
        ('biweekly', 'Quinzenal'),
        ('monthly', 'Mensal'),
        ('bimonthly', 'Bimestral'),
        ('quarterly', 'Trimestral'),
        ('semiannual', 'Semestral'),
        ('annual', 'Anual'),
    ]
    
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='recurring_transactions')
    name = models.CharField(_('name'), max_length=200)
    description_pattern = models.CharField(_('description pattern'), max_length=500)
    
    # Amount settings
    expected_amount = models.DecimalField(_('expected amount'), max_digits=15, decimal_places=2)
    amount_tolerance = models.DecimalField(
        _('amount tolerance'), 
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('5.00'),
        help_text="Tolerance percentage for amount matching"
    )
    
    # Timing settings
    frequency = models.CharField(_('frequency'), max_length=20, choices=FREQUENCY_CHOICES)
    next_expected_date = models.DateField(_('next expected date'))
    day_tolerance = models.IntegerField(_('day tolerance'), default=3)
    
    # Categorization
    category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, blank=True, null=True)
    
    # Settings
    is_active = models.BooleanField(_('is active'), default=True)
    auto_categorize = models.BooleanField(_('auto categorize'), default=True)
    send_alerts = models.BooleanField(_('send alerts'), default=True)
    
    # Statistics
    total_occurrences = models.IntegerField(_('total occurrences'), default=0)
    last_occurrence_date = models.DateField(_('last occurrence date'), blank=True, null=True)
    accuracy_rate = models.FloatField(_('accuracy rate'), default=0.0)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'recurring_transactions'
        verbose_name = _('Recurring Transaction')
        verbose_name_plural = _('Recurring Transactions')
    
    def __str__(self):
        return f"{self.name} - {self.frequency}"


class Budget(models.Model):
    """
    Budget management for expense tracking and control
    """
    BUDGET_TYPES = [
        ('monthly', 'Mensal'),
        ('weekly', 'Semanal'),
        ('yearly', 'Anual'),
        ('custom', 'Personalizado'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('exceeded', 'Excedido'),
        ('paused', 'Pausado'),
    ]
    
    # Basic information
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField(_('budget name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    # Budget settings
    budget_type = models.CharField(_('budget type'), max_length=20, choices=BUDGET_TYPES, default='monthly')
    amount = models.DecimalField(_('budget amount'), max_digits=15, decimal_places=2)
    spent_amount = models.DecimalField(_('spent amount'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Categories
    categories = models.ManyToManyField(
        TransactionCategory,
        related_name='budgets',
        blank=True,
        help_text="Categories included in this budget"
    )
    
    # Time period
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'))
    
    # Alert settings
    alert_threshold = models.IntegerField(
        _('alert threshold (%)'),
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Send alert when this percentage of budget is reached"
    )
    is_alert_enabled = models.BooleanField(_('enable alerts'), default=True)
    last_alert_sent = models.DateTimeField(_('last alert sent'), blank=True, null=True)
    
    # Status
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='active')
    is_rollover = models.BooleanField(_('rollover unused budget'), default=False)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_budgets')
    
    class Meta:
        db_table = 'budgets'
        verbose_name = _('Budget')
        verbose_name_plural = _('Budgets')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - R$ {self.amount}"
    
    @property
    def remaining_amount(self):
        """Calculate remaining budget amount"""
        return self.amount - self.spent_amount
    
    @property
    def spent_percentage(self):
        """Calculate percentage of budget spent"""
        if self.amount == 0:
            return 0
        return (self.spent_amount / self.amount) * 100
    
    @property
    def is_exceeded(self):
        """Check if budget is exceeded"""
        return self.spent_amount > self.amount
    
    @property
    def is_alert_threshold_reached(self):
        """Check if alert threshold is reached"""
        return self.spent_percentage >= self.alert_threshold
    
    def update_spent_amount(self):
        """Update spent amount based on transactions"""
        from django.db.models import Sum
        from django.utils import timezone
        
        # Get transactions in budget period
        transactions = Transaction.objects.filter(
            bank_account__company=self.company,
            transaction_date__gte=self.start_date,
            transaction_date__lte=self.end_date,
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        )
        
        # Filter by categories if specified
        if self.categories.exists():
            transactions = transactions.filter(category__in=self.categories.all())
        
        # Calculate total spent
        total_spent = transactions.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        self.spent_amount = abs(total_spent)
        self.save(update_fields=['spent_amount', 'updated_at'])
        
        # Update status based on spending
        if self.is_exceeded and self.status != 'exceeded':
            self.status = 'exceeded'
            self.save(update_fields=['status'])


class FinancialGoal(models.Model):
    """
    Financial goals tracking and management
    """
    GOAL_TYPES = [
        ('savings', 'Poupança'),
        ('debt_reduction', 'Redução de Dívida'),
        ('expense_reduction', 'Redução de Gastos'),
        ('income_increase', 'Aumento de Renda'),
        ('emergency_fund', 'Reserva de Emergência'),
        ('investment', 'Investimento'),
        ('custom', 'Personalizado'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('completed', 'Concluído'),
        ('paused', 'Pausado'),
        ('cancelled', 'Cancelado'),
    ]
    
    # Basic information
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='financial_goals')
    name = models.CharField(_('goal name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    goal_type = models.CharField(_('goal type'), max_length=20, choices=GOAL_TYPES)
    
    # Goal settings
    target_amount = models.DecimalField(_('target amount'), max_digits=15, decimal_places=2)
    current_amount = models.DecimalField(_('current amount'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    target_date = models.DateField(_('target date'))
    
    # Categories and accounts
    categories = models.ManyToManyField(
        TransactionCategory,
        related_name='financial_goals',
        blank=True,
        help_text="Categories related to this goal"
    )
    bank_accounts = models.ManyToManyField(
        BankAccount,
        related_name='financial_goals',
        blank=True,
        help_text="Accounts to track for this goal"
    )
    
    # Progress tracking
    monthly_target = models.DecimalField(
        _('monthly target'),
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Monthly amount needed to reach goal"
    )
    
    # Settings
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='active')
    is_automatic_tracking = models.BooleanField(_('automatic tracking'), default=True)
    send_reminders = models.BooleanField(_('send reminders'), default=True)
    reminder_frequency = models.IntegerField(_('reminder frequency (days)'), default=7)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_goals')
    completed_at = models.DateTimeField(_('completed at'), blank=True, null=True)
    
    class Meta:
        db_table = 'financial_goals'
        verbose_name = _('Financial Goal')
        verbose_name_plural = _('Financial Goals')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - R$ {self.target_amount}"
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.target_amount == 0:
            return 0
        return (self.current_amount / self.target_amount) * 100
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to reach goal"""
        return self.target_amount - self.current_amount
    
    @property
    def days_remaining(self):
        """Calculate days remaining to target date"""
        from django.utils import timezone
        if self.target_date:
            delta = self.target_date - timezone.now().date()
            return delta.days
        return None
    
    @property
    def required_monthly_amount(self):
        """Calculate required monthly amount to reach goal"""
        if not self.days_remaining or self.days_remaining <= 0:
            return self.remaining_amount
        
        months_remaining = max(1, self.days_remaining / 30)
        return self.remaining_amount / Decimal(str(months_remaining))
    
    def update_progress(self):
        """Update goal progress based on transactions"""
        from django.db.models import Sum
        from django.utils import timezone
        
        if not self.is_automatic_tracking:
            return
        
        # Calculate progress based on goal type
        if self.goal_type == 'savings':
            # Sum positive transactions in specified accounts
            transactions = Transaction.objects.filter(
                bank_account__in=self.bank_accounts.all(),
                transaction_type__in=['credit', 'transfer_in', 'pix_in'],
                transaction_date__gte=self.created_at.date()
            )
        elif self.goal_type == 'debt_reduction':
            # Sum debt payments
            transactions = Transaction.objects.filter(
                bank_account__company=self.company,
                category__in=self.categories.all(),
                transaction_type__in=['debit', 'transfer_out', 'pix_out'],
                transaction_date__gte=self.created_at.date()
            )
        elif self.goal_type == 'expense_reduction':
            # Calculate expense reduction compared to baseline
            # This would need more complex logic with historical comparison
            return
        else:
            return
        
        total = transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        self.current_amount = abs(total)
        
        # Check if goal is completed
        if self.current_amount >= self.target_amount and self.status == 'active':
            self.status = 'completed'
            self.completed_at = timezone.now()
        
        self.save(update_fields=['current_amount', 'status', 'completed_at', 'updated_at'])


class BankSync(models.Model):
    """
    Bank synchronization logs and status
    """
    SYNC_STATUS = [
        ('pending', 'Pendente'),
        ('running', 'Executando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
        ('partial', 'Parcial'),
    ]
    
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='sync_logs')
    started_at = models.DateTimeField(_('started at'), auto_now_add=True)
    completed_at = models.DateTimeField(_('completed at'), blank=True, null=True)
    status = models.CharField(_('status'), max_length=20, choices=SYNC_STATUS, default='pending')
    
    # Sync details
    transactions_found = models.IntegerField(_('transactions found'), default=0)
    transactions_new = models.IntegerField(_('new transactions'), default=0)
    transactions_updated = models.IntegerField(_('updated transactions'), default=0)
    
    # Error handling
    error_message = models.TextField(_('error message'), blank=True)
    error_code = models.CharField(_('error code'), max_length=50, blank=True)
    
    # Sync range
    sync_from_date = models.DateField(_('sync from date'))
    sync_to_date = models.DateField(_('sync to date'))
    
    class Meta:
        db_table = 'bank_syncs'
        verbose_name = _('Bank Sync')
        verbose_name_plural = _('Bank Syncs')
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Sync {self.bank_account} - {self.status} ({self.started_at.strftime('%d/%m/%Y %H:%M')})"
    
    @property
    def duration(self):
        """Calculate sync duration"""
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return None


class BankConnection(models.Model):
    """
    Belvo bank connection management
    Manages connections to financial institutions via Belvo API
    """
    CONNECTION_STATUS_CHOICES = [
        ('valid', _('Valid')),
        ('invalid', _('Invalid')),
        ('unconfirmed', _('Unconfirmed')),
        ('token_renewal_required', _('Token Renewal Required')),
    ]
    
    LAST_ACCESS_MODE_CHOICES = [
        ('single', _('Single')),
        ('recurrent', _('Recurrent')),
    ]
    
    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Belvo connection data
    belvo_id = models.CharField(_('Belvo ID'), max_length=100, unique=True)
    institution = models.CharField(_('Institution'), max_length=100)
    display_name = models.CharField(_('Display Name'), max_length=255, blank=True)
    
    # Company association
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='bank_connections',
        verbose_name=_('Company')
    )
    
    # Connection status
    status = models.CharField(
        _('Status'), 
        max_length=30, 
        choices=CONNECTION_STATUS_CHOICES,
        default='unconfirmed'
    )
    
    # Access configuration
    last_access_mode = models.CharField(
        _('Last Access Mode'),
        max_length=20,
        choices=LAST_ACCESS_MODE_CHOICES,
        default='single'
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_bank_connections',
        verbose_name=_('Created By')
    )
    
    # Belvo timestamps
    belvo_created_at = models.DateTimeField(_('Belvo Created At'), null=True, blank=True)
    belvo_created_by = models.CharField(_('Belvo Created By'), max_length=100, blank=True)
    
    # Refresh token for renewed access
    refresh_rate = models.IntegerField(_('Refresh Rate'), default=86400)  # 24 hours
    
    # External ID (for reference)
    external_id = models.CharField(_('External ID'), max_length=100, blank=True)
    
    # Credentials storage (encrypted)
    credentials_stored = models.BooleanField(_('Credentials Stored'), default=False)
    
    # Metadata
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)
    
    class Meta:
        db_table = 'bank_connections'
        verbose_name = _('Bank Connection')
        verbose_name_plural = _('Bank Connections')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['belvo_id']),
            models.Index(fields=['institution']),
        ]
    
    def __str__(self):
        return f"{self.institution} - {self.display_name or 'Unnamed'} ({self.status})"
    
    def is_active(self):
        """Check if connection is active and valid"""
        return self.status == 'valid'
    
    def needs_token_renewal(self):
        """Check if connection needs token renewal"""
        return self.status == 'token_renewal_required'
    
    def get_institution_display(self):
        """Get formatted institution name"""
        return self.display_name or self.institution
    
    @property
    def connection_age_days(self):
        """Calculate connection age in days"""
        from django.utils import timezone
        if self.belvo_created_at:
            return (timezone.now() - self.belvo_created_at).days
        return (timezone.now() - self.created_at).days
    
    def update_status(self, new_status, save=True):
        """Update connection status with validation"""
        if new_status in dict(self.CONNECTION_STATUS_CHOICES):
            self.status = new_status
            if save:
                self.save(update_fields=['status'])
            return True
        return False
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'belvo_id': self.belvo_id,
            'institution': self.institution,
            'display_name': self.display_name,
            'status': self.status,
            'last_access_mode': self.last_access_mode,
            'created_at': self.created_at.isoformat(),
            'connection_age_days': self.connection_age_days,
            'is_active': self.is_active(),
            'needs_token_renewal': self.needs_token_renewal(),
        }