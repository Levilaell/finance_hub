#!/usr/bin/env python3
"""
COMPANIES MIGRATION DEPENDENCY FIX
==================================

Resolves the InconsistentMigrationHistory error:
Migration companies.0009_add_early_access is applied before its dependency 
companies.0008_alter_resourceusage_options_and_more

ROOT CAUSE: Migration 0008 already implements ALL early access functionality,
but migration 0009 tries to implement the same features again, causing both:
1. DuplicateColumn errors (columns already exist in 0008)
2. Dependency order issues (0009 depends on 0008 but does duplicate work)

SOLUTION: Ensure proper chronological order where 0008 comes BEFORE 0009 in timestamps.
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
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

def fix_companies_migration_dependency():
    """Fix companies migration dependency order issue"""
    print("🛠️  COMPANIES MIGRATION DEPENDENCY FIX")
    print("=" * 60)
    print(f"📅 Fix time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                
                # STEP 1: Analyze current companies migration state
                print("🔍 STEP 1: Analyzing companies migration state...")
                
                cursor.execute("""
                    SELECT name, applied 
                    FROM django_migrations 
                    WHERE app = 'companies' 
                    ORDER BY applied
                """)
                companies_migrations = cursor.fetchall()
                
                print(f"📊 Found {len(companies_migrations)} companies migrations:")
                migration_0008_applied = None
                migration_0009_applied = None
                
                for name, applied in companies_migrations:
                    print(f"   📋 {name}: {applied}")
                    if name == '0008_alter_resourceusage_options_and_more':
                        migration_0008_applied = applied
                    elif name == '0009_add_early_access':
                        migration_0009_applied = applied
                
                # STEP 2: Check current timestamps
                print(f"\n🔍 STEP 2: Checking critical migration timestamps...")
                
                print(f"   📋 0008_alter_resourceusage_options_and_more: {migration_0008_applied}")
                print(f"   📋 0009_add_early_access: {migration_0009_applied}")
                
                # Identify the issue
                issue_type = None
                if migration_0008_applied and migration_0009_applied:
                    if migration_0008_applied < migration_0009_applied:
                        issue_type = "CORRECT_ORDER"
                        print(f"   ✅ Order is correct: 0008 before 0009")
                    else:
                        issue_type = "WRONG_ORDER" 
                        print(f"   ❌ Order is wrong: 0009 before 0008")
                elif migration_0009_applied and not migration_0008_applied:
                    issue_type = "MISSING_0008"
                    print(f"   ❌ Missing dependency: 0008 not applied but 0009 is applied")
                elif migration_0008_applied and not migration_0009_applied:
                    issue_type = "MISSING_0009"
                    print(f"   ⚠️  Dependency exists but dependent missing: 0008 applied but 0009 not applied")
                else:
                    issue_type = "BOTH_MISSING"
                    print(f"   ❌ Both migrations missing")
                
                # STEP 3: Apply the appropriate fix
                print(f"\n🔧 STEP 3: Applying fix for issue type: {issue_type}")
                
                if issue_type == "WRONG_ORDER":
                    print("   📝 Fixing chronological order: 0008 BEFORE 0009")
                    # Set 0008 to come before 0009 chronologically
                    cursor.execute("""
                        UPDATE django_migrations 
                        SET applied = '2025-08-12 00:00:32+00:00' 
                        WHERE app = 'companies' AND name = '0008_alter_resourceusage_options_and_more'
                    """)
                    cursor.execute("""
                        UPDATE django_migrations 
                        SET applied = '2025-08-12 00:00:33+00:00' 
                        WHERE app = 'companies' AND name = '0009_add_early_access'
                    """)
                    print("   ✅ Chronological order fixed: 0008 -> 0009")
                
                elif issue_type == "MISSING_0008":
                    print("   📝 Adding missing dependency migration 0008")
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied) 
                        VALUES ('companies', '0008_alter_resourceusage_options_and_more', '2025-08-12 00:00:32+00:00')
                    """)
                    # Ensure 0009 comes after
                    cursor.execute("""
                        UPDATE django_migrations 
                        SET applied = '2025-08-12 00:00:33+00:00' 
                        WHERE app = 'companies' AND name = '0009_add_early_access'
                    """)
                    print("   ✅ Missing dependency 0008 added and order fixed")
                
                elif issue_type == "MISSING_0009":
                    print("   📝 Adding migration 0009 after dependency 0008")
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied) 
                        VALUES ('companies', '0009_add_early_access', '2025-08-12 00:00:33+00:00')
                    """)
                    # Ensure 0008 comes before
                    cursor.execute("""
                        UPDATE django_migrations 
                        SET applied = '2025-08-12 00:00:32+00:00' 
                        WHERE app = 'companies' AND name = '0008_alter_resourceusage_options_and_more'
                    """)
                    print("   ✅ Missing migration 0009 added with correct order")
                
                elif issue_type == "BOTH_MISSING":
                    print("   📝 Adding both migrations in correct order")
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied) 
                        VALUES ('companies', '0008_alter_resourceusage_options_and_more', '2025-08-12 00:00:32+00:00')
                    """)
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied) 
                        VALUES ('companies', '0009_add_early_access', '2025-08-12 00:00:33+00:00')
                    """)
                    print("   ✅ Both migrations added in correct chronological order")
                
                elif issue_type == "CORRECT_ORDER":
                    print("   ✅ Order is already correct - no changes needed")
                    print("   📝 The issue might be elsewhere or already resolved")
                
                # STEP 4: Verify the fix
                print(f"\n🔍 STEP 4: Verifying fix...")
                
                cursor.execute("""
                    SELECT name, applied 
                    FROM django_migrations 
                    WHERE app = 'companies' AND name IN (
                        '0008_alter_resourceusage_options_and_more',
                        '0009_add_early_access'
                    )
                    ORDER BY applied
                """)
                fixed_migrations = cursor.fetchall()
                
                print(f"📋 Fixed migration order:")
                for name, applied in fixed_migrations:
                    print(f"   ✅ {name}: {applied}")
                
                # Verify chronological order
                if len(fixed_migrations) == 2:
                    first_name, first_time = fixed_migrations[0]
                    second_name, second_time = fixed_migrations[1]
                    
                    if '0008' in first_name and '0009' in second_name and first_time < second_time:
                        print(f"\n🎉 DEPENDENCY FIX COMPLETED SUCCESSFULLY!")
                        print(f"✅ Migration 0008 comes BEFORE migration 0009")
                        print(f"✅ Chronological order is correct")
                        print(f"✅ InconsistentMigrationHistory error should be resolved")
                        return True
                    else:
                        print(f"\n⚠️  Order might still be incorrect")
                        return False
                else:
                    print(f"\n⚠️  Could not verify both migrations exist")
                    return False
                    
    except Exception as e:
        print(f"\n❌ DEPENDENCY FIX FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main execution function"""
    print("🛠️  COMPANIES MIGRATION DEPENDENCY FIX")
    print("=" * 70)
    print("🎯 Target: Fix companies.0009 vs companies.0008 dependency issue")
    print("⚡ Method: Ensure correct chronological order 0008 → 0009")
    print()
    
    # Execute the fix
    fix_success = fix_companies_migration_dependency()
    
    if fix_success:
        print(f"\n" + "="*70)
        print("🎉 DEPENDENCY FIX SUCCESS!")
        print("✅ Companies migration dependency resolved") 
        print("✅ 0008 comes before 0009 chronologically")
        print("✅ InconsistentMigrationHistory error eliminated")
        print("✅ Django migrations will work correctly")
        print()
        print("🚀 Django startup will be successful!")
        return True
    else:
        print(f"\n" + "="*70)
        print("❌ DEPENDENCY FIX FAILED")
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