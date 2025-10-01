"""
Banking models for Pluggy integration.
Ref: https://docs.pluggy.ai/docs/data-structure
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class Connector(models.Model):
    """
    Represents a bank/financial institution connector from Pluggy.
    Ref: https://docs.pluggy.ai/reference/connector-retrieve
    """
    pluggy_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=200)
    institution_name = models.CharField(max_length=200)
    institution_url = models.CharField(max_length=500, blank=True)
    country = models.CharField(max_length=2, default='BR')
    primary_color = models.CharField(max_length=7, blank=True)  # Hex color
    logo_url = models.CharField(max_length=500, blank=True)
    type = models.CharField(max_length=50)  # PERSONAL_BANK, BUSINESS_BANK, etc.
    credentials_schema = models.JSONField(default=dict)  # Schema for required credentials
    supports_mfa = models.BooleanField(default=False)
    is_sandbox = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['country', 'is_active']),
            models.Index(fields=['type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.country})"


class BankConnection(models.Model):
    """
    Represents a user's connection to a bank (Item in Pluggy).
    Ref: https://docs.pluggy.ai/reference/items-retrieve
    https://docs.pluggy.ai/docs/item-lifecycle
    """
    STATUS_CHOICES = [
        ('UPDATING', 'Updating'),
        ('UPDATED', 'Updated'),
        ('LOGIN_ERROR', 'Login Error'),
        ('WAITING_USER_INPUT', 'Waiting User Input'),
        ('OUTDATED', 'Outdated'),
        ('ERROR', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_connections')
    connector = models.ForeignKey(Connector, on_delete=models.PROTECT, related_name='connections')

    # Pluggy identifiers
    pluggy_item_id = models.CharField(max_length=100, unique=True, db_index=True)

    # Connection status
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='UPDATING')
    status_detail = models.JSONField(null=True, blank=True)  # Error details if any

    # Execution details
    last_updated_at = models.DateTimeField(null=True, blank=True)
    execution_status = models.CharField(max_length=50, blank=True)

    # User consent
    consent_given_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    webhook_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['status', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.connector.name}"


class BankAccount(models.Model):
    """
    Represents a bank account within a connection.
    Ref: https://docs.pluggy.ai/reference/accounts-retrieve
    """
    ACCOUNT_TYPES = [
        ('CHECKING', 'Checking Account'),
        ('SAVINGS', 'Savings Account'),
        ('CREDIT_CARD', 'Credit Card'),
        ('LOAN', 'Loan'),
        ('INVESTMENT', 'Investment'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    connection = models.ForeignKey(BankConnection, on_delete=models.CASCADE, related_name='accounts')

    # Pluggy identifiers
    pluggy_account_id = models.CharField(max_length=100, unique=True, db_index=True)

    # Account details
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    subtype = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=200)
    number = models.CharField(max_length=50, blank=True)  # Account number (masked)

    # Financial data
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    currency_code = models.CharField(max_length=3, default='BRL')

    # Bank details
    bank_data = models.JSONField(default=dict)  # Additional bank-specific data

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['type', 'name']
        indexes = [
            models.Index(fields=['connection', 'is_active']),
            models.Index(fields=['type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Transaction(models.Model):
    """
    Represents a financial transaction.
    Ref: https://docs.pluggy.ai/reference/transactions-list
    """
    TRANSACTION_TYPES = [
        ('DEBIT', 'Debit'),
        ('CREDIT', 'Credit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')

    # Pluggy identifiers
    pluggy_transaction_id = models.CharField(max_length=100, unique=True, db_index=True)

    # Transaction details
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency_code = models.CharField(max_length=3, default='BRL')

    # Dates
    date = models.DateTimeField(db_index=True)  # Transaction date with time from Pluggy

    # Categorization - Pluggy original (reference only)
    pluggy_category = models.CharField(max_length=100, blank=True)
    pluggy_category_id = models.CharField(max_length=50, blank=True)

    # User customizable category
    user_category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )

    # Payment data
    payment_data = models.JSONField(null=True, blank=True)  # Additional payment details
    merchant_name = models.CharField(max_length=200, blank=True)
    merchant_category = models.CharField(max_length=100, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['account', 'date']),
            models.Index(fields=['type', 'date']),
            models.Index(fields=['pluggy_category', 'date']),
            models.Index(fields=['user_category', 'date']),
        ]

    def __str__(self):
        return f"{self.date} - {self.description} ({self.amount})"

    @property
    def is_income(self):
        """Check if transaction is income (credit)."""
        return self.type == 'CREDIT'

    @property
    def is_expense(self):
        """Check if transaction is expense (debit)."""
        return self.type == 'DEBIT'

    @property
    def effective_category(self):
        """Get the effective category (user category if set, otherwise Pluggy category)."""
        if self.user_category:
            return self.user_category.name
        return self.pluggy_category


class Category(models.Model):
    """
    Represents a transaction category.
    """
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    color = models.CharField(max_length=7, default='#d946ef')  # Hex color
    icon = models.CharField(max_length=10, default='📁')  # Emoji icon
    is_system = models.BooleanField(default=False)  # System categories can't be deleted
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'
        unique_together = [['user', 'name', 'type']]
        indexes = [
            models.Index(fields=['user', 'type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class SyncLog(models.Model):
    """
    Logs for synchronization operations.
    """
    SYNC_TYPES = [
        ('CONNECTORS', 'Connectors Sync'),
        ('ACCOUNTS', 'Accounts Sync'),
        ('TRANSACTIONS', 'Transactions Sync'),
        ('FULL', 'Full Sync'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    connection = models.ForeignKey(BankConnection, on_delete=models.CASCADE,
                                  related_name='sync_logs', null=True, blank=True)
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    records_synced = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    details = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.sync_type} - {self.status} at {self.started_at}"