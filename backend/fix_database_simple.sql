-- Script simples para corrigir inconsistências do banco
-- Criar tabela email_verifications

CREATE TABLE IF NOT EXISTS email_verifications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(100) UNIQUE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

-- Criar indexes
CREATE INDEX IF NOT EXISTS email_verifications_user_id_is_used_idx 
    ON email_verifications(user_id, is_used);

CREATE INDEX IF NOT EXISTS email_verifications_token_idx 
    ON email_verifications(token);

CREATE INDEX IF NOT EXISTS email_verifications_expires_at_idx 
    ON email_verifications(expires_at);

-- Registrar migração
INSERT INTO django_migrations (app, name, applied) 
VALUES ('authentication', '0003_emailverification', NOW())
ON CONFLICT (app, name) DO NOTHING;

-- Remover indexes problemáticos se existirem
DROP INDEX IF EXISTS banking_tra_acc_date_idx;
DROP INDEX IF EXISTS banking_tra_type_date_idx;
DROP INDEX IF EXISTS banking_tra_cat_date_idx;
DROP INDEX IF EXISTS banking_tra_complex_idx;