# Companies App Simplification - Implementation Guide

## Overview
This guide provides step-by-step instructions for implementing the simplified companies app design.

## Implementation Steps

### Step 1: Backup Current Implementation
```bash
# Create backup directory
mkdir backend/apps/companies/legacy

# Copy current files
cp backend/apps/companies/models.py backend/apps/companies/legacy/
cp backend/apps/companies/serializers.py backend/apps/companies/legacy/
cp backend/apps/companies/views.py backend/apps/companies/legacy/
cp backend/apps/companies/urls.py backend/apps/companies/legacy/
cp backend/apps/companies/admin.py backend/apps/companies/legacy/
```

### Step 2: Replace Backend Files
```bash
# Replace with simplified versions
mv backend/apps/companies/models_redesigned.py backend/apps/companies/models.py
mv backend/apps/companies/serializers_redesigned.py backend/apps/companies/serializers.py
mv backend/apps/companies/views_redesigned.py backend/apps/companies/views.py
mv backend/apps/companies/urls_redesigned.py backend/apps/companies/urls.py
mv backend/apps/companies/admin_redesigned.py backend/apps/companies/admin.py
```

### Step 3: Clean Up Management Commands
```bash
# Remove non-essential commands
cd backend/apps/companies/management/commands/
rm billing_report.py check_limits.py check_stripe_fields.py
rm check_user_trial.py create_user_companies.py debug_usage_counter.py
rm diagnose_counter_issue.py fix_production_counter.py fix_trial_dates.py
rm list_plans_for_stripe.py populate_usage.py recalculate_usage.py
rm seed_plans.py simulate_payment.py test_plan_limits.py
rm update_stripe_prices.py update_stripe_prices_prod.py

# Replace with simplified commands
mv create_subscription_plans_simplified.py create_subscription_plans.py
mv fix_usage_counters_simplified.py fix_usage_counters.py
mv check_usage_simplified.py check_usage.py
```

### Step 4: Create Database Migration
```python
# Create migration file: backend/apps/companies/migrations/0002_simplify_models.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('companies', '0001_initial'),
    ]

    operations = [
        # First, create payment app models if not exists
        migrations.RunSQL(
            "CREATE TABLE IF NOT EXISTS payment_methods AS SELECT * FROM payment_methods WHERE 1=0;",
            reverse_sql="DROP TABLE IF EXISTS payment_methods;"
        ),
        migrations.RunSQL(
            "CREATE TABLE IF NOT EXISTS payment_history AS SELECT * FROM payment_history WHERE 1=0;",
            reverse_sql="DROP TABLE IF EXISTS payment_history;"
        ),
        
        # Copy payment data to new tables
        migrations.RunSQL(
            "INSERT INTO payment_app_payment_methods SELECT * FROM payment_methods;",
            reverse_sql="DELETE FROM payment_app_payment_methods;"
        ),
        migrations.RunSQL(
            "INSERT INTO payment_app_payment_history SELECT * FROM payment_history;",
            reverse_sql="DELETE FROM payment_app_payment_history;"
        ),
        
        # Remove unnecessary fields from Company
        migrations.RemoveField(model_name='company', name='trade_name'),
        migrations.RemoveField(model_name='company', name='cnpj'),
        migrations.RemoveField(model_name='company', name='company_type'),
        migrations.RemoveField(model_name='company', name='business_sector'),
        migrations.RemoveField(model_name='company', name='email'),
        migrations.RemoveField(model_name='company', name='phone'),
        migrations.RemoveField(model_name='company', name='website'),
        migrations.RemoveField(model_name='company', name='address_street'),
        migrations.RemoveField(model_name='company', name='address_number'),
        migrations.RemoveField(model_name='company', name='address_complement'),
        migrations.RemoveField(model_name='company', name='address_neighborhood'),
        migrations.RemoveField(model_name='company', name='address_city'),
        migrations.RemoveField(model_name='company', name='address_state'),
        migrations.RemoveField(model_name='company', name='address_zipcode'),
        migrations.RemoveField(model_name='company', name='monthly_revenue'),
        migrations.RemoveField(model_name='company', name='employee_count'),
        migrations.RemoveField(model_name='company', name='logo'),
        migrations.RemoveField(model_name='company', name='primary_color'),
        migrations.RemoveField(model_name='company', name='currency'),
        migrations.RemoveField(model_name='company', name='fiscal_year_start'),
        migrations.RemoveField(model_name='company', name='enable_ai_categorization'),
        migrations.RemoveField(model_name='company', name='auto_categorize_threshold'),
        migrations.RemoveField(model_name='company', name='enable_notifications'),
        migrations.RemoveField(model_name='company', name='enable_email_reports'),
        migrations.RemoveField(model_name='company', name='next_billing_date'),
        migrations.RemoveField(model_name='company', name='subscription_start_date'),
        migrations.RemoveField(model_name='company', name='subscription_end_date'),
        migrations.RemoveField(model_name='company', name='last_usage_reset'),
        migrations.RemoveField(model_name='company', name='notified_80_percent'),
        migrations.RemoveField(model_name='company', name='notified_90_percent'),
        
        # Remove unnecessary fields from SubscriptionPlan
        migrations.RemoveField(model_name='subscriptionplan', name='plan_type'),
        migrations.RemoveField(model_name='subscriptionplan', name='trial_days'),
        migrations.RemoveField(model_name='subscriptionplan', name='mercadopago_plan_id'),
        migrations.RemoveField(model_name='subscriptionplan', name='has_ai_categorization'),
        migrations.RemoveField(model_name='subscriptionplan', name='enable_ai_reports'),
        migrations.RemoveField(model_name='subscriptionplan', name='has_api_access'),
        migrations.RemoveField(model_name='subscriptionplan', name='has_accountant_access'),
        migrations.RemoveField(model_name='subscriptionplan', name='has_priority_support'),
        
        # Rename field for clarity
        migrations.RenameField(
            model_name='subscriptionplan',
            old_name='enable_ai_insights',
            new_name='has_ai_insights'
        ),
        
        # Delete models that moved to payments app
        migrations.DeleteModel(name='PaymentMethod'),
        migrations.DeleteModel(name='PaymentHistory'),
        migrations.DeleteModel(name='CompanyUser'),
    ]
```

