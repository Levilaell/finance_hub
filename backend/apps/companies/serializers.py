"""
Companies app serializers
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Company, CompanyUser, SubscriptionPlan, PaymentMethod, PaymentHistory

User = get_user_model()


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Subscription plan details"""
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'slug', 'plan_type', 'price_monthly', 'price_yearly',
            'max_transactions', 'max_bank_accounts', 'max_users',
            'has_ai_categorization', 'has_advanced_reports', 'has_api_access',
            'has_accountant_access'
        ]


class CompanySerializer(serializers.ModelSerializer):
    """Company profile serializer"""
    owner = serializers.SerializerMethodField()
    subscription_plan = SubscriptionPlanSerializer(read_only=True)
    is_trial = serializers.ReadOnlyField()
    is_subscribed = serializers.ReadOnlyField()
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'trade_name', 'display_name', 'cnpj', 'company_type',
            'business_sector', 'email', 'phone', 'website', 'owner',
            'address_street', 'address_number', 'address_complement',
            'address_neighborhood', 'address_city', 'address_state',
            'address_zipcode', 'monthly_revenue', 'employee_count',
            'subscription_plan', 'subscription_status', 'is_trial',
            'is_subscribed', 'trial_ends_at', 'next_billing_date',
            'subscription_start_date', 'subscription_end_date',
            'logo', 'primary_color', 'currency', 'fiscal_year_start',
            'enable_ai_categorization', 'auto_categorize_threshold',
            'enable_notifications', 'enable_email_reports',
            'created_at', 'is_active'
        ]
        read_only_fields = [
            'owner', 'subscription_status', 'trial_ends_at', 
            'next_billing_date', 'subscription_start_date', 
            'subscription_end_date', 'created_at'
        ]
    
    def get_owner(self, obj):
        """Get owner basic info"""
        return {
            'id': obj.owner.id,
            'name': obj.owner.full_name,
            'email': obj.owner.email
        }


class CompanyUpdateSerializer(serializers.ModelSerializer):
    """Company update serializer (limited fields)"""
    
    class Meta:
        model = Company
        fields = [
            'name', 'trade_name', 'cnpj', 'email', 'phone', 'website',
            'address_street', 'address_number', 'address_complement',
            'address_neighborhood', 'address_city', 'address_state',
            'address_zipcode', 'monthly_revenue', 'employee_count',
            'logo', 'primary_color', 'fiscal_year_start',
            'enable_ai_categorization', 'auto_categorize_threshold',
            'enable_notifications', 'enable_email_reports'
        ]


class CompanyUserSerializer(serializers.ModelSerializer):
    """Company user/team member serializer"""
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = CompanyUser
        fields = [
            'id', 'user', 'role', 'permissions', 'is_active',
            'invited_at', 'joined_at'
        ]
    
    def get_user(self, obj):
        """Get user info"""
        return {
            'id': obj.user.id,
            'name': obj.user.full_name,
            'email': obj.user.email,
            'avatar': obj.user.avatar.url if obj.user.avatar else None
        }


class InviteUserSerializer(serializers.Serializer):
    """Invite user to company serializer"""
    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(choices=CompanyUser.ROLE_CHOICES, required=True)
    permissions = serializers.JSONField(required=False, default=dict)
    
    def validate_email(self, value):
        """Check if user already exists in company"""
        company = self.context['request'].user.company
        if CompanyUser.objects.filter(
            company=company,
            user__email=value
        ).exists():
            raise serializers.ValidationError("User already member of this company.")
        return value


class UpgradeSubscriptionSerializer(serializers.Serializer):
    """Upgrade subscription serializer"""
    plan_id = serializers.IntegerField(required=True)
    billing_cycle = serializers.ChoiceField(
        choices=['monthly', 'yearly'],
        required=True
    )
    
    def validate_plan_id(self, value):
        """Validate plan exists and is upgradeable"""
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            current_plan = self.context['request'].user.company.subscription_plan
            
            # Check if it's actually an upgrade
            if plan.price_monthly <= current_plan.price_monthly:
                raise serializers.ValidationError("Selected plan is not an upgrade.")
                
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid subscription plan.")


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Payment method serializer"""
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'payment_type', 'card_brand', 'last_four', 'exp_month', 
            'exp_year', 'cardholder_name', 'is_default', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class AddPaymentMethodSerializer(serializers.Serializer):
    """Add payment method serializer"""
    payment_type = serializers.ChoiceField(choices=PaymentMethod.PAYMENT_TYPES)
    
    # Credit card fields
    card_number = serializers.CharField(max_length=19, required=False)
    exp_month = serializers.IntegerField(min_value=1, max_value=12, required=False)
    exp_year = serializers.IntegerField(min_value=2024, max_value=2040, required=False)
    cvc = serializers.CharField(max_length=4, required=False)
    cardholder_name = serializers.CharField(max_length=200, required=False)
    
    def validate(self, data):
        """Validate payment method data"""
        if data['payment_type'] in ['credit_card', 'debit_card']:
            required_fields = ['card_number', 'exp_month', 'exp_year', 'cvc', 'cardholder_name']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError(f"{field} is required for card payments")
        return data


class PaymentHistorySerializer(serializers.ModelSerializer):
    """Payment history serializer"""
    payment_method_display = serializers.SerializerMethodField()
    plan_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'transaction_type', 'amount', 'currency', 'status', 
            'description', 'invoice_number', 'invoice_url', 'transaction_date',
            'due_date', 'paid_at', 'payment_method_display', 'plan_name', 'created_at'
        ]
    
    def get_payment_method_display(self, obj):
        """Get payment method display string"""
        if obj.payment_method:
            return str(obj.payment_method)
        return "N/A"
    
    def get_plan_name(self, obj):
        """Get subscription plan name"""
        if obj.subscription_plan:
            return obj.subscription_plan.name
        return None