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
    
    class Meta:
        model = User
        fields = (
            'email', 'password', 'password2', 'first_name', 'last_name',
            'phone', 'company_name', 'company_type', 'business_sector'
        )
        
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        company_name = validated_data.pop('company_name')
        company_type = validated_data.pop('company_type')
        business_sector = validated_data.pop('business_sector')
        validated_data.pop('password2')
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['email'],
            **validated_data
        )
        
        # Create company with trial subscription
        trial_plan = SubscriptionPlan.objects.filter(plan_type='starter').first()
        if not trial_plan:
            trial_plan = SubscriptionPlan.objects.first()
            
        Company.objects.create(
            owner=user,
            name=company_name,
            company_type=company_type,
            business_sector=business_sector,
            subscription_plan=trial_plan,
            subscription_status='trial'
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
                raise serializers.ValidationError('Invalid credentials.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
                
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include "email" and "password".')


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
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirmation serializer"""
    token = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Change password serializer"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct.")
        return value


class EmailVerificationSerializer(serializers.Serializer):
    """Email verification serializer"""
    token = serializers.CharField(required=True)