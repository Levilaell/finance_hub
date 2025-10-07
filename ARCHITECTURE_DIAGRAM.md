# Stripe Subscription System Architecture

**Visual representation of the complete subscription system architecture**

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                          │
│                      https://caixahub.com.br                        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ HTTPS/REST API
                                   │ JWT Authentication
                                   │
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (Django/Railway)                       │
│              https://financehub-production.up.railway.app           │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │              API Layer (Django REST Framework)             │   │
│  │                                                             │   │
│  │  /api/subscriptions/checkout/  ─────────────────────┐     │   │
│  │  /api/subscriptions/status/    ─────────────────┐   │     │   │
│  │  /api/subscriptions/portal/    ───────────┐     │   │     │   │
│  │  /api/subscriptions/config/    ─────┐     │     │   │     │   │
│  │  /api/banking/accounts/        ─┐   │     │     │   │     │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                  │   │     │     │   │     │       │
│                                  │   │     │     │   │     │       │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │           Subscription Middleware                          │   │
│  │                                                             │   │
│  │  1. Check if user is authenticated                         │   │
│  │  2. Check if path requires subscription                    │   │
│  │  3. Query: has_active_subscription property                │   │
│  │  4. Allow or Block (402 Payment Required)                  │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                  │   │     │     │   │     │       │
│                                  ▼   ▼     ▼     ▼   ▼     ▼       │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │              Subscription Services Layer                   │   │
│  │                                                             │   │
│  │  • get_or_create_customer()                                │   │
│  │  • create_subscription_with_trial()                        │   │
│  │  • get_subscription_status()                               │   │
│  │  • create_customer_portal_session()                        │   │
│  │  • cancel_subscription()                                   │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                  │                                 │
│                                  │                                 │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                  dj-stripe Integration                      │   │
│  │                                                             │   │
│  │  • Webhook handler: /stripe/webhook/{uuid}/                │   │
│  │  • Signature verification                                  │   │
│  │  • Event processing                                        │   │
│  │  • Model synchronization                                   │   │
│  │  • Signal dispatching                                      │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                  │                                 │
│                                  ▼                                 │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │              Signal Handlers (Webhooks)                    │   │
│  │                                                             │   │
│  │  customer.subscription.created  → track_trial_usage        │   │
│  │  customer.subscription.updated  → handle_status_change     │   │
│  │  customer.subscription.deleted  → handle_cancellation      │   │
│  │  invoice.payment_succeeded      → log_payment              │   │
│  │  invoice.payment_failed         → log_failure              │   │
│  │  trial_will_end                 → send_notification        │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                  │                                 │
│                                  ▼                                 │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                    PostgreSQL Database                      │   │
│  │                                                             │   │
│  │  Django Models:                                             │   │
│  │  • User (authentication.User)                              │   │
│  │  • TrialUsageTracking (subscriptions)                      │   │
│  │                                                             │   │
│  │  dj-stripe Models (synced from Stripe):                    │   │
│  │  • Customer (linked to User via subscriber field)          │   │
│  │  • Subscription                                            │   │
│  │  • Product                                                 │   │
│  │  • Price                                                   │   │
│  │  • PaymentMethod                                           │   │
│  │  • Invoice                                                 │   │
│  │  • Event (webhook event log)                              │   │
│  │  • WebhookEndpoint                                         │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Stripe API Calls
                                   │ Webhook Delivery
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       STRIPE PLATFORM                               │
│                     https://stripe.com                              │
│                                                                     │
│  • Customer Management                                             │
│  • Subscription Management                                         │
│  • Payment Processing                                              │
│  • Checkout Sessions                                               │
│  • Customer Portal                                                 │
│  • Webhook Event Delivery                                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. Checkout Flow (New Subscription)

