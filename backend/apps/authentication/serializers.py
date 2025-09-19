"""
Authentication serializers
"""
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company, SubscriptionPlan
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
            'full_name', 'initials', 'phone', 'timezone', 'company'
        )
        read_only_fields = ('id', 'username', 'company')
    
    def get_company(self, obj):
        """Get user's company data"""
        try:
            # Import here to avoid circular import
            from apps.companies.serializers import CompanySerializer
            
            # First try to get company if user is owner
            if hasattr(obj, 'company'):
                return CompanySerializer(obj.company).data
            
            # Team member functionality has been simplified
            # Only company owners are supported in current architecture
                
        except (AttributeError, Company.DoesNotExist):
            pass
        
        return None


class RegisterSerializer(serializers.ModelSerializer):
    """Registration serializer with company creation"""
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'O e-mail é obrigatório.',
            'invalid': 'Digite um endereço de e-mail válido.',
            'blank': 'O campo de e-mail não pode estar vazio.'
        }
    )
    password = serializers.CharField(
        write_only=True, 
        required=True,
        error_messages={
            'required': 'A senha é obrigatória.',
            'blank': 'O campo de senha não pode estar vazio.'
        }
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True,
        error_messages={
            'required': 'A confirmação de senha é obrigatória.',
            'blank': 'O campo de confirmação de senha não pode estar vazio.'
        }
    )
    first_name = serializers.CharField(
        required=True,
        error_messages={
            'required': 'O nome é obrigatório.',
            'blank': 'O campo de nome não pode estar vazio.'
        }
    )
    last_name = serializers.CharField(
        required=True,
        error_messages={
            'required': 'O sobrenome é obrigatório.',
            'blank': 'O campo de sobrenome não pode estar vazio.'
        }
    )
    company_name = serializers.CharField(
        required=True,
        error_messages={
            'required': 'O nome da empresa é obrigatório.',
            'blank': 'O campo de nome da empresa não pode estar vazio.'
        }
    )
    company_type = serializers.CharField(
        required=True,
        error_messages={
            'required': 'O tipo de empresa é obrigatório.',
            'blank': 'O campo de tipo de empresa não pode estar vazio.'
        }
    )
    business_sector = serializers.CharField(
        required=True,
        error_messages={
            'required': 'O setor de negócios é obrigatório.',
            'blank': 'O campo de setor de negócios não pode estar vazio.'
        }
    )
    company_cnpj = serializers.CharField(
        required=True, 
        validators=[validate_cnpj],
        error_messages={
            'required': 'O CNPJ é obrigatório.',
            'blank': 'O campo de CNPJ não pode estar vazio.',
            'invalid': 'CNPJ inválido. Digite apenas números (14 dígitos).'
        }
    )
    phone = serializers.CharField(
        required=True, 
        validators=[validate_phone],
        error_messages={
            'required': 'O telefone é obrigatório.',
            'blank': 'O campo de telefone não pode estar vazio.',
            'invalid': 'Telefone inválido. Use o formato: (11) 98765-4321'
        }
    )
    selected_plan = serializers.CharField(required=False, default='starter')
    
    class Meta:
        model = User
        fields = (
            'email', 'password', 'password2', 'first_name', 'last_name',
            'phone', 'company_name', 'company_cnpj', 'company_type', 'business_sector', 'selected_plan'
        )
        
    def validate_email(self, value):
        """Validação customizada para email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este e-mail já está cadastrado.')
        return value
    
    def validate_first_name(self, value):
        """Validação customizada para nome"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError('O nome deve ter pelo menos 2 caracteres.')
        if not value.replace(' ', '').isalpha():
            raise serializers.ValidationError('O nome deve conter apenas letras.')
        return value.strip()
    
    def validate_last_name(self, value):
        """Validação customizada para sobrenome"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError('O sobrenome deve ter pelo menos 2 caracteres.')
        if not value.replace(' ', '').isalpha():
            raise serializers.ValidationError('O sobrenome deve conter apenas letras.')
        return value.strip()
    
    def validate_company_name(self, value):
        """Validação customizada para nome da empresa"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError('O nome da empresa deve ter pelo menos 3 caracteres.')
        return value.strip()
    
    def validate_company_cnpj(self, value):
        """Validação customizada para CNPJ incluindo duplicação"""
        from apps.companies.models import Company
        from apps.companies.validators import validate_cnpj as cnpj_validator
        
        # Primeiro valida o formato
        try:
            cnpj_validator(value)
        except serializers.ValidationError:
            raise
        
        # Depois verifica se já existe
        from apps.companies.validators import format_cnpj
        formatted_cnpj = format_cnpj(value)
        
        if Company.objects.filter(cnpj=formatted_cnpj).exists():
            raise serializers.ValidationError('Este CNPJ já está cadastrado.')
        
        return value
    
    def validate_password(self, value):
        """Validação customizada para senha com mensagens em português"""
        from django.contrib.auth.password_validation import (
            MinimumLengthValidator,
            UserAttributeSimilarityValidator,
            CommonPasswordValidator,
            NumericPasswordValidator
        )
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        errors = []
        
        # Validação de comprimento mínimo
        try:
            MinimumLengthValidator(min_length=8).validate(value)
        except DjangoValidationError:
            errors.append('A senha deve ter pelo menos 8 caracteres.')
        
        # Validação de senha comum
        try:
            CommonPasswordValidator().validate(value)
        except DjangoValidationError:
            errors.append('Esta senha é muito comum. Escolha uma senha mais segura.')
        
        # Validação de senha numérica
        try:
            NumericPasswordValidator().validate(value)
        except DjangoValidationError:
            errors.append('A senha não pode conter apenas números.')
        
        # Verificações adicionais
        if not any(char.isupper() for char in value):
            errors.append('A senha deve conter pelo menos uma letra maiúscula.')
        
        if not any(char.islower() for char in value):
            errors.append('A senha deve conter pelo menos uma letra minúscula.')
        
        if not any(char.isdigit() for char in value):
            errors.append('A senha deve conter pelo menos um número.')
        
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in value):
            errors.append('A senha deve conter pelo menos um caractere especial (!@#$%^&* etc).')
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return value
        
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "As senhas não coincidem.", "password2": "As senhas não coincidem."})
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
                    max_bank_accounts=2,
                    display_order=1
                )
        
        # ALWAYS CREATE TRIAL FOR 14 DAYS - NO EXCEPTIONS
        from django.utils import timezone
        from datetime import timedelta
        import logging
        
        logger = logging.getLogger(__name__)
        
        trial_end_date = timezone.now() + timedelta(days=14)
        logger.info(f"Creating company for user {user.email} with trial ending at {trial_end_date}")
        
        company = Company.objects.create(
            owner=user,
            name=company_name,
            cnpj=format_cnpj(company_cnpj),
            company_type=company_type,
            business_sector=business_sector,
            subscription_plan=selected_plan,
            subscription_status='trial',  # ALWAYS trial
            trial_ends_at=trial_end_date  # ALWAYS 14 days
        )
        
        logger.info(f"Company created: {company.id} - Status: {company.subscription_status} - Trial ends: {company.trial_ends_at}")
        
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