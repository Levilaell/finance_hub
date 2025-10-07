# Stripe Production Deployment Guide

**Complete checklist for migrating dj-stripe from test mode to production mode**

---

## Overview

This guide covers the complete deployment process for transitioning your Stripe integration from test mode to production. The system uses:
- **dj-stripe** for Stripe data synchronization and webhook handling
- **Custom subscription services** for trial tracking and subscription management
- **Django signals** for webhook event processing
- **Middleware** for subscription-based access control

---

## PHASE 1: Pre-Deployment Preparation

### 1.1 Stripe Dashboard Configuration

**CRITICAL: Complete these steps in Stripe Dashboard BEFORE deployment**

#### A. Create Production Product and Price

1. Log into Stripe Dashboard (production mode)
2. Navigate to Products > Create Product
3. Configure your subscription product:
   - Name: "CaixaHub Premium" (or your product name)
   - Description: Add detailed description
   - Pricing model: Recurring
   - Price: Set your BRL amount
   - Billing period: Monthly
   - Currency: BRL
4. Save and copy the **Price ID** (starts with `price_`)
5. Note: Keep this Price ID - you'll need it for `STRIPE_DEFAULT_PRICE_ID`

#### B. Configure Customer Portal

1. Navigate to Settings > Billing > Customer Portal
2. Enable the customer portal
3. Configure allowed features:
   - ✓ Update payment method
   - ✓ View invoice history
   - ✓ Cancel subscription (recommended: at period end only)
4. Set business information (company name, support email, etc.)
5. Save changes

### 1.2 Environment Variables Preparation

**Create a secure list of production environment variables:**

```bash
# Django Core
DJANGO_SECRET_KEY=<generate-new-production-secret>
JWT_SECRET_KEY=<generate-new-jwt-secret>
DJANGO_SETTINGS_MODULE=core.settings.production

# Database (provided by Railway)
DATABASE_URL=<railway-postgres-url>

# Frontend
FRONTEND_URL=https://caixahub.com.br

# Stripe PRODUCTION Keys
STRIPE_LIVE_MODE=true
STRIPE_LIVE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
STRIPE_LIVE_PUBLIC_KEY=pk_live_xxxxxxxxxxxxx
STRIPE_DEFAULT_PRICE_ID=price_xxxxxxxxxxxxx

# Stripe TEST Keys (keep for fallback/testing)
STRIPE_TEST_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_TEST_PUBLIC_KEY=pk_test_xxxxxxxxxxxxx

# Webhook Secret (will be set in Phase 2)
DJSTRIPE_WEBHOOK_SECRET=<to-be-generated>

# Open Banking (if applicable)
PLUGGY_CLIENT_ID=<your-production-pluggy-id>
PLUGGY_CLIENT_SECRET=<your-production-pluggy-secret>
PLUGGY_USE_SANDBOX=false
```

**Security Notes:**
- Generate `DJANGO_SECRET_KEY`: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
- Generate `JWT_SECRET_KEY`: Use the same command but MUST be different from `DJANGO_SECRET_KEY`
- NEVER commit secrets to version control
- Use Railway's environment variable management

---

## PHASE 2: Initial Deployment

### 2.1 Database Migrations

**Run migrations to create dj-stripe tables:**

```bash
# SSH into your Railway instance or run locally with production DATABASE_URL
python manage.py migrate djstripe

# This creates the following tables:
# - djstripe_customer
# - djstripe_subscription
# - djstripe_price
# - djstripe_product
# - djstripe_paymentmethod
# - djstripe_invoice
# - djstripe_webhookendpoint
# - djstripe_event
# - And many more...

# Also run your app's migrations:
python manage.py migrate subscriptions
# This creates:
# - trial_usage_tracking (custom model)
```

**Verify migrations:**
```bash
python manage.py showmigrations djstripe
python manage.py showmigrations subscriptions
```

### 2.2 Initial Data Synchronization

**CRITICAL: Sync existing Stripe data to your database**

This step is essential if you have existing customers/subscriptions in Stripe, or if you need to populate Products/Prices.

