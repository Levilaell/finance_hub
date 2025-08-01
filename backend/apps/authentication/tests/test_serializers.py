"""
Test cases for authentication serializers
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from ..serializers import (
    ChangePasswordSerializer,
    DeleteAccountSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class UserSerializerTestCase(TestCase):
    """Test cases for UserSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            first_name='Test',
            last_name='User',
            password='TestPass123!',
            phone='(11) 99999-9999',
            is_email_verified=True
        )

    def test_serialize_user(self):
        """Test serializing a user"""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        expected_fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'initials', 'phone', 'avatar',
            'is_email_verified', 'is_phone_verified',
            'preferred_language', 'timezone', 'date_of_birth', 'company'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')
        self.assertEqual(data['full_name'], 'Test User')
        self.assertEqual(data['initials'], 'TU')
        self.assertTrue(data['is_email_verified'])

    def test_read_only_fields(self):
        """Test that read-only fields cannot be updated"""
        serializer = UserSerializer(
            self.user,
            data={'is_email_verified': False, 'company': 'new-company'},
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        
        # Read-only fields should not change
        self.assertTrue(updated_user.is_email_verified)

    def test_update_allowed_fields(self):
        """Test updating allowed fields"""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '(11) 88888-8888',
            'preferred_language': 'en'
        }
        
        serializer = UserSerializer(self.user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
        self.assertEqual(updated_user.phone, '(11) 88888-8888')
        self.assertEqual(updated_user.preferred_language, 'en')


class RegisterSerializerTestCase(TestCase):
    """Test cases for RegisterSerializer"""

    def setUp(self):
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

    def test_valid_registration_data(self):
        """Test registration with valid data"""
        serializer = RegisterSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_required_fields(self):
        """Test registration with missing required fields"""
        required_fields = [
            'email', 'password', 'password2', 'first_name', 'last_name',
            'phone', 'company_name', 'company_cnpj', 'company_type', 'business_sector'
        ]
        
        for field in required_fields:
            data = self.valid_data.copy()
            data.pop(field)
            
            serializer = RegisterSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(field, serializer.errors)

    def test_invalid_email_format(self):
        """Test registration with invalid email format"""
        data = self.valid_data.copy()
        data['email'] = 'invalid-email'
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create a user first
        User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!'
        )
        
        serializer = RegisterSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_password_mismatch(self):
        """Test registration with password mismatch"""
        data = self.valid_data.copy()
        data['password2'] = 'DifferentPassword123!'
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_weak_password(self):
        """Test registration with weak password"""
        weak_passwords = [
            '123',  # Too short
            'password',  # Too common
            '12345678',  # Only numbers
            'PASSWORD',  # Only uppercase
            'password',  # Only lowercase
            'Password',  # Missing number and special char
        ]
        
        for weak_password in weak_passwords:
            data = self.valid_data.copy()
            data['password'] = weak_password
            data['password2'] = weak_password
            
            serializer = RegisterSerializer(data=data)
            self.assertFalse(serializer.is_valid(), f"Password '{weak_password}' should be invalid")
            self.assertIn('password', serializer.errors)

    def test_invalid_names(self):
        """Test registration with invalid names"""
        # Too short first name
        data = self.valid_data.copy()
        data['first_name'] = 'A'
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)
        
        # Non-alphabetic first name
        data = self.valid_data.copy()
        data['first_name'] = 'Test123'
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)
        
        # Too short last name
        data = self.valid_data.copy()
        data['last_name'] = 'B'
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('last_name', serializer.errors)

    def test_invalid_company_name(self):
        """Test registration with invalid company name"""
        data = self.valid_data.copy()
        data['company_name'] = 'AB'  # Too short
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('company_name', serializer.errors)

    def test_invalid_cnpj(self):
        """Test registration with invalid CNPJ"""
        invalid_cnpjs = [
            '123',  # Too short
            '12345678000100',  # Invalid check digits
            'abcd1234000195',  # Contains letters
        ]
        
        for invalid_cnpj in invalid_cnpjs:
            data = self.valid_data.copy()
            data['company_cnpj'] = invalid_cnpj
            
            serializer = RegisterSerializer(data=data)
            self.assertFalse(serializer.is_valid(), f"CNPJ '{invalid_cnpj}' should be invalid")
            self.assertIn('company_cnpj', serializer.errors)

    def test_name_validation_strips_whitespace(self):
        """Test that name validation strips whitespace"""
        data = self.valid_data.copy()
        data['first_name'] = '  Test  '
        data['last_name'] = '  User  '
        data['company_name'] = '  Test Company  '
        
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        self.assertEqual(serializer.validated_data['first_name'], 'Test')
        self.assertEqual(serializer.validated_data['last_name'], 'User')
        self.assertEqual(serializer.validated_data['company_name'], 'Test Company')


