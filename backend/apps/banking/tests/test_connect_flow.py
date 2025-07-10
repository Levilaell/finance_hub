"""
End-to-end tests for bank connection flow
"""
import json
from unittest.mock import patch, AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta

from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company
from apps.banking.models import BankAccount, BankProvider
from apps.banking.services import BankingSyncService

User = get_user_model()


class BankConnectionFlowTestCase(APITestCase):
    """Test complete bank connection flow from UI perspective"""
    
    def setUp(self):
        # Create test user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user
        )
        self.user.company = self.company
        self.user.save()
        
        # Authenticate
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
    @patch('apps.banking.pluggy_views.PluggyClient')
    def test_pluggy_connection_flow(self, mock_client_class):
        """Test Pluggy connection flow"""
        # Mock client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Step 1: User loads accounts page, gets bank list
        mock_client.get_connectors.return_value = [
            {
                'id': 201,
                'name': 'Banco do Brasil',
                'type': 'PERSONAL_BANK',
                'imageUrl': 'https://example.com/bb.png',
                'primaryColor': '#FFD700',
                'health': {'status': 'ONLINE'}
            },
            {
                'id': 202,
                'name': 'Itaú',
                'type': 'PERSONAL_BANK',
                'imageUrl': 'https://example.com/itau.png',
                'primaryColor': '#EC7000',
                'health': {'status': 'ONLINE'}
            }
        ]
        
        response = self.client.get(reverse('banking:pluggy-banks'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)
        
        # Step 2: User selects a bank and requests connect token
        mock_client.create_connect_token.return_value = {
            'accessToken': 'connect-token-xyz'
        }
        
        response = self.client.post(reverse('banking:pluggy-connect-token'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'pluggy_connect_required')
        
        connect_token = response.data['data']['connect_token']
        self.assertEqual(connect_token, 'connect-token-xyz')
        
        # Step 3: User completes Pluggy Connect, callback is triggered
        mock_client.get_item.return_value = {
            'id': 'item-abc123',
            'connectorId': 201,
            'connector': {'name': 'Banco do Brasil'},
            'status': 'OK'
        }
        
        mock_client.get_accounts.return_value = [
            {
                'id': 'acc-001',
                'type': 'BANK',
                'subtype': 'CHECKING_ACCOUNT',
                'number': '12345',
                'agency': '0001',
                'balance': 2500.50,
                'name': 'Conta Corrente'
            },
            {
                'id': 'acc-002',
                'type': 'BANK',
                'subtype': 'SAVINGS_ACCOUNT',
                'number': '54321',
                'agency': '0001',
                'balance': 5000.00,
                'name': 'Conta Poupança'
            }
        ]
        
        callback_data = {
            'item_id': 'item-abc123',
            'connector_name': 'Banco do Brasil'
        }
        response = self.client.post(
            reverse('banking:pluggy-callback'),
            callback_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['accounts']), 2)
        
        # Verify accounts were created
        accounts = BankAccount.objects.filter(company=self.company)
        self.assertEqual(accounts.count(), 2)
        
        # Check first account
        acc1 = accounts.get(external_account_id='acc-001')
        self.assertEqual(acc1.account_type, 'checking')
        self.assertEqual(acc1.account_number, '12345')
        self.assertEqual(acc1.current_balance, Decimal('2500.50'))
        self.assertEqual(acc1.pluggy_item_id, 'item-abc123')
        
        # Check second account
        acc2 = accounts.get(external_account_id='acc-002')
        self.assertEqual(acc2.account_type, 'savings')
        self.assertEqual(acc2.account_number, '54321')
        self.assertEqual(acc2.current_balance, Decimal('5000.00'))
        
    def test_open_banking_fallback_flow(self):
        """Test Open Banking fallback when Pluggy is not available"""
        # Create bank provider
        bank_provider = BankProvider.objects.create(
            name='Banco do Brasil',
            code='001',
            is_open_banking=True,
            is_active=True
        )
        
        # Step 1: Request connection without use_pluggy flag
        connect_data = {
            'bank_code': '001',
            'use_pluggy': False
        }
        
        response = self.client.post(
            reverse('banking:connect-account'),
            connect_data,
            format='json'
        )
        
        # Should get consent flow or direct connection
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        
        if response.data.get('status') == 'consent_required':
            # OAuth flow initiated
            self.assertIn('consent_id', response.data)
            self.assertIn('authorization_url', response.data)
        else:
            # Direct connection (sandbox mode)
            self.assertEqual(response.data['status'], 'success')
            self.assertIn('account_id', response.data)
            
    @patch('apps.banking.tasks.sync_bank_account')
    def test_manual_sync_after_connection(self, mock_sync_task):
        """Test manual sync after bank connection"""
        # Create connected account
        bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='test-001',
            is_active=True
        )
        
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=bank_provider,
            account_type='checking',
            account_number='12345',
            agency='0001',
            pluggy_item_id='item-123',
            external_account_id='acc-123',
            current_balance=Decimal('1000.00'),
            status='active'
        )
        
        # Mock task
        mock_sync_task.delay.return_value = MagicMock(id='task-123')
        
        # Request sync
        response = self.client.post(
            reverse('banking:pluggy-sync', kwargs={'account_id': account.id})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'processing')
        
        # Verify task was called
        mock_sync_task.delay.assert_called_once_with(account.id)
        
    def test_account_disconnection(self):
        """Test disconnecting a bank account"""
        # Create connected account
        bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='test-001',
            is_active=True
        )
        
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=bank_provider,
            account_type='checking',
            account_number='12345',
            agency='0001',
            pluggy_item_id='item-123',
            status='active',
            is_active=True
        )
        
        # Disconnect account
        response = self.client.delete(
            reverse('banking:pluggy-disconnect', kwargs={'account_id': account.id})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify account is deactivated
        account.refresh_from_db()
        self.assertEqual(account.status, 'inactive')
        self.assertFalse(account.is_active)
        
    def test_error_handling_invalid_credentials(self):
        """Test error handling for invalid credentials"""
        # This would test the UI flow when user enters wrong credentials
        # Implementation depends on how Pluggy Connect handles errors
        pass
        
    def test_concurrent_connections(self):
        """Test handling multiple concurrent bank connections"""
        # This would test what happens when user tries to connect
        # multiple banks at the same time
        pass


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class BankSyncIntegrationTestCase(TransactionTestCase):
    """Test bank sync integration with Celery tasks"""
    
    def setUp(self):
        # Create test user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user
        )
        
        # Create bank account
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='pluggy_201',
            is_active=True
        )
        
        self.account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            account_number='12345',
            agency='0001',
            pluggy_item_id='item-123',
            external_account_id='acc-123',
            status='active'
        )
        
    @patch('apps.banking.pluggy_sync_service.PluggyClient')
    def test_automatic_sync_task(self, mock_client_class):
        """Test automatic sync via Celery task"""
        from apps.banking.tasks import sync_bank_account
        
        # Mock client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock account data
        mock_client.get_account.return_value = {
            'id': 'acc-123',
            'balance': 3000.00
        }
        
        # Mock transactions
        mock_client.get_transactions.return_value = {
            'results': [
                {
                    'id': 'tx-001',
                    'description': 'Salary',
                    'amount': 5000.00,
                    'date': timezone.now().isoformat(),
                    'type': 'CREDIT'
                }
            ],
            'totalPages': 1,
            'page': 1
        }
        
        # Run sync task
        result = sync_bank_account(self.account.id)
        
        # Verify
        self.assertTrue(result['success'])
        self.assertEqual(result['transactions_synced'], 1)
        
        # Check database
        self.account.refresh_from_db()
        self.assertEqual(self.account.current_balance, Decimal('3000.00'))
        self.assertIsNotNone(self.account.last_sync_at)
        
    def test_periodic_sync_task(self):
        """Test periodic sync for all accounts"""
        from apps.banking.tasks import sync_all_accounts
        
        # This would test the periodic task that syncs all accounts
        # Implementation depends on task configuration
        pass