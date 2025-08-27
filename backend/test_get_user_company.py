#!/usr/bin/env python
"""
Test get_user_company function locally to debug the issue
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.companies.models import Company

User = get_user_model()

def get_user_company(user):
    """
    Cópia exata da função do views.py
    """
    try:
        from apps.companies.models import Company
        return Company.objects.get(owner=user)
    except Company.DoesNotExist:
        return None
    except Company.MultipleObjectsReturned:
        # If user owns multiple companies, get the first one
        from apps.companies.models import Company
        return Company.objects.filter(owner=user).first()

def test_function():
    print("🧪 Testing get_user_company function")
    print("=" * 50)
    
    # Lista todos os users e companies
    print("\n📋 ALL USERS:")
    for user in User.objects.all()[:10]:  # Primeiros 10
        print(f"  User {user.id}: {user.email}")
    
    print("\n📋 ALL COMPANIES:")
    for company in Company.objects.all()[:10]:  # Primeiras 10
        print(f"  Company {company.id}: {company.name} (Owner: {company.owner.email})")
    
    # Verificar se existe algum user com email similar ao dos logs
    print("\n🔍 SEARCHING FOR SIMILAR EMAILS:")
    similar_emails = User.objects.filter(email__icontains="arabel")
    for user in similar_emails:
        print(f"  Found: {user.id} - {user.email}")
        
        company = get_user_company(user)
        if company:
            print(f"    Company: {company.id} - {company.name}")
        else:
            print(f"    No company found")
    
    # Test with a known user (if any)
    try:
        if User.objects.exists():
            test_user = User.objects.first()
            print(f"\n🧪 Testing with user: {test_user.email}")
            
            test_company = get_user_company(test_user)
            if test_company:
                print(f"  ✅ get_user_company returned: {test_company.id} - {test_company.name}")
            else:
                print(f"  ❌ get_user_company returned None")
                
                # Check if user has company via hasattr
                if hasattr(test_user, 'company'):
                    print(f"  🔍 user.company attribute exists")
                    if test_user.company:
                        print(f"     Company via attribute: {test_user.company.id} - {test_user.company.name}")
                    else:
                        print(f"     user.company is None")
                else:
                    print(f"  ❌ user.company attribute doesn't exist")
        else:
            print("❌ No users found in database")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_function()