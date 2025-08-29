#!/usr/bin/env python
"""
Startup-safe script to fix foreign key constraint issue
This version handles startup environment better
"""
import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

try:
    import django
    django.setup()
    
    from django.db import connection, transaction
    
    def fix_foreign_key_constraint():
        """Fix the foreign key constraint pointing to wrong table"""
        
        try:
            with connection.cursor() as cursor:
                # Check current constraint
                cursor.execute("""
                SELECT 
                    tc.constraint_name,
                    ccu.table_name AS foreign_table_name
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
                    print("✅ No problematic FK constraint found")
                    return True
                
                constraint_name, foreign_table = constraint
                
                # Check if constraint points to wrong table
                if foreign_table == 'payments_subscriptionplan':
                    print(f"🔧 Found problematic constraint: {constraint_name}")
                    print(f"   Points to wrong table: {foreign_table}")
                    
                    # Check if correct table exists
                    cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'companies_subscriptionplan'
                    """)
                    correct_table_exists = cursor.fetchone()[0] > 0
                    
                    if not correct_table_exists:
                        print("❌ Correct table companies_subscriptionplan doesn't exist")
                        return False
                    
                    # Check if plan ID 2 exists in correct table
                    cursor.execute("SELECT COUNT(*) FROM companies_subscriptionplan WHERE id = 2")
                    plan_exists = cursor.fetchone()[0] > 0
                    
                    if not plan_exists:
                        print("❌ Plan ID 2 not found in companies_subscriptionplan")
                        return False
                    
                    # Fix the constraint
                    with transaction.atomic():
                        # Drop old constraint
                        cursor.execute(f"ALTER TABLE payments_subscription DROP CONSTRAINT {constraint_name}")
                        print(f"✅ Dropped old constraint {constraint_name}")
                        
                        # Add new constraint pointing to correct table
                        new_constraint_name = "payments_subscription_plan_id_fk"
                        cursor.execute(f"""
                        ALTER TABLE payments_subscription 
                        ADD CONSTRAINT {new_constraint_name}
                        FOREIGN KEY (plan_id) REFERENCES companies_subscriptionplan(id) 
                        DEFERRABLE INITIALLY DEFERRED
                        """)
                        print(f"✅ Created new constraint {new_constraint_name}")
                        
                    print("🎉 Foreign key constraint fixed successfully!")
                    return True
                else:
                    print(f"✅ FK constraint already points to correct table: {foreign_table}")
                    return True
                    
        except Exception as e:
            print(f"❌ Error fixing FK constraint: {e}")
            return False
    
    if __name__ == "__main__":
        success = fix_foreign_key_constraint()
        exit(0 if success else 1)
        
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    exit(1)