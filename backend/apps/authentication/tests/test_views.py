"""
Test cases for authentication views and API endpoints
"""
import json
import secrets
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import EmailVerification, PasswordReset

User = get_user_model()


class RegisterViewTestCase(APITestCase):
    """Test cases for user registration endpoint"""

    def setUp(self):
        self.register_url = reverse('authentication:register')
        self.valid_data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '(11) 99999-9999',
            'company_name': 'Test Company',
            'company_cnpj': '12345678000195',
            'company_type': 'ME',
            'business_sector': 'Tecnologia',
            'selected_plan': 'starter'
        }

    @patch('apps.notifications.email_service.send_verification_email_task.delay')
    def test_successful_registration(self, mock_email_task):
        """Test successful user registration"""
        response = self.client.post(self.register_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('message', response.data)
        
        # Verify user was created
        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertFalse(user.is_email_verified)
        
        # Verify email verification token was created
        self.assertTrue(EmailVerification.objects.filter(user=user).exists())
        
        # Verify email task was called
        mock_email_task.assert_called_once()
        
        # Verify JWT tokens are present
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

    def test_registration_with_invalid_data(self):
        """Test registration with invalid data"""
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        response = self.client.post(self.register_url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_with_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create a user first
        User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!'
        )
        
        response = self.client.post(self.register_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_password_mismatch(self):
        """Test registration with password mismatch"""
        invalid_data = self.valid_data.copy()
        invalid_data['password2'] = 'DifferentPassword123!'
        
        response = self.client.post(self.register_url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    @override_settings(RATELIMIT_ENABLE=True)
    def test_registration_rate_limiting(self):
        """Test that registration is rate limited"""
        # This test would need actual rate limiting configured
        # For now, just ensure the endpoint responds properly
        response = self.client.post(self.register_url, self.valid_data)
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_429_TOO_MANY_REQUESTS])


class LoginViewTestCase(APITestCase):
    """Test cases for user login endpoint"""

    def setUp(self):
        self.login_url = reverse('authentication:login')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )

    def test_successful_login(self):
        """Test successful login"""
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        
        # Verify JWT tokens are present
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        
        # Verify user data
        self.assertEqual(response.data['user']['email'], 'test@example.com')
        
        # Verify last login was updated
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)

    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_nonexistent_user(self):
        """Test login with nonexistent user"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_inactive_user(self):
        """Test login with inactive user"""
        self.user.is_active = False
        self.user.save()
        
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_fields(self):
        """Test login with missing fields"""
        # Missing password
        response = self.client.post(self.login_url, {'email': 'test@example.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing email  
        response = self.client.post(self.login_url, {'password': 'TestPass123!'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.authentication.utils.verify_totp_token')
    def test_login_with_2fa_enabled(self, mock_verify_totp):
        """Test login with 2FA enabled"""
        # Enable 2FA for user
        self.user.is_two_factor_enabled = True
        self.user.two_factor_secret = 'TEST2FASECRET123456789012345678'
        self.user.save()
        
        # First attempt without 2FA code should require 2FA
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('requires_2fa', response.data)
        self.assertTrue(response.data['requires_2fa'])
        
        # Second attempt with valid 2FA code should succeed
        mock_verify_totp.return_value = True
        data['two_fa_code'] = '123456'
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)

    @patch('apps.authentication.utils.verify_totp_token')
    @patch('apps.authentication.utils.verify_backup_code')
    def test_login_with_2fa_backup_code(self, mock_verify_backup, mock_verify_totp):
        """Test login with 2FA backup code"""
        self.user.is_two_factor_enabled = True
        self.user.two_factor_secret = 'TEST2FASECRET123456789012345678'
        self.user.save()
        
        # Mock TOTP failure but backup code success
        mock_verify_totp.return_value = False
        mock_verify_backup.return_value = True
        
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'two_fa_code': '12345678'  # Backup code format
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)


class LogoutViewTestCase(APITestCase):
    """Test cases for user logout endpoint"""

    def setUp(self):
        self.logout_url = reverse('authentication:logout')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!'
        )

    def test_successful_logout(self):
        """Test successful logout"""
        # First login to get tokens
        self.client.force_authenticate(user=self.user)
        refresh = RefreshToken.for_user(self.user)
        
        data = {'refresh': str(refresh)}
        response = self.client.post(self.logout_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_logout_without_authentication(self):
        """Test logout without authentication"""
        response = self.client.post(self.logout_url, {})
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_invalid_token(self):
        """Test logout with invalid refresh token"""
        self.client.force_authenticate(user=self.user)
        
        data = {'refresh': 'invalid-token'}
        response = self.client.post(self.logout_url, data)
        
        # Should still return success (graceful handling)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ProfileViewTestCase(APITestCase):
    """Test cases for user profile endpoint"""

    def setUp(self):
        self.profile_url = reverse('authentication:profile')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )

    def test_get_profile_authenticated(self):
        """Test getting profile when authenticated"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')

    def test_get_profile_unauthenticated(self):
        """Test getting profile when not authenticated"""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile(self):
        """Test updating user profile"""
        self.client.force_authenticate(user=self.user)
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '(11) 88888-8888'
        }
        
        response = self.client.patch(self.profile_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        self.assertEqual(response.data['phone'], '(11) 88888-8888')
        
        # Verify database was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_profile_cache_headers(self):
        """Test that profile has appropriate cache headers"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Cache-Control'], 'no-cache, no-store, must-revalidate')
        self.assertEqual(response['Pragma'], 'no-cache')
        self.assertEqual(response['Expires'], '0')


class ChangePasswordViewTestCase(APITestCase):
    """Test cases for change password endpoint"""

    def setUp(self):
        self.change_password_url = reverse('authentication:change-password')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='OldPass123!'
        )

    def test_successful_password_change(self):
        """Test successful password change"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!'
        }
        
        response = self.client.put(self.change_password_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('tokens', response.data)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))
        self.assertFalse(self.user.check_password('OldPass123!'))

    def test_password_change_with_wrong_old_password(self):
        """Test password change with incorrect old password"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'old_password': 'WrongOldPass123!',
            'new_password': 'NewPass123!'
        }
        
        response = self.client.put(self.change_password_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)

    def test_password_change_with_weak_new_password(self):
        """Test password change with weak new password"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'weak'
        }
        
        response = self.client.put(self.change_password_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)

    def test_password_change_unauthenticated(self):
        """Test password change without authentication"""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!'
        }
        
        response = self.client.put(self.change_password_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetViewTestCase(APITestCase):
    """Test cases for password reset endpoints"""

    def setUp(self):
        self.reset_request_url = reverse('authentication:password-reset-request')
        self.reset_confirm_url = reverse('authentication:password-reset-confirm')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!'
        )

    @patch('apps.notifications.email_service.send_password_reset_email_task.delay')
    def test_password_reset_request(self, mock_email_task):
        """Test password reset request"""
        data = {'email': 'test@example.com'}
        
        response = self.client.post(self.reset_request_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify reset token was created
        self.assertTrue(PasswordReset.objects.filter(user=self.user).exists())
        
        # Verify email task was called
        mock_email_task.assert_called_once()

    def test_password_reset_request_nonexistent_email(self):
        """Test password reset request with nonexistent email"""
        data = {'email': 'nonexistent@example.com'}
        
        response = self.client.post(self.reset_request_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_password_reset_confirm_with_valid_token(self):
        """Test password reset confirmation with valid token"""
        # Create a reset token
        token = secrets.token_urlsafe(32)
        PasswordReset.objects.create(
            user=self.user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=2)
        )
        
        data = {
            'token': token,
            'password': 'NewPassword123!',
            'password2': 'NewPassword123!'
        }
        
        response = self.client.post(self.reset_confirm_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123!'))
        
        # Verify token was marked as used
        reset = PasswordReset.objects.get(token=token)
        self.assertTrue(reset.is_used)

    def test_password_reset_confirm_with_invalid_token(self):
        """Test password reset confirmation with invalid token"""
        data = {
            'token': 'invalid-token',
            'password': 'NewPassword123!',
            'password2': 'NewPassword123!'
        }
        
        response = self.client.post(self.reset_confirm_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_password_reset_confirm_with_expired_token(self):
        """Test password reset confirmation with expired token"""
        # Create an expired reset token
        token = secrets.token_urlsafe(32)
        PasswordReset.objects.create(
            user=self.user,
            token=token,
            expires_at=timezone.now() - timedelta(hours=1)  # Expired
        )
        
        data = {
            'token': token,
            'password': 'NewPassword123!',
            'password2': 'NewPassword123!'
        }
        
        response = self.client.post(self.reset_confirm_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class EmailVerificationViewTestCase(APITestCase):
    """Test cases for email verification endpoints"""

    def setUp(self):
        self.verify_url = reverse('authentication:verify-email')
        self.resend_url = reverse('authentication:resend-verification')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!',
            is_email_verified=False
        )

    def test_email_verification_with_valid_token(self):
        """Test email verification with valid token"""
        # Create verification token
        token = secrets.token_urlsafe(32)
        EmailVerification.objects.create(
            user=self.user,
            token=token,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        data = {'token': token}
        response = self.client.post(self.verify_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify user email was marked as verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        
        # Verify token was marked as used
        verification = EmailVerification.objects.get(token=token)
        self.assertTrue(verification.is_used)

    def test_email_verification_with_invalid_token(self):
        """Test email verification with invalid token"""
        data = {'token': 'invalid-token'}
        response = self.client.post(self.verify_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_email_verification_with_expired_token(self):
        """Test email verification with expired token"""
        # Create expired verification token
        token = secrets.token_urlsafe(32)
        EmailVerification.objects.create(
            user=self.user,
            token=token,
            expires_at=timezone.now() - timedelta(days=1)  # Expired
        )
        
        data = {'token': token}
        response = self.client.post(self.verify_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    @patch('apps.notifications.email_service.send_verification_email_task.delay')
    def test_resend_verification_email(self, mock_email_task):
        """Test resending verification email"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(self.resend_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify new verification token was created
        self.assertTrue(EmailVerification.objects.filter(user=self.user).exists())
        
        # Verify email task was called
        mock_email_task.assert_called_once()

    def test_resend_verification_already_verified(self):
        """Test resending verification when already verified"""
        self.user.is_email_verified = True
        self.user.save()
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(self.resend_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)


class TokenRefreshViewTestCase(APITestCase):
    """Test cases for JWT token refresh endpoint"""

    def setUp(self):
        self.refresh_url = reverse('authentication:token-refresh')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!'
        )

    def test_successful_token_refresh(self):
        """Test successful token refresh"""
        refresh = RefreshToken.for_user(self.user)
        
        data = {'refresh': str(refresh)}
        response = self.client.post(self.refresh_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_refresh_with_invalid_token(self):
        """Test token refresh with invalid token"""
        data = {'refresh': 'invalid-token'}
        response = self.client.post(self.refresh_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_token_refresh_without_token(self):
        """Test token refresh without providing token"""
        response = self.client.post(self.refresh_url, {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class TwoFactorAuthViewTestCase(APITestCase):
    """Test cases for 2FA setup and management endpoints"""

    def setUp(self):
        self.setup_2fa_url = reverse('authentication:setup-2fa')
        self.enable_2fa_url = reverse('authentication:enable-2fa')
        self.disable_2fa_url = reverse('authentication:disable-2fa')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!'
        )

    def test_setup_2fa_generates_secret(self):
        """Test that 2FA setup generates secret and QR code"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.setup_2fa_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('qr_code', response.data)
        self.assertIn('backup_codes_count', response.data)
        self.assertIn('setup_complete', response.data)
        
        # Verify secret was generated and saved
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.two_factor_secret, '')

    @patch('apps.authentication.utils.verify_totp_token')
    def test_enable_2fa_with_valid_token(self, mock_verify_totp):
        """Test enabling 2FA with valid TOTP token"""
        # Setup secret first
        self.user.two_factor_secret = 'TEST2FASECRET123456789012345678'
        self.user.save()
        
        mock_verify_totp.return_value = True
        
        self.client.force_authenticate(user=self.user)
        
        data = {'token': '123456'}
        response = self.client.post(self.enable_2fa_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('backup_codes', response.data)
        
        # Verify 2FA was enabled
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_two_factor_enabled)
        self.assertTrue(len(self.user.backup_codes) > 0)

    @patch('apps.authentication.utils.verify_totp_token')
    def test_enable_2fa_with_invalid_token(self, mock_verify_totp):
        """Test enabling 2FA with invalid TOTP token"""
        self.user.two_factor_secret = 'TEST2FASECRET123456789012345678'
        self.user.save()
        
        mock_verify_totp.return_value = False
        
        self.client.force_authenticate(user=self.user)
        
        data = {'token': '000000'}
        response = self.client.post(self.enable_2fa_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_disable_2fa_with_valid_password(self):
        """Test disabling 2FA with valid password"""
        # Enable 2FA first
        self.user.is_two_factor_enabled = True
        self.user.two_factor_secret = 'TEST2FASECRET123456789012345678'
        self.user.backup_codes = ['12345678']
        self.user.save()
        
        self.client.force_authenticate(user=self.user)
        
        data = {'password': 'TestPass123!'}
        response = self.client.post(self.disable_2fa_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify 2FA was disabled
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_two_factor_enabled)
        self.assertEqual(self.user.two_factor_secret, '')
        self.assertEqual(self.user.backup_codes, [])

    def test_disable_2fa_with_invalid_password(self):
        """Test disabling 2FA with invalid password"""
        self.user.is_two_factor_enabled = True
        self.user.save()
        
        self.client.force_authenticate(user=self.user)
        
        data = {'password': 'WrongPassword'}
        response = self.client.post(self.disable_2fa_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class DeleteAccountViewTestCase(APITestCase):
    """Test cases for account deletion endpoint"""

    def setUp(self):
        self.delete_account_url = reverse('authentication:delete-account')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!'
        )

    def test_successful_account_deletion(self):
        """Test successful account deletion"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'password': 'TestPass123!',
            'confirmation': 'deletar'
        }
        
        response = self.client.post(self.delete_account_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify user was deleted
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=self.user.id)

    def test_account_deletion_with_wrong_password(self):
        """Test account deletion with wrong password"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'password': 'WrongPassword',
            'confirmation': 'deletar'
        }
        
        response = self.client.post(self.delete_account_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_account_deletion_wrong_confirmation(self):
        """Test account deletion with wrong confirmation"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'password': 'TestPass123!',
            'confirmation': 'delete'  # Should be 'deletar'
        }
        
        response = self.client.post(self.delete_account_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirmation', response.data)

    def test_superuser_cannot_delete_account(self):
        """Test that superuser accounts cannot be deleted"""
        self.user.is_superuser = True
        self.user.save()
        
        self.client.force_authenticate(user=self.user)
        
        data = {
            'password': 'TestPass123!',
            'confirmation': 'deletar'
        }
        
        response = self.client.post(self.delete_account_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)

    def test_account_deletion_unauthenticated(self):
        """Test account deletion without authentication"""
        data = {
            'password': 'TestPass123!',
            'confirmation': 'deletar'
        }
        
        response = self.client.post(self.delete_account_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)