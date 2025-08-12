-- Script SQL para resetar completamente o banco de produção
-- ATENÇÃO: Isso vai APAGAR TODOS OS DADOS!

-- Desconectar todas as conexões ativas
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = current_database() 
  AND pid <> pg_backend_pid();

-- Deletar todas as tabelas
DO $$ 
DECLARE
    r RECORD;
BEGIN
    -- Desabilitar checagem de foreign keys temporariamente
    EXECUTE 'SET session_replication_role = replica';
    
    -- Deletar todas as tabelas
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') 
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
    
    -- Reabilitar checagem de foreign keys
    EXECUTE 'SET session_replication_role = DEFAULT';
END $$;

-- Mensagem de confirmação
SELECT 'Database reset complete. All tables have been dropped.' as status;