-- ULTRA-DEEP ANALYSIS: Fix reports migration dependency issue
-- Problem: reports.0003 applied before its dependency reports.0002
-- Solution: Remove 0003, allow 0002 to apply, then reapply 0003

-- STEP 1: Check current state
SELECT app, name, applied FROM django_migrations 
WHERE app = 'reports' 
ORDER BY applied;

-- STEP 2: Remove the problematic migration 0003 from django_migrations
-- This allows Django to reapply it in correct order
DELETE FROM django_migrations 
WHERE app = 'reports' AND name = '0003_aianalysistemplate_aianalysis';

-- STEP 3: Verify removal
SELECT 'After removal:' as status;
SELECT app, name, applied FROM django_migrations 
WHERE app = 'reports' 
ORDER BY applied;

-- Note: After running this SQL, you need to run:
-- railway run python manage.py migrate reports
-- This will apply 0002 first, then 0003 in correct order

-- CRITICAL SAFEGUARD: 
-- The tables ai_analyses and ai_analysis_templates should already exist
-- from when 0003 was applied incorrectly. Migration 0002 only removes fields
-- that were already removed, so it should be safe to apply.