class LoginSerializerTestCase(TestCase):
    """Test cases for LoginSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!'
        )

    def test_valid_login(self):
        """Test login with valid credentials"""
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], self.user)

    def test_invalid_email(self):
        """Test login with invalid email"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'TestPass123!'
        }
        
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_invalid_password(self):
        """Test login with invalid password"""
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword'
        }
        
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_inactive_user(self):
        """Test login with inactive user"""
        self.user.is_active = False
        self.user.save()
        
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_missing_fields(self):
        """Test login with missing fields"""
        # Missing email
        serializer = LoginSerializer(data={'password': 'TestPass123!'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
        # Missing password
        serializer = LoginSerializer(data={'email': 'test@example.com'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_two_fa_code_field(self):
        """Test that 2FA code field is accepted"""
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'two_fa_code': '123456'
        }
        
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class PasswordResetRequestSerializerTestCase(TestCase):
    """Test cases for PasswordResetRequestSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!'
        )

    def test_valid_email(self):
        """Test password reset request with valid email"""
        serializer = PasswordResetRequestSerializer(data={'email': 'test@example.com'})
        self.assertTrue(serializer.is_valid())

    def test_nonexistent_email(self):
        """Test password reset request with nonexistent email"""
        serializer = PasswordResetRequestSerializer(data={'email': 'nonexistent@example.com'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_invalid_email_format(self):
        """Test password reset request with invalid email format"""
        serializer = PasswordResetRequestSerializer(data={'email': 'invalid-email'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_missing_email(self):
        """Test password reset request with missing email"""
        serializer = PasswordResetRequestSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class PasswordResetConfirmSerializerTestCase(TestCase):
    """Test cases for PasswordResetConfirmSerializer"""

    def test_valid_data(self):
        """Test password reset confirm with valid data"""
        data = {
            'token': 'valid-token',
            'password': 'NewPass123!',
            'password2': 'NewPass123!'
        }
        
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_password_mismatch(self):
        """Test password reset confirm with password mismatch"""
        data = {
            'token': 'valid-token',
            'password': 'NewPass123!',
            'password2': 'DifferentPass123!'
        }
        
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_weak_password(self):
        """Test password reset confirm with weak password"""
        data = {
            'token': 'valid-token',
            'password': 'weak',
            'password2': 'weak'
        }
        
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_missing_fields(self):
        """Test password reset confirm with missing fields"""
        # Missing token
        serializer = PasswordResetConfirmSerializer(data={
            'password': 'NewPass123!',
            'password2': 'NewPass123!'
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)
        
        # Missing password
        serializer = PasswordResetConfirmSerializer(data={
            'token': 'valid-token',
            'password2': 'NewPass123!'
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)


class ChangePasswordSerializerTestCase(TestCase):
    """Test cases for ChangePasswordSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='OldPass123!'
        )

    def test_valid_password_change(self):
        """Test password change with valid data"""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!'
        }
        
        # Mock request with user
        class MockRequest:
            user = self.user
        
        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': MockRequest()}
        )
        self.assertTrue(serializer.is_valid())

    def test_incorrect_old_password(self):
        """Test password change with incorrect old password"""
        data = {
            'old_password': 'WrongOldPass123!',
            'new_password': 'NewPass123!'
        }
        
        class MockRequest:
            user = self.user
        
        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': MockRequest()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)

    def test_weak_new_password(self):
        """Test password change with weak new password"""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'weak'
        }
        
        class MockRequest:
            user = self.user
        
        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': MockRequest()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)


class EmailVerificationSerializerTestCase(TestCase):
    """Test cases for EmailVerificationSerializer"""

    def test_valid_token(self):
        """Test email verification with valid token"""
        serializer = EmailVerificationSerializer(data={'token': 'valid-token'})
        self.assertTrue(serializer.is_valid())

    def test_missing_token(self):
        """Test email verification with missing token"""
        serializer = EmailVerificationSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)


class DeleteAccountSerializerTestCase(TestCase):
    """Test cases for DeleteAccountSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!'
        )

    def test_valid_deletion_data(self):
        """Test account deletion with valid data"""
        data = {
            'password': 'TestPass123!',
            'confirmation': 'deletar'
        }
        
        class MockRequest:
            user = self.user
        
        serializer = DeleteAccountSerializer(
            data=data,
            context={'request': MockRequest()}
        )
        self.assertTrue(serializer.is_valid())

    def test_incorrect_password(self):
        """Test account deletion with incorrect password"""
        data = {
            'password': 'WrongPassword',
            'confirmation': 'deletar'
        }
        
        class MockRequest:
            user = self.user
        
        serializer = DeleteAccountSerializer(
            data=data,
            context={'request': MockRequest()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_incorrect_confirmation(self):
        """Test account deletion with incorrect confirmation"""
        data = {
            'password': 'TestPass123!',
            'confirmation': 'delete'  # Should be 'deletar'
        }
        
        class MockRequest:
            user = self.user
        
        serializer = DeleteAccountSerializer(
            data=data,
            context={'request': MockRequest()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirmation', serializer.errors)

    def test_missing_fields(self):
        """Test account deletion with missing fields"""
        class MockRequest:
            user = self.user
        
        # Missing password
        serializer = DeleteAccountSerializer(
            data={'confirmation': 'deletar'},
            context={'request': MockRequest()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
        
        # Missing confirmation
        serializer = DeleteAccountSerializer(
            data={'password': 'TestPass123!'},
            context={'request': MockRequest()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirmation', serializer.errors)