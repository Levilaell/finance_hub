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
    Serializer para registro simplificado: apenas User
    """
    # Campos do User
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'email',
            'phone',
            'password',
        )

    def validate_email(self, value):
        """Verifica se email já existe"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email já está cadastrado.")
        return value

    def validate(self, attrs):
        """Validação geral do formulário"""
        # Validar força da senha
        validate_password(attrs['password'])

        return attrs

    def create(self, validated_data):
        """Criar apenas User (sem Company)"""
        # Gerar username a partir do email
        validated_data['username'] = validated_data['email']

        # Criar User
        user = User.objects.create_user(**validated_data)

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