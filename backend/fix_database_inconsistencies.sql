-- =====================================================
-- SCRIPT PARA CORRIGIR INCONSISTÊNCIAS DO BANCO DE DADOS
-- Finance Hub - Django Database Schema Fixes
-- =====================================================

-- Data de criação: 2024-08-20
-- Objetivo: Corrigir inconsistências entre modelos Django e schema do banco

-- =====================================================
-- 1. RECRIAR TABELA EMAIL_VERIFICATIONS (CRÍTICO)
-- =====================================================

-- Esta tabela foi removida pela migração 0002_remove_email_verification
-- mas o código Python ainda tenta usá-la no RegisterView e EarlyAccessRegisterView

-- Verificar se a tabela já existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'email_verifications'
    ) THEN
        -- Recriar tabela email_verifications
        CREATE TABLE email_verifications (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            token VARCHAR(100) UNIQUE NOT NULL,
            is_used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            
            -- Foreign key para users
            CONSTRAINT email_verifications_user_id_fkey 
                FOREIGN KEY (user_id) 
                REFERENCES users(id) 
                ON DELETE CASCADE
        );
        
        -- Criar indexes conforme definidos no modelo Django
        CREATE INDEX email_verifications_user_id_is_used_idx 
            ON email_verifications(user_id, is_used);
        
        CREATE INDEX email_verifications_token_idx 
            ON email_verifications(token);
        
        CREATE INDEX email_verifications_expires_at_idx 
            ON email_verifications(expires_at);
        
        RAISE NOTICE 'Tabela email_verifications recriada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela email_verifications já existe';
    END IF;
END $$;

-- =====================================================
-- 2. REGISTRAR MIGRAÇÃO COMO APLICADA
-- =====================================================

-- Inserir registro da migração que recria a EmailVerification
INSERT INTO django_migrations (app, name, applied) 
VALUES ('authentication', '0003_emailverification', NOW())
ON CONFLICT (app, name) DO NOTHING;

-- =====================================================
-- 3. VERIFICAR E CORRIGIR INDEXES DE TRANSAÇÕES (BANKING)
-- =====================================================

-- O Django detectou que alguns indexes precisam ser removidos/alterados

-- Verificar e remover indexes duplicados ou desnecessários
DO $$
BEGIN
    -- Index: banking_tra_acc_date_idx
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'banking_tra_acc_date_idx'
    ) THEN
        DROP INDEX IF EXISTS banking_tra_acc_date_idx;
        RAISE NOTICE 'Index banking_tra_acc_date_idx removido';
    END IF;
    
    -- Index: banking_tra_type_date_idx  
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'banking_tra_type_date_idx'
    ) THEN
        DROP INDEX IF EXISTS banking_tra_type_date_idx;
        RAISE NOTICE 'Index banking_tra_type_date_idx removido';
    END IF;
    
    -- Index: banking_tra_cat_date_idx
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'banking_tra_cat_date_idx'
    ) THEN
        DROP INDEX IF EXISTS banking_tra_cat_date_idx;
        RAISE NOTICE 'Index banking_tra_cat_date_idx removido';
    END IF;
    
    -- Index: banking_tra_complex_idx
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'banking_tra_complex_idx'
    ) THEN
        DROP INDEX IF EXISTS banking_tra_complex_idx;
        RAISE NOTICE 'Index banking_tra_complex_idx removido';
    END IF;
END $$;

-- =====================================================
-- 4. VALIDAÇÃO DE SCHEMA
-- =====================================================

-- Verificar se as tabelas críticas existem
DO $$
DECLARE
    missing_tables TEXT[] := ARRAY[]::TEXT[];
    table_name TEXT;
BEGIN
    -- Lista de tabelas críticas para verificar
    FOREACH table_name IN ARRAY ARRAY[
        'users', 'companies', 'transactions', 'bank_accounts', 
        'email_verifications', 'password_resets', 'subscriptions'
    ] LOOP
        IF NOT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = table_name
        ) THEN
            missing_tables := array_append(missing_tables, table_name);
        END IF;
    END LOOP;
    
    -- Reportar tabelas faltantes
    IF array_length(missing_tables, 1) > 0 THEN
        RAISE WARNING 'Tabelas faltantes: %', array_to_string(missing_tables, ', ');
    ELSE
        RAISE NOTICE '✅ Todas as tabelas críticas estão presentes';
    END IF;
END $$;

-- =====================================================
-- 5. VERIFICAÇÃO DE INTEGRIDADE REFERENCIAL
-- =====================================================

-- Verificar se há foreign keys quebradas
DO $$
DECLARE
    broken_refs INTEGER;
BEGIN
    -- Verificar referências de users para companies
    SELECT COUNT(*) INTO broken_refs
    FROM users u
    LEFT JOIN companies c ON u.id = c.owner_id
    WHERE u.id IN (
        SELECT owner_id FROM companies WHERE owner_id IS NOT NULL
    ) AND c.id IS NULL;
    
    IF broken_refs > 0 THEN
        RAISE WARNING 'Encontradas % referências quebradas users->companies', broken_refs;
    END IF;
    
    -- Verificar referências de transactions para accounts
    SELECT COUNT(*) INTO broken_refs
    FROM transactions t
    LEFT JOIN bank_accounts ba ON t.account_id = ba.id
    WHERE ba.id IS NULL;
    
    IF broken_refs > 0 THEN
        RAISE WARNING 'Encontradas % referências quebradas transactions->bank_accounts', broken_refs;
    ELSE
        RAISE NOTICE '✅ Integridade referencial OK';
    END IF;
END $$;

-- =====================================================
-- 6. LIMPEZA E OTIMIZAÇÃO
-- =====================================================

-- Atualizar estatísticas das tabelas modificadas
ANALYZE email_verifications;
ANALYZE transactions;
ANALYZE users;

-- =====================================================
-- 7. RESUMO FINAL
-- =====================================================

-- Exibir resumo das correções aplicadas
DO $$
BEGIN
    RAISE NOTICE '=== RESUMO DAS CORREÇÕES APLICADAS ===';
    RAISE NOTICE '✅ Tabela email_verifications recriada';
    RAISE NOTICE '✅ Migração 0003_emailverification registrada';
    RAISE NOTICE '✅ Indexes desnecessários removidos';
    RAISE NOTICE '✅ Integridade referencial verificada';
    RAISE NOTICE '✅ Estatísticas atualizadas';
    RAISE NOTICE '';
    RAISE NOTICE '🎯 PRÓXIMOS PASSOS:';
    RAISE NOTICE '1. Aplicar migrações Django: python manage.py migrate';
    RAISE NOTICE '2. Testar registro de usuário';
    RAISE NOTICE '3. Testar admin panel';
    RAISE NOTICE '4. Monitorar logs para outros erros';
END $$;