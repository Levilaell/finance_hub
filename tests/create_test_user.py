#!/usr/bin/env python3
import os
import sys
import django

# Add backend to path
sys.path.insert(0, '/Users/levilaell/Desktop/finance_management/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from apps.authentication.models import User
from apps.companies.models import Company, SubscriptionPlan

# Create test user
email = 'test@example.com'
password = 'test123'

# Delete if exists
User.objects.filter(email=email).delete()

# Create new user
user = User.objects.create_user(
    username=email,  # Use email as username
    email=email,
    password=password,
    first_name='Test',
    last_name='User',
    phone='11999999999'
)

# Get the starter plan
starter_plan = SubscriptionPlan.objects.filter(name='Starter').first()
if not starter_plan:
    print("❌ No subscription plans found. Run: python manage.py create_subscription_plans")
    sys.exit(1)

# Create company for user
company = Company.objects.create(
    name='Test Company',
    cnpj='12345678901234',
    company_type='mei',
    business_sector='services',
    owner=user,  # Add owner
    subscription_plan=starter_plan  # Add subscription plan
)
# User is automatically linked through owner field

print(f"✅ User created: {email}")
print(f"✅ Password: {password}")
print(f"✅ Company: {company.name}")
print("\nUse these credentials to test the API!")