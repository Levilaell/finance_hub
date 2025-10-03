# 🔐 Variáveis de Ambiente - Railway

## ✅ Obrigatórias (Deploy não funcionará sem elas)

Configure no Railway Dashboard → Variables:

```bash
# Django Core
DJANGO_ENV=production
DJANGO_SETTINGS_MODULE=core.settings.production
DJANGO_SECRET_KEY=<gerar-secret-key>

# Database (auto-configurado se usar Railway PostgreSQL)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# JWT
JWT_SECRET_KEY=<gerar-jwt-secret>

# Frontend
FRONTEND_URL=https://seu-frontend.vercel.app
```

## 🔑 Gerar Secret Keys

Execute localmente para gerar:

```bash
# Django Secret Key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# JWT Secret Key
python -c 'import secrets; print(secrets.token_urlsafe(50))'
```

## 💳 Stripe (Necessário para pagamentos)

```bash
# Modo de operação
STRIPE_LIVE_MODE=false

# Test keys (obter em: https://dashboard.stripe.com/test/apikeys)
STRIPE_TEST_SECRET_KEY=sk_test_...
STRIPE_TEST_PUBLIC_KEY=pk_test_...

# Webhook secret (obter ao criar webhook)
STRIPE_WEBHOOK_SECRET=whsec_...
DJSTRIPE_WEBHOOK_SECRET=whsec_...

# Price ID do produto (obter em: https://dashboard.stripe.com/test/products)
STRIPE_DEFAULT_PRICE_ID=price_...
```

### Como obter Stripe Webhook Secret:

1. Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://seu-backend.railway.app/stripe/webhook/`
3. Eventos para ouvir:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copiar "Signing secret"

## 🏦 Pluggy (Necessário para Open Banking)

```bash
# Credenciais (obter em: https://dashboard.pluggy.ai)
PLUGGY_CLIENT_ID=seu-client-id
PLUGGY_CLIENT_SECRET=seu-client-secret

# Configuração
PLUGGY_BASE_URL=https://api.pluggy.ai
PLUGGY_CONNECT_URL=https://connect.pluggy.ai
PLUGGY_USE_SANDBOX=false

# Webhook (configurar após deploy)
PLUGGY_WEBHOOK_URL=https://seu-backend.railway.app/api/banking/webhooks/pluggy/
PLUGGY_WEBHOOK_SECRET=seu-webhook-secret
```

### Como obter Pluggy Webhook Secret:

1. Pluggy Dashboard → Webhooks
2. Add endpoint: `https://seu-backend.railway.app/api/banking/webhooks/pluggy/`
3. Copiar secret

## 🤖 OpenAI (Opcional - para features de IA)

```bash
OPENAI_API_KEY=sk-...
```

## ⚙️ Opcionais (Performance e Logs)

```bash
# Gunicorn
WEB_CONCURRENCY=4              # Número de workers (baseado em CPU)
GUNICORN_TIMEOUT=120           # Timeout de requisições (segundos)

# Deploy
PORT=8000                      # Porta (Railway configura automaticamente)
DISABLE_COLLECTSTATIC=1        # Desabilitar collectstatic no build

# Python
PYTHONUNBUFFERED=1            # Logs em tempo real

# Localização
LANGUAGE_CODE=pt-br
TIME_ZONE=America/Sao_Paulo
```

## 📋 Checklist de Configuração

### Passo 1: Railway Dashboard
- [ ] Add PostgreSQL service
- [ ] Copiar todas as variáveis obrigatórias acima
- [ ] Gerar e adicionar DJANGO_SECRET_KEY
- [ ] Gerar e adicionar JWT_SECRET_KEY
- [ ] Adicionar FRONTEND_URL

### Passo 2: Stripe
- [ ] Criar conta Stripe (se não tiver)
- [ ] Copiar Test API keys
- [ ] Criar produto e obter PRICE_ID
- [ ] Aguardar deploy do Railway
- [ ] Criar webhook e copiar secret

### Passo 3: Pluggy
- [ ] Criar conta Pluggy (se não tiver)
- [ ] Copiar credenciais (CLIENT_ID e SECRET)
- [ ] Aguardar deploy do Railway
- [ ] Criar webhook e copiar secret

### Passo 4: Verificação
- [ ] Railway build passou
- [ ] App iniciou sem erros
- [ ] Health check respondendo: `/admin/login/`
- [ ] Criar superuser: `railway run python manage.py createsuperuser`
- [ ] Testar login no admin

## 🔍 Verificar Configuração

```bash
# Ver todas as variáveis
railway variables

# Testar conexão com database
railway run python manage.py check --database default

# Ver logs
railway logs
```

## ⚠️ Importante

- **NUNCA** commitar secrets no Git
- Usar **test keys** em produção inicialmente
- Trocar para **live keys** apenas quando estiver funcionando perfeitamente
- Configurar webhooks **após** primeiro deploy (precisa da URL)
