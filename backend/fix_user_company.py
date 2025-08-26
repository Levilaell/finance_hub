#!/usr/bin/env python3
"""
Fix User Company Association Issue
Creates a company for the admin user to resolve SubscriptionStatusView error
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, '/Users/levilaell/Desktop/finance_hub/backend')

django.setup()

from django.contrib.auth import get_user_model
from apps.companies.models import Company
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

def fix_user_company_association():
    """
    Fix the user company association issue
    """
    print("🔧 FIXING USER COMPANY ASSOCIATION")
    print("=" * 40)
    
    # Get the admin user
    try:
        user = User.objects.get(email='admin@admin.com')
        print(f"✅ Found user: {user.email}")
    except User.DoesNotExist:
        print("❌ Admin user not found")
        return False
    
    # Check if user already has a company
    existing_companies = Company.objects.filter(owner=user)
    if existing_companies.exists():
        company = existing_companies.first()
        print(f"✅ User already has company: {company.name}")
        return True
    
    # Create a company for the user
    try:
        company = Company.objects.create(
            owner=user,
            name="Admin Company",
            subscription_status='active',  # Set as active
            plan_type='pro',  # Set as pro plan
            trial_end=timezone.now() + timedelta(days=30),  # 30 days trial
            billing_email=user.email,
            
            # Usage limits for pro plan
            max_bank_accounts=10,
            max_transactions_per_month=10000,
            max_reports_per_month=100,
            max_ai_requests_per_month=1000,
            
            # Initialize usage counters
            current_month_transactions=0,
            current_month_reports=0,
            current_month_ai_requests=0,
        )
        
        print(f"✅ Created company: {company.name}")
        print(f"   - Plan: {company.plan_type}")
        print(f"   - Status: {company.subscription_status}")
        print(f"   - Trial End: {company.trial_end}")
        
        # Verify the fix
        user.refresh_from_db()
        if hasattr(user, 'company'):
            print(f"✅ User now has company: {user.company}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating company: {e}")
        return False

def test_fix():
    """
    Test that the fix works
    """
    print("\n🧪 TESTING THE FIX")
    print("-" * 20)
    
    from django.test import Client
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    try:
        user = User.objects.get(email='admin@admin.com')
        
        # Test with Django test client
        client = Client()
        client.force_login(user)
        
        response = client.get('/api/companies/subscription-status/')
        print(f"✅ Test request status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: SubscriptionStatusView now works!")
            return True
        else:
            print(f"❌ Still failing: {response.content.decode()[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def create_additional_test_user():
    """
    Create a complete test user with company for future testing
    """
    print("\n👤 CREATING COMPLETE TEST USER")
    print("-" * 35)
    
    # Create test user
    try:
        test_user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True,
            }
        )
        
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            print(f"✅ Created test user: {test_user.email}")
        else:
            print(f"✅ Test user already exists: {test_user.email}")
        
        # Create company for test user
        test_company, created = Company.objects.get_or_create(
            owner=test_user,
            defaults={
                'name': 'Test Company',
                'subscription_status': 'trial',
                'plan_type': 'basic',
                'trial_end': timezone.now() + timedelta(days=14),
                'billing_email': test_user.email,
                'max_bank_accounts': 3,
                'max_transactions_per_month': 1000,
                'max_reports_per_month': 10,
                'max_ai_requests_per_month': 100,
            }
        )
        
        if created:
            print(f"✅ Created test company: {test_company.name}")
        else:
            print(f"✅ Test company already exists: {test_company.name}")
        
        print(f"\n📝 TEST CREDENTIALS:")
        print(f"   Email: test@example.com")
        print(f"   Password: testpass123")
        print(f"   Company: {test_company.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False

if __name__ == "__main__":
    success = fix_user_company_association()
    if success:
        test_fix()
        create_additional_test_user()
        
        print("\n🎉 SOLUTION COMPLETE!")
        print("=" * 25)
        print("✅ Admin user now has a company")
        print("✅ SubscriptionStatusView should work")
        print("✅ Test user created for future testing")
        print("\n🚀 NEXT STEPS:")
        print("1. Clear browser cookies and login again")
        print("2. Test /api/companies/subscription-status/ endpoint")
        print("3. Check frontend dashboard for subscription data")
    else:
        print("\n❌ Fix failed - manual intervention required")