```
┌─────────┐
│  User   │
└────┬────┘
     │
     │ 1. Click "Subscribe"
     ▼
┌─────────────────────────────────────┐
│  Frontend: /checkout                │
│                                     │
│  Calls: POST /api/subscriptions/    │
│         checkout/                   │
└────────────────┬────────────────────┘
                 │
                 │ 2. Create Checkout Session
                 ▼
┌─────────────────────────────────────┐
│  Backend: create_checkout_session() │
│                                     │
│  1. Get/create Stripe Customer      │
│  2. Check trial eligibility         │
│  3. Create Stripe Checkout Session  │
│  4. Return checkout URL             │
└────────────────┬────────────────────┘
                 │
                 │ 3. Redirect to Stripe
                 ▼
┌─────────────────────────────────────┐
│  Stripe Checkout Page               │
│                                     │
│  User enters payment method         │
│  User confirms subscription         │
└────────────────┬────────────────────┘
                 │
                 │ 4. Payment Processing
                 ▼
┌─────────────────────────────────────┐
│  Stripe Platform                    │
│                                     │
│  1. Create Subscription (trialing)  │
│  2. Attach PaymentMethod            │
│  3. Set default payment method      │
└────────────────┬────────────────────┘
                 │
                 │ 5. Webhook: subscription.created
                 ▼
┌─────────────────────────────────────┐
│  Backend: /stripe/webhook/{uuid}/   │
│                                     │
│  1. Verify signature                │
│  2. Process event                   │
│  3. Sync subscription to DB         │
│  4. Trigger signals                 │
└────────────────┬────────────────────┘
                 │
                 │ 6. Signal Handler
                 ▼
┌─────────────────────────────────────┐
│  track_trial_on_subscription_       │
│  created()                          │
│                                     │
│  1. Check if trial_end exists       │
│  2. Get Customer from event         │
│  3. Mark trial as used              │
│  4. Save TrialUsageTracking         │
└────────────────┬────────────────────┘
                 │
                 │ 7. Redirect to success page
                 ▼
┌─────────────────────────────────────┐
│  Frontend: /checkout/success        │
│                                     │
│  Display success message            │
│  User now has access                │
└─────────────────────────────────────┘
```

### 2. Access Control Flow (Middleware)

```
┌─────────┐
│  User   │
└────┬────┘
     │
     │ HTTP Request to /api/banking/accounts/
     ▼
┌─────────────────────────────────────────┐
│  Django Middleware Stack                │
│                                         │
│  1. SecurityMiddleware                  │
│  2. CorsMiddleware                      │
│  3. SessionMiddleware                   │
│  4. AuthenticationMiddleware  ◄─────────┼─── JWT Token
│  5. SubscriptionRequiredMiddleware      │
└────────────────┬────────────────────────┘
                 │
                 │ Is user authenticated?
                 ▼
         ┌───────────────┐
         │ NO            │ YES
         │               │
         ▼               ▼
    ┌────────┐    ┌──────────────────┐
    │ Allow  │    │ Is path exempt?  │
    │ (pass) │    └────────┬─────────┘
    └────────┘             │
                           │
                   ┌───────┴───────┐
                   │ YES           │ NO
                   │               │
                   ▼               ▼
              ┌────────┐    ┌───────────────────┐
              │ Allow  │    │ Is superuser?     │
              │ (pass) │    └────────┬──────────┘
              └────────┘             │
                                     │
                             ┌───────┴───────┐
                             │ YES           │ NO
                             │               │
                             ▼               ▼
                        ┌────────┐    ┌─────────────────────┐
                        │ Allow  │    │ Check subscription  │
                        │ (pass) │    │ via property:       │
                        └────────┘    │ has_active_         │
                                      │ subscription        │
                                      └──────────┬──────────┘
                                                 │
                                         ┌───────┴───────┐
                                         │ TRUE          │ FALSE
                                         │               │
                                         ▼               ▼
                                    ┌────────┐    ┌───────────┐
                                    │ Allow  │    │ Block     │
                                    │ 200 OK │    │ 402 Error │
                                    └────────┘    └───────────┘
```

### 3. has_active_subscription Property Logic

