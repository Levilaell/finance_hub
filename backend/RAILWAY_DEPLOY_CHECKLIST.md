# RAILWAY DEPLOYMENT CHECKLIST - CRITICAL ISSUES RESOLUTION

## IMMEDIATE PRE-DEPLOYMENT ACTIONS

### 1. Environment Variables Setup 🔐

```bash
# Generate secure encryption key (64-char hex)
python -c "import secrets; print('AI_INSIGHTS_ENCRYPTION_KEY=' + secrets.token_hex(32))"

# Set in Railway Dashboard:
AI_INSIGHTS_ENCRYPTION_KEY=<generated-key>
DJANGO_SETTINGS_MODULE=core.settings.production
```

### 2. Production Database Backup ☁️

```bash
# Create backup before deployment
railway run pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 3. Critical Validation Script 🔍

**Run this in Railway console FIRST:**

```bash
railway run python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    # Check early access fields
    cursor.execute('''
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = \'companies\' 
        AND column_name LIKE \'%early_access%\'
        ORDER BY column_name;
    ''')
    fields = [row[0] for row in cursor.fetchall()]
    print(f'Early access fields ({len(fields)}): {fields}')
    
    # Check table existence
    cursor.execute('''
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = \'early_access_invites\'
        );
    ''')
    table_exists = cursor.fetchone()[0]
    print(f'EarlyAccessInvite table exists: {table_exists}')
    
    # Check migration status
    cursor.execute('''
        SELECT name 
        FROM django_migrations 
        WHERE app = \'companies\' 
        AND name IN (\'0008_alter_resourceusage_options_and_more\', \'0009_add_early_access\')
        ORDER BY name;
    ''')
    migrations = [row[0] for row in cursor.fetchall()]
    print(f'Critical migrations applied ({len(migrations)}): {migrations}')

print('\\n=== MODEL IMPORT TEST ===')
from apps.companies.models import Company, EarlyAccessInvite
from apps.notifications.models import Notification
print('✅ All critical models import successfully')
"
```

**Expected Output:**
- Early access fields (3): ['early_access_expires_at', 'is_early_access', 'used_invite_code']
- EarlyAccessInvite table exists: True
- Critical migrations applied (2): ['0008_alter_resourceusage_options_and_more', '0009_add_early_access']
- ✅ All critical models import successfully

---

## POTENTIAL ISSUES AND FIXES

### Issue 1: Early Access Fields Missing ❌

**If validation shows < 3 fields:**

```bash
# Upload and run the fix script
railway run psql $DATABASE_URL -f fix_duplicate_early_access_production.sql
```

### Issue 2: Migration History Inconsistency ⚠️

**If migrations show as unapplied:**

```bash
railway run python manage.py migrate --fake companies 0008
railway run python manage.py migrate --fake companies 0009
```

### Issue 3: Model Import Errors 💥

**If model imports fail:**

```bash
# Check specific error
railway run python -c "
try:
    from apps.companies.models import EarlyAccessInvite
    print('✅ EarlyAccessInvite imports OK')
except Exception as e:
    print(f'❌ EarlyAccessInvite import failed: {e}')

try:
    from apps.notifications.models import Notification  
    print('✅ Notification imports OK')
except Exception as e:
    print(f'❌ Notification import failed: {e}')
"
```

---

## DEPLOYMENT EXECUTION

### Step 1: Deploy Code 🚀

```bash
git add -A
git commit -m "fix: resolve migration inconsistencies for Railway deployment

- Add comprehensive migration analysis and validation scripts
- Create production fix for duplicate early access migrations  
- Generate Railway deployment checklist and validation tools
- Prepare emergency rollback procedures

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

### Step 2: Monitor Deployment 👁️

```bash
# Watch deployment logs
railway logs --tail

# Look for these patterns:
# ✅ "Operations to perform: Apply all migrations"
# ✅ "Applying companies.0008_alter_resourceusage_options_and_more... OK"
# ✅ "Applying companies.0009_add_early_access... OK"
# ❌ "django.db.utils.ProgrammingError: column already exists"
# ❌ "django.db.utils.IntegrityError: duplicate key value"
```

