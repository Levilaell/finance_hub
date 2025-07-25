"""
Banking and financial transaction models - Pluggy Integration
Following Pluggy's official documentation structure
"""
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class PluggyConnector(models.Model):
    """
    Pluggy connector information (cached from API)
    Maps to Pluggy's connector concept
    """
    # Pluggy connector ID
    pluggy_id = models.IntegerField(_('Pluggy ID'), unique=True, primary_key=True)
    
    # Basic info
    name = models.CharField(_('name'), max_length=200)
    institution_url = models.URLField(_('institution URL'), blank=True)
    image_url = models.URLField(_('image URL'), blank=True)
    primary_color = models.CharField(_('primary color'), max_length=7, default='#000000')
    
    # Type and classification
    type = models.CharField(_('type'), max_length=50)  # PERSONAL_BANK, BUSINESS_BANK, etc
    country = models.CharField(_('country'), max_length=2, default='BR')
    
    # Features
    has_mfa = models.BooleanField(_('has MFA'), default=False)
    has_oauth = models.BooleanField(_('has OAuth'), default=False)
    is_open_finance = models.BooleanField(_('is Open Finance'), default=False)
    is_sandbox = models.BooleanField(_('is sandbox'), default=False)
    
    # Supported products
    products = models.JSONField(_('supported products'), default=list)  # ['ACCOUNTS', 'TRANSACTIONS', etc]
    
    # Credentials schema
    credentials = models.JSONField(_('credentials schema'), default=list)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'pluggy_connectors'
        verbose_name = _('Pluggy Connector')
        verbose_name_plural = _('Pluggy Connectors')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.pluggy_id})"


class PluggyItem(models.Model):
    """
    Represents a connection to a financial institution via Pluggy
    Maps to Pluggy's Item concept
    """
    ITEM_STATUS_CHOICES = [
        ('LOGIN_IN_PROGRESS', 'Login in Progress'),
        ('WAITING_USER_INPUT', 'Waiting User Input'),
        ('UPDATING', 'Updating'),
        ('UPDATED', 'Updated'),
        ('LOGIN_ERROR', 'Login Error'),
        ('OUTDATED', 'Outdated'),
        ('ERROR', 'Error'),
    ]
    
    EXECUTION_STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('SUCCESS', 'Success'),
        ('PARTIAL_SUCCESS', 'Partial Success'),
        ('LOGIN_ERROR', 'Login Error'),
        ('INVALID_CREDENTIALS', 'Invalid Credentials'),
        ('USER_INPUT_TIMEOUT', 'User Input Timeout'),
        ('USER_AUTHORIZATION_PENDING', 'User Authorization Pending'),
        ('USER_AUTHORIZATION_NOT_GRANTED', 'User Authorization Not Granted'),
        ('SITE_NOT_AVAILABLE', 'Site Not Available'),
        ('ERROR', 'Error'),
    ]
    
    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pluggy_id = models.CharField(_('Pluggy Item ID'), max_length=100, unique=True, db_index=True)
    
    # Relations
    company = models.ForeignKey(
        'companies.Company', 
        on_delete=models.CASCADE, 
        related_name='pluggy_items'
    )
    connector = models.ForeignKey(
        PluggyConnector,
        on_delete=models.PROTECT,
        related_name='items'
    )
    
    # User tracking
    client_user_id = models.CharField(_('client user ID'), max_length=100, blank=True)
    
    # Status tracking
    status = models.CharField(
        _('status'), 
        max_length=30, 
        choices=ITEM_STATUS_CHOICES,
        default='CREATED'
    )
    execution_status = models.CharField(
        _('execution status'),
        max_length=50,
        choices=EXECUTION_STATUS_CHOICES,
        blank=True
    )
    
    # Dates
    created_at = models.DateTimeField(_('created at'))
    updated_at = models.DateTimeField(_('updated at'))
    last_successful_update = models.DateTimeField(_('last successful update'), null=True, blank=True)
    
    # Error tracking
    error_code = models.CharField(_('error code'), max_length=50, blank=True)
    error_message = models.TextField(_('error message'), blank=True)
    
    # Status details from Pluggy
    status_detail = models.JSONField(_('status detail'), default=dict, blank=True)
    
    # Consents (for Open Finance)
    consent_id = models.CharField(_('consent ID'), max_length=100, blank=True)
    consent_expires_at = models.DateTimeField(_('consent expires at'), null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    
    # Tracking
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    
    class Meta:
        db_table = 'pluggy_items'
        verbose_name = _('Pluggy Item')
        verbose_name_plural = _('Pluggy Items')
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['pluggy_id']),
            models.Index(fields=['last_successful_update']),
        ]
    
    def __str__(self):
        return f"{self.connector.name} - {self.pluggy_id}"


