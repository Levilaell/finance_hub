# Companies App Simplification - Migration Plan

## Overview
This document outlines the migration from the complex companies app to a simplified version that maintains only essential functionality.

## Removed Features
1. **Multi-user support** (CompanyUser model)
2. **Payment methods management** (moved to payments app)
3. **Payment history** (moved to payments app)
4. **Complex company profile fields** (address, business metrics, customization)
5. **Notification preferences**
6. **20+ management commands** (kept only 3 essential ones)

## Data Migration Strategy

### Phase 1: Database Migration
```python
# Migration to simplify Company model
class Migration(migrations.Migration):
    operations = [
        # Remove unnecessary fields
        migrations.RemoveField(model_name='company', name='trade_name'),
        migrations.RemoveField(model_name='company', name='cnpj'),
        migrations.RemoveField(model_name='company', name='company_type'),
        migrations.RemoveField(model_name='company', name='business_sector'),
        migrations.RemoveField(model_name='company', name='email'),
        migrations.RemoveField(model_name='company', name='phone'),
        migrations.RemoveField(model_name='company', name='website'),
        # ... remove all address fields
        migrations.RemoveField(model_name='company', name='monthly_revenue'),
        migrations.RemoveField(model_name='company', name='employee_count'),
        migrations.RemoveField(model_name='company', name='logo'),
        migrations.RemoveField(model_name='company', name='primary_color'),
        migrations.RemoveField(model_name='company', name='currency'),
        migrations.RemoveField(model_name='company', name='fiscal_year_start'),
        # ... remove notification fields
    ]
```

### Phase 2: Move Payment Data
```python
# Move PaymentMethod and PaymentHistory to payments app
# 1. Create models in payments app
# 2. Data migration to copy records
# 3. Update foreign keys
# 4. Delete old models
```

### Phase 3: API Endpoints Update
- `/api/companies/subscription/upgrade/` → Move to payments app
- `/api/companies/subscription/cancel/` → Move to payments app  
- `/api/companies/billing/*` → Move to payments app
- Keep only:
  - `/api/companies/plans/`
  - `/api/companies/detail/`
  - `/api/companies/usage-limits/`
  - `/api/companies/subscription-status/`

## Frontend Updates Required

### Services to Update
1. `billing.service.ts` → Move to `payment.service.ts`
2. `subscription.service.ts` → Simplify to use new endpoints

### Components to Update
1. Settings page - Remove company profile editing
2. Billing components - Move to payments app
3. Usage indicators - Simplify to use new API

## Rollback Plan
1. Keep backup of original models as `models_legacy.py`
2. Database backup before migration
3. Feature flag to switch between old/new implementation
4. Gradual rollout with monitoring

## Benefits
1. **Code reduction**: ~80% less code to maintain
2. **Simpler testing**: Fewer edge cases
3. **Better separation**: Payment logic moved to payments app
4. **Cleaner API**: Only essential endpoints
5. **Easier onboarding**: Less complex for new developers