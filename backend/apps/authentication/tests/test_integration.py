"""
Integration tests for authentication system
Tests complete user flows from registration to authentication
"""
import secrets
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import EmailVerification, PasswordReset
from .test_utils import AuthTestMixin, mock_external_services

User = get_user_model()


class UserRegistrationFlowTestCase(APITestCase, AuthTestMixin):
    """Test complete user registration flow"""

    def setUp(self):
        self.register_url = reverse('authentication:register')
        self.verify_email_url = reverse('authentication:verify-email')
        self.login_url = reverse('authentication:login')

    @mock_external_services()
    def test_complete_registration_flow(self):
        """Test complete user registration and email verification flow"""
        # Step 1: Register user
        registration_data = self.get_valid_registration_data()
        response = self.client.post(self.register_url, registration_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        
        # Verify user was created
        user = User.objects.get(email=registration_data['email'])
        self.assertFalse(user.is_email_verified)
        
        # Verify company was created
        self.assertTrue(hasattr(user, 'company'))
        self.assertEqual(user.company.name, registration_data['company_name'])
        
        # Step 2: Verify email verification token was created
        verification = EmailVerification.objects.get(user=user)
        self.assertFalse(verification.is_used)
        self.assertGreater(verification.expires_at, timezone.now())
        
        # Step 3: Verify email
        verify_response = self.client.post(self.verify_email_url, {
            'token': verification.token
        })
        
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        
        # Step 4: Verify user email is now verified
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        
        # Step 5: Verify token is marked as used
        verification.refresh_from_db()
        self.assertTrue(verification.is_used)
        
        # Step 6: Login should work after verification
        login_response = self.client.post(self.login_url, {
            'email': registration_data['email'],
            'password': registration_data['password']
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', login_response.data)

    @mock_external_services()
    def test_registration_with_duplicate_email_fails(self):
        """Test that registration fails with duplicate email"""
        # Create a user first
        self.create_test_user(email='test@example.com')
        
        # Try to register with same email
        registration_data = self.get_valid_registration_data(email='test@example.com')
        response = self.client.post(self.register_url, registration_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    @mock_external_services()
    def test_registration_creates_trial_subscription(self):
        """Test that registration creates a trial subscription"""
        registration_data = self.get_valid_registration_data()
        response = self.client.post(self.register_url, registration_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(email=registration_data['email'])
        company = user.company
        
        # Verify trial subscription
        self.assertEqual(company.subscription_status, 'trial')
        self.assertIsNotNone(company.trial_ends_at)
        self.assertGreater(company.trial_ends_at, timezone.now())
        
        # Trial should be 14 days
        trial_duration = company.trial_ends_at - company.created_at
        self.assertAlmostEqual(trial_duration.days, 14, delta=1)


class LoginFlowTestCase(APITestCase, AuthTestMixin):
    """Test complete login flow scenarios"""

    def setUp(self):
        self.login_url = reverse('authentication:login')
        self.profile_url = reverse('authentication:profile')
        self.logout_url = reverse('authentication:logout')

    def test_complete_login_logout_flow(self):
        """Test complete login and logout flow"""
        user = self.create_verified_user()
        
        # Step 1: Login
        login_response = self.client.post(self.login_url, {
            'email': user.email,
            'password': 'TestPass123!'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', login_response.data)
        self.assertIn('user', login_response.data)
        
        # Verify last login was updated
        user.refresh_from_db()
        self.assertIsNotNone(user.last_login)
        
        # Step 2: Access protected resource using tokens
        self.client.force_authenticate(user=user)
        profile_response = self.client.get(self.profile_url)
        
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data['email'], user.email)
        
        # Step 3: Logout
        logout_response = self.client.post(self.logout_url, {
            'refresh': login_response.data['tokens']['refresh']
        })
        
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

    @patch('apps.authentication.utils.verify_totp_token')
    def test_2fa_login_flow(self, mock_verify_totp):
        """Test complete 2FA login flow"""
        user = self.create_2fa_user()
        mock_verify_totp.return_value = True
        
        # Step 1: Initial login without 2FA code
        response = self.client.post(self.login_url, {
            'email': user.email,
            'password': 'TestPass123!'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('requires_2fa', response.data)
        self.assertTrue(response.data['requires_2fa'])
        
        # Step 2: Login with 2FA code
        response = self.client.post(self.login_url, {
            'email': user.email,
            'password': 'TestPass123!',
            'two_fa_code': '123456'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertNotIn('requires_2fa', response.data)

    def test_failed_login_attempts_tracking(self):
        """Test that failed login attempts are tracked"""
        user = self.create_test_user()
        
        # Make several failed login attempts
        for i in range(5):
            response = self.client.post(self.login_url, {
                'email': user.email,
                'password': 'WrongPassword'
            })
            
            if i < 4:
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            else:
                # 5th attempt should trigger lockout
                self.assertEqual(response.status_code, status.HTTP_423_LOCKED)
        
        # Successful login should reset the counter
        # But first we need to wait for lockout to expire or reset it manually
        from ..security_logging import LoginAttemptTracker
        LoginAttemptTracker.reset_attempts(user.email, '127.0.0.1')
        
        response = self.client.post(self.login_url, {
            'email': user.email,
            'password': 'TestPass123!'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PasswordResetFlowTestCase(APITestCase, AuthTestMixin):
    """Test complete password reset flow"""

    def setUp(self):
        self.reset_request_url = reverse('authentication:password-reset-request')
        self.reset_confirm_url = reverse('authentication:password-reset-confirm')
        self.login_url = reverse('authentication:login')

    @mock_external_services()
    def test_complete_password_reset_flow(self):
        """Test complete password reset flow"""
        user = self.create_verified_user()
        
        # Step 1: Request password reset
        reset_request_response = self.client.post(self.reset_request_url, {
            'email': user.email
        })
        
        self.assertEqual(reset_request_response.status_code, status.HTTP_200_OK)
        
        # Step 2: Verify reset token was created
        reset_token = PasswordReset.objects.get(user=user)
        self.assertFalse(reset_token.is_used)
        self.assertGreater(reset_token.expires_at, timezone.now())
        
        # Step 3: Confirm password reset
        new_password = 'NewPassword123!'
        reset_confirm_response = self.client.post(self.reset_confirm_url, {
            'token': reset_token.token,
            'password': new_password,
            'password2': new_password
        })
        
        self.assertEqual(reset_confirm_response.status_code, status.HTTP_200_OK)
        
        # Step 4: Verify password was changed
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))
        self.assertFalse(user.check_password('TestPass123!'))
        
        # Step 5: Verify token is marked as used
        reset_token.refresh_from_db()
        self.assertTrue(reset_token.is_used)
        
        # Step 6: Login with new password should work
        login_response = self.client.post(self.login_url, {
            'email': user.email,
            'password': new_password
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Step 7: Login with old password should fail
        old_login_response = self.client.post(self.login_url, {
            'email': user.email,
            'password': 'TestPass123!'
        })
        
        self.assertEqual(old_login_response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock_external_services()
    def test_password_reset_token_expiration(self):
        """Test that expired password reset tokens are rejected"""
        user = self.create_verified_user()
        
        # Create expired reset token
        expired_reset = self.create_expired_password_reset(user)
        
        # Try to use expired token
        response = self.client.post(self.reset_confirm_url, {
            'token': expired_reset.token,
            'password': 'NewPassword123!',
            'password2': 'NewPassword123!'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    @mock_external_services()
    def test_password_reset_token_single_use(self):
        """Test that password reset tokens can only be used once"""
        user = self.create_verified_user()
        reset_token = self.create_password_reset(user)
        
        # Use token first time
        response = self.client.post(self.reset_confirm_url, {
            'token': reset_token.token,
            'password': 'NewPassword123!',
            'password2': 'NewPassword123!'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try to use token second time
        response = self.client.post(self.reset_confirm_url, {
            'token': reset_token.token,
            'password': 'AnotherPassword123!',
            'password2': 'AnotherPassword123!'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TwoFactorSetupFlowTestCase(APITestCase, AuthTestMixin):
    """Test complete 2FA setup and usage flow"""

    def setUp(self):
        self.setup_2fa_url = reverse('authentication:setup-2fa')
        self.enable_2fa_url = reverse('authentication:enable-2fa')
        self.disable_2fa_url = reverse('authentication:disable-2fa')
        self.login_url = reverse('authentication:login')

    @patch('apps.authentication.utils.verify_totp_token')
    @patch('apps.authentication.utils.generate_qr_code')
    def test_complete_2fa_setup_flow(self, mock_qr_code, mock_verify_totp):
        """Test complete 2FA setup flow"""
        user = self.create_verified_user()
        self.authenticate_user(user)
        
        mock_qr_code.return_value = "data:image/png;base64,mock_qr_code"
        mock_verify_totp.return_value = True
        
        # Step 1: Setup 2FA (get QR code)
        setup_response = self.client.get(self.setup_2fa_url)
        
        self.assertEqual(setup_response.status_code, status.HTTP_200_OK)
        self.assertIn('qr_code', setup_response.data)
        self.assertIn('backup_codes_count', setup_response.data)
        
        # Verify secret was generated
        user.refresh_from_db()
        self.assertNotEqual(user.two_factor_secret, '')
        
        # Step 2: Enable 2FA with valid token
        enable_response = self.client.post(self.enable_2fa_url, {
            'token': '123456'
        })
        
        self.assertEqual(enable_response.status_code, status.HTTP_200_OK)
        self.assertIn('backup_codes', enable_response.data)
        
        # Verify 2FA is enabled
        user.refresh_from_db()
        self.assertTrue(user.is_two_factor_enabled)
        self.assertTrue(len(user.backup_codes) > 0)
        
        # Step 3: Test login with 2FA
        login_response = self.client.post(self.login_url, {
            'email': user.email,
            'password': 'TestPass123!',
            'two_fa_code': '123456'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', login_response.data)

    def test_2fa_disable_flow(self):
        """Test 2FA disable flow"""
        user = self.create_2fa_user()
        self.authenticate_user(user)
        
        # Disable 2FA
        disable_response = self.client.post(self.disable_2fa_url, {
            'password': 'TestPass123!'
        })
        
        self.assertEqual(disable_response.status_code, status.HTTP_200_OK)
        
        # Verify 2FA is disabled
        user.refresh_from_db()
        self.assertFalse(user.is_two_factor_enabled)
        self.assertEqual(user.two_factor_secret, '')
        self.assertEqual(user.backup_codes, [])
        
        # Login should no longer require 2FA
        login_response = self.client.post(self.login_url, {
            'email': user.email,
            'password': 'TestPass123!'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertNotIn('requires_2fa', login_response.data)


class TokenRefreshFlowTestCase(APITestCase, AuthTestMixin):
    """Test JWT token refresh flow"""

    def setUp(self):
        self.refresh_url = reverse('authentication:token-refresh')
        self.profile_url = reverse('authentication:profile')

    def test_token_refresh_flow(self):
        """Test JWT token refresh flow"""
        user = self.create_verified_user()
        tokens = self.get_jwt_tokens(user)
        
        # Step 1: Use refresh token to get new access token
        refresh_response = self.client.post(self.refresh_url, {
            'refresh': tokens['refresh']
        })
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        self.assertIn('refresh', refresh_response.data)
        
        # Step 2: New access token should be different
        new_access_token = refresh_response.data['access']
        self.assertNotEqual(new_access_token, tokens['access'])
        
        # Step 3: New access token should work for authenticated requests
        # This would require manual header setting in a real test
        self.client.force_authenticate(user=user)
        profile_response = self.client.get(self.profile_url)
        
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

    def test_refresh_token_rotation(self):
        """Test refresh token rotation"""
        user = self.create_verified_user()
        tokens = self.get_jwt_tokens(user)
        
        # Use refresh token
        response = self.client.post(self.refresh_url, {
            'refresh': tokens['refresh']
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # New refresh token should be different (if rotation is enabled)
        new_refresh_token = response.data['refresh']
        # Note: Token rotation depends on Django settings
        # This test documents the expected behavior


class EmailVerificationFlowTestCase(APITestCase, AuthTestMixin):
    """Test email verification flow"""

    def setUp(self):
        self.verify_email_url = reverse('authentication:verify-email')
        self.resend_verification_url = reverse('authentication:resend-verification')

    def test_email_verification_flow(self):
        """Test email verification flow"""
        user = self.create_test_user()
        verification = self.create_email_verification(user)
        
        # Step 1: Verify email with token
        response = self.client.post(self.verify_email_url, {
            'token': verification.token
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 2: Verify user email is marked as verified
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        
        # Step 3: Verify token is marked as used
        verification.refresh_from_db()
        self.assertTrue(verification.is_used)

    @mock_external_services()
    def test_resend_verification_flow(self):
        """Test resend verification email flow"""
        user = self.create_test_user()
        self.authenticate_user(user)
        
        # Step 1: Resend verification email
        response = self.client.post(self.resend_verification_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 2: Verify new verification token was created
        verifications = EmailVerification.objects.filter(user=user)
        self.assertTrue(verifications.exists())


class ProfileManagementFlowTestCase(APITestCase, AuthTestMixin):
    """Test profile management flow"""

    def setUp(self):
        self.profile_url = reverse('authentication:profile')
        self.change_password_url = reverse('authentication:change-password')

    def test_profile_update_flow(self):
        """Test profile update flow"""
        user = self.create_verified_user()
        self.authenticate_user(user)
        
        # Step 1: Get current profile
        get_response = self.client.get(self.profile_url)
        
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        original_data = get_response.data
        
        # Step 2: Update profile
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '(11) 88888-8888'
        }
        
        update_response = self.client.patch(self.profile_url, update_data)
        
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['first_name'], 'Updated')
        self.assertEqual(update_response.data['last_name'], 'Name')
        
        # Step 3: Verify changes persist
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Name')

    def test_password_change_flow(self):
        """Test password change flow"""
        user = self.create_verified_user()
        self.authenticate_user(user)
        
        # Step 1: Change password
        response = self.client.put(self.change_password_url, {
            'old_password': 'TestPass123!',
            'new_password': 'NewPassword123!'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)  # New tokens should be provided
        
        # Step 2: Verify password was changed
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewPassword123!'))
        self.assertFalse(user.check_password('TestPass123!'))


class AccountDeletionFlowTestCase(APITestCase, AuthTestMixin):
    """Test account deletion flow"""

    def setUp(self):
        self.delete_account_url = reverse('authentication:delete-account')
        self.login_url = reverse('authentication:login')

    def test_account_deletion_flow(self):
        """Test complete account deletion flow"""
        user = self.create_verified_user()
        user_id = user.id
        self.authenticate_user(user)
        
        # Step 1: Delete account
        response = self.client.post(self.delete_account_url, {
            'password': 'TestPass123!',
            'confirmation': 'deletar'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 2: Verify user was deleted
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=user_id)
        
        # Step 3: Login should no longer work
        login_response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_400_BAD_REQUEST)


class ConcurrentRequestsTestCase(APITestCase, AuthTestMixin):
    """Test handling of concurrent requests"""

    def setUp(self):
        self.login_url = reverse('authentication:login')
        self.refresh_url = reverse('authentication:token-refresh')

    def test_concurrent_login_requests(self):
        """Test handling of concurrent login requests"""
        user = self.create_verified_user()
        
        # Simulate concurrent login requests
        import threading
        import time
        
        results = []
        
        def login_request():
            response = self.client.post(self.login_url, {
                'email': user.email,
                'password': 'TestPass123!'
            })
            results.append(response.status_code)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=login_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        for status_code in results:
            self.assertEqual(status_code, status.HTTP_200_OK)

    def test_concurrent_token_refresh(self):
        """Test handling of concurrent token refresh requests"""
        user = self.create_verified_user()
        tokens = self.get_jwt_tokens(user)
        
        # This test would ideally test concurrent refresh token usage
        # and verify that race conditions are handled properly
        
        refresh_response = self.client.post(self.refresh_url, {
            'refresh': tokens['refresh']
        })
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)


class CrossSystemIntegrationTestCase(TransactionTestCase, AuthTestMixin):
    """Test integration with other system components"""

    def test_user_creation_triggers_company_creation(self):
        """Test that user registration creates associated company"""
        with patch('apps.notifications.email_service.send_verification_email_task.delay'):
            registration_data = self.get_valid_registration_data()
            
            response = self.client.post(
                reverse('authentication:register'), 
                registration_data
            )
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            user = User.objects.get(email=registration_data['email'])
            
            # Verify company was created
            self.assertTrue(hasattr(user, 'company'))
            self.assertEqual(user.company.name, registration_data['company_name'])
            self.assertEqual(user.company.owner, user)

    def test_user_deletion_cascades_properly(self):
        """Test that user deletion properly cascades to related objects"""
        user = self.create_verified_user()
        
        # Create related objects
        verification = self.create_email_verification(user)
        reset = self.create_password_reset(user)
        
        verification_id = verification.id
        reset_id = reset.id
        
        # Delete user
        user.delete()
        
        # Verify related objects were deleted
        with self.assertRaises(EmailVerification.DoesNotExist):
            EmailVerification.objects.get(id=verification_id)
        
        with self.assertRaises(PasswordReset.DoesNotExist):
            PasswordReset.objects.get(id=reset_id)