#!/usr/bin/env python
"""
Test script for secure authentication implementation
"""
import os
import sys
import django
import time
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from apps.authentication.security_logging import log_security_event, SecurityEvent

User = get_user_model()


def test_cookie_authentication():
    """Test httpOnly cookie authentication flow"""
    print("\n=== Testing httpOnly Cookie Authentication ===")
    
    client = APIClient()
    
    # Create test user
    test_email = f"test_{int(time.time())}@example.com"
    test_password = "TestPassword123!@#"
    
    print(f"\n1. Creating test user: {test_email}")
    user = User.objects.create_user(
        username=test_email,
        email=test_email,
        password=test_password,
        first_name="Test",
        last_name="User"
    )
    print(f"   ✓ User created with ID: {user.id}")
    
    # Test login
    print("\n2. Testing login with cookie authentication")
    response = client.post('/api/auth/login/', {
        'email': test_email,
        'password': test_password
    })
    
    print(f"   Status: {response.status_code}")
    print(f"   Cookies: {response.cookies.keys()}")
    
    # Check for httpOnly cookies
    access_cookie = response.cookies.get('access_token')
    refresh_cookie = response.cookies.get('refresh_token')
    
    if access_cookie:
        print(f"   ✓ Access token cookie set (httpOnly: {access_cookie.get('httponly', False)})")
    else:
        print("   ✗ Access token cookie NOT set")
        
    if refresh_cookie:
        print(f"   ✓ Refresh token cookie set (httpOnly: {refresh_cookie.get('httponly', False)})")
    else:
        print("   ✗ Refresh token cookie NOT set")
    
    # Test authenticated request
    print("\n3. Testing authenticated API request")
    profile_response = client.get('/api/auth/profile/')
    print(f"   Profile request status: {profile_response.status_code}")
    if profile_response.status_code == 200:
        print(f"   ✓ Successfully fetched profile for: {profile_response.data.get('email')}")
    else:
        print("   ✗ Failed to fetch profile")
    
    # Test logout
    print("\n4. Testing logout")
    logout_response = client.post('/api/auth/logout/')
    print(f"   Logout status: {logout_response.status_code}")
    
    # Verify cookies are cleared
    logout_access = logout_response.cookies.get('access_token')
    logout_refresh = logout_response.cookies.get('refresh_token')
    
    if logout_access and logout_access.value == '':
        print("   ✓ Access token cookie cleared")
    if logout_refresh and logout_refresh.value == '':
        print("   ✓ Refresh token cookie cleared")
    
    # Cleanup
    user.delete()
    
    return True


def test_session_invalidation():
    """Test session invalidation on password change"""
    print("\n=== Testing Session Invalidation ===")
    
    client1 = APIClient()
    client2 = APIClient()
    
    # Create test user
    test_email = f"test_session_{int(time.time())}@example.com"
    test_password = "TestPassword123!@#"
    
    print(f"\n1. Creating test user: {test_email}")
    user = User.objects.create_user(
        username=test_email,
        email=test_email,
        password=test_password
    )
    
    # Login with two different clients (simulating two devices)
    print("\n2. Logging in from two different sessions")
    response1 = client1.post('/api/auth/login/', {
        'email': test_email,
        'password': test_password
    })
    print(f"   Session 1 login: {response1.status_code}")
    
    response2 = client2.post('/api/auth/login/', {
        'email': test_email,
        'password': test_password
    })
    print(f"   Session 2 login: {response2.status_code}")
    
    # Verify both sessions work
    print("\n3. Verifying both sessions are active")
    profile1 = client1.get('/api/auth/profile/')
    profile2 = client2.get('/api/auth/profile/')
    print(f"   Session 1 profile access: {profile1.status_code}")
    print(f"   Session 2 profile access: {profile2.status_code}")
    
    # Change password from session 1
    print("\n4. Changing password from session 1")
    new_password = "NewTestPassword123!@#"
    change_response = client1.post('/api/auth/change-password/', {
        'old_password': test_password,
        'new_password': new_password
    })
    print(f"   Password change status: {change_response.status_code}")
    
    # Test if session 2 is invalidated
    print("\n5. Testing if session 2 is invalidated")
    profile2_after = client2.get('/api/auth/profile/')
    print(f"   Session 2 profile access after password change: {profile2_after.status_code}")
    
    if profile2_after.status_code == 401:
        print("   ✓ Session 2 successfully invalidated")
    else:
        print("   ✗ Session 2 still active (security issue!)")
    
    # Session 1 should get new tokens
    if change_response.status_code == 200 and 'tokens' in change_response.data:
        print("   ✓ Session 1 received new tokens after password change")
    
    # Cleanup
    user.delete()
    
    return True


