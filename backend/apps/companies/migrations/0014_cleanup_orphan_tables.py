"""
Clean up orphan tables and consolidate payment-related tables
"""
from django.db import migrations, connection


def cleanup_orphan_tables(apps, schema_editor):
    """
    Remove orphan tables that don't have corresponding Django models
    and consolidate duplicate payment tables
    """
    with connection.cursor() as cursor:
        # List of tables to potentially remove (after checking they're empty or migrated)
        orphan_tables = [
            'payment_history',  # No Django model, appears to be legacy
            'payment_methods',  # Duplicate of payments_paymentmethod
            'notification_preferences',  # No Django model
            'company_users',  # No Django model, relationships handled differently
        ]
        
        duplicate_tables = [
            'payments_subscriptionplan',  # Already consolidated into subscription_plans
        ]
        
        # Check and drop orphan tables if they're empty
        for table in orphan_tables:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, [table])
            
            if cursor.fetchone()[0]:
                # Check if table has any data
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    # Safe to drop empty table
                    cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                    print(f"Dropped empty orphan table: {table}")
                else:
                    print(f"Warning: Table {table} has {count} rows, not dropping")
        
        # Drop duplicate subscription plan table after consolidation
        for table in duplicate_tables:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, [table])
            
            if cursor.fetchone()[0]:
                # This should be safe after consolidation migration
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"Dropped duplicate table: {table}")


def reverse_cleanup(apps, schema_editor):
    """
    This migration is not easily reversible as it drops tables
    """
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('companies', '0013_consolidate_subscription_plans'),
    ]

    operations = [
        migrations.RunPython(
            cleanup_orphan_tables,
            reverse_cleanup,
        ),
    ]