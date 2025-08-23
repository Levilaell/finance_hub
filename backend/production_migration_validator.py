#!/usr/bin/env python
"""
PRODUCTION MIGRATION VALIDATOR
Validate production database state and detect critical issues for Railway deployment
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

try:
    django.setup()
    from django.db import connection
except Exception as e:
    print(f"⚠️ Django setup failed (expected in production): {e}")
    print("This script should be run in Railway environment")

def validate_production_schema():
    """Validate production database schema"""
    print("🔍 PRODUCTION SCHEMA VALIDATION")
    print("=" * 50)
    
    validations = []
    
    try:
        with connection.cursor() as cursor:
            # 1. Check early access fields duplication
            print("\n1. EARLY ACCESS FIELDS VALIDATION:")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'companies' 
                AND column_name IN ('is_early_access', 'early_access_expires_at', 'used_invite_code')
                ORDER BY column_name;
            """)
            early_access_fields = cursor.fetchall()
            
            if len(early_access_fields) == 3:
                print("  ✅ All 3 early access fields exist")
                for field in early_access_fields:
                    print(f"    - {field[0]}: {field[1]} (nullable: {field[2]})")
                validations.append(("early_access_fields", True, "All fields present"))
            else:
                print(f"  ❌ Expected 3 fields, found {len(early_access_fields)}")
                validations.append(("early_access_fields", False, f"Missing fields: {3 - len(early_access_fields)}"))
            
            # 2. Check EarlyAccessInvite table
            print("\n2. EARLY ACCESS INVITE TABLE:")
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'early_access_invites'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                print("  ✅ early_access_invites table exists")
                
                # Check table structure
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'early_access_invites'
                    ORDER BY ordinal_position;
                """)
                columns = cursor.fetchall()
                print(f"    Columns ({len(columns)}):")
                for col in columns:
                    print(f"      - {col[0]}: {col[1]}")
                
                validations.append(("early_access_table", True, f"Table exists with {len(columns)} columns"))
            else:
                print("  ❌ early_access_invites table missing")
                validations.append(("early_access_table", False, "Table not found"))
            
            # 3. Check notifications table structure
            print("\n3. NOTIFICATIONS TABLE VALIDATION:")
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = 'notifications'
                AND column_name IN ('event', 'event_key', 'notification_type', 'data')
                ORDER BY column_name;
            """)
            notif_fields = cursor.fetchall()
            
            has_new_format = any(field[0] in ['event', 'event_key'] for field in notif_fields)
            has_old_format = any(field[0] in ['notification_type', 'data'] for field in notif_fields)
            
            if has_new_format and not has_old_format:
                print("  ✅ Notifications table has new schema (event/event_key)")
                validations.append(("notifications_schema", True, "Using new schema"))
            elif has_old_format and not has_new_format:
                print("  ❌ Notifications table has old schema (notification_type/data)")
                validations.append(("notifications_schema", False, "Still using old schema"))
            elif has_new_format and has_old_format:
                print("  ⚠️ Notifications table has mixed schema (both old and new)")
                validations.append(("notifications_schema", False, "Mixed schema detected"))
            else:
                print("  ❌ Notifications table schema unclear")
                validations.append(("notifications_schema", False, "Schema unclear"))
            
            # 4. Check transaction indexes
            print("\n4. TRANSACTION INDEXES VALIDATION:")
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'banking_transactions'
                AND indexname LIKE '%banking_tra_%'
                ORDER BY indexname;
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            
            removed_indexes = [
                'banking_tra_acc_date_idx',
                'banking_tra_type_date_idx', 
                'banking_tra_cat_date_idx',
                'banking_tra_complex_idx'
            ]
            
            found_removed = [idx for idx in removed_indexes if idx in indexes]
            if found_removed:
                print(f"  ⚠️ Found {len(found_removed)} indexes that should have been removed:")
                for idx in found_removed:
                    print(f"    - {idx}")
                validations.append(("transaction_indexes", False, f"{len(found_removed)} old indexes still exist"))
            else:
                print("  ✅ Old transaction indexes properly removed")
                print(f"    Current indexes: {len(indexes)}")
                validations.append(("transaction_indexes", True, "Old indexes removed"))
            
            # 5. Check encrypted_parameter field
            print("\n5. BANKING ENCRYPTION VALIDATION:")
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = 'banking_pluggyitem'
                AND column_name IN ('parameter', 'encrypted_parameter')
                ORDER BY column_name;
            """)
            encryption_fields = cursor.fetchall()
            
            has_encrypted = any(field[0] == 'encrypted_parameter' for field in encryption_fields)
            if has_encrypted:
                print("  ✅ encrypted_parameter field exists")
                validations.append(("banking_encryption", True, "Encryption field present"))
            else:
                print("  ❌ encrypted_parameter field missing")
                validations.append(("banking_encryption", False, "Encryption field missing"))
            
            # 6. Check migration history consistency
            print("\n6. MIGRATION HISTORY VALIDATION:")
            cursor.execute("""
                SELECT app, name, applied
                FROM django_migrations 
                WHERE app IN ('companies', 'notifications', 'banking', 'reports')
                AND name IN (
                    '0008_alter_resourceusage_options_and_more',
                    '0009_add_early_access',
                    '0002_add_event_key',
                    '0003_cleanup_old_fields',
                    '0011_remove_transaction_banking_tra_acc_date_idx_and_more'
                )
                ORDER BY app, name;
            """)
            critical_migrations = cursor.fetchall()
            
            print(f"  Critical migrations applied: {len(critical_migrations)}")
            for migration in critical_migrations:
                print(f"    - {migration[0]}.{migration[1]} ({migration[2]})")
            
            expected_count = 5  # 2 companies + 2 notifications + 1 banking
            if len(critical_migrations) == expected_count:
                validations.append(("migration_history", True, "All critical migrations applied"))
            else:
                validations.append(("migration_history", False, f"Expected {expected_count}, found {len(critical_migrations)}"))
            
    except Exception as e:
        print(f"❌ Database validation failed: {e}")
        validations.append(("database_connection", False, str(e)))
    
    # Generate summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, status, _ in validations if status)
    total = len(validations)
    
    print(f"Validations: {passed}/{total} passed")
    print()
    
    for validation, status, message in validations:
        icon = "✅" if status else "❌"
        print(f"{icon} {validation}: {message}")
    
    if passed == total:
        print("\n🎉 ALL VALIDATIONS PASSED - Production schema is healthy")
        return True
    else:
        print(f"\n⚠️ {total - passed} VALIDATION(S) FAILED - Requires attention")
        return False

def generate_fix_script():
    """Generate SQL script to fix common issues"""
    print("\n" + "=" * 50)
    print("FIX SCRIPT GENERATION")
    print("=" * 50)
    
    fix_script = """
