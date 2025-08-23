#!/usr/bin/env python3
"""
ULTRA-DEEP DIAGNOSTIC: Early Access Column Conflict Analysis
===========================================================

Analyzes the exact cause of DuplicateColumn error for early_access_expires_at
and provides comprehensive resolution strategy.

COMPREHENSIVE ANALYSIS SCOPE:
- Database schema analysis (actual columns in companies table)
- Django migration state (which migrations Django thinks are applied)
- Migration file analysis (what each migration attempts to do)  
- Conflict identification (exact mismatch between schema and migrations)
- Resolution strategy (safe fix without data loss)
"""

import os
import sys
import django
from datetime import datetime

# Setup Django (use production for Railway diagnosis)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

try:
    django.setup()
    from django.db import connection, transaction
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

def analyze_early_access_conflict():
    """Ultra-deep analysis of early access column conflict"""
    print("🔍 ULTRA-DEEP DIAGNOSTIC: Early Access Column Conflict")
    print("=" * 70)
    print(f"📅 Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        with connection.cursor() as cursor:
            
            # PHASE 1: Analyze actual database schema
            print("🔍 PHASE 1: DATABASE SCHEMA ANALYSIS")
            print("-" * 50)
            
            # Check if companies table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'companies'
                );
            """)
            companies_exists = cursor.fetchone()[0]
            print(f"📊 Companies table exists: {companies_exists}")
            
            if companies_exists:
                # Get all columns in companies table
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'companies' 
                    ORDER BY ordinal_position;
                """)
                columns = cursor.fetchall()
                
                print(f"📋 Companies table has {len(columns)} columns:")
                
                early_access_columns = []
                for col_name, data_type, is_nullable, default in columns:
                    if 'early_access' in col_name.lower():
                        early_access_columns.append((col_name, data_type, is_nullable, default))
                        print(f"   🔍 EARLY ACCESS COLUMN: {col_name} ({data_type}, nullable={is_nullable}, default={default})")
                    elif col_name in ['is_early_access', 'used_invite_code']:
                        early_access_columns.append((col_name, data_type, is_nullable, default))
                        print(f"   🔍 RELATED COLUMN: {col_name} ({data_type}, nullable={is_nullable}, default={default})")
                
                if not early_access_columns:
                    print("   ⚠️  No early access related columns found in database")
                else:
                    print(f"   ✅ Found {len(early_access_columns)} early access related columns")
                
                # Check subscription_status field and its constraints
                cursor.execute("""
                    SELECT column_name, data_type, character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_name = 'companies' AND column_name = 'subscription_status';
                """)
                status_col = cursor.fetchone()
                if status_col:
                    print(f"   📋 subscription_status: {status_col[1]} (max_length={status_col[2]})")
            
            # PHASE 2: Analyze Django migration state
            print(f"\n🔍 PHASE 2: DJANGO MIGRATION STATE ANALYSIS")
            print("-" * 50)
            
            # Check which companies migrations are applied
            cursor.execute("""
                SELECT name, applied 
                FROM django_migrations 
                WHERE app = 'companies' 
                ORDER BY applied;
            """)
            companies_migrations = cursor.fetchall()
            
            print(f"📊 Found {len(companies_migrations)} applied companies migrations:")
            migration_0009_applied = False
            for name, applied in companies_migrations:
                print(f"   ✅ {name} -> {applied}")
                if name == '0009_add_early_access':
                    migration_0009_applied = True
            
            # PHASE 3: Critical conflict analysis  
            print(f"\n🎯 PHASE 3: CONFLICT ANALYSIS")
            print("-" * 50)
            
            print(f"🔍 Migration 0009_add_early_access status: {'APPLIED' if migration_0009_applied else 'NOT APPLIED'}")
            print(f"🔍 Early access columns in database: {len(early_access_columns)} found")
            
            # Check for specific columns that migration 0009 tries to add
            target_columns = ['is_early_access', 'early_access_expires_at', 'used_invite_code']
            existing_target_columns = [col[0] for col in early_access_columns if col[0] in target_columns]
            
            print(f"\n📋 CONFLICT MATRIX:")
            for col in target_columns:
                exists_in_db = col in existing_target_columns
                print(f"   {col:<25} | Database: {'EXISTS' if exists_in_db else 'MISSING'} | Migration: {'WILL ADD' if not migration_0009_applied else 'DONE'}")
            
            # Identify the exact conflict
            conflict_type = None
            if migration_0009_applied and existing_target_columns:
                conflict_type = "DOUBLE_APPLICATION"
                print(f"\n🚨 CONFLICT TYPE: DOUBLE APPLICATION")
                print(f"   Migration 0009 is marked as applied, but columns exist")
                print(f"   This suggests the migration was applied twice or columns were added manually")
            elif not migration_0009_applied and existing_target_columns:
                conflict_type = "SCHEMA_AHEAD"
                print(f"\n🚨 CONFLICT TYPE: SCHEMA AHEAD OF MIGRATIONS")
                print(f"   Columns exist but migration 0009 not applied")
                print(f"   This suggests columns were added manually or migration state is corrupted")
            elif migration_0009_applied and not existing_target_columns:
                conflict_type = "MIGRATION_ROLLBACK"
                print(f"\n🚨 CONFLICT TYPE: MIGRATION ROLLBACK")
                print(f"   Migration marked as applied but columns missing")
                print(f"   This suggests migration was rolled back without updating state")
            else:
                conflict_type = "NORMAL"
                print(f"\n✅ NO CONFLICT DETECTED")
                print(f"   Migration state and database schema are consistent")
            
            # PHASE 4: Check EarlyAccessInvite table
            print(f"\n🔍 PHASE 4: EARLY ACCESS INVITE TABLE ANALYSIS")
            print("-" * 50)
            
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'early_access_invites'
                );
            """)
            invite_table_exists = cursor.fetchone()[0]
            print(f"📊 early_access_invites table exists: {invite_table_exists}")
            
            if invite_table_exists:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'early_access_invites' 
                    ORDER BY ordinal_position;
                """)
                invite_columns = cursor.fetchall()
                print(f"📋 EarlyAccessInvite table has {len(invite_columns)} columns:")
                for col_name, data_type, is_nullable in invite_columns:
                    print(f"   - {col_name} ({data_type}, nullable={is_nullable})")
            
            # PHASE 5: Generate resolution strategy
            print(f"\n🛠️  PHASE 5: RESOLUTION STRATEGY")
            print("-" * 50)
            
            if conflict_type == "DOUBLE_APPLICATION":
                print("📋 RECOMMENDED RESOLUTION: Skip AddField operations")
                print("   1. Create new migration that skips AddField if columns exist")
                print("   2. Use RunPython to check column existence before adding")
                print("   3. Only add missing columns, update subscription_status choices")
                
            elif conflict_type == "SCHEMA_AHEAD":
                print("📋 RECOMMENDED RESOLUTION: Mark migration as fake applied")
                print("   1. Use --fake flag to mark migration 0009 as applied without running it")
                print("   2. Verify all expected columns exist with correct data types")
                print("   3. Ensure subscription_status choices are updated")
                
            elif conflict_type == "MIGRATION_ROLLBACK":
                print("📋 RECOMMENDED RESOLUTION: Re-run migration or manual schema fix")
                print("   1. Either rollback migration 0009 in Django state")
                print("   2. Or manually add the missing columns to match migration")
                
            else:
                print("📋 RECOMMENDED RESOLUTION: Standard migration apply")
                print("   1. Run migration normally with 'python manage.py migrate'")
                print("   2. No conflicts detected")
            
            # PHASE 6: Safety recommendations
            print(f"\n🛡️  PHASE 6: SAFETY RECOMMENDATIONS")
            print("-" * 50)
            print("✅ SAFETY MEASURES:")
            print("   1. Always backup database before applying fixes")
            print("   2. Test resolution on staging environment first")
            print("   3. Use atomic transactions for all schema changes")
            print("   4. Verify data integrity after applying fixes")
            print("   5. Check that early access functionality works end-to-end")
            
            # PHASE 7: Detailed diagnostics
            print(f"\n📊 PHASE 7: DETAILED DIAGNOSTICS")
            print("-" * 50)
            
            # Get total counts
            if companies_exists:
                cursor.execute("SELECT COUNT(*) FROM companies;")
                company_count = cursor.fetchone()[0]
                print(f"📈 Total companies: {company_count}")
                
                if existing_target_columns and 'is_early_access' in existing_target_columns:
                    cursor.execute("SELECT COUNT(*) FROM companies WHERE is_early_access = true;")
                    early_access_count = cursor.fetchone()[0]
                    print(f"📈 Early access companies: {early_access_count}")
            
            if invite_table_exists:
                cursor.execute("SELECT COUNT(*) FROM early_access_invites;")
                invite_count = cursor.fetchone()[0]
                print(f"📈 Early access invites: {invite_count}")
            
            return {
                'conflict_type': conflict_type,
                'migration_0009_applied': migration_0009_applied,
                'columns_exist': len(existing_target_columns) > 0,
                'existing_columns': existing_target_columns,
                'invite_table_exists': invite_table_exists
            }
            
    except Exception as e:
        print(f"\n❌ DIAGNOSTIC FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main execution function"""
    print("🔍 ULTRA-DEEP DIAGNOSTIC: Early Access Migration Conflict")
    print("=" * 70)
    print("🎯 Target: Analyze and resolve DuplicateColumn error")
    print("⚡ Method: Comprehensive schema vs migration state analysis")
    print()
    
    result = analyze_early_access_conflict()
    
    if result:
        print(f"\n" + "="*70)
        print("🎯 DIAGNOSTIC SUMMARY")
        print("="*70)
        print(f"✅ Conflict type: {result['conflict_type']}")
        print(f"✅ Migration 0009 applied: {result['migration_0009_applied']}")  
        print(f"✅ Early access columns exist: {result['columns_exist']}")
        print(f"✅ Existing columns: {result['existing_columns']}")
        print(f"✅ Invite table exists: {result['invite_table_exists']}")
        print(f"\n🚀 Diagnostic complete - resolution strategy provided above")
        return True
    else:
        print(f"\n" + "="*70)
        print("❌ DIAGNOSTIC FAILED")
        print("   Check the logs above for error details")
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostic cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)