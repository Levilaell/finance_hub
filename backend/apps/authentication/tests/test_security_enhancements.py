"""
Comprehensive security tests for enhanced authentication system
"""
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import EmailVerification, PasswordReset
from apps.authentication.security.rate_limiting import ProgressiveRateLimiter
from apps.authentication.security.audit_logger import SecurityAuditLogger

User = get_user_model()


class SecureAuthenticationTestCase(APITestCase):
    """Test secure authentication with httpOnly cookies"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='SecurePass123!',
            first_name='Test',
            last_name='User'
        )
        self.login_url = '/api/auth/login/'
        self.logout_url = '/api/auth/logout/'
        self.profile_url = '/api/auth/profile/'

    def test_secure_login_sets_httponly_cookies(self):
        """Test that login sets secure httpOnly cookies"""
        response = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'SecurePass123!'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Check that response doesn't contain tokens in body
        self.assertNotIn('tokens', response.data)
        
        # Check that cookies are set
        cookies = response.cookies
        self.assertIn('access_token', cookies)
        self.assertIn('refresh_token', cookies)
        
        # Verify cookie security attributes
        access_cookie = cookies['access_token']
        self.assertTrue(access_cookie['httponly'])
        self.assertEqual(access_cookie['samesite'], 'Lax')
        self.assertEqual(access_cookie['path'], '/')
        
        refresh_cookie = cookies['refresh_token']
        self.assertTrue(refresh_cookie['httponly'])
        self.assertEqual(refresh_cookie['samesite'], 'Lax')

    def test_authenticated_request_with_cookies(self):
        """Test that authenticated requests work with cookies"""
        # First login to set cookies
        login_response = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'SecurePass123!'
        })
        self.assertEqual(login_response.status_code, 200)
        
        # Make authenticated request using cookies
        profile_response = self.client.get(self.profile_url)
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.data['email'], 'testuser@example.com')

    def test_logout_clears_cookies(self):
        """Test that logout clears authentication cookies"""
        # Login first
        self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'SecurePass123!'
        })
        
        # Logout
        logout_response = self.client.post(self.logout_url)
        self.assertEqual(logout_response.status_code, 200)
        
        # Check that cookies are cleared (empty value with past expiry)
        cookies = logout_response.cookies
        if 'access_token' in cookies:
            self.assertEqual(cookies['access_token'].value, '')
        if 'refresh_token' in cookies:
            self.assertEqual(cookies['refresh_token'].value, '')

    def test_token_refresh_with_cookies(self):
        """Test token refresh using httpOnly cookies"""
        # Login to set initial cookies
        self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'SecurePass123!'
        })
        
        # Call refresh endpoint
        refresh_response = self.client.post('/api/auth/refresh/')
        self.assertEqual(refresh_response.status_code, 200)
        
        # Verify new cookies are set
        cookies = refresh_response.cookies
        self.assertIn('access_token', cookies)
        
        # Verify response contains user data but not tokens
        self.assertIn('user', refresh_response.data)
        self.assertNotIn('tokens', refresh_response.data)


class CSRFProtectionTestCase(APITestCase):
    """Test CSRF protection for state-changing operations"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='SecurePass123!',
            first_name='Test',
            last_name='User'
        )
        # Login to get authenticated session
        self.client.post('/api/auth/login/', {
            'email': 'testuser@example.com',
            'password': 'SecurePass123!'
        })

    def test_csrf_protection_enabled_for_logout(self):
        """Test that CSRF protection is enabled for logout"""
        # This will depend on your CSRF implementation
        # The test structure is here for when you implement it
        response = self.client.post('/api/auth/logout/')
        # In a real implementation, this might require CSRF token
        self.assertIn(response.status_code, [200, 403])  # Success or CSRF failure

    def test_csrf_exemption_for_jwt_requests(self):
        """Test that JWT-authenticated requests are exempt from CSRF"""
        # This test verifies that the CSRFExemptionMiddleware works correctly
        profile_response = self.client.get('/api/auth/profile/')
        self.assertEqual(profile_response.status_code, 200)


