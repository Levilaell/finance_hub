"""
Serializers for Banking API.
Ref: https://www.django-rest-framework.org/api-guide/serializers/
"""

from rest_framework import serializers
from .models import (
    Connector, BankConnection, BankAccount,
    Transaction, SyncLog, Category, Bill, CategoryRule
)


class ConnectorSerializer(serializers.ModelSerializer):
    """Serializer for bank connectors."""

    class Meta:
        model = Connector
        fields = [
            'id', 'pluggy_id', 'name', 'institution_name',
            'institution_url', 'country', 'primary_color',
            'logo_url', 'type', 'credentials_schema',
            'supports_mfa', 'is_sandbox', 'is_active'
        ]
        read_only_fields = ['id', 'pluggy_id']


class BankAccountSerializer(serializers.ModelSerializer):
    """Serializer for bank accounts."""
    connection_id = serializers.UUIDField(source='connection.id', read_only=True)
    institution_name = serializers.CharField(source='connection.connector.institution_name', read_only=True)
    is_credit_card = serializers.SerializerMethodField()

    class Meta:
        model = BankAccount
        fields = [
            'id', 'connection_id', 'institution_name',
            'type', 'subtype', 'name', 'number',
            'balance', 'currency_code',
            'is_credit_card', 'available_credit_limit', 'credit_limit', 'credit_data',
            'last_synced_at', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'connection_id', 'institution_name', 'is_credit_card',
            'last_synced_at', 'created_at', 'updated_at'
        ]

    def get_is_credit_card(self, obj):
        """Check if account is a credit card."""
        return obj.type == 'CREDIT_CARD'


class BankConnectionSerializer(serializers.ModelSerializer):
    """Serializer for bank connections."""
    connector = ConnectorSerializer(read_only=True)
    accounts = BankAccountSerializer(many=True, read_only=True)
    connector_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = BankConnection
        fields = [
            'id', 'connector', 'connector_id', 'accounts',
            'status', 'status_detail', 'last_updated_at',
            'execution_status', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'status_detail', 'last_updated_at',
            'execution_status', 'created_at', 'updated_at'
        ]


