#!/usr/bin/env python
"""
Debug subscription constraint issue
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
        # Check if payments_subscriptionplan table exists
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'payments_subscriptionplan'
        );
        """)
        payments_table_exists = cursor.fetchone()[0]
        print(f"payments_subscriptionplan table exists: {payments_table_exists}")
        
        # Check if companies_subscriptionplan table exists
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'companies_subscriptionplan'
        );
        """)
        companies_table_exists = cursor.fetchone()[0]
        print(f"companies_subscriptionplan table exists: {companies_table_exists}")
        
        # Check constraint on payments_subscription table
        cursor.execute("""
        SELECT 
            tc.constraint_name, 
            tc.table_name, 
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_name = 'payments_subscription'
        AND kcu.column_name = 'plan_id';
        """)
        
        constraints = cursor.fetchall()
        print(f"\nForeign key constraints on payments_subscription.plan_id:")
        for constraint in constraints:
            print(f"  {constraint[0]} -> {constraint[3]}.{constraint[4]}")
            
        # Count plans in both tables
        if companies_table_exists:
            cursor.execute("SELECT COUNT(*) FROM companies_subscriptionplan")
            companies_count = cursor.fetchone()[0]
            print(f"\ncompanies_subscriptionplan records: {companies_count}")
            
            if companies_count > 0:
                cursor.execute("SELECT id, name FROM companies_subscriptionplan ORDER BY id")
                companies_plans = cursor.fetchall()
                print("Companies plans:")
                for plan in companies_plans:
                    print(f"  ID: {plan[0]}, Name: {plan[1]}")
        
        if payments_table_exists:
            cursor.execute("SELECT COUNT(*) FROM payments_subscriptionplan")
            payments_count = cursor.fetchone()[0]
            print(f"\npayments_subscriptionplan records: {payments_count}")

if __name__ == "__main__":
    main()