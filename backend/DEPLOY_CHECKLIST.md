# 🚀 CHECKLIST DE DEPLOY RAILWAY - FINANCE HUB

## ⚠️ PROBLEMAS CRÍTICOS IDENTIFICADOS

### 1. **Collation Version Mismatch** (ALTA PRIORIDADE)
- **Sintoma**: `database "railway" has a collation version mismatch`
- **Causa**: PostgreSQL atualizado de v2.36 para v2.41
- **Impacto**: Migrações com índices podem falhar

### 2. **Notifications Migrations Missing** (MÉDIO)
- **Problema**: Tabela tem schema novo mas migrações 0002/0003 não existem
- **Impacto**: Fresh deploy pode falhar

### 3. **Encryption Key Missing** (SEGURANÇA)
- **Warning**: AI_INSIGHTS_ENCRYPTION_KEY não configurado
- **Impacto**: MFA params usando fallback inseguro

---

## 📋 PRÉ-DEPLOY (OBRIGATÓRIO)

### 1. **Backup de Segurança**
```bash
railway run pg_dump > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. **Verificar Migrações Pendentes**
```bash
railway shell
python manage.py showmigrations | grep '\\[ \\]'
```

### 3. **Corrigir Collation Version**
```bash
railway shell
psql $DATABASE_URL -c "ALTER DATABASE railway REFRESH COLLATION VERSION;"
```

### 4. **Configurar Variáveis de Ambiente**
Railway Dashboard → Variables:
```
AI_INSIGHTS_ENCRYPTION_KEY=<32-char-base64-key>
PLUGGY_WEBHOOK_SECRET=<24-char-base64-key>
```

---

## 🚀 DEPLOY

### 1. **Deploy Principal**
```bash
git push railway main
```
Railway auto-executa: `python manage.py migrate`

### 2. **Monitorar Deploy**
```bash
railway logs
```
Buscar por: `error`, `fail`, `migration`

---

## ✅ PÓS-DEPLOY (VALIDAÇÃO)

### 1. **Validação Automática**
```bash
railway shell
python validate_production_migrations.py
```

### 2. **Smoke Tests**
```bash
# Health check
curl -f https://financehub-production.up.railway.app/api/health/

# Admin access
curl -f https://financehub-production.up.railway.app/admin/

# Frontend
curl -f https://caixahub.com.br/
```

### 3. **Verificação Manual**
- [ ] Login funciona
- [ ] Dashboard carrega
- [ ] Conectar banco funciona
- [ ] Sincronização funciona
- [ ] Relatórios funcionam

---

## 🚨 PLANO DE EMERGÊNCIA

### Se Deploy Falhar:

1. **Rollback Imediato**
```bash
railway rollback
```

2. **Ou Rollback Específico**
```bash
railway shell
python manage.py migrate <app> <migration_anterior>
```

3. **Verificar Logs**
```bash
railway logs | grep -A5 -B5 error
```

---

## 📊 MONITORAMENTO (24H)

### Métricas a Acompanhar:
- [ ] Taxa de erro < 1%
- [ ] Response time < 500ms
- [ ] Database collation warnings eliminados
- [ ] Encryption warnings eliminados
- [ ] Funcionalidades críticas OK

### Alerts:
- [ ] Configurar alertas para erros de migração
- [ ] Monitor de performance de queries
- [ ] Alert para high error rate

---

## 🎯 STATUS ATUAL

✅ **Scripts Criados**:
- `fix_railway_production.sql` - Correção SQL
- `validate_production_migrations.py` - Validação completa
- `railway_deploy_commands.sh` - Comandos automatizados

⚠️ **Ação Requerida do Usuário**:
- Configurar variáveis de ambiente no Railway
- Executar correção de collation
- Monitorar deploy