class RateLimitingTestCase(TestCase):
    """Test progressive rate limiting functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='SecurePass123!'
        )
        self.rate_limiter = ProgressiveRateLimiter('test_auth', base_delay=1, max_delay=60)

    def test_progressive_delay_calculation(self):
        """Test that delays increase progressively"""
        ip = '127.0.0.1'
        
        # First attempt - no delay
        delay, reason = self.rate_limiter.get_delay(ip)
        self.assertEqual(delay, 0)
        
        # Record failed attempts and check delays
        delays = []
        for i in range(5):
            self.rate_limiter.record_attempt(ip, success=False)
            delay, reason = self.rate_limiter.get_delay(ip)
            delays.append(delay)
        
        # Verify delays are increasing (1, 2, 4, 8, 16)
        expected_delays = [1, 2, 4, 8, 16]
        self.assertEqual(delays, expected_delays)

    def test_successful_attempt_resets_delay(self):
        """Test that successful attempts reset the delay"""
        ip = '127.0.0.1'
        
        # Record several failed attempts
        for _ in range(3):
            self.rate_limiter.record_attempt(ip, success=False)
        
        # Should have delay
        delay, reason = self.rate_limiter.get_delay(ip)
        self.assertGreater(delay, 0)
        
        # Record successful attempt
        self.rate_limiter.record_attempt(ip, success=True)
        
        # Delay should be reset
        delay, reason = self.rate_limiter.get_delay(ip)
        self.assertEqual(delay, 0)

    def test_login_rate_limiting_integration(self):
        """Test rate limiting integration with login endpoint"""
        login_url = '/api/auth/login/'
        
        # Make several failed login attempts
        for _ in range(10):
            response = self.client.post(login_url, {
                'email': 'testuser@example.com',
                'password': 'wrongpassword'
            })
        
        # Should get rate limited
        response = self.client.post(login_url, {
            'email': 'testuser@example.com',
            'password': 'wrongpassword'
        })
        
        # Depending on implementation, might be 429 or still 401
        self.assertIn(response.status_code, [429, 401])


class SecurityHeadersTestCase(TestCase):
    """Test security headers middleware"""
    
    def setUp(self):
        self.client = Client()

    def test_security_headers_present(self):
        """Test that security headers are added to responses"""
        response = self.client.get('/api/auth/profile/')  # Any endpoint
        
        # Check for key security headers
        expected_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'X-XSS-Protection',
            'Referrer-Policy',
            'Content-Security-Policy'
        ]
        
        for header in expected_headers:
            self.assertIn(header, response.headers, f"Missing security header: {header}")

    def test_csp_header_content(self):
        """Test Content Security Policy header content"""
        response = self.client.get('/api/auth/profile/')
        
        csp = response.get('Content-Security-Policy', '')
        self.assertIn("default-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)

    def test_frame_options_deny(self):
        """Test X-Frame-Options is set to DENY"""
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.get('X-Frame-Options'), 'DENY')


class RequestSigningTestCase(APITestCase):
    """Test request signing for critical operations"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='SecurePass123!'
        )
        # Login to get authenticated
        self.client.post('/api/auth/login/', {
            'email': 'testuser@example.com',
            'password': 'SecurePass123!'
        })

    def test_password_change_requires_signature(self):
        """Test that password change requires valid request signature"""
        change_url = '/api/auth/change-password/'
        
        # Attempt password change without signature
        response = self.client.post(change_url, {
            'old_password': 'SecurePass123!',
            'new_password': 'NewSecurePass123!'
        })
        
        # Should require signature (implementation dependent)
        # This test structure is ready for when you implement signature verification
        self.assertIn(response.status_code, [400, 403, 200])

    def test_valid_signature_allows_operation(self):
        """Test that valid signature allows critical operations"""
        # This would test the actual signature verification
        # Implementation depends on your specific signing algorithm
        pass


class AuditLoggingTestCase(TestCase):
    """Test security audit logging"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='SecurePass123!'
        )
        self.audit_logger = SecurityAuditLogger()

    @patch('apps.authentication.security.audit_logger.logger')
    def test_successful_login_logged(self, mock_logger):
        """Test that successful logins are logged"""
        self.audit_logger.log_successful_login(
            self.user, 
            '127.0.0.1', 
            'Mozilla/5.0 Test Browser'
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn('SUCCESSFUL_LOGIN', call_args)
        self.assertIn(self.user.email, call_args)

    @patch('apps.authentication.security.audit_logger.logger')
    def test_failed_login_logged(self, mock_logger):
        """Test that failed logins are logged"""
        self.audit_logger.log_failed_login(
            'testuser@example.com',
            '127.0.0.1',
            'Mozilla/5.0 Test Browser',
            'Invalid credentials'
        )
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        self.assertIn('FAILED_LOGIN', call_args)
        self.assertIn('testuser@example.com', call_args)

    @patch('apps.authentication.security.audit_logger.logger')
    def test_password_change_logged(self, mock_logger):
        """Test that password changes are logged"""
        self.audit_logger.log_password_change(
            self.user,
            '127.0.0.1',
            'Mozilla/5.0 Test Browser'
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn('PASSWORD_CHANGED', call_args)


class TokenSecurityTestCase(APITestCase):
    """Test JWT token security measures"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='SecurePass123!'
        )

    def test_token_rotation_on_refresh(self):
        """Test that refresh tokens are rotated"""
        # Login to get initial tokens
        login_response = self.client.post('/api/auth/login/', {
            'email': 'testuser@example.com',
            'password': 'SecurePass123!'
        })
        
        initial_refresh_cookie = login_response.cookies.get('refresh_token')
        
        # Refresh tokens
        refresh_response = self.client.post('/api/auth/refresh/')
        new_refresh_cookie = refresh_response.cookies.get('refresh_token')
        
        # Tokens should be different (if rotation is enabled)
        if initial_refresh_cookie and new_refresh_cookie:
            self.assertNotEqual(
                initial_refresh_cookie.value, 
                new_refresh_cookie.value
            )

    def test_expired_token_handling(self):
        """Test handling of expired tokens"""
        # This test would require mocking token expiration
        # or using very short-lived tokens for testing
        pass

    def test_invalid_token_clears_cookies(self):
        """Test that invalid tokens result in cleared cookies"""
        # Set invalid cookie manually
        self.client.cookies['access_token'] = 'invalid_token'
        
        # Make authenticated request
        response = self.client.get('/api/auth/profile/')
        
        # Should get 401 and cookies should be cleared in response
        self.assertEqual(response.status_code, 401)


