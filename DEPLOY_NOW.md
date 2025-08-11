# 🚀 Deploy Imediato no Railway - Passo a Passo

## ✅ Checklist Pré-Deploy

- [ ] Railway CLI instalado (`npm install -g @railway/cli`)
- [ ] Conta Railway criada e configurada
- [ ] Projeto Railway criado
- [ ] PostgreSQL e Redis adicionados ao projeto
- [ ] Variáveis de ambiente configuradas

## 📝 Passos para Deploy

### 1️⃣ Configurar Variáveis de Ambiente

```bash
# Opção A: Usar script automatizado
cd deploy
chmod +x setup-railway-env.sh
./setup-railway-env.sh

# Opção B: Copiar manualmente no Railway Dashboard
# Usar as variáveis do arquivo .env prod fornecido
```

### 2️⃣ Fazer Deploy via GitHub

```bash
# Commit das mudanças
git add .
git commit -m "feat: complete deployment automation for Railway"
git push origin main
```

### 3️⃣ Deploy Manual (Alternativa)

```bash
# Login no Railway
railway login

# Linkar projeto
railway link

# Deploy backend
railway up

# Verificar logs
railway logs
```

## 🔧 Comandos Úteis

```bash
# Ver status
railway status

# Ver logs em tempo real
railway logs --tail

# Executar comandos
railway run python manage.py migrate
railway run python manage.py createsuperuser

# Rollback se necessário
railway rollback
```

## 🚨 Troubleshooting Rápido

### Erro de Migração
```bash
railway run python manage.py migrate --fake-initial
```

### Erro de Static Files
```bash
railway run python manage.py collectstatic --noinput
```

### Verificar Health
```bash
curl https://finance-backend-production-29df.up.railway.app/api/health/
```

## 📊 URLs de Produção

- **Backend**: https://finance-backend-production-29df.up.railway.app
- **Frontend**: https://finance-frontend-production-24be.up.railway.app
- **Domínio Principal**: https://caixahub.com.br

## ✅ Validação Pós-Deploy

1. Acessar `/api/health/` - deve retornar 200 OK
2. Acessar frontend - deve carregar normalmente
3. Testar login/registro
4. Verificar integração com Stripe
5. Testar conexão bancária Pluggy

## 🔄 Próximos Passos

1. Configurar domínio customizado no Railway
2. Ativar SSL/HTTPS
3. Configurar monitoramento (Sentry)
4. Configurar backups automáticos
5. Revisar limites de rate limiting

---

**Suporte**: Em caso de problemas, verificar `DEPLOYMENT_GUIDE.md` para documentação completa.