### Step 5: Update Frontend Services
```bash
# Replace subscription service
mv frontend/services/subscription.service.simplified.ts frontend/services/subscription.service.ts

# Update imports in components
# Replace all imports of billing.service with payment.service
# Update UsageIndicators component
mv frontend/components/UsageIndicators.simplified.tsx frontend/components/UsageIndicators.tsx
```

### Step 6: Update Related Apps

#### Update Banking App
```python
# In banking/models.py Transaction model, update increment method:
def save(self, *args, **kwargs):
    is_new = not self.pk
    super().save(*args, **kwargs)
    
    if is_new and self.company:
        # Use simplified increment method
        self.company.increment_usage('transactions')
```

#### Update AI Insights App
```python
# In ai_insights views, update AI usage tracking:
def create_insight(request):
    # ... existing code ...
    
    # Check AI limit
    limit_reached, usage_info = company.check_limit('ai_requests')
    if limit_reached:
        return Response({'error': f'AI limit reached: {usage_info}'}, status=400)
    
    # ... create insight ...
    
    # Increment usage
    company.increment_usage('ai_requests')
```

### Step 7: Run Migrations
```bash
# Apply migrations
python manage.py migrate companies

# Create subscription plans
python manage.py create_subscription_plans

# Fix any usage counters
python manage.py fix_usage_counters
```

### Step 8: Test Implementation
```bash
# Run tests
python manage.py test apps.companies

# Check usage for all companies
python manage.py check_usage

# Test API endpoints
curl http://localhost:8000/api/companies/plans/
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/companies/detail/
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/companies/usage-limits/
```

## Rollback Instructions
If issues arise, rollback using:
```bash
# Restore original files
cp backend/apps/companies/legacy/* backend/apps/companies/
# Reverse migration
python manage.py migrate companies 0001_initial
```

## Benefits Summary
- **80% code reduction** (719 → ~150 lines in models)
- **Simpler API** (4 endpoints vs 15+)
- **Cleaner separation** (payments moved to payments app)
- **Easier testing** (fewer edge cases)
- **Better maintainability** (focused on core functionality)