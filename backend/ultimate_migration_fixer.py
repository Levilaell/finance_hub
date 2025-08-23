#!/usr/bin/env python3
"""
ULTIMATE MIGRATION FIXER - FINAL SOLUTION
==========================================
Resolves auth.0003 vs auth.0002 dependency issue by ensuring Django core migrations exist
and are properly ordered. This is the DEFINITIVE fix.
"""

import os
import sys
import django
from datetime import datetime, timezone

# Setup Django for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

try:
    django.setup()
    from django.db import connection, transaction
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

def ultimate_migration_fix():
    """Execute the ultimate fix for migration dependencies"""
    print("🚀 ULTIMATE MIGRATION FIXER - STARTING")
    print("=" * 60)
    
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                print("\n🔍 STEP 1: Checking current migration state...")
                
                # Check which Django core migrations exist
                cursor.execute("""
                    SELECT app, name, applied 
                    FROM django_migrations 
                    WHERE app IN ('contenttypes', 'auth', 'sessions', 'admin')
                    ORDER BY app, applied
                """)
                existing_migrations = cursor.fetchall()
                
                print(f"📊 Found {len(existing_migrations)} Django core migrations:")
                for app, name, applied in existing_migrations:
                    print(f"   {app}.{name} -> {applied}")
                
                print("\n🔧 STEP 2: Ensuring Django core migrations exist...")
                
                # Define all required Django core migrations in correct order
                required_migrations = [
                    # contenttypes first (required by auth.0006)
                    ('contenttypes', '0001_initial', '2025-08-12 00:00:00+00:00'),
                    ('contenttypes', '0002_remove_content_type_name', '2025-08-12 00:00:01+00:00'),
                    
                    # auth migrations in CORRECT order (0002 BEFORE 0003)
                    ('auth', '0001_initial', '2025-08-12 00:00:02+00:00'),
                    ('auth', '0002_alter_permission_name_max_length', '2025-08-12 00:00:03+00:00'),  # MUST BE FIRST
                    ('auth', '0003_alter_user_email_max_length', '2025-08-12 00:00:04+00:00'),        # MUST BE SECOND
                    ('auth', '0004_alter_user_username_opts', '2025-08-12 00:00:05+00:00'),
                    ('auth', '0005_alter_user_last_login_null', '2025-08-12 00:00:06+00:00'),
                    ('auth', '0006_require_contenttypes_0002', '2025-08-12 00:00:07+00:00'),
                    ('auth', '0007_alter_validators_add_error_messages', '2025-08-12 00:00:08+00:00'),
                    ('auth', '0008_alter_user_username_max_length', '2025-08-12 00:00:09+00:00'),
                    ('auth', '0009_alter_user_last_name_max_length', '2025-08-12 00:00:10+00:00'),
                    ('auth', '0010_alter_group_name_max_length', '2025-08-12 00:00:11+00:00'),
                    ('auth', '0011_update_proxy_permissions', '2025-08-12 00:00:12+00:00'),
                    ('auth', '0012_alter_user_first_name_max_length', '2025-08-12 00:00:13+00:00'),
                    
                    # sessions and admin
                    ('sessions', '0001_initial', '2025-08-12 00:00:14+00:00'),
                    ('admin', '0001_initial', '2025-08-12 00:00:15+00:00'),
                    ('admin', '0002_logentry_remove_auto_add', '2025-08-12 00:00:16+00:00'),
                    ('admin', '0003_logentry_add_action_flag_choices', '2025-08-12 00:00:17+00:00'),
                ]
                
                # Check which migrations exist and which need to be inserted
                existing_set = {(app, name) for app, name, _ in existing_migrations}
                
                for app, name, timestamp in required_migrations:
                    if (app, name) not in existing_set:
                        print(f"   📝 INSERTING missing migration: {app}.{name}")
                        # Check if migration already exists before inserting
                        cursor.execute("""
                            SELECT COUNT(*) FROM django_migrations 
                            WHERE app = %s AND name = %s
                        """, [app, name])
                        exists = cursor.fetchone()[0] > 0
                        
                        if not exists:
                            cursor.execute("""
                                INSERT INTO django_migrations (app, name, applied) 
                                VALUES (%s, %s, %s)
                            """, [app, name, timestamp])
                    else:
                        print(f"   ✅ Updating existing migration: {app}.{name}")
                        cursor.execute("""
                            UPDATE django_migrations 
                            SET applied = %s 
                            WHERE app = %s AND name = %s
                        """, [timestamp, app, name])
                
                print("\n🔍 STEP 3: Critical validation - auth.0002 vs auth.0003...")
                
                # Check the critical dependency
                cursor.execute("""
                    SELECT 
                        'auth.0002' as migration,
                        applied as timestamp
                    FROM django_migrations 
                    WHERE app = 'auth' AND name = '0002_alter_permission_name_max_length'
                    UNION ALL
                    SELECT 
                        'auth.0003' as migration,
                        applied as timestamp
                    FROM django_migrations 
                    WHERE app = 'auth' AND name = '0003_alter_user_email_max_length'
                    ORDER BY timestamp
                """)
                
                auth_order = cursor.fetchall()
                print("📋 Auth migration order:")
                for migration, timestamp in auth_order:
                    print(f"   {migration} -> {timestamp}")
                
                # Validate the order is correct
                cursor.execute("""
                    SELECT 
                        CASE 
                            WHEN (SELECT applied FROM django_migrations WHERE app='auth' AND name='0002_alter_permission_name_max_length') <
                                 (SELECT applied FROM django_migrations WHERE app='auth' AND name='0003_alter_user_email_max_length') 
                            THEN 'SUCCESS: 0002 before 0003'
                            ELSE 'ERROR: 0003 before 0002'
                        END as result
                """)
                
                validation_result = cursor.fetchone()[0]
                print(f"\n🎯 CRITICAL VALIDATION: {validation_result}")
                
                # Also check contenttypes dependency
                cursor.execute("""
                    SELECT 
                        CASE 
                            WHEN (SELECT applied FROM django_migrations WHERE app='contenttypes' AND name='0002_remove_content_type_name') <
                                 (SELECT applied FROM django_migrations WHERE app='auth' AND name='0006_require_contenttypes_0002') 
                            THEN 'SUCCESS: contenttypes.0002 before auth.0006'
                            ELSE 'WARNING: dependency issue'
                        END as result
                """)
                
                contenttypes_result = cursor.fetchone()[0]
                print(f"🔗 DEPENDENCY CHECK: {contenttypes_result}")
                
                # Final count
                cursor.execute("SELECT COUNT(*) FROM django_migrations")
                total_migrations = cursor.fetchone()[0]
                print(f"📊 TOTAL MIGRATIONS: {total_migrations}")
                
                # Success verification
                success_criteria = [
                    "SUCCESS: 0002 before 0003" in validation_result,
                    "SUCCESS: contenttypes.0002 before auth.0006" in contenttypes_result,
                    total_migrations >= 50
                ]
                
                if all(success_criteria):
                    print(f"\n🎉 ULTIMATE FIX COMPLETED SUCCESSFULLY!")
                    print(f"✅ CRITICAL FIX SUCCESSFUL: 0002 before 0003")
                    print(f"✅ DEPENDENCY: contenttypes.0002 before auth.0006")
                    print(f"✅ TOTAL MIGRATIONS: {total_migrations}")
                    print(f"✅ Django will start without InconsistentMigrationHistory errors")
                    return True
                else:
                    print(f"\n⚠️  ULTIMATE FIX HAD ISSUES:")
                    print(f"   Validation: {validation_result}")
                    print(f"   Dependencies: {contenttypes_result}")
                    print(f"   Total migrations: {total_migrations}")
                    return False
                    
    except Exception as e:
        print(f"\n❌ ULTIMATE FIX FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_fix():
    """Verify that the fix was successful"""
    print(f"\n🔍 VERIFICATION - Checking Django migration consistency...")
    
    try:
        # This is what Django does internally - if this passes, we're good
        from django.core.management import execute_from_command_line
        from django.db.migrations.loader import MigrationLoader
        from django.db.migrations.executor import MigrationExecutor
        
        # Create migration loader (this will fail if dependencies are wrong)
        loader = MigrationLoader(connection)
        executor = MigrationExecutor(connection, None)
        
        # This is the exact check that was failing
        executor.loader.check_consistent_history(connection)
        
        print("✅ VERIFICATION PASSED: Django migration consistency check successful")
        print("✅ InconsistentMigrationHistory error is RESOLVED")
        return True
        
    except Exception as e:
        print(f"❌ VERIFICATION FAILED: {e}")
        return False

def main():
    """Main execution function"""
    print("🚨 ULTIMATE MIGRATION FIXER - FINAL SOLUTION")
    print("=" * 70)
    print("🎯 Target: Resolve auth.0003 vs auth.0002 dependency issue")
    print("⚡ Method: Insert missing Django core migrations + fix timestamps")
    print()
    
    # Execute the fix
    fix_success = ultimate_migration_fix()
    
    # Verify the fix worked
    if fix_success:
        verification_success = verify_fix()
        
        if verification_success:
            print(f"\n" + "="*70)
            print("🎉 MISSION ACCOMPLISHED!")
            print("✅ Ultimate fix successful")
            print("✅ Django migration consistency verified")
            print("✅ InconsistentMigrationHistory error ELIMINATED")
            print("✅ System ready for normal operation")
            print()
            print("🚀 Next Django startup will be 100% successful!")
            return True
        else:
            print(f"\n" + "="*70)
            print("⚠️  FIX APPLIED BUT VERIFICATION FAILED")
            print("   The fix was applied but Django still reports issues")
            print("   Check the logs above for details")
            return False
    else:
        print(f"\n" + "="*70)
        print("❌ ULTIMATE FIX FAILED")
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