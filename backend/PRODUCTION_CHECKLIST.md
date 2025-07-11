# 📋 Checklist de Produção - CaixaHub

## ✅ Funcionalidades Core
- [ ] Autenticação e autorização funcionando
- [ ] Dashboard com métricas corretas
- [ ] Conexão bancária via Pluggy testada
- [ ] Sincronização de transações
- [ ] Categorização automática
- [ ] Relatórios básicos

## 🔐 Segurança
- [ ] Variáveis de ambiente configuradas
- [ ] Secrets seguros (não hardcoded)
- [ ] HTTPS configurado
- [ ] CORS configurado corretamente
- [ ] Rate limiting ativo
- [ ] Backups automáticos

## 🏗️ Infraestrutura
- [ ] Banco de dados PostgreSQL
- [ ] Redis para cache/filas
- [ ] Storage para arquivos (S3 ou similar)
- [ ] Servidor de email configurado
- [ ] Monitoramento (Sentry, logs)

## 🔑 APIs e Integrações
- [ ] Pluggy API credentials (produção)
- [ ] Stripe/pagamento configurado
- [ ] Email service (SendGrid/SES)
- [ ] WhatsApp Business API (se aplicável)

## 📝 Configurações de Produção

### Backend (.env)
```env
# Django
SECRET_KEY=<gerar-nova-chave-segura>
DEBUG=False
ALLOWED_HOSTS=app.caixahub.com.br

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379/0

# Pluggy (obter em https://dashboard.pluggy.ai)
PLUGGY_CLIENT_ID=<seu-client-id-producao>
PLUGGY_CLIENT_SECRET=<seu-client-secret-producao>

# Email
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<sendgrid-api-key>

# Storage
AWS_ACCESS_KEY_ID=<aws-key>
AWS_SECRET_ACCESS_KEY=<aws-secret>
AWS_STORAGE_BUCKET_NAME=caixahub-prod

# Monitoring
SENTRY_DSN=<sentry-dsn>
```

### Frontend (.env.production)
```env
NEXT_PUBLIC_API_URL=https://api.caixahub.com.br
NEXT_PUBLIC_APP_URL=https://app.caixahub.com.br
```

## 🚀 Processo de Deploy

### 1. Preparação Local
```bash
# Backend
python manage.py test
python manage.py check --deploy
python manage.py collectstatic --noinput

# Frontend
npm run build
npm run test
```

### 2. Deploy Staging
```bash
# Testar em ambiente staging primeiro
git push staging main
# Executar testes E2E
# Validar integrações
```

### 3. Deploy Produção
```bash
# Apenas após validação em staging
git push production main
python manage.py migrate
python manage.py createsuperuser
```

## 📊 Pós-Deploy

- [ ] Verificar logs de erro
- [ ] Testar fluxo de registro
- [ ] Testar conexão bancária
- [ ] Monitorar performance
- [ ] Configurar alertas

## ⚠️ NÃO fazer em produção

- ❌ DEBUG=True
- ❌ Usar sqlite
- ❌ Credentials em código
- ❌ Desenvolver features
- ❌ Testes com dados reais sem backup