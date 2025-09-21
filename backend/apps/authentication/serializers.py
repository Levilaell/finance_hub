"""
Authentication serializers - COMPLETE VERSION
"""
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para retornar dados do usuário (sem senha)
    """
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'full_name',
            'phone', 
            'timezone',
            'created_at'
        )
        read_only_fields = ('id', 'username', 'created_at')


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para registro completo: User + Company
    """
    # Campos do User
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    # Campos da Company (não estão no User model)
    company_name = serializers.CharField(max_length=200)
    company_cnpj = serializers.CharField(max_length=18)
    company_type = serializers.ChoiceField(choices=[
        ('mei', 'MEI'),
        ('me', 'Microempresa'),
        ('epp', 'Empresa de Pequeno Porte'),
        ('ltda', 'Limitada'),
        ('sa', 'Sociedade Anônima'),
        ('other', 'Outros'),
    ])
    business_sector = serializers.ChoiceField(choices=[
        ('retail', 'Comércio'),
        ('services', 'Serviços'),
        ('industry', 'Indústria'),
        ('technology', 'Tecnologia'),
        ('healthcare', 'Saúde'),
        ('education', 'Educação'),
        ('food', 'Alimentação'),
        ('construction', 'Construção'),
        ('automotive', 'Automotivo'),
        ('agriculture', 'Agricultura'),
        ('other', 'Outros'),
    ])
    
    class Meta:
        model = User
        fields = (
            # Campos do User
            'email', 'password', 'password2', 'first_name', 'last_name', 'phone',
            # Campos da Company (extras)
            'company_name', 'company_cnpj', 'company_type', 'business_sector'
        )
    
    def validate_email(self, value):
        """Verifica se email já existe"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email já está cadastrado.")
        return value
    
    def validate_company_cnpj(self, value):
        """Verifica se CNPJ já existe"""
        # Import aqui para evitar circular import
        from apps.companies.models import Company
        
        # Remover formatação do CNPJ (manter só números)
        cnpj_clean = ''.join(filter(str.isdigit, value))
        
        if len(cnpj_clean) != 14:
            raise serializers.ValidationError("CNPJ deve ter 14 dígitos.")
        
        if Company.objects.filter(cnpj=value).exists():
            raise serializers.ValidationError("Este CNPJ já está cadastrado.")
        
        return value
    
    def validate(self, attrs):
        """Validação geral do formulário"""
        # Verificar se senhas coincidem
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "As senhas não coincidem."
            })
        
        # Validar força da senha
        validate_password(attrs['password'])
        
        return attrs
    
    def create(self, validated_data):
        """Criar User + Company automaticamente"""
        # Separar dados da Company dos dados do User
        company_data = {
            'name': validated_data.pop('company_name'),
            'cnpj': validated_data.pop('company_cnpj'),
            'company_type': validated_data.pop('company_type'),
            'business_sector': validated_data.pop('business_sector'),
        }
        
        # Limpar dados do User
        validated_data.pop('password2')
        validated_data['username'] = validated_data['email']
        
        # 1. Criar User primeiro
        user = User.objects.create_user(**validated_data)
        
        # 2. Criar Company associada ao User
        from apps.companies.models import Company
        Company.objects.create(
            owner=user,
            **company_data
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer para login
    """
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    
    def validate(self, attrs):
        """Validar credenciais"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Tentar autenticar (username=email no nosso caso)
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    "Email ou senha incorretos."
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    "Conta desativada."
                )
            
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError(
            "Email e senha são obrigatórios."
        )


class TokenResponseSerializer(serializers.Serializer):
    """
    Serializer para resposta de tokens (documentação)
    """
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()