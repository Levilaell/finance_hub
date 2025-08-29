#!/usr/bin/env python
"""
Script to check migration status and foreign key constraints in production
"""
import os
import django
from django.core.management import execute_from_command_line

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.db import connection

def check_migrations():
    """Check migration status"""
    print("=== MIGRATION STATUS ===")
    execute_from_command_line(['manage.py', 'showmigrations'])

def check_foreign_keys():
    """Check foreign key constraints"""
    print("\n=== FOREIGN KEY CONSTRAINTS ===")
    cursor = connection.cursor()
    
    # Check payments_subscription constraints
    cursor.execute("""
    SELECT 
        tc.constraint_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu 
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu 
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name = 'payments_subscription'
        AND kcu.column_name = 'plan_id';
    """)
    
    constraint = cursor.fetchone()
    if constraint:
        print(f"payments_subscription.plan_id -> {constraint[2]}.{constraint[3]}")
        
        # Check if referenced table exists
        cursor.execute(f"SELECT COUNT(*) FROM {constraint[2]} WHERE id = 2")
        count = cursor.fetchone()[0] 
        print(f"Plan ID 2 exists in {constraint[2]}: {count > 0}")
    else:
        print("No FK constraint found for plan_id")

def check_tables():
    """Check subscription-related tables"""
    print("\n=== SUBSCRIPTION TABLES ===")
    cursor = connection.cursor()
    cursor.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_name LIKE '%subscription%' 
    ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    for table in tables:
        print(f"Table: {table[0]}")
        
        # Check record count if it's a subscription plan table
        if 'plan' in table[0]:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"  Records: {count}")
                
                if count > 0:
                    cursor.execute(f"SELECT id, name FROM {table[0]} LIMIT 5")
                    plans = cursor.fetchall()
                    for plan in plans:
                        print(f"    ID: {plan[0]}, Name: {plan[1]}")
            except Exception as e:
                print(f"  Error reading: {e}")

if __name__ == "__main__":
    check_migrations()
    check_foreign_keys()
    check_tables()