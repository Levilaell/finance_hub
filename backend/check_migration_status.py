#!/usr/bin/env python
"""
QUICK MIGRATION STATUS CHECKER

Quick verification script to check if auth migration dependencies are correct.
Use this to verify the state before and after running the ultimate fix.

EXECUTION:
Local:      python check_migration_status.py
Production: railway run python check_migration_status.py
"""

import os
import django
from datetime import datetime

# Setup Django
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
    django.setup()

from django.db import connection

def check_migration_status():
    """Quick check of migration status"""
    cursor = connection.cursor()
    
    print("=" * 60)
    print("🔍 DJANGO MIGRATION STATUS CHECKER")
    print("=" * 60)
    print(f"⏰ Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🗄️  Database: {connection.settings_dict['NAME']}")
    print()
    
    # Total migrations
    cursor.execute("SELECT COUNT(*) FROM django_migrations")
    total = cursor.fetchone()[0]
    print(f"📊 Total migrations: {total}")
    
    # Auth migrations count
    cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app = 'auth'")
    auth_count = cursor.fetchone()[0]
    print(f"🔐 Auth migrations: {auth_count}")
    
    # Critical auth migrations check
    cursor.execute("""
        SELECT name, applied 
        FROM django_migrations 
        WHERE app = 'auth' AND name IN ('0002_alter_permission_name_max_length', '0003_alter_user_email_max_length')
        ORDER BY applied
    """)
    critical_auths = cursor.fetchall()
    
    print("\n🎯 CRITICAL AUTH MIGRATIONS:")
    if len(critical_auths) == 2:
        for name, applied in critical_auths:
            print(f"   {name}: {applied}")
        
        first_migration = critical_auths[0][0]
        if first_migration == '0002_alter_permission_name_max_length':
            print("✅ ORDER: CORRECT - 0002 before 0003")
            order_ok = True
        else:
            print("❌ ORDER: WRONG - 0003 before 0002 (DEPENDENCY VIOLATION)")
            order_ok = False
    else:
        print(f"❌ ERROR: Found {len(critical_auths)} critical auth migrations (expected 2)")
        order_ok = False
    
    # Contenttypes dependency check
    cursor.execute("""
        SELECT applied FROM django_migrations 
        WHERE app = 'contenttypes' AND name = '0002_remove_content_type_name'
    """)
    ct_result = cursor.fetchone()
    
    cursor.execute("""
        SELECT applied FROM django_migrations 
        WHERE app = 'auth' AND name = '0006_require_contenttypes_0002'
    """)
    auth6_result = cursor.fetchone()
    
    print("\n🔗 CONTENTTYPES DEPENDENCY:")
    if ct_result and auth6_result:
        ct_time = ct_result[0]
        auth6_time = auth6_result[0]
        print(f"   contenttypes.0002: {ct_time}")
        print(f"   auth.0006: {auth6_time}")
        
        if ct_time < auth6_time:
            print("✅ DEPENDENCY: CORRECT - contenttypes.0002 before auth.0006")
            dep_ok = True
        else:
            print("❌ DEPENDENCY: WRONG - contenttypes.0002 after auth.0006")
            dep_ok = False
    else:
        print("❌ ERROR: Missing contenttypes or auth.0006 migrations")
        dep_ok = False
    
    # Final status
    print("\n" + "=" * 60)
    if order_ok and dep_ok:
        print("✅ OVERALL STATUS: ALL GOOD")
        print("🚀 Django should start without migration errors")
        exit_code = 0
    else:
        print("❌ OVERALL STATUS: ISSUES FOUND")
        print("🔧 Run ultimate_migration_fixer.py to fix these issues")
        exit_code = 1
    
    print("=" * 60)
    return exit_code

if __name__ == "__main__":
    import sys
    exit_code = check_migration_status()
    sys.exit(exit_code)