class BankAccount(models.Model):
    """
    Bank account connected via Pluggy
    """
    ACCOUNT_TYPE_CHOICES = [
        ('BANK', 'Bank Account'),
        ('CREDIT', 'Credit Card'),
        ('INVESTMENT', 'Investment'),
        ('LOAN', 'Loan'),
        ('OTHER', 'Other'),
    ]
    
    ACCOUNT_SUBTYPE_CHOICES = [
        ('CHECKING_ACCOUNT', 'Checking Account'),
        ('SAVINGS_ACCOUNT', 'Savings Account'),
        ('CREDIT_CARD', 'Credit Card'),
        ('PREPAID_CARD', 'Prepaid Card'),
        ('INVESTMENT_ACCOUNT', 'Investment Account'),
        ('LOAN_ACCOUNT', 'Loan Account'),
        ('OTHER', 'Other'),
    ]
    
    # IDs
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pluggy_id = models.CharField(_('Pluggy Account ID'), max_length=100, unique=True, db_index=True)
    
    # Relations
    item = models.ForeignKey(
        PluggyItem,
        on_delete=models.CASCADE,
        related_name='accounts'
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='bank_accounts_v2'
    )
    
    # Account info from Pluggy
    type = models.CharField(_('type'), max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    subtype = models.CharField(_('subtype'), max_length=30, choices=ACCOUNT_SUBTYPE_CHOICES, blank=True)
    number = models.CharField(_('number'), max_length=50, blank=True)
    name = models.CharField(_('name'), max_length=200, blank=True)
    marketing_name = models.CharField(_('marketing name'), max_length=200, blank=True, null=True)
    
    # Owner info
    owner = models.CharField(_('owner'), max_length=200, blank=True, null=True)
    tax_number = models.CharField(_('tax number'), max_length=20, blank=True, null=True)
    
    # Balance info
    balance = models.DecimalField(_('balance'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    balance_date = models.DateTimeField(_('balance date'), blank=True, null=True)
    currency_code = models.CharField(_('currency code'), max_length=3, default='BRL')
    
    # Bank specific data (for BANK type)
    bank_data = models.JSONField(_('bank data'), default=dict, blank=True, null=True)
    
    # Credit card specific data (for CREDIT type)
    credit_data = models.JSONField(_('credit data'), default=dict, blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'))
    updated_at = models.DateTimeField(_('updated at'))
    
    # Tracking
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    
    class Meta:
        db_table = 'bank_accounts_v2'
        verbose_name = _('Bank Account')
        verbose_name_plural = _('Bank Accounts')
        unique_together = [['company', 'pluggy_id']]
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['item', 'type']),
            models.Index(fields=['pluggy_id']),
        ]
    
    def __str__(self):
        return f"{self.name or self.number} - {self.get_type_display()}"
    
    @property
    def masked_number(self):
        """Return masked account number for security"""
        if self.number and len(self.number) > 4:
            return f"****{self.number[-4:]}"
        return self.number
    
    @property
    def display_name(self):
        """Return display name for the account"""
        if self.name:
            return self.name
        elif self.marketing_name:
            return self.marketing_name
        else:
            return f"{self.item.connector.name} - {self.masked_number}"


class PluggyCategory(models.Model):
    """
    Pluggy's transaction categories (cached)
    """
    id = models.CharField(_('category ID'), max_length=100, primary_key=True)
    description = models.CharField(_('description'), max_length=200)
    parent_id = models.CharField(_('parent ID'), max_length=100, blank=True, null=True)
    parent_description = models.CharField(_('parent description'), max_length=200, blank=True)
    
    # Mapping to internal categories
    internal_category = models.ForeignKey(
        'TransactionCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pluggy_mappings'
    )
    
    class Meta:
        db_table = 'pluggy_categories'
        verbose_name = _('Pluggy Category')
        verbose_name_plural = _('Pluggy Categories')
        ordering = ['parent_description', 'description']
    
    def __str__(self):
        if self.parent_description:
            return f"{self.parent_description} > {self.description}"
        return self.description


class Transaction(models.Model):
    """
    Financial transaction from Pluggy
    """
    TRANSACTION_TYPE_CHOICES = [
        ('DEBIT', 'Debit'),
        ('CREDIT', 'Credit'),
    ]
    
    TRANSACTION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('POSTED', 'Posted'),
    ]
    
    # IDs
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pluggy_id = models.CharField(_('Pluggy Transaction ID'), max_length=100, unique=True, db_index=True)
    
    # Relations
    account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    # Transaction data
    type = models.CharField(_('type'), max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    status = models.CharField(_('status'), max_length=10, choices=TRANSACTION_STATUS_CHOICES, default='POSTED')
    
    description = models.CharField(_('description'), max_length=500)
    amount = models.DecimalField(_('amount'), max_digits=15, decimal_places=2)
    currency_code = models.CharField(_('currency code'), max_length=3, default='BRL')
    
    date = models.DateTimeField(_('transaction date'))
    
    # Merchant info
    merchant = models.JSONField(_('merchant'), default=dict, blank=True)
    
    # Payment data (for Open Finance)
    payment_data = models.JSONField(_('payment data'), default=dict, blank=True)
    
    # Category from Pluggy
    pluggy_category_id = models.CharField(_('Pluggy category ID'), max_length=100, blank=True)
    pluggy_category_description = models.CharField(_('Pluggy category'), max_length=200, blank=True)
    
    # Mapped internal category
    category = models.ForeignKey(
        'TransactionCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_v2'
    )
    
    # Additional fields
    operation_type = models.CharField(_('operation type'), max_length=50, blank=True)
    payment_method = models.CharField(_('payment method'), max_length=50, blank=True)
    
    # Credit card specific
    credit_card_metadata = models.JSONField(_('credit card metadata'), default=dict, blank=True)
    
    # User annotations
    notes = models.TextField(_('notes'), blank=True)
    tags = models.JSONField(_('tags'), default=list)
    
    # Metadata
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    created_at = models.DateTimeField(_('created at'))
    updated_at = models.DateTimeField(_('updated at'))
    
    # Tracking
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    
    class Meta:
        db_table = 'transactions_v2'
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['account', 'date']),
            models.Index(fields=['pluggy_id']),
            models.Index(fields=['date', 'type']),
            models.Index(fields=['pluggy_category_id']),
            models.Index(fields=['category', 'date']),
        ]
    
    def __str__(self):
        return f"{self.description} - {self.get_amount_display()}"
    
    def get_amount_display(self):
        """Return formatted amount with sign"""
        if self.type == 'CREDIT':
            return f"+{self.currency_code} {abs(self.amount):,.2f}"
        else:
            return f"-{self.currency_code} {abs(self.amount):,.2f}"
    
    @property
    def is_income(self):
        """Check if transaction is income"""
        return self.type == 'CREDIT'
    
    @property
    def is_expense(self):
        """Check if transaction is expense"""
        return self.type == 'DEBIT'


