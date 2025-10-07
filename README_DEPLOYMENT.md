# Stripe Production Deployment Documentation

**Complete documentation package for deploying dj-stripe subscription system to production**

---

## Quick Navigation

### For First-Time Deployment
1. **Start here:** [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) - Overview and decision tree
2. **Then read:** [STRIPE_PRODUCTION_DEPLOYMENT.md](STRIPE_PRODUCTION_DEPLOYMENT.md) - Complete step-by-step guide
3. **Keep handy:** [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md) - Command reference
4. **If issues:** [STRIPE_TROUBLESHOOTING.md](STRIPE_TROUBLESHOOTING.md) - Problem solving

### For Experienced Developers
1. **Use:** [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md) - Fast execution
2. **Reference:** [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) - System architecture
3. **If stuck:** [STRIPE_TROUBLESHOOTING.md](STRIPE_TROUBLESHOOTING.md) - Quick fixes

### For Understanding the System
1. **Read:** [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) - Visual architecture
2. **Then:** [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) - Key concepts
3. **Details:** [STRIPE_PRODUCTION_DEPLOYMENT.md](STRIPE_PRODUCTION_DEPLOYMENT.md) - Implementation

---

## Document Index

### 1. DEPLOYMENT_SUMMARY.md
**Purpose:** High-level overview and navigation guide
**Use when:** First learning about the system or deciding which guide to use
**Contents:**
- Document overview and purpose
- System architecture summary
- Key concepts (test vs production, webhooks, trial logic)
- Decision tree for which guide to use
- Pre-flight checklist
- Success criteria
- Common pitfalls

**Target audience:** Everyone
**Reading time:** 15 minutes

### 2. STRIPE_PRODUCTION_DEPLOYMENT.md
**Purpose:** Complete step-by-step deployment guide
**Use when:** Deploying to production for the first time
**Contents:**
- 8 detailed deployment phases
- Environment variable configuration
- Database migrations
- Data synchronization procedures
- Webhook setup and verification
- Post-deployment testing
- Monitoring and maintenance
- Rollback procedures
- Security notes

**Target audience:** Developers deploying to production
**Execution time:** 3-4 hours (first time)

### 3. DEPLOYMENT_QUICKSTART.md
**Purpose:** Fast reference for experienced developers
**Use when:** You know what you're doing, just need commands
**Contents:**
- Copy-paste ready commands
- Sequential execution order
- Quick verification steps
- Common fixes
- Minimal explanations

**Target audience:** Experienced developers, repeat deployments
**Execution time:** 1-2 hours

### 4. STRIPE_TROUBLESHOOTING.md
**Purpose:** Diagnostic and problem-solving guide
**Use when:** Something isn't working in production
**Contents:**
- 12 common issue scenarios
- Diagnostic procedures
- Root cause analysis
- Step-by-step solutions
- Verification procedures
- Emergency reset procedures

**Target audience:** Developers troubleshooting issues
**Reference time:** As needed per issue

### 5. ARCHITECTURE_DIAGRAM.md
**Purpose:** Visual system architecture reference
**Use when:** Understanding how components interact
**Contents:**
- System overview diagram
- Data flow diagrams (checkout, access control, webhooks)
- Component interaction maps
- Database schema relationships
- Security architecture
- Deployment states
- Monitoring points

**Target audience:** Technical architects, developers
**Reading time:** 20 minutes

---

## Document Relationships