```bash
# Option 1: Full sync (recommended for fresh deployment)
python manage.py sync_stripe

# Expected output:
# 📦 Sincronizando Products...
#   ✓ CaixaHub Premium
# 💰 Sincronizando Prices...
#   ✓ R$ 49.90 - CaixaHub Premium
# 👥 Sincronizando Customers...
#   ✓ user@example.com
# 📋 Sincronizando Subscriptions...
#   ✓ sub_xxxxx - active
# ✅ Sincronização completa!

# Option 2: Clean sync (if you have test data pollution)
python manage.py sync_stripe --clean
# WARNING: This deletes old Plan objects before syncing
```

**What gets synced:**
- ✓ Products from Stripe Dashboard
- ✓ Prices (linked to products)
- ✓ Customers (if any exist)
- ✓ Subscriptions (if any exist)
- ✗ Webhook endpoints (handled separately in next step)

**Important Notes:**
- This command uses the Stripe API key based on `STRIPE_LIVE_MODE` setting
- If `STRIPE_LIVE_MODE=true`, it syncs from production Stripe
- If `STRIPE_LIVE_MODE=false`, it syncs from test Stripe
- Run this BEFORE setting up webhooks to ensure data consistency

### 2.3 Webhook Registration

**CRITICAL: Webhooks are required for subscription lifecycle events**

#### Step 1: Determine Your Webhook URL

Your webhook URL format (provided by dj-stripe):
```
https://your-domain.railway.app/stripe/webhook/
```

**Important:** dj-stripe automatically appends a UUID to webhook URLs for security. The actual webhook URL in Stripe Dashboard will look like:
```
https://your-domain.railway.app/stripe/webhook/{uuid}/
```

#### Step 2: Create Webhook in Stripe Dashboard

**Method A: Manual Creation (Recommended)**

1. Log into Stripe Dashboard (production mode)
2. Navigate to Developers > Webhooks
3. Click "Add endpoint"
4. Enter endpoint URL: `https://financehub-production.up.railway.app/stripe/webhook/`
5. Select events to listen for:
   - ✓ `customer.subscription.created`
   - ✓ `customer.subscription.updated`
   - ✓ `customer.subscription.deleted`
   - ✓ `customer.subscription.trial_will_end`
   - ✓ `invoice.payment_succeeded`
   - ✓ `invoice.payment_failed`
6. Click "Add endpoint"
7. Copy the **Signing secret** (starts with `whsec_`)

**Method B: Programmatic Creation**

```bash
# Create webhook endpoint via command
python manage.py register_stripe_webhook \
    --url https://financehub-production.up.railway.app/stripe/webhook/ \
    --create-in-stripe

# Expected output:
# 📡 Creating webhook endpoint in Stripe...
# ✅ Created in Stripe: we_xxxxxxxxxxxxx
#    Secret: whsec_xxxxxxxxxxxxx
# 📥 Syncing to local database...
# ✅ Synced to database: we_xxxxxxxxxxxxx
# 🔑 Webhook Secret for Django settings:
#    DJSTRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

#### Step 3: Sync Webhook to Database

```bash
# If you created webhook manually in Stripe Dashboard, sync it:
python manage.py register_stripe_webhook

# Expected output:
# 📥 Syncing webhook endpoints from Stripe...
# Found 1 endpoint(s) in Stripe:
#   - we_xxxxx: https://your-domain/stripe/webhook/{uuid}/
#     ✅ Synced to database: we_xxxxx
#
# 📋 Configuration:
# 1️⃣  Add to Railway environment variables:
#    DJSTRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
# 2️⃣  Your webhook URL for Stripe Dashboard:
#    https://your-domain/stripe/webhook/{uuid}/
# 3️⃣  Redeploy your Railway app to apply the secret
```

#### Step 4: Update Environment Variables

Add the webhook secret to Railway:
```bash
DJSTRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

Then redeploy your application.

### 2.4 Verify Webhook Configuration

**Test webhook delivery:**

1. In Stripe Dashboard > Webhooks, select your endpoint
2. Click "Send test webhook"
3. Select event type: `customer.subscription.created`
4. Click "Send test webhook"
5. Check response status: Should be **200 OK**
6. Check Railway logs for confirmation:
   ```
   INFO Subscription created via webhook: sub_xxxxx
   ```

