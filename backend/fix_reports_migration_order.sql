-- CORREÇÃO DE ORDEM DAS MIGRAÇÕES - APP REPORTS
-- Erro: reports.0003 aplicada antes da dependência reports.0002

-- 1. Verificar estado atual
SELECT app, name, applied 
FROM django_migrations 
WHERE app = 'reports' AND name IN ('0002_alter_aianalysis_options_and_more', '0003_aianalysistemplate_aianalysis')
ORDER BY applied;

-- 2. Corrigir timestamps para ordem correta (0002 antes de 0003)
UPDATE django_migrations 
SET applied = '2025-08-12 02:00:00+00'
WHERE app = 'reports' AND name = '0002_alter_aianalysis_options_and_more';

UPDATE django_migrations 
SET applied = '2025-08-12 02:30:00+00'
WHERE app = 'reports' AND name = '0003_aianalysistemplate_aianalysis';

-- 3. Verificar correção
SELECT app, name, applied 
FROM django_migrations 
WHERE app = 'reports' AND name IN ('0002_alter_aianalysis_options_and_more', '0003_aianalysistemplate_aianalysis')
ORDER BY applied;

-- 4. Validar todas as migrações do reports estão em ordem
SELECT app, name, applied 
FROM django_migrations 
WHERE app = 'reports'
ORDER BY applied;

-- Resultado esperado:
-- reports | 0001_initial | [timestamp anterior]
-- reports | 0002_alter_aianalysis_options_and_more | 2025-08-12 02:00:00+00
-- reports | 0003_aianalysistemplate_aianalysis | 2025-08-12 02:30:00+00
-- reports | [outras migrações] | [timestamps posteriores]