"""
Banking app serializers - Pluggy Integration
Following Pluggy's official API structure
"""
from decimal import Decimal
from typing import Dict, Any

from rest_framework import serializers
from django.utils import timezone

from .models import (
    PluggyConnector, PluggyItem, BankAccount, 
    Transaction, TransactionCategory, PluggyCategory
)


class PluggyConnectorSerializer(serializers.ModelSerializer):
    """Serializer for Pluggy connectors"""
    
    class Meta:
        model = PluggyConnector
        fields = [
            'pluggy_id', 'name', 'institution_url', 'image_url',
            'primary_color', 'type', 'country', 'has_mfa', 
            'has_oauth', 'is_open_finance', 'is_sandbox',
            'products', 'credentials'
        ]
        read_only_fields = ['pluggy_id']


class PluggyItemSerializer(serializers.ModelSerializer):
    """Serializer for Pluggy items"""
    connector = PluggyConnectorSerializer(read_only=True)
    accounts_count = serializers.IntegerField(source='accounts.count', read_only=True)
    
    class Meta:
        model = PluggyItem
        fields = [
            'id', 'pluggy_id', 'connector', 'status', 'execution_status',
            'created_at', 'updated_at', 'last_successful_update',
            'error_code', 'error_message', 'status_detail',
            'consent_expires_at', 'accounts_count'
        ]
        read_only_fields = [
            'id', 'pluggy_id', 'status', 'execution_status',
            'created_at', 'updated_at', 'last_successful_update',
            'error_code', 'error_message', 'status_detail'
        ]


class BankAccountSerializer(serializers.ModelSerializer):
    """Serializer for bank accounts"""
    connector = serializers.SerializerMethodField()
    item_status = serializers.CharField(source='item.status', read_only=True)
    display_name = serializers.CharField(read_only=True)
    masked_number = serializers.CharField(read_only=True)
    
    class Meta:
        model = BankAccount
        fields = [
            'id', 'pluggy_id', 'type', 'subtype', 'number', 'name',
            'marketing_name', 'owner', 'balance', 'balance_date',
            'currency_code', 'bank_data', 'credit_data', 'is_active',
            'created_at', 'updated_at', 'connector', 'item_status',
            'display_name', 'masked_number'
        ]
        read_only_fields = [
            'id', 'pluggy_id', 'created_at', 'updated_at',
            'display_name', 'masked_number'
        ]
    
    def get_connector(self, obj):
        """Get connector info for the account"""
        return {
            'id': obj.item.connector.pluggy_id,
            'name': obj.item.connector.name,
            'image_url': obj.item.connector.image_url,
            'primary_color': obj.item.connector.primary_color,
            'is_open_finance': obj.item.connector.is_open_finance
        }


class TransactionCategorySerializer(serializers.ModelSerializer):
    """Serializer for transaction categories"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TransactionCategory
        fields = [
            'id', 'name', 'slug', 'type', 'parent', 'icon', 'color',
            'is_system', 'is_active', 'order', 'full_name'
        ]
        read_only_fields = ['id', 'slug']
    
    def get_full_name(self, obj):
        """Get full category path"""
        if obj.parent:
            return f"{obj.parent.name} > {obj.name}"
        return obj.name


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transactions"""
    account_info = serializers.SerializerMethodField()
    category_detail = TransactionCategorySerializer(source='category', read_only=True)
    amount_display = serializers.CharField(source='get_amount_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'pluggy_id', 'type', 'status', 'description', 'amount',
            'currency_code', 'date', 'merchant', 'payment_data',
            'pluggy_category_id', 'pluggy_category_description',
            'category', 'category_detail', 'operation_type',
            'payment_method', 'credit_card_metadata', 'notes', 'tags',
            'metadata', 'created_at', 'updated_at', 'account_info',
            'amount_display', 'is_income', 'is_expense'
        ]
        read_only_fields = [
            'id', 'pluggy_id', 'created_at', 'updated_at',
            'amount_display', 'is_income', 'is_expense'
        ]
    
    def get_account_info(self, obj):
        """Get basic account info"""
        return {
            'id': obj.account.id,
            'name': obj.account.display_name,
            'type': obj.account.type
        }


