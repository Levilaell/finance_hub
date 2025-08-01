"""
Unit tests for Encryption Service
Tests field-level encryption functionality for sensitive financial data
"""
import pytest
from unittest.mock import patch, Mock
from django.test import TestCase
from django.conf import settings
from decimal import Decimal

from apps.ai_insights.services.encryption_service import EncryptionService


class TestEncryptionService(TestCase):
    """Test encryption service functionality"""

    def setUp(self):
        self.encryption_service = EncryptionService()
    
    def test_service_initialization(self):
        """Test that service initializes correctly"""
        self.assertIsNotNone(self.encryption_service.cipher)
        self.assertTrue(hasattr(self.encryption_service, 'cipher'))
    
    def test_encrypt_decrypt_string(self):
        """Test basic string encryption and decryption"""
        test_data = "sensitive_account_number_123456"
        
        # Encrypt
        encrypted = self.encryption_service.encrypt_field(test_data)
        
        # Should be different from original
        self.assertNotEqual(encrypted, test_data)
        self.assertIsInstance(encrypted, str)
        
        # Decrypt
        decrypted = self.encryption_service.decrypt_field(encrypted)
        self.assertEqual(decrypted, test_data)
    
    def test_encrypt_decrypt_number(self):
        """Test numeric data encryption and decryption"""
        test_balance = Decimal('12345.67')
        
        # Encrypt
        encrypted = self.encryption_service.encrypt_field(test_balance)
        self.assertNotEqual(str(encrypted), str(test_balance))
        
        # Decrypt
        decrypted = self.encryption_service.decrypt_field(encrypted)
        self.assertEqual(decrypted, str(test_balance))
    
    def test_encrypt_none_values(self):
        """Test that None values are handled correctly"""
        result = self.encryption_service.encrypt_field(None)
        self.assertIsNone(result)
        
        result = self.encryption_service.decrypt_field(None)
        self.assertIsNone(result)
    
    def test_encrypt_empty_string(self):
        """Test that empty strings are handled correctly"""
        result = self.encryption_service.encrypt_field("")
        self.assertEqual(result, "")
        
        result = self.encryption_service.decrypt_field("")
        self.assertEqual(result, "")
    
    def test_sensitive_field_detection(self):
        """Test that sensitive fields are correctly identified"""
        # Sensitive fields
        self.assertTrue(self.encryption_service.is_sensitive_field('account_number'))
        self.assertTrue(self.encryption_service.is_sensitive_field('balance'))
        self.assertTrue(self.encryption_service.is_sensitive_field('transaction_amount'))
        self.assertTrue(self.encryption_service.is_sensitive_field('credit_card_number'))
        self.assertTrue(self.encryption_service.is_sensitive_field('bank_account'))
        self.assertTrue(self.encryption_service.is_sensitive_field('ssn'))
        self.assertTrue(self.encryption_service.is_sensitive_field('tax_id'))
        
        # Non-sensitive fields
        self.assertFalse(self.encryption_service.is_sensitive_field('id'))
        self.assertFalse(self.encryption_service.is_sensitive_field('created_at'))
        self.assertFalse(self.encryption_service.is_sensitive_field('name'))
        self.assertFalse(self.encryption_service.is_sensitive_field('email'))
    
    def test_encrypt_data_dictionary(self):
        """Test encryption of a data dictionary"""
        test_data = {
            'id': 123,
            'account_number': '123456789',
            'balance': Decimal('1000.00'),
            'name': 'Test Account',
            'created_at': '2023-01-01T00:00:00Z',
            'transaction_amount': Decimal('500.00'),
            'description': 'Test transaction'
        }
        
        encrypted_data = self.encryption_service.encrypt_data(test_data)
        
        # Non-sensitive fields should remain unchanged
        self.assertEqual(encrypted_data['id'], 123)
        self.assertEqual(encrypted_data['name'], 'Test Account')
        self.assertEqual(encrypted_data['created_at'], '2023-01-01T00:00:00Z')
        self.assertEqual(encrypted_data['description'], 'Test transaction')
        
        # Sensitive fields should be encrypted (different from original)
        self.assertNotEqual(encrypted_data['account_number'], '123456789')
        self.assertNotEqual(encrypted_data['balance'], Decimal('1000.00'))
        self.assertNotEqual(encrypted_data['transaction_amount'], Decimal('500.00'))
    
    def test_decrypt_data_dictionary(self):
        """Test decryption of a data dictionary"""
        test_data = {
            'id': 123,
            'account_number': '123456789',
            'balance': Decimal('1000.00'),
            'name': 'Test Account',
            'transaction_amount': Decimal('500.00')
        }
        
        # Encrypt first
        encrypted_data = self.encryption_service.encrypt_data(test_data)
        
        # Then decrypt
        decrypted_data = self.encryption_service.decrypt_data(encrypted_data)
        
        # Should match original
        self.assertEqual(decrypted_data['id'], 123)
        self.assertEqual(decrypted_data['account_number'], '123456789')
        self.assertEqual(decrypted_data['balance'], '1000.00')  # Decimal becomes string after encryption/decryption
        self.assertEqual(decrypted_data['name'], 'Test Account')
        self.assertEqual(decrypted_data['transaction_amount'], '500.00')
    
    def test_encrypt_data_list(self):
        """Test encryption of a list of data items"""
        test_data = [
            {'id': 1, 'balance': Decimal('100.00'), 'name': 'Account 1'},
            {'id': 2, 'balance': Decimal('200.00'), 'name': 'Account 2'}
        ]
        
        encrypted_list = self.encryption_service.encrypt_data(test_data)
        
        self.assertEqual(len(encrypted_list), 2)
        
        # Check first item
        self.assertEqual(encrypted_list[0]['id'], 1)
        self.assertEqual(encrypted_list[0]['name'], 'Account 1')
        self.assertNotEqual(encrypted_list[0]['balance'], Decimal('100.00'))
        
        # Check second item
        self.assertEqual(encrypted_list[1]['id'], 2)
        self.assertEqual(encrypted_list[1]['name'], 'Account 2')
        self.assertNotEqual(encrypted_list[1]['balance'], Decimal('200.00'))
    
    def test_decrypt_data_list(self):
        """Test decryption of a list of data items"""
        test_data = [
            {'id': 1, 'balance': Decimal('100.00'), 'name': 'Account 1'},
            {'id': 2, 'balance': Decimal('200.00'), 'name': 'Account 2'}
        ]
        
        # Encrypt then decrypt
        encrypted_list = self.encryption_service.encrypt_data(test_data)
        decrypted_list = self.encryption_service.decrypt_data(encrypted_list)
        
        self.assertEqual(len(decrypted_list), 2)
        
        # Check first item
        self.assertEqual(decrypted_list[0]['id'], 1)
        self.assertEqual(decrypted_list[0]['name'], 'Account 1')
        self.assertEqual(decrypted_list[0]['balance'], '100.00')
        
        # Check second item
        self.assertEqual(decrypted_list[1]['id'], 2)
        self.assertEqual(decrypted_list[1]['name'], 'Account 2')
        self.assertEqual(decrypted_list[1]['balance'], '200.00')
    
    def test_invalid_encrypted_data(self):
        """Test handling of invalid encrypted data"""
        # Invalid base64
        with self.assertRaises(Exception):
            self.encryption_service.decrypt_field("invalid_base64_data!")
        
        # Valid base64 but invalid encryption
        import base64
        invalid_encrypted = base64.b64encode(b"invalid_encrypted_data").decode('utf-8')
        
        with self.assertRaises(Exception):
            self.encryption_service.decrypt_field(invalid_encrypted)
    
    def test_large_data_encryption(self):
        """Test encryption of large data sets"""
        large_data = "x" * 10000  # 10KB string
        
        encrypted = self.encryption_service.encrypt_field(large_data)
        decrypted = self.encryption_service.decrypt_field(encrypted)
        
        self.assertEqual(decrypted, large_data)
    
    def test_special_characters(self):
        """Test encryption of data with special characters"""
        test_data = "Account#123@bank.com!$%^&*()[]{}|"
        
        encrypted = self.encryption_service.encrypt_field(test_data)
        decrypted = self.encryption_service.decrypt_field(encrypted)
        
        self.assertEqual(decrypted, test_data)
    
    def test_unicode_data(self):
        """Test encryption of unicode data"""
        test_data = "Çrédït Ñümber 12345 ñáme"
        
        encrypted = self.encryption_service.encrypt_field(test_data)
        decrypted = self.encryption_service.decrypt_field(encrypted)
        
        self.assertEqual(decrypted, test_data)
    
    @patch('apps.ai_insights.services.encryption_service.settings')
    def test_missing_encryption_key(self, mock_settings):
        """Test behavior when encryption key is not configured"""
        mock_settings.AI_INSIGHTS_ENCRYPTION_KEY = None
        
        with self.assertRaises(ValueError, match="AI_INSIGHTS_ENCRYPTION_KEY not configured"):
            EncryptionService()
    
    def test_nested_data_structures(self):
        """Test encryption of nested data structures"""
        test_data = {
            'user': {
                'id': 123,
                'account_number': '123456789',
                'profile': {
                    'name': 'John Doe',
                    'ssn': '123-45-6789'
                }
            },
            'transactions': [
                {
                    'id': 1,
                    'amount': Decimal('100.00'),
                    'account_number': '987654321'
                }
            ]
        }
        
        encrypted_data = self.encryption_service.encrypt_data(test_data)
        decrypted_data = self.encryption_service.decrypt_data(encrypted_data)
        
        # Check nested encryption worked
        self.assertEqual(decrypted_data['user']['id'], 123)
        self.assertEqual(decrypted_data['user']['account_number'], '123456789')
        self.assertEqual(decrypted_data['user']['profile']['name'], 'John Doe')
        self.assertEqual(decrypted_data['user']['profile']['ssn'], '123-45-6789')
        self.assertEqual(decrypted_data['transactions'][0]['id'], 1)
        self.assertEqual(decrypted_data['transactions'][0]['amount'], '100.00')
        self.assertEqual(decrypted_data['transactions'][0]['account_number'], '987654321')
    
    def test_consistency_across_instances(self):
        """Test that different service instances produce consistent results"""
        test_data = "sensitive_data_123"
        
        service1 = EncryptionService()
        service2 = EncryptionService()
        
        # Encrypt with first instance
        encrypted = service1.encrypt_field(test_data)
        
        # Decrypt with second instance
        decrypted = service2.decrypt_field(encrypted)
        
        self.assertEqual(decrypted, test_data)


