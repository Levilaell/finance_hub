"""
Simplified Companies serializers - Essential functionality only
"""
from rest_framework import serializers
from .models import Company, SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Simple plan serializer"""
    yearly_discount = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'slug',
            'price_monthly', 'price_yearly', 'yearly_discount',
            'max_transactions', 'max_bank_accounts', 'max_ai_requests_per_month',
            'enable_ai_insights', 'has_advanced_reports'
        ]
    
    def get_yearly_discount(self, obj):
        """Calculate yearly discount percentage"""
        if obj.price_monthly == 0:
            return 0
        monthly_total = obj.price_monthly * 12
        discount = monthly_total - obj.price_yearly
        return int((discount / monthly_total) * 100)


class CompanySerializer(serializers.ModelSerializer):
    """Simple company serializer"""
    subscription_plan = SubscriptionPlanSerializer(read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    is_trial_active = serializers.ReadOnlyField()
    days_until_trial_ends = serializers.ReadOnlyField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'owner_email',
            'subscription_plan', 'subscription_status',
            'billing_cycle', 'trial_ends_at',
            'is_trial_active', 'days_until_trial_ends',
            'current_month_transactions', 'current_month_ai_requests',
            'created_at'
        ]
        read_only_fields = [
            'owner_email', 'subscription_status', 'trial_ends_at',
            'current_month_transactions', 'current_month_ai_requests'
        ]


class UsageLimitsSerializer(serializers.Serializer):
    """Usage limits response serializer"""
    transactions = serializers.DictField()
    bank_accounts = serializers.DictField()
    ai_requests = serializers.DictField()


class SubscriptionStatusSerializer(serializers.Serializer):
    """Subscription status response"""
    subscription_status = serializers.CharField()
    plan = SubscriptionPlanSerializer(allow_null=True)
    trial_days_left = serializers.IntegerField()
    trial_ends_at = serializers.DateTimeField(allow_null=True)
    requires_payment_setup = serializers.BooleanField()
    has_payment_method = serializers.BooleanField()