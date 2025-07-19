# 🚀 Deploy Guide - Railway

Este guia contém **todas as instruções** para fazer deploy do CaixaHub no Railway.

## 📋 Pré-requisitos

- [ ] Conta no [Railway](https://railway.app)
- [ ] Repositório no GitHub
- [ ] Conta no Stripe (para pagamentos)
- [ ] API Key do OpenAI
- [ ] Conta no Pluggy (Open Banking)

## 🏗️ Arquitetura do Deploy

```
Frontend (Next.js) ←→ Backend (Django) ←→ PostgreSQL
       ↓                    ↓               ↓
   Railway App         Railway App    Railway Addon
```

## 📦 1. Preparação do Código

O sistema já está preparado com:

✅ **Dockerfiles** otimizados  
✅ **railway.toml** configurado  
✅ **Health checks** implementados  
✅ **Environment variables** documentadas  
✅ **Database migrations** automáticas  

## 🚂 2. Deploy no Railway

### **2.1 Backend (Django)**

1. **Criar Projeto Backend:**
   ```bash
   # No Railway Dashboard
   New Project → Deploy from GitHub → Selecionar repositório
   ```

2. **Configurar Build:**
   - **Root Directory**: `backend`
   - **Build**: Railway detecta Dockerfile automaticamente
   - **Deploy**: Configurado via `railway.toml`

3. **Adicionar PostgreSQL:**
   ```bash
   # No projeto Railway
   Add Service → Database → PostgreSQL
   ```

4. **Adicionar Redis:**
   ```bash
   # No projeto Railway
   Add Service → Database → Redis
   ```

5. **Environment Variables:**
   
   Copie de `.env.example` e configure:
   
   ```bash
   SECRET_KEY=sua-chave-secreta-50-chars
   DEBUG=False
   DJANGO_SETTINGS_MODULE=core.settings.production
   ALLOWED_HOSTS=seu-backend.railway.app
   CORS_ALLOWED_ORIGINS=https://seu-frontend.railway.app
   FRONTEND_URL=https://seu-frontend.railway.app
   
   # OpenAI
   OPENAI_API_KEY=sk-sua-key
   
   # Pluggy
   PLUGGY_CLIENT_ID=seu-client-id
   PLUGGY_CLIENT_SECRET=seu-client-secret
   PLUGGY_USE_SANDBOX=true
   
   # Stripe
   STRIPE_SECRET_KEY=sk_test_sua-key
   STRIPE_PUBLIC_KEY=pk_test_sua-key
   STRIPE_WEBHOOK_SECRET=whsec_sua-key
   
   # Email (exemplo SendGrid)
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_PORT=587
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=sua-sendgrid-key
   DEFAULT_FROM_EMAIL=noreply@seudominio.com
   ```

   > **Nota**: Railway fornece automaticamente `DATABASE_URL` e `REDIS_URL`

### **2.2 Frontend (Next.js)**

1. **Criar Projeto Frontend:**
   ```bash
   # No Railway Dashboard
   New Project → Deploy from GitHub → Selecionar repositório
   ```

2. **Configurar Build:**
   - **Root Directory**: `frontend`
   - **Build**: Railway detecta Dockerfile automaticamente

3. **Environment Variables:**
   
   ```bash
   # API Backend
   NEXT_PUBLIC_API_URL=https://seu-backend.railway.app
   
   # App Configuration
   NEXT_PUBLIC_APP_NAME=CaixaHub
   NEXT_PUBLIC_APP_URL=https://seu-frontend.railway.app
   
   # Stripe (chave pública)
   NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_sua-key
   ```

## ⚙️ 3. Configuração Final

### **3.1 Domains & SSL**

Railway fornece automaticamente:
- **SSL gratuito** para domínios `.railway.app`
- **Custom domains** (opcional): Configure DNS para seus domínios

### **3.2 Verificar Deploy**

1. **Backend Health Check:**
   ```bash
   curl https://seu-backend.railway.app/api/health/
   ```

2. **Frontend Load:**
   ```bash
   curl https://seu-frontend.railway.app/
   ```

3. **Database Migration:**
   ```bash
   # Railway executa automaticamente:
   python manage.py migrate
   python manage.py seed_plans
   ```

## 🔧 4. Configurações Específicas

### **4.1 Webhooks do Stripe**

1. **Endpoint URL:**
   ```
   https://seu-backend.railway.app/api/payments/stripe/webhook/
   ```

2. **Events to send:**
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`

### **4.2 Pluggy Callback URL**

Configure no dashboard Pluggy:
```
https://seu-frontend.railway.app/banking/callback
```

### **4.3 CORS Configuration**

Verifique se as variáveis estão corretas:
```bash
ALLOWED_HOSTS=seu-backend.railway.app
CORS_ALLOWED_ORIGINS=https://seu-frontend.railway.app
```

## 📊 5. Monitoramento

### **5.1 Logs em Tempo Real**
```bash
# Railway CLI
railway logs --service backend
railway logs --service frontend
```

### **5.2 Health Checks**

Railway monitora automaticamente:
- **Backend**: `/api/health/` (Database + Redis + Environment)
- **Frontend**: `/` (Next.js ready check)

### **5.3 Alerts**

Configure no Railway Dashboard:
- **Deploy failures**
- **Service downtime**
- **Resource usage**

## 🚀 6. Deploy Workflow

### **Desenvolvimento → Produção**

```bash
# 1. Desenvolver localmente
git checkout -b nova-feature
# ... código ...

# 2. Commit e push
git add .
git commit -m "feat: nova funcionalidade"
git push origin nova-feature

# 3. Merge para main
git checkout main
git merge nova-feature
git push origin main

# 4. Railway deploy automático! 🎉
# ✅ Backend deploy (2-3 min)
# ✅ Frontend deploy (1-2 min)
# ✅ Database migration automática
# ✅ Zero downtime
```

## 🛠️ 7. Troubleshooting

### **Deploy Falhou?**

1. **Check Logs:**
   ```bash
   railway logs --service backend
   ```

2. **Variáveis de Ambiente:**
   - Verificar se todas estão configuradas
   - Testar health check: `/api/health/`

3. **Database Issues:**
   ```bash
   # Verificar conexão
   railway run python manage.py dbshell
   ```

### **Frontend não carrega?**

1. **API URL incorreta:**
   ```bash
   # Verificar variável
   NEXT_PUBLIC_API_URL=https://seu-backend.railway.app
   ```

2. **CORS Error:**
   ```bash
   # Verificar no backend
   CORS_ALLOWED_ORIGINS=https://seu-frontend.railway.app
   ```

## 💰 8. Custos Railway

| Plano | Preço | Recursos |
|-------|-------|----------|
| **Hobby** | $5/mês | 1 projeto, execução limitada |
| **Pro** | $20/mês | Projetos ilimitados, execução completa |

**Estimate para CaixaHub:**
- **Backend**: ~$15-25/mês
- **Frontend**: ~$10-15/mês
- **PostgreSQL**: Incluído
- **Redis**: Incluído
- **Total**: ~$25-40/mês

## ✅ 9. Checklist Final

Antes de ir live:

- [ ] ✅ Backend health check funcionando
- [ ] ✅ Frontend carregando
- [ ] ✅ Database migrations aplicadas
- [ ] ✅ Planos de assinatura criados (`seed_plans`)
- [ ] ✅ Stripe webhooks configurados
- [ ] ✅ Pluggy callback URL configurado
- [ ] ✅ Email templates funcionando
- [ ] ✅ CORS configurado corretamente
- [ ] ✅ SSL funcionando
- [ ] ✅ Logs sendo capturados
- [ ] ✅ Monitoring ativo

## 🎯 Próximos Passos

Após deploy:

1. **Custom Domain** (opcional)
2. **CDN** para assets estáticos
3. **Backup** estratégia para database
4. **Monitoring** avançado (Sentry)
5. **Analytics** (Google Analytics)

---

## 🆘 Suporte

**Issues comuns e soluções:** 

- **500 Error**: Verificar logs e variáveis de ambiente
- **CORS Error**: Verificar `CORS_ALLOWED_ORIGINS`
- **Database Error**: Verificar `DATABASE_URL` automático do Railway
- **Build Error**: Verificar Dockerfile e dependências

**Railway funciona muito bem para Django + Next.js!** 🎉