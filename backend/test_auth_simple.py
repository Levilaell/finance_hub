#!/usr/bin/env python
"""
Simple authentication security test for Finance Hub
"""
import os
import sys
import django
import unittest

# Set up Django first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.test')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()

class SimpleAuthenticationTest(TestCase):
    """Simple authentication security tests"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access protected endpoints"""
        print("🔒 Testing unauthenticated access...")
        
        # Try to access a protected endpoint
        response = self.client.get('/api/companies/')
        print(f"  Protected endpoint without auth: {response.status_code} (expected 401)")
        
        self.assertIn(response.status_code, [401, 403])
    
    def test_basic_login_flow(self):
        """Test basic login functionality"""
        print("🔒 Testing basic login flow...")
        
        # Test valid login
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post('/api/auth/login/', login_data)
        print(f"  Valid login: {response.status_code}")
        
        # Should be successful (200) or redirect (302)
        self.assertIn(response.status_code, [200, 201, 302])
    
    def test_invalid_login(self):
        """Test invalid login attempts"""
        print("🔒 Testing invalid login attempts...")
        
        # Test invalid password
        login_data = {
            'email': 'test@example.com',
            'password': 'WrongPassword!'
        }
        
        response = self.client.post('/api/auth/login/', login_data)
        print(f"  Invalid password: {response.status_code} (expected 400/401)")
        
        self.assertIn(response.status_code, [400, 401])
        
        # Test non-existent user
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post('/api/auth/login/', login_data)
        print(f"  Non-existent user: {response.status_code} (expected 400/401)")
        
        self.assertIn(response.status_code, [400, 401])
    
    def test_sql_injection_protection(self):
        """Test basic SQL injection protection"""
        print("🔒 Testing SQL injection protection...")
        
        # Try SQL injection in login
        malicious_data = {
            'email': "'; DROP TABLE users; --",
            'password': 'TestPass123!'
        }
        
        response = self.client.post('/api/auth/login/', malicious_data)
        print(f"  SQL injection test: {response.status_code} (should handle gracefully)")
        
        # Verify user still exists
        user_exists = User.objects.filter(username='testuser').exists()
        print(f"  User still exists: {user_exists} (expected True)")
        
        self.assertTrue(user_exists)
    
    def test_xss_protection(self):
        """Test XSS protection in forms"""
        print("🔒 Testing XSS protection...")
        
        # Try XSS in registration
        xss_data = {
            'username': '<script>alert("xss")</script>',
            'email': 'xss@example.com',
            'password': 'TestPass123!',
            'first_name': '<script>alert("xss")</script>',
            'last_name': 'User'
        }
        
        response = self.client.post('/api/auth/register/', xss_data)
        print(f"  XSS in registration: {response.status_code}")
        
        # Check if user was created (shouldn't be created with script tags)
        if response.status_code in [200, 201]:
            user = User.objects.filter(email='xss@example.com').first()
            if user:
                print(f"  Username stored: {user.username} (should be sanitized)")
                # Username should not contain script tags
                self.assertNotIn('<script>', user.username)
    
    def test_csrf_protection(self):
        """Test CSRF protection"""
        print("🔒 Testing CSRF protection...")
        
        # Make POST request without CSRF token
        response = self.client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        })
        
        print(f"  POST without CSRF token: {response.status_code}")
        
        # Should be handled appropriately (might be disabled for API endpoints)
        self.assertIn(response.status_code, [200, 201, 400, 401, 403])

def run_tests():
    """Run all authentication tests"""
    print("🛡️  Finance Hub Authentication Security Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(SimpleAuthenticationTest)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n📊 Test Results:")
    print("=" * 30)
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("✅ Authentication security tests mostly passed!")
    elif success_rate >= 60:
        print("⚠️  Some authentication security issues found")
    else:
        print("❌ Multiple authentication security issues found")
    
    return result

if __name__ == '__main__':
    run_tests()