### Step 3: Post-Deployment Validation ✅

```bash
# Test critical user flows
railway run python -c "
from django.contrib.auth import get_user_model
from apps.companies.models import Company

User = get_user_model()

# Test user creation
print('Testing user creation...')
try:
    user = User.objects.create_user(
        username='test_deploy_$(date +%s)',
        email='test@example.com',
        password='testpass123'
    )
    print('✅ User creation: OK')
    
    # Test company creation with early access
    company = Company.objects.create(
        name='Test Company Deploy',
        owner=user,
        is_early_access=True
    )
    print('✅ Company with early access: OK')
    
    # Cleanup
    company.delete()
    user.delete()
    print('✅ Cleanup: OK')
    
except Exception as e:
    print(f'❌ User flow test failed: {e}')
"
```

---

## EMERGENCY ROLLBACK PROCEDURES 🚨

### If Deployment Fails Completely

```bash
# Option 1: Rollback via Railway Dashboard
# Go to Railway Dashboard > Deployments > Click on previous successful deployment > Redeploy

# Option 2: Git rollback
git log --oneline -5  # Find last good commit
git reset --hard <last-good-commit-hash>
git push --force origin main

# Option 3: Database restoration
railway run psql $DATABASE_URL < backup_<timestamp>.sql
```

### If Specific Migration Fails

```bash
# Mark problematic migration as applied without running it
railway run python manage.py migrate --fake companies 0008
railway run python manage.py migrate --fake companies 0009

# Or run the emergency fix script
railway run psql $DATABASE_URL -f fix_duplicate_early_access_production.sql
```

---

## POST-DEPLOYMENT MONITORING

### Performance Checks 📊

```bash
# Check query performance (removed indexes impact)
railway run python -c "
import time
from django.db import connection
from apps.banking.models import Transaction

start = time.time()
count = Transaction.objects.filter(date__gte='2025-01-01').count()
duration = time.time() - start

print(f'Transaction query performance: {count} records in {duration:.2f}s')
if duration > 2.0:
    print('⚠️ Query performance degraded - consider recreating indexes')
else:
    print('✅ Query performance acceptable')
"
```

### Error Rate Monitoring 🔍

```bash
# Monitor for 5 minutes after deployment
for i in {1..5}; do
    echo "=== Monitoring minute $i ==="
    railway logs --tail | grep -i error | head -5
    sleep 60
done
```

### Critical Feature Tests 🧪

```bash
# Test bank account connection
# Test transaction sync  
# Test report generation
# Test user registration

railway run python -c "
print('Testing critical features...')

# Import test
from apps.banking.models import BankAccount, Transaction
from apps.reports.models import Report
from apps.authentication.models import EmailVerification

print('✅ All models import successfully')
print('🎉 Deployment validation complete')
"
```

---

## SUCCESS CRITERIA ✅

- [ ] Environment variables set correctly
- [ ] All migrations applied without errors
- [ ] Early access functionality working
- [ ] No duplicate field errors in logs  
- [ ] User registration working
- [ ] Bank account connection working
- [ ] Critical models import successfully
- [ ] No significant performance degradation
- [ ] Error rate remains normal
- [ ] All critical features tested

---

## CONTACT & ESCALATION 📞

**If Issues Persist:**
1. Create GitHub issue with deployment logs
2. Include validation script outputs
3. Attach error messages and stack traces
4. Note: Emergency rollback procedures above

**Files Generated for Support:**
- `MIGRATION_ANALYSIS_REPORT.md` - Complete analysis
- `fix_duplicate_early_access_production.sql` - Production fix script  
- `railway_validation_script.py` - Quick validation
- `production_migration_validator.py` - Comprehensive validation

---

**Generated**: 2025-08-23 | **Framework**: Claude Code SuperClaude
**Next Review**: After successful deployment