class CreateConnectionSerializer(serializers.Serializer):
    """Serializer for creating a bank connection."""
    connector_id = serializers.IntegerField(required=True)
    credentials = serializers.DictField(
        child=serializers.CharField(),
        required=True,
        help_text="Credentials required by the connector"
    )

    def validate_connector_id(self, value):
        """Validate that connector exists."""
        if not Connector.objects.filter(pluggy_id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive connector.")
        return value


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transactions."""
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_type = serializers.CharField(source='account.type', read_only=True)
    is_income = serializers.BooleanField(read_only=True)
    is_expense = serializers.BooleanField(read_only=True)

    # Category information
    category = serializers.CharField(source='effective_category', read_only=True)
    user_category_id = serializers.PrimaryKeyRelatedField(
        source='user_category',
        queryset=Category.objects.none(),
        required=False,
        allow_null=True
    )

    # Linked bill information
    linked_bill = serializers.SerializerMethodField()
    has_linked_bill = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'account_name', 'account_type',
            'type', 'description', 'amount', 'currency_code',
            'date', 'category', 'user_category_id', 'pluggy_category',
            'merchant_name', 'is_income', 'is_expense', 'created_at',
            'linked_bill', 'has_linked_bill'
        ]
        read_only_fields = ['id', 'pluggy_category', 'pluggy_category_id', 'created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for user_category based on request user
        if 'request' in self.context:
            user = self.context['request'].user
            self.fields['user_category_id'].queryset = Category.objects.filter(user=user)

    def get_linked_bill(self, obj):
        """Get linked bill info if exists."""
        if hasattr(obj, 'linked_bill') and obj.linked_bill:
            bill = obj.linked_bill
            return {
                'id': str(bill.id),
                'description': bill.description,
                'amount': str(bill.amount),
                'due_date': bill.due_date.isoformat(),
                'type': bill.type
            }
        return None

    def get_has_linked_bill(self, obj):
        """Check if transaction has linked bill."""
        return hasattr(obj, 'linked_bill') and obj.linked_bill is not None


class TransactionFilterSerializer(serializers.Serializer):
    """Serializer for transaction filters."""
    account_id = serializers.UUIDField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    type = serializers.ChoiceField(choices=['CREDIT', 'DEBIT'], required=False)
    category = serializers.CharField(required=False)


class SyncStatusSerializer(serializers.ModelSerializer):
    """Serializer for sync logs."""
    connection_name = serializers.SerializerMethodField()

    class Meta:
        model = SyncLog
        fields = [
            'id', 'connection_name', 'sync_type', 'status',
            'started_at', 'completed_at', 'records_synced',
            'error_message'
        ]

    def get_connection_name(self, obj):
        if obj.connection:
            return f"{obj.connection.connector.name}"
        return "System"


class ConnectTokenSerializer(serializers.Serializer):
    """Serializer for connect token response."""
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()


class SummarySerializer(serializers.Serializer):
    """Serializer for financial summary."""
    income = serializers.DecimalField(max_digits=15, decimal_places=2)
    expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    accounts_count = serializers.IntegerField()
    transactions_count = serializers.IntegerField()


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for categories."""
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'type', 'color', 'icon',
            'is_system', 'parent', 'subcategories', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_system', 'created_at', 'updated_at']

    def get_subcategories(self, obj):
        """Return subcategories only for parent categories."""
        if obj.parent is None:
            children = obj.subcategories.all()
            if children.exists():
                return CategoryChildSerializer(children, many=True).data
        return []

    def validate(self, data):
        """Validate category data including parent constraints."""
        user = self.context['request'].user
        name = data.get('name')
        type_value = data.get('type') or (self.instance.type if self.instance else None)
        parent = data.get('parent')

        # Validate parent constraints
        if parent:
            # 1. Parent must belong to the same user
            if parent.user != user:
                raise serializers.ValidationError({
                    'parent': 'Categoria pai inválida'
                })

            # 2. Parent must be of the same type
            if parent.type != type_value:
                raise serializers.ValidationError({
                    'parent': 'Categoria pai deve ser do mesmo tipo (receita/despesa)'
                })

            # 3. Parent cannot have a parent (max 2 levels)
            if parent.parent is not None:
                raise serializers.ValidationError({
                    'parent': 'Não é permitido criar subcategoria de subcategoria'
                })

        # Check for duplicates (excluding current instance on updates)
        queryset = Category.objects.filter(user=user, name=name, type=type_value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError({
                'name': f'Category "{name}" already exists for {type_value}'
            })

        return data


class CategoryChildSerializer(serializers.ModelSerializer):
    """Simplified serializer for subcategories (no nested children)."""

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'type', 'color', 'icon',
            'is_system', 'parent', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_system', 'created_at', 'updated_at']


class BillSerializer(serializers.ModelSerializer):
    """Serializer for bills (accounts payable/receivable)."""
    is_overdue = serializers.BooleanField(read_only=True)
    amount_remaining = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    payment_percentage = serializers.FloatField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)

    # Linked transaction information (legacy)
    linked_transaction_details = serializers.SerializerMethodField()
    has_linked_transaction = serializers.SerializerMethodField()

    # Payments (novo sistema de pagamentos parciais)
    payments = serializers.SerializerMethodField()
    payments_count = serializers.SerializerMethodField()
    can_add_payment = serializers.BooleanField(read_only=True)

    class Meta:
        model = Bill
        fields = [
            'id', 'type', 'description', 'amount', 'amount_paid',
            'amount_remaining', 'payment_percentage', 'currency_code',
            'due_date', 'paid_at', 'status', 'is_overdue',
            'category', 'category_name', 'category_color', 'category_icon',
            'recurrence', 'parent_bill', 'installment_number',
            'customer_supplier', 'notes', 'linked_transaction',
            'linked_transaction_details', 'has_linked_transaction',
            'payments', 'payments_count', 'can_add_payment',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'is_overdue', 'amount_remaining', 'payment_percentage',
            'category_name', 'category_color', 'category_icon',
            'linked_transaction_details', 'has_linked_transaction',
            'payments', 'payments_count', 'can_add_payment',
            'created_at', 'updated_at'
        ]

    def get_linked_transaction_details(self, obj):
        """Get linked transaction info if exists (legacy)."""
        if obj.linked_transaction:
            tx = obj.linked_transaction
            return {
                'id': str(tx.id),
                'description': tx.description,
                'amount': str(tx.amount),
                'date': tx.date.isoformat(),
                'account_name': tx.account.name if tx.account else None
            }
        return None

    def get_has_linked_transaction(self, obj):
        """
        Check if bill has linked transaction.
        Verifica AMBOS: campo legacy E BillPayments com transação.
        """
        # Legacy check
        if obj.linked_transaction is not None:
            return True
        # Novo sistema: verifica se há payments com transação
        return obj.payments.filter(transaction__isnull=False).exists()

    def get_payments(self, obj):
        """Retorna lista de pagamentos da bill."""
        from .serializers import BillPaymentSerializer
        payments = obj.payments.select_related('transaction', 'transaction__account').all()
        return BillPaymentSerializer(payments, many=True).data

    def get_payments_count(self, obj):
        """Retorna contagem de pagamentos."""
        return obj.payments.count()

    def validate(self, data):
        """Validate bill data."""
        # Ensure amount_paid doesn't exceed amount
        amount = data.get('amount', getattr(self.instance, 'amount', 0))
        amount_paid = data.get('amount_paid', getattr(self.instance, 'amount_paid', 0))

        if amount_paid > amount:
            raise serializers.ValidationError({
                'amount_paid': 'Amount paid cannot exceed total amount'
            })

        # Validate category type matches bill type
        category = data.get('category')
        bill_type = data.get('type', getattr(self.instance, 'type', None))

        if category and bill_type:
            expected_category_type = 'income' if bill_type == 'receivable' else 'expense'
            if category.type != expected_category_type:
                raise serializers.ValidationError({
                    'category': f'Category type must be {expected_category_type} for {bill_type} bills'
                })

        return data


class BillFilterSerializer(serializers.Serializer):
    """Serializer for bill filters."""
    type = serializers.ChoiceField(choices=['payable', 'receivable'], required=False)
    status = serializers.ChoiceField(
        choices=['pending', 'partially_paid', 'paid', 'cancelled'],
        required=False
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    category = serializers.UUIDField(required=False)
    is_overdue = serializers.BooleanField(required=False)


class RegisterPaymentSerializer(serializers.Serializer):
    """Serializer for registering bill payment."""
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_amount(self, value):
        """Validate payment amount."""
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero")
        return value


class BillsSummarySerializer(serializers.Serializer):
    """Serializer for bills summary."""
    total_receivable = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_receivable_month = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_payable = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_payable_month = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_overdue = serializers.DecimalField(max_digits=15, decimal_places=2)
    overdue_count = serializers.IntegerField()
    receivable_count = serializers.IntegerField()
    payable_count = serializers.IntegerField()


# ============================================================
# Transaction-Bill Linking Serializers
# ============================================================

class LinkTransactionSerializer(serializers.Serializer):
    """Serializer for linking a transaction to a bill."""
    transaction_id = serializers.UUIDField(required=True)

    def validate_transaction_id(self, value):
        """Validate that transaction exists and belongs to user."""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context required")

        try:
            transaction = Transaction.objects.get(
                id=value,
                account__connection__user=request.user,
                account__connection__is_active=True
            )
        except Transaction.DoesNotExist:
            raise serializers.ValidationError("Transaction not found")

        # Check if already linked
        if hasattr(transaction, 'linked_bill') and transaction.linked_bill:
            raise serializers.ValidationError("Transaction is already linked to another bill")

        return value


class LinkBillSerializer(serializers.Serializer):
    """Serializer for linking a bill to a transaction."""
    bill_id = serializers.UUIDField(required=True)

    def validate_bill_id(self, value):
        """Validate that bill exists and belongs to user."""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context required")

        try:
            bill = Bill.objects.get(id=value, user=request.user)
        except Bill.DoesNotExist:
            raise serializers.ValidationError("Bill not found")

        # Check eligibility
        if bill.status != 'pending':
            raise serializers.ValidationError(f"Bill must be pending. Current status: {bill.status}")

        if bill.amount_paid > 0:
            raise serializers.ValidationError("Bill already has prior payments")

        if bill.linked_transaction is not None:
            raise serializers.ValidationError("Bill is already linked to another transaction")

        return value


class TransactionSuggestionSerializer(serializers.ModelSerializer):
    """Serializer for transaction suggestions (for linking to bills)."""
    account_name = serializers.CharField(source='account.name', read_only=True)
    relevance_score = serializers.IntegerField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'description', 'amount', 'date', 'type',
            'account_name', 'merchant_name', 'relevance_score'
        ]


class BillSuggestionSerializer(serializers.ModelSerializer):
    """Serializer for bill suggestions (for linking to transactions)."""
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True, allow_null=True)
    relevance_score = serializers.IntegerField(read_only=True)

    class Meta:
        model = Bill
        fields = [
            'id', 'description', 'amount', 'due_date', 'type',
            'customer_supplier', 'category_name', 'category_icon',
            'relevance_score'
        ]


