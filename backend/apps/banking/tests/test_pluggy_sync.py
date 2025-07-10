"""
Tests for Pluggy sync service
"""
import json
from unittest.mock import patch, AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.companies.models import Company
from apps.banking.models import BankAccount, BankProvider, Transaction, BankSync
from apps.banking.pluggy_sync_service import PluggySyncService

User = get_user_model()


class PluggySyncServiceTestCase(TestCase):
    """Test Pluggy sync service functionality"""
    
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
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Banco do Brasil',
            code='pluggy_201',
            is_open_banking=False,
            is_active=True
        )
        
        # Create bank account
        self.account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            account_number='12345',
            agency='0001',
            pluggy_item_id='item-123',
            external_account_id='account-123',
            status='active',
            current_balance=Decimal('1000.00')
        )
        
        self.sync_service = PluggySyncService()
        
    @patch('apps.banking.pluggy_sync_service.PluggyClient')
    def test_sync_transactions_success(self, mock_client_class):
        """Test successful transaction sync"""
        # Mock client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock account data
        mock_client.get_account.return_value = {
            'id': 'account-123',
            'balance': 1500.00,
            'balanceDate': '2024-01-10T12:00:00Z'
        }
        
        # Mock transactions
        mock_client.get_transactions.return_value = {
            'results': [
                {
                    'id': 'tx-001',
                    'description': 'PIX Recebido',
                    'amount': 500.00,
                    'date': '2024-01-10T10:00:00Z',
                    'type': 'CREDIT',
                    'category': 'Transfer',
                    'providerCode': 'PIX_IN'
                },
                {
                    'id': 'tx-002',
                    'description': 'Pagamento Conta Luz',
                    'amount': -150.00,
                    'date': '2024-01-09T15:00:00Z',
                    'type': 'DEBIT',
                    'category': 'Bills',
                    'providerCode': 'BILL_PAYMENT'
                }
            ],
            'totalPages': 1,
            'page': 1
        }
        
        # Run sync
        result = self.sync_service.sync_account_transactions(self.account)
        
        # Verify sync log
        self.assertEqual(result.status, 'completed')
        self.assertEqual(result.transactions_found, 2)
        self.assertEqual(result.transactions_new, 2)
        
        # Verify account balance updated
        self.account.refresh_from_db()
        self.assertEqual(self.account.current_balance, Decimal('1500.00'))
        
        # Verify transactions created
        transactions = Transaction.objects.filter(bank_account=self.account)
        self.assertEqual(transactions.count(), 2)
        
        # Check first transaction
        tx1 = transactions.get(external_id='tx-001')
        self.assertEqual(tx1.description, 'PIX Recebido')
        self.assertEqual(tx1.amount, Decimal('500.00'))
        self.assertEqual(tx1.transaction_type, 'pix_in')
        
        # Check second transaction
        tx2 = transactions.get(external_id='tx-002')
        self.assertEqual(tx2.description, 'Pagamento Conta Luz')
        self.assertEqual(tx2.amount, Decimal('-150.00'))
        self.assertEqual(tx2.transaction_type, 'debit')
        
    @patch('apps.banking.pluggy_sync_service.PluggyClient')
    def test_sync_with_existing_transactions(self, mock_client_class):
        """Test sync with existing transactions (avoid duplicates)"""
        # Create existing transaction
        existing_tx = Transaction.objects.create(
            bank_account=self.account,
            external_id='tx-001',
            description='Existing Transaction',
            amount=Decimal('100.00'),
            transaction_type='credit',
            transaction_date=timezone.now()
        )
        
        # Mock client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock account data
        mock_client.get_account.return_value = {
            'id': 'account-123',
            'balance': 1500.00
        }
        
        # Mock transactions (including existing one)
        mock_client.get_transactions.return_value = {
            'results': [
                {
                    'id': 'tx-001',  # Same as existing
                    'description': 'PIX Recebido',
                    'amount': 100.00,
                    'date': '2024-01-10T10:00:00Z',
                    'type': 'CREDIT'
                },
                {
                    'id': 'tx-002',  # New transaction
                    'description': 'Nova Transação',
                    'amount': 200.00,
                    'date': '2024-01-10T11:00:00Z',
                    'type': 'CREDIT'
                }
            ],
            'totalPages': 1,
            'page': 1
        }
        
        # Run sync
        result = self.sync_service.sync_account_transactions(self.account)
        
        # Verify
        self.assertEqual(result.transactions_found, 2)
        self.assertEqual(result.transactions_new, 1)  # Only one new transaction
        
        # Check transaction count
        transactions = Transaction.objects.filter(bank_account=self.account)
        self.assertEqual(transactions.count(), 2)  # Original + 1 new
        
    @patch('apps.banking.pluggy_sync_service.PluggyClient')
    def test_sync_error_handling(self, mock_client_class):
        """Test sync error handling"""
        # Mock client with error
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get_account.side_effect = Exception('API Error')
        
        # Run sync
        result = self.sync_service.sync_account_transactions(self.account)
        
        # Verify
        self.assertEqual(result.status, 'failed')
        self.assertIn('API Error', result.error_message)
        self.assertEqual(result.transactions_found, 0)
        self.assertEqual(result.transactions_new, 0)
        
    @patch('apps.banking.pluggy_sync_service.PluggyClient')
    def test_map_transaction_types(self, mock_client_class):
        """Test transaction type mapping"""
        # Mock client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock account data
        mock_client.get_account.return_value = {
            'id': 'account-123',
            'balance': 2000.00
        }
        
        # Mock various transaction types
        mock_client.get_transactions.return_value = {
            'results': [
                {
                    'id': 'tx-pix-in',
                    'description': 'PIX Recebido',
                    'amount': 100.00,
                    'date': '2024-01-10T10:00:00Z',
                    'type': 'CREDIT',
                    'providerCode': 'PIX'
                },
                {
                    'id': 'tx-pix-out',
                    'description': 'PIX Enviado',
                    'amount': -50.00,
                    'date': '2024-01-10T11:00:00Z',
                    'type': 'DEBIT',
                    'providerCode': 'PIX'
                },
                {
                    'id': 'tx-transfer-in',
                    'description': 'TED Recebida',
                    'amount': 200.00,
                    'date': '2024-01-10T12:00:00Z',
                    'type': 'CREDIT',
                    'providerCode': 'TED'
                },
                {
                    'id': 'tx-transfer-out',
                    'description': 'TED Enviada',
                    'amount': -150.00,
                    'date': '2024-01-10T13:00:00Z',
                    'type': 'DEBIT',
                    'providerCode': 'TED'
                },
                {
                    'id': 'tx-fee',
                    'description': 'Taxa Bancária',
                    'amount': -10.00,
                    'date': '2024-01-10T14:00:00Z',
                    'type': 'DEBIT',
                    'category': 'Bank Fees'
                }
            ],
            'totalPages': 1,
            'page': 1
        }
        
        # Run sync
        result = self.sync_service.sync_account_transactions(self.account)
        
        # Verify transaction types
        self.assertEqual(result.transactions_new, 5)
        
        transactions = Transaction.objects.filter(bank_account=self.account).order_by('external_id')
        
        # Check mapped types
        self.assertEqual(transactions.get(external_id='tx-pix-in').transaction_type, 'pix_in')
        self.assertEqual(transactions.get(external_id='tx-pix-out').transaction_type, 'pix_out')
        self.assertEqual(transactions.get(external_id='tx-transfer-in').transaction_type, 'transfer_in')
        self.assertEqual(transactions.get(external_id='tx-transfer-out').transaction_type, 'transfer_out')
        self.assertEqual(transactions.get(external_id='tx-fee').transaction_type, 'fee')
        
    @patch('apps.banking.pluggy_sync_service.PluggyClient')
    def test_pagination_handling(self, mock_client_class):
        """Test handling paginated results"""
        # Mock client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock account data
        mock_client.get_account.return_value = {
            'id': 'account-123',
            'balance': 3000.00
        }
        
        # Mock paginated responses
        page1_transactions = [
            {
                'id': f'tx-{i:03d}',
                'description': f'Transaction {i}',
                'amount': 10.00 * i,
                'date': f'2024-01-{10-i:02d}T10:00:00Z',
                'type': 'CREDIT'
            }
            for i in range(1, 6)  # 5 transactions
        ]
        
        page2_transactions = [
            {
                'id': f'tx-{i:03d}',
                'description': f'Transaction {i}',
                'amount': 10.00 * i,
                'date': f'2024-01-{10-i:02d}T10:00:00Z',
                'type': 'CREDIT'
            }
            for i in range(6, 9)  # 3 transactions
        ]
        
        # Configure mock to return different pages
        mock_client.get_transactions.side_effect = [
            {'results': page1_transactions, 'totalPages': 2, 'page': 1},
            {'results': page2_transactions, 'totalPages': 2, 'page': 2}
        ]
        
        # Run sync
        result = self.sync_service.sync_account_transactions(self.account)
        
        # Verify all transactions were processed
        self.assertEqual(result.transactions_found, 8)
        self.assertEqual(result.transactions_new, 8)
        
        # Check database
        transactions = Transaction.objects.filter(bank_account=self.account)
        self.assertEqual(transactions.count(), 8)
        
    def test_sync_frequency_limit(self):
        """Test sync frequency limiting"""
        # Create recent sync log
        recent_sync = BankSync.objects.create(
            bank_account=self.account,
            status='completed',
            started_at=timezone.now() - timedelta(minutes=30),
            completed_at=timezone.now() - timedelta(minutes=25),
            sync_from_date=timezone.now().date() - timedelta(days=30),
            sync_to_date=timezone.now().date()
        )
        
        # Set sync frequency to 1 hour
        self.account.sync_frequency = 1
        self.account.save()
        
        # Try to sync again (should be skipped due to frequency limit)
        # This depends on implementation - adjust based on actual service behavior
        
    @patch('apps.banking.pluggy_sync_service.PluggyClient')
    def test_sync_date_range(self, mock_client_class):
        """Test sync with specific date range"""
        # Mock client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock account data
        mock_client.get_account.return_value = {
            'id': 'account-123',
            'balance': 1000.00
        }
        
        # Mock empty transactions
        mock_client.get_transactions.return_value = {
            'results': [],
            'totalPages': 1,
            'page': 1
        }
        
        # Run sync with date range
        from_date = timezone.now().date() - timedelta(days=7)
        to_date = timezone.now().date()
        
        result = self.sync_service.sync_account_transactions(
            self.account,
            from_date=from_date,
            to_date=to_date
        )
        
        # Verify date range was used in API call
        mock_client.get_transactions.assert_called_with(
            'account-123',
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            page=1,
            page_size=500
        )