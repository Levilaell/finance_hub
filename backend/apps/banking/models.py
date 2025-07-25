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
    logo_url = models.URLField(_('logo URL'), blank=True, help_text='External logo URL (e.g., from Pluggy)')
    color = models.CharField(_('brand color'), max_length=7, default='#000000')
    primary_color = models.CharField(_('primary color'), max_length=7, default='#000000', blank=True)
    is_open_banking = models.BooleanField(_('supports Open Banking'), default=True)
    api_endpoint = models.URLField(_('API endpoint'), blank=True)
    is_active = models.BooleanField(_('is active'), default=True)
    is_open_finance = models.BooleanField(
        default=False,
        help_text='Se este provedor é um conector Open Finance'
    )
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
        ('credit_card', 'Cartão de Crédito'),
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
    agency = models.CharField(_('agency'), max_length=10, blank=True, null=True)
    account_number = models.CharField(_('account number'), max_length=20)
    account_digit = models.CharField(_('account digit'), max_length=2, blank=True)
    name = models.CharField(_('account name'), max_length=255, blank=True)
    currency = models.CharField(_('currency'), max_length=3, default='BRL')
    
    # Open Banking integration
    external_id = models.CharField(_('external account ID'), max_length=100, blank=True)
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
    sync_status = models.CharField(_('sync status'), max_length=30, default='active', blank=True)
    sync_error_message = models.TextField(_('sync error message'), blank=True)
    
    # Account settings
    nickname = models.CharField(_('nickname'), max_length=100, blank=True)
    is_primary = models.BooleanField(_('is primary account'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Additional data
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'bank_accounts'
        verbose_name = _('Bank Account')
        verbose_name_plural = _('Bank Accounts')
        unique_together = [('company', 'external_id')]  # Pluggy provides unique IDs
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['bank_provider', 'external_id']),
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
        """Custom validation for bank accounts"""
        super().clean()
        
        # For Pluggy integration, we rely on external_id for uniqueness
        # Agency and account validation is optional since formats vary by bank
        pass
    
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
    
    def save(self, *args, **kwargs):
        """Auto-generate slug if not provided"""
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while TransactionCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


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
    
    # Categorization is now handled automatically by Pluggy
    
    # Additional metadata
    reference_number = models.CharField(_('reference number'), max_length=100, blank=True)
    pix_key = models.CharField(_('PIX key'), max_length=100, blank=True)
    notes = models.TextField(_('notes'), blank=True)
    tags = models.JSONField(_('tags'), default=list)
    metadata = models.JSONField(_('metadata'), default=dict, blank=True, help_text='Additional data from Pluggy')
    
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
            # AI categorization indexes removed - now using Pluggy automatic categorization
            
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


