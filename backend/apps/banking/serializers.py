"""
Banking app serializers
Data serialization for financial models
"""
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import (BankAccount, BankProvider, BankSync, Budget, Transaction, TransactionCategory)


class BankProviderSerializer(serializers.ModelSerializer):
    """
    Bank provider serializer for connection options
    """
    class Meta:
        model = BankProvider
        fields = [
            'id', 'name', 'code', 'logo', 'color',
            'is_open_banking', 'supports_pix', 'supports_ted'
        ]


class BankAccountSerializer(serializers.ModelSerializer):
    """
    Bank account serializer with balance and status info
    """
    bank_provider = BankProviderSerializer(read_only=True)
    bank_provider_id = serializers.IntegerField(write_only=True)
    masked_account = serializers.ReadOnlyField()
    display_name = serializers.ReadOnlyField()
    account_name = serializers.ReadOnlyField(source='display_name')  # Alias for frontend compatibility
    last_sync_status = serializers.SerializerMethodField()
    transaction_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BankAccount
        fields = [
            'id', 'bank_provider', 'bank_provider_id', 'account_type', 'agency', 
            'account_number', 'account_digit', 'masked_account', 'display_name',
            'account_name', 'current_balance', 'available_balance', 'nickname',
            'is_primary', 'is_active', 'status', 'last_sync_at',
            'last_sync_status', 'transaction_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'current_balance', 'available_balance', 'last_sync_at',
            'status', 'masked_account', 'display_name', 'account_name', 'created_at', 'updated_at'
        ]
    
    def get_last_sync_status(self, obj):
        """Get last sync status"""
        last_sync = obj.sync_logs.first()
        if last_sync:
            return {
                'status': last_sync.status,
                'started_at': last_sync.started_at,
                'transactions_new': last_sync.transactions_new
            }
        return None
    
    def get_transaction_count(self, obj):
        """Get total transaction count for this account"""
        return obj.transactions.count()


class TransactionCategorySerializer(serializers.ModelSerializer):
    """
    Transaction category serializer with hierarchy
    """
    full_name = serializers.ReadOnlyField()
    subcategories = serializers.SerializerMethodField()
    transaction_count = serializers.SerializerMethodField()
    slug = serializers.SlugField(read_only=True)
    
    class Meta:
        model = TransactionCategory
        fields = [
            'id', 'name', 'slug', 'category_type', 'parent',
            'icon', 'color', 'full_name', 'subcategories',
            'transaction_count', 'is_system', 'is_active'
        ]
    
    def get_subcategories(self, obj):
        """Get subcategories if any"""
        if obj.subcategories.exists():
            return TransactionCategorySerializer(
                obj.subcategories.filter(is_active=True), 
                many=True
            ).data
        return []
    
    def get_transaction_count(self, obj):
        """Get transaction count for this category"""
        request = self.context.get('request')
        if request and hasattr(request.user, 'company'):
            return obj.transactions.filter(
                bank_account__company=request.user.company
            ).count()
        return 0


class TransactionSerializer(serializers.ModelSerializer):
    """
    Transaction serializer with categorization and formatting
    """
    bank_account_name = serializers.CharField(source='bank_account.display_name', read_only=True)
    account_name = serializers.CharField(source='bank_account.display_name', read_only=True)  # Alias for frontend compatibility
    category_detail = serializers.SerializerMethodField()  # Full category object for frontend
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    formatted_amount = serializers.ReadOnlyField()
    amount_with_sign = serializers.ReadOnlyField()
    is_income = serializers.ReadOnlyField()
    is_expense = serializers.ReadOnlyField()
    external_id = serializers.CharField(read_only=True)  # Add external_id
    
    def get_category_detail(self, obj):
        """Return full category object for frontend compatibility"""
        if obj.category:
            return {
                'id': str(obj.category.id),
                'name': obj.category.name,
                'color': obj.category.color,
                'icon': obj.category.icon
            }
        return None
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'bank_account', 'bank_account_name', 'account_name', 'transaction_type',
            'amount', 'formatted_amount', 'amount_with_sign', 'description',
            'transaction_date', 'posted_date', 'counterpart_name', 'counterpart_document',
            'category', 'category_detail', 'category_name', 'category_icon', 'subcategory',
            'subcategory_name', 'reference_number', 'pix_key', 'notes',
            'tags', 'status', 'is_income', 'is_expense', 'is_reconciled',
            'created_at', 'updated_at', 'external_id'
        ]
        read_only_fields = [
            'formatted_amount',
            'amount_with_sign', 'is_income', 'is_expense', 'bank_account_name',
            'account_name', 'category_detail', 'category_name', 'category_icon', 'subcategory_name',
            'external_id'
        ]
    
    def update(self, instance, validated_data):
        """Update transaction and mark as manually reviewed"""
        # Campo is_manually_reviewed removido - categorização automática via Pluggy
        return super().update(instance, validated_data)