class LinkedTransactionSerializer(serializers.ModelSerializer):
    """Serializer for linked transaction info (embedded in Bill)."""
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'description', 'amount', 'date', 'account_name']


class LinkedBillSerializer(serializers.ModelSerializer):
    """Serializer for linked bill info (embedded in Transaction)."""

    class Meta:
        model = Bill
        fields = ['id', 'description', 'amount', 'due_date', 'type']


class AutoMatchResultSerializer(serializers.Serializer):
    """Serializer for auto-match results after sync."""

    class MatchedItemSerializer(serializers.Serializer):
        transaction_id = serializers.UUIDField()
        transaction_description = serializers.CharField()
        bill_id = serializers.UUIDField()
        bill_description = serializers.CharField()
        amount = serializers.DecimalField(max_digits=15, decimal_places=2)

    class AmbiguousItemSerializer(serializers.Serializer):
        transaction_id = serializers.UUIDField()
        transaction_description = serializers.CharField()
        amount = serializers.DecimalField(max_digits=15, decimal_places=2)
        matching_bills_count = serializers.IntegerField()

    matched = MatchedItemSerializer(many=True)
    ambiguous = AmbiguousItemSerializer(many=True)
    matched_count = serializers.IntegerField()
    ambiguous_count = serializers.IntegerField()


