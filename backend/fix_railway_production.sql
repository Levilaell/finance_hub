-- SCRIPT DE CORREÇÃO PARA PRODUÇÃO RAILWAY
-- Execute via: railway shell
-- Depois: \i fix_railway_production.sql

-- 1. CORRIGIR COLLATION VERSION MISMATCH
ALTER DATABASE railway REFRESH COLLATION VERSION;

-- 2. VERIFICAR SE MIGRAÇÕES CRÍTICAS FORAM APLICADAS
SELECT 
    app, 
    name, 
    applied,
    CASE 
        WHEN app = 'companies' AND name = '0009_add_early_access' THEN '🔑 Early Access'
        WHEN app = 'banking' AND name = '0010_add_encrypted_parameter' THEN '🔒 MFA Encryption' 
        WHEN app = 'banking' AND name = '0011_remove_transaction_banking_tra_acc_date_idx_and_more' THEN '⚡ Index Removal'
        WHEN app = 'reports' AND name = '0005_fix_inconsistent_history' THEN '🔧 History Fix'
        ELSE '📋 Standard'
    END as tipo
FROM django_migrations 
WHERE (app, name) IN (
    ('companies', '0009_add_early_access'),
    ('banking', '0010_add_encrypted_parameter'),
    ('banking', '0011_remove_transaction_banking_tra_acc_date_idx_and_more'),
    ('reports', '0005_fix_inconsistent_history')
)
ORDER BY app, name;

-- 3. VERIFICAR CAMPOS CRÍTICOS
\echo '🔍 VERIFICANDO CAMPOS CRÍTICOS...'

-- Early Access fields na tabela companies
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'companies' 
AND column_name IN ('is_early_access', 'early_access_expires_at', 'used_invite_code')
ORDER BY column_name;

-- Verificar tabela early_access_invites
SELECT 
    COUNT(*) as total_registros,
    COUNT(*) FILTER (WHERE is_used = true) as usados,
    COUNT(*) FILTER (WHERE expires_at > NOW()) as validos
FROM early_access_invites;

-- 4. VERIFICAR PERFORMANCE DOS ÍNDICES (após remoção)
\echo '⚡ VERIFICANDO ÍNDICES DE TRANSAÇÕES...'

SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'transactions'
ORDER BY indexname;

-- 5. VERIFICAR INTEGRIDADE REFERENCIAL
\echo '🔗 VERIFICANDO INTEGRIDADE REFERENCIAL...'

-- Transações órfãs (sem conta)
SELECT COUNT(*) as transacoes_orfas
FROM transactions t
LEFT JOIN bank_accounts ba ON t.account_id = ba.id
WHERE ba.id IS NULL;

-- Contas órfãs (sem empresa)
SELECT COUNT(*) as contas_orfas  
FROM bank_accounts ba
LEFT JOIN companies c ON ba.company_id = c.id
WHERE c.id IS NULL;

\echo '✅ SCRIPT DE CORREÇÃO CONCLUÍDO'
\echo 'Execute: python manage.py migrate para aplicar migrações pendentes'