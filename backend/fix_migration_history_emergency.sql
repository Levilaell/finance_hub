-- CORREÇÃO EMERGENCIAL - InconsistentMigrationHistory
-- Execute IMEDIATAMENTE via Railway shell

-- 1. VERIFICAR ESTADO ATUAL
SELECT app, name, applied 
FROM django_migrations 
WHERE app = 'companies' 
AND name IN ('0008_alter_resourceusage_options_and_more', '0009_add_early_access')
ORDER BY name;

-- 2. MARCAR 0008 COMO APLICADA (fake apply)
-- Isso resolve o erro de dependência inconsistente
INSERT INTO django_migrations (app, name, applied) 
VALUES ('companies', '0008_alter_resourceusage_options_and_more', NOW())
ON CONFLICT (app, name) DO NOTHING;

-- 3. VERIFICAR CORREÇÃO
SELECT app, name, applied 
FROM django_migrations 
WHERE app = 'companies' 
AND name IN ('0008_alter_resourceusage_options_and_more', '0009_add_early_access')
ORDER BY name;

-- 4. VERIFICAR SE PODE PROSSEGUIR
\echo '✅ HISTÓRICO DE MIGRAÇÃO CORRIGIDO'
\echo 'Execute: python manage.py migrate para continuar'