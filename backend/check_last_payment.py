#!/usr/bin/env python
"""Check last payment and subscription status"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from apps.companies.models import Company, PaymentHistory
from apps.authentication.models import User
from datetime import datetime, timedelta
from django.utils import timezone

print("=== CHECKING LAST PAYMENT AND SUBSCRIPTION ===\n")

# Get the last payment
last_payment = PaymentHistory.objects.order_by('-created_at').first()

if last_payment:
    print(f"Last Payment:")
    print(f"  Date: {last_payment.created_at}")
    print(f"  Company: {last_payment.company.name}")
    print(f"  Plan: {last_payment.subscription_plan.name if last_payment.subscription_plan else 'N/A'}")
    print(f"  Amount: R$ {last_payment.amount}")
    print(f"  Status: {last_payment.status}")
    print(f"  Type: {last_payment.transaction_type}")
    print(f"  Stripe Payment ID: {last_payment.stripe_payment_intent_id or 'N/A'}")
    
    # Check company status
    company = last_payment.company
    print(f"\nCompany Status:")
    print(f"  Name: {company.name}")
    print(f"  Status: {company.subscription_status}")
    print(f"  Plan: {company.subscription_plan.name if company.subscription_plan else 'NO PLAN'}")
    print(f"  Billing Cycle: {company.billing_cycle}")
    print(f"  Subscription ID: {company.subscription_id or 'N/A'}")
    print(f"  Next Billing: {company.next_billing_date}")
else:
    print("No payments found")

# Check recent companies with trial status
print("\n" + "="*50)
print("COMPANIES IN TRIAL:\n")

trial_companies = Company.objects.filter(subscription_status='trial').order_by('-created_at')[:5]
for company in trial_companies:
    days_left = 0
    if company.trial_ends_at:
        delta = company.trial_ends_at - timezone.now()
        days_left = max(0, delta.days)
    
    print(f"- {company.name} ({company.owner.email})")
    print(f"  Trial ends: {company.trial_ends_at}")
    print(f"  Days left: {days_left}")
    print(f"  Plan: {company.subscription_plan.name if company.subscription_plan else 'NO PLAN'}")
    print()

# Check if webhook URL is correct
print("="*50)
print("\nWEBHOOK INFO:")
print(f"Expected URL: https://finance-backend-production-29df.up.railway.app/api/payments/webhooks/stripe/")
print("Make sure this matches the URL in Stripe dashboard!")