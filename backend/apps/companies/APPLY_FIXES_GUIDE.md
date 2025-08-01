# How to Apply Companies Module Security Fixes

## Quick Start Commands

### 1. Run Tests First
```bash
# Run the security tests to verify current state
python manage.py test apps.companies.tests.test_security_fixes

# Run all company tests
python manage.py test apps.companies
```

### 2. Apply Database Migrations
```bash
# Make migrations if needed
python manage.py makemigrations companies

# Apply the consolidation migration
python manage.py migrate companies 0003

# Verify migration status
python manage.py showmigrations companies
```

### 3. Update Model References
Replace imports in your code:

```python
# OLD - Remove these
from apps.companies.models import SubscriptionPlan

# NEW - Use these
from apps.payments.models import SubscriptionPlan, Subscription
from apps.companies.models import Company, ResourceUsage
```

### 4. Verify Middleware is Active
```bash
# Check middleware configuration
python manage.py shell
>>> from django.conf import settings
>>> 'apps.companies.middleware.TrialExpirationMiddleware' in settings.MIDDLEWARE
True
```

### 5. Test API Endpoints
```bash
# Test with expired trial
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/companies/usage-limits/
# Should return 402 if trial expired

# Test company isolation
curl -H "Authorization: Bearer $USER1_TOKEN" http://localhost:8000/api/companies/detail/
# Should only return user1's company data
```

### 6. Verify Atomic Operations
```python
# Django shell test
python manage.py shell
>>> from apps.companies.models import Company
>>> company = Company.objects.first()
>>> # Test atomic increment
>>> for i in range(10):
...     company.increment_usage('transactions')
>>> company.refresh_from_db()
>>> print(company.current_month_transactions)  # Should be exactly 10
```

## Rollback Instructions (if needed)

### 1. Revert Migration
```bash
python manage.py migrate companies 0002
```

### 2. Remove Middleware
Edit `core/settings/base.py` and remove:
```python
'apps.companies.middleware.TrialExpirationMiddleware',
```

### 3. Restore Original Models
Replace consolidated models with original version.

## Monitoring After Deployment

### Check for Errors
```bash
# Monitor logs for permission errors
tail -f logs/django.log | grep -i "permission\|denied"

# Check for 402 responses (payment required)
tail -f logs/access.log | grep " 402 "
```

### Performance Monitoring
```sql
-- Check for lock contention on companies table
SELECT * FROM pg_locks WHERE relation::regclass = 'companies'::regclass;

-- Monitor slow queries
SELECT query, calls, mean_time 
FROM pg_stat_statements 
WHERE query LIKE '%companies%' 
ORDER BY mean_time DESC;
```

## Common Issues and Solutions

### Issue: Migration Fails
```bash
# Check for existing subscription data
python manage.py shell
>>> from apps.payments.models import Subscription
>>> Subscription.objects.filter(company__isnull=True).count()
```

### Issue: Middleware Blocking Valid Users
Check trial dates:
```python
>>> from apps.companies.models import Company
>>> company = Company.objects.get(owner__email='user@example.com')
>>> print(company.subscription.trial_ends_at)
>>> print(company.subscription.status)
```

### Issue: Race Conditions Still Occurring
Verify atomic operations:
```python
>>> Company.increment_usage.__wrapped__.__code__.co_flags & 0x80
128  # Should be non-zero, indicating @transaction.atomic
```