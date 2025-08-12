-- SCRIPT DE RESET COMPLETO DO BANCO DE PRODUÇÃO
-- Este script vai DELETAR TODOS OS DADOS!

-- 1. Desconectar outras sessões
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = current_database() 
  AND pid <> pg_backend_pid();

-- 2. Dropar TODAS as tabelas
DO $$ 
DECLARE
    r RECORD;
BEGIN
    -- Desabilitar verificação de foreign keys
    SET session_replication_role = 'replica';
    
    -- Listar e dropar todas as tabelas
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') 
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
        RAISE NOTICE 'Dropped table: %', r.tablename;
    END LOOP;
    
    -- Reabilitar verificação de foreign keys
    SET session_replication_role = 'default';
END $$;

-- 3. Confirmar que todas as tabelas foram removidas
SELECT 'Tables remaining: ' || COUNT(*) as status 
FROM pg_tables 
WHERE schemaname = 'public';

-- 4. Limpar qualquer sequência órfã
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT sequencename FROM pg_sequences WHERE schemaname = 'public')
    LOOP
        EXECUTE 'DROP SEQUENCE IF EXISTS public.' || quote_ident(r.sequencename) || ' CASCADE';
    END LOOP;
END $$;

-- Mensagem final
SELECT 'DATABASE RESET COMPLETE - All tables and sequences have been dropped!' as result;