```
┌────────────────────────────────────┐
│  User.has_active_subscription      │
│  (Property in User model)          │
└────────────────┬───────────────────┘
                 │
                 │ Query Database
                 ▼
┌────────────────────────────────────┐
│  Subscription.objects.filter(      │
│      customer__subscriber=user,    │
│      status__in=[                  │
│          'trialing',               │
│          'active',                 │
│          'past_due'                │
│      ]                             │
│  ).exists()                        │
└────────────────┬───────────────────┘
                 │
         ┌───────┴───────┐
         │ TRUE          │ FALSE
         │               │
         ▼               ▼
    ┌─────────┐    ┌──────────┐
    │ User    │    │ User has │
    │ has     │    │ no       │
    │ access  │    │ access   │
    └─────────┘    └──────────┘

Key Points:
• Checks customer__subscriber link (MUST exist)
• Accepts trialing, active, OR past_due status
• past_due = grace period during payment retry
• Returns False if link is broken
```

### 4. Webhook Processing Flow

```
┌─────────────────────────────────────┐
│  Stripe Event Occurs                │
│  (e.g., payment succeeded)          │
└────────────────┬────────────────────┘
                 │
                 │ Stripe sends POST request
                 ▼
┌─────────────────────────────────────┐
│  /stripe/webhook/{uuid}/            │
│  (dj-stripe URL handler)            │
└────────────────┬────────────────────┘
                 │
                 │ 1. Verify webhook signature
                 ▼
         ┌───────────────┐
         │ Valid?        │
         └───────┬───────┘
                 │
         ┌───────┴───────┐
         │ NO            │ YES
         │               │
         ▼               ▼
    ┌────────┐    ┌─────────────────┐
    │ Return │    │ Parse event     │
    │ 401    │    │ data            │
    └────────┘    └────────┬────────┘
                           │
                           │ 2. Save to Event model
                           ▼
                  ┌─────────────────┐
                  │ Sync related    │
                  │ objects to DB   │
                  │ (Customer,      │
                  │ Subscription,   │
                  │ etc.)           │
                  └────────┬────────┘
                           │
                           │ 3. Dispatch signal
                           ▼
                  ┌─────────────────┐
                  │ Signal handler  │
                  │ executes        │
                  └────────┬────────┘
                           │
                           │ 4. Custom logic
                           ▼
                  ┌─────────────────┐
                  │ • Update trial  │
                  │   tracking      │
                  │ • Log events    │
                  │ • Send emails   │
                  │   (future)      │
                  └────────┬────────┘
                           │
                           │ 5. Return success
                           ▼
                      ┌─────────┐
                      │ 200 OK  │
                      └─────────┘
```

### 5. Trial Eligibility Decision Tree

```
┌─────────────────────────────────────┐
│  User starts checkout               │
└────────────────┬────────────────────┘
                 │
                 │ Check trial eligibility
                 ▼
┌─────────────────────────────────────┐
│  Query TrialUsageTracking           │
│  for user                           │
└────────────────┬────────────────────┘
                 │
         ┌───────┴───────┐
         │ has_used_     │
         │ trial=True?   │
         └───────┬───────┘
                 │
         ┌───────┴───────┐
         │ YES           │ NO
         │               │
         ▼               ▼
    ┌────────┐    ┌─────────────────┐
    │ NO     │    │ Check past      │
    │ TRIAL  │    │ subscriptions   │
    │        │    └────────┬────────┘
    │ trial_ │             │
    │ days=0 │     ┌───────┴───────┐
    └────────┘     │ Any past      │
                   │ subscriptions?│
                   └───────┬───────┘
                           │
                   ┌───────┴───────┐
                   │ YES           │ NO
                   │               │
                   ▼               ▼
              ┌────────┐    ┌────────────┐
              │ NO     │    │ GRANT      │
              │ TRIAL  │    │ TRIAL      │
              │        │    │            │
              │ trial_ │    │ trial_     │
              │ days=0 │    │ days=7     │
              └────────┘    └────────────┘
```

---

## Component Interactions

### Services ↔ Stripe API

