# Stripe Production Troubleshooting Guide

**Diagnostic procedures and solutions for common Stripe integration issues**

---

## Diagnostic Flow Chart

```
Issue Reported
    ↓
1. Check Stripe Dashboard → Webhook delivery status
    ↓
2. Check Railway Logs → Application errors
    ↓
3. Check Database → Data synchronization
    ↓
4. Test API Endpoints → Integration verification
    ↓
5. Apply Fix → Re-test
```

---

## Issue Category Index

1. [Webhook Issues](#webhook-issues)
2. [Subscription Creation Failures](#subscription-creation-failures)
3. [Trial Tracking Issues](#trial-tracking-issues)
4. [Access Control Problems](#access-control-problems)
5. [Payment Processing Issues](#payment-processing-issues)
6. [Data Synchronization Issues](#data-synchronization-issues)
7. [Customer Portal Issues](#customer-portal-issues)

---

## Webhook Issues

### Issue 1: Webhooks returning 401 Unauthorized

**Symptoms:**
- Stripe Dashboard shows 401 response
- Events not processing in application
- Logs: "Webhook signature verification failed"

**Diagnosis:**
```bash
# Check webhook secret is set
echo $DJSTRIPE_WEBHOOK_SECRET

# Check webhook endpoint in database
python manage.py shell
>>> from djstripe.models import WebhookEndpoint
>>> endpoints = WebhookEndpoint.objects.all()
>>> for ep in endpoints:
...     print(f"ID: {ep.id}, Secret: {ep.secret[:20]}..., URL: {ep.url}")
```

**Root Causes:**
1. `DJSTRIPE_WEBHOOK_SECRET` not set in environment
2. Webhook secret doesn't match Stripe Dashboard
3. Webhook endpoint not synced to database

**Solutions:**
```bash
# Solution 1: Re-sync webhook from Stripe
python manage.py register_stripe_webhook

# Solution 2: Manually set webhook secret
# 1. Get secret from Stripe Dashboard > Webhooks > Endpoint > Signing secret
# 2. Set in Railway: DJSTRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
# 3. Redeploy application

# Solution 3: Create new webhook
python manage.py register_stripe_webhook \
    --url https://financehub-production.up.railway.app/stripe/webhook/ \
    --create-in-stripe
```

**Verification:**
```bash
# Test webhook from Stripe Dashboard
# Developers > Webhooks > Select endpoint > Send test webhook
# Expected: 200 OK response
```

---

### Issue 2: Webhooks returning 404 Not Found

**Symptoms:**
- Stripe Dashboard shows 404 response
- URL appears correct but not found
- Logs: No webhook processing logs

**Diagnosis:**
```bash
# Check URL pattern in core/urls.py
grep -A 5 "djstripe.urls" backend/core/urls.py

# Expected:
# path('stripe/', include('djstripe.urls', namespace='djstripe')),

# Check webhook URL format
# Correct: https://domain.com/stripe/webhook/{uuid}/
# Incorrect: https://domain.com/api/stripe/webhook/
```

**Root Causes:**
1. Incorrect webhook URL in Stripe Dashboard
2. URL routing not configured
3. Middleware blocking webhook endpoint

**Solutions:**
```bash
# Solution 1: Get correct webhook URL
python manage.py shell
>>> from djstripe.models import WebhookEndpoint
>>> ep = WebhookEndpoint.objects.first()
>>> print(f"Correct URL: {ep.url}")

# Solution 2: Update URL in Stripe Dashboard
# Copy URL from above
# Stripe Dashboard > Webhooks > Edit endpoint > Update URL

# Solution 3: Verify middleware exemption
# Check backend/apps/subscriptions/middleware.py
# Ensure '/stripe/' is in EXEMPT_PATHS (it should be via djstripe URLs)
```

**Verification:**
```bash
# Test URL directly
curl https://financehub-production.up.railway.app/stripe/webhook/
# Expected: 405 Method Not Allowed (means URL is found, POST required)
```

---

### Issue 3: Webhooks returning 500 Internal Server Error

**Symptoms:**
- Stripe Dashboard shows 500 response
- Application errors in logs
- Events partially processed

**Diagnosis:**
```bash
# Check Railway logs for stack trace
# Look for patterns:
# - Database errors (connection, deadlock)
# - Missing objects (Customer.DoesNotExist)
# - Signal handler errors

# Check recent events
python manage.py shell
>>> from djstripe.models import Event
>>> failed_events = Event.objects.filter(
...     webhook_message__isnull=False
... ).order_by('-created')[:10]
>>> for e in failed_events:
...     print(f"{e.type}: {e.webhook_message}")
```

**Root Causes:**
1. Database deadlocks (concurrent webhooks)
2. Missing Customer or Subscription objects
3. Signal handler exceptions
4. Database connection issues

**Solutions:**
```bash
# Solution 1: Database deadlock (auto-handled by retry logic)
# No action needed - Stripe will retry automatically
# Monitor logs for persistent deadlocks:
grep "deadlock" /var/log/railway.log

# Solution 2: Missing objects - re-sync
python manage.py sync_stripe

# Solution 3: Check database connection
python manage.py dbshell
# If connection fails, check DATABASE_URL environment variable

# Solution 4: Review signal handlers
# Check backend/apps/subscriptions/signals.py for errors
# Add try-except blocks around problematic code
```

**Verification:**
```bash
# Retry failed events manually (if needed)
python manage.py shell
>>> import stripe
>>> from django.conf import settings
>>> stripe.api_key = settings.STRIPE_SECRET_KEY
>>> event = stripe.Event.retrieve('evt_xxxxxxxxxxxxx')
>>> from djstripe.models import Event
>>> Event.process_event(event)
```

---

## Subscription Creation Failures

### Issue 4: "Customer does not exist" error

**Symptoms:**
- Checkout fails with "Customer not found"
- Customer exists in database but not in Stripe
- Error: `stripe.error.InvalidRequestError: No such customer`

**Diagnosis:**
```bash
python manage.py shell
>>> from djstripe.models import Customer
>>> from apps.authentication.models import User
>>> user = User.objects.get(email='user@example.com')
>>> customer = Customer.objects.filter(subscriber=user).first()
>>> print(f"DB Customer: {customer.id if customer else 'None'}")

# Try to retrieve from Stripe
>>> if customer:
...     try:
...         stripe_customer = customer.api_retrieve()
...         print(f"Stripe Customer: {stripe_customer.id}")
...     except Exception as e:
...         print(f"Error: {e}")
```

**Root Causes:**
1. Customer created in database but not in Stripe
2. Customer deleted in Stripe but still in database
3. Test/production mode mismatch

**Solutions:**
```bash
# Solution 1: Re-create customer
python manage.py shell
>>> from apps.subscriptions.services import get_or_create_customer
>>> from apps.authentication.models import User
>>> user = User.objects.get(email='user@example.com')
>>>
>>> # Delete stale customer
>>> from djstripe.models import Customer
>>> Customer.objects.filter(subscriber=user).delete()
>>>
>>> # Create fresh customer
>>> customer = get_or_create_customer(user)
>>> print(f"New Customer: {customer.id}")

# Solution 2: Sync all customers from Stripe
python manage.py sync_stripe

# Solution 3: Verify Stripe mode
echo $STRIPE_LIVE_MODE
# Should be 'true' for production
```

**Verification:**
```bash
# Test customer creation
python manage.py shell
>>> from apps.authentication.models import User
>>> from apps.subscriptions.services import get_or_create_customer
>>> user = User.objects.get(email='user@example.com')
>>> customer = get_or_create_customer(user)
>>> print(f"Customer created: {customer.id}")
>>> print(f"Linked to user: {customer.subscriber.email}")
```

---

### Issue 5: "Price does not exist" error

**Symptoms:**
- Checkout fails with "Invalid price"
- Error: `stripe.error.InvalidRequestError: No such price`
- `STRIPE_DEFAULT_PRICE_ID` set but not working

**Diagnosis:**
```bash
# Check STRIPE_DEFAULT_PRICE_ID
echo $STRIPE_DEFAULT_PRICE_ID

# Verify price exists in Stripe
python manage.py shell
>>> import stripe
>>> from django.conf import settings
>>> stripe.api_key = settings.STRIPE_SECRET_KEY
>>> price_id = settings.STRIPE_DEFAULT_PRICE_ID
>>> print(f"Checking price: {price_id}")
>>> try:
...     price = stripe.Price.retrieve(price_id)
...     print(f"Price found: {price.unit_amount/100} {price.currency}")
... except Exception as e:
...     print(f"Error: {e}")
```

**Root Causes:**
1. `STRIPE_DEFAULT_PRICE_ID` not set
2. Price ID from test mode used in production (or vice versa)
3. Price deleted in Stripe Dashboard
4. Typo in price ID

**Solutions:**
```bash
# Solution 1: Get correct production price ID
# Stripe Dashboard > Products > Select product > Copy Price ID

# Solution 2: Update environment variable
# Railway > Variables > STRIPE_DEFAULT_PRICE_ID=price_xxxxxxxxxxxxx
# Redeploy

# Solution 3: Verify price mode matches STRIPE_LIVE_MODE
# Test prices start with: price_test_xxxxxxxxxxxxx
# Live prices start with: price_xxxxxxxxxxxxx

# Solution 4: Sync prices from Stripe
python manage.py sync_stripe
```

**Verification:**
```bash
# Test checkout endpoint
curl -X POST https://financehub-production.up.railway.app/api/subscriptions/checkout/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
# Expected: {"checkout_url": "https://checkout.stripe.com/..."}
```

---

## Trial Tracking Issues

### Issue 6: Trial not being marked as used

**Symptoms:**
- User completes trial subscription
- `has_used_trial` remains False
- User can initiate multiple trials

**Diagnosis:**
```bash
python manage.py shell
>>> from apps.subscriptions.models import TrialUsageTracking
>>> from apps.authentication.models import User
>>> user = User.objects.get(email='user@example.com')
>>> tracking = TrialUsageTracking.objects.filter(user=user).first()
>>> print(f"Has used trial: {tracking.has_used_trial if tracking else 'No record'}")
>>> print(f"First trial: {tracking.first_trial_at if tracking else 'None'}")

# Check if subscription has trial_end
>>> from djstripe.models import Subscription
>>> sub = Subscription.objects.filter(customer__subscriber=user).first()
>>> print(f"Trial end: {sub.trial_end if sub else 'No subscription'}")

# Check webhook events
>>> from djstripe.models import Event
>>> events = Event.objects.filter(
...     type='customer.subscription.created',
...     customer__subscriber=user
... ).order_by('-created')
>>> print(f"Webhook events: {events.count()}")
```

**Root Causes:**
1. Webhook `customer.subscription.created` not firing
2. Subscription created without trial (trial_end is None)
3. Signal handler error during trial tracking
4. Race condition between checkout and webhook

**Solutions:**
```bash
# Solution 1: Manually mark trial as used
python manage.py shell
>>> from apps.subscriptions.models import TrialUsageTracking
>>> from apps.authentication.models import User
>>> from django.utils import timezone
>>> user = User.objects.get(email='user@example.com')
>>> tracking, _ = TrialUsageTracking.objects.get_or_create(user=user)
>>> tracking.has_used_trial = True
>>> tracking.first_trial_at = timezone.now()
>>> tracking.save()
>>> print("Trial marked as used")

# Solution 2: Re-process webhook event
>>> from djstripe.models import Event
>>> event = Event.objects.filter(
...     type='customer.subscription.created',
...     customer__subscriber=user
... ).latest('created')
>>> from apps.subscriptions.signals import track_trial_on_subscription_created
>>> track_trial_on_subscription_created(sender=None, event=event)

# Solution 3: Check webhook delivery in Stripe Dashboard
# Developers > Events > Filter: customer.subscription.created
# Verify event was sent and delivered successfully
```

**Verification:**
```bash
# Test trial eligibility
curl https://financehub-production.up.railway.app/api/subscriptions/status/ \
  -H "Authorization: Bearer <token>"
# Expected: "has_used_trial": true
```

---

### Issue 7: User gets trial despite having previous subscription

**Symptoms:**
- User with canceled subscription receives trial again
- Trial eligibility logic not working
- Multiple trials per user

**Diagnosis:**
```bash
python manage.py shell
>>> from apps.authentication.models import User
>>> from djstripe.models import Subscription
>>> from apps.subscriptions.models import TrialUsageTracking
>>>
>>> user = User.objects.get(email='user@example.com')
>>>
>>> # Check trial tracking
>>> tracking = TrialUsageTracking.objects.filter(user=user).first()
>>> print(f"Trial tracking: {tracking.has_used_trial if tracking else 'None'}")
>>>
>>> # Check past subscriptions
>>> past_subs = Subscription.objects.filter(customer__subscriber=user)
>>> print(f"Past subscriptions: {past_subs.count()}")
>>> for sub in past_subs:
...     print(f"  - {sub.id}: {sub.status}, trial: {sub.trial_end}")
```

**Root Causes:**
1. Trial tracking not created/updated
2. Logic in checkout view not checking past subscriptions
3. Customer has multiple Customer records (not properly linked)

**Solutions:**
```bash
# Solution 1: Verify trial eligibility logic
# Check backend/apps/subscriptions/views.py:60-64
# Should check both trial_tracking.has_used_trial AND past subscriptions

# Solution 2: Fix trial tracking for existing users
python manage.py shell
>>> from apps.authentication.models import User
>>> from djstripe.models import Subscription
>>> from apps.subscriptions.models import TrialUsageTracking
>>> from django.utils import timezone
>>>
>>> # Find users with subscriptions but no trial tracking
>>> users_with_subs = User.objects.filter(
...     customer__subscription__isnull=False
... ).distinct()
>>>
>>> for user in users_with_subs:
...     tracking, created = TrialUsageTracking.objects.get_or_create(user=user)
...     if not tracking.has_used_trial:
...         sub = Subscription.objects.filter(customer__subscriber=user).first()
...         tracking.has_used_trial = True
...         tracking.first_trial_at = sub.created or timezone.now()
...         tracking.save()
...         print(f"Fixed trial tracking for {user.email}")

# Solution 3: Run batch fix
python manage.py check_trial_status
```

**Verification:**
```bash
# Test checkout for user with past subscription
curl -X POST https://financehub-production.up.railway.app/api/subscriptions/checkout/ \
  -H "Authorization: Bearer <token>"
# Then check created subscription in Stripe Dashboard
# Trial period days should be 0
```

---

## Access Control Problems

### Issue 8: User with active subscription denied access

**Symptoms:**
- Middleware returns 402 error
- User has active/trialing subscription
- API requests fail with "Subscription required"

**Diagnosis:**
```bash
python manage.py shell
>>> from apps.authentication.models import User
>>> from djstripe.models import Subscription, Customer
>>>
>>> user = User.objects.get(email='user@example.com')
>>>
>>> # Check has_active_subscription property
>>> print(f"Has active subscription: {user.has_active_subscription}")
>>>
>>> # Check subscription details
>>> subs = Subscription.objects.filter(
...     customer__subscriber=user,
...     status__in=['trialing', 'active', 'past_due']
... )
>>> print(f"Active subscriptions: {subs.count()}")
>>> for sub in subs:
...     print(f"  - {sub.id}: {sub.status}")
>>>
>>> # Check customer link
>>> customer = Customer.objects.filter(subscriber=user).first()
>>> print(f"Customer: {customer.id if customer else 'NOT LINKED'}")
>>> print(f"Customer subscriber: {customer.subscriber if customer else 'None'}")
```

**Root Causes:**
1. Customer not linked to User (`customer.subscriber` is None)
2. Subscription status not in allowed list
3. Subscription not synced from Stripe
4. Multiple Customer records causing query issues

**Solutions:**
```bash
# Solution 1: Fix customer link
python manage.py fix_customer_links

# Solution 2: Manual customer link
python manage.py shell
>>> from apps.authentication.models import User
>>> from djstripe.models import Customer
>>>
>>> user = User.objects.get(email='user@example.com')
>>> customer = Customer.objects.get(email=user.email)  # or by id
>>> customer.subscriber = user
>>> customer.save()
>>> print(f"Linked Customer {customer.id} to User {user.id}")

# Solution 3: Re-sync subscription
>>> from djstripe.models import Subscription
>>> import stripe
>>> from django.conf import settings
>>> stripe.api_key = settings.STRIPE_SECRET_KEY
>>>
>>> stripe_sub = stripe.Subscription.retrieve('sub_xxxxxxxxxxxxx')
>>> dj_sub = Subscription.sync_from_stripe_data(stripe_sub)
>>> print(f"Synced subscription: {dj_sub.status}")

# Solution 4: Check for duplicate customers
>>> customers = Customer.objects.filter(email=user.email)
>>> print(f"Customer count: {customers.count()}")
>>> if customers.count() > 1:
...     # Keep the one with subscriber link or most recent
...     keep = customers.filter(subscriber=user).first() or customers.latest('created')
...     Customer.objects.exclude(id=keep.id).delete()
...     print(f"Removed duplicates, kept {keep.id}")
```

**Verification:**
```bash
# Test API access
curl https://financehub-production.up.railway.app/api/banking/accounts/ \
  -H "Authorization: Bearer <token>"
# Expected: 200 OK with data (not 402)
```

---

### Issue 9: Middleware blocking exempt paths

**Symptoms:**
- Authentication endpoints blocked
- Subscription endpoints blocked
- Users can't access checkout

**Diagnosis:**
```bash
# Check middleware configuration
grep -A 30 "EXEMPT_PATHS" backend/apps/subscriptions/middleware.py

# Check if middleware is enabled
grep "SubscriptionRequiredMiddleware" backend/core/settings/production.py
```

**Root Causes:**
1. Exempt path not in EXEMPT_PATHS list
2. Path matching logic incorrect
3. Middleware order issue

**Solutions:**
```bash
# Solution 1: Add path to EXEMPT_PATHS
# Edit backend/apps/subscriptions/middleware.py
# Add path to EXEMPT_PATHS list (line 18-30)

# Solution 2: Verify path matching
python manage.py shell
>>> from apps.subscriptions.middleware import SubscriptionRequiredMiddleware
>>> middleware = SubscriptionRequiredMiddleware(None)
>>> path = '/api/subscriptions/checkout/'
>>> is_exempt = middleware.is_exempt_path(path)
>>> print(f"Path {path} exempt: {is_exempt}")  # Should be True

# Solution 3: Disable middleware temporarily for testing
# Comment out in core/settings/production.py MIDDLEWARE list
# Redeploy and test
```

**Verification:**
```bash
# Test exempt endpoint without subscription
curl https://financehub-production.up.railway.app/api/subscriptions/config/
# Expected: 200 OK (no authentication required)
```

---

## Payment Processing Issues

### Issue 10: Payment method attachment fails

**Symptoms:**
- Checkout succeeds but payment method not attached
- Subscription created but no default payment method
- First payment fails

**Diagnosis:**
```bash
python manage.py shell
>>> from djstripe.models import Subscription, PaymentMethod
>>> sub = Subscription.objects.get(id='sub_xxxxxxxxxxxxx')
>>> print(f"Default payment method: {sub.default_payment_method}")
>>>
>>> # Check customer's payment methods
>>> customer = sub.customer
>>> pms = PaymentMethod.objects.filter(customer=customer)
>>> print(f"Payment methods: {pms.count()}")
>>> for pm in pms:
...     print(f"  - {pm.id}: {pm.type}")
```

**Root Causes:**
1. Payment method not attached during checkout
2. Stripe Checkout not configured to save payment method
3. Customer invoice settings not set

**Solutions:**
```bash
# Solution 1: Verify Stripe Checkout configuration
# Check backend/apps/subscriptions/views.py:81-96
# Ensure subscription_data includes payment method saving

# Solution 2: Attach payment method manually (if needed)
python manage.py shell
>>> import stripe
>>> from django.conf import settings
>>> stripe.api_key = settings.STRIPE_SECRET_KEY
>>>
>>> # Attach payment method
>>> stripe.PaymentMethod.attach(
...     'pm_xxxxxxxxxxxxx',
...     customer='cus_xxxxxxxxxxxxx'
... )
>>>
>>> # Set as default
>>> stripe.Customer.modify(
...     'cus_xxxxxxxxxxxxx',
...     invoice_settings={'default_payment_method': 'pm_xxxxxxxxxxxxx'}
... )

# Solution 3: Re-sync payment method
>>> from djstripe.models import PaymentMethod
>>> stripe_pm = stripe.PaymentMethod.retrieve('pm_xxxxxxxxxxxxx')
>>> dj_pm = PaymentMethod.sync_from_stripe_data(stripe_pm)
```

**Verification:**
```bash
# Check in Stripe Dashboard
# Customers > Select customer > Payment methods
# Should show attached payment method
```

---

## Data Synchronization Issues

### Issue 11: Stale subscription data

**Symptoms:**
- Subscription status in database doesn't match Stripe
- Cancellations not reflected
- Status changes delayed

**Diagnosis:**
```bash
python manage.py shell
>>> from djstripe.models import Subscription
>>> import stripe
>>> from django.conf import settings
>>> stripe.api_key = settings.STRIPE_SECRET_KEY
>>>
>>> sub_id = 'sub_xxxxxxxxxxxxx'
>>>
>>> # Compare database vs Stripe
>>> db_sub = Subscription.objects.get(id=sub_id)
>>> print(f"Database status: {db_sub.status}")
>>> print(f"Database updated: {db_sub.modified}")
>>>
>>> stripe_sub = stripe.Subscription.retrieve(sub_id)
>>> print(f"Stripe status: {stripe_sub.status}")
>>> print(f"Match: {db_sub.status == stripe_sub.status}")
```

**Root Causes:**
1. Webhook not delivered
2. Webhook processing failed
3. Data not synced after manual Stripe Dashboard changes

**Solutions:**
```bash
# Solution 1: Manual sync of specific subscription
python manage.py shell
>>> from djstripe.models import Subscription
>>> import stripe
>>> from django.conf import settings
>>> stripe.api_key = settings.STRIPE_SECRET_KEY
>>>
>>> stripe_sub = stripe.Subscription.retrieve('sub_xxxxxxxxxxxxx')
>>> dj_sub = Subscription.sync_from_stripe_data(stripe_sub)
>>> print(f"Synced: {dj_sub.status}")

# Solution 2: Full sync
python manage.py sync_stripe

# Solution 3: Check webhook delivery
# Stripe Dashboard > Webhooks > Recent deliveries
# Resend failed webhooks if needed
```

**Verification:**
```bash
# Compare database and Stripe
python manage.py shell
>>> from djstripe.models import Subscription
>>> import stripe
>>> stripe.api_key = settings.STRIPE_SECRET_KEY
>>>
>>> for sub in Subscription.objects.filter(status__in=['active', 'trialing'])[:5]:
...     stripe_sub = stripe.Subscription.retrieve(sub.id)
...     match = "✓" if sub.status == stripe_sub.status else "✗"
...     print(f"{match} {sub.id}: DB={sub.status}, Stripe={stripe_sub.status}")
```

---

## Customer Portal Issues

### Issue 12: Portal session creation fails

**Symptoms:**
- Portal endpoint returns error
- Customer can't manage subscription
- Error: "Unable to create portal session"

**Diagnosis:**
```bash
python manage.py shell
>>> from apps.authentication.models import User
>>> from djstripe.models import Customer
>>>
>>> user = User.objects.get(email='user@example.com')
>>> customer = Customer.objects.filter(subscriber=user).first()
>>>
>>> print(f"Customer found: {customer.id if customer else 'None'}")
>>>
>>> if customer:
...     import stripe
...     from django.conf import settings
...     stripe.api_key = settings.STRIPE_SECRET_KEY
...     try:
...         session = stripe.billing_portal.Session.create(
...             customer=customer.id,
...             return_url='https://caixahub.com.br'
...         )
...         print(f"Portal URL: {session.url}")
...     except Exception as e:
...         print(f"Error: {e}")
```

**Root Causes:**
1. Customer not linked to user
2. Customer Portal not configured in Stripe Dashboard
3. Customer doesn't exist in Stripe

**Solutions:**
```bash
# Solution 1: Enable Customer Portal
# Stripe Dashboard > Settings > Billing > Customer Portal
# Click "Enable customer portal"
# Configure allowed features
# Save

# Solution 2: Fix customer link
python manage.py fix_customer_links

# Solution 3: Verify customer in Stripe
python manage.py shell
>>> from djstripe.models import Customer
>>> customer = Customer.objects.get(id='cus_xxxxxxxxxxxxx')
>>> stripe_customer = customer.api_retrieve()
>>> print(f"Customer exists: {stripe_customer.id}")
```

**Verification:**
```bash
curl -X POST https://financehub-production.up.railway.app/api/subscriptions/portal/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"return_url": "https://caixahub.com.br/settings"}'
# Expected: {"url": "https://billing.stripe.com/..."}
```

---

## Emergency Procedures

### Complete System Reset (Last Resort)

**WARNING: This will delete all subscription data. Only use if instructed.**

```bash
# 1. Backup database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# 2. Clear djstripe tables
python manage.py shell
>>> from djstripe.models import *
>>> WebhookEndpoint.objects.all().delete()
>>> Event.objects.all().delete()
>>> Subscription.objects.all().delete()
>>> Customer.objects.all().delete()
>>> Price.objects.all().delete()
>>> Product.objects.all().delete()
>>> # etc.

# 3. Re-run migrations
python manage.py migrate djstripe --fake-initial

# 4. Re-sync from Stripe
python manage.py sync_stripe

# 5. Re-register webhooks
python manage.py register_stripe_webhook
```

---

## Support Resources

**Stripe Dashboard URLs:**
- Webhooks: https://dashboard.stripe.com/webhooks
- Events: https://dashboard.stripe.com/events
- Subscriptions: https://dashboard.stripe.com/subscriptions
- Customers: https://dashboard.stripe.com/customers
- Products: https://dashboard.stripe.com/products
- Logs: https://dashboard.stripe.com/logs

**Documentation:**
- dj-stripe: https://dj-stripe.readthedocs.io/
- Stripe API: https://stripe.com/docs/api
- Stripe Webhooks: https://stripe.com/docs/webhooks

**Log Locations:**
- Railway: App > Deployments > View logs
- Stripe: Dashboard > Developers > Logs
- Webhook: Dashboard > Webhooks > Recent deliveries