class BankSyncSerializer(serializers.ModelSerializer):
    """
    Bank synchronization log serializer
    """
    bank_account_name = serializers.CharField(source='bank_account.display_name', read_only=True)
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = BankSync
        fields = [
            'id', 'bank_account', 'bank_account_name', 'started_at',
            'completed_at', 'duration', 'status', 'transactions_found',
            'transactions_new', 'transactions_updated', 'error_message',
            'sync_from_date', 'sync_to_date'
        ]


class DashboardSerializer(serializers.Serializer):
    """
    Dashboard data serializer
    """
    current_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    monthly_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    monthly_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    monthly_net = serializers.DecimalField(max_digits=15, decimal_places=2)
    accounts_count = serializers.IntegerField()
    transactions_count = serializers.IntegerField()
    recent_transactions = TransactionSerializer(many=True, read_only=True)
    top_categories = serializers.ListField(child=serializers.DictField())


class TransactionSummarySerializer(serializers.Serializer):
    """
    Transaction summary for reports
    """
    period = serializers.CharField()
    income = serializers.DecimalField(max_digits=15, decimal_places=2)
    expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    net = serializers.DecimalField(max_digits=15, decimal_places=2)
    transaction_count = serializers.IntegerField()
    top_income_categories = serializers.ListField(child=serializers.DictField())
    top_expense_categories = serializers.ListField(child=serializers.DictField())


class CashFlowSerializer(serializers.Serializer):
    """
    Cash flow projection serializer
    """
    date = serializers.DateField()
    projected_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    expected_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    expected_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    confidence_level = serializers.FloatField()
    alerts = serializers.ListField(child=serializers.CharField(), required=False)


class CategoryAnalysisSerializer(serializers.Serializer):
    """
    Category analysis for insights
    """
    category_name = serializers.CharField()
    category_icon = serializers.CharField()
    current_period = serializers.DecimalField(max_digits=15, decimal_places=2)
    previous_period = serializers.DecimalField(max_digits=15, decimal_places=2)
    change_percentage = serializers.FloatField()
    transaction_count = serializers.IntegerField()
    average_amount = serializers.DecimalField(max_digits=15, decimal_places=2)


