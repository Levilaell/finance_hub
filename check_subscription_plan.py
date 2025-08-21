#!/usr/bin/env python
"""
Quick check for subscription plan issue
Run this in production to check if plan is configured correctly
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.contrib.auth import get_user_model
from apps.companies.models import SubscriptionPlan

User = get_user_model()

def check_subscription():
    print("🔍 CHECKING SUBSCRIPTION PLANS")
    print("=" * 40)
    
    # Check all plans in the system
    plans = SubscriptionPlan.objects.all()
    print(f"Total plans in system: {plans.count()}")
    
    for plan in plans:
        print(f"\n📋 Plan: {plan.name}")
        print(f"   Type: {plan.plan_type}")
        print(f"   Advanced Reports: {plan.has_advanced_reports}")
        print(f"   Active: {plan.is_active}")
    
    # Check your specific user
    email = "arabel.bebel@hotmail.com"
    
    try:
        user = User.objects.get(email=email)
        if hasattr(user, 'company') and user.company:
            company = user.company
            plan = company.subscription_plan
            
            print(f"\n👤 YOUR ACCOUNT:")
            print(f"   Email: {user.email}")
            print(f"   Company: {company.name}")
            print(f"   Subscription Status: {company.subscription_status}")
            
            if plan:
                print(f"   Plan: {plan.name}")
                print(f"   Plan Type: {plan.plan_type}")
                print(f"   ✅ has_advanced_reports: {plan.has_advanced_reports}")
                
                # Check if Professional plan should have advanced reports
                if plan.plan_type == 'professional' and not plan.has_advanced_reports:
                    print(f"   ⚠️  WARNING: Professional plan should have advanced_reports=True")
                    print(f"   🔧 SOLUTION: Update the plan to enable advanced reports")
            else:
                print(f"   ❌ No subscription plan assigned!")
        else:
            print(f"   ❌ User has no company")
            
    except User.DoesNotExist:
        print(f"❌ User {email} not found")

if __name__ == "__main__":
    check_subscription()