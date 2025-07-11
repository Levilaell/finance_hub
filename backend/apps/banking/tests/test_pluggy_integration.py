"""
Tests for Pluggy banking integration
"""
import json
from unittest.mock import patch, AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company
from apps.banking.models import BankAccount, BankProvider, Transaction
from apps.banking.pluggy_client import PluggyClient, PluggyError

User = get_user_model()


class PluggyClientTestCase(TestCase):
    """Test Pluggy client functionality"""
    
    def setUp(self):
        self.client = PluggyClient()
        
    @patch('httpx.AsyncClient.post')
    async def test_authenticate(self, mock_post):
        """Test Pluggy authentication"""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'accessToken': 'test-token-123'
        }
        mock_post.return_value = mock_response
        
        # Test authentication
        await self.client._authenticate()
        
        # Verify
        self.assertEqual(self.client._access_token, 'test-token-123')
        self.assertIsNotNone(self.client._token_expires_at)
        
    @patch('httpx.AsyncClient.get')
    async def test_get_connectors(self, mock_get):
        """Test getting bank connectors"""
        # Mock authentication
        self.client._access_token = 'test-token'
        self.client._token_expires_at = datetime.now() + timedelta(hours=2)
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 201,
                    'name': 'Banco do Brasil',
                    'type': 'PERSONAL_BANK',
                    'country': 'BR',
                    'primaryColor': '#FFD700',
                    'health': {'status': 'ONLINE'}
                },
                {
                    'id': 202,
                    'name': 'Itaú',
                    'type': 'PERSONAL_BANK',
                    'country': 'BR',
                    'primaryColor': '#EC7000',
                    'health': {'status': 'ONLINE'}
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test
        connectors = await self.client.get_connectors()
        
        # Verify
        self.assertEqual(len(connectors), 2)
        self.assertEqual(connectors[0]['name'], 'Banco do Brasil')
        self.assertEqual(connectors[1]['name'], 'Itaú')
        
    @patch('httpx.AsyncClient.post')
    async def test_create_connect_token(self, mock_post):
        """Test creating Pluggy Connect token"""
        # Mock authentication
        self.client._access_token = 'test-token'
        self.client._token_expires_at = datetime.now() + timedelta(hours=2)
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'accessToken': 'connect-token-123'
        }
        mock_post.return_value = mock_response
        
        # Test
        result = await self.client.create_connect_token()
        
        # Verify
        self.assertEqual(result['accessToken'], 'connect-token-123')


class PluggyViewsTestCase(APITestCase):
    """Test Pluggy views and endpoints"""
    
    def setUp(self):
        # Create test user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create subscription plan first
        from apps.companies.models import SubscriptionPlan
        self.subscription_plan = SubscriptionPlan.objects.create(
            name='Starter',
            slug='starter',
            plan_type='starter',
            price_monthly=0.00,
            price_yearly=0.00,
            max_transactions=1000,
            max_bank_accounts=3
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user,
            subscription_plan=self.subscription_plan
        )
        self.user.company = self.company
        self.user.save()
        
        # Create test bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Banco do Brasil',
            code='001',
            is_open_banking=True,
            is_active=True
        )
        
        # Authenticate
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
    @patch('apps.banking.pluggy_client.PluggyClient')
    def test_get_pluggy_banks(self, mock_client_class):
        """Test getting available banks from Pluggy"""
        # Mock client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get_connectors.return_value = [
            {
                'id': 201,
                'name': 'Banco do Brasil',
                'type': 'PERSONAL_BANK',
                'imageUrl': 'https://example.com/bb.png',
                'primaryColor': '#FFD700',
                'health': {'status': 'ONLINE'},
                'hasAccounts': True,
                'hasTransactions': True
            }
        ]
        
        # Make request
        url = reverse('banking:pluggy-banks')
        response = self.client.get(url)
        
        # Verify
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['name'], 'Banco do Brasil')
        
    @patch('apps.banking.pluggy_client.PluggyClient')
    def test_create_connect_token(self, mock_client_class):
        """Test creating Pluggy Connect token"""
        # Mock client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.create_connect_token.return_value = {
            'accessToken': 'connect-token-123'
        }
        
        # Make request
        url = reverse('banking:pluggy-connect-token')
        response = self.client.post(url)
        
        # Verify
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['connect_token'], 'connect-token-123')
        self.assertEqual(response.data['data']['status'], 'pluggy_connect_required')
        
    @patch('apps.banking.pluggy_client.PluggyClient')
    def test_handle_item_callback(self, mock_client_class):
        """Test handling Pluggy item callback"""
        # Mock client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock item data
        mock_client.get_item.return_value = {
            'id': 'item-123',
            'connectorId': 201,
            'connector': {
                'name': 'Banco do Brasil'
            }
        }
        
        # Mock accounts data
        mock_client.get_accounts.return_value = [
            {
                'id': 'account-123',
                'type': 'BANK',
                'number': '12345',
                'agency': '0001',
                'balance': 1000.50,
                'name': 'Conta Corrente'
            }
        ]
        
        # Make request
        url = reverse('banking:pluggy-callback')
        data = {
            'item_id': 'item-123',
            'connector_name': 'Banco do Brasil'
        }
        response = self.client.post(url, data, format='json')
        
        # Verify
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['accounts']), 1)
        
        # Check database
        account = BankAccount.objects.get(external_id='account-123')
        self.assertEqual(account.pluggy_item_id, 'item-123')
        self.assertEqual(account.account_number, '12345')
        self.assertEqual(account.agency, '0001')
        self.assertEqual(account.current_balance, Decimal('1000.50'))
        
    @patch('apps.banking.tasks.sync_bank_account')
    def test_sync_account(self, mock_sync_task):
        """Test manually syncing account"""
        # Create test account
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            account_number='12345',
            agency='0001',
            pluggy_item_id='item-123',
            external_id='account-123',
            status='active'
        )
        
        # Mock task
        mock_sync_task.delay.return_value = MagicMock()
        
        # Make request
        url = reverse('banking:pluggy-sync', kwargs={'account_id': account.id})
        response = self.client.post(url)
        
        # Verify
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'processing')
        mock_sync_task.delay.assert_called_once_with(account.id)
        
    def test_disconnect_account(self):
        """Test disconnecting account"""
        # Create test account
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            account_number='12345',
            agency='0001',
            pluggy_item_id='item-123',
            status='active',
            is_active=True
        )
        
        # Make request
        url = reverse('banking:pluggy-disconnect', kwargs={'account_id': account.id})
        response = self.client.delete(url)
        
        # Verify
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check database
        account.refresh_from_db()
        self.assertEqual(account.status, 'inactive')
        self.assertFalse(account.is_active)
        
    def test_get_account_status(self):
        """Test getting account status"""
        # Create test account
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            account_number='12345',
            agency='0001',
            external_id='account-123',
            current_balance=Decimal('1500.00'),
            status='active',
            last_sync_at=timezone.now()
        )
        
        # Make request
        url = reverse('banking:pluggy-status', kwargs={'account_id': account.id})
        response = self.client.get(url)
        
        # Verify
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['account_id'], account.id)
        self.assertEqual(response.data['data']['status'], 'active')
        self.assertEqual(response.data['data']['balance'], 1500.0)


