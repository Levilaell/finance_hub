# Deploy no Render

Este guia descreve como fazer o deploy da aplicação Finance Management no Render.

## Pré-requisitos

1. Conta no [Render](https://render.com)
2. Conta no GitHub com o repositório do projeto
3. Configurações de API (Stripe, Pluggy, etc.)

## Passos para Deploy

### 1. Preparar o Repositório

Certifique-se de que os seguintes arquivos estão commitados:
- `render.yaml` (configuração dos serviços)
- `backend/requirements.txt` com `dj-database-url`
- Configurações de produção atualizadas

### 2. Conectar o GitHub ao Render

1. Acesse [dashboard.render.com](https://dashboard.render.com)
2. Clique em "New +" → "Blueprint"
3. Conecte sua conta do GitHub
4. Selecione o repositório `finance_management`
5. O Render detectará automaticamente o `render.yaml`

### 3. Configurar Variáveis de Ambiente

Após criar o blueprint, configure as seguintes variáveis de ambiente em cada serviço:

#### Backend (finance-backend)
```
DJANGO_SECRET_KEY=<gerada automaticamente>
DEBUG=False
ALLOWED_HOSTS=.onrender.com
CORS_ALLOWED_ORIGINS=https://finance-frontend.onrender.com
FRONTEND_URL=https://finance-frontend.onrender.com

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
DEFAULT_FROM_EMAIL=noreply@seudominio.com

# APIs
OPENAI_API_KEY=sk-...
PLUGGY_CLIENT_ID=seu-client-id
PLUGGY_CLIENT_SECRET=seu-client-secret
PLUGGY_WEBHOOK_URL=https://finance-backend.onrender.com/api/banking/pluggy/webhook/

# Pagamento
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# AWS S3 (para arquivos de mídia)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...
AWS_S3_REGION_NAME=us-east-1
```

#### Frontend (finance-frontend)
```
NEXT_PUBLIC_API_URL=https://finance-backend.onrender.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_PLUGGY_CONNECT_KEY=seu-connect-key
```

### 4. Deploy

1. Após configurar as variáveis, clique em "Apply"
2. O Render iniciará o deploy de todos os serviços
3. Aguarde o build e deploy completar (cerca de 10-15 minutos)

### 5. Configurações Pós-Deploy

#### Domínio Customizado (Opcional)
1. Vá em Settings de cada serviço web
2. Adicione seu domínio customizado
3. Configure o DNS conforme instruções do Render

#### Webhooks
Configure os webhooks nos serviços externos:

**Stripe:**
- URL: `https://finance-backend.onrender.com/api/payments/stripe/webhook/`
- Eventos: `checkout.session.completed`, `invoice.payment_succeeded`, etc.

**Pluggy:**
- URL: `https://finance-backend.onrender.com/api/banking/pluggy/webhook/`

### 6. Monitoramento

- Verifique os logs em cada serviço no dashboard do Render
- Configure alertas para falhas de deploy
- Monitore o uso de recursos

## Troubleshooting

### Erro de Migração
Se houver erro nas migrações:
1. Acesse o Shell do serviço backend
2. Execute: `python manage.py migrate --run-syncdb`

### Erro de Static Files
Se os arquivos estáticos não carregarem:
1. Verifique se `whitenoise` está instalado
2. Execute: `python manage.py collectstatic --noinput`

### Erro de Conexão Redis
Verifique se o serviço Redis está rodando e as URLs estão corretas.

## Comandos Úteis

```bash
# Criar superusuário
python manage.py createsuperuser

# Criar categorias padrão
python manage.py create_default_categories

# Criar planos de assinatura
python manage.py create_subscription_plans
```

## Custos Estimados

- **Starter Plan**: ~$7/mês por serviço
- **Redis**: ~$7/mês
- **PostgreSQL**: ~$7/mês
- **Total**: ~$35-40/mês para todos os serviços

## Alternativas de Deploy

Se preferir economizar nos custos iniciais:
1. Use apenas 1 web service combinando backend + frontend
2. Use SQLite ao invés de PostgreSQL (não recomendado para produção)
3. Desative temporariamente os workers do Celery