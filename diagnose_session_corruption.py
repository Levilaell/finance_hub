#!/usr/bin/env python3
"""
Comprehensive session corruption and authentication diagnostics for production
"""

import requests
import json
import sys
from datetime import datetime
import time

# Production URL
PRODUCTION_API = 'https://caixahub.com.br'
API_BASE = f'{PRODUCTION_API}/api'

def analyze_session_behavior():
    """Test session behavior and corruption patterns"""
    print("🔍 Testing Production Session Behavior")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/139.0.0.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    })
    
    # Test 1: Multiple rapid login attempts (like in logs)
    print("\n📊 Test 1: Multiple Rapid Login Attempts")
    print("-" * 40)
    
    test_credentials = {
        'email': 'test-diagnostics@example.com',  # Non-existent for testing
        'password': 'invalid'
    }
    
    for attempt in range(5):
        print(f"Attempt {attempt + 1}/5...", end='', flush=True)
        try:
            response = session.post(f'{API_BASE}/auth/login/', 
                                  json=test_credentials, 
                                  timeout=10)
            
            print(f" Status: {response.status_code}")
            
            # Check for specific error messages
            if response.status_code == 401:
                try:
                    error_data = response.json()
                    if 'token' in str(error_data).lower():
                        print(f"  ⚠️  Token-related error: {error_data}")
                except:
                    pass
            
            # Check session cookies
            session_cookies = [cookie for cookie in session.cookies if 'session' in cookie.name.lower()]
            if session_cookies:
                print(f"  🍪 Session cookies: {len(session_cookies)}")
            
            time.sleep(1)  # Small delay between attempts
            
        except requests.exceptions.RequestException as e:
            print(f" ❌ Error: {e}")
        
    # Test 2: CSRF Token Behavior
    print(f"\n📊 Test 2: CSRF Token Behavior")
    print("-" * 40)
    
    try:
        # Get CSRF token
        response = session.get(f'{API_BASE}/auth/csrf/')
        print(f"CSRF endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            csrf_data = response.json()
            csrf_token = csrf_data.get('csrfToken', '')
            print(f"CSRF token length: {len(csrf_token)}")
            
            # Try login with CSRF
            session.headers.update({'X-CSRFToken': csrf_token})
            
    except requests.exceptions.RequestException as e:
        print(f"CSRF test failed: {e}")
    
    # Test 3: Session Persistence
    print(f"\n📊 Test 3: Session Persistence")  
    print("-" * 40)
    
    # Make multiple requests to see if session persists
    for i in range(3):
        try:
            response = session.get(f'{API_BASE}/auth/profile/', timeout=5)
            print(f"Profile request {i+1}: {response.status_code}")
            
            if response.status_code == 200:
                print("  ✅ Session persistent")
            elif response.status_code == 401:
                print("  ❌ Session lost/expired")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Request failed: {e}")
    
    # Test 4: Cookie Analysis
    print(f"\n📊 Test 4: Cookie Analysis")
    print("-" * 40)
    
    all_cookies = list(session.cookies)
    print(f"Total cookies: {len(all_cookies)}")
    
    for cookie in all_cookies:
        print(f"  🍪 {cookie.name}: domain={cookie.domain}, secure={cookie.secure}, path={cookie.path}")
        
        # Check for signed cookie format (production uses signed_cookies)
        if 'session' in cookie.name.lower() and cookie.value:
            cookie_parts = cookie.value.count(':')
            print(f"    Cookie format: {cookie_parts} colons (signed cookies should have multiple parts)")

def test_auth_flow_with_timing():
    """Test complete auth flow with detailed timing"""
    print("\n🚀 Complete Auth Flow Test")
    print("=" * 60)
    
    session = requests.Session()
    timings = {}
    
    # Step 1: Health check
    start_time = time.time()
    try:
        response = session.get(f'{PRODUCTION_API}/health/', timeout=10)
        timings['health_check'] = time.time() - start_time
        print(f"Health check: {response.status_code} ({timings['health_check']:.2f}s)")
    except Exception as e:
        print(f"Health check failed: {e}")
    
    # Step 2: Options preflight for login
    start_time = time.time()
    try:
        response = session.options(f'{API_BASE}/auth/login/', timeout=10)
        timings['options_login'] = time.time() - start_time
        print(f"OPTIONS /auth/login/: {response.status_code} ({timings['options_login']:.2f}s)")
    except Exception as e:
        print(f"OPTIONS failed: {e}")
    
    # Step 3: Actual login attempt (invalid credentials)
    start_time = time.time()
    try:
        response = session.post(f'{API_BASE}/auth/login/', 
                              json={'email': 'nonexistent@test.com', 'password': 'invalid'},
                              timeout=10)
        timings['login_attempt'] = time.time() - start_time
        print(f"Login attempt: {response.status_code} ({timings['login_attempt']:.2f}s)")
        
        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"  Error: {error_data}")
            except:
                print(f"  Raw response: {response.text[:200]}")
                
    except Exception as e:
        print(f"Login failed: {e}")
    
    print(f"\nTiming Summary:")
    for step, duration in timings.items():
        status = "⚠️" if duration > 2.0 else "✅"
        print(f"  {status} {step}: {duration:.2f}s")

def check_cors_and_headers():
    """Check CORS configuration and security headers"""
    print("\n🔒 CORS and Security Headers Test")
    print("=" * 60)
    
    # Test from different origins
    test_origins = [
        'https://caixahub.com.br',
        'https://www.caixahub.com.br', 
        'http://localhost:3000',
        'https://malicious-site.com'
    ]
    
    for origin in test_origins:
        print(f"\nTesting from origin: {origin}")
        try:
            headers = {
                'Origin': origin,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'content-type,authorization'
            }
            
            response = requests.options(f'{API_BASE}/auth/login/', 
                                      headers=headers, 
                                      timeout=5)
            
            print(f"  Status: {response.status_code}")
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
            }
            
            for header, value in cors_headers.items():
                if value:
                    print(f"  {header}: {value}")
                    
        except Exception as e:
            print(f"  ❌ Failed: {e}")

def main():
    print("🚨 PRODUCTION SESSION CORRUPTION DIAGNOSTICS")
    print("=" * 80)
    print(f"Target: {PRODUCTION_API}")
    print(f"Timestamp: {datetime.now()}")
    print("=" * 80)
    
    try:
        # Test basic connectivity first
        print("🌐 Testing basic connectivity...")
        response = requests.get(f'{PRODUCTION_API}/health/', timeout=10)
        print(f"Health check: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Basic connectivity failed. Aborting tests.")
            return
            
        # Run diagnostic tests
        analyze_session_behavior()
        test_auth_flow_with_timing()
        check_cors_and_headers()
        
        print("\n✅ DIAGNOSTICS COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()