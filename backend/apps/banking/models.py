"""
Banking models for Pluggy integration
"""
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class PluggyConnector(models.Model):
    """
    Pluggy connectors (banks/financial institutions)
    Synced from Pluggy API
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pluggy_id = models.IntegerField(_('Pluggy ID'), unique=True, db_index=True)
    name = models.CharField(_('name'), max_length=200)
    institution_url = models.URLField(_('institution URL'), blank=True)
    image_url = models.URLField(_('image URL'), blank=True)
    primary_color = models.CharField(_('primary color'), max_length=7, default='#000000')
    type = models.CharField(_('type'), max_length=50)  # e.g., 'PERSONAL_BANK'
    country = models.CharField(_('country'), max_length=2, default='BR')
    
    # Capabilities
    has_mfa = models.BooleanField(_('has MFA'), default=False)
    has_oauth = models.BooleanField(_('has OAuth'), default=False)
    is_open_finance = models.BooleanField(_('is Open Finance'), default=False)
    is_sandbox = models.BooleanField(_('is sandbox'), default=False)
    
    # Configuration
    products = models.JSONField(_('supported products'), default=list)
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
        return self.name

    @property
    def supports_accounts(self):
        return 'ACCOUNTS' in self.products

    @property
    def supports_transactions(self):
        return 'TRANSACTIONS' in self.products
    
    @property
    def supports_credit_cards(self):
        return 'CREDITCARDS' in self.products


class PluggyItem(models.Model):
    """
    Pluggy Item - represents a connection to a financial institution for a company
    """
    STATUS_CHOICES = [
        ('WAITING_USER_INPUT', _('Waiting User Input')),
        ('UPDATING', _('Updating')),
        ('UPDATED', _('Updated')),
        ('LOGIN_ERROR', _('Login Error')),
        ('OUTDATED', _('Outdated')),
    ]

    EXECUTION_STATUS_CHOICES = [
        ('CREATED', _('Created')),
        ('LOGIN_IN_PROGRESS', _('Login In Progress')),
        ('LOGIN_MFA_IN_PROGRESS', _('Login MFA In Progress')),
        ('ACCOUNTS_IN_PROGRESS', _('Accounts In Progress')),
        ('CREDITCARDS_IN_PROGRESS', _('Credit Cards In Progress')),
        ('TRANSACTIONS_IN_PROGRESS', _('Transactions In Progress')),
        ('INVESTMENT_TRANSACTIONS_IN_PROGRESS', _('Investment Transactions In Progress')),
        ('PAYMENT_DATA_IN_PROGRESS', _('Payment Data In Progress')),
        ('IDENTITY_IN_PROGRESS', _('Identity In Progress')),
        ('MERGING', _('Merging')),
        ('ERROR', _('Error')),
        ('MERGE_ERROR', _('Merge Error')),
        ('INVALID_CREDENTIALS', _('Invalid Credentials')),
        ('ALREADY_LOGGED_IN', _('Already Logged In')),
        ('SITE_NOT_AVAILABLE', _('Site Not Available')),
        ('INVALID_CREDENTIALS_MFA', _('Invalid Credentials MFA')),
        ('USER_INPUT_TIMEOUT', _('User Input Timeout')),
        ('ACCOUNT_LOCKED', _('Account Locked')),
        ('ACCOUNT_NEEDS_ACTION', _('Account Needs Action')),
        ('USER_NOT_SUPPORTED', _('User Not Supported')),
        ('ACCOUNT_CREDENTIALS_RESET', _('Account Credentials Reset')),
        ('CONNECTION_ERROR', _('Connection Error')),
        ('USER_AUTHORIZATION_NOT_GRANTED', _('User Authorization Not Granted')),
        ('USER_AUTHORIZATION_REVOKED', _('User Authorization Revoked')),
        ('WAITING_USER_INPUT', _('Waiting User Input')),
        ('USER_AUTHORIZATION_PENDING', _('User Authorization Pending')),
        ('SUCCESS', _('Success')),
        ('PARTIAL_SUCCESS', _('Partial Success')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='pluggy_items')
    connector = models.ForeignKey(PluggyConnector, on_delete=models.PROTECT, related_name='items')
    
    # Pluggy data
    pluggy_item_id = models.CharField(_('Pluggy Item ID'), max_length=100, unique=True, db_index=True)
    client_user_id = models.CharField(_('client user ID'), max_length=100, blank=True)
    webhook_url = models.URLField(_('webhook URL'), blank=True)
    products = models.JSONField(_('products'), default=list, blank=True)
    
    # Status tracking
    status = models.CharField(_('status'), max_length=30, choices=STATUS_CHOICES, default='CREATED')
    execution_status = models.CharField(_('execution status'), max_length=50, choices=EXECUTION_STATUS_CHOICES, blank=True)
    
    # Timestamps from Pluggy
    pluggy_created_at = models.DateTimeField(_('Pluggy created at'))
    pluggy_updated_at = models.DateTimeField(_('Pluggy updated at'))
    last_successful_update = models.DateTimeField(_('last successful update'), null=True, blank=True)
    
    # Error handling
    error_code = models.CharField(_('error code'), max_length=50, blank=True)
    error_message = models.TextField(_('error message'), blank=True)
    status_detail = models.JSONField(_('status detail'), default=dict, blank=True)
    
    # Open Finance (if applicable)
    consent_id = models.CharField(_('consent ID'), max_length=100, blank=True)
    consent_expires_at = models.DateTimeField(_('consent expires at'), null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    
    # Our timestamps
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
        return f"{self.connector.name} - {self.company.name}"

    @property
    def is_connected(self):
        return self.status in ['UPDATED', 'UPDATING']
    
    @property
    def has_error(self):
        return self.status == 'LOGIN_ERROR' or 'ERROR' in (self.execution_status or '')
    
    @property
    def needs_user_action(self):
        return self.status == 'WAITING_USER_INPUT'
    
    @property
    def is_outdated(self):
        return self.status == 'OUTDATED'


class BankAccount(models.Model):
    """
    Bank Account from Pluggy
    """
    ACCOUNT_TYPES = [
        ('BANK', _('Bank Account')),
        ('CREDIT', _('Credit Card')),
        ('INVESTMENT', _('Investment')),
        ('LOAN', _('Loan')),
        ('OTHER', _('Other')),
    ]

    ACCOUNT_SUBTYPES = [
        ('CHECKING_ACCOUNT', _('Checking Account')),
        ('SAVINGS_ACCOUNT', _('Savings Account')),
        ('CREDIT_CARD', _('Credit Card')),
        ('PREPAID_CARD', _('Prepaid Card')),
        ('INVESTMENT_ACCOUNT', _('Investment Account')),
        ('LOAN_ACCOUNT', _('Loan Account')),
        ('OTHER', _('Other')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='bank_accounts')
    item = models.ForeignKey(PluggyItem, on_delete=models.CASCADE, related_name='accounts')
    
    # Pluggy data
    pluggy_account_id = models.CharField(_('Pluggy Account ID'), max_length=100, unique=True, db_index=True)
    type = models.CharField(_('type'), max_length=20, choices=ACCOUNT_TYPES)
    subtype = models.CharField(_('subtype'), max_length=30, choices=ACCOUNT_SUBTYPES, blank=True)
    number = models.CharField(_('number'), max_length=50, blank=True)
    name = models.CharField(_('name'), max_length=200, blank=True)
    marketing_name = models.CharField(_('marketing name'), max_length=200, null=True, blank=True)
    
    # Account holder info
    owner = models.CharField(_('owner'), max_length=200, null=True, blank=True)
    tax_number = models.CharField(_('tax number'), max_length=20, null=True, blank=True)
    
    # Balance information
    balance = models.DecimalField(_('balance'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    balance_in_account_currency = models.DecimalField(
        _('balance in account currency'), 
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    balance_date = models.DateTimeField(_('balance date'), null=True, blank=True)
    currency_code = models.CharField(_('currency code'), max_length=3, default='BRL')
    
    # Additional data (varies by account type)
    bank_data = models.JSONField(_('bank data'), default=dict, null=True, blank=True)
    credit_data = models.JSONField(_('credit data'), default=dict, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Timestamps from Pluggy
    pluggy_created_at = models.DateTimeField(_('Pluggy created at'))
    pluggy_updated_at = models.DateTimeField(_('Pluggy updated at'))
    
    # Our timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'bank_accounts'
        verbose_name = _('Bank Account')
        verbose_name_plural = _('Bank Accounts')
        unique_together = [('company', 'pluggy_account_id')]
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['item', 'type']),
            models.Index(fields=['pluggy_account_id']),
            models.Index(fields=['type', 'is_active']),
        ]

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.number})"
        return f"{self.item.connector.name} - {self.number}"

    @property
    def bank_name(self):
        return self.item.connector.name

    @property
    def masked_number(self):
        if not self.number:
            return "****"
        if len(self.number) <= 4:
            return self.number
        return f"****{self.number[-4:]}"

    @property
    def is_credit_card(self):
        return self.type == 'CREDIT'

    @property
    def formatted_balance(self):
        from django.contrib.humanize.templatetags.humanize import intcomma
        return f"R$ {intcomma(self.balance)}"


class TransactionCategory(models.Model):
    """
    Transaction categories for organizing expenses/income
    """
    CATEGORY_TYPES = [
        ('income', _('Income')),
        ('expense', _('Expense')),
        ('transfer', _('Transfer')),
        ('both', _('Both')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='transaction_categories', null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='subcategories', null=True, blank=True)
    
    # Category details
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True)
    type = models.CharField(_('type'), max_length=20, choices=CATEGORY_TYPES)
    
    # Visual
    icon = models.CharField(_('icon'), max_length=50, default='📁')
    color = models.CharField(_('color'), max_length=7, default='#6B7280')
    
    # System vs User categories
    is_system = models.BooleanField(_('is system category'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    order = models.IntegerField(_('order'), default=0)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'transaction_categories'
        verbose_name = _('Transaction Category')
        verbose_name_plural = _('Transaction Categories')
        unique_together = [('company', 'slug')]
        ordering = ['type', 'order', 'name']
        indexes = [
            models.Index(fields=['company', 'type', 'is_active']),
            models.Index(fields=['slug']),
            models.Index(fields=['parent', 'order']),
        ]

    def __str__(self):
        return self.name


class PluggyCategory(models.Model):
    """
    Pluggy categories mapping to our internal categories
    """
    id = models.CharField(_('category ID'), max_length=100, primary_key=True)
    description = models.CharField(_('description'), max_length=200)
    parent_id = models.CharField(_('parent ID'), max_length=100, null=True, blank=True)
    parent_description = models.CharField(_('parent description'), max_length=200, blank=True)
    
    # Mapping to our internal category
    internal_category = models.ForeignKey(
        TransactionCategory, 
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
    Financial transactions from bank accounts
    """
    TRANSACTION_TYPES = [
        ('DEBIT', _('Debit')),
        ('CREDIT', _('Credit')),
    ]

    TRANSACTION_STATUS = [
        ('PENDING', _('Pending')),
        ('POSTED', _('Posted')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    # Pluggy data
    pluggy_transaction_id = models.CharField(_('Pluggy Transaction ID'), max_length=100, unique=True, db_index=True)
    type = models.CharField(_('type'), max_length=10, choices=TRANSACTION_TYPES)
    status = models.CharField(_('status'), max_length=10, choices=TRANSACTION_STATUS, default='POSTED')
    
    # Transaction details
    description = models.CharField(_('description'), max_length=500)
    description_raw = models.TextField(_('description raw'), null=True, blank=True)
    amount = models.DecimalField(_('amount'), max_digits=15, decimal_places=2)
    amount_in_account_currency = models.DecimalField(
        _('amount in account currency'), 
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    balance = models.DecimalField(_('transaction balance'), max_digits=15, decimal_places=2, null=True, blank=True)
    currency_code = models.CharField(_('currency code'), max_length=3, default='BRL')
    date = models.DateTimeField(_('transaction date'))
    
    # Provider information
    provider_code = models.CharField(_('provider code'), max_length=50, blank=True)
    provider_id = models.CharField(_('provider ID'), max_length=100, blank=True)
    
    # Additional data
    merchant = models.JSONField(_('merchant'), default=dict, null=True, blank=True)
    payment_data = models.JSONField(_('payment data'), default=dict, null=True, blank=True)
    
    # Pluggy category
    pluggy_category_id = models.CharField(_('Pluggy category ID'), max_length=100, blank=True)
    pluggy_category_description = models.CharField(_('Pluggy category'), max_length=200, blank=True)
    
    # Transaction metadata
    operation_type = models.CharField(_('operation type'), max_length=50, blank=True)
    payment_method = models.CharField(_('payment method'), max_length=50, blank=True)
    credit_card_metadata = models.JSONField(_('credit card metadata'), default=dict, null=True, blank=True)
    
    # User annotations
    notes = models.TextField(_('notes'), blank=True)
    tags = models.JSONField(_('tags'), default=list, null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    
    # Timestamps from Pluggy
    pluggy_created_at = models.DateTimeField(_('Pluggy created at'))
    pluggy_updated_at = models.DateTimeField(_('Pluggy updated at'))
    
    # Soft delete
    is_deleted = models.BooleanField(_('is deleted'), default=False)
    deleted_at = models.DateTimeField(_('deleted at'), null=True, blank=True)
    
    # Our timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

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
        return f"{self.description} - {self.formatted_amount}"

    @property
    def formatted_amount(self):
        from django.contrib.humanize.templatetags.humanize import intcomma
        symbol = "+" if self.type == 'CREDIT' else "-"
        return f"{symbol}R$ {intcomma(abs(self.amount))}"

    @property
    def is_income(self):
        return self.type == 'CREDIT'

    @property
    def is_expense(self):
        return self.type == 'DEBIT'

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])


class ItemWebhook(models.Model):
    """
    Webhook events from Pluggy
    """
    WEBHOOK_EVENTS = [
        ('item.created', _('Item Created')),
        ('item.updated', _('Item Updated')),
        ('item.error', _('Item Error')),
        ('item.deleted', _('Item Deleted')),
        ('item.login_succeeded', _('Login Succeeded')),
        ('item.waiting_user_input', _('Waiting User Input')),
        ('connector.status_updated', _('Connector Status Updated')),
        ('transactions.created', _('Transactions Created')),
        ('transactions.updated', _('Transactions Updated')),
        ('transactions.deleted', _('Transactions Deleted')),
        ('consent.created', _('Consent Created')),
        ('consent.updated', _('Consent Updated')),
        ('consent.revoked', _('Consent Revoked')),
        ('payment_intent.created', _('Payment Intent Created')),
        ('payment_intent.completed', _('Payment Intent Completed')),
        ('payment_intent.waiting_payer_authorization', _('Payment Intent Waiting Payer Authorization')),
        ('payment_intent.error', _('Payment Intent Error')),
        ('scheduled_payment.created', _('Scheduled Payment Created')),
        ('scheduled_payment.completed', _('Scheduled Payment Completed')),
        ('scheduled_payment.error', _('Scheduled Payment Error')),
        ('scheduled_payment.canceled', _('Scheduled Payment Canceled')),
        ('payment_refund.completed', _('Payment Refund Completed')),
        ('payment_refund.error', _('Payment Refund Error')),
        ('automatic_pix_payment.created', _('Automatic PIX Payment Created')),
        ('automatic_pix_payment.completed', _('Automatic PIX Payment Completed')),
        ('automatic_pix_payment.error', _('Automatic PIX Payment Error')),
        ('automatic_pix_payment.canceled', _('Automatic PIX Payment Canceled')),
    ]

    TRIGGERED_BY_CHOICES = [
        ('USER', _('User Action')),
        ('CLIENT', _('Client Action')),
        ('SYNC', _('Sync Process')),
        ('INTERNAL', _('Internal Process')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(PluggyItem, on_delete=models.CASCADE, related_name='webhooks')
    
    # Webhook data
    event_type = models.CharField(_('event type'), max_length=50, choices=WEBHOOK_EVENTS)
    event_id = models.CharField(_('event ID'), max_length=100, unique=True)
    payload = models.JSONField(_('payload'))
    
    # Processing status
    processed = models.BooleanField(_('processed'), default=False)
    processed_at = models.DateTimeField(_('processed at'), null=True, blank=True)
    triggered_by = models.CharField(
        _('triggered by'), 
        max_length=20, 
        choices=TRIGGERED_BY_CHOICES, 
        blank=True,
        help_text=_('Who or what triggered this webhook event')
    )
    error = models.TextField(_('error'), blank=True)
    
    # Timestamp
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
        return f"{self.event_type} - {self.item}"

    def mark_as_processed(self, error=None):
        self.processed = True
        self.processed_at = timezone.now()
        if error:
            self.error = str(error)
        self.save(update_fields=['processed', 'processed_at', 'error'])