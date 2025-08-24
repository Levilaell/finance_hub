#!/usr/bin/env python3
"""
Script de teste para verificar problemas de cookies em mobile Safari
Execute: python manage.py shell < test_mobile_cookies.py
"""

import os
import django
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

from django.conf import settings
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.authentication.cookie_middleware import _is_mobile_safari, set_jwt_cookies, set_mobile_compatible_cookies
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import HttpResponse

User = get_user_model()

def test_mobile_cookie_detection():
    """Test mobile Safari detection"""
    print("=== MOBILE SAFARI DETECTION TEST ===")
    
    test_user_agents = [
        # Mobile Safari (iOS 18.6)
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Mobile/15E148 Safari/604.1",
        
        # Desktop Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
        
        # Chrome Mobile
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/127.0.6533.107 Mobile/15E148 Safari/604.1",
        
        # Chrome Desktop
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    ]
    
    for ua in test_user_agents:
        is_mobile = _is_mobile_safari(ua)
        browser_name = "Mobile Safari" if "iPhone" in ua and "Safari" in ua and "Chrome" not in ua else \
                      "Desktop Safari" if "Safari" in ua and "Chrome" not in ua and "iPhone" not in ua else \
                      "Chrome Mobile" if "iPhone" in ua and "Chrome" in ua else \
                      "Chrome Desktop"
        
        print(f"{browser_name:<15}: {is_mobile} | UA: {ua[:60]}...")
    
    print()

def test_cookie_settings():
    """Test cookie configuration"""
    print("=== COOKIE SETTINGS TEST ===")
    
    # Create mock request with mobile Safari UA
    factory = RequestFactory()
    request = factory.get('/', HTTP_USER_AGENT="Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Mobile/15E148 Safari/604.1")
    request.META['HTTP_ORIGIN'] = 'https://caixahub.com.br'
    request.META['HTTP_HOST'] = 'financehub-production.up.railway.app'
    
    # Get first user for test
    try:
        user = User.objects.first()
        if not user:
            print("❌ No users found for testing")
            return
            
        print(f"Testing with user: {user.email}")
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        tokens = {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }
        
        print(f"Access token length: {len(tokens['access'])}")
        print(f"Refresh token length: {len(tokens['refresh'])}")
        
        # Test mobile cookie strategy
        response = HttpResponse()
        set_mobile_compatible_cookies(response, tokens, request, user)
        
        print("\n=== COOKIES SET ===")
        cookies_set = []
        for key, morsel in response.cookies.items():
            cookies_set.append({
                'name': key,
                'secure': morsel['secure'],
                'httponly': morsel['httponly'],
                'samesite': morsel['samesite'],
                'domain': morsel['domain'],
                'path': morsel['path'],
                'max_age': morsel['max-age']
            })
            print(f"Cookie: {key}")
            print(f"  Secure: {morsel['secure']}")
            print(f"  HttpOnly: {morsel['httponly']}")
            print(f"  SameSite: {morsel['samesite']}")
            print(f"  Domain: {morsel['domain']}")
            print(f"  Path: {morsel['path']}")
            print(f"  Max-Age: {morsel['max-age']}")
            print()
        
        print(f"Total cookies set: {len(cookies_set)}")
        
        # Test headers
        print("=== DEBUG HEADERS ===")
        for header, value in response.items():
            if header.startswith('X-'):
                print(f"{header}: {value}")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

def test_settings_validation():
    """Test settings configuration"""
    print("\n=== SETTINGS VALIDATION ===")
    
    print(f"DEBUG: {settings.DEBUG}")
    print(f"JWT_COOKIE_SECURE: {getattr(settings, 'JWT_COOKIE_SECURE', 'NOT SET')}")
    print(f"JWT_COOKIE_SAMESITE: {getattr(settings, 'JWT_COOKIE_SAMESITE', 'NOT SET')}")
    print(f"JWT_COOKIE_DOMAIN: {getattr(settings, 'JWT_COOKIE_DOMAIN', 'NOT SET')}")
    print(f"ADD_DEBUG_HEADERS: {getattr(settings, 'ADD_DEBUG_HEADERS', 'NOT SET')}")
    
    # Check JWT settings
    jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
    access_lifetime = jwt_settings.get('ACCESS_TOKEN_LIFETIME', timedelta(minutes=30))
    refresh_lifetime = jwt_settings.get('REFRESH_TOKEN_LIFETIME', timedelta(days=3))
    
    print(f"ACCESS_TOKEN_LIFETIME: {access_lifetime}")
    print(f"REFRESH_TOKEN_LIFETIME: {refresh_lifetime}")

if __name__ == "__main__":
    test_mobile_cookie_detection()
    test_cookie_settings()
    test_settings_validation()