```
┌─────────────────────────────────────┐
│  Subscription Services              │
│  (services.py)                      │
└─────────────────┬───────────────────┘
                  │
                  │ Direct API Calls
                  ▼
         ┌────────────────┐
         │ Stripe API     │
         └────────┬───────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌────────┐  ┌──────────┐  ┌──────────┐
│Customer│  │Subscription││PaymentMethod│
│.create()│  │.create() │  │.attach() │
└────────┘  └──────────┘  └──────────┘
    │             │             │
    │             │             │
    └─────────────┼─────────────┘
                  │
                  │ Return Stripe Objects
                  ▼
┌─────────────────────────────────────┐
│  dj-stripe Sync Methods             │
│                                     │
│  Customer.sync_from_stripe_data()   │
│  Subscription.sync_from_stripe_data()│
│  PaymentMethod.sync_from_stripe_data()│
└─────────────────┬───────────────────┘
                  │
                  │ Save to Database
                  ▼
         ┌────────────────┐
         │ PostgreSQL     │
         └────────────────┘
```

### Signals ↔ Database

```
┌─────────────────────────────────────┐
│  Webhook Event Received             │
└─────────────────┬───────────────────┘
                  │
                  │ dj-stripe processes
                  ▼
┌─────────────────────────────────────┐
│  signals.WEBHOOK_SIGNALS[           │
│      "customer.subscription.created"│
│  ]                                  │
└─────────────────┬───────────────────┘
                  │
                  │ Dispatches to
                  ▼
┌─────────────────────────────────────┐
│  @receiver decorator                │
│  track_trial_on_subscription_created│
└─────────────────┬───────────────────┘
                  │
                  │ 1. Get event data
                  │ 2. Extract customer_id
                  │ 3. Query Customer
                  ▼
         ┌────────────────┐
         │ Database       │
         │ Queries        │
         └────────┬───────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌────────┐  ┌──────────┐  ┌──────────────┐
│Customer│  │ User     │  │TrialUsage    │
│.filter()│  │.get()   │  │Tracking      │
└────────┘  └──────────┘  │.get_or_create│
                          └──────────────┘
                                 │
                                 │ Update fields
                                 ▼
                          ┌──────────────┐
                          │ .save()      │
                          └──────────────┘
```

---

## Database Schema Relationships

```
┌─────────────────────────────────────┐
│  User (authentication.User)         │
│  ─────────────────────────────────  │
│  id (PK)                            │
│  email (unique)                     │
│  first_name                         │
│  last_name                          │
│  created_at                         │
└─────────────────┬───────────────────┘
                  │
                  │ One-to-One
                  ▼
┌─────────────────────────────────────┐
│  TrialUsageTracking                 │
│  ─────────────────────────────────  │
│  id (PK)                            │
│  user_id (FK → User) (unique)       │
│  has_used_trial (boolean)           │
│  first_trial_at (datetime)          │
│  created_at                         │
└─────────────────────────────────────┘

                  ┌──────────────────┐
                  │                  │
                  ▼                  │ One-to-Many
┌─────────────────────────────────────┐
│  Customer (djstripe.Customer)       │
│  ─────────────────────────────────  │
│  id (PK, Stripe ID: cus_xxx)        │
│  subscriber_id (FK → User) ◄────────┼─── CRITICAL LINK
│  email                              │
│  metadata (JSON)                    │
│  created                            │
└─────────────────┬───────────────────┘
                  │
                  │ One-to-Many
                  ▼
┌─────────────────────────────────────┐
│  Subscription (djstripe.Subscription)│
│  ─────────────────────────────────  │
│  id (PK, Stripe ID: sub_xxx)        │
│  customer_id (FK → Customer)        │
│  status (trialing/active/etc.)      │
│  trial_end (datetime)               │
│  current_period_end (datetime)      │
│  cancel_at_period_end (boolean)     │
│  default_payment_method_id (FK)     │
│  created                            │
└─────────────────┬───────────────────┘
                  │
                  │ Many-to-One
                  ▼
┌─────────────────────────────────────┐
│  Price (djstripe.Price)             │
│  ─────────────────────────────────  │
│  id (PK, Stripe ID: price_xxx)      │
│  product_id (FK → Product)          │
│  unit_amount (integer, in cents)    │
│  currency (BRL)                     │
│  recurring (JSON)                   │
└─────────────────┬───────────────────┘
                  │
                  │ Many-to-One
                  ▼
┌─────────────────────────────────────┐
│  Product (djstripe.Product)         │
│  ─────────────────────────────────  │
│  id (PK, Stripe ID: prod_xxx)       │
│  name                               │
│  description                        │
│  active (boolean)                   │
└─────────────────────────────────────┘
```

