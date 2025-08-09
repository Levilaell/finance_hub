# Variáveis de Ambiente Necessárias no Railway

Configure estas variáveis no Railway Dashboard em Settings → Variables:

## Obrigatórias

```bash
# Django
DJANGO_SECRET_KEY=<gerar-uma-chave-segura>
DJANGO_SETTINGS_MODULE=core.settings.production

# Banco de Dados (Railway fornece automaticamente)
DATABASE_URL=<fornecida-pelo-railway>

# Frontend URL
FRONTEND_URL=https://seu-frontend.railway.app

# CORS
CORS_ALLOWED_ORIGINS=https://seu-frontend.railway.app
```

## Recomendadas para Segurança

```bash
# JWT - Use uma das opções:
# Opção 1: Chave simétrica simples (mais fácil)
JWT_SECRET_KEY=<gerar-uma-chave-segura-de-64-caracteres>

# Opção 2: Par de chaves RSA (mais seguro, mas mais complexo)
JWT_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----
<sua-chave-privada-rsa>
-----END RSA PRIVATE KEY-----

JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----
<sua-chave-publica-rsa>
-----END PUBLIC KEY-----

# Criptografia AI Insights
AI_INSIGHTS_ENCRYPTION_KEY=<gerar-uma-chave-de-32-bytes-base64>
```

## Como Gerar as Chaves

### Django Secret Key
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### JWT Secret Key (64 caracteres)
```python
import secrets
print(secrets.token_urlsafe(48))
```

### AI Insights Encryption Key
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### Par de Chaves RSA (opcional)
```bash
# Gerar chave privada
openssl genrsa -out private.pem 2048

# Gerar chave pública
openssl rsa -in private.pem -pubout -out public.pem

# Visualizar as chaves
cat private.pem
cat public.pem
```

## Exemplo de Configuração Mínima

No Railway, adicione estas variáveis:

1. **DJANGO_SECRET_KEY**: `fR7x_Qn9Lz3mK8pW2vT6yB4hN1jC5sA0gE9uX7dI3qO6wZ`
2. **JWT_SECRET_KEY**: `hG3nK7mP9qR2sT5vW8xY0aB4cD6eF1jL3nO5pQ7rS9tU2wX4yZ6`
3. **AI_INSIGHTS_ENCRYPTION_KEY**: `gAAAABh3TqPzRK6nK7mP9qR2sT5vW8xY0aB4cD6eF1jL3nO5pQ7rS9tU2wX4yZ6=`
4. **FRONTEND_URL**: `https://finance-frontend-production-24be.up.railway.app`
5. **CORS_ALLOWED_ORIGINS**: `https://finance-frontend-production-24be.up.railway.app`

## Notas

- As chaves acima são exemplos, gere suas próprias chaves!
- Após adicionar as variáveis, faça redeploy do serviço
- O Railway já fornece DATABASE_URL automaticamente
- Para produção, use sempre chaves fortes e únicas