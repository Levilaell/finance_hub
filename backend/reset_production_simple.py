#!/usr/bin/env python
"""
Simple script to reset production database
Use this to clean all tables and start fresh
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.core.management import call_command
from django.db import connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_database():
    """Reset database by dropping all tables"""
    
    print("\n" + "="*60)
    print("RESETTING PRODUCTION DATABASE")
    print("="*60 + "\n")
    
    try:
        with connection.cursor() as cursor:
            # Get all tables
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public';
            """)
            tables = cursor.fetchall()
            
            if tables:
                print(f"Found {len(tables)} tables to drop")
                
                # Disable foreign key checks
                cursor.execute("SET session_replication_role = replica;")
                
                # Drop all tables
                for table in tables:
                    table_name = table[0]
                    print(f"  Dropping: {table_name}")
                    cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                
                # Re-enable foreign key checks
                cursor.execute("SET session_replication_role = DEFAULT;")
                
                print("\n✅ All tables dropped successfully\n")
            else:
                print("No tables found to drop\n")
        
        # Now run migrations from scratch
        print("Running migrations...")
        call_command('migrate', '--noinput')
        print("✅ Migrations completed\n")
        
        # Create initial data
        print("Creating subscription plans...")
        try:
            call_command('create_subscription_plans')
            print("✅ Subscription plans created\n")
        except Exception as e:
            print(f"⚠️  Could not create subscription plans: {e}\n")
        
        print("="*60)
        print("✨ DATABASE RESET COMPLETED!")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        print(f"\n❌ Error: {e}")
        return False


if __name__ == '__main__':
    success = reset_database()
    sys.exit(0 if success else 1)