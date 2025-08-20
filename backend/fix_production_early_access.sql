-- =====================================================
-- SQL SCRIPT PARA CORRIGIR PRODUÇÃO - EARLY ACCESS
-- =====================================================
-- 
-- Este script adiciona os campos e tabelas necessários
-- para corrigir o erro de produção no Railway.
--
-- EXECUTAR EM PRODUÇÃO APENAS!
-- 
-- Erro: column "is_early_access" of relation "companies" does not exist
-- Solução: Aplicar manualmente a migração 0009_add_early_access.py
--
-- =====================================================

-- 1. ADICIONAR CAMPOS FALTANTES NA TABELA COMPANIES
-- =====================================================

-- Campo is_early_access (boolean, default false)
ALTER TABLE companies 
ADD COLUMN IF NOT EXISTS is_early_access BOOLEAN DEFAULT FALSE;

-- Campo early_access_expires_at (timestamp nullable)
ALTER TABLE companies 
ADD COLUMN IF NOT EXISTS early_access_expires_at TIMESTAMPTZ NULL;

-- Campo used_invite_code (varchar 20, blank permitido)
ALTER TABLE companies 
ADD COLUMN IF NOT EXISTS used_invite_code VARCHAR(20) DEFAULT '';

-- Comentários para documentação
COMMENT ON COLUMN companies.is_early_access IS 'Flag indicating if company has early access';
COMMENT ON COLUMN companies.early_access_expires_at IS 'When early access expires';
COMMENT ON COLUMN companies.used_invite_code IS 'Invite code used during registration';

-- 2. VERIFICAR E ATUALIZAR CONSTRAINT DE SUBSCRIPTION_STATUS
-- =====================================================

-- Primeiro, verificar se o constraint existe
DO $$
BEGIN
    -- Verificar se já existe o valor 'early_access' permitido
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name LIKE '%subscription_status%'
        AND check_clause LIKE '%early_access%'
    ) THEN
        -- Se não existe, precisamos atualizar o constraint
        -- Primeiro drop o constraint existente (se houver)
        ALTER TABLE companies DROP CONSTRAINT IF EXISTS companies_subscription_status_check;
        
        -- Adicionar novo constraint com 'early_access'
        ALTER TABLE companies ADD CONSTRAINT companies_subscription_status_check 
        CHECK (subscription_status IN ('trial', 'active', 'cancelled', 'expired', 'early_access'));
        
        RAISE NOTICE 'Constraint subscription_status atualizado com early_access';
    ELSE
        RAISE NOTICE 'Constraint subscription_status já inclui early_access';
    END IF;
END $$;

-- 3. CRIAR TABELA EARLY_ACCESS_INVITES
-- =====================================================

