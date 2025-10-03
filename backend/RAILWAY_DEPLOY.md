# 🚂 Railway Deploy - Troubleshooting

## ✅ Arquivos Necessários

Certifique-se que estes arquivos existem:
- [x] `requirements.txt`
- [x] `Procfile`
- [x] `runtime.txt`
- [x] `nixpacks.toml`
- [x] `railway.json`
- [x] `start.sh`
- [x] `manage.py`

## 🔧 Configuração Mínima no Railway

### 1. Variáveis de Ambiente Obrigatórias

No Railway Dashboard → Variables, adicione:

```bash
# Essencial para build
DJANGO_ENV=production
DJANGO_SETTINGS_MODULE=core.settings.production
PYTHONUNBUFFERED=1

# Database (auto-configurado se usar Railway PostgreSQL)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Secrets (GERAR NOVOS!)
DJANGO_SECRET_KEY=<usar-comando-abaixo>
JWT_SECRET_KEY=<usar-comando-abaixo>

# Frontend
FRONTEND_URL=https://seu-frontend.vercel.app
```

### 2. Gerar Secret Keys

```bash
# Django Secret Key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# JWT Secret Key
python -c 'import secrets; print(secrets.token_urlsafe(50))'
```

## 🐛 Erros Comuns e Soluções

### ❌ "Failed to find your WSGI_APPLICATION"

**Causa:** Nixpacks não detectou WSGI_APPLICATION

**Solução:**
```bash
# Arquivo base.py deve ter:
WSGI_APPLICATION = 'core.wsgi.application'
```

✅ **RESOLVIDO** - Já configurado em `core/settings/base.py:56`

### ❌ "ModuleNotFoundError: No module named 'X'"

**Causa:** Dependência não instalada

**Solução:**
```bash
# Verificar requirements.txt contém a dependência
# Fazer rebuild no Railway
```

### ❌ "DJANGO_SECRET_KEY not set"

**Causa:** Variável de ambiente não configurada

**Solução:**
```bash
# No Railway Dashboard → Variables:
DJANGO_SECRET_KEY=<secret-gerado>
```

### ❌ "Database connection failed"

**Causa:** DATABASE_URL incorreto ou PostgreSQL não conectado

**Solução:**
1. Railway Dashboard → Add PostgreSQL
2. Verificar variável: `DATABASE_URL=${{Postgres.DATABASE_URL}}`
3. Aguardar 1-2 minutos para propagação

### ❌ "Static files not found"

**Causa:** collectstatic falhou ou STATIC_ROOT incorreto

**Solução:**
```bash
# O start.sh já executa collectstatic
# Verificar logs: railway logs
```

### ❌ "Worker timeout" / "Application startup timeout"

**Causa:** Aplicação demora muito para iniciar

**Solução:**
```bash
# No railway.json, aumentar timeout:
"healthcheckTimeout": 300  # 5 minutos
```

### ❌ "502 Bad Gateway"

**Causa:** Aplicação não respondendo na porta correta

**Solução:**
```bash
# Verificar que start.sh usa $PORT:
--bind 0.0.0.0:$PORT

# Railway configura PORT automaticamente
```

## 📊 Checklist de Deploy

### Antes do Deploy
- [ ] `WSGI_APPLICATION` configurado em settings
- [ ] Todos os arquivos de configuração criados
- [ ] `.env.example` revisado
- [ ] Secrets gerados (não usar exemplos!)

### Durante o Deploy
- [ ] PostgreSQL adicionado no Railway
- [ ] Variáveis de ambiente configuradas
- [ ] Build completo com sucesso
- [ ] Migrations executadas

### Após o Deploy
- [ ] Health check passou: `/admin/login/`
- [ ] Criar superuser: `railway run python manage.py createsuperuser`
- [ ] Testar login no admin
- [ ] Configurar webhooks (Stripe, Pluggy)

## 🔍 Verificação de Deploy

### 1. Build Logs
```bash
railway logs --deployment
```

Procure por:
- ✅ `Successfully installed <packages>`
- ✅ `Running migrations...`
- ✅ `Migrations completed`
- ✅ `Starting Gunicorn server`

### 2. Runtime Logs
```bash
railway logs
```

Procure por:
- ✅ `Starting Finance Hub Backend`
- ✅ `Database connection successful`
- ✅ `Listening at: http://0.0.0.0:PORT`
- ❌ Erros de importação
- ❌ Database errors

### 3. Health Check
```bash
curl https://seu-app.railway.app/admin/login/
```

Deve retornar: `200 OK`

## 🚀 Deploy Rápido (Comandos)

```bash
# 1. Conectar projeto
railway link

# 2. Adicionar PostgreSQL
railway add postgresql

# 3. Configurar env vars (interativo)
railway variables set DJANGO_SECRET_KEY=<secret>
railway variables set JWT_SECRET_KEY=<secret>
railway variables set FRONTEND_URL=<url>

# 4. Deploy
railway up

# 5. Ver logs
railway logs

# 6. Criar superuser
railway run python manage.py createsuperuser
```

## 📞 Suporte

**Logs completos:**
```bash
railway logs --json > deploy-logs.json
```

**Verificar variáveis:**
```bash
railway variables
```

**Restart:**
```bash
railway restart
```

**Rollback:**
```bash
# Via Dashboard: Deployments → Select previous → Redeploy
```

## 🔗 Links Úteis

- [Railway Docs](https://docs.railway.app)
- [Nixpacks Python](https://nixpacks.com/docs/providers/python)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