**Common webhook issues:**
- **401 Unauthorized**: `DJSTRIPE_WEBHOOK_SECRET` is missing or incorrect
- **404 Not Found**: Webhook URL is incorrect (check UUID format)
- **500 Internal Server Error**: Application error (check logs for stack trace)

---

## PHASE 3: Post-Deployment Verification

### 3.1 Frontend Integration Verification

**Test that frontend receives correct Stripe publishable key:**

```bash
# API request (should return production key)
curl https://financehub-production.up.railway.app/api/subscriptions/config/ \
  -H "Authorization: Bearer <valid-jwt-token>"

# Expected response:
{
  "publishable_key": "pk_live_xxxxxxxxxxxxx"
}

# If STRIPE_LIVE_MODE=false, returns:
{
  "publishable_key": "pk_test_xxxxxxxxxxxxx"
}
```

**Code reference:** `/mnt/c/Users/Levi Lael/Desktop/finance_hub/backend/apps/subscriptions/views.py:189-191`

### 3.2 Checkout Flow End-to-End Test

**Perform a real checkout test:**

1. Create a test user account
2. Navigate to checkout page
3. Complete Stripe Checkout with real payment method
4. Verify trial is applied (if first-time user)
5. Check database for created records:

```bash
# Check Customer creation
python manage.py shell
>>> from djstripe.models import Customer
>>> customer = Customer.objects.last()
>>> customer.subscriber  # Should link to User
>>> customer.email

# Check Subscription creation
>>> from djstripe.models import Subscription
>>> sub = Subscription.objects.last()
>>> sub.status  # Should be 'trialing' or 'active'
>>> sub.plan.amount  # Should match your price

# Check trial tracking
>>> from apps.subscriptions.models import TrialUsageTracking
>>> trial = TrialUsageTracking.objects.last()
>>> trial.has_used_trial  # Should be True
>>> trial.first_trial_at  # Should have timestamp
```

### 3.3 Subscription Status Verification

**Test subscription status endpoint:**

```bash
curl https://financehub-production.up.railway.app/api/subscriptions/status/ \
  -H "Authorization: Bearer <user-jwt-token>"

# Expected response for active subscription:
{
  "status": "trialing",
  "trial_end": "2025-10-13T12:00:00Z",
  "current_period_end": "2025-10-13T12:00:00Z",
  "cancel_at_period_end": false,
  "canceled_at": null,
  "days_until_renewal": 7,
  "amount": 49.90,
  "currency": "BRL",
  "payment_method": {
    "last4": "4242",
    "brand": "visa"
  },
  "has_used_trial": true,
  "first_trial_at": "2025-10-06T12:00:00Z"
}
```

### 3.4 Customer Portal Verification

**Test Stripe Customer Portal access:**

```bash
curl -X POST https://financehub-production.up.railway.app/api/subscriptions/portal/ \
  -H "Authorization: Bearer <user-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"return_url": "https://caixahub.com.br/settings"}'

# Expected response:
{
  "url": "https://billing.stripe.com/p/session/xxxxxxxxxxxxx"
}
```

### 3.5 Middleware Access Control Test

**Verify subscription-based access control:**

```bash
# Test 1: User WITHOUT subscription (should block)
curl https://financehub-production.up.railway.app/api/banking/accounts/ \
  -H "Authorization: Bearer <no-subscription-user-token>"

# Expected response (402 Payment Required):
{
  "error": "Subscription required. Please complete checkout.",
  "code": "CHECKOUT_REQUIRED",
  "redirect": "/checkout"
}

# Test 2: User WITH active subscription (should allow)
curl https://financehub-production.up.railway.app/api/banking/accounts/ \
  -H "Authorization: Bearer <subscribed-user-token>"

# Expected response: 200 OK with data

# Test 3: User with expired subscription (should block)
curl https://financehub-production.up.railway.app/api/banking/accounts/ \
  -H "Authorization: Bearer <expired-subscription-user-token>"

# Expected response (402 Payment Required):
{
  "error": "Active subscription required",
  "code": "SUBSCRIPTION_REQUIRED",
  "redirect": "/subscription/expired"
}
```