-- PRODUCTION DATABASE FIX SCRIPT
-- Run this script only if validation failures are detected

BEGIN;

-- Fix 1: Remove duplicate indexes if they still exist
DROP INDEX IF EXISTS banking_tra_acc_date_idx;
DROP INDEX IF EXISTS banking_tra_type_date_idx;
DROP INDEX IF EXISTS banking_tra_cat_date_idx;
DROP INDEX IF EXISTS banking_tra_complex_idx;

-- Fix 2: Ensure early access fields exist
ALTER TABLE companies ADD COLUMN IF NOT EXISTS is_early_access BOOLEAN DEFAULT FALSE;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS early_access_expires_at TIMESTAMPTZ NULL;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS used_invite_code VARCHAR(20) DEFAULT '';

-- Fix 3: Ensure early_access_invites table exists
CREATE TABLE IF NOT EXISTS early_access_invites (
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

-- Fix 4: Ensure notifications table has new schema
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS event VARCHAR(50) DEFAULT 'sync_completed';
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS event_key VARCHAR(255) NULL UNIQUE;
-- Note: Removing old fields requires careful data migration

-- Fix 5: Ensure encrypted_parameter field exists
ALTER TABLE banking_pluggyitem ADD COLUMN IF NOT EXISTS encrypted_parameter TEXT DEFAULT '';

COMMIT;

-- Verify changes
SELECT 'Early access fields' as check_type, count(*) as field_count
FROM information_schema.columns 
WHERE table_name = 'companies' 
AND column_name IN ('is_early_access', 'early_access_expires_at', 'used_invite_code');

SELECT 'Early access table' as check_type, count(*) as table_count
FROM information_schema.tables 
WHERE table_name = 'early_access_invites';
"""
    
    print("Generated fix script (save as fix_production_schema.sql):")
    print(fix_script)

if __name__ == '__main__':
    print("🚀 PRODUCTION MIGRATION VALIDATOR")
    print("For Railway deployment validation")
    print()
    
    try:
        schema_ok = validate_production_schema()
        generate_fix_script()
        
        if schema_ok:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Validator failed: {e}")
        sys.exit(2)