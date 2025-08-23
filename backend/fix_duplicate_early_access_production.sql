-- PRODUCTION FIX FOR DUPLICATE EARLY ACCESS MIGRATIONS
-- This script handles the case where both 0008 and 0009 were applied

BEGIN;

-- Step 1: Verify current state
DO $$
DECLARE
    field_count INTEGER;
    table_exists BOOLEAN;
BEGIN
    -- Check how many early access fields exist
    SELECT COUNT(*) INTO field_count
    FROM information_schema.columns 
    WHERE table_name = 'companies' 
    AND column_name IN ('is_early_access', 'early_access_expires_at', 'used_invite_code');
    
    -- Check if early_access_invites table exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'early_access_invites'
    ) INTO table_exists;
    
    RAISE NOTICE 'Early access fields found: %', field_count;
    RAISE NOTICE 'Early access table exists: %', table_exists;
    
    -- If fields are missing, this indicates PostgreSQL rejected the duplicate operations
    IF field_count < 3 THEN
        RAISE NOTICE 'Adding missing early access fields...';
        
        -- Add missing fields
        ALTER TABLE companies ADD COLUMN IF NOT EXISTS is_early_access BOOLEAN DEFAULT FALSE;
        ALTER TABLE companies ADD COLUMN IF NOT EXISTS early_access_expires_at TIMESTAMPTZ NULL;
        ALTER TABLE companies ADD COLUMN IF NOT EXISTS used_invite_code VARCHAR(20) DEFAULT '';
        
        -- Update subscription_status choices
        -- Note: This requires Django to handle the choices validation
        
        RAISE NOTICE 'Early access fields added successfully';
    ELSE
        RAISE NOTICE 'All early access fields already exist';
    END IF;
    
    -- Create table if it doesn't exist
    IF NOT table_exists THEN
        RAISE NOTICE 'Creating early_access_invites table...';
        
        CREATE TABLE early_access_invites (
            id BIGSERIAL PRIMARY KEY,
            invite_code VARCHAR(20) UNIQUE NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            is_used BOOLEAN DEFAULT FALSE,
            used_at TIMESTAMPTZ NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            notes TEXT DEFAULT '',
            created_by_id BIGINT REFERENCES auth_user(id) ON DELETE CASCADE,
            used_by_id BIGINT REFERENCES auth_user(id) ON DELETE SET NULL
        );
        
        RAISE NOTICE 'early_access_invites table created successfully';
    ELSE
        RAISE NOTICE 'early_access_invites table already exists';
    END IF;
    
END $$;

-- Step 2: Verify the fix
SELECT 'companies_early_access_fields' as validation,
       COUNT(*) as field_count
FROM information_schema.columns 
WHERE table_name = 'companies' 
AND column_name IN ('is_early_access', 'early_access_expires_at', 'used_invite_code')

UNION ALL

SELECT 'early_access_invites_table' as validation,
       COUNT(*) as table_count
FROM information_schema.tables 
WHERE table_name = 'early_access_invites';

COMMIT;

-- Final verification queries
\echo '=== VERIFICATION ==='
\echo 'Early access fields in companies table:'
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'companies' 
AND column_name IN ('is_early_access', 'early_access_expires_at', 'used_invite_code')
ORDER BY column_name;

\echo 'Early access invites table structure:'
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'early_access_invites'
ORDER BY ordinal_position;