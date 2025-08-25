# 🚨 CRITICAL PRODUCTION FIX - Stripe Price IDs

## Problem
Payment system failing with error: **"No such price: price_1RkePtPFSVtvOaJKYbiX6TqQ"**

The database contains **invalid Stripe price IDs** that don't exist in the Stripe account.

## Root Cause
Database has old/incorrect price IDs:
- Starter: `price_1RkePtPFSVtvOaJK**YbiX6TqQ**` ❌ (Invalid)
- Should be: `price_1RkePtPFSVtvOaJK**YbiX6TqQ**` ✅ (Valid)

## Solution

### Option 1: Management Command (Recommended)
```bash
python manage.py update_stripe_prices_prod
```

### Option 2: Railway CLI
```bash
railway run python manage.py update_stripe_prices_prod
```

### Option 3: Manual SQL (Emergency Only)
```sql
UPDATE subscription_plans SET 
  stripe_price_id_monthly = 'price_1RkePlPFSVtvOaJKYbiX6TqQ',
  stripe_price_id_yearly = 'price_1RnPVfPFSVtvOaJKmwxNmUdz'
WHERE slug = 'starter';

UPDATE subscription_plans SET 
  stripe_price_id_monthly = 'price_1RkeQgPFSVtvOaJKgPOzW1SD',
  stripe_price_id_yearly = 'price_1RnPVRPFSVtvOaJKIWxiSHfm'
WHERE slug = 'professional';

UPDATE subscription_plans SET 
  stripe_price_id_monthly = 'price_1RkeVLPFSVtvOaJKY5efgwca',
  stripe_price_id_yearly = 'price_1RnPV8PFSVtvOaJKoiZxvjPa'
WHERE slug = 'enterprise';
```

## Expected Result
✅ Payment system will work correctly  
✅ Users can upgrade subscription plans  
✅ No more "No such price" errors  

## Verification
After running the fix:
```bash
python manage.py shell -c "
from apps.companies.models import SubscriptionPlan
for plan in SubscriptionPlan.objects.all():
    print(f'{plan.name}: {plan.stripe_price_id_monthly}')
"
```

Should show:
```
Starter: price_1RkePlPFSVtvOaJKYbiX6TqQ
Professional: price_1RkeQgPFSVtvOaJKgPOzW1SD  
Enterprise: price_1RkeVLPFSVtvOaJKY5efgwca
```

## Deploy Priority: 🔥 CRITICAL HOTFIX
This blocks all subscription upgrades in production.