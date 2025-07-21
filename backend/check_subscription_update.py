#!/usr/bin/env python
"""Check if subscription was updated"""
import os
import sys
import django
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from apps.companies.models import Company, PaymentHistory
from apps.authentication.models import User

print("=== CHECKING RECENT SUBSCRIPTION UPDATES ===\n")

# Check companies with active status
active_companies = Company.objects.filter(subscription_status='active').order_by('-updated_at')[:5]

if active_companies:
    print("ACTIVE SUBSCRIPTIONS:")
    for company in active_companies:
        print(f"\n✓ {company.name}")
        print(f"  Owner: {company.owner.email}")
        print(f"  Status: {company.subscription_status}")
        print(f"  Plan: {company.subscription_plan.name if company.subscription_plan else 'NO PLAN'}")
        print(f"  Billing: {company.billing_cycle}")
        print(f"  Subscription ID: {company.subscription_id[:20]}..." if company.subscription_id else "  Subscription ID: None")
        print(f"  Updated: {company.updated_at}")
else:
    print("No active subscriptions found\n")

# Check recent payments
print("\n" + "="*50)
print("RECENT PAYMENTS (Last 24h):\n")

since = datetime.now() - timedelta(hours=24)
recent_payments = PaymentHistory.objects.filter(
    created_at__gte=since
).order_by('-created_at')

if recent_payments:
    for payment in recent_payments:
        print(f"• {payment.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Company: {payment.company.name}")
        print(f"  Plan: {payment.subscription_plan.name if payment.subscription_plan else 'N/A'}")
        print(f"  Amount: R$ {payment.amount}")
        print(f"  Status: {payment.status}")
        print(f"  Type: {payment.transaction_type}")
        print()
else:
    print("No recent payments found")

# Check your specific user
your_email = input("\nEnter your email to check your subscription: ").strip()
if your_email:
    try:
        user = User.objects.get(email=your_email)
        if hasattr(user, 'company'):
            company = user.company
            print(f"\nYOUR SUBSCRIPTION STATUS:")
            print(f"  Company: {company.name}")
            print(f"  Status: {company.subscription_status}")
            print(f"  Plan: {company.subscription_plan.name if company.subscription_plan else 'NO PLAN'}")
            print(f"  Billing: {company.billing_cycle}")
            print(f"  Next billing: {company.next_billing_date}")
    except User.DoesNotExist:
        print("User not found")