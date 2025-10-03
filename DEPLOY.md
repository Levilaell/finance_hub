# 🚀 Guia de Deploy - Finance Hub

## 📋 Pré-requisitos

### Contas Necessárias
- [ ] Railway account (backend hosting)
- [ ] Vercel account (frontend hosting)
- [ ] PostgreSQL database (Railway ou outro)
- [ ] Stripe account (pagamentos)
- [ ] Pluggy account (open banking)

### Credenciais Necessárias
Antes de começar, tenha em mãos:
- Stripe API keys (test e live)
- Pluggy client ID e secret
- OpenAI API key (opcional)

---

## 🔧 Deploy do Backend (Railway)

### 1. Setup do Projeto no Railway

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Inicializar projeto
cd backend
railway init
```

### 2. Configurar Variáveis de Ambiente

No Railway Dashboard, adicione as seguintes variáveis:

**Essenciais:**
```bash
DJANGO_ENV=production
DJANGO_SETTINGS_MODULE=core.settings.production
DJANGO_SECRET_KEY=<gere-um-secret-key-forte>
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Auto-configurado pelo Railway
JWT_SECRET_KEY=<gere-outro-secret-key>
FRONTEND_URL=https://seu-frontend.vercel.app
```

**Stripe:**
```bash
STRIPE_LIVE_MODE=false  # true para produção
STRIPE_TEST_SECRET_KEY=sk_test_...
STRIPE_TEST_PUBLIC_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
DJSTRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_DEFAULT_PRICE_ID=price_...
```

**Pluggy:**
```bash
PLUGGY_CLIENT_ID=seu-client-id
PLUGGY_CLIENT_SECRET=seu-client-secret
PLUGGY_USE_SANDBOX=false
PLUGGY_WEBHOOK_URL=https://seu-backend.up.railway.app/api/banking/webhooks/pluggy/
```

**Opcional:**
```bash
OPENAI_API_KEY=sk-...
WEB_CONCURRENCY=4
GUNICORN_TIMEOUT=120
```

### 3. Gerar Secret Keys Seguros

```bash
# Django Secret Key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# JWT Secret Key
python -c 'import secrets; print(secrets.token_urlsafe(50))'
```

### 4. Configurar Database

Railway criará automaticamente um PostgreSQL. Para usar:

1. Adicione PostgreSQL no Railway
2. A variável `DATABASE_URL` será auto-configurada
3. O `start.sh` executará migrations automaticamente

### 5. Deploy

```bash
# Via Railway CLI
railway up

# Ou conecte o GitHub repo no Railway Dashboard
# Deploy automático a cada push na branch main
```

### 6. Configurar Domínio Customizado

1. Railway Dashboard → Settings → Domains
2. Adicionar domínio: `api.seudominio.com`
3. Configurar DNS:
   ```
   CNAME api <seu-projeto>.up.railway.app
   ```

### 7. Webhooks

**Stripe:**
1. Stripe Dashboard → Webhooks
2. Add endpoint: `https://api.seudominio.com/stripe/webhook/`
3. Copiar signing secret para `STRIPE_WEBHOOK_SECRET`

**Pluggy:**
1. Pluggy Dashboard → Webhooks
2. Add endpoint: `https://api.seudominio.com/api/banking/webhooks/pluggy/`
3. Copiar secret para `PLUGGY_WEBHOOK_SECRET`

---

## 🎨 Deploy do Frontend (Vercel)

### 1. Setup do Projeto no Vercel

```bash
# Instalar Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel
```

### 2. Configurar Variáveis de Ambiente

No Vercel Dashboard:

```bash
NEXT_PUBLIC_API_URL=https://api.seudominio.com
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_...
NEXT_PUBLIC_PLUGGY_CLIENT_ID=seu-client-id
NODE_ENV=production
```

### 3. Configurar Domínio

1. Vercel Dashboard → Settings → Domains
2. Adicionar: `app.seudominio.com`
3. Configurar DNS:
   ```
   CNAME app cname.vercel-dns.com
   ```

### 4. Deploy Automático

Configure GitHub integration no Vercel:
- Deploy automático na branch `main`
- Preview deploys em PRs

---

## ✅ Checklist Pós-Deploy

### Backend
- [ ] Health check funcionando: `https://api.seudominio.com/admin/login/`
- [ ] Admin acessível: criar superuser
  ```bash
  railway run python manage.py createsuperuser
  ```
- [ ] Migrations aplicadas
- [ ] Static files servidos
- [ ] Webhooks configurados (Stripe + Pluggy)
- [ ] CORS configurado corretamente
- [ ] SSL/HTTPS funcionando

### Frontend
- [ ] Site acessível: `https://app.seudominio.com`
- [ ] Login funcionando
- [ ] API calls funcionando
- [ ] Stripe checkout funcionando
- [ ] Pluggy connect funcionando
- [ ] CSP headers corretos

### Segurança
- [ ] Secrets não commitados no Git
- [ ] `.env` no `.gitignore`
- [ ] `DEBUG=False` em produção
- [ ] `ALLOWED_HOSTS` configurado
- [ ] Rate limiting ativo
- [ ] HTTPS forçado
- [ ] Sentry configurado (opcional)

---

## 🔍 Monitoramento

### Logs do Backend (Railway)
```bash
railway logs
```

### Logs do Frontend (Vercel)
```bash
vercel logs
```

### Métricas
- Railway Dashboard: CPU, RAM, Network
- Vercel Analytics: Performance, Core Web Vitals
- Sentry: Error tracking (se configurado)

---

## 🐛 Troubleshooting

### Backend não inicia
1. Verificar logs: `railway logs`
2. Confirmar env vars: `railway variables`
3. Testar localmente: `DJANGO_ENV=production python manage.py check`

### Erro 500 no frontend
1. Verificar CORS no backend (`ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`)
2. Confirmar `NEXT_PUBLIC_API_URL` correto
3. Verificar logs do Railway

### Webhooks não funcionam
1. Verificar URL do webhook está acessível
2. Confirmar secrets configurados
3. Verificar logs de requisições no Stripe/Pluggy Dashboard

### Database migration error
```bash
railway run python manage.py migrate --verbosity 3
railway run python manage.py showmigrations
```

---

## 🔄 Atualizações

### Deploy de Nova Versão

**Backend:**
```bash
git push origin main  # Se GitHub connected
# OU
railway up
```

**Frontend:**
```bash
git push origin main  # Auto-deploy via Vercel
# OU
vercel --prod
```

### Rollback

**Railway:**
1. Dashboard → Deployments
2. Selecionar versão anterior → Redeploy

**Vercel:**
1. Dashboard → Deployments
2. Selecionar versão anterior → Promote to Production

---

## 📞 Suporte

**Erros de Deploy:**
- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs

**Integrações:**
- Stripe: https://stripe.com/docs
- Pluggy: https://docs.pluggy.ai

**Issues do Projeto:**
- GitHub Issues: [link do seu repo]
