#!/usr/bin/env python
"""
Script to fix foreign key constraint issue in production
This fixes the payments_subscription.plan_id constraint to point to the correct table
"""
import os
import django
from django.core.management import execute_from_command_line

# Set up Django environment for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.db import connection, transaction
import logging

logger = logging.getLogger(__name__)

def fix_foreign_key_constraint():
    """Fix the foreign key constraint pointing to wrong table"""
    
    print("🔍 Checking current foreign key constraint...")
    
    with connection.cursor() as cursor:
        # Check current constraint
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
        if not constraint:
            print("❌ No FK constraint found for plan_id")
            return False
        
        constraint_name, column_name, foreign_table, foreign_column = constraint
        print(f"Current constraint: {constraint_name}")
        print(f"Points to: {foreign_table}.{foreign_column}")
        
        # Check if correct table exists
        cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_name = 'subscription_plans'
        """)
        subscription_plans_exists = cursor.fetchone()[0] > 0
        
        cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_name = 'companies_subscriptionplan'  
        """)
        companies_table_exists = cursor.fetchone()[0] > 0
        
        print(f"subscription_plans table exists: {subscription_plans_exists}")
        print(f"companies_subscriptionplan table exists: {companies_table_exists}")
        
        # Check if plan ID 2 exists in correct table
        correct_table = None
        if subscription_plans_exists:
            cursor.execute("SELECT COUNT(*) FROM subscription_plans WHERE id = 2")
            count = cursor.fetchone()[0]
            print(f"Plan ID 2 exists in subscription_plans: {count > 0}")
            if count > 0:
                correct_table = 'subscription_plans'
        
        if companies_table_exists:
            cursor.execute("SELECT COUNT(*) FROM companies_subscriptionplan WHERE id = 2") 
            count = cursor.fetchone()[0]
            print(f"Plan ID 2 exists in companies_subscriptionplan: {count > 0}")
            if count > 0 and not correct_table:
                correct_table = 'companies_subscriptionplan'
        
        if not correct_table:
            print("❌ Plan ID 2 not found in any subscription plan table")
            return False
        
        # If constraint points to wrong table, fix it
        if foreign_table != correct_table:
            print(f"\n🔧 Fixing FK constraint to point to {correct_table}...")
            
            with transaction.atomic():
                # Drop old constraint
                cursor.execute(f"ALTER TABLE payments_subscription DROP CONSTRAINT {constraint_name}")
                print(f"✅ Dropped old constraint {constraint_name}")
                
                # Add new constraint pointing to correct table
                new_constraint_name = f"payments_subscription_plan_id_fk"
                cursor.execute(f"""
                ALTER TABLE payments_subscription 
                ADD CONSTRAINT {new_constraint_name}
                FOREIGN KEY (plan_id) REFERENCES {correct_table}(id) 
                DEFERRABLE INITIALLY DEFERRED
                """)
                print(f"✅ Created new constraint {new_constraint_name}")
                
            print("🎉 Foreign key constraint fixed successfully!")
            return True
        else:
            print("✅ FK constraint already points to correct table")
            
            # Still check if plan exists
            cursor.execute(f"SELECT name FROM {correct_table} WHERE id = 2")
            plan = cursor.fetchone()
            if plan:
                print(f"✅ Plan ID 2 ({plan[0]}) exists in {correct_table}")
                return True
            else:
                print(f"❌ Plan ID 2 not found in {correct_table}")
                return False

if __name__ == "__main__":
    try:
        success = fix_foreign_key_constraint()
        if success:
            print("\n✅ Database constraint issue resolved!")
        else:
            print("\n❌ Could not resolve database constraint issue")
    except Exception as e:
        print(f"\n❌ Error: {e}")