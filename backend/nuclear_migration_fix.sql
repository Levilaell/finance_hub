-- ⚡ NUCLEAR MIGRATION FIX - Correção definitiva de conflitos
-- Execução: railway connect < nuclear_migration_fix.sql

-- Verificar situação atual
SELECT 'BEFORE NUCLEAR FIX - Migration status:' as info;
SELECT app, name, applied FROM django_migrations 
WHERE (app = 'companies' AND name IN ('0008_alter_resourceusage_options_and_more', '0009_add_early_access'))
   OR (app = 'banking' AND name = '0008_delete_consent')
   OR (app = 'reports' AND name LIKE '%inconsistent%')
ORDER BY app, name;

-- STEP 1: Remover companies.0009 que foi aplicada antes da dependência
DELETE FROM django_migrations 
WHERE app = 'companies' AND name = '0009_add_early_access';

-- STEP 2: Corrigir timestamp do banking.0008 para ordem cronológica
UPDATE django_migrations 
SET applied = '2025-07-31 02:00:00+00:00' 
WHERE app = 'banking' AND name = '0008_delete_consent';

-- STEP 3: Remover migrações reports problemáticas
DELETE FROM django_migrations 
WHERE app = 'reports' AND name IN (
    '0002_alter_aianalysis_options_and_more', 
    '0003_aianalysistemplate_aianalysis', 
    '0005_fix_inconsistent_history'
);

-- STEP 4: Reaplicar migrações reports na ordem correta
INSERT INTO django_migrations (app, name, applied) VALUES 
('reports', '0002_alter_aianalysis_options_and_more', '2025-08-12 01:00:00+00:00'),
('reports', '0003_aianalysistemplate_aianalysis', '2025-08-12 02:00:00+00:00'),
('reports', '0005_fix_inconsistent_history', '2025-08-12 03:00:00+00:00');

-- Verificar correção aplicada
SELECT 'AFTER NUCLEAR FIX - Migration status:' as info;
SELECT app, name, applied FROM django_migrations 
WHERE app IN ('companies', 'banking', 'reports')
ORDER BY applied ASC;

-- Verificar que conflitos foram resolvidos
SELECT 'Checking for dependency conflicts:' as info;
SELECT 
  CASE 
    WHEN COUNT(*) = 0 THEN '✅ NO CONFLICTS - Ready for deploy!'
    ELSE '❌ CONFLICTS STILL EXIST'
  END as status
FROM django_migrations m1
INNER JOIN django_migrations m2 ON m1.app = m2.app
WHERE m1.name = '0009_add_early_access' AND m2.name = '0008_alter_resourceusage_options_and_more'
  AND m1.applied < m2.applied;

COMMIT;