```
START HERE
    │
    ▼
┌─────────────────────────────────┐
│  DEPLOYMENT_SUMMARY.md          │
│  (Overview & Navigation)        │
└────────────┬────────────────────┘
             │
             ├──────────────────────────────────────┐
             │                                      │
             ▼                                      ▼
┌─────────────────────────────┐      ┌─────────────────────────────┐
│  First Time Deployer?       │      │  Experienced Developer?     │
└────────────┬────────────────┘      └────────────┬────────────────┘
             │                                      │
             ▼                                      ▼
┌─────────────────────────────┐      ┌─────────────────────────────┐
│  STRIPE_PRODUCTION_         │      │  DEPLOYMENT_QUICKSTART.md   │
│  DEPLOYMENT.md              │      │  (Command Reference)        │
│  (Full Step-by-Step)        │      └────────────┬────────────────┘
└────────────┬────────────────┘                   │
             │                                     │
             ▼                                     ▼
┌─────────────────────────────┐      ┌─────────────────────────────┐
│  DEPLOYMENT_QUICKSTART.md   │      │  Execute Commands           │
│  (For Future Deployments)   │      └────────────┬────────────────┘
└─────────────────────────────┘                   │
                                                  │
             ┌────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Issues During Deployment?      │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  STRIPE_TROUBLESHOOTING.md      │
│  (Problem Solving)              │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Issue Resolved                 │
│  Continue Deployment            │
└─────────────────────────────────┘

REFERENCE ANYTIME
    │
    ▼
┌─────────────────────────────────┐
│  ARCHITECTURE_DIAGRAM.md        │
│  (System Understanding)         │
└─────────────────────────────────┘
```

---

## Key Files in Codebase

### Subscription System
```
backend/apps/subscriptions/
├── models.py                  # TrialUsageTracking model
├── services.py               # Business logic & Stripe API calls
├── views.py                  # API endpoints
├── signals.py                # Webhook event handlers
├── middleware.py             # Access control
├── urls.py                   # URL routing
└── management/commands/
    ├── sync_stripe.py        # Data synchronization
    ├── register_stripe_webhook.py  # Webhook setup
    ├── check_trial_status.py # Trial monitoring
    └── fix_customer_links.py # Customer-User linking
```

### Authentication
```
backend/apps/authentication/
└── models.py                 # User model with has_active_subscription
```

### Configuration
```
backend/core/
├── settings/
│   ├── base.py              # Base settings
│   └── production.py        # Production settings (Stripe config)
└── urls.py                  # Main routing (includes djstripe URLs)
```

### Frontend Integration
```
frontend/
├── services/
│   └── subscription.service.ts  # Subscription API client
└── components/
    └── subscription/
        └── SubscriptionManagement.tsx  # Subscription UI
```

---

## Quick Reference Commands

### Initial Setup
```bash
# 1. Migrations
python manage.py migrate djstripe
python manage.py migrate subscriptions

# 2. Data Sync
python manage.py sync_stripe

# 3. Webhook Registration
python manage.py register_stripe_webhook

# 4. Verify
python manage.py check_trial_status
```

### Maintenance Commands
```bash
# Fix customer links
python manage.py fix_customer_links

# Re-sync data
python manage.py sync_stripe

# Check trial status
python manage.py check_trial_status

# Database shell
python manage.py shell
python manage.py dbshell
```

### Diagnostic Commands
```bash
# Check webhook endpoints
python manage.py shell
>>> from djstripe.models import WebhookEndpoint
>>> WebhookEndpoint.objects.all()

# Check recent events
>>> from djstripe.models import Event
>>> Event.objects.all().order_by('-created')[:10]

# Check subscriptions
>>> from djstripe.models import Subscription
>>> Subscription.objects.filter(status='active')
```

---

## Environment Variables Checklist

```bash
# Required for Production
DJANGO_SECRET_KEY=<production-secret>
JWT_SECRET_KEY=<jwt-secret>
DJANGO_SETTINGS_MODULE=core.settings.production
DATABASE_URL=<postgres-url>
FRONTEND_URL=https://caixahub.com.br

# Stripe Production
STRIPE_LIVE_MODE=true
STRIPE_LIVE_SECRET_KEY=sk_live_...
STRIPE_LIVE_PUBLIC_KEY=pk_live_...
STRIPE_DEFAULT_PRICE_ID=price_...
DJSTRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Test (keep for fallback)
STRIPE_TEST_SECRET_KEY=sk_test_...
STRIPE_TEST_PUBLIC_KEY=pk_test_...
```

---

## API Endpoints Reference

### Subscription Management
```
POST   /api/subscriptions/checkout/     # Create checkout session
GET    /api/subscriptions/status/       # Get subscription status
POST   /api/subscriptions/portal/       # Create portal session
GET    /api/subscriptions/config/       # Get Stripe public key
```

### Webhooks
```
POST   /stripe/webhook/{uuid}/          # dj-stripe webhook handler
```

