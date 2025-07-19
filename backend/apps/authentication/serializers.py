"""
Authentication serializers
"""
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company, SubscriptionPlan, CompanyUser
from apps.companies.validators import validate_cnpj, validate_phone, format_cnpj, format_phone

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User serializer for profile data"""
    full_name = serializers.CharField(read_only=True)
    initials = serializers.CharField(read_only=True)
    company = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'initials', 'phone', 'avatar',
            'is_email_verified', 'is_phone_verified',
            'preferred_language', 'timezone', 'date_of_birth', 'company'
        )
        read_only_fields = ('id', 'username', 'is_email_verified', 'is_phone_verified', 'company')
    
    def get_company(self, obj):
        """Get user's company data"""
        try:
            # Import here to avoid circular import
            from apps.companies.serializers import CompanySerializer
            
            # First try to get company if user is owner
            if hasattr(obj, 'company'):
                return CompanySerializer(obj.company).data
            
            # If user is not owner, check if they're a team member
            company_user = CompanyUser.objects.filter(user=obj, is_active=True).first()
            if company_user:
                return CompanySerializer(company_user.company).data
                
        except (AttributeError, Company.DoesNotExist):
            pass
        
        return None


class RegisterSerializer(serializers.ModelSerializer):
    """Registration serializer with company creation"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    company_name = serializers.CharField(required=True)
    company_type = serializers.CharField(required=True)
    business_sector = serializers.CharField(required=True)
    company_cnpj = serializers.CharField(required=True, validators=[validate_cnpj])
    phone = serializers.CharField(required=True, validators=[validate_phone])
    selected_plan = serializers.CharField(required=False, default='starter')
    
    class Meta:
        model = User
        fields = (
            'email', 'password', 'password2', 'first_name', 'last_name',
            'phone', 'company_name', 'company_cnpj', 'company_type', 'business_sector', 'selected_plan'
        )
        
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return attrs
    
    def create(self, validated_data):
        company_name = validated_data.pop('company_name')
        company_cnpj = validated_data.pop('company_cnpj')
        company_type = validated_data.pop('company_type')
        business_sector = validated_data.pop('business_sector')
        selected_plan_slug = validated_data.pop('selected_plan', 'starter')
        validated_data.pop('password2')
        
        # Format phone before saving
        validated_data['phone'] = format_phone(validated_data['phone'])
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['email'],
            **validated_data
        )
        
        # Get selected plan - NO MORE FREE PLAN
        selected_plan = SubscriptionPlan.objects.filter(slug=selected_plan_slug).first()
        if not selected_plan or selected_plan_slug == 'free':
            # Fallback to starter plan if invalid or trying to use free
            selected_plan = SubscriptionPlan.objects.filter(slug='starter').first()
            if not selected_plan:
                # Create a minimal starter plan if it doesn't exist
                selected_plan = SubscriptionPlan.objects.create(
                    name='Starter',
                    slug='starter',
                    plan_type='starter',
                    price_monthly=49,
                    price_yearly=490,
                    max_transactions=500,
                    max_bank_accounts=2,
                    max_users=3,
                    has_ai_categorization=False,
                    enable_ai_insights=False,
                    enable_ai_reports=False,
                    max_ai_requests_per_month=0,
                    has_advanced_reports=True,
                    has_api_access=False,
                    has_accountant_access=False,
                    has_priority_support=True,
                    display_order=1
                )
        
        # ALWAYS CREATE TRIAL FOR 14 DAYS - NO EXCEPTIONS
        from django.utils import timezone
        from datetime import timedelta
        
        Company.objects.create(
            owner=user,
            name=company_name,
            cnpj=format_cnpj(company_cnpj),
            company_type=company_type,
            business_sector=business_sector,
            subscription_plan=selected_plan,
            subscription_status='trial',  # ALWAYS trial
            trial_ends_at=timezone.now() + timedelta(days=14)  # ALWAYS 14 days
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    """Login serializer"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    two_fa_code = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            
            if not user:
                raise serializers.ValidationError('Credenciais inválidas.')
            
            if not user.is_active:
                raise serializers.ValidationError('Conta de usuário desativada.')
                
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Deve incluir "email" e "senha".')


class TokenSerializer(serializers.Serializer):
    """JWT token response serializer"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class RefreshTokenSerializer(serializers.Serializer):
    """Refresh token serializer"""
    refresh = serializers.CharField(required=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Password reset request serializer"""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Nenhum usuário encontrado com este endereço de e-mail.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirmation serializer"""
    token = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Change password serializer"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Senha atual está incorreta.")
        return value


class EmailVerificationSerializer(serializers.Serializer):
    """Email verification serializer"""
    token = serializers.CharField(required=True)


class DeleteAccountSerializer(serializers.Serializer):
    """Delete account serializer with password verification"""
    password = serializers.CharField(required=True, write_only=True)
    confirmation = serializers.CharField(required=True)
    
    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Senha incorreta.")
        return value
        
    def validate_confirmation(self, value):
        if value.lower() != 'deletar':
            raise serializers.ValidationError("Digite 'deletar' para confirmar.")
        return value