class PluggyIntegrationTestCase(TransactionTestCase):
    """End-to-end integration tests"""
    
    def setUp(self):
        # Create test user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create subscription plan first
        from apps.companies.models import SubscriptionPlan
        self.subscription_plan = SubscriptionPlan.objects.create(
            name='Starter',
            slug='starter',
            plan_type='starter',
            price_monthly=0.00,
            price_yearly=0.00,
            max_transactions=1000,
            max_bank_accounts=3
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user,
            subscription_plan=self.subscription_plan
        )
        self.user.company = self.company
        self.user.save()
        
        # Authenticate
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
    @patch('apps.banking.pluggy_client.PluggyClient')
    def test_complete_connection_flow(self, mock_client_class):
        """Test complete bank connection flow"""
        # Mock client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Step 1: Get available banks
        mock_client.get_connectors.return_value = [
            {
                'id': 201,
                'name': 'Banco do Brasil',
                'type': 'PERSONAL_BANK',
                'primaryColor': '#FFD700',
                'health': {'status': 'ONLINE'}
            }
        ]
        
        url = reverse('banking:pluggy-banks')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 2: Create connect token
        mock_client.create_connect_token.return_value = {
            'accessToken': 'connect-token-123'
        }
        
        url = reverse('banking:pluggy-connect-token')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        connect_token = response.data['data']['connect_token']
        
        # Step 3: Simulate successful connection callback
        mock_client.get_item.return_value = {
            'id': 'item-123',
            'connectorId': 201,
            'connector': {'name': 'Banco do Brasil'}
        }
        
        mock_client.get_accounts.return_value = [
            {
                'id': 'account-123',
                'type': 'BANK',
                'number': '12345',
                'agency': '0001',
                'balance': 2500.00
            }
        ]
        
        url = reverse('banking:pluggy-callback')
        data = {
            'item_id': 'item-123',
            'connector_name': 'Banco do Brasil'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify account was created
        accounts = BankAccount.objects.filter(company=self.company)
        self.assertEqual(accounts.count(), 1)
        
        account = accounts.first()
        self.assertEqual(account.pluggy_item_id, 'item-123')
        self.assertEqual(account.external_id, 'account-123')
        self.assertEqual(account.current_balance, Decimal('2500.00'))
        self.assertEqual(account.status, 'active')


class PluggyWebhookTestCase(TestCase):
    """Test Pluggy webhook handling"""
    
    def setUp(self):
        self.client = APIClient()
        
    def test_webhook_item_created(self):
        """Test webhook for item creation"""
        url = reverse('banking:pluggy-webhook')
        data = {
            'type': 'item/created',
            'data': {
                'id': 'item-123',
                'connectorId': 201
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'received')
        
    def test_webhook_item_error(self):
        """Test webhook for item error"""
        url = reverse('banking:pluggy-webhook')
        data = {
            'type': 'item/error',
            'data': {
                'id': 'item-123',
                'error': 'INVALID_CREDENTIALS'
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_webhook_transactions_created(self):
        """Test webhook for new transactions"""
        url = reverse('banking:pluggy-webhook')
        data = {
            'type': 'transactions/created',
            'data': {
                'accountId': 'account-123',
                'count': 10
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)