**Code reference:** `/mnt/c/Users/Levi Lael/Desktop/finance_hub/backend/apps/subscriptions/middleware.py`

---

## PHASE 4: Monitoring and Maintenance

### 4.1 Webhook Event Monitoring

**Monitor webhook events in production:**

```bash
# Check recent webhook events
python manage.py shell
>>> from djstripe.models import Event
>>> Event.objects.all().order_by('-created')[:10]

# Check for failed webhooks
>>> Event.objects.filter(webhook_message__isnull=False).order_by('-created')
```

**Stripe Dashboard monitoring:**
1. Navigate to Developers > Webhooks
2. Select your endpoint
3. View "Recent deliveries" section
4. Check for failed deliveries (non-200 status codes)

### 4.2 Trial Usage Tracking

**Monitor trial conversions:**

```bash
python manage.py check_trial_status

# Expected output:
# Trial Usage Report:
# - Total users with trials: 45
# - Active trials: 12
# - Converted trials: 28
# - Expired trials: 5
```

### 4.3 Customer-User Link Verification

**Verify all Stripe Customers are linked to Users:**

```bash
python manage.py fix_customer_links

# This command:
# - Finds Customers without linked Users
# - Attempts to link via email or metadata
# - Reports any orphaned customers
```

### 4.4 Log Monitoring

**Key log patterns to monitor:**

```bash
# Successful webhook processing
INFO Subscription created via webhook: sub_xxxxx
INFO Trial tracked via webhook for user 123
INFO Payment succeeded: R$ 49.90 for subscription sub_xxxxx

# Warning signs
WARNING Subscription past due: sub_xxxxx
WARNING Payment failed (attempt 3): R$ 49.90 for subscription sub_xxxxx
WARNING Trial ending soon for subscription sub_xxxxx

# Errors requiring attention
ERROR Error tracking trial in webhook: <error>
ERROR Error processing webhook event evt_xxxxx
ERROR Deadlock detected while processing webhook event evt_xxxxx
```

**Code reference:** `/mnt/c/Users/Levi Lael/Desktop/finance_hub/backend/apps/subscriptions/signals.py`

---

## PHASE 5: Common Issues and Solutions

### 5.1 "Customer does not exist" Error

**Symptom:** Creating subscription fails with "Customer not found in Stripe"

**Diagnosis:**
```bash
# Check if customer exists in database but not in Stripe
python manage.py shell
>>> from djstripe.models import Customer
>>> customer = Customer.objects.get(id='cus_xxxxx')
>>> customer.api_retrieve()  # Raises DoesNotExist if not in Stripe
```

**Solution:**
```bash
# Re-sync customers from Stripe
python manage.py sync_stripe

# Or create customer manually
>>> from apps.subscriptions.services import get_or_create_customer
>>> from apps.authentication.models import User
>>> user = User.objects.get(email='user@example.com')
>>> customer = get_or_create_customer(user)
```

### 5.2 "Webhook signature verification failed"

**Symptom:** Webhooks fail with 401 error

**Diagnosis:**
- `DJSTRIPE_WEBHOOK_SECRET` is missing
- `DJSTRIPE_WEBHOOK_SECRET` doesn't match Stripe Dashboard
- Webhook endpoint UUID mismatch

**Solution:**
1. Verify environment variable:
   ```bash
   echo $DJSTRIPE_WEBHOOK_SECRET  # Should start with 'whsec_'
   ```
2. Re-sync webhook secret from Stripe:
   ```bash
   python manage.py register_stripe_webhook
   ```
3. Update Railway environment variables
4. Redeploy application

### 5.3 "Trial not being tracked"

**Symptom:** `has_used_trial` remains False after trial subscription created

**Diagnosis:**
- Webhook signal not firing
- Race condition in trial tracking
- Subscription created without trial_end

**Solution:**
1. Check webhook events:
   ```bash
   # Look for customer.subscription.created event
   python manage.py shell
   >>> from djstripe.models import Event
   >>> Event.objects.filter(type='customer.subscription.created').latest('created')
   ```