class UserSettingsSerializer(serializers.Serializer):
    """Serializer for user settings."""
    auto_match_transactions = serializers.BooleanField(required=False)

    def update(self, instance, validated_data):
        """Update user settings."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ============================================================
# BillPayment Serializers (Pagamentos Parciais)
# ============================================================

class BillPaymentSerializer(serializers.ModelSerializer):
    """Serializer para pagamentos individuais de uma bill."""
    transaction_details = serializers.SerializerMethodField()
    has_transaction = serializers.SerializerMethodField()

    class Meta:
        from .models import BillPayment
        model = BillPayment
        fields = [
            'id', 'amount', 'payment_date', 'notes',
            'transaction', 'transaction_details', 'has_transaction',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'transaction_details', 'has_transaction', 'created_at', 'updated_at']

    def get_transaction_details(self, obj):
        """Retorna detalhes da transação vinculada."""
        if obj.transaction:
            return {
                'id': str(obj.transaction.id),
                'description': obj.transaction.description,
                'amount': str(obj.transaction.amount),
                'date': obj.transaction.date.isoformat(),
                'account_name': obj.transaction.account.name if obj.transaction.account else None
            }
        return None

    def get_has_transaction(self, obj):
        """Indica se o pagamento tem transação vinculada."""
        return obj.transaction is not None


class BillPaymentCreateSerializer(serializers.Serializer):
    """Serializer para criar um pagamento com ou sem transação vinculada."""
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    transaction_id = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_amount(self, value):
        """Valida que o valor é positivo."""
        if value <= 0:
            raise serializers.ValidationError("Valor deve ser maior que zero")
        return value

    def validate_transaction_id(self, value):
        """Valida que a transação existe e não está vinculada."""
        if value is None:
            return None

        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context required")

        try:
            transaction = Transaction.objects.get(
                id=value,
                account__connection__user=request.user,
                account__connection__is_active=True
            )
        except Transaction.DoesNotExist:
            raise serializers.ValidationError("Transação não encontrada")

        # Verifica se já está vinculada via BillPayment
        from .models import BillPayment
        if BillPayment.objects.filter(transaction=transaction).exists():
            raise serializers.ValidationError("Transação já está vinculada a outra conta")

        # Verifica se está vinculada via legacy
        if hasattr(transaction, 'linked_bill') and transaction.linked_bill:
            raise serializers.ValidationError("Transação já está vinculada (legacy) a outra conta")

        return value

    def validate(self, data):
        """Validação geral."""
        bill = self.context.get('bill')
        if not bill:
            raise serializers.ValidationError("Bill context required")

        # Valida que o valor não excede o restante
        if data['amount'] > bill.amount_remaining:
            raise serializers.ValidationError({
                'amount': f"Valor excede o restante ({bill.amount_remaining})"
            })

        # Se tem transação, o valor deve ser igual ao da transação
        if data.get('transaction_id'):
            transaction = Transaction.objects.get(id=data['transaction_id'])
            if transaction.amount != data['amount']:
                raise serializers.ValidationError({
                    'amount': f"Valor deve ser igual ao da transação ({transaction.amount})"
                })

        return data


class PartialPaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer para sugestões de transações para pagamento parcial."""
    account_name = serializers.CharField(source='account.name', read_only=True)
    relevance_score = serializers.IntegerField(read_only=True)
    would_complete_bill = serializers.BooleanField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'description', 'amount', 'date', 'type',
            'account_name', 'merchant_name', 'relevance_score',
            'would_complete_bill'
        ]


