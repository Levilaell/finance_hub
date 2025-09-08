# AUTH_SIMPLIFIED.py - Configuração JWT Ultra-Simplificada para MVP
"""
Configuração de autenticação simplificada que elimina complexidades desnecessárias
para garantir funcionamento confiável em produção.

USO: Adicionar as configurações abaixo em development.py e production.py
"""

from datetime import timedelta
import os

# JWT Configuration - ULTRA SIMPLIFIED
SIMPLE_JWT = {
    # Tokens mais longos para reduzir problemas de refresh
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),  # 2 horas ao invés de 30min
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # 7 dias ao invés de 3
    
    # Simplificar rotação de tokens - desabilitar para MVP
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    
    # Algoritmo mais simples e confiável
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.environ.get('SECRET_KEY'),  # Usar SECRET_KEY diretamente
    
    # Headers mais simples
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # Remover complexidades desnecessárias
    'UPDATE_LAST_LOGIN': False,
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# Autenticação mais robusta - apenas JWT Bearer
AUTHENTICATION_CLASSES = [
    'rest_framework_simplejwt.authentication.JWTAuthentication',
]

# Remover middlewares complexos para MVP
SIMPLIFIED_MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS mais permissivo para MVP (ajustar em produção)
CORS_ALLOW_ALL_ORIGINS = False  # Manter segurança
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://caixahub.com.br",
    "https://seu-frontend-url.com",
]

CORS_ALLOW_CREDENTIALS = False  # Não usar cookies, apenas Bearer tokens
CORS_ALLOW_ALL_HEADERS = True   # Simplificar para MVP

# Rate limiting mais permissivo para MVP
REST_FRAMEWORK_SIMPLIFIED_THROTTLES = {
    'login': '50/hour',        # Mais permissivo
    'api': '2000/hour',        # Menos restritivo
    'burst': '100/minute',     # Permitir mais requisições
}

print("🔧 AUTH_SIMPLIFIED.py loaded - Ultra-simplified JWT authentication for MVP")