**Key Relationship:**
```
User ──[One-to-Many]──> Customer ──[One-to-Many]──> Subscription

Query to check access:
Subscription.objects.filter(
    customer__subscriber=user,  ◄─── This join is critical
    status__in=['trialing', 'active', 'past_due']
).exists()
```

---

## Environment Variable Flow

```
┌─────────────────────────────────────┐
│  Railway Environment Variables      │
│                                     │
│  STRIPE_LIVE_MODE=true              │
│  STRIPE_LIVE_SECRET_KEY=sk_live_xxx │
│  STRIPE_LIVE_PUBLIC_KEY=pk_live_xxx │
│  STRIPE_DEFAULT_PRICE_ID=price_xxx  │
│  DJSTRIPE_WEBHOOK_SECRET=whsec_xxx  │
└─────────────────┬───────────────────┘
                  │
                  │ Read at startup
                  ▼
┌─────────────────────────────────────┐
│  Django Settings                    │
│  (core/settings/production.py)     │
│                                     │
│  STRIPE_LIVE_MODE = env('...')      │
│  STRIPE_SECRET_KEY = (              │
│      LIVE_KEY if LIVE_MODE          │
│      else TEST_KEY                  │
│  )                                  │
└─────────────────┬───────────────────┘
                  │
                  │ Used by
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌────────┐  ┌──────────┐  ┌──────────┐
│Services│  │dj-stripe │  │Frontend  │
│        │  │          │  │API       │
│stripe. │  │DJSTRIPE_ │  │config    │
│api_key │  │settings  │  │endpoint  │
└────────┘  └──────────┘  └──────────┘
```

---

## Critical File Locations

```
finance_hub/
│
├── backend/
│   ├── apps/
│   │   ├── authentication/
│   │   │   └── models.py ◄───────────── User model with has_active_subscription
│   │   │
│   │   └── subscriptions/
│   │       ├── models.py ◄─────────── TrialUsageTracking
│   │       ├── services.py ◄────────── Business logic & Stripe API calls
│   │       ├── views.py ◄──────────── API endpoints
│   │       ├── signals.py ◄─────────── Webhook event handlers
│   │       ├── middleware.py ◄───────── Access control
│   │       ├── urls.py ◄─────────────── URL routing
│   │       │
│   │       └── management/commands/
│   │           ├── sync_stripe.py ◄──────── Data synchronization
│   │           ├── register_stripe_webhook.py ◄─ Webhook setup
│   │           ├── check_trial_status.py ◄────── Trial monitoring
│   │           └── fix_customer_links.py ◄────── Maintenance
│   │
│   └── core/
│       ├── settings/
│       │   ├── base.py ◄───────────────── Base configuration
│       │   └── production.py ◄─────────── Production settings
│       │
│       └── urls.py ◄────────────────────── Main URL config (includes djstripe)
│
└── frontend/
    └── services/
        └── subscription.service.ts ◄──── Frontend API client
```

---

## Security Architecture

