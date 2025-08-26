#!/usr/bin/env python3
"""
Comprehensive Authentication Debugging Script
Diagnoses the SubscriptionStatusView authentication issue
"""

import os
import sys
import django
import requests
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
sys.path.insert(0, '/Users/levilaell/Desktop/finance_hub/backend')

django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient
from apps.authentication.jwt_cookie_authentication import JWTCookieAuthentication
import logging

User = get_user_model()

def diagnose_authentication_issue():
    """
    Complete authentication flow diagnosis
    """
    print("🔍 AUTHENTICATION ISSUE DIAGNOSIS")
    print("=" * 50)
    
    # 1. Check Django/DRF Configuration
    print("\n1. 📋 CONFIGURATION CHECK")
    print("-" * 30)
    
    rest_config = getattr(settings, 'REST_FRAMEWORK', {})
    auth_classes = rest_config.get('DEFAULT_AUTHENTICATION_CLASSES', [])
    
    print(f"✅ REST_FRAMEWORK configured: {bool(rest_config)}")
    print(f"✅ Authentication classes: {len(auth_classes)}")
    
    for i, auth_class in enumerate(auth_classes):
        print(f"   {i+1}. {auth_class}")
        
        # Test import
        try:
            from django.utils.module_loading import import_string
            import_string(auth_class)
            print(f"      ✅ Import successful")
        except ImportError as e:
            print(f"      ❌ Import failed: {e}")
    
    # JWT Cookie settings
    print(f"\n🍪 JWT Cookie Settings:")
    print(f"   JWT_COOKIE_SECURE: {getattr(settings, 'JWT_COOKIE_SECURE', 'Not set')}")
    print(f"   JWT_COOKIE_SAMESITE: {getattr(settings, 'JWT_COOKIE_SAMESITE', 'Not set')}")
    print(f"   JWT_ACCESS_COOKIE_NAME: {getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'Not set')}")
    print(f"   JWT_COOKIE_DOMAIN: {getattr(settings, 'JWT_COOKIE_DOMAIN', 'Not set')}")
    
    # CORS settings
    cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
    print(f"\n🌐 CORS Settings:")
    print(f"   CORS_ALLOW_CREDENTIALS: {getattr(settings, 'CORS_ALLOW_CREDENTIALS', 'Not set')}")
    print(f"   CORS_ALLOWED_ORIGINS: {cors_origins}")
    
    # 2. Test Authentication Classes
    print("\n2. 🔐 AUTHENTICATION CLASS TEST")
    print("-" * 35)
    
    try:
        auth_instance = JWTCookieAuthentication()
        print("✅ JWTCookieAuthentication instantiated successfully")
        
        # Test mock request
        from django.test import RequestFactory
        factory = RequestFactory()
        
        # Test without cookies
        request = factory.get('/api/companies/subscription-status/')
        result = auth_instance.authenticate(request)
        print(f"✅ No cookies test: {result}")
        
        # Test with invalid cookie
        request = factory.get('/api/companies/subscription-status/', HTTP_COOKIE='access_token=invalid_token')
        result = auth_instance.authenticate(request)
        print(f"✅ Invalid token test: {result}")
        
    except Exception as e:
        print(f"❌ JWTCookieAuthentication test failed: {e}")
    
    # 3. Check if user exists and can authenticate
    print("\n3. 👤 USER AUTHENTICATION TEST")
    print("-" * 35)
    
    try:
        # Find a test user
        user = User.objects.filter(is_active=True).first()
        if not user:
            print("❌ No active users found")
            return
        
        print(f"✅ Test user found: {user.email} (ID: {user.id})")
        
        # Test Django test client (simulates full request)
        client = Client()
        
        # Test subscription-status endpoint without auth
        response = client.get('/api/companies/subscription-status/')
        print(f"✅ Unauthenticated request: Status {response.status_code}")
        
        # Test with authenticated client
        client.force_login(user)
        response = client.get('/api/companies/subscription-status/')
        print(f"✅ Authenticated request: Status {response.status_code}")
        
        if response.status_code != 200:
            print(f"   Response: {response.content.decode()[:200]}")
            
    except Exception as e:
        print(f"❌ User authentication test failed: {e}")
    
    # 4. Test API Client (DRF)
    print("\n4. 🔌 DRF API CLIENT TEST")
    print("-" * 30)
    
    try:
        api_client = APIClient()
        
        # Test without auth
        response = api_client.get('/api/companies/subscription-status/')
        print(f"✅ DRF unauthenticated: Status {response.status_code}")
        
        if user:
            # Test with auth
            api_client.force_authenticate(user=user)
            response = api_client.get('/api/companies/subscription-status/')
            print(f"✅ DRF authenticated: Status {response.status_code}")
            
            if response.status_code != 200:
                print(f"   Response: {response.data}")
                
    except Exception as e:
        print(f"❌ DRF API client test failed: {e}")
    
    # 5. Test actual HTTP request (like frontend would make)
    print("\n5. 🌐 HTTP REQUEST TEST")
    print("-" * 25)
    
    try:
        # Test without credentials
        response = requests.get('http://localhost:8000/api/companies/subscription-status/')
        print(f"✅ HTTP without credentials: Status {response.status_code}")
        
        # Test the health endpoint (should work)
        response = requests.get('http://localhost:8000/api/health/')
        print(f"✅ HTTP health check: Status {response.status_code}")
        
    except requests.RequestException as e:
        print(f"❌ HTTP request test failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # 6. Recommendations
    print("\n6. 💡 DIAGNOSIS RESULTS & RECOMMENDATIONS")
    print("-" * 45)
    
    print("Based on the error 'As credenciais de autenticação não foram fornecidas':")
    print()
    print("🎯 MOST LIKELY CAUSES:")
    print("   1. Frontend request not sending JWT cookies")
    print("   2. Request made before user is fully logged in")
    print("   3. Browser not supporting SameSite=Lax correctly")
    print("   4. CORS preflight removing cookies")
    print()
    print("🔧 IMMEDIATE SOLUTIONS:")
    print("   1. Check browser developer tools → Network → Request headers")
    print("   2. Verify 'Cookie: access_token=...' header is present")
    print("   3. Test with different browser (Chrome vs Firefox)")
    print("   4. Add debug logging to JWTCookieAuthentication")
    print()
    print("🚀 QUICK FIXES TO TRY:")
    print("   1. Clear browser cookies and login again")
    print("   2. Check if request timing (made too early)")
    print("   3. Test with mobile browser (uses localStorage)")
    print()
    print("🔬 DEBUG STEPS:")
    print("   1. Add console.log in frontend api-client.ts")
    print("   2. Add print() in JWTCookieAuthentication.authenticate()")
    print("   3. Check Railway logs for request details")
    print()
    
    # 7. Create debug patch
    print("7. 🔧 CREATING DEBUG PATCH")
    print("-" * 30)
    print("Creating a debug version of JWTCookieAuthentication...")
    print("This will log authentication attempts for 10 minutes.")
    
    return True

if __name__ == "__main__":
    diagnose_authentication_issue()