CREATE TABLE IF NOT EXISTS early_access_invites (
    id BIGSERIAL PRIMARY KEY,
    invite_code VARCHAR(20) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_used BOOLEAN DEFAULT FALSE NOT NULL,
    used_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    notes TEXT DEFAULT '' NOT NULL,
    created_by_id BIGINT NOT NULL,
    used_by_id BIGINT NULL,
    
    -- Foreign keys
    CONSTRAINT early_access_invites_created_by_fk 
        FOREIGN KEY (created_by_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    CONSTRAINT early_access_invites_used_by_fk 
        FOREIGN KEY (used_by_id) REFERENCES auth_user(id) ON DELETE SET NULL
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS early_access_invites_invite_code_idx 
    ON early_access_invites(invite_code);
CREATE INDEX IF NOT EXISTS early_access_invites_created_by_idx 
    ON early_access_invites(created_by_id);
CREATE INDEX IF NOT EXISTS early_access_invites_used_by_idx 
    ON early_access_invites(used_by_id);
CREATE INDEX IF NOT EXISTS early_access_invites_is_used_idx 
    ON early_access_invites(is_used);
CREATE INDEX IF NOT EXISTS early_access_invites_expires_at_idx 
    ON early_access_invites(expires_at);

-- Comentários para documentação
COMMENT ON TABLE early_access_invites IS 'Early access invite codes for MVP testing';
COMMENT ON COLUMN early_access_invites.invite_code IS 'Unique invite code';
COMMENT ON COLUMN early_access_invites.expires_at IS 'When early access period ends';
COMMENT ON COLUMN early_access_invites.is_used IS 'Whether invite has been used';
COMMENT ON COLUMN early_access_invites.used_at IS 'When invite was used';
COMMENT ON COLUMN early_access_invites.created_by_id IS 'User who created this invite';
COMMENT ON COLUMN early_access_invites.used_by_id IS 'User who used this invite';

-- 4. REGISTRAR MIGRAÇÃO COMO APLICADA
-- =====================================================

-- Inserir registro na tabela de migrações do Django
-- Só insere se não existir
INSERT INTO django_migrations (app, name, applied)
SELECT 'companies', '0009_add_early_access', NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM django_migrations 
    WHERE app = 'companies' AND name = '0009_add_early_access'
);

-- 5. VERIFICAÇÕES FINAIS
-- =====================================================

-- Verificar se todas as colunas foram criadas
DO $$
DECLARE
    missing_columns TEXT[] := ARRAY[]::TEXT[];
    col_name TEXT;
    table_exists BOOLEAN;
BEGIN
    -- Verificar colunas da tabela companies
    FOR col_name IN SELECT unnest(ARRAY['is_early_access', 'early_access_expires_at', 'used_invite_code'])
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'companies' AND column_name = col_name
        ) THEN
            missing_columns := array_append(missing_columns, col_name);
        END IF;
    END LOOP;
    
    -- Verificar se tabela early_access_invites existe
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'early_access_invites'
    ) INTO table_exists;
    
    -- Relatório final
    IF array_length(missing_columns, 1) > 0 THEN
        RAISE EXCEPTION 'ERRO: Colunas faltando na tabela companies: %', array_to_string(missing_columns, ', ');
    END IF;
    
    IF NOT table_exists THEN
        RAISE EXCEPTION 'ERRO: Tabela early_access_invites não foi criada';
    END IF;
    
    -- Verificar migração registrada
    IF NOT EXISTS (
        SELECT 1 FROM django_migrations 
        WHERE app = 'companies' AND name = '0009_add_early_access'
    ) THEN
        RAISE EXCEPTION 'ERRO: Migração não foi registrada em django_migrations';
    END IF;
    
    RAISE NOTICE '✅ SUCESSO: Todas as alterações foram aplicadas corretamente';
    RAISE NOTICE '✅ Colunas companies: is_early_access, early_access_expires_at, used_invite_code';
    RAISE NOTICE '✅ Tabela early_access_invites criada';
    RAISE NOTICE '✅ Migração 0009_add_early_access registrada';
    RAISE NOTICE '🎉 Sistema de registro deve funcionar agora!';
END $$;

-- 6. MOSTRAR ESTATÍSTICAS FINAIS
-- =====================================================

-- Contar registros
SELECT 
    'companies' as tabela,
    count(*) as total_registros,
    count(*) FILTER (WHERE is_early_access = true) as early_access_ativo
FROM companies

UNION ALL

SELECT 
    'early_access_invites' as tabela,
    count(*) as total_registros,
    count(*) FILTER (WHERE is_used = false) as convites_disponiveis
FROM early_access_invites;

-- Mostrar estrutura das novas colunas
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'companies' 
AND column_name IN ('is_early_access', 'early_access_expires_at', 'used_invite_code')
ORDER BY column_name;

-- =====================================================
-- FIM DO SCRIPT
-- =====================================================
--
-- COMO EXECUTAR:
-- 1. Conectar ao banco de produção do Railway
-- 2. Executar este script completo
-- 3. Verificar as mensagens de sucesso
-- 4. Testar criação de nova conta
--
-- VALIDAÇÃO PÓS-EXECUÇÃO:
-- railway run python validate_early_access_migration.py
--
-- =====================================================