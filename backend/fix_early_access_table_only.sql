-- =====================================================
-- SQL PARA CRIAR APENAS A TABELA EARLY_ACCESS_INVITES
-- =====================================================
-- 
-- Os campos da tabela companies já foram criados com sucesso.
-- Este script cria apenas a tabela early_access_invites 
-- com a referência correta para a tabela 'users'.
--
-- =====================================================

-- 1. CRIAR TABELA EARLY_ACCESS_INVITES
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
    
    -- Foreign keys - usando 'users' ao invés de 'auth_user'
    CONSTRAINT early_access_invites_created_by_fk 
        FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT early_access_invites_used_by_fk 
        FOREIGN KEY (used_by_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 2. CRIAR ÍNDICES PARA PERFORMANCE
-- =====================================================

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

-- 3. ADICIONAR COMENTÁRIOS
-- =====================================================

COMMENT ON TABLE early_access_invites IS 'Early access invite codes for MVP testing';
COMMENT ON COLUMN early_access_invites.invite_code IS 'Unique invite code';
COMMENT ON COLUMN early_access_invites.expires_at IS 'When early access period ends';
COMMENT ON COLUMN early_access_invites.is_used IS 'Whether invite has been used';
COMMENT ON COLUMN early_access_invites.used_at IS 'When invite was used';
COMMENT ON COLUMN early_access_invites.created_by_id IS 'User who created this invite';
COMMENT ON COLUMN early_access_invites.used_by_id IS 'User who used this invite';

-- 4. VERIFICAÇÃO FINAL
-- =====================================================

DO $$
BEGIN
    -- Verificar se tabela foi criada
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'early_access_invites'
    ) THEN
        RAISE NOTICE '✅ SUCESSO: Tabela early_access_invites criada com sucesso!';
        RAISE NOTICE '✅ Sistema de early access agora está completo';
        RAISE NOTICE '🎉 Sistema de registro deve funcionar!';
    ELSE
        RAISE EXCEPTION 'ERRO: Tabela early_access_invites não foi criada';
    END IF;
END $$;

-- 5. MOSTRAR ESTRUTURA DA NOVA TABELA
-- =====================================================

SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'early_access_invites'
ORDER BY ordinal_position;