### Protected Endpoints (Require Subscription)
```
GET    /api/banking/accounts/           # Banking data
GET    /api/banking/transactions/       # Transactions
# ... and other protected endpoints
```

---

## Success Indicators

Your deployment is successful when:

✓ Webhook test in Stripe Dashboard returns 200 OK
✓ End-to-end checkout creates subscription in database
✓ Trial is applied to eligible users
✓ Customer is linked to User (subscriber field set)
✓ Subscription status endpoint returns accurate data
✓ Access control blocks non-subscribed users
✓ Customer Portal creates successfully
✓ Webhook events appear in database
✓ Logs show successful event processing

---

## Common Issues Quick Reference

| Issue | Quick Fix | Document |
|-------|-----------|----------|
| Webhook 401 | Re-sync webhook secret | STRIPE_TROUBLESHOOTING.md #1 |
| Webhook 404 | Check URL format | STRIPE_TROUBLESHOOTING.md #2 |
| Customer not linked | Run fix_customer_links | STRIPE_TROUBLESHOOTING.md #4 |
| Trial not tracked | Manual mark via shell | STRIPE_TROUBLESHOOTING.md #6 |
| Access denied with sub | Check customer link | STRIPE_TROUBLESHOOTING.md #8 |
| Stale subscription | Re-sync from Stripe | STRIPE_TROUBLESHOOTING.md #11 |
| Portal fails | Enable in Dashboard | STRIPE_TROUBLESHOOTING.md #12 |

---

## Support Resources

### Stripe
- Dashboard: https://dashboard.stripe.com
- API Docs: https://stripe.com/docs/api
- Webhooks: https://stripe.com/docs/webhooks
- Support: https://support.stripe.com

### dj-stripe
- Documentation: https://dj-stripe.readthedocs.io/
- GitHub: https://github.com/dj-stripe/dj-stripe
- Issues: https://github.com/dj-stripe/dj-stripe/issues

### Railway
- Dashboard: https://railway.app
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway

### Django
- Documentation: https://docs.djangoproject.com/
- REST Framework: https://www.django-rest-framework.org/

---

## Version Information

- **Documentation Version:** 1.0
- **Last Updated:** 2025-10-06
- **Compatible With:**
  - dj-stripe: 2.x
  - Django: 4.x
  - Python: 3.9+
  - Stripe API: 2024-x

---

## Next Steps

1. **Read DEPLOYMENT_SUMMARY.md** to understand the system
2. **Review environment checklist** to ensure you have everything
3. **Follow the deployment guide** appropriate for your experience level
4. **Test thoroughly** using the verification procedures
5. **Monitor closely** for the first 24-48 hours
6. **Refer to troubleshooting** if any issues arise

---

## Maintenance Schedule

**Daily (First Week):**
- Monitor webhook deliveries in Stripe Dashboard
- Review application logs for errors
- Check failed payment notifications

**Weekly:**
- Run `check_trial_status` command
- Verify customer-user links with `fix_customer_links`
- Review subscription churn metrics

**Monthly:**
- Full data sync: `python manage.py sync_stripe`
- Database performance review
- Security audit of environment variables

**Quarterly:**
- Update dj-stripe to latest version
- Review and update webhook event handlers
- Test rollback procedures

---

## Credits and Acknowledgments

This deployment documentation was created through comprehensive analysis of:
- dj-stripe integration architecture
- Custom subscription service layer
- Django middleware implementation
- Stripe webhook processing flow
- Database schema relationships
- Security configurations

Special attention was given to:
- Trial eligibility logic
- Customer-User linking
- Access control implementation
- Webhook signature verification
- Error handling and retry mechanisms

---

## License

This documentation is part of the CaixaHub project and follows the same license as the main project.

---

## Contact

For questions about this deployment documentation or the subscription system:
- Review the troubleshooting guide first
- Check Stripe Dashboard for webhook/payment issues
- Consult Railway logs for application errors
- Refer to dj-stripe documentation for model questions

---

**Remember:** Production deployment is a systematic process. Follow the guides in order, verify each step, and don't skip the testing procedures. Your careful execution will result in a robust, secure subscription system.

Good luck with your deployment!