2. Manually mark trial as used:
   ```bash
   >>> from apps.subscriptions.models import TrialUsageTracking
   >>> from apps.authentication.models import User
   >>> user = User.objects.get(email='user@example.com')
   >>> trial, _ = TrialUsageTracking.objects.get_or_create(user=user)
   >>> trial.has_used_trial = True
   >>> trial.first_trial_at = timezone.now()
   >>> trial.save()
   ```

### 5.4 "Subscription exists but user has no access"

**Symptom:** User has subscription in Stripe but `has_active_subscription` returns False

**Diagnosis:**
- Customer not linked to User (`customer.subscriber` is None)
- Subscription status not synced
- Subscription in database is stale

**Solution:**
1. Fix customer link:
   ```bash
   python manage.py fix_customer_links
   ```
2. Re-sync subscription:
   ```bash
   python manage.py shell
   >>> from djstripe.models import Subscription
   >>> import stripe
   >>> stripe_sub = stripe.Subscription.retrieve('sub_xxxxx')
   >>> dj_sub = Subscription.sync_from_stripe_data(stripe_sub)
   ```

### 5.5 "Database deadlock on webhook processing"

**Symptom:** Logs show deadlock errors during webhook processing

**Diagnosis:**
- Concurrent webhooks updating same records
- Transaction conflicts in signal handlers

**Solution:**
- System already has retry logic with exponential backoff
- Stripe will automatically retry failed webhooks
- Monitor logs for persistent deadlocks:
  ```bash
  WARNING Deadlock detected while processing webhook event evt_xxxxx. Stripe will retry automatically.
  ```
- If persistent, investigate locking in signals:
  `/mnt/c/Users/Levi Lael/Desktop/finance_hub/backend/apps/subscriptions/signals.py:56`

---

## PHASE 6: Production Checklist

### Pre-Deployment Checklist

- [ ] Product and Price created in Stripe Dashboard (production mode)
- [ ] Customer Portal configured in Stripe Dashboard
- [ ] All environment variables documented and ready
- [ ] `STRIPE_LIVE_MODE=true` set in environment variables
- [ ] Production Stripe keys obtained and secured
- [ ] `STRIPE_DEFAULT_PRICE_ID` set to production Price ID
- [ ] Database backup created (if migrating existing data)

### Deployment Checklist

- [ ] All environment variables set in Railway
- [ ] Application deployed with `DJANGO_SETTINGS_MODULE=core.settings.production`
- [ ] Database migrations run: `python manage.py migrate`
- [ ] dj-stripe migrations verified: `python manage.py showmigrations djstripe`
- [ ] Initial data sync completed: `python manage.py sync_stripe`
- [ ] Webhook endpoint created in Stripe Dashboard
- [ ] Webhook endpoint synced to database: `python manage.py register_stripe_webhook`
- [ ] `DJSTRIPE_WEBHOOK_SECRET` set in Railway environment variables
- [ ] Application redeployed after webhook secret added

### Post-Deployment Checklist

- [ ] Stripe config endpoint returns production key: `GET /api/subscriptions/config/`
- [ ] Webhook test successful (200 OK response in Stripe Dashboard)
- [ ] End-to-end checkout test completed successfully
- [ ] Subscription status endpoint verified: `GET /api/subscriptions/status/`
- [ ] Customer Portal access verified: `POST /api/subscriptions/portal/`
- [ ] Middleware access control tested (with and without subscription)
- [ ] Trial tracking verified (first-time user receives trial)
- [ ] Webhook events monitoring in Stripe Dashboard
- [ ] Application logs monitored for errors
- [ ] Customer-User links verified: `python manage.py fix_customer_links`

### Monitoring Checklist

- [ ] Webhook delivery monitoring in Stripe Dashboard
- [ ] Application logs reviewed daily for errors
- [ ] Failed payment notifications monitored
- [ ] Trial conversion rates tracked
- [ ] Subscription churn monitored
- [ ] Database performance monitored (especially webhook processing)

---

## PHASE 7: Rollback Plan

### If deployment fails:

1. **Immediate rollback:**
   ```bash
   # Set back to test mode
   STRIPE_LIVE_MODE=false
   STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
   STRIPE_PUBLIC_KEY=pk_test_xxxxxxxxxxxxx
   ```

