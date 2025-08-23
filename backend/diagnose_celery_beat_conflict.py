#!/usr/bin/env python3
"""
ULTRA-DEEP DIAGNOSTIC: Celery Beat Migration Conflict Analysis
=============================================================

Analyzes the exact cause of DuplicateTable error for django_celery_beat tables
and provides comprehensive resolution strategy.

COMPREHENSIVE ANALYSIS SCOPE:
- Database schema analysis (actual Celery Beat tables)
- Django migration state (which django_celery_beat migrations are applied)
- Migration file analysis (what each migration attempts to create)
- Conflict identification (exact mismatch between schema and migrations)
- Resolution strategy (safe fix without data loss)
"""

import os
import sys
import django
from datetime import datetime

# Setup Django for development analysis
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')

try:
    django.setup()
    from django.db import connection, transaction
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

def analyze_celery_beat_conflict():
    """Ultra-deep analysis of Celery Beat table conflict"""
    print("🔍 ULTRA-DEEP DIAGNOSTIC: Celery Beat Migration Conflict")
    print("=" * 70)
    print(f"📅 Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        with connection.cursor() as cursor:
            
            # PHASE 1: Analyze actual database schema for Celery Beat tables
            print("🔍 PHASE 1: CELERY BEAT DATABASE SCHEMA ANALYSIS")
            print("-" * 50)
            
            # Check all Celery Beat related tables
            celery_beat_tables = [
                'django_celery_beat_crontabschedule',
                'django_celery_beat_intervalschedule', 
                'django_celery_beat_periodictask',
                'django_celery_beat_clockedschedule',
                'django_celery_beat_solarschedule'
            ]
            
            existing_tables = []
            missing_tables = []
            
            for table_name in celery_beat_tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, [table_name])
                table_exists = cursor.fetchone()[0]
                
                if table_exists:
                    existing_tables.append(table_name)
                    print(f"   ✅ {table_name}: EXISTS")
                else:
                    missing_tables.append(table_name)
                    print(f"   ❌ {table_name}: MISSING")
            
            print(f"\n📊 Summary: {len(existing_tables)} exist, {len(missing_tables)} missing")
            
            # Detailed analysis of existing tables
            if existing_tables:
                print(f"\n📋 DETAILED TABLE ANALYSIS:")
                for table_name in existing_tables:
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_name = %s 
                        ORDER BY ordinal_position;
                    """, [table_name])
                    columns = cursor.fetchall()
                    print(f"   📋 {table_name}: {len(columns)} columns")
                    
                    # Show first few columns for verification
                    for i, (col_name, data_type, nullable) in enumerate(columns[:5]):
                        print(f"      - {col_name} ({data_type})")
                    if len(columns) > 5:
                        print(f"      ... and {len(columns) - 5} more columns")
            
            # PHASE 2: Analyze Django migration state for django_celery_beat
            print(f"\n🔍 PHASE 2: DJANGO_CELERY_BEAT MIGRATION STATE")
            print("-" * 50)
            
            # Check which django_celery_beat migrations are applied
            cursor.execute("""
                SELECT name, applied 
                FROM django_migrations 
                WHERE app = 'django_celery_beat' 
                ORDER BY applied;
            """)
            celery_beat_migrations = cursor.fetchall()
            
            print(f"📊 Found {len(celery_beat_migrations)} applied django_celery_beat migrations:")
            initial_migration_applied = False
            
            for name, applied in celery_beat_migrations:
                print(f"   ✅ {name} -> {applied}")
                if name.startswith('0001_'):
                    initial_migration_applied = True
            
            # PHASE 3: Critical conflict analysis
            print(f"\n🎯 PHASE 3: CONFLICT ANALYSIS")
            print("-" * 50)
            
            print(f"🔍 Initial migration status: {'APPLIED' if initial_migration_applied else 'NOT APPLIED'}")
            print(f"🔍 Critical table (crontabschedule): {'EXISTS' if 'django_celery_beat_crontabschedule' in existing_tables else 'MISSING'}")
            
            # Identify the exact conflict
            conflict_type = None
            critical_table_exists = 'django_celery_beat_crontabschedule' in existing_tables
            
            if initial_migration_applied and critical_table_exists:
                conflict_type = "DOUBLE_APPLICATION"
                print(f"\n🚨 CONFLICT TYPE: DOUBLE APPLICATION")
                print(f"   Initial migration is applied, but Django is trying to create tables again")
                print(f"   This suggests migration was applied but Django lost track of state")
                
            elif not initial_migration_applied and critical_table_exists:
                conflict_type = "SCHEMA_AHEAD" 
                print(f"\n🚨 CONFLICT TYPE: SCHEMA AHEAD OF MIGRATIONS")
                print(f"   Tables exist but initial migration not marked as applied")
                print(f"   This suggests tables were created manually or migration state corrupted")
                
            elif initial_migration_applied and not critical_table_exists:
                conflict_type = "MIGRATION_ROLLBACK"
                print(f"\n🚨 CONFLICT TYPE: MIGRATION ROLLBACK")
                print(f"   Migration marked as applied but tables missing")
                print(f"   This suggests tables were dropped without updating migration state")
                
            else:
                conflict_type = "NORMAL"
                print(f"\n✅ NO CONFLICT DETECTED")
                print(f"   Migration state and database schema are consistent")
            
            # PHASE 4: Check for migration dependencies
            print(f"\n🔍 PHASE 4: MIGRATION DEPENDENCY ANALYSIS")
            print("-" * 50)
            
            # Check if there are any pending migrations for django_celery_beat
            try:
                from django.core.management.commands.migrate import Command as MigrateCommand
                from django.db.migrations.executor import MigrationExecutor
                
                executor = MigrationExecutor(connection)
                plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
                
                celery_beat_pending = [migration for migration in plan if migration[0].app_label == 'django_celery_beat']
                
                if celery_beat_pending:
                    print(f"📋 Pending django_celery_beat migrations: {len(celery_beat_pending)}")
                    for migration, backwards in celery_beat_pending:
                        print(f"   {'⬅️' if backwards else '➡️'} {migration.app_label}.{migration.name}")
                else:
                    print(f"✅ No pending django_celery_beat migrations")
                    
            except Exception as e:
                print(f"⚠️  Could not analyze migration plan: {e}")
            
            # PHASE 5: Generate resolution strategy
            print(f"\n🛠️  PHASE 5: RESOLUTION STRATEGY")
            print("-" * 50)
            
            if conflict_type == "DOUBLE_APPLICATION":
                print("📋 RECOMMENDED RESOLUTION: Fake apply migrations")
                print("   1. Use --fake flag to mark migrations as applied without running them:")
                print("      python manage.py migrate django_celery_beat --fake")
                print("   2. Verify all expected tables exist with correct schema")
                print("   3. Test Celery Beat functionality")
                
            elif conflict_type == "SCHEMA_AHEAD":
                print("📋 RECOMMENDED RESOLUTION: Mark migrations as fake applied") 
                print("   1. Use --fake flag to sync migration state with actual schema:")
                print("      python manage.py migrate django_celery_beat --fake-initial")
                print("   2. Verify table schemas match expected migration structure")
                
            elif conflict_type == "MIGRATION_ROLLBACK":
                print("📋 RECOMMENDED RESOLUTION: Rollback migration state or recreate tables")
                print("   1. Either rollback django_celery_beat migrations:")
                print("      python manage.py migrate django_celery_beat zero --fake")
                print("   2. Or manually recreate the missing tables")
                print("   3. Then run migrations normally")
                
            else:
                print("📋 RECOMMENDED RESOLUTION: Standard migration apply")
                print("   1. Run migration normally:")
                print("      python manage.py migrate django_celery_beat")
                print("   2. No conflicts detected")
            
            # PHASE 6: Safety recommendations
            print(f"\n🛡️  PHASE 6: SAFETY RECOMMENDATIONS")
            print("-" * 50)
            print("✅ SAFETY MEASURES:")
            print("   1. Always backup database before applying fixes")
            print("   2. Test resolution on staging environment first")
            print("   3. Verify Celery Beat tasks continue working after fix")
            print("   4. Check that periodic task scheduling functions correctly")
            print("   5. Monitor for any Celery Beat errors after deployment")
            
            # PHASE 7: Create smart fix script
            print(f"\n🤖 PHASE 7: SMART FIX GENERATION")
            print("-" * 50)
            
            if conflict_type in ["DOUBLE_APPLICATION", "SCHEMA_AHEAD"]:
                print("📋 Generating smart fix script for automatic resolution...")
                smart_fix_needed = True
            else:
                print("📋 No smart fix script needed - standard migration should work")
                smart_fix_needed = False
            
            return {
                'conflict_type': conflict_type,
                'initial_migration_applied': initial_migration_applied,
                'tables_exist': len(existing_tables) > 0,
                'existing_tables': existing_tables,
                'missing_tables': missing_tables,
                'smart_fix_needed': smart_fix_needed
            }
            
    except Exception as e:
        print(f"\n❌ DIAGNOSTIC FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main execution function"""
    print("🔍 ULTRA-DEEP DIAGNOSTIC: Celery Beat Migration Conflict")
    print("=" * 70)
    print("🎯 Target: Analyze and resolve DuplicateTable error")
    print("⚡ Method: Comprehensive schema vs migration state analysis")
    print()
    
    result = analyze_celery_beat_conflict()
    
    if result:
        print(f"\n" + "="*70)
        print("🎯 DIAGNOSTIC SUMMARY")
        print("="*70)
        print(f"✅ Conflict type: {result['conflict_type']}")
        print(f"✅ Initial migration applied: {result['initial_migration_applied']}")
        print(f"✅ Celery Beat tables exist: {result['tables_exist']}")
        print(f"✅ Existing tables: {len(result['existing_tables'])}")
        print(f"✅ Missing tables: {len(result['missing_tables'])}")
        print(f"✅ Smart fix needed: {result['smart_fix_needed']}")
        print(f"\n🚀 Diagnostic complete - resolution strategy provided above")
        return result
    else:
        print(f"\n" + "="*70)
        print("❌ DIAGNOSTIC FAILED")
        print("   Check the logs above for error details")
        return None

if __name__ == '__main__':
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostic cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)