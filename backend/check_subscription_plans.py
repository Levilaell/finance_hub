#!/usr/bin/env python
"""
Check subscription plans in both companies and payments apps
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from apps.companies.models import SubscriptionPlan as CompanyPlan
from apps.payments.models import SubscriptionPlan as PaymentPlan

def main():
    print("=== COMPANY PLANS (apps.companies) ===")
    try:
        company_plans = CompanyPlan.objects.all()
        for plan in company_plans:
            print(f"ID: {plan.id}, Name: {plan.name}, Display: {plan.display_name}")
        print(f"Total Company Plans: {company_plans.count()}")
    except Exception as e:
        print(f"Error accessing CompanyPlan: {e}")
    
    print("\n=== PAYMENT PLANS (apps.payments) ===")
    try:
        payment_plans = PaymentPlan.objects.all()
        for plan in payment_plans:
            print(f"ID: {plan.id}, Name: {plan.name}")
        print(f"Total Payment Plans: {payment_plans.count()}")
    except Exception as e:
        print(f"Error accessing PaymentPlan: {e}")
    
    # Check if we need to sync plans
    print("\n=== PLAN SYNC STATUS ===")
    try:
        company_count = CompanyPlan.objects.count()
        payment_count = PaymentPlan.objects.count()
        
        if company_count > 0 and payment_count == 0:
            print("❌ ISSUE: Company plans exist but Payment plans are missing!")
            print("💡 SOLUTION: Need to sync plans from companies to payments app")
        elif company_count == payment_count:
            print("✅ Plan counts match")
        else:
            print(f"⚠️  Plan count mismatch: Company={company_count}, Payment={payment_count}")
            
    except Exception as e:
        print(f"Error checking sync status: {e}")

if __name__ == "__main__":
    main()