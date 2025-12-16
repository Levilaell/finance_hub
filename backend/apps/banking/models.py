"""
Banking models for Pluggy integration.
Ref: https://docs.pluggy.ai/docs/data-structure
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
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

    # Credit card fields
    available_credit_limit = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text='Available credit limit for credit cards'
    )
    credit_limit = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text='Total credit limit for credit cards'
    )
    credit_data = models.JSONField(
        default=dict, blank=True,
        help_text='Additional credit card data from Pluggy'
    )

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


class Bill(models.Model):
    """
    Represents accounts payable and receivable.
    These are bills/invoices that are not yet reflected in bank transactions.
    """
    TYPE_CHOICES = [
        ('payable', 'A Pagar'),
        ('receivable', 'A Receber'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('partially_paid', 'Parcialmente Pago'),
        ('paid', 'Pago'),
        ('cancelled', 'Cancelado'),
    ]

    RECURRENCE_CHOICES = [
        ('once', 'Uma vez'),
        ('monthly', 'Mensal'),
        ('weekly', 'Semanal'),
        ('yearly', 'Anual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bills')

    # Bill details
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    currency_code = models.CharField(max_length=3, default='BRL')

    # Dates
    due_date = models.DateField(db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bills'
    )

    # Recurrence
    recurrence = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='once')
    parent_bill = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='installments',
        help_text='For recurring bills, links to the original bill'
    )
    installment_number = models.IntegerField(
        null=True,
        blank=True,
        help_text='Installment number for recurring bills'
    )

    # Customer/Supplier
    customer_supplier = models.CharField(
        max_length=200,
        blank=True,
        help_text='Name of customer (for receivables) or supplier (for payables)'
    )

    # Notes
    notes = models.TextField(blank=True)

    # OCR fields (for uploaded boletos)
    source_file = models.FileField(
        upload_to='bills/uploads/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['pdf', 'png', 'jpg', 'jpeg'])],
        help_text='Original boleto file (PDF or image)'
    )
    barcode = models.CharField(
        max_length=100,
        blank=True,
        help_text='Linha digitável do boleto (47-48 dígitos)'
    )
    ocr_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text='OCR confidence score (0-100)'
    )
    ocr_raw_data = models.JSONField(
        null=True,
        blank=True,
        help_text='Raw OCR extraction data'
    )
    created_from_ocr = models.BooleanField(
        default=False,
        help_text='Whether this bill was created from OCR upload'
    )

    # Link to bank transaction (when paid through bank)
    # OneToOneField garante que uma transação só pode estar vinculada a uma bill
    linked_transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_bill'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'type', 'status']),
            models.Index(fields=['user', 'due_date']),
            models.Index(fields=['status', 'due_date']),
        ]

    def __str__(self):
        return f"{self.get_type_display()} - {self.description} ({self.amount})"

    @property
    def is_overdue(self):
        """Check if bill is overdue."""
        if self.status in ['paid', 'cancelled']:
            return False
        return timezone.now().date() > self.due_date

    @property
    def amount_remaining(self):
        """Calculate remaining amount to be paid."""
        return self.amount - self.amount_paid

    @property
    def payment_percentage(self):
        """Calculate payment percentage."""
        if self.amount == 0:
            return 0
        return (self.amount_paid / self.amount) * 100

    def update_status(self):
        """Update status based on amount_paid."""
        if self.amount_paid >= self.amount:
            self.status = 'paid'
            if not self.paid_at:
                self.paid_at = timezone.now()
        elif self.amount_paid > 0:
            self.status = 'partially_paid'
        else:
            self.status = 'pending'
        self.save()

    def recalculate_payments(self):
        """
        Recalcula amount_paid a partir de todos os BillPayments.
        Deve ser chamado após adicionar/remover pagamentos.
        """
        from django.db.models import Sum
        total = self.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        self.amount_paid = total
        self.update_status()

    @property
    def can_add_payment(self):
        """Verifica se a bill pode receber mais pagamentos."""
        return self.status not in ['paid', 'cancelled'] and self.amount_remaining > 0


class BillPayment(models.Model):
    """
    Representa um pagamento individual de uma conta (Bill).
    Permite vincular múltiplas transações a uma única bill (pagamentos rateados).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    # Detalhes do pagamento
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    # Transação vinculada (opcional - pagamento pode ser manual)
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bill_payment'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']
        indexes = [
            models.Index(fields=['bill', 'payment_date']),
        ]

    def __str__(self):
        tx_info = f" (Tx: {self.transaction.description[:20]})" if self.transaction else " (Manual)"
        return f"Pagamento de {self.amount} para {self.bill.description[:30]}{tx_info}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalcula os totais da bill após salvar
        self.bill.recalculate_payments()

    def delete(self, *args, **kwargs):
        bill = self.bill
        super().delete(*args, **kwargs)
        # Recalcula os totais da bill após deletar
        bill.recalculate_payments()


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


class CategoryRule(models.Model):
    """
    Regra de categorização automática baseada em padrão de transação.
    Permite aplicar automaticamente categorias a transações que matcham
    um padrão específico (por prefixo, conteúdo ou similaridade fuzzy).
    """
    MATCH_TYPE_CHOICES = [
        ('prefix', 'Prefixo'),
        ('contains', 'Contém'),
        ('fuzzy', 'Similaridade'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='category_rules')

    # Padrão de matching (normalizado: sem acentos, lowercase)
    pattern = models.CharField(max_length=200)
    match_type = models.CharField(max_length=20, choices=MATCH_TYPE_CHOICES, default='prefix')

    # Categoria a aplicar quando houver match
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='rules')

    # Status e métricas
    is_active = models.BooleanField(default=True)
    applied_count = models.IntegerField(default=0)  # Quantas vezes foi aplicada

    # Rastreabilidade
    created_from_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_rules',
        help_text='Transação que originou a criação desta regra'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Category Rule'
        verbose_name_plural = 'Category Rules'
        unique_together = [['user', 'pattern', 'match_type']]
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.get_match_type_display()}: '{self.pattern}' → {self.category.name}"
