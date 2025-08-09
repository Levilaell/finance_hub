"""
Banking and financial transaction models - Pluggy Integration
Following Pluggy's official documentation structure
"""
import uuid
import logging
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import ActiveTransactionManager

User = get_user_model()
logger = logging.getLogger(__name__)


class PluggyConnector(models.Model):
    """
    Pluggy connector information (cached from API)
    Maps to Pluggy's connector concept
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pluggy_id = models.IntegerField(_('Pluggy ID'), unique=True, db_index=True)
    
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
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'pluggy_connectors'
        verbose_name = _('Pluggy Connector')
        verbose_name_plural = _('Pluggy Connectors')
        ordering = ['name']
        indexes = [
            models.Index(fields=['pluggy_id']),
            models.Index(fields=['type', 'country']),
            models.Index(fields=['is_open_finance']),
        ]
    
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
        ('DELETED', 'Deleted'),
        ('CONSENT_REVOKED', 'Consent Revoked'),
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
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pluggy_item_id = models.CharField(_('Pluggy Item ID'), max_length=100, unique=True, db_index=True)
    
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
    
    # Webhook configuration
    webhook_url = models.URLField(_('webhook URL'), blank=True)
    
    # Scheduling
    next_auto_sync_at = models.DateTimeField(_('next auto sync at'), null=True, blank=True)
    
    # Products enabled for this item
    products = models.JSONField(_('products'), default=list, blank=True)  # ['ACCOUNTS', 'TRANSACTIONS', etc]
    
    # MFA parameter for waiting user input
    parameter = models.JSONField(_('parameter'), default=dict, blank=True)  # For MFA responses - DEPRECATED, use encrypted_parameter
    encrypted_parameter = models.TextField(_('encrypted parameter'), blank=True, default='')  # Encrypted MFA parameters
    
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
    
    # Dates from Pluggy API
    pluggy_created_at = models.DateTimeField(_('Pluggy created at'))
    pluggy_updated_at = models.DateTimeField(_('Pluggy updated at'))
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
    
    # Local timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'pluggy_items'
        verbose_name = _('Pluggy Item')
        verbose_name_plural = _('Pluggy Items')
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['pluggy_item_id']),
            models.Index(fields=['last_successful_update']),
            models.Index(fields=['connector', 'status']),
        ]
    
    def __str__(self):
        return f"{self.connector.name} - {self.pluggy_item_id}"
    
    def get_mfa_parameter(self):
        """
        Get decrypted MFA parameter
        Returns the decrypted parameter or falls back to unencrypted if needed
        """
        from apps.banking.utils.encryption import banking_encryption
        
        # First try encrypted parameter
        if self.encrypted_parameter:
            try:
                return banking_encryption.decrypt_mfa_parameter(self.encrypted_parameter)
            except Exception as e:
                logger.error(f"Failed to decrypt parameter for item {self.pluggy_item_id}: {e}")
        
        # Fall back to unencrypted parameter for backward compatibility
        if self.parameter:
            return self.parameter
        
        return {}
    
    def set_mfa_parameter(self, parameter_data):
        """
        Set and encrypt MFA parameter
        
        Args:
            parameter_data: Dictionary with MFA parameter information
        """
        from apps.banking.utils.encryption import banking_encryption
        
        if not parameter_data:
            self.encrypted_parameter = ''
            self.parameter = {}
            return
        
        try:
            # Encrypt the parameter
            self.encrypted_parameter = banking_encryption.encrypt_mfa_parameter(parameter_data)
            # Clear the unencrypted field for security
            self.parameter = {}
        except Exception as e:
            logger.error(f"Failed to encrypt parameter for item {self.pluggy_item_id}: {e}")
            # Fallback to unencrypted (not recommended but prevents breaking)
            self.parameter = parameter_data
            self.encrypted_parameter = ''
    
    def clear_mfa_parameter(self):
        """Clear both encrypted and unencrypted MFA parameters"""
        self.encrypted_parameter = ''
        self.parameter = {}
    
    def save(self, *args, **kwargs):
        """Override save to handle parameter migration"""
        # Migrate unencrypted parameters to encrypted on save
        if self.parameter and not self.encrypted_parameter:
            from apps.banking.utils.encryption import banking_encryption
            try:
                self.encrypted_parameter = banking_encryption.encrypt_mfa_parameter(self.parameter)
                self.parameter = {}  # Clear unencrypted after successful encryption
            except Exception as e:
                logger.warning(f"Could not migrate parameter to encrypted format: {e}")
        
        super().save(*args, **kwargs)


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
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pluggy_account_id = models.CharField(_('Pluggy Account ID'), max_length=100, unique=True, db_index=True)
    
    # Relations
    item = models.ForeignKey(
        PluggyItem,
        on_delete=models.CASCADE,
        related_name='accounts'
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='bank_accounts'
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
    balance_in_account_currency = models.DecimalField(_('balance in account currency'), max_digits=15, decimal_places=2, null=True, blank=True)
    balance_date = models.DateTimeField(_('balance date'), blank=True, null=True)
    currency_code = models.CharField(_('currency code'), max_length=3, default='BRL')
    
    # Investment specific fields
    investment_status = models.CharField(_('investment status'), max_length=50, blank=True)
    
    # Bank specific data (for BANK type)
    bank_data = models.JSONField(_('bank data'), default=dict, blank=True, null=True)
    
    # Credit card specific data (for CREDIT type)
    credit_data = models.JSONField(_('credit data'), default=dict, blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Dates from Pluggy API
    pluggy_created_at = models.DateTimeField(_('Pluggy created at'))
    pluggy_updated_at = models.DateTimeField(_('Pluggy updated at'))
    
    # Local timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'bank_accounts'
        verbose_name = _('Bank Account')
        verbose_name_plural = _('Bank Accounts')
        unique_together = [['company', 'pluggy_account_id']]
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['item', 'type']),
            models.Index(fields=['pluggy_account_id']),
            models.Index(fields=['type', 'is_active']),
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
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pluggy_transaction_id = models.CharField(_('Pluggy Transaction ID'), max_length=100, unique=True, db_index=True)
    
    # Relations
    account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    # Transaction data
    type = models.CharField(_('type'), max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    status = models.CharField(_('status'), max_length=10, choices=TRANSACTION_STATUS_CHOICES, default='POSTED')
    
    description = models.CharField(_('description'), max_length=500)
    description_raw = models.TextField(_('description raw'), blank=True, null=True)  # Raw description from API
    amount = models.DecimalField(_('amount'), max_digits=15, decimal_places=2)
    amount_in_account_currency = models.DecimalField(_('amount in account currency'), max_digits=15, decimal_places=2, null=True, blank=True)
    balance = models.DecimalField(_('transaction balance'), max_digits=15, decimal_places=2, null=True, blank=True)  # Account balance after transaction
    currency_code = models.CharField(_('currency code'), max_length=3, default='BRL')
    
    date = models.DateTimeField(_('transaction date'))
    
    # Provider information
    provider_code = models.CharField(_('provider code'), max_length=50, blank=True)
    provider_id = models.CharField(_('provider ID'), max_length=100, blank=True)
    
    # Merchant info
    merchant = models.JSONField(_('merchant'), default=dict, blank=True, null=True)
    
    # Payment data (for Open Finance)
    payment_data = models.JSONField(_('payment data'), default=dict, blank=True, null=True)
    
    # Category from Pluggy
    pluggy_category_id = models.CharField(_('Pluggy category ID'), max_length=100, blank=True)
    pluggy_category_description = models.CharField(_('Pluggy category'), max_length=200, blank=True)
    
    # Mapped internal category
    category = models.ForeignKey(
        'TransactionCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    # Additional fields
    operation_type = models.CharField(_('operation type'), max_length=50, blank=True)
    payment_method = models.CharField(_('payment method'), max_length=50, blank=True)
    
    # Credit card specific
    credit_card_metadata = models.JSONField(_('credit card metadata'), default=dict, blank=True, null=True)
    
    # User annotations
    notes = models.TextField(_('notes'), blank=True)
    tags = models.JSONField(_('tags'), default=list, blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    
    # Dates from Pluggy API
    pluggy_created_at = models.DateTimeField(_('Pluggy created at'))
    pluggy_updated_at = models.DateTimeField(_('Pluggy updated at'))
    
    # Soft delete support
    is_deleted = models.BooleanField(_('is deleted'), default=False)
    deleted_at = models.DateTimeField(_('deleted at'), null=True, blank=True)
    
    # Local timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    # Managers
    objects = models.Manager()  # Default manager
    active = ActiveTransactionManager()  # Active transactions only
    
    class Meta:
        db_table = 'transactions'
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['account', 'date']),
            models.Index(fields=['company', 'date']),
            models.Index(fields=['pluggy_transaction_id']),
            models.Index(fields=['date', 'type']),
            models.Index(fields=['pluggy_category_id']),
            models.Index(fields=['category', 'date']),
            models.Index(fields=['type', 'status']),
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
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'transaction_categories'
        verbose_name = _('Transaction Category')
        verbose_name_plural = _('Transaction Categories')
        ordering = ['type', 'order', 'name']
        unique_together = [['company', 'slug']]
        indexes = [
            models.Index(fields=['company', 'type', 'is_active']),
            models.Index(fields=['slug']),
            models.Index(fields=['parent', 'order']),
        ]
    
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
        # Data Events
        ('item.created', 'Item Created'),
        ('item.updated', 'Item Updated'),
        ('item.error', 'Item Error'),
        ('item.deleted', 'Item Deleted'),
        ('item.login_succeeded', 'Login Succeeded'),
        ('item.waiting_user_input', 'Waiting User Input'),
        ('connector.status_updated', 'Connector Status Updated'),
        ('transactions.created', 'Transactions Created'),
        ('transactions.updated', 'Transactions Updated'),
        ('transactions.deleted', 'Transactions Deleted'),
        ('consent.created', 'Consent Created'),
        ('consent.updated', 'Consent Updated'),
        ('consent.revoked', 'Consent Revoked'),
        
        # Payment Events (if using Pluggy Payments)
        ('payment_intent.created', 'Payment Intent Created'),
        ('payment_intent.completed', 'Payment Intent Completed'),
        ('payment_intent.waiting_payer_authorization', 'Payment Intent Waiting Payer Authorization'),
        ('payment_intent.error', 'Payment Intent Error'),
        ('scheduled_payment.created', 'Scheduled Payment Created'),
        ('scheduled_payment.completed', 'Scheduled Payment Completed'),
        ('scheduled_payment.error', 'Scheduled Payment Error'),
        ('scheduled_payment.canceled', 'Scheduled Payment Canceled'),
        ('payment_refund.completed', 'Payment Refund Completed'),
        ('payment_refund.error', 'Payment Refund Error'),
        ('automatic_pix_payment.created', 'Automatic PIX Payment Created'),
        ('automatic_pix_payment.completed', 'Automatic PIX Payment Completed'),
        ('automatic_pix_payment.error', 'Automatic PIX Payment Error'),
        ('automatic_pix_payment.canceled', 'Automatic PIX Payment Canceled'),
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
    
    # Who triggered the webhook
    TRIGGER_CHOICES = [
        ('USER', 'User Action'),
        ('CLIENT', 'Client Action'), 
        ('SYNC', 'Sync Process'),
        ('INTERNAL', 'Internal Process'),
    ]
    triggered_by = models.CharField(
        _('triggered by'), 
        max_length=20, 
        choices=TRIGGER_CHOICES,
        blank=True,
        help_text=_('Who or what triggered this webhook event')
    )
    
    error = models.TextField(_('error'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'item_webhooks'
        verbose_name = _('Item Webhook')
        verbose_name_plural = _('Item Webhooks')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['item', 'event_type']),
            models.Index(fields=['processed', 'created_at']),
            models.Index(fields=['event_id']),
            models.Index(fields=['event_type', 'processed']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.item.pluggy_item_id}"