"""
Banking serializers for API responses
"""
from rest_framework import serializers
from django.utils import timezone
from .models import (
    PluggyConnector, 
    PluggyItem, 
    BankAccount, 
    Transaction, 
    TransactionCategory,
    ItemWebhook
)


class PluggyConnectorSerializer(serializers.ModelSerializer):
    """Serializer for Pluggy connectors (banks)"""
    
    class Meta:
        model = PluggyConnector
        fields = [
            'id', 'pluggy_id', 'name', 'institution_url', 'image_url',
            'primary_color', 'type', 'country', 'has_mfa', 'has_oauth',
            'is_open_finance', 'is_sandbox', 'products', 'credentials'
        ]
        read_only_fields = ['id', 'pluggy_id']


class PluggyItemSerializer(serializers.ModelSerializer):
    """Serializer for Pluggy items (bank connections)"""
    
    connector_name = serializers.CharField(source='connector.name', read_only=True)
    connector_image_url = serializers.CharField(source='connector.image_url', read_only=True)
    connector_primary_color = serializers.CharField(source='connector.primary_color', read_only=True)
    is_connected = serializers.BooleanField(read_only=True)
    has_error = serializers.BooleanField(read_only=True)
    needs_user_action = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PluggyItem
        fields = [
            'id', 'pluggy_item_id', 'connector', 'connector_name', 
            'connector_image_url', 'connector_primary_color',
            'status', 'execution_status', 'is_connected', 'has_error', 
            'needs_user_action', 'error_message', 'last_successful_update',
            'consent_expires_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'pluggy_item_id', 'status', 'execution_status', 
            'error_message', 'last_successful_update', 'created_at', 'updated_at'
        ]


class BankAccountSerializer(serializers.ModelSerializer):
    """Serializer for bank accounts"""
    
    bank_name = serializers.CharField(read_only=True)
    masked_number = serializers.CharField(read_only=True)
    formatted_balance = serializers.CharField(read_only=True)
    is_credit_card = serializers.BooleanField(read_only=True)
    
    # Item details
    item_id = serializers.CharField(source='item.id', read_only=True)
    item_status = serializers.CharField(source='item.status', read_only=True)
    connector_name = serializers.CharField(source='item.connector.name', read_only=True)
    connector_image_url = serializers.CharField(source='item.connector.image_url', read_only=True)
    
    class Meta:
        model = BankAccount
        fields = [
            'id', 'pluggy_account_id', 'type', 'subtype', 'number', 
            'masked_number', 'name', 'marketing_name', 'owner',
            'balance', 'formatted_balance', 'balance_date', 'currency_code',
            'bank_name', 'is_credit_card', 'is_active',
            'item_id', 'item_status', 'connector_name', 'connector_image_url',
            'bank_data', 'credit_data',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'pluggy_account_id', 'bank_name', 'masked_number',
            'formatted_balance', 'is_credit_card', 'item_id', 'item_status',
            'connector_name', 'connector_image_url', 'created_at', 'updated_at'
        ]