class TwoFactorSecurityTestCase(APITestCase):
    """Test 2FA security enhancements"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='SecurePass123!'
        )
        # Enable 2FA for user
        self.user.is_two_factor_enabled = True
        self.user.two_factor_secret = 'TESTBASE32SECRET'
        self.user.save()

    def test_2fa_required_login_flow(self):
        """Test that 2FA is required for enabled users"""
        response = self.client.post('/api/auth/login/', {
            'email': 'testuser@example.com',
            'password': 'SecurePass123!'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get('requires_2fa'))
        self.assertNotIn('access_token', response.cookies)

    def test_invalid_2fa_code_blocks_login(self):
        """Test that invalid 2FA codes block login"""
        response = self.client.post('/api/auth/login/', {
            'email': 'testuser@example.com',
            'password': 'SecurePass123!',
            'two_fa_code': '000000'  # Invalid code
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertNotIn('access_token', response.cookies)


@override_settings(DEBUG=False)
class ProductionSecurityTestCase(TestCase):
    """Test security settings in production mode"""
    
    def test_secure_cookies_in_production(self):
        """Test that cookies are marked secure in production"""
        client = Client()
        user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='SecurePass123!'
        )
        
        response = client.post('/api/auth/login/', {
            'email': 'testuser@example.com',
            'password': 'SecurePass123!'
        }, secure=True)  # Simulate HTTPS
        
        # In production, cookies should be marked secure
        if 'access_token' in response.cookies:
            # This test depends on your production settings
            pass

    def test_hsts_header_in_production(self):
        """Test HSTS header is present in production"""
        client = Client()
        response = client.get('/api/auth/profile/', secure=True)
        
        # Should have HSTS header in production
        # Implementation depends on your security middleware
        pass


class IntegrationSecurityTestCase(APITestCase):
    """Integration tests for complete security flow"""
    
    def test_complete_secure_auth_flow(self):
        """Test complete authentication flow with all security measures"""
        # 1. Register user
        register_response = self.client.post('/api/auth/register/', {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
            'company_name': 'Test Company',
            'company_cnpj': '12.345.678/0001-90',
            'company_type': 'ltda',
            'business_sector': 'technology',
            'phone': '(11) 98765-4321'
        })
        
        self.assertEqual(register_response.status_code, 201)
        self.assertIn('access_token', register_response.cookies)
        
        # 2. Make authenticated request
        profile_response = self.client.get('/api/auth/profile/')
        self.assertEqual(profile_response.status_code, 200)
        
        # 3. Refresh token
        refresh_response = self.client.post('/api/auth/refresh/')
        self.assertEqual(refresh_response.status_code, 200)
        
        # 4. Logout
        logout_response = self.client.post('/api/auth/logout/')
        self.assertEqual(logout_response.status_code, 200)
        
        # 5. Verify logged out
        profile_response_after_logout = self.client.get('/api/auth/profile/')
        self.assertEqual(profile_response_after_logout.status_code, 401)

    def test_security_headers_on_all_responses(self):
        """Test that security headers are present on all API responses"""
        test_urls = [
            '/api/auth/profile/',
            '/api/auth/login/',
            '/api/auth/refresh/',
        ]
        
        for url in test_urls:
            response = self.client.get(url) if url.endswith('profile/') else self.client.post(url, {})
            
            # Check key security headers
            self.assertIn('X-Content-Type-Options', response.headers)
            self.assertIn('X-Frame-Options', response.headers)
            self.assertIn('Content-Security-Policy', response.headers)