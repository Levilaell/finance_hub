from rest_framework import serializers
from .models import SubscriptionPlan, Subscription, PaymentMethod, Payment, UsageRecord
from apps.companies.models import Company


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Subscription plan details"""
    monthly_price = serializers.SerializerMethodField()
    yearly_price = serializers.SerializerMethodField()
    yearly_savings = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'display_name',
            'monthly_price', 'yearly_price', 'yearly_savings',
            'max_transactions', 'max_bank_accounts', 'max_ai_requests',
            'features'
        ]
    
    def get_monthly_price(self, obj):
        return float(obj.price_monthly)
    
    def get_yearly_price(self, obj):
        return float(obj.price_yearly)
    
    def get_yearly_savings(self, obj):
        monthly_total = obj.price_monthly * 12
        savings = monthly_total - obj.price_yearly
        return float(savings)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Company subscription status"""
    plan = SubscriptionPlanSerializer(read_only=True)
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


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Payment method management"""
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'type', 'is_default', 'brand', 'last4',
            'exp_month', 'exp_year', 'display_name', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_display_name(self, obj):
        return str(obj)


class CreatePaymentMethodSerializer(serializers.Serializer):
    """Create new payment method"""
    type = serializers.ChoiceField(choices=['card', 'bank_account', 'pix'])
    token = serializers.CharField(help_text="Payment gateway token")
    is_default = serializers.BooleanField(default=False)
    
    # Card specific fields
    brand = serializers.CharField(required=False)
    last4 = serializers.CharField(max_length=4, required=False)
    exp_month = serializers.IntegerField(required=False, min_value=1, max_value=12)
    exp_year = serializers.IntegerField(required=False)
    
    def validate(self, attrs):
        if attrs['type'] == 'card':
            required_fields = ['brand', 'last4', 'exp_month', 'exp_year']
            for field in required_fields:
                if field not in attrs:
                    raise serializers.ValidationError(
                        f"{field} is required for card payment methods"
                    )
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    """Payment transaction details"""
    payment_method = PaymentMethodSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'amount', 'currency', 'status', 'description',
            'gateway', 'payment_method', 'created_at', 'paid_at'
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