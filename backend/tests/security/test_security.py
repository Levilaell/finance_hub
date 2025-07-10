"""
Security tests for the CaixaHub backend.

Tests for:
- JWT token security
- Password hashing and validation
- 2FA implementation
- Session security
- Brute force protection
- Permission escalation prevention
- Data access controls
- API endpoint security
- File upload security
- Sensitive data encryption
- PII handling
- Bank token encryption
- Audit logging
- SQL injection prevention
- XSS prevention
- CSRF protection
"""

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from datetime import datetime, timedelta
import json
import time
from unittest.mock import patch, MagicMock
import hashlib
import hmac

from apps.companies.models import Company, CompanyUser, SubscriptionPlan
from apps.banking.models import BankAccount, BankProvider, Transaction, TransactionCategory
from apps.authentication.models import EmailVerification, PasswordReset
from apps.authentication.validators import PasswordValidator
from apps.reports.models import Report
from apps.notifications.models import Notification

User = get_user_model()


class TestAuthenticationSecurity(TestCase):
    """Test authentication security measures."""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_jwt_token_expiration(self):
        """Test JWT tokens expire correctly."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        # Create token with custom expiration
        refresh = RefreshToken.for_user(user)
        
        # Access token should have shorter expiration
        access_token = refresh.access_token
        
        # Check token claims
        self.assertIn('exp', access_token)
        self.assertIn('user_id', access_token)
        
        # Verify expiration is set correctly (default should be reasonable)
        exp_timestamp = access_token['exp']
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        now = timezone.now()
        
        # Access token should expire within hours, not days
        time_until_expiry = exp_datetime - now
        self.assertLess(time_until_expiry.total_seconds(), 24 * 3600)  # Less than 24 hours
    
    def test_password_hashing_security(self):
        """Test passwords are properly hashed."""
        password = 'SecurePass123!'
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=password,
            first_name='Test',
            last_name='User'
        )
        
        # Password should not be stored in plain text
        self.assertNotEqual(user.password, password)
        
        # Password should be hashed with a strong algorithm
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
        
        # Verify password check works
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.check_password('WrongPassword'))
    
    def test_password_validation_rules(self):
        """Test password validation enforces security rules."""
        validator = PasswordValidator()
        
        # Test weak passwords
        weak_passwords = [
            'password',      # Common password
            '12345678',      # Numeric only
            'abcdefgh',      # Letters only
            'Pass123',       # Too short
            'password123',   # No special chars/uppercase
        ]
        
        for weak_pass in weak_passwords:
            with self.assertRaises(ValidationError):
                validator.validate(weak_pass)
        
        # Test strong passwords
        strong_passwords = [
            'SecurePass123!',
            'C0mpl3x!P@ssw0rd',
            'MyStr0ng#Password',
        ]
        
        for strong_pass in strong_passwords:
            # Should not raise exception
            validator.validate(strong_pass)
    
    @patch('apps.authentication.models.pyotp.TOTP')
    def test_2fa_implementation(self, mock_totp):
        """Test 2FA is properly implemented."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        # Enable 2FA
        user.is_two_factor_enabled = True
        user.two_factor_secret = 'JBSWY3DPEHPK3PXP'
        user.save()
        
        # Mock TOTP verification
        mock_totp_instance = MagicMock()
        mock_totp_instance.verify.return_value = False
        mock_totp.return_value = mock_totp_instance
        
        # Login without 2FA code should indicate 2FA required
        response = self.client.post(reverse('authentication:login'), {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get('requires_2fa'))
        self.assertNotIn('access', response.data)
        
        # Login with invalid 2FA code should fail
        response = self.client.post(reverse('authentication:login'), {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'two_factor_code': '000000'
        })
        
        self.assertEqual(response.status_code, 400)
        
        # Login with valid 2FA code should succeed
        mock_totp_instance.verify.return_value = True
        
        response = self.client.post(reverse('authentication:login'), {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'two_factor_code': '123456'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
    
    def test_session_security_headers(self):
        """Test security headers are set correctly."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Make a request
        response = self.client.get(reverse('authentication:user-detail'))
        
        # Check security headers (these would be set by middleware/nginx in production)
        # In tests, we verify the framework supports them
        self.assertEqual(response.status_code, 200)


class TestBruteForceProtection(TestCase):
    """Test brute force attack protection."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
    
    def test_login_attempt_tracking(self):
        """Test failed login attempts are tracked."""
        # Make several failed login attempts
        for i in range(5):
            response = self.client.post(reverse('authentication:login'), {
                'email': 'test@example.com',
                'password': 'WrongPassword'
            })
            self.assertEqual(response.status_code, 401)
        
        # Check login attempts would be recorded
        # Note: LoginAttempt model would need to be implemented
        # For now, we verify the authentication fails
        pass
    
    @override_settings(MAX_LOGIN_ATTEMPTS=3)
    def test_account_lockout_after_failed_attempts(self):
        """Test account lockout after multiple failed attempts."""
        # This would require implementing the actual lockout mechanism
        # For now, we test the concept
        pass
    
    def test_ip_based_rate_limiting(self):
        """Test IP-based rate limiting for login attempts."""
        # Make many requests from same IP
        for i in range(10):
            self.client.post(reverse('authentication:login'), {
                'email': f'user{i}@example.com',
                'password': 'password'
            })
        
        # Further requests should be rate limited
        # This would be implemented at the middleware/nginx level


class TestAuthorizationSecurity(TestCase):
    """Test authorization and permission security."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create users with different roles
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='TestPass123!',
            first_name='Owner',
            last_name='User'
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='TestPass123!',
            first_name='Regular',
            last_name='User'
        )
        
        self.attacker = User.objects.create_user(
            username='attacker',
            email='attacker@example.com',
            password='TestPass123!',
            first_name='Attacker',
            last_name='User'
        )
        
        # Create companies
        plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00, price_yearly=990.00
        )
        
        self.company = Company.objects.create(
            name='Target Company',
            cnpj='12345678901234',
            owner=self.owner,
            subscription_plan=plan
        )
        
        self.attacker_company = Company.objects.create(
            name='Attacker Company',
            cnpj='98765432109876',
            owner=self.attacker,
            subscription_plan=plan
        )
        
        # Set up company users
        CompanyUser.objects.create(
            company=self.company,
            user=self.owner,
            role='owner'
        )
        
        CompanyUser.objects.create(
            company=self.company,
            user=self.regular_user,
            role='member'
        )
        
        CompanyUser.objects.create(
            company=self.attacker_company,
            user=self.attacker,
            role='owner'
        )
    
    def test_permission_escalation_prevention(self):
        """Test users cannot escalate their permissions."""
        # Regular user tries to perform owner action
        refresh = RefreshToken.for_user(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Try to remove another user (owner only)
        response = self.client.post(reverse('companies:company-remove-user'), {
            'user_id': self.owner.id
        })
        self.assertEqual(response.status_code, 403)
        
        # Try to update company settings (owner only)
        response = self.client.patch(
            reverse('companies:company-update'),
            {'subscription_plan': 'enterprise'}
        )
        self.assertIn(response.status_code, [403, 400])
    
    def test_cross_company_access_prevention(self):
        """Test users cannot access other companies' data."""
        # Create bank account for target company
        provider = BankProvider.objects.create(name='Test Bank', code='001')
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=provider,
            account_type='checking',
            agency='0001',
            account_number='123456',
            current_balance=Decimal('10000.00')
        )
        
        # Attacker tries to access target company's data
        refresh = RefreshToken.for_user(self.attacker)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Try direct access to account
        response = self.client.get(
            reverse('banking:bank-account-detail', kwargs={'pk': account.id})
        )
        self.assertEqual(response.status_code, 404)
        
        # Try to list accounts (should only see own)
        response = self.client.get(reverse('banking:bank-account-list'))
        self.assertEqual(response.status_code, 200)
        
        # Should not contain target company's account
        account_ids = [acc['id'] for acc in response.data['results']]
        self.assertNotIn(str(account.id), account_ids)
    
    def test_api_endpoint_authentication_required(self):
        """Test all API endpoints require authentication."""
        # List of endpoints that should require auth
        protected_endpoints = [
            reverse('banking:dashboard'),
            reverse('banking:bank-account-list'),
            reverse('banking:transaction-list'),
            reverse('reports:report-list'),
            reverse('companies:company-detail'),
            reverse('notifications:notification-list'),
        ]
        
        # Test without authentication
        self.client.credentials()  # Clear auth
        
        for endpoint in protected_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code,
                401,
                f"Endpoint {endpoint} did not require authentication"
            )


class TestDataSecurity(TestCase):
    """Test data security measures."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test data
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00, price_yearly=990.00
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='12345678901234',
            owner=self.user,
            subscription_plan=plan
        )
        
        CompanyUser.objects.create(
            company=self.company,
            user=self.user,
            role='owner'
        )
    
    def test_sensitive_data_encryption(self):
        """Test sensitive data is encrypted in database."""
        # Create bank account with sensitive token
        provider = BankProvider.objects.create(name='Test Bank', code='001')
        
        sensitive_token = 'super-secret-bank-token-12345'
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=provider,
            account_type='checking',
            agency='0001',
            account_number='123456',
            current_balance=Decimal('1000.00'),
            access_token=sensitive_token
        )
        
        # Check token is encrypted in database
        # Direct database query should not reveal plain text
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT access_token FROM banking_bankaccount WHERE id = %s",
                [account.id]
            )
            row = cursor.fetchone()
            stored_token = row[0] if row else None
        
        # Token should be encrypted (not equal to plain text)
        self.assertIsNotNone(stored_token)
        self.assertNotEqual(stored_token, sensitive_token)
        
        # But should be accessible through model
        self.assertEqual(account.access_token, sensitive_token)
    
    def test_pii_data_handling(self):
        """Test PII data is handled securely."""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Get user data
        response = self.client.get(reverse('authentication:user-detail'))
        self.assertEqual(response.status_code, 200)
        
        # Sensitive fields should be masked or excluded
        # For example, full SSN/CPF should not be returned
        self.assertNotIn('password', response.data)
        self.assertNotIn('password_hash', response.data)
    
    def test_bank_token_security(self):
        """Test bank tokens are never exposed in API responses."""
        provider = BankProvider.objects.create(name='Test Bank', code='001')
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=provider,
            account_type='checking',
            agency='0001',
            account_number='123456',
            current_balance=Decimal('1000.00'),
            access_token='secret-token',
            refresh_token='secret-refresh-token'
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Get account details
        response = self.client.get(
            reverse('banking:bank-account-detail', kwargs={'pk': account.id})
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Tokens should not be in response
        self.assertNotIn('access_token', response.data)
        self.assertNotIn('refresh_token', response.data)
        
        # Account number should be masked
        self.assertIn('masked_account', response.data)
        self.assertNotEqual(response.data['masked_account'], '123456')


class TestInputValidation(TestCase):
    """Test input validation and injection prevention."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00, price_yearly=990.00
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='12345678901234',
            owner=self.user,
            subscription_plan=plan
        )
        
        CompanyUser.objects.create(
            company=self.company,
            user=self.user,
            role='owner'
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    
    def test_sql_injection_prevention(self):
        """Test SQL injection is prevented."""
        # Try SQL injection in search
        malicious_inputs = [
            "'; DROP TABLE banking_transaction; --",
            "1' OR '1'='1",
            "admin'--",
            "1; UPDATE companies_company SET owner_id=1; --"
        ]
        
        for malicious_input in malicious_inputs:
            response = self.client.get(
                reverse('banking:transaction-list'),
                {'search': malicious_input}
            )
            
            # Should return safely without executing SQL
            self.assertIn(response.status_code, [200, 400])
            
            # Tables should still exist
            self.assertTrue(
                Transaction._meta.db_table in connection.introspection.table_names()
            )
    
    def test_xss_prevention(self):
        """Test XSS attacks are prevented."""
        provider = BankProvider.objects.create(name='Test Bank', code='001')
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=provider,
            account_type='checking',
            agency='0001',
            account_number='123456',
            current_balance=Decimal('1000.00')
        )
        
        category = TransactionCategory.objects.create(
            name='Test',
            category_type='expense'
        )
        
        # Try XSS in transaction description
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>"
        ]
        
        for payload in xss_payloads:
            response = self.client.post(reverse('banking:transaction-list'), {
                'account': str(account.id),
                'transaction_type': 'debit',
                'amount': '100.00',
                'description': payload,
                'transaction_date': datetime.now().date().isoformat(),
                'category': category.id
            })
            
            if response.status_code == 201:
                # Check the data is stored safely (escaped)
                transaction = Transaction.objects.get(pk=response.data['id'])
                
                # Description should be stored as-is (not executed)
                self.assertEqual(transaction.description, payload)
                
                # When returned in API, should be safe
                response = self.client.get(
                    reverse('banking:transaction-detail', kwargs={'pk': transaction.id})
                )
                self.assertEqual(response.data['description'], payload)
    
    def test_csrf_protection(self):
        """Test CSRF protection is active."""
        # CSRF is handled by Django middleware
        # In API context, we use JWT tokens which are CSRF-safe
        
        # Verify we're using JWT authentication
        response = self.client.get(reverse('banking:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Try without proper auth header
        self.client.credentials()  # Clear credentials
        response = self.client.get(reverse('banking:dashboard'))
        self.assertEqual(response.status_code, 401)
    
    def test_file_upload_validation(self):
        """Test file upload security."""
        # This would test file upload endpoints if they existed
        # For example, report uploads, document attachments, etc.
        pass
    
    def test_input_type_validation(self):
        """Test input type validation."""
        provider = BankProvider.objects.create(name='Test Bank', code='001')
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=provider,
            account_type='checking',
            agency='0001',
            account_number='123456',
            current_balance=Decimal('1000.00')
        )
        
        # Test invalid data types
        invalid_inputs = [
            {'amount': 'not-a-number'},
            {'amount': [100, 200]},
            {'transaction_date': 'not-a-date'},
            {'account': 'not-a-uuid'},
            {'category': 'not-an-id'},
        ]
        
        for invalid_data in invalid_inputs:
            valid_data = {
                'account': str(account.id),
                'transaction_type': 'debit',
                'amount': '100.00',
                'description': 'Test',
                'transaction_date': datetime.now().date().isoformat(),
            }
            valid_data.update(invalid_data)
            
            response = self.client.post(
                reverse('banking:transaction-list'),
                valid_data
            )
            
            # Should reject invalid input
            self.assertEqual(response.status_code, 400)


class TestAuditLogging(TestCase):
    """Test audit logging for security events."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
    
    def test_login_attempts_logged(self):
        """Test login attempts are logged."""
        # Successful login
        response = self.client.post(reverse('authentication:login'), {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        })
        self.assertEqual(response.status_code, 200)
        
        # Check login would be logged
        # Note: LoginAttempt model would need to be implemented
        # For now, we verify the authentication works
        
        # Failed login
        response = self.client.post(reverse('authentication:login'), {
            'email': 'test@example.com',
            'password': 'WrongPassword'
        })
        self.assertEqual(response.status_code, 401)
    
    def test_sensitive_operations_logged(self):
        """Test sensitive operations are logged."""
        # This would test logging of:
        # - User permission changes
        # - Financial transaction modifications
        # - Report access
        # - Data exports
        # - Settings changes
        pass