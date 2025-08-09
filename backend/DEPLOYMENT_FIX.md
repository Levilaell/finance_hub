# Railway Deployment Fix - Resolução de Erros Críticos

## Problemas Identificados

### 1. InconsistentMigrationHistory
**Erro**: `Migration reports.0003_aianalysistemplate_aianalysis is applied before its dependency reports.0002_alter_aianalysis_options_and_more`

**Causa**: As migrações foram aplicadas fora de ordem no banco de produção.

### 2. Health Check Retornando 301
**Erro**: Endpoint `/health/` retornando 301 (redirect) ao invés de 200

**Causa**: `SECURE_SSL_REDIRECT=True` forçava redirect HTTPS, mas Railway já faz SSL termination na edge.

### 3. Tabela "users" não existe
**Erro**: `relation "users" does not exist`

**Causa**: Migrações não conseguiam rodar devido ao erro de inconsistência.

## Soluções Implementadas

### 1. Correção de Migrações Duplicadas
- **Removido**: `0004_fix_migration_order.py` (duplicado)
- **Mantido**: `0004_merge_20250803_2225.py` (oficial)
- **Criado**: `0005_fix_inconsistent_history.py` para corrigir o histórico

### 2. Desabilitado SSL Redirect
- **Arquivo**: `core/settings/production.py`
- **Mudança**: `SECURE_SSL_REDIRECT` agora padrão `False`
- **Razão**: Railway já faz SSL termination, redirect causa loop

### 3. Script start.sh Melhorado
- **Detecta** inconsistências de migração automaticamente
- **Corrige** inserindo registros faltantes no django_migrations
- **Tenta** fake migrations se necessário
- **Continua** mesmo com erros para não quebrar deploy

### 4. Comando de Management
- **Criado**: `fix_migration_history` comando
- **Uso**: `python manage.py fix_migration_history`
- **Função**: Diagnostica e corrige problemas de migração

## Como Fazer Deploy

1. **Commit das mudanças**:
```bash
git add .
git commit -m "fix: resolver erros críticos de deployment no Railway"
git push
```

2. **No Railway Dashboard**:
- Deploy automático deve iniciar
- Monitore os logs para verificar se as correções funcionaram

3. **Se ainda houver problemas**:
- Acesse o shell do Railway
- Execute: `python manage.py fix_migration_history`
- Execute: `python manage.py migrate --fake reports 0002`

## Variáveis de Ambiente Necessárias

Certifique-se de que estas estão configuradas no Railway:

- `DJANGO_SECRET_KEY`: Chave secreta do Django
- `DATABASE_URL`: URL do PostgreSQL (use referência ao serviço)
- `ALLOWED_HOSTS`: Domínio do Railway (auto-detectado se não definido)
- `SECURE_SSL_REDIRECT`: Deixe como False ou não defina

## Monitoramento

Após deploy, verifique:

1. **Health Check**: `https://seu-app.railway.app/health/`
   - Deve retornar 200 com JSON
   - Não deve redirecionar

2. **Admin**: `https://seu-app.railway.app/admin/`
   - Deve carregar sem erros

3. **API Root**: `https://seu-app.railway.app/api/`
   - Deve mostrar endpoints disponíveis

## Comandos Úteis

```bash
# Verificar migrações
python manage.py showmigrations reports

# Corrigir histórico
python manage.py fix_migration_history

# Forçar migração específica
python manage.py migrate reports 0002 --fake

# Resetar todas as migrações do reports (CUIDADO!)
python manage.py migrate reports zero --fake
python manage.py migrate reports
```