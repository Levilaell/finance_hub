from rest_framework import serializers
from .models import Subscription, PaymentMethod, Payment, UsageRecord
from apps.companies.models import SubscriptionPlan
from apps.companies.models import Company


class SubscriptionSerializer(serializers.ModelSerializer):
    """Company subscription status"""
    plan = serializers.StringRelatedField(read_only=True)
    is_active = serializers.ReadOnlyField()
    is_trial = serializers.ReadOnlyField()
    trial_days_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'status', 'billing_period',
            'is_active', 'is_trial', 'trial_days_remaining',
            'trial_ends_at', 'current_period_start', 'current_period_end',
            'cancelled_at', 'created_at'
        ]


class CreateCheckoutSessionSerializer(serializers.Serializer):
    """Create payment checkout session"""
    plan_id = serializers.IntegerField()
    billing_period = serializers.ChoiceField(choices=['monthly', 'yearly'])
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()
    
    def validate_plan_id(self, value):
        try:
            SubscriptionPlan.objects.get(id=value, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid plan selected")
        return value


class ValidatePaymentSerializer(serializers.Serializer):
    """Validate payment completion"""
    session_id = serializers.CharField()
    
    
class UsageSerializer(serializers.ModelSerializer):
    """Feature usage tracking"""
    limit = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = UsageRecord
        fields = ['type', 'count', 'limit', 'percentage', 'period_start', 'period_end']
    
    def get_limit(self, obj):
        subscription = obj.company.subscription
        if not subscription:
            return 0
            
        limits = {
            'transaction': subscription.plan.max_transactions,
            'bank_account': subscription.plan.max_bank_accounts,
            'ai_request': subscription.plan.max_ai_requests,
        }
        return limits.get(obj.type, 0)
    
    def get_percentage(self, obj):
        limit = self.get_limit(obj)
        if limit == 0:
            return 0
        return min(100, round((obj.count / limit) * 100, 1))


class CompanySubscriptionSerializer(serializers.ModelSerializer):
    """Company with subscription details"""
    subscription = SubscriptionSerializer(read_only=True)
    current_usage = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'subscription', 'current_usage']
    
    def get_current_usage(self, obj):
        usage_types = ['transaction', 'bank_account', 'ai_request']
        usage_data = {}
        
        for usage_type in usage_types:
            record = UsageRecord.get_current_usage(obj, usage_type)
            usage_data[usage_type] = UsageSerializer(record).data
            
        return usage_data