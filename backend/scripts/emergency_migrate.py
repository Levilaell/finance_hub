#!/usr/bin/env python
"""
Emergency migration script to ensure database is properly set up
This script checks and runs critical migrations
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

# Setup Django
django.setup()

from django.db import connection

def check_table_exists(table_name):
    """Check if a table exists in the database"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, [table_name])
        return cursor.fetchone()[0]

def main():
    print("🚨 Emergency Migration Check Starting...")
    
    # Check critical tables
    critical_tables = ['users', 'companies', 'django_migrations']
    
    for table in critical_tables:
        exists = check_table_exists(table)
        print(f"  Table '{table}': {'✅ EXISTS' if exists else '❌ MISSING'}")
        
        if not exists and table == 'users':
            print(f"  ⚠️  Critical table 'users' is missing!")
            print("  🔧 Running authentication migrations...")
            try:
                execute_from_command_line(['manage.py', 'migrate', 'authentication', '--no-input'])
                print("  ✅ Authentication migrations completed")
            except Exception as e:
                print(f"  ❌ Migration failed: {e}")
    
    # Check if django_migrations exists
    if not check_table_exists('django_migrations'):
        print("\n⚠️  django_migrations table missing - running initial migration")
        try:
            execute_from_command_line(['manage.py', 'migrate', '--no-input'])
            print("✅ Initial migrations completed")
        except Exception as e:
            print(f"❌ Initial migration failed: {e}")
    else:
        # Run any pending migrations
        print("\n🔄 Checking for pending migrations...")
        try:
            execute_from_command_line(['manage.py', 'migrate', '--no-input'])
            print("✅ All migrations completed successfully")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
    
    print("\n✅ Emergency migration check completed")

if __name__ == '__main__':
    main()