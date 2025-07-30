"""
Tests for Pluggy integration improvements
"""
import json
from unittest.mock import patch, Mock
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from apps.companies.models import Company
from apps.banking.models import (
    PluggyConnector, PluggyItem, BankAccount,
    Transaction, TransactionCategory, PluggyCategory
)
from apps.banking.integrations.pluggy.client import PluggyClient, PluggyError

User = get_user_model()


class PluggyClientTestCase(TestCase):
    """Test Pluggy client functionality"""
    
    def setUp(self):
        self.client = PluggyClient()
        
    def test_update_transaction_category(self):
        """Test updating transaction category"""
        with patch.object(self.client, '_make_request') as mock_request:
            mock_request.return_value = {
                'id': 'trans_123',
                'categoryId': 'cat_456',
                'category': 'Food > Restaurant'
            }
            
            result = self.client.update_transaction_category('trans_123', 'cat_456')
            
            mock_request.assert_called_once_with(
                'PATCH',
                'transactions/trans_123',
                data={'categoryId': 'cat_456'}
            )
            self.assertEqual(result['categoryId'], 'cat_456')
    
    def test_create_connect_token_with_all_parameters(self):
        """Test creating connect token with all parameters"""
        with patch.object(self.client, '_make_request') as mock_request:
            mock_request.return_value = {
                'accessToken': 'token_123',
                'connectUrl': 'https://connect.pluggy.ai?token=token_123'
            }
            
            result = self.client.create_connect_token(
                client_user_id='user_123',
                item_id='item_456',
                webhook_url='https://example.com/webhook',
                oauth_redirect_uri='https://example.com/callback',
                avoid_duplicates=True,
                country_codes=['BR', 'US'],
                connector_types=['PERSONAL_BANK', 'BUSINESS_BANK'],
                connector_ids=[1, 2, 3],
                products_types=['ACCOUNTS', 'TRANSACTIONS']
            )
            
            expected_payload = {
                'clientUserId': 'user_123',
                'itemId': 'item_456',
                'webhookUrl': 'https://example.com/webhook',
                'oauthRedirectUri': 'https://example.com/callback',
                'avoidDuplicates': True,
                'countryCodes': ['BR', 'US'],
                'connectorTypes': ['PERSONAL_BANK', 'BUSINESS_BANK'],
                'connectorIds': [1, 2, 3],
                'productsTypes': ['ACCOUNTS', 'TRANSACTIONS']
            }
            
            mock_request.assert_called_once_with(
                'POST',
                'connect_token',
                data=expected_payload
            )
            self.assertEqual(result['accessToken'], 'token_123')
    
    def test_validate_webhook_signature_valid(self):
        """Test valid webhook signature validation"""
        import hmac
        import hashlib
        
        # Set up webhook secret
        with patch('django.conf.settings.PLUGGY_WEBHOOK_SECRET', 'test_secret'):
            payload = b'{"event": "item.updated", "itemId": "123"}'
            
            # Generate valid signature
            expected_signature = hmac.new(
                b'test_secret',
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Test validation
            is_valid = self.client.validate_webhook_signature(expected_signature, payload)
            self.assertTrue(is_valid)
    
    def test_validate_webhook_signature_invalid(self):
        """Test invalid webhook signature validation"""
        with patch('django.conf.settings.PLUGGY_WEBHOOK_SECRET', 'test_secret'):
            payload = b'{"event": "item.updated", "itemId": "123"}'
            invalid_signature = 'invalid_signature_123'
            
            is_valid = self.client.validate_webhook_signature(invalid_signature, payload)
            self.assertFalse(is_valid)
    
    def test_validate_webhook_signature_no_secret(self):
        """Test webhook validation when no secret is configured"""
        with patch('django.conf.settings.PLUGGY_WEBHOOK_SECRET', None):
            payload = b'{"event": "item.updated", "itemId": "123"}'
            signature = 'any_signature'
            
            # Should accept webhook when no secret is configured
            is_valid = self.client.validate_webhook_signature(signature, payload)
            self.assertTrue(is_valid)


class TransactionCategorySyncTestCase(APITestCase):
    """Test transaction category synchronization with Pluggy"""
    
    def setUp(self):
        # Create user and company
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            name='Test Company',
            document='12345678901234'
        )
        self.user.company = self.company
        self.user.save()
        
        # Create connector and item
        self.connector = PluggyConnector.objects.create(
            pluggy_id=1,
            name='Test Bank',
            type='PERSONAL_BANK',
            country='BR'
        )
        
        self.item = PluggyItem.objects.create(
            pluggy_item_id='item_123',
            company=self.company,
            connector=self.connector,
            status='UPDATED',
            pluggy_created_at='2024-01-01T00:00:00Z',
            pluggy_updated_at='2024-01-01T00:00:00Z'
        )
        
        # Create account
        self.account = BankAccount.objects.create(
            pluggy_account_id='acc_123',
            item=self.item,
            company=self.company,
            type='BANK',
            name='Test Account',
            balance=Decimal('1000.00'),
            pluggy_created_at='2024-01-01T00:00:00Z',
            pluggy_updated_at='2024-01-01T00:00:00Z'
        )
        
        # Create categories
        self.pluggy_category = PluggyCategory.objects.create(
            id='Food > Restaurant',
            description='Restaurant',
            parent_description='Food'
        )
        
        self.category = TransactionCategory.objects.create(
            name='Restaurant',
            slug='restaurant',
            type='expense',
            company=self.company
        )
        
        # Link Pluggy category to internal category
        self.pluggy_category.internal_category = self.category
        self.pluggy_category.save()
        
        # Create transaction
        self.transaction = Transaction.objects.create(
            pluggy_transaction_id='trans_123',
            account=self.account,
            company=self.company,
            type='DEBIT',
            description='Restaurant payment',
            amount=Decimal('50.00'),
            date='2024-01-01T12:00:00Z',
            pluggy_created_at='2024-01-01T12:00:00Z',
            pluggy_updated_at='2024-01-01T12:00:00Z'
        )
        
        self.client.force_authenticate(user=self.user)
    
    @patch('apps.banking.integrations.pluggy.client.PluggyClient.update_transaction_category')
    def test_update_transaction_category_syncs_with_pluggy(self, mock_update):
        """Test that updating transaction category syncs with Pluggy"""
        mock_update.return_value = {
            'id': 'trans_123',
            'categoryId': 'Food > Restaurant'
        }
        
        url = reverse('banking:transaction-detail', kwargs={'pk': self.transaction.id})
        data = {
            'category': str(self.category.id)
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_update.assert_called_once_with(
            'trans_123',
            'Food > Restaurant'
        )
        
        # Verify transaction was updated
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.category, self.category)
    
    def test_update_transaction_without_pluggy_mapping(self):
        """Test updating transaction category without Pluggy mapping"""
        # Create category without Pluggy mapping
        new_category = TransactionCategory.objects.create(
            name='Custom Category',
            slug='custom-category',
            type='expense',
            company=self.company
        )
        
        url = reverse('banking:transaction-detail', kwargs={'pk': self.transaction.id})
        data = {
            'category': str(new_category.id)
        }
        
        with patch('apps.banking.integrations.pluggy.client.PluggyClient.update_transaction_category') as mock_update:
            response = self.client.patch(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Should not call Pluggy API when no mapping exists
            mock_update.assert_not_called()
            
            # Transaction should still be updated locally
            self.transaction.refresh_from_db()
            self.assertEqual(self.transaction.category, new_category)


class ConnectTokenTestCase(APITestCase):
    """Test Pluggy Connect token creation with new parameters"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            name='Test Company',
            document='12345678901234'
        )
        self.user.company = self.company
        self.user.save()
        
        self.client.force_authenticate(user=self.user)
        self.url = reverse('banking:pluggy-connect-token')
    
    @patch('apps.banking.integrations.pluggy.client.PluggyClient.create_connect_token')
    def test_create_connect_token_with_filters(self, mock_create):
        """Test creating connect token with filtering parameters"""
        mock_create.return_value = {
            'accessToken': 'token_123',
            'connectUrl': 'https://connect.pluggy.ai?token=token_123'
        }
        
        data = {
            'avoid_duplicates': True,
            'country_codes': ['BR'],
            'connector_types': ['PERSONAL_BANK'],
            'products_types': ['ACCOUNTS', 'TRANSACTIONS']
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['data']['connect_token'], 'token_123')
        
        # Verify parameters were passed correctly
        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args['avoid_duplicates'], True)
        self.assertEqual(call_args['country_codes'], ['BR'])
        self.assertEqual(call_args['connector_types'], ['PERSONAL_BANK'])
        self.assertEqual(call_args['products_types'], ['ACCOUNTS', 'TRANSACTIONS'])