2. **Preserve production data:**
   - Webhook endpoints remain in Stripe Dashboard
   - Synced data remains in database
   - No data loss if rollback is immediate

3. **Re-sync from test mode:**
   ```bash
   python manage.py sync_stripe --clean
   ```

4. **Investigate issues:**
   - Review Railway logs
   - Check Stripe Dashboard webhook logs
   - Test locally with production DATABASE_URL

---

## PHASE 8: Command Reference

### Django Management Commands

```bash
# Database operations
python manage.py migrate                    # Run all pending migrations
python manage.py showmigrations djstripe    # Show dj-stripe migration status

# Stripe synchronization
python manage.py sync_stripe                # Sync all Stripe data
python manage.py sync_stripe --clean        # Clean and sync

# Webhook management
python manage.py register_stripe_webhook    # Sync webhooks from Stripe
python manage.py register_stripe_webhook --url https://domain.com/stripe/webhook/ --create-in-stripe  # Create new webhook

# Subscription management
python manage.py check_trial_status         # Report on trial usage
python manage.py fix_customer_links         # Fix Customer-User links

# Database inspection
python manage.py shell                      # Django shell for manual queries
python manage.py dbshell                    # Direct database access
```

### dj-stripe Models Reference

```python
# Key models synced from Stripe
from djstripe.models import (
    Customer,           # Stripe customers (linked to User via subscriber)
    Subscription,       # Subscription records
    Product,            # Products from Stripe Dashboard
    Price,              # Prices (replaces deprecated Plan)
    PaymentMethod,      # Payment methods
    Invoice,            # Invoices
    Event,              # Webhook events
    WebhookEndpoint,    # Webhook endpoint configurations
)

# Custom models
from apps.subscriptions.models import (
    TrialUsageTracking,  # Tracks if user has used trial
)
```

---

## Critical Security Notes

1. **Never commit secrets to Git:**
   - Use Railway environment variables
   - Add `.env` to `.gitignore`
   - Rotate secrets if accidentally committed

2. **Webhook secret validation:**
   - Always verify webhook signatures
   - Current setting: `DJSTRIPE_WEBHOOK_VALIDATION = 'verify_signature'`
   - Do NOT disable webhook validation in production

3. **Environment separation:**
   - Keep test and production API keys strictly separated
   - Use `STRIPE_LIVE_MODE` flag to control which keys are active
   - Never use test mode in production

4. **Database access:**
   - Restrict database access to application only
   - Use Railway's private networking
   - Regularly backup production database

5. **Logging:**
   - Avoid logging sensitive data (card numbers, full keys)
   - Current implementation sanitizes logs
   - Review logs regularly for security issues

---

## Support and Resources

**Documentation:**
- dj-stripe: https://dj-stripe.readthedocs.io/
- Stripe API: https://stripe.com/docs/api
- Stripe Webhooks: https://stripe.com/docs/webhooks

**Key Files:**
- Services: `/mnt/c/Users/Levi Lael/Desktop/finance_hub/backend/apps/subscriptions/services.py`
- Views: `/mnt/c/Users/Levi Lael/Desktop/finance_hub/backend/apps/subscriptions/views.py`
- Signals: `/mnt/c/Users/Levi Lael/Desktop/finance_hub/backend/apps/subscriptions/signals.py`
- Middleware: `/mnt/c/Users/Levi Lael/Desktop/finance_hub/backend/apps/subscriptions/middleware.py`
- Settings: `/mnt/c/Users/Levi Lael/Desktop/finance_hub/backend/core/settings/production.py`

**Contact:**
- For deployment issues, check Railway logs first
- For Stripe issues, check Stripe Dashboard > Developers > Logs
- For webhook issues, check Stripe Dashboard > Webhooks > Recent deliveries

---

## Conclusion

This guide provides a complete, systematic approach to deploying your Stripe subscription system to production. Follow each phase in order, verify each step, and use the troubleshooting section for any issues.

**Key takeaway:** Production deployment is not just changing environment variables. It requires:
1. Database migrations for dj-stripe tables
2. Data synchronization from Stripe
3. Webhook registration and configuration
4. Comprehensive testing and verification
5. Ongoing monitoring and maintenance

Good luck with your production deployment!