class TransactionCategory(models.Model):
    """
    Internal transaction categories for organization
    """
    CATEGORY_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
        ('both', 'Both'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True)
    type = models.CharField(_('type'), max_length=20, choices=CATEGORY_TYPE_CHOICES)
    
    # Hierarchy
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    
    # Visual
    icon = models.CharField(_('icon'), max_length=50, default='📁')
    color = models.CharField(_('color'), max_length=7, default='#6B7280')
    
    # Settings
    is_system = models.BooleanField(_('is system category'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    order = models.IntegerField(_('order'), default=0)
    
    # Company specific
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='transaction_categories',
        null=True,
        blank=True
    )
    
    # Metadata
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    
    class Meta:
        db_table = 'transaction_categories_v2'
        verbose_name = _('Transaction Category')
        verbose_name_plural = _('Transaction Categories')
        ordering = ['type', 'order', 'name']
        unique_together = [['company', 'slug']]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            while TransactionCategory.objects.filter(
                slug=slug,
                company=self.company
            ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)


class ItemWebhook(models.Model):
    """
    Track webhook events for items
    """
    EVENT_TYPE_CHOICES = [
        ('item.created', 'Item Created'),
        ('item.updated', 'Item Updated'),
        ('item.error', 'Item Error'),
        ('item.deleted', 'Item Deleted'),
        ('item.login_succeeded', 'Login Succeeded'),
        ('item.waiting_user_input', 'Waiting User Input'),
        ('transactions.created', 'Transactions Created'),
        ('transactions.updated', 'Transactions Updated'),
        ('transactions.deleted', 'Transactions Deleted'),
        ('consent.created', 'Consent Created'),
        ('consent.updated', 'Consent Updated'),
        ('consent.revoked', 'Consent Revoked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(
        PluggyItem,
        on_delete=models.CASCADE,
        related_name='webhooks'
    )
    
    event_type = models.CharField(_('event type'), max_length=50, choices=EVENT_TYPE_CHOICES)
    event_id = models.CharField(_('event ID'), max_length=100, unique=True)
    
    payload = models.JSONField(_('payload'))
    processed = models.BooleanField(_('processed'), default=False)
    processed_at = models.DateTimeField(_('processed at'), null=True, blank=True)
    
    error = models.TextField(_('error'), blank=True)
    
    created = models.DateTimeField(_('created'), auto_now_add=True)
    
    class Meta:
        db_table = 'item_webhooks'
        verbose_name = _('Item Webhook')
        verbose_name_plural = _('Item Webhooks')
        ordering = ['-created']
        indexes = [
            models.Index(fields=['item', 'event_type']),
            models.Index(fields=['processed', 'created']),
            models.Index(fields=['event_id']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.item.pluggy_id}"