```
┌─────────────────────────────────────┐
│  Frontend                           │
└─────────────────┬───────────────────┘
                  │
                  │ HTTPS only
                  │ Bearer JWT Token
                  ▼
┌─────────────────────────────────────┐
│  Django Security Middleware         │
│                                     │
│  • SECURE_SSL_REDIRECT=True         │
│  • SECURE_HSTS_SECONDS=31536000     │
│  • CORS_ALLOWED_ORIGINS (whitelist) │
│  • CSRF_TRUSTED_ORIGINS             │
└─────────────────┬───────────────────┘
                  │
                  │ JWT Validation
                  ▼
┌─────────────────────────────────────┐
│  JWT Authentication                 │
│                                     │
│  • HS256 algorithm                  │
│  • JWT_SECRET_KEY (separate)        │
│  • 30 min access token lifetime     │
│  • 3 day refresh token lifetime     │
│  • Token rotation enabled           │
│  • Blacklist after rotation         │
└─────────────────┬───────────────────┘
                  │
                  │ User authenticated
                  ▼
┌─────────────────────────────────────┐
│  Subscription Middleware            │
│  (Access Control)                   │
└─────────────────┬───────────────────┘
                  │
                  │ Subscription verified
                  ▼
┌─────────────────────────────────────┐
│  Protected Resources                │
└─────────────────────────────────────┘

Webhook Security:
┌─────────────────────────────────────┐
│  Stripe Webhook                     │
└─────────────────┬───────────────────┘
                  │
                  │ Stripe-Signature header
                  ▼
┌─────────────────────────────────────┐
│  dj-stripe Signature Verification   │
│                                     │
│  • DJSTRIPE_WEBHOOK_SECRET          │
│  • DJSTRIPE_WEBHOOK_VALIDATION=     │
│    'verify_signature'               │
│  • DJSTRIPE_WEBHOOK_TOLERANCE=300   │
└─────────────────┬───────────────────┘
                  │
                  │ Valid signature
                  ▼
┌─────────────────────────────────────┐
│  Process Event                      │
└─────────────────────────────────────┘
```

---

## Deployment States

### Test Mode (Development)
```
Frontend ──────► Backend (TEST keys) ──────► Stripe Test Mode
                     │                             │
                     ▼                             ▼
                PostgreSQL ◄──────────────── Test Products/Prices
                     │                             │
                     └─────► Test Cards ───────────┘
                              4242 4242 4242 4242
```

### Production Mode (Live)
```
Frontend ──────► Backend (LIVE keys) ──────► Stripe Production
                     │                             │
                     ▼                             ▼
                PostgreSQL ◄──────────────── Real Products/Prices
                     │                             │
                     └─────► Real Cards ───────────┘
                              User's actual cards
```

**Controlled by single variable:** `STRIPE_LIVE_MODE=true|false`

---

## Error Handling Flow

```
┌─────────────────────────────────────┐
│  User Action (e.g., checkout)      │
└─────────────────┬───────────────────┘
                  │
                  │ API Request
                  ▼
┌─────────────────────────────────────┐
│  Django View (try/except block)     │
└─────────────────┬───────────────────┘
                  │
         ┌────────┴────────┐
         │ Success?        │
         └────────┬────────┘
                  │
         ┌────────┴────────┐
         │ YES             │ NO
         │                 │
         ▼                 ▼
    ┌────────┐      ┌──────────────┐
    │ Return │      │ Catch Error  │
    │ 200 OK │      └──────┬───────┘
    │ + data │             │
    └────────┘             │
                           │
                  ┌────────┴────────┐
                  │ Error Type?     │
                  └────────┬────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ stripe.error │  │ Database     │  │ Generic      │
│ .CardError   │  │ Error        │  │ Exception    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         │ Log error
                         ▼
                ┌─────────────────┐
                │ logger.error()  │
                │ (with context)  │
                └────────┬────────┘
                         │
                         │ Return error response
                         ▼
                ┌─────────────────┐
                │ Return 400/500  │
                │ + error message │
                └─────────────────┘
```

---

## Monitoring Points

```
┌─────────────────────────────────────┐
│  1. Stripe Dashboard                │
│     • Webhook deliveries            │
│     • Payment status                │
│     • Subscription changes          │
└─────────────────────────────────────┘
                  │
                  │ Webhook events
                  ▼
┌─────────────────────────────────────┐
│  2. Application Logs (Railway)      │
│     • Webhook processing            │
│     • API request/response          │
│     • Error stack traces            │
└─────────────────────────────────────┘
                  │
                  │ Log entries
                  ▼
┌─────────────────────────────────────┐
│  3. Database (djstripe_event)       │
│     • Event history                 │
│     • Processing status             │
│     • Failure messages              │
└─────────────────────────────────────┘
                  │
                  │ Queries
                  ▼
┌─────────────────────────────────────┐
│  4. Management Commands             │
│     • check_trial_status            │
│     • Data consistency checks       │
└─────────────────────────────────────┘
```

---

This architecture diagram provides a visual understanding of how all components interact in the subscription system. Use it as a reference when troubleshooting or extending the system.