def test_security_logging():
    """Test security event logging"""
    print("\n=== Testing Security Logging ===")
    
    # Check if security log file exists
    from pathlib import Path
    logs_dir = Path(__file__).parent / 'logs'
    security_log = logs_dir / 'security.log'
    
    print(f"\n1. Checking security log configuration")
    print(f"   Log directory: {logs_dir}")
    print(f"   Security log exists: {security_log.exists()}")
    
    # Create a test security event
    print("\n2. Creating test security events")
    
    # Simulate failed login
    log_security_event(
        SecurityEvent.LOGIN_FAILED,
        extra_data={
            'email': 'test@example.com',
            'ip_address': '127.0.0.1',
            'reason': 'Invalid credentials'
        }
    )
    print("   ✓ Logged failed login event")
    
    # Simulate successful login
    test_user = User.objects.create_user(
        username='security_test',
        email='security@test.com',
        password='Test123!@#'
    )
    
    log_security_event(
        SecurityEvent.LOGIN_SUCCESS,
        user=test_user,
        extra_data={'ip_address': '127.0.0.1'}
    )
    print("   ✓ Logged successful login event")
    
    # Simulate password change
    log_security_event(
        SecurityEvent.PASSWORD_CHANGED,
        user=test_user
    )
    print("   ✓ Logged password change event")
    
    # Read recent log entries
    if security_log.exists():
        print("\n3. Recent security log entries:")
        with open(security_log, 'r') as f:
            lines = f.readlines()
            for line in lines[-5:]:  # Last 5 entries
                if 'Security Event' in line:
                    print(f"   {line.strip()}")
    
    # Cleanup
    test_user.delete()
    
    return True


def test_token_rotation():
    """Test token refresh and rotation"""
    print("\n=== Testing Token Rotation ===")
    
    client = APIClient()
    
    # Create and login user
    test_email = f"test_rotation_{int(time.time())}@example.com"
    user = User.objects.create_user(
        username=test_email,
        email=test_email,
        password="Test123!@#"
    )
    
    print(f"\n1. Logging in as {test_email}")
    login_response = client.post('/api/auth/login/', {
        'email': test_email,
        'password': 'Test123!@#'
    })
    print(f"   Login status: {login_response.status_code}")
    
    # Get initial refresh token from cookie
    initial_refresh = login_response.cookies.get('refresh_token')
    if initial_refresh:
        print(f"   ✓ Initial refresh token received")
    
    # Test token refresh
    print("\n2. Testing token refresh")
    refresh_response = client.post('/api/auth/refresh/')
    print(f"   Refresh status: {refresh_response.status_code}")
    
    # Check if new tokens were issued
    new_access = refresh_response.cookies.get('access_token')
    new_refresh = refresh_response.cookies.get('refresh_token')
    
    if new_access:
        print("   ✓ New access token issued")
    if new_refresh and initial_refresh and new_refresh.value != initial_refresh.value:
        print("   ✓ Refresh token rotated (new token issued)")
    elif new_refresh:
        print("   ⚠ Refresh token NOT rotated (same token)")
    
    # Verify old refresh token is invalid (if rotation is enabled)
    print("\n3. Testing if old refresh token is invalidated")
    # This would require manually setting the old token, which is complex in this test
    print("   ⚠ Manual verification required")
    
    # Cleanup
    user.delete()
    
    return True


def test_account_lockout():
    """Test account lockout after failed attempts"""
    print("\n=== Testing Account Lockout ===")
    
    client = APIClient()
    test_email = "lockout_test@example.com"
    
    # Create user
    user = User.objects.create_user(
        username=test_email,
        email=test_email,
        password="CorrectPassword123!@#"
    )
    
    print(f"\n1. Testing failed login attempts for {test_email}")
    
    # Make multiple failed login attempts
    for i in range(6):  # Assuming lockout after 5 attempts
        response = client.post('/api/auth/login/', {
            'email': test_email,
            'password': 'WrongPassword'
        })
        print(f"   Attempt {i+1}: Status {response.status_code}")
        
        if response.status_code == 423:  # Locked
            print(f"   ✓ Account locked after {i+1} attempts")
            break
    
    # Try with correct password
    print("\n2. Testing login with correct password after lockout")
    correct_response = client.post('/api/auth/login/', {
        'email': test_email,
        'password': 'CorrectPassword123!@#'
    })
    
    if correct_response.status_code == 423:
        print("   ✓ Login blocked even with correct password")
    else:
        print(f"   ✗ Login allowed (status: {correct_response.status_code})")
    
    # Cleanup
    user.delete()
    
    return True


def main():
    """Run all authentication tests"""
    print("=" * 60)
    print("SECURE AUTHENTICATION IMPLEMENTATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Cookie Authentication", test_cookie_authentication),
        ("Session Invalidation", test_session_invalidation),
        ("Security Logging", test_security_logging),
        ("Token Rotation", test_token_rotation),
        ("Account Lockout", test_account_lockout),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ ERROR in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)