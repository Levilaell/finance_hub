#!/usr/bin/env python
"""
RAILWAY PRODUCTION VALIDATION
Quick validation script for Railway deployment issues
"""
import os
import sys
import warnings
warnings.filterwarnings('ignore')  # Suppress Django warnings for clean output

# Setup minimal Django for database access
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
sys.path.insert(0, '/app')  # Railway path

try:
    import django
    django.setup()
    from django.db import connection
    from django.db.migrations.recorder import MigrationRecorder
    django_available = True
except ImportError as e:
    print(f"Django not available: {e}")
    django_available = False

def quick_validation():
    """Quick validation for Railway"""
    if not django_available:
        return
        
    print("=== RAILWAY PRODUCTION VALIDATION ===")
    
    try:
        with connection.cursor() as cursor:
            # 1. Early access fields check
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'companies' 
                AND column_name LIKE '%early_access%'
                ORDER BY column_name;
            """)
            ea_fields = [row[0] for row in cursor.fetchall()]
            print(f"Early access fields: {ea_fields}")
            
            # 2. Migration status
            cursor.execute("""
                SELECT app, name 
                FROM django_migrations 
                WHERE (app = 'companies' AND name IN ('0008_alter_resourceusage_options_and_more', '0009_add_early_access'))
                OR (app = 'notifications' AND name IN ('0002_add_event_key', '0003_cleanup_old_fields'))
                ORDER BY app, name;
            """)
            critical_migrations = cursor.fetchall()
            print(f"Critical migrations: {len(critical_migrations)}")
            for app, name in critical_migrations:
                print(f"  - {app}.{name}")
            
            # 3. Check for duplicate early access table
            cursor.execute("""
                SELECT count(*) 
                FROM information_schema.tables 
                WHERE table_name = 'early_access_invites';
            """)
            ea_table_count = cursor.fetchone()[0]
            print(f"Early access table exists: {ea_table_count > 0}")
            
            # 4. Environment check
            print(f"AI_INSIGHTS_ENCRYPTION_KEY set: {'AI_INSIGHTS_ENCRYPTION_KEY' in os.environ}")
            print(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
            
            # 5. Quick model import test
            try:
                from apps.companies.models import Company, EarlyAccessInvite
                from apps.notifications.models import Notification
                print("Model imports: OK")
            except Exception as e:
                print(f"Model imports failed: {e}")
                
    except Exception as e:
        print(f"Validation error: {e}")

if __name__ == '__main__':
    quick_validation()