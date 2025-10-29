"""
Serializers for Banking API.
Ref: https://www.django-rest-framework.org/api-guide/serializers/
"""

from rest_framework import serializers
from .models import (
    Connector, BankConnection, BankAccount,
    Transaction, SyncLog, Category, Bill
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

    class Meta:
        model = Transaction
        fields = [
            'id', 'account_name', 'account_type',
            'type', 'description', 'amount', 'currency_code',
            'date', 'category', 'user_category_id', 'pluggy_category',
            'merchant_name', 'is_income', 'is_expense', 'created_at'
        ]
        read_only_fields = ['id', 'pluggy_category', 'pluggy_category_id', 'created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for user_category based on request user
        if 'request' in self.context:
            user = self.context['request'].user
            self.fields['user_category_id'].queryset = Category.objects.filter(user=user)


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

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'type', 'color', 'icon',
            'is_system', 'parent', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_system', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate that user doesn't create duplicate categories."""
        user = self.context['request'].user
        name = data.get('name')
        type_value = data.get('type')

        # Check for duplicates (excluding current instance on updates)
        queryset = Category.objects.filter(user=user, name=name, type=type_value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError({
                'name': f'Category "{name}" already exists for {type_value}'
            })

        return data


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

    class Meta:
        model = Bill
        fields = [
            'id', 'type', 'description', 'amount', 'amount_paid',
            'amount_remaining', 'payment_percentage', 'currency_code',
            'due_date', 'paid_at', 'status', 'is_overdue',
            'category', 'category_name', 'category_color', 'category_icon',
            'recurrence', 'parent_bill', 'installment_number',
            'customer_supplier', 'notes', 'linked_transaction',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'is_overdue', 'amount_remaining', 'payment_percentage',
            'category_name', 'category_color', 'category_icon',
            'created_at', 'updated_at'
        ]

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