class TransactionCategorySerializer(serializers.ModelSerializer):
    """Serializer for transaction categories"""
    
    transaction_count = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = TransactionCategory
        fields = [
            'id', 'name', 'slug', 'type', 'icon', 'color',
            'is_system', 'is_active', 'order', 'parent',
            'transaction_count', 'subcategories',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_transaction_count(self, obj):
        """Get count of transactions in this category"""
        if hasattr(obj, '_transaction_count'):
            return obj._transaction_count
        return obj.transactions.filter(is_deleted=False).count()
    
    def get_subcategories(self, obj):
        """Get subcategories if this is a parent category"""
        if obj.subcategories.exists():
            return TransactionCategorySerializer(
                obj.subcategories.filter(is_active=True), 
                many=True
            ).data
        return []


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transactions"""
    
    formatted_amount = serializers.CharField(read_only=True)
    is_income = serializers.BooleanField(read_only=True)
    is_expense = serializers.BooleanField(read_only=True)
    
    # Account details
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_number = serializers.CharField(source='account.masked_number', read_only=True)
    bank_name = serializers.CharField(source='account.bank_name', read_only=True)
    
    # Category details
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'pluggy_transaction_id', 'type', 'status',
            'description', 'amount', 'formatted_amount', 'currency_code',
            'date', 'is_income', 'is_expense',
            'account', 'account_name', 'account_number', 'bank_name',
            'category', 'category_name', 'category_icon', 'category_color',
            'pluggy_category_description', 'operation_type', 'payment_method',
            'merchant', 'notes', 'tags',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'pluggy_transaction_id', 'type', 'status', 'description',
            'amount', 'formatted_amount', 'currency_code', 'date',
            'is_income', 'is_expense', 'account_name', 'account_number',
            'bank_name', 'pluggy_category_description', 'operation_type',
            'payment_method', 'merchant', 'created_at', 'updated_at'
        ]


class TransactionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating transactions (category, notes, tags)"""
    
    class Meta:
        model = Transaction
        fields = ['category', 'notes', 'tags']


class ItemWebhookSerializer(serializers.ModelSerializer):
    """Serializer for webhook events"""
    
    class Meta:
        model = ItemWebhook
        fields = [
            'id', 'event_type', 'event_id', 'payload', 'processed',
            'processed_at', 'triggered_by', 'error', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# === CREATE/UPDATE SERIALIZERS ===

class CreateItemSerializer(serializers.Serializer):
    """Serializer for creating a new bank connection"""
    
    connector_id = serializers.IntegerField()
    credentials = serializers.DictField()
    webhook_url = serializers.URLField(required=False)
    products = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    
    def validate_connector_id(self, value):
        """Validate that connector exists"""
        if not PluggyConnector.objects.filter(pluggy_id=value).exists():
            raise serializers.ValidationError("Connector not found")
        return value


class UpdateItemCredentialsSerializer(serializers.Serializer):
    """Serializer for updating item credentials"""
    
    credentials = serializers.DictField()


class CreateCategorySerializer(serializers.ModelSerializer):
    """Serializer for creating transaction categories"""
    
    class Meta:
        model = TransactionCategory
        fields = ['name', 'type', 'icon', 'color', 'parent']
    
    def validate_name(self, value):
        """Validate category name is unique for company"""
        company = self.context['request'].user.company
        if TransactionCategory.objects.filter(
            company=company, 
            name__iexact=value
        ).exists():
            raise serializers.ValidationError("Category with this name already exists")
        return value


# === STATS SERIALIZERS ===

class AccountStatsSerializer(serializers.Serializer):
    """Serializer for account statistics"""
    
    total_accounts = serializers.IntegerField()
    connected_accounts = serializers.IntegerField()
    error_accounts = serializers.IntegerField()
    total_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    last_sync = serializers.DateTimeField()


class TransactionStatsSerializer(serializers.Serializer):
    """Serializer for transaction statistics"""
    
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    total_transactions = serializers.IntegerField()
    total_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Top categories
    top_expense_categories = serializers.ListField()
    top_income_categories = serializers.ListField()
    
    # Monthly breakdown
    monthly_breakdown = serializers.ListField()


class CategoryStatsSerializer(serializers.Serializer):
    """Serializer for category statistics"""
    
    category_id = serializers.UUIDField()
    category_name = serializers.CharField()
    category_icon = serializers.CharField()
    category_color = serializers.CharField()
    transaction_count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


# === DASHBOARD SERIALIZERS ===

class DashboardDataSerializer(serializers.Serializer):
    """Serializer for dashboard data"""
    
    account_stats = AccountStatsSerializer()
    transaction_stats = TransactionStatsSerializer()
    recent_transactions = TransactionSerializer(many=True)
    top_categories = CategoryStatsSerializer(many=True)
    monthly_trends = serializers.ListField()


# === SYNC SERIALIZERS ===

class SyncResultSerializer(serializers.Serializer):
    """Serializer for sync operation results"""
    
    item_id = serializers.CharField()
    status = serializers.CharField()
    accounts_synced = serializers.IntegerField()
    transactions_synced = serializers.IntegerField()
    new_transactions = serializers.IntegerField()
    updated_transactions = serializers.IntegerField()
    errors = serializers.ListField(required=False)
    sync_duration = serializers.FloatField()
    
    
class BulkSyncResultSerializer(serializers.Serializer):
    """Serializer for bulk sync results"""
    
    total_items = serializers.IntegerField()
    successful_syncs = serializers.IntegerField()
    failed_syncs = serializers.IntegerField()
    sync_results = SyncResultSerializer(many=True)
    total_duration = serializers.FloatField()