@pytest.mark.django_db 
class TestEncryptionServiceIntegration:
    """Integration tests for encryption service"""
    
    def test_cache_integration(self):
        """Test encryption service with Django cache"""
        from django.core.cache import cache
        
        encryption_service = EncryptionService()
        
        # Test data
        test_data = {
            'id': 123,
            'balance': Decimal('1000.00'),
            'account_number': '123456789'
        }
        
        # Encrypt and cache
        encrypted_data = encryption_service.encrypt_data(test_data)
        cache.set('test_encrypted_data', encrypted_data, timeout=60)
        
        # Retrieve and decrypt
        cached_data = cache.get('test_encrypted_data')
        decrypted_data = encryption_service.decrypt_data(cached_data)
        
        assert decrypted_data['id'] == 123
        assert decrypted_data['balance'] == '1000.00'
        assert decrypted_data['account_number'] == '123456789'
    
    def test_database_field_encryption_simulation(self):
        """Test simulation of database field encryption"""
        encryption_service = EncryptionService()
        
        # Simulate saving encrypted data to database
        original_data = {
            'user_id': 123,
            'account_number': '123456789',
            'balance': Decimal('1500.75'),
            'created_at': '2023-01-01T00:00:00Z'
        }
        
        # Encrypt before "saving"
        encrypted_for_db = encryption_service.encrypt_data(original_data)
        
        # Simulate database storage (in real use, this would be saved to DB)
        stored_data = encrypted_for_db.copy()
        
        # Simulate retrieval and decryption
        decrypted_from_db = encryption_service.decrypt_data(stored_data)
        
        # Verify data integrity
        assert decrypted_from_db['user_id'] == 123
        assert decrypted_from_db['account_number'] == '123456789'
        assert decrypted_from_db['balance'] == '1500.75'
        assert decrypted_from_db['created_at'] == '2023-01-01T00:00:00Z'
    
    def test_performance_benchmark(self):
        """Test encryption/decryption performance"""
        import time
        
        encryption_service = EncryptionService()
        
        # Test data set
        test_data = [
            {
                'id': i,
                'account_number': f'account_{i:06d}',
                'balance': Decimal(f'{i * 100}.{i % 100:02d}'),
                'transaction_amount': Decimal(f'{i * 10}.{i % 10}')
            }
            for i in range(100)  # 100 records
        ]
        
        # Measure encryption time
        start_time = time.time()
        encrypted_data = encryption_service.encrypt_data(test_data)
        encryption_time = time.time() - start_time
        
        # Measure decryption time
        start_time = time.time()
        decrypted_data = encryption_service.decrypt_data(encrypted_data)
        decryption_time = time.time() - start_time
        
        # Performance assertions (adjust thresholds as needed)
        assert encryption_time < 1.0, f"Encryption too slow: {encryption_time:.3f}s"
        assert decryption_time < 1.0, f"Decryption too slow: {decryption_time:.3f}s"
        
        # Verify data integrity
        assert len(decrypted_data) == 100
        assert decrypted_data[0]['account_number'] == 'account_000000'
        assert decrypted_data[99]['account_number'] == 'account_000099'