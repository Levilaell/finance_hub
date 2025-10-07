# Stripe Production Deployment - Quick Start

**Fast reference for experienced developers. See STRIPE_PRODUCTION_DEPLOYMENT.md for detailed explanations.**

---

## Pre-Deployment (Stripe Dashboard)

```bash
# 1. Create Product & Price in Stripe Dashboard (production mode)
#    Products > Create Product > Set price > Copy Price ID
#    SAVE: price_xxxxxxxxxxxxx

# 2. Configure Customer Portal
#    Settings > Billing > Customer Portal > Enable
```

---

## Environment Variables (Railway)

```bash
# Set these in Railway BEFORE deployment:
DJANGO_SECRET_KEY=<new-production-secret>
JWT_SECRET_KEY=<new-jwt-secret>
DJANGO_SETTINGS_MODULE=core.settings.production
DATABASE_URL=<railway-postgres-url>
FRONTEND_URL=https://caixahub.com.br

# Stripe Production
STRIPE_LIVE_MODE=true
STRIPE_LIVE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
STRIPE_LIVE_PUBLIC_KEY=pk_live_xxxxxxxxxxxxx
STRIPE_DEFAULT_PRICE_ID=price_xxxxxxxxxxxxx

# Stripe Test (keep for fallback)
STRIPE_TEST_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_TEST_PUBLIC_KEY=pk_test_xxxxxxxxxxxxx

# Webhook (set AFTER step 3)
DJSTRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

---

## Deployment Commands (Sequential Order)

### Step 1: Migrations
```bash
python manage.py migrate djstripe
python manage.py migrate subscriptions
python manage.py showmigrations  # Verify
```

### Step 2: Data Sync
```bash
# Sync Products, Prices, Customers, Subscriptions from Stripe
python manage.py sync_stripe

# Expected: Products, Prices synced successfully
```

### Step 3: Webhook Setup
```bash
# Option A: Sync from existing webhook in Stripe Dashboard
python manage.py register_stripe_webhook

# Option B: Create new webhook programmatically
python manage.py register_stripe_webhook \
    --url https://financehub-production.up.railway.app/stripe/webhook/ \
    --create-in-stripe

# COPY the webhook secret: whsec_xxxxxxxxxxxxx
# ADD to Railway: DJSTRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
# REDEPLOY application
```

### Step 4: Verification
```bash
# Test webhook in Stripe Dashboard > Webhooks > Send test webhook
# Expected: 200 OK response

# Test subscription config endpoint
curl https://financehub-production.up.railway.app/api/subscriptions/config/ \
  -H "Authorization: Bearer <token>"
# Expected: {"publishable_key": "pk_live_xxxxxxxxxxxxx"}
```

---

## Post-Deployment Tests

### 1. End-to-End Checkout
- Create test user
- Complete checkout with real card
- Verify subscription in database
- Check trial tracking

### 2. Subscription Status
```bash
curl https://financehub-production.up.railway.app/api/subscriptions/status/ \
  -H "Authorization: Bearer <token>"
# Expected: status, trial_end, amount, payment_method
```

### 3. Customer Portal
```bash
curl -X POST https://financehub-production.up.railway.app/api/subscriptions/portal/ \
  -H "Authorization: Bearer <token>" \
  -d '{"return_url": "https://caixahub.com.br/settings"}'
# Expected: {"url": "https://billing.stripe.com/..."}
```

### 4. Access Control
```bash
# No subscription → 402 error
curl https://financehub-production.up.railway.app/api/banking/accounts/ \
  -H "Authorization: Bearer <no-sub-token>"
# Expected: {"error": "Subscription required", "code": "CHECKOUT_REQUIRED"}

# Active subscription → 200 OK
curl https://financehub-production.up.railway.app/api/banking/accounts/ \
  -H "Authorization: Bearer <active-sub-token>"
# Expected: Data returned
```

---

## Monitoring Commands

```bash
# Check trial conversions
python manage.py check_trial_status

# Fix orphaned customers
python manage.py fix_customer_links

# View recent webhook events
python manage.py shell
>>> from djstripe.models import Event
>>> Event.objects.all().order_by('-created')[:10]
```

---

## Common Issues - Quick Fixes

### Webhook 401 Error
```bash
# Re-sync webhook secret
python manage.py register_stripe_webhook
# Add DJSTRIPE_WEBHOOK_SECRET to Railway
# Redeploy
```

### Trial Not Tracked
```bash
# Manual fix
python manage.py shell
>>> from apps.subscriptions.models import TrialUsageTracking
>>> from apps.authentication.models import User
>>> from django.utils import timezone
>>> user = User.objects.get(email='user@example.com')
>>> trial, _ = TrialUsageTracking.objects.get_or_create(user=user)
>>> trial.has_used_trial = True
>>> trial.first_trial_at = timezone.now()
>>> trial.save()
```

### Customer Not Linked
```bash
python manage.py fix_customer_links
```

### Stale Subscription Data
```bash
python manage.py sync_stripe
```

---

## Rollback

```bash
# In Railway environment variables:
STRIPE_LIVE_MODE=false
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_PUBLIC_KEY=pk_test_xxxxxxxxxxxxx

# Redeploy
```

---

## Critical Paths

- **Services:** `backend/apps/subscriptions/services.py`
- **Webhooks:** `backend/apps/subscriptions/signals.py`
- **Middleware:** `backend/apps/subscriptions/middleware.py`
- **Settings:** `backend/core/settings/production.py`

---

## Support

- **Webhook logs:** Stripe Dashboard > Webhooks > Recent deliveries
- **Application logs:** Railway deployment logs
- **Event history:** Stripe Dashboard > Developers > Events
- **Full guide:** STRIPE_PRODUCTION_DEPLOYMENT.md
