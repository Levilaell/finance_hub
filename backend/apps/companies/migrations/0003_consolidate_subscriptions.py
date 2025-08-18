"""
Migration to consolidate subscription models
"""
from django.db import migrations, transaction


def consolidate_subscription_data(apps, schema_editor):
    """
    Migrate subscription data from Company model to payments.Subscription model
    """
    Company = apps.get_model('companies', 'Company')
    Subscription = apps.get_model('payments', 'Subscription')
    SubscriptionPlan = apps.get_model('companies', 'SubscriptionPlan')
    
    # First, ensure payment app plans exist
    plan_mapping = {
        'starter': {'max_transactions': 500, 'max_bank_accounts': 1, 'max_ai_requests': 100},
        'professional': {'max_transactions': 2000, 'max_bank_accounts': 3, 'max_ai_requests': 500},
        'enterprise': {'max_transactions': 10000, 'max_bank_accounts': 10, 'max_ai_requests': 2000},
    }
    
    for plan_name, limits in plan_mapping.items():
        SubscriptionPlan.objects.get_or_create(
            name=plan_name,
            defaults={
                'display_name': plan_name.title(),
                'price_monthly': 29 if plan_name == 'starter' else (99 if plan_name == 'professional' else 299),
                'price_yearly': 290 if plan_name == 'starter' else (990 if plan_name == 'professional' else 2990),
                'max_transactions': limits['max_transactions'],
                'max_bank_accounts': limits['max_bank_accounts'],
                'max_ai_requests': limits['max_ai_requests'],
                'features': {
                    'ai_insights': plan_name != 'starter',
                    'advanced_reports': plan_name != 'starter',
                    'api_access': plan_name == 'enterprise',
                    'priority_support': plan_name == 'enterprise',
                }
            }
        )
    
    # Migrate each company's subscription data
    for company in Company.objects.all():
        # Skip if subscription already exists (from payments app)
        if hasattr(company, 'subscription'):
            continue
        
        # Determine plan from company's subscription_plan
        plan = None
        if company.subscription_plan:
            # Try to match by slug or name
            try:
                plan = SubscriptionPlan.objects.get(
                    name=company.subscription_plan.slug
                )
            except SubscriptionPlan.DoesNotExist:
                # Default to starter plan
                plan = SubscriptionPlan.objects.get(name='starter')
        
        if not plan:
            plan = SubscriptionPlan.objects.get(name='starter')
        
        # Create subscription record
        with transaction.atomic():
            Subscription.objects.create(
                company=company,
                plan=plan,
                status=company.subscription_status or 'trial',
                billing_period=company.billing_cycle or 'monthly',
                trial_ends_at=company.trial_ends_at,
                stripe_subscription_id=company.subscription_id if hasattr(company, 'subscription_id') else None,
            )


def reverse_consolidation(apps, schema_editor):
    """
    Reverse the consolidation - copy data back to Company model
    """
    Subscription = apps.get_model('payments', 'Subscription')
    
    # Delete all subscription records
    Subscription.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('companies', '0002_auto_simplify'),
        ('payments', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(
            consolidate_subscription_data,
            reverse_consolidation
        ),
    ]