class PluggyConnectTokenSerializer(serializers.Serializer):
    """Serializer for Pluggy Connect token request"""
    item_id = serializers.CharField(required=False, allow_blank=True)
    client_user_id = serializers.CharField(required=False)
    webhook_url = serializers.CharField(required=False)
    
    def validate(self, attrs):
        """Validate token request"""
        # If updating, item_id is required
        if self.context.get('updating') and not attrs.get('item_id'):
            raise serializers.ValidationError({
                'item_id': 'Item ID is required for updates'
            })
        return attrs


class PluggyCallbackSerializer(serializers.Serializer):
    """Serializer for Pluggy Connect callback"""
    item_id = serializers.CharField(required=True)
    status = serializers.CharField(required=False)
    error = serializers.CharField(required=False, allow_blank=True)
    
    def validate_item_id(self, value):
        """Validate item ID"""
        if not value:
            raise serializers.ValidationError('Item ID is required')
        return value


class AccountSyncSerializer(serializers.Serializer):
    """Serializer for account sync request"""
    force = serializers.BooleanField(default=False)
    from_date = serializers.DateField(required=False)
    to_date = serializers.DateField(required=False)


class BulkCategorizeSerializer(serializers.Serializer):
    """Serializer for bulk categorization"""
    transaction_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )
    category_id = serializers.UUIDField(required=True)
    
    def validate_category_id(self, value):
        """Validate category exists for the user's company"""
        request = self.context.get('request')
        if request and hasattr(request.user, 'company'):
            if not TransactionCategory.objects.filter(
                id=value,
                company__in=[request.user.company, None]  # Company specific or system
            ).exists():
                raise serializers.ValidationError('Invalid category')
        return value


class TransactionFilterSerializer(serializers.Serializer):
    """Serializer for transaction filters"""
    account_id = serializers.UUIDField(required=False)
    category_id = serializers.UUIDField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    min_amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    max_amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    type = serializers.ChoiceField(choices=['DEBIT', 'CREDIT'], required=False)
    search = serializers.CharField(max_length=200, required=False)
    
    def validate(self, attrs):
        """Validate filters"""
        # Validate date range
        if attrs.get('start_date') and attrs.get('end_date'):
            if attrs['start_date'] > attrs['end_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date'
                })
        
        # Validate amount range
        if attrs.get('min_amount') and attrs.get('max_amount'):
            if attrs['min_amount'] > attrs['max_amount']:
                raise serializers.ValidationError({
                    'max_amount': 'Max amount must be greater than min amount'
                })
        
        return attrs


class DashboardTransactionSerializer(serializers.ModelSerializer):
    """Serializer for dashboard transactions with legacy field names"""
    transaction_date = serializers.DateField(source='date')
    transaction_type = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', allow_null=True, read_only=True)
    category_icon = serializers.CharField(source='category.icon', allow_null=True, read_only=True)
    bank_account_name = serializers.CharField(source='account.display_name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'description', 'amount', 'transaction_date', 
            'transaction_type', 'category_name', 'category_icon', 
            'bank_account_name'
        ]
    
    def get_transaction_type(self, obj):
        """Convert DEBIT/CREDIT to legacy format"""
        if obj.type == 'CREDIT':
            return 'credit'
        elif obj.type == 'DEBIT':
            return 'debit'
        return obj.type.lower()


class DashboardDataSerializer(serializers.Serializer):
    """Serializer for dashboard data"""
    total_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_accounts = serializers.IntegerField()
    active_accounts = serializers.IntegerField()
    
    current_month = serializers.DictField(child=serializers.DecimalField(max_digits=15, decimal_places=2))
    previous_month = serializers.DictField(child=serializers.DecimalField(max_digits=15, decimal_places=2))
    
    recent_transactions = TransactionSerializer(many=True)
    category_breakdown = serializers.ListField(
        child=serializers.DictField()
    )
    
    accounts_summary = serializers.ListField(
        child=serializers.DictField()
    )


class WebhookEventSerializer(serializers.Serializer):
    """Serializer for webhook events"""
    event = serializers.CharField()
    data = serializers.DictField()
    
    def validate_event(self, value):
        """Validate event type"""
        valid_events = [
            'item.created', 'item.updated', 'item.error', 'item.deleted',
            'item.login_succeeded', 'item.waiting_user_input',
            'transactions.created', 'transactions.updated', 'transactions.deleted',
            'consent.created', 'consent.updated', 'consent.revoked'
        ]
        if value not in valid_events:
            raise serializers.ValidationError(f'Invalid event type: {value}')
        return value