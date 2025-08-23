#!/usr/bin/env python
"""
ULTRA-DEEP ANALYSIS: Fix reports migration dependency issue
Problem: reports.0003 applied before its dependency reports.0002
Solution: Remove 0003 from django_migrations, allow correct order reapplication
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.db import connection

def fix_reports_migration_order():
    """Fix the migration dependency issue by removing 0003 from migration table"""
    
    print("🔍 ULTRA-DEEP ANALYSIS: Reports Migration Order Fix")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        # STEP 1: Check current state
        print("📊 STEP 1: Checking current migration state...")
        cursor.execute("""
            SELECT app, name, applied 
            FROM django_migrations 
            WHERE app = 'reports' 
            ORDER BY applied;
        """)
        
        current_migrations = cursor.fetchall()
        print(f"Found {len(current_migrations)} reports migrations:")
        for app, name, applied in current_migrations:
            print(f"  ✓ {app}.{name} (applied: {applied})")
        
        # Check if 0003 exists (the problematic one)
        problematic_exists = any(
            '0003_aianalysistemplate_aianalysis' in name 
            for _, name, _ in current_migrations
        )
        
        if not problematic_exists:
            print("❌ Migration 0003 not found in applied migrations")
            print("The issue may already be resolved or different than expected")
            return False
            
        # STEP 2: Remove problematic migration
        print("\n🔧 STEP 2: Removing problematic migration 0003...")
        cursor.execute("""
            DELETE FROM django_migrations 
            WHERE app = 'reports' AND name = '0003_aianalysistemplate_aianalysis';
        """)
        
        deleted_count = cursor.rowcount
        print(f"✅ Removed {deleted_count} migration record(s)")
        
        # STEP 3: Verify removal
        print("\n✅ STEP 3: Verifying removal...")
        cursor.execute("""
            SELECT app, name, applied 
            FROM django_migrations 
            WHERE app = 'reports' 
            ORDER BY applied;
        """)
        
        remaining_migrations = cursor.fetchall()
        print(f"Remaining {len(remaining_migrations)} reports migrations:")
        for app, name, applied in remaining_migrations:
            print(f"  ✓ {app}.{name} (applied: {applied})")
            
        print("\n🎯 NEXT STEPS:")
        print("1. Run: railway run python manage.py migrate reports")
        print("2. This will apply 0002 first, then 0003 in correct order")
        print("3. Verify with: railway run python manage.py showmigrations reports")
        
        return True

if __name__ == "__main__":
    try:
        success = fix_reports_migration_order()
        if success:
            print("\n✅ Migration order fix completed successfully!")
        else:
            print("\n❌ Migration order fix failed or not needed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)