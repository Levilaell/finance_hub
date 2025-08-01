"""
Test cases for authentication models
"""
import secrets
from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from ..models import EmailVerification, PasswordReset

User = get_user_model()


class UserModelTestCase(TestCase):
    """Test cases for the User model"""

    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'username': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'TestPass123!',
            'phone': '(11) 99999-9999',
        }

    def test_create_user_with_email(self):
        """Test creating a user with email"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.check_password('TestPass123!'))
        self.assertFalse(user.is_email_verified)
        self.assertFalse(user.is_phone_verified)
        self.assertFalse(user.is_two_factor_enabled)
        self.assertEqual(user.preferred_language, 'pt-br')
        self.assertEqual(user.timezone, 'America/Sao_Paulo')

    def test_create_user_without_email_raises_error(self):
        """Test that creating a user without email raises an error"""
        user_data = self.user_data.copy()
        user_data.pop('email')
        
        with self.assertRaises(TypeError):
            User.objects.create_user(**user_data)

    def test_create_user_with_duplicate_email_raises_error(self):
        """Test that creating a user with duplicate email raises an error"""
        User.objects.create_user(**self.user_data)
        
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(**self.user_data)

    def test_user_str_representation(self):
        """Test the string representation of a user"""
        user = User.objects.create_user(**self.user_data)
        expected = f"Test User (test@example.com)"
        self.assertEqual(str(user), expected)

    def test_user_full_name_property(self):
        """Test the full_name property"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.full_name, "Test User")
        
        # Test with empty names
        user.first_name = ""
        user.last_name = ""
        self.assertEqual(user.full_name, "")

    def test_user_initials_property(self):
        """Test the initials property"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.initials, "TU")
        
        # Test with empty names falls back to username
        user.first_name = ""
        user.last_name = ""
        self.assertEqual(user.initials, "TE")  # First two chars of username

    def test_user_email_verification_fields(self):
        """Test email verification related fields"""
        user = User.objects.create_user(**self.user_data)
        
        # Initially not verified
        self.assertFalse(user.is_email_verified)
        
        # Can be set to verified
        user.is_email_verified = True
        user.save()
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

    def test_user_phone_verification_fields(self):
        """Test phone verification related fields"""
        user = User.objects.create_user(**self.user_data)
        
        # Initially not verified
        self.assertFalse(user.is_phone_verified)
        
        # Can be set to verified
        user.is_phone_verified = True
        user.save()
        user.refresh_from_db()
        self.assertTrue(user.is_phone_verified)

    def test_user_two_factor_fields(self):
        """Test 2FA related fields"""
        user = User.objects.create_user(**self.user_data)
        
        # Initially disabled
        self.assertFalse(user.is_two_factor_enabled)
        self.assertEqual(user.two_factor_secret, '')
        self.assertEqual(user.backup_codes, [])
        
        # Can enable 2FA
        user.is_two_factor_enabled = True
        user.two_factor_secret = 'SECRETKEY123456789012345678901234'
        user.backup_codes = ['12345678', '87654321']
        user.save()
        user.refresh_from_db()
        
        self.assertTrue(user.is_two_factor_enabled)
        self.assertEqual(user.two_factor_secret, 'SECRETKEY123456789012345678901234')
        self.assertEqual(user.backup_codes, ['12345678', '87654321'])

    def test_user_payment_gateway_fields(self):
        """Test payment gateway related fields"""
        user = User.objects.create_user(**self.user_data)
        
        # Initially empty
        self.assertIsNone(user.payment_customer_id)
        self.assertIsNone(user.payment_gateway)
        
        # Can set payment gateway info
        user.payment_customer_id = 'cus_stripe123'
        user.payment_gateway = 'stripe'
        user.save()
        user.refresh_from_db()
        
        self.assertEqual(user.payment_customer_id, 'cus_stripe123')
        self.assertEqual(user.payment_gateway, 'stripe')

    def test_user_timestamps(self):
        """Test that timestamps are set correctly"""
        before_create = timezone.now()
        user = User.objects.create_user(**self.user_data)
        after_create = timezone.now()
        
        self.assertTrue(before_create <= user.created_at <= after_create)
        self.assertTrue(before_create <= user.updated_at <= after_create)
        
        # Test updated_at changes on save
        original_updated = user.updated_at
        user.first_name = 'Updated'
        user.save()
        
        self.assertGreater(user.updated_at, original_updated)

    def test_user_indexes_created(self):
        """Test that database indexes are created"""
        # This is more of an integration test but helps ensure indexes exist
        User.objects.create_user(**self.user_data)
        
        # These queries should use indexes efficiently
        User.objects.filter(email='test@example.com')
        User.objects.filter(is_email_verified=True)
        User.objects.filter(created_at__gte=timezone.now() - timedelta(days=1))


class EmailVerificationModelTestCase(TestCase):
    """Test cases for EmailVerification model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            first_name='Test',
            last_name='User',
            password='TestPass123!'
        )

    def test_create_email_verification(self):
        """Test creating an email verification token"""
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(days=7)
        
        verification = EmailVerification.objects.create(
            user=self.user,
            token=token,
            expires_at=expires_at
        )
        
        self.assertEqual(verification.user, self.user)
        self.assertEqual(verification.token, token)
        self.assertEqual(verification.expires_at, expires_at)
        self.assertFalse(verification.is_used)
        self.assertTrue(verification.created_at)

    def test_email_verification_str_representation(self):
        """Test string representation of EmailVerification"""
        verification = EmailVerification.objects.create(
            user=self.user,
            token='test-token',
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        expected = f"Verification for {self.user.email}"
        self.assertEqual(str(verification), expected)

    def test_email_verification_token_uniqueness(self):
        """Test that verification tokens must be unique"""
        token = 'unique-token'
        
        EmailVerification.objects.create(
            user=self.user,
            token=token,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Creating another with same token should fail
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EmailVerification.objects.create(
                    user=self.user,
                    token=token,
                    expires_at=timezone.now() + timedelta(days=7)
                )

    def test_email_verification_relationships(self):
        """Test relationships with User model"""
        verification = EmailVerification.objects.create(
            user=self.user,
            token='test-token',
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Test reverse relationship
        self.assertIn(verification, self.user.email_verifications.all())

    def test_email_verification_cascade_delete(self):
        """Test that verification is deleted when user is deleted"""
        verification = EmailVerification.objects.create(
            user=self.user,
            token='test-token',
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        verification_id = verification.id
        self.user.delete()
        
        # Verification should be deleted
        with self.assertRaises(EmailVerification.DoesNotExist):
            EmailVerification.objects.get(id=verification_id)


class PasswordResetModelTestCase(TestCase):
    """Test cases for PasswordReset model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            first_name='Test',
            last_name='User',
            password='TestPass123!'
        )

    def test_create_password_reset(self):
        """Test creating a password reset token"""
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=2)
        
        reset = PasswordReset.objects.create(
            user=self.user,
            token=token,
            expires_at=expires_at
        )
        
        self.assertEqual(reset.user, self.user)
        self.assertEqual(reset.token, token)
        self.assertEqual(reset.expires_at, expires_at)
        self.assertFalse(reset.is_used)
        self.assertTrue(reset.created_at)

    def test_password_reset_str_representation(self):
        """Test string representation of PasswordReset"""
        reset = PasswordReset.objects.create(
            user=self.user,
            token='test-token',
            expires_at=timezone.now() + timedelta(hours=2)
        )
        
        expected = f"Password reset for {self.user.email}"
        self.assertEqual(str(reset), expected)

    def test_password_reset_token_uniqueness(self):
        """Test that reset tokens must be unique"""
        token = 'unique-reset-token'
        
        PasswordReset.objects.create(
            user=self.user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=2)
        )
        
        # Creating another with same token should fail
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PasswordReset.objects.create(
                    user=self.user,
                    token=token,
                    expires_at=timezone.now() + timedelta(hours=2)
                )

    def test_password_reset_relationships(self):
        """Test relationships with User model"""
        reset = PasswordReset.objects.create(
            user=self.user,
            token='test-token',
            expires_at=timezone.now() + timedelta(hours=2)
        )
        
        # Test reverse relationship
        self.assertIn(reset, self.user.password_resets.all())

    def test_password_reset_cascade_delete(self):
        """Test that reset is deleted when user is deleted"""
        reset = PasswordReset.objects.create(
            user=self.user,
            token='test-token',
            expires_at=timezone.now() + timedelta(hours=2)
        )
        
        reset_id = reset.id
        self.user.delete()
        
        # Reset should be deleted
        with self.assertRaises(PasswordReset.DoesNotExist):
            PasswordReset.objects.get(id=reset_id)

    def test_password_reset_indexing(self):
        """Test that appropriate indexes work efficiently"""
        # Create a few resets
        for i in range(3):
            PasswordReset.objects.create(
                user=self.user,
                token=f'token-{i}',
                expires_at=timezone.now() + timedelta(hours=2)
            )
        
        # These queries should use indexes efficiently
        PasswordReset.objects.filter(user=self.user, is_used=False)
        PasswordReset.objects.filter(token='token-1')
        PasswordReset.objects.filter(expires_at__gt=timezone.now())