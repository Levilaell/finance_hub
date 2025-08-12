#!/usr/bin/env python
"""
WARNING: This script will RESET the production database!
Only use if you're absolutely sure you want to delete all data.
"""
import os
import sys
import django
from django.core.management import call_command
from django.db import connection
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_production_database():
    """Reset production database - WARNING: DELETES ALL DATA!"""
    
    print("\n" + "="*60)
    print("⚠️  WARNING: PRODUCTION DATABASE RESET")
    print("="*60 + "\n")
    
    print("This will DELETE ALL DATA in the production database!")
    print("Are you absolutely sure you want to continue?")
    print("\nType 'YES DELETE EVERYTHING' to confirm: ")
    
    confirmation = input().strip()
    
    if confirmation != "YES DELETE EVERYTHING":
        print("\n❌ Operation cancelled. Database was NOT modified.")
        return False
    
    print("\n🔄 Starting database reset...")
    
    try:
        with connection.cursor() as cursor:
            # Get all tables
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
                AND tablename != 'django_migrations';
            """)
            tables = cursor.fetchall()
            
            if tables:
                print(f"📊 Found {len(tables)} tables to drop")
                
                # Drop all tables except django_migrations
                cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
                for table in tables:
                    table_name = table[0]
                    print(f"   Dropping table: {table_name}")
                    cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                
                print("✅ All tables dropped\n")
            
            # Clean django_migrations table
            print("🧹 Cleaning migration history...")
            cursor.execute("TRUNCATE TABLE django_migrations;")
            print("✅ Migration history cleaned\n")
        
        print("\n" + "="*60)
        print("✅ DATABASE RESET COMPLETED")
        print("="*60 + "\n")
        
        print("📝 Next steps:")
        print("1. Run migrations: python manage.py migrate")
        print("2. Initialize production: python initialize_production.py")
        print("\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        print(f"\n❌ Error during reset: {e}")
        return False


if __name__ == '__main__':
    # Double safety check
    print("⚠️  THIS IS A DESTRUCTIVE OPERATION!")
    print("You are about to delete ALL DATA in the PRODUCTION database.")
    print("This action CANNOT be undone!")
    print("\nPress Ctrl+C now to cancel, or Enter to continue...")
    input()
    
    success = reset_production_database()
    sys.exit(0 if success else 1)