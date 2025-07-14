"""
Companies app serializers
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Company, CompanyUser, SubscriptionPlan, PaymentMethod, PaymentHistory

User = get_user_model()


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans"""
    yearly_discount = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'slug', 'plan_type',
            'price_monthly', 'price_yearly',
            'max_transactions', 'max_bank_accounts', 'max_users',
            'has_ai_categorization', 'enable_ai_insights', 'enable_ai_reports',
            'max_ai_requests_per_month', 'has_advanced_reports',
            'has_api_access', 'has_accountant_access', 'has_priority_support',
            'yearly_discount'
        ]
    
    def get_yearly_discount(self, obj):
        return obj.get_yearly_discount_percentage()


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
    """Serializer for subscription upgrade"""
    plan_id = serializers.CharField(required=True)
    billing_cycle = serializers.ChoiceField(
        choices=['monthly', 'yearly'],
        default='monthly'
    )
    payment_method_id = serializers.CharField(required=False)
    
    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Plano inválido ou inativo")
        
        # Check if it's actually an upgrade
        user = self.context['request'].user
        current_plan = user.company.subscription_plan
        
        if current_plan and plan.price_monthly <= current_plan.price_monthly:
            if plan.id != current_plan.id:
                raise serializers.ValidationError(
                    "Só é possível fazer upgrade para um plano superior"
                )
        
        return value


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
    """Serializer for adding payment methods"""
    payment_type = serializers.ChoiceField(
        choices=['credit_card', 'debit_card', 'pix']
    )
    card_number = serializers.CharField(required=False)
    exp_month = serializers.IntegerField(required=False, min_value=1, max_value=12)
    exp_year = serializers.IntegerField(required=False, min_value=2024, max_value=2050)
    cvc = serializers.CharField(required=False, max_length=4)
    cardholder_name = serializers.CharField(required=False)
    
    def validate(self, data):
        if data['payment_type'] in ['credit_card', 'debit_card']:
            required_fields = ['card_number', 'exp_month', 'exp_year', 'cvc', 'cardholder_name']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError(
                        f"Campo {field} é obrigatório para cartões"
                    )
            
            # Validate card number
            card_number = data['card_number'].replace(' ', '').replace('-', '')
            if not card_number.isdigit() or len(card_number) < 13 or len(card_number) > 19:
                raise serializers.ValidationError("Número de cartão inválido")
            
            # Basic Luhn check
            if not self.luhn_check(card_number):
                raise serializers.ValidationError("Número de cartão inválido")
        
        return data
    
    def luhn_check(self, card_number):
        """Validate credit card number using Luhn algorithm"""
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d*2))
        return checksum % 10 == 0


class PaymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for payment history"""
    plan_name = serializers.CharField(source='subscription_plan.name', read_only=True)
    payment_method_display = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'transaction_type', 'amount', 'currency', 'status',
            'description', 'invoice_number', 'invoice_url',
            'transaction_date', 'due_date', 'paid_at',
            'plan_name', 'payment_method_display', 'created_at'
        ]
    
    def get_payment_method_display(self, obj):
        if obj.payment_method:
            if obj.payment_method.payment_type == 'pix':
                return 'PIX'
            return f"{obj.payment_method.card_brand} •••• {obj.payment_method.last_four}"
        return "Método padrão"