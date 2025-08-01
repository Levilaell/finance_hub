"""
Test utilities and fixtures for authentication tests
"""
import secrets
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import EmailVerification, PasswordReset

User = get_user_model()


class AuthTestMixin:
    """Mixin class providing common authentication test utilities"""
    
    def create_test_user(self, **kwargs):
        """Create a test user with default values"""
        defaults = {
            'email': 'test@example.com',
            'username': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'TestPass123!',
            'phone': '(11) 99999-9999',
        }
        defaults.update(kwargs)
        
        return User.objects.create_user(**defaults)
    
    def create_verified_user(self, **kwargs):
        """Create a test user with verified email"""
        user = self.create_test_user(**kwargs)
        user.is_email_verified = True
        user.save()
        return user
    
    def create_2fa_user(self, **kwargs):
        """Create a test user with 2FA enabled"""
        user = self.create_test_user(**kwargs)
        user.is_two_factor_enabled = True
        user.two_factor_secret = 'TESTSECRET123456789012345678901234'
        user.backup_codes = ['pbkdf2_sha256$hashed_backup_code_1', 'pbkdf2_sha256$hashed_backup_code_2']
        user.save()
        return user
    
    def create_superuser(self, **kwargs):
        """Create a superuser for testing"""
        defaults = {
            'email': 'admin@example.com',
            'username': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'password': 'AdminPass123!',
        }
        defaults.update(kwargs)
        
        return User.objects.create_superuser(**defaults)
    
    def create_email_verification(self, user, **kwargs):
        """Create an email verification token for a user"""
        defaults = {
            'token': secrets.token_urlsafe(32),
            'expires_at': timezone.now() + timedelta(days=7),
        }
        defaults.update(kwargs)
        
        return EmailVerification.objects.create(
            user=user,
            **defaults
        )
    
    def create_password_reset(self, user, **kwargs):
        """Create a password reset token for a user"""
        defaults = {
            'token': secrets.token_urlsafe(32),
            'expires_at': timezone.now() + timedelta(hours=2),
        }
        defaults.update(kwargs)
        
        return PasswordReset.objects.create(
            user=user,
            **defaults
        )
    
    def create_expired_email_verification(self, user, **kwargs):
        """Create an expired email verification token"""
        defaults = {
            'expires_at': timezone.now() - timedelta(days=1),
        }
        defaults.update(kwargs)
        
        return self.create_email_verification(user, **defaults)
    
    def create_expired_password_reset(self, user, **kwargs):
        """Create an expired password reset token"""
        defaults = {
            'expires_at': timezone.now() - timedelta(hours=1),
        }
        defaults.update(kwargs)
        
        return self.create_password_reset(user, **defaults)
    
    def create_used_email_verification(self, user, **kwargs):
        """Create a used email verification token"""
        verification = self.create_email_verification(user, **kwargs)
        verification.is_used = True
        verification.save()
        return verification
    
    def create_used_password_reset(self, user, **kwargs):
        """Create a used password reset token"""
        reset = self.create_password_reset(user, **kwargs)
        reset.is_used = True
        reset.save()
        return reset
    
    def get_jwt_tokens(self, user):
        """Get JWT tokens for a user"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    
    def authenticate_user(self, user):
        """Authenticate a user in the test client"""
        self.client.force_authenticate(user=user)
    
    def get_valid_registration_data(self, **kwargs):
        """Get valid registration data for testing"""
        defaults = {
            'email': 'newuser@example.com',
            'password': 'NewPass123!',
            'password2': 'NewPass123!',
            'first_name': 'New',
            'last_name': 'User',
            'phone': '(11) 99999-9999',
            'company_name': 'New Company',
            'company_cnpj': '12345678000195',
            'company_type': 'ME',
            'business_sector': 'Tecnologia',
            'selected_plan': 'starter'
        }
        defaults.update(kwargs)
        return defaults
    
    def get_valid_login_data(self, user=None, **kwargs):
        """Get valid login data for testing"""
        if user is None:
            user = self.create_test_user()
        
        defaults = {
            'email': user.email,
            'password': 'TestPass123!',
        }
        defaults.update(kwargs)
        return defaults


class MockEmailService:
    """Mock email service for testing"""
    
    def __init__(self):
        self.sent_emails = []
        self.verification_emails = []
        self.password_reset_emails = []
    
    def send_verification_email_task(self, user_id, verification_url):
        """Mock verification email sending"""
        self.verification_emails.append({
            'user_id': user_id,
            'verification_url': verification_url,
            'timestamp': timezone.now()
        })
        return True
    
    def send_password_reset_email_task(self, user_id, reset_url):
        """Mock password reset email sending"""
        self.password_reset_emails.append({
            'user_id': user_id,
            'reset_url': reset_url,
            'timestamp': timezone.now()
        })
        return True
    
    def clear_sent_emails(self):
        """Clear all sent emails"""
        self.sent_emails.clear()
        self.verification_emails.clear()
        self.password_reset_emails.clear()


class Mock2FAService:
    """Mock 2FA service for testing"""
    
    def __init__(self):
        self.valid_tokens = {}
        self.used_backup_codes = set()
    
    def set_valid_totp_token(self, secret, token):
        """Set a TOTP token as valid for testing"""
        self.valid_tokens[secret] = token
    
    def verify_totp_token(self, secret, token):
        """Mock TOTP token verification"""
        return self.valid_tokens.get(secret) == token
    
    def verify_backup_code(self, user, code):
        """Mock backup code verification"""
        # Simple mock - in real tests, this would check hashed codes
        if code in self.used_backup_codes:
            return False
        
        if code in ['12345678', '87654321']:  # Mock backup codes
            self.used_backup_codes.add(code)
            return True
        
        return False
    
    def generate_qr_code(self, uri):
        """Mock QR code generation"""
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


class SecurityTestHelpers:
    """Helper methods for security testing"""
    
    @staticmethod
    def get_malicious_email_inputs():
        """Get list of malicious email inputs for testing"""
        return [
            'test@evil.com\r\nBcc: admin@company.com',  # Email injection
            'test+<script>alert(1)</script>@example.com',  # XSS attempt
            'test@example.com; DROP TABLE users;',  # SQL injection attempt
            '<script>alert("xss")</script>@example.com',
            'admin\' OR \'1\'=\'1\' --@example.com',
        ]
    
    @staticmethod
    def get_malicious_name_inputs():
        """Get list of malicious name inputs for testing"""
        return [
            '<script>alert("xss")</script>',
            'Robert"; DROP TABLE users; --',
            'John\x00Doe',  # Null byte injection
            '<img src=x onerror=alert("xss")>',
            'javascript:alert("xss")',
        ]
    
    @staticmethod
    def get_weak_passwords():
        """Get list of weak passwords for testing"""
        return [
            'password',          # Too common
            '12345678',         # Only numbers
            'PASSWORD',         # Only uppercase
            'password',         # Only lowercase
            'Pass123',          # No special characters
            'Pass!',            # Too short
            'passWORD123',      # No special characters
            '123',              # Too short
            'qwerty',           # Common pattern
        ]
    
    @staticmethod
    def get_invalid_jwt_tokens():
        """Get list of invalid JWT tokens for testing"""
        return [
            'invalid.token.here',
            'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature',
            '',
            'not-a-jwt-at-all',
            'eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyX2lkIjoxfQ.',  # Algorithm none
        ]


class PerformanceTestHelpers:
    """Helper methods for performance testing"""
    
    @staticmethod
    def measure_response_time(func, *args, **kwargs):
        """Measure response time of a function"""
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    @staticmethod
    def assert_response_time_within_limit(test_case, response_time, limit_seconds):
        """Assert that response time is within acceptable limits"""
        test_case.assertLess(
            response_time, 
            limit_seconds,
            f"Response time {response_time:.3f}s exceeded limit of {limit_seconds}s"
        )


class DatabaseTestHelpers:
    """Helper methods for database-related testing"""
    
    @staticmethod
    def assert_queries_within_limit(test_case, query_limit):
        """Context manager to assert number of database queries"""
        from django.test.utils import override_settings
        from django.db import connection
        from django.test import TransactionTestCase
        
        class QueryCountContext:
            def __init__(self, limit):
                self.limit = limit
                self.initial_queries = len(connection.queries)
            
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                final_queries = len(connection.queries)
                query_count = final_queries - self.initial_queries
                test_case.assertLessEqual(
                    query_count,
                    self.limit,
                    f"Query count {query_count} exceeded limit of {self.limit}"
                )
        
        return QueryCountContext(query_limit)


class APITestHelpers:
    """Helper methods for API testing"""
    
    @staticmethod
    def assert_required_fields_present(test_case, response_data, required_fields):
        """Assert that required fields are present in response"""
        for field in required_fields:
            test_case.assertIn(
                field, 
                response_data, 
                f"Required field '{field}' missing from response"
            )
    
    @staticmethod
    def assert_fields_not_present(test_case, response_data, forbidden_fields):
        """Assert that sensitive fields are not present in response"""
        for field in forbidden_fields:
            test_case.assertNotIn(
                field, 
                response_data, 
                f"Sensitive field '{field}' should not be in response"
            )
    
    @staticmethod
    def assert_pagination_response(test_case, response_data):
        """Assert that response has proper pagination structure"""
        required_pagination_fields = ['count', 'next', 'previous', 'results']
        for field in required_pagination_fields:
            test_case.assertIn(field, response_data)


def create_test_company(owner):
    """Create a test company for a user"""
    from apps.companies.models import Company, SubscriptionPlan
    
    # Get or create a starter plan
    plan, created = SubscriptionPlan.objects.get_or_create(
        slug='starter',
        defaults={
            'name': 'Starter Plan',
            'plan_type': 'starter',
            'price_monthly': 49,
            'price_yearly': 490,
            'max_transactions': 500,
            'max_bank_accounts': 2,
            'has_ai_categorization': False,
            'enable_ai_insights': False,
            'enable_ai_reports': False,
            'max_ai_requests_per_month': 0,
            'has_advanced_reports': True,
            'has_api_access': False,
            'has_accountant_access': False,
            'has_priority_support': True,
            'display_order': 1
        }
    )
    
    company = Company.objects.create(
        owner=owner,
        name='Test Company Ltd',
        cnpj='12.345.678/0001-95',
        company_type='ME',
        business_sector='Tecnologia',
        subscription_plan=plan,
        subscription_status='trial',
        trial_ends_at=timezone.now() + timedelta(days=14)
    )
    
    return company


def mock_external_services():
    """Decorator to mock external services for testing"""
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            with patch('apps.notifications.email_service.send_verification_email_task.delay') as mock_verification:
                with patch('apps.notifications.email_service.send_password_reset_email_task.delay') as mock_reset:
                    with patch('apps.authentication.utils.verify_totp_token') as mock_totp:
                        with patch('apps.authentication.utils.verify_backup_code') as mock_backup:
                            # Set up default mock behaviors
                            mock_verification.return_value = True
                            mock_reset.return_value = True
                            mock_totp.return_value = True
                            mock_backup.return_value = True
                            
                            # Add mocks to test instance if it's a test method
                            if args and hasattr(args[0], 'assertEqual'):
                                test_instance = args[0]
                                test_instance.mock_verification_email = mock_verification
                                test_instance.mock_reset_email = mock_reset
                                test_instance.mock_totp = mock_totp
                                test_instance.mock_backup = mock_backup
                            
                            return test_func(*args, **kwargs)
        return wrapper
    return decorator


class AuthTestCase:
    """Base test case class with authentication utilities"""
    
    def setUp(self):
        super().setUp()
        # Clear any cached data
        from django.core.cache import cache
        cache.clear()
        
        # Initialize mock services
        self.mock_email_service = MockEmailService()
        self.mock_2fa_service = Mock2FAService()
    
    def tearDown(self):
        super().tearDown()
        # Clean up any test data
        self.mock_email_service.clear_sent_emails()
        self.mock_2fa_service.valid_tokens.clear()
        self.mock_2fa_service.used_backup_codes.clear()


# Export commonly used test data
TEST_USER_DATA = {
    'email': 'test@example.com',
    'password': 'TestPass123!',
    'first_name': 'Test',
    'last_name': 'User',
    'phone': '(11) 99999-9999',
}

TEST_COMPANY_DATA = {
    'company_name': 'Test Company Ltd',
    'company_cnpj': '12345678000195',
    'company_type': 'ME',
    'business_sector': 'Tecnologia',
}

TEST_REGISTRATION_DATA = {
    **TEST_USER_DATA,
    'password2': 'TestPass123!',
    **TEST_COMPANY_DATA,
    'selected_plan': 'starter'
}

# Common HTTP status codes for testing
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_429_TOO_MANY_REQUESTS = 429