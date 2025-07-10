"""
Authentication serializers
"""
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company, SubscriptionPlan

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User serializer for profile data"""
    full_name = serializers.CharField(read_only=True)
    initials = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'initials', 'phone', 'avatar',
            'is_email_verified', 'is_phone_verified',
            'preferred_language', 'timezone', 'date_of_birth'
        )
        read_only_fields = ('id', 'username', 'is_email_verified', 'is_phone_verified')


class RegisterSerializer(serializers.ModelSerializer):
    """Registration serializer with company creation"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    company_name = serializers.CharField(required=True)
    company_type = serializers.CharField(required=True)
    business_sector = serializers.CharField(required=True)
    selected_plan = serializers.CharField(required=False, default='free')
    
    class Meta:
        model = User
        fields = (
            'email', 'password', 'password2', 'first_name', 'last_name',
            'phone', 'company_name', 'company_type', 'business_sector', 'selected_plan'
        )
        
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return attrs
    
    def create(self, validated_data):
        company_name = validated_data.pop('company_name')
        company_type = validated_data.pop('company_type')
        business_sector = validated_data.pop('business_sector')
        selected_plan_slug = validated_data.pop('selected_plan', 'free')
        validated_data.pop('password2')
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['email'],
            **validated_data
        )
        
        # Get selected plan or fallback to free plan
        selected_plan = SubscriptionPlan.objects.filter(slug=selected_plan_slug).first()
        if not selected_plan:
            # If selected plan not found, try to get free plan
            selected_plan = SubscriptionPlan.objects.filter(slug='free').first()
            if not selected_plan:
                # If no free plan, get any available plan
                selected_plan = SubscriptionPlan.objects.first()
        
        # Determine subscription status based on plan
        subscription_status = 'active' if selected_plan_slug == 'free' else 'trial'
            
        Company.objects.create(
            owner=user,
            name=company_name,
            company_type=company_type,
            business_sector=business_sector,
            subscription_plan=selected_plan,
            subscription_status=subscription_status
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    """Login serializer"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
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