"""
Consolidate subscription plans - merge payments_subscriptionplan into subscription_plans
and update all references
"""
from django.db import migrations, connection


def consolidate_subscription_plans(apps, schema_editor):
    """
    Merge data from payments_subscriptionplan into subscription_plans
    and ensure companies are using the correct plans
    """
    with connection.cursor() as cursor:
        # First, check if payments_subscriptionplan exists and has data
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'payments_subscriptionplan'
            );
        """)
        if not cursor.fetchone()[0]:
            return  # Table doesn't exist, nothing to do
        
        # Get existing plans from subscription_plans
        cursor.execute("SELECT id, slug FROM subscription_plans;")
        existing_plans = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Insert or update plans from payments_subscriptionplan
        cursor.execute("""
            SELECT name, price_monthly, price_yearly, max_transactions, 
                   max_bank_accounts, max_ai_requests
            FROM payments_subscriptionplan;
        """)
        
        payments_plans = cursor.fetchall()
        
        for plan in payments_plans:
            name, price_monthly, price_yearly, max_trans, max_banks, max_ai = plan
            slug = name.lower()
            
            if slug in existing_plans:
                # Update existing plan with better data from payments
                cursor.execute("""
                    UPDATE subscription_plans 
                    SET price_monthly = %s, price_yearly = %s,
                        max_transactions = %s, max_bank_accounts = %s,
                        max_ai_requests_per_month = %s,
                        name = %s
                    WHERE slug = %s;
                """, (price_monthly, price_yearly, max_trans, max_banks, 
                      max_ai, name.capitalize(), slug))
            else:
                # Insert new plan
                cursor.execute("""
                    INSERT INTO subscription_plans (
                        name, slug, plan_type, price_monthly, price_yearly,
                        max_transactions, max_bank_accounts, max_ai_requests_per_month,
                        trial_days, has_ai_categorization, enable_ai_insights,
                        enable_ai_reports, has_advanced_reports, has_api_access,
                        has_accountant_access, has_priority_support,
                        display_order, is_active, created_at, updated_at
                    ) VALUES (
                        %s, %s, 'standard', %s, %s, %s, %s, %s,
                        14, true, true, false, false, false, false, false,
                        0, true, NOW(), NOW()
                    );
                """, (name.capitalize(), slug, price_monthly, price_yearly,
                      max_trans, max_banks, max_ai))
        
        # Update feature flags based on plan type
        cursor.execute("""
            UPDATE subscription_plans 
            SET enable_ai_reports = true,
                has_advanced_reports = true,
                has_api_access = true
            WHERE slug = 'professional';
        """)
        
        cursor.execute("""
            UPDATE subscription_plans 
            SET enable_ai_reports = true,
                has_advanced_reports = true,
                has_api_access = true,
                has_accountant_access = true,
                has_priority_support = true
            WHERE slug = 'enterprise';
        """)


def reverse_consolidation(apps, schema_editor):
    """
    This migration is not reversible as it merges data
    """
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('companies', '0012_add_notification_fields'),
    ]

    operations = [
        migrations.RunPython(
            consolidate_subscription_plans,
            reverse_consolidation,
        ),
    ]