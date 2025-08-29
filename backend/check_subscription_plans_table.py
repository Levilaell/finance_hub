#!/usr/bin/env python
"""
Check subscription_plans table
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.db import connection

def main():
    with connection.cursor() as cursor:
        # Check if subscription_plans table exists
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'subscription_plans'
        );
        """)
        table_exists = cursor.fetchone()[0]
        print(f"subscription_plans table exists: {table_exists}")
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM subscription_plans")
            count = cursor.fetchone()[0]
            print(f"subscription_plans records: {count}")
            
            if count > 0:
                cursor.execute("SELECT id, name FROM subscription_plans ORDER BY id")
                plans = cursor.fetchall()
                print("Plans:")
                for plan in plans:
                    print(f"  ID: {plan[0]}, Name: {plan[1]}")
            else:
                print("❌ subscription_plans table is EMPTY!")
                print("💡 Need to populate this table")
        else:
            print("❌ subscription_plans table does NOT exist!")
        
        # Check companies_subscriptionplan exists and has data
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'companies_subscriptionplan'
        );
        """)
        companies_exists = cursor.fetchone()[0]
        
        if companies_exists:
            cursor.execute("SELECT COUNT(*) FROM companies_subscriptionplan")
            companies_count = cursor.fetchone()[0]
            print(f"\ncompanies_subscriptionplan records: {companies_count}")
            
            if companies_count > 0:
                cursor.execute("SELECT id, name FROM companies_subscriptionplan ORDER BY id")
                companies_plans = cursor.fetchall()
                print("Companies plans:")
                for plan in companies_plans:
                    print(f"  ID: {plan[0]}, Name: {plan[1]}")

if __name__ == "__main__":
    main()