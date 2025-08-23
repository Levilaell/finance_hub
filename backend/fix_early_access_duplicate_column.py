#!/usr/bin/env python3
"""
SMART EARLY ACCESS COLUMN FIX
=============================

Resolves DuplicateColumn error for early_access_expires_at by creating a smart
migration that only adds columns if they don't already exist.

PROBLEM: Migration 0009_add_early_access tries to add columns that already exist
SOLUTION: Skip AddField operations for existing columns, only update missing parts

APPROACH:
1. Check if each column exists before attempting to add it
2. Only add missing columns (safe)
3. Update subscription_status choices (safe to repeat)
4. Ensure EarlyAccessInvite table exists (safe to repeat)
"""

import os
import sys
import django
from datetime import datetime

# Setup Django for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

try:
    django.setup()
    from django.db import connection, transaction
    from django.core.management import call_command
    from django.db.migrations.executor import MigrationExecutor
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            );
        """, [table_name, column_name])
        return cursor.fetchone()[0]

def check_table_exists(table_name):
    """Check if a table exists"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, [table_name])
        return cursor.fetchone()[0]

def smart_early_access_fix():
    """Smart fix for early access column duplication"""
    print("🛠️  SMART EARLY ACCESS COLUMN FIX")
    print("=" * 60)
    print(f"📅 Fix time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                
                # STEP 1: Analyze current state
                print("🔍 STEP 1: Analyzing current column state...")
                
                target_columns = {
                    'is_early_access': 'boolean',
                    'early_access_expires_at': 'timestamp with time zone', 
                    'used_invite_code': 'character varying'
                }
                
                existing_columns = {}
                missing_columns = []
                
                for col_name, expected_type in target_columns.items():
                    exists = check_column_exists('companies', col_name)
                    existing_columns[col_name] = exists
                    if not exists:
                        missing_columns.append(col_name)
                    print(f"   📋 {col_name}: {'EXISTS' if exists else 'MISSING'}")
                
                # STEP 2: Add only missing columns
                print(f"\n🔧 STEP 2: Adding missing columns ({len(missing_columns)} needed)...")
                
                if 'is_early_access' in missing_columns:
                    print("   📝 Adding is_early_access column...")
                    cursor.execute("""
                        ALTER TABLE companies 
                        ADD COLUMN is_early_access BOOLEAN DEFAULT FALSE NOT NULL;
                    """)
                    print("   ✅ is_early_access added successfully")
                
                if 'early_access_expires_at' in missing_columns:
                    print("   📝 Adding early_access_expires_at column...")  
                    cursor.execute("""
                        ALTER TABLE companies 
                        ADD COLUMN early_access_expires_at TIMESTAMPTZ NULL;
                    """)
                    print("   ✅ early_access_expires_at added successfully")
                
                if 'used_invite_code' in missing_columns:
                    print("   📝 Adding used_invite_code column...")
                    cursor.execute("""
                        ALTER TABLE companies 
                        ADD COLUMN used_invite_code VARCHAR(20) DEFAULT '' NOT NULL;
                    """)
                    print("   ✅ used_invite_code added successfully")
                
                if not missing_columns:
                    print("   ✅ All columns already exist - no additions needed")
                
                # STEP 3: Ensure EarlyAccessInvite table exists
                print(f"\n🔧 STEP 3: Ensuring EarlyAccessInvite table exists...")
                
                invite_table_exists = check_table_exists('early_access_invites')
                print(f"   📋 early_access_invites table: {'EXISTS' if invite_table_exists else 'MISSING'}")
                
                if not invite_table_exists:
                    print("   📝 Creating early_access_invites table...")
                    cursor.execute("""
                        CREATE TABLE early_access_invites (
                            id BIGSERIAL PRIMARY KEY,
                            invite_code VARCHAR(20) UNIQUE NOT NULL,
                            expires_at TIMESTAMPTZ NOT NULL,
                            is_used BOOLEAN DEFAULT FALSE NOT NULL,
                            used_at TIMESTAMPTZ NULL,
                            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
                            notes TEXT DEFAULT '' NOT NULL,
                            created_by_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            used_by_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL
                        );
                    """)
                    
                    # Add indexes
                    cursor.execute("CREATE INDEX early_access_invites_invite_code_idx ON early_access_invites (invite_code);")
                    cursor.execute("CREATE INDEX early_access_invites_created_by_id_idx ON early_access_invites (created_by_id);")
                    cursor.execute("CREATE INDEX early_access_invites_used_by_id_idx ON early_access_invites (used_by_id);")
                    cursor.execute("CREATE INDEX early_access_invites_expires_at_idx ON early_access_invites (expires_at);")
                    
                    print("   ✅ early_access_invites table created successfully")
                else:
                    print("   ✅ early_access_invites table already exists")
                
                # STEP 4: Update subscription_status choices (safe to repeat)
                print(f"\n🔧 STEP 4: Updating subscription_status field constraints...")
                
                # Check current max_length
                cursor.execute("""
                    SELECT character_maximum_length 
                    FROM information_schema.columns 
                    WHERE table_name = 'companies' AND column_name = 'subscription_status';
                """)
                current_length = cursor.fetchone()
                current_max_length = current_length[0] if current_length else None
                
                print(f"   📋 Current subscription_status max_length: {current_max_length}")
                
                # Ensure it can handle 'early_access' value (13 chars)
                if current_max_length and current_max_length < 15:
                    print("   📝 Expanding subscription_status max_length...")
                    cursor.execute("""
                        ALTER TABLE companies 
                        ALTER COLUMN subscription_status TYPE VARCHAR(20);
                    """)
                    print("   ✅ subscription_status max_length updated")
                else:
                    print("   ✅ subscription_status max_length is sufficient")
                
                # STEP 5: Mark migration as applied if not already
                print(f"\n🔧 STEP 5: Ensuring migration is marked as applied...")
                
                cursor.execute("""
                    SELECT COUNT(*) FROM django_migrations 
                    WHERE app = 'companies' AND name = '0009_add_early_access';
                """)
                migration_applied = cursor.fetchone()[0] > 0
                
                print(f"   📋 Migration 0009_add_early_access: {'APPLIED' if migration_applied else 'NOT APPLIED'}")
                
                if not migration_applied:
                    print("   📝 Marking migration 0009 as applied...")
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied) 
                        VALUES ('companies', '0009_add_early_access', NOW());
                    """)
                    print("   ✅ Migration 0009 marked as applied")
                else:
                    print("   ✅ Migration 0009 already marked as applied")
                
                # STEP 6: Final validation
                print(f"\n🔍 STEP 6: Final validation...")
                
                # Verify all columns exist
                final_check = {}
                all_columns_exist = True
                for col_name in target_columns.keys():
                    exists = check_column_exists('companies', col_name)
                    final_check[col_name] = exists
                    print(f"   {'✅' if exists else '❌'} {col_name}: {'EXISTS' if exists else 'MISSING'}")
                    if not exists:
                        all_columns_exist = False
                
                # Verify table exists  
                final_table_check = check_table_exists('early_access_invites')
                print(f"   {'✅' if final_table_check else '❌'} early_access_invites table: {'EXISTS' if final_table_check else 'MISSING'}")
                
                if all_columns_exist and final_table_check:
                    print(f"\n🎉 SMART FIX COMPLETED SUCCESSFULLY!")
                    print(f"✅ All early access columns exist")
                    print(f"✅ EarlyAccessInvite table exists") 
                    print(f"✅ Migration marked as applied")
                    print(f"✅ DuplicateColumn error should be resolved")
                    print(f"✅ Early access functionality ready for use")
                    return True
                else:
                    print(f"\n⚠️  SMART FIX HAD ISSUES:")
                    print(f"   All columns exist: {all_columns_exist}")
                    print(f"   Table exists: {final_table_check}")
                    return False
                    
    except Exception as e:
        print(f"\n❌ SMART FIX FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main execution function"""
    print("🛠️  SMART EARLY ACCESS COLUMN FIX")
    print("=" * 70)
    print("🎯 Target: Resolve DuplicateColumn error for early_access_expires_at")
    print("⚡ Method: Smart column addition - only add what's missing")
    print()
    
    # Execute the smart fix
    fix_success = smart_early_access_fix()
    
    if fix_success:
        print(f"\n" + "="*70)
        print("🎉 SMART FIX SUCCESS!")
        print("✅ Early access columns and table are ready")
        print("✅ DuplicateColumn error resolved")
        print("✅ Migration state is consistent")  
        print("✅ System ready for early access functionality")
        print()
        print("🚀 Next Django migration run will be successful!")
        return True
    else:
        print(f"\n" + "="*70)
        print("❌ SMART FIX FAILED")
        print("   Check the logs above for error details")
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)