# ============================================================
# OCR Upload Serializers
# ============================================================

class BillUploadSerializer(serializers.Serializer):
    """Serializer for validating boleto file upload."""
    file = serializers.FileField(required=True)

    ALLOWED_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg']
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    def validate_file(self, value):
        """Validate file extension and size."""
        # Check file extension
        file_ext = value.name.lower().split('.')[-1] if '.' in value.name else ''
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Formato não suportado. Use: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        # Check file size
        if value.size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            raise serializers.ValidationError(
                f"Arquivo muito grande. Máximo: {max_mb:.0f}MB"
            )

        return value


class BillOCRResultSerializer(serializers.Serializer):
    """Serializer for OCR processing result."""
    success = serializers.BooleanField()
    barcode = serializers.CharField(allow_blank=True)
    amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, allow_null=True
    )
    due_date = serializers.DateField(allow_null=True)
    beneficiary = serializers.CharField(allow_blank=True)
    confidence = serializers.FloatField()
    needs_review = serializers.BooleanField()
    extracted_fields = serializers.DictField(required=False)
    error = serializers.CharField(allow_blank=True)


class BillFromOCRSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a Bill from OCR results.
    Used after user reviews and confirms OCR data.
    """
    # OCR-specific fields
    barcode = serializers.CharField(max_length=100, required=False, allow_blank=True)
    ocr_confidence = serializers.FloatField(required=False, allow_null=True)
    ocr_raw_data = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = Bill
        fields = [
            'type', 'description', 'amount', 'due_date',
            'customer_supplier', 'category', 'notes',
            'barcode', 'ocr_confidence', 'ocr_raw_data'
        ]

    def create(self, validated_data):
        """Create bill with OCR flag set."""
        validated_data['created_from_ocr'] = True
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# ============================================================
# Category Rule Serializers
# ============================================================

class CategoryRuleSerializer(serializers.ModelSerializer):
    """Serializer for category rules."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    match_type_display = serializers.CharField(source='get_match_type_display', read_only=True)

    class Meta:
        model = CategoryRule
        fields = [
            'id', 'pattern', 'match_type', 'match_type_display',
            'category', 'category_name', 'category_color', 'category_icon',
            'is_active', 'applied_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'applied_count', 'created_at', 'updated_at']

    def validate_pattern(self, value):
        """Validate pattern minimum length."""
        if len(value) < 3:
            raise serializers.ValidationError("Padrão deve ter pelo menos 3 caracteres")
        return value

    def validate_category(self, value):
        """Ensure category belongs to the user."""
        request = self.context.get('request')
        if request and value.user != request.user:
            raise serializers.ValidationError("Categoria inválida")
        return value


class SimilarTransactionSerializer(serializers.Serializer):
    """Serializer for similar transactions response."""
    id = serializers.UUIDField()
    description = serializers.CharField()
    merchant_name = serializers.CharField(allow_blank=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    date = serializers.DateTimeField()
    match_type = serializers.CharField()
    score = serializers.FloatField()


class SimilarTransactionsResponseSerializer(serializers.Serializer):
    """Response serializer for GET /transactions/{id}/similar/"""
    count = serializers.IntegerField()
    transactions = SimilarTransactionSerializer(many=True)
    suggested_pattern = serializers.CharField()
    suggested_match_type = serializers.CharField()


class CategoryUpdateWithRuleSerializer(serializers.Serializer):
    """
    Serializer for PATCH /transactions/{id}/ with rule creation support.
    Extends the normal category update with batch operations.
    """
    user_category_id = serializers.UUIDField(required=False, allow_null=True)
    apply_to_similar = serializers.BooleanField(default=False)
    create_rule = serializers.BooleanField(default=False)
    similar_transaction_ids = serializers.ListField(
        child=serializers.UUIDField(),
        default=list,
        required=False
    )