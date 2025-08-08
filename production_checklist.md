# 🛠️ CHECKLIST PRÁTICO: O que FALTA configurar para Produção

Você está absolutamente certo! Minha análise anterior focou na arquitetura técnica, mas aqui está o que realmente precisa ser FEITO na prática para colocar o sistema em produção:

## 🚨 CRÍTICO - Configurar ANTES do Go-Live

### 1. 🔑 Chaves de API e Secrets

✅ **OBRIGATÓRIAS (Sistema não funciona sem)**

#### Django Core
```env
DJANGO_SECRET_KEY=sua-chave-super-secreta-aqui-min-50-chars
```

#### Database
```env
DATABASE_URL=postgresql://user:pass@host:port/db  # Railway fornece automaticamente
```

#### APIs Essenciais
```env
OPENAI_API_KEY=sk-proj-...        # ❌ FALTA
PLUGGY_CLIENT_ID=seu-client-id    # ❌ FALTA
PLUGGY_CLIENT_SECRET=seu-client-secret  # ❌ FALTA
```

#### Pagamentos
```env
STRIPE_PUBLIC_KEY=pk_live_...      # ❌ FALTA
STRIPE_SECRET_KEY=sk_live_...      # ❌ FALTA
STRIPE_WEBHOOK_SECRET=whsec_...    # ❌ FALTA
```

---

### 2. 🌐 Configurar Webhooks (CRÍTICO)

#### Stripe Webhooks
1. No painel do Stripe, adicionar endpoint:
```
https://seu-backend.railway.app/api/payments/webhooks/stripe/
```

2. Eventos obrigatórios:
- checkout.session.completed
- invoice.payment_succeeded
- invoice.payment_failed
- customer.subscription.updated
- customer.subscription.deleted

3. Obter `STRIPE_WEBHOOK_SECRET` do painel

#### Pluggy Webhooks
1. No painel do Pluggy:
```
https://seu-backend.railway.app/api/banking/webhooks/pluggy/
```

2. Railway:
```env
PLUGGY_WEBHOOK_SECRET=seu-webhook-secret
PLUGGY_WEBHOOK_URL=https://seu-backend.railway.app/api/banking/webhooks/pluggy/
```

---

### 3. 🏠 Domínios e CORS

❌ FALTA CONFIGURAR:

#### Backend
```env
ALLOWED_HOSTS=seu-backend.railway.app,seu-frontend.railway.app
CORS_ALLOWED_ORIGINS=https://seu-frontend.railway.app
```

#### Frontend
```env
NEXT_PUBLIC_API_URL=https://seu-backend.railway.app
NEXT_PUBLIC_APP_URL=https://seu-frontend.railway.app
```

---

### 4. 📧 Email (Opcional mas Recomendado)

Exemplo com SendGrid:
```env
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.sua-api-key-sendgrid
DEFAULT_FROM_EMAIL=noreply@seudominio.com
```

---

## 🔧 CONFIGURAÇÕES ESPECÍFICAS POR SERVIÇO

### Railway Variables (Backend)
```env
DJANGO_SECRET_KEY=...
DEBUG=False
DJANGO_SETTINGS_MODULE=core.settings.production

OPENAI_API_KEY=sk-proj-...
PLUGGY_CLIENT_ID=...
PLUGGY_CLIENT_SECRET=...
PLUGGY_USE_SANDBOX=false  # ❌ Mudar para produção!

STRIPE_PUBLIC_KEY=pk_live_...     # ❌ Mudar para LIVE!
STRIPE_SECRET_KEY=sk_live_...     # ❌ Mudar para LIVE!
STRIPE_WEBHOOK_SECRET=whsec_...

ALLOWED_HOSTS=seu-backend.railway.app
CORS_ALLOWED_ORIGINS=https://seu-frontend.railway.app
FRONTEND_URL=https://seu-frontend.railway.app
```

### Railway Variables (Frontend)
```env
NEXT_PUBLIC_API_URL=https://seu-backend.railway.app
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_live_...  # ❌ Mudar para LIVE!
```

---

## ⚠️ PROBLEMAS IDENTIFICADOS

1. 🚨 **Stripe Service INCOMPLETO**  
`stripe_service.py` é apenas um stub. Implementar:
- Checkout sessions reais
- Webhook handling completo
- Payment intents
- Subscription management

2. 🚨 **URLs Hardcoded**
```js
// next.config.js linha 39
"connect-src 'self' http://localhost:8000 https://finance-backend-production-29df.up.railway.app"
```
Trocar por variável de ambiente!

3. 🚨 **Pluggy Sandbox Mode**
```python
PLUGGY_USE_SANDBOX = config('PLUGGY_USE_SANDBOX', default=False, cast=bool)
```
Verificar se está como `False` em produção.

---

## 📋 ACTIONS IMEDIATAS

### Passo 1: APIs e Keys
- Criar conta OpenAI
- Configurar Pluggy em produção
- Configurar Stripe em modo LIVE
- Gerar todos os webhook secrets

### Passo 2: Implementar Stripe Service
- apps/payments/services/stripe_service.py

### Passo 3: Configurar Railway
- Adicionar variáveis
- Configurar Redis e PostgreSQL addons

### Passo 4: DNS e Domínios
- Definir domínios finais
- Configurar CORS e CSP
- Testar conectividade

### Passo 5: Webhooks
- Configurar endpoints no Stripe e Pluggy
- Testar com ngrok
- Verificar logs no Railway

---

## 🔍 VERIFICAÇÕES PRÉ-DEPLOY

Checklist Final:
- ✅ Variáveis no Railway
- ✅ Stripe LIVE
- ✅ Pluggy PRODUÇÃO
- ✅ Webhooks testados
- ✅ CORS OK
- ✅ URLs hardcoded removidas
- ✅ Stripe service finalizado
- ✅ Email configurado
- ✅ Sentry ativo
- ✅ Backup automático

---

## 💰 CUSTOS ESTIMADOS

**APIs:**
- OpenAI: $20-50/mês
- Pluggy: sob consulta
- Stripe: 2.9% + $0.30/tx

**Infraestrutura:**
- Railway: $20-50/mês
- SendGrid: $15/mês
- Domínio: $10-15/ano

**Total Estimado:** $70-140/mês

---

## 🎯 RESUMO: O QUE REALMENTE FALTA

1. 🔥 URGENTE: Implementar Stripe service completo  
2. 🔥 URGENTE: Configurar todas as chaves de API  
3. 🔥 URGENTE: Configurar webhooks Stripe + Pluggy  
4. 🔥 URGENTE: Definir domínios e configurar CORS  
5. 📧 IMPORTANTE: Configurar email  
6. 📊 IMPORTANTE: Configurar Sentry monitoring  
