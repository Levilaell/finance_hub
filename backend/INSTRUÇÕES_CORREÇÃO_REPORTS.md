# CORREÇÃO URGENTE - App Reports Migration Order

## Problema Identificado
```
InconsistentMigrationHistory: Migration reports.0003_aianalysistemplate_aianalysis is applied before its dependency reports.0002_alter_aianalysis_options_and_more
```

## Solução Preparada
Criados scripts para corrigir ordem dos timestamps das migrações do app `reports`.

## Instruções de Execução

### Opção 1: Script Python (Recomendado)
```bash
# 1. Conectar ao Railway
railway login

# 2. Executar script de correção
railway run python fix_reports_migration_order.py
```

### Opção 2: SQL Direto via psql
```bash
# 1. Conectar ao banco
railway connect

# 2. Executar comando SQL (dentro do psql)
\i fix_reports_migration_order.sql
```

### Opção 3: Railway Shell + SQL Manual
```bash
# 1. Abrir shell do Railway
railway shell

# 2. Conectar ao banco
psql $DATABASE_URL

# 3. Executar comandos (um por vez):
SELECT app, name, applied FROM django_migrations WHERE app = 'reports' AND name IN ('0002_alter_aianalysis_options_and_more', '0003_aianalysistemplate_aianalysis') ORDER BY applied;

UPDATE django_migrations SET applied = '2025-08-12 02:00:00+00' WHERE app = 'reports' AND name = '0002_alter_aianalysis_options_and_more';

UPDATE django_migrations SET applied = '2025-08-12 02:30:00+00' WHERE app = 'reports' AND name = '0003_aianalysistemplate_aianalysis';

SELECT app, name, applied FROM django_migrations WHERE app = 'reports' AND name IN ('0002_alter_aianalysis_options_and_more', '0003_aianalysistemplate_aianalysis') ORDER BY applied;
```

## Resultado Esperado
Após a correção, as migrações devem ficar na ordem:
1. `reports.0002_alter_aianalysis_options_and_more` (02:00:00)
2. `reports.0003_aianalysistemplate_aianalysis` (02:30:00)

## Próximos Passos
1. ✅ Executar uma das opções de correção acima
2. 🚀 Fazer novo deploy: `railway deploy`
3. 📋 Verificar se o deploy é bem-sucedido
4. ⚠️  Se aparecer outro erro de migração, repetir o processo para o próximo app

## Observações
- Esta é a mesma metodologia usada para corrigir `auth`, `companies`, `banking`, `authentication`
- A correção é segura e não afeta dados, apenas reordena timestamps
- Após esta correção, pode haver outros apps com problemas similares