class BudgetSerializer(serializers.ModelSerializer):
    """
    Budget serializer for expense tracking
    """
    remaining_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    spent_percentage = serializers.FloatField(read_only=True)
    is_exceeded = serializers.BooleanField(read_only=True)
    is_alert_threshold_reached = serializers.BooleanField(read_only=True)
    categories = TransactionCategorySerializer(many=True, read_only=True)
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Budget
        fields = [
            'id', 'name', 'description', 'budget_type', 'amount', 'spent_amount',
            'remaining_amount', 'spent_percentage', 'start_date', 'end_date',
            'alert_threshold', 'is_alert_enabled', 'status', 'is_rollover',
            'categories', 'category_ids', 'is_exceeded', 'is_alert_threshold_reached',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'spent_amount', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        validated_data['company'] = self.context['request'].user.company
        validated_data['created_by'] = self.context['request'].user
        
        budget = Budget.objects.create(**validated_data)
        
        if category_ids:
            budget.categories.set(category_ids)
        
        return budget
    
    def update(self, instance, validated_data):
        category_ids = validated_data.pop('category_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if category_ids is not None:
            instance.categories.set(category_ids)
        
        return instance

'''
class FinancialGoalSerializer(serializers.ModelSerializer):
    """
    Financial goal serializer for goal tracking
    """
    progress_percentage = serializers.FloatField(read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    required_monthly_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    categories = TransactionCategorySerializer(many=True, read_only=True)
    bank_accounts = BankAccountSerializer(many=True, read_only=True)
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    account_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = FinancialGoal
        fields = [
            'id', 'name', 'description', 'goal_type', 'target_amount', 'current_amount',
            'target_date', 'monthly_target', 'progress_percentage', 'remaining_amount',
            'days_remaining', 'required_monthly_amount', 'status', 'is_automatic_tracking',
            'send_reminders', 'reminder_frequency', 'categories', 'bank_accounts',
            'category_ids', 'account_ids', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']
    
    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        account_ids = validated_data.pop('account_ids', [])
        validated_data['company'] = self.context['request'].user.company
        validated_data['created_by'] = self.context['request'].user
        
        goal = FinancialGoal.objects.create(**validated_data)
        
        if category_ids:
            goal.categories.set(category_ids)
        if account_ids:
            goal.bank_accounts.set(account_ids)
        
        return goal
    
    def update(self, instance, validated_data):
        category_ids = validated_data.pop('category_ids', None)
        account_ids = validated_data.pop('account_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if category_ids is not None:
            instance.categories.set(category_ids)
        if account_ids is not None:
            instance.bank_accounts.set(account_ids)
        
        return instance
'''

class TimeSeriesDataSerializer(serializers.Serializer):
    """
    Time series data for charts and analytics
    """
    date = serializers.DateField()
    income = serializers.DecimalField(max_digits=15, decimal_places=2)
    expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_flow = serializers.DecimalField(max_digits=15, decimal_places=2)


class ExpenseTrendSerializer(serializers.Serializer):
    """
    Expense trend analysis data
    """
    period = serializers.CharField()
    category = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    transaction_count = serializers.IntegerField()
    change_from_previous = serializers.DecimalField(max_digits=15, decimal_places=2)
    change_percentage = serializers.FloatField()


class ComparativeAnalysisSerializer(serializers.Serializer):
    """
    Comparative analysis data for dashboard
    """
    current_period = serializers.DecimalField(max_digits=15, decimal_places=2)
    previous_period = serializers.DecimalField(max_digits=15, decimal_places=2)
    variance = serializers.DecimalField(max_digits=15, decimal_places=2)
    variance_percentage = serializers.FloatField()
    trend = serializers.CharField()  # 'up', 'down', 'stable'
    
    
class EnhancedDashboardSerializer(serializers.Serializer):
    """
    Enhanced dashboard data with all features
    """
    # Basic financial data
    current_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    monthly_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    monthly_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    monthly_net = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Transactions
    recent_transactions = TransactionSerializer(many=True)
    transactions_count = serializers.IntegerField()
    
    # Categories
    top_categories = serializers.ListField()
    
    # Accounts
    accounts_count = serializers.IntegerField()
    
    # Budget data
    active_budgets = BudgetSerializer(many=True)
    budgets_summary = serializers.DictField()
    
    # Goals data
    '''
    active_goals = FinancialGoalSerializer(many=True)
    '''
    goals_summary = serializers.DictField()
    
    # Trend data
    monthly_trends = TimeSeriesDataSerializer(many=True)
    expense_trends = ExpenseTrendSerializer(many=True)
    
    # Comparative analysis
    income_comparison = ComparativeAnalysisSerializer()
    expense_comparison = ComparativeAnalysisSerializer()
    
    # Insights
    financial_insights = serializers.ListField()


