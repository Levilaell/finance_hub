"""
Banking services tests
"""
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.banking.models import BankAccount, BankProvider, Transaction
from apps.banking.services import BankingSyncService, OpenBankingService
from apps.companies.models import Company, SubscriptionPlan

User = get_user_model()


class BankingServicesTestCase(TestCase):
    """Base test case for banking services"""
    
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPass123!'
        )
        
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            plan_type='starter',
            price_monthly=29.90
        )
        
        # Create company
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            company_type='mei',
            business_sector='services',
            subscription_plan=self.plan
        )
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='001',
            color='#000000'
        )
        
        # Create bank account
        self.bank_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='567890',
            external_account_id='ext_123456',
            access_token='mock_token'
        )


class OpenBankingServiceTest(BankingServicesTestCase):
    """Test Open Banking service"""
    
    def setUp(self):
        super().setUp()
        self.service = OpenBankingService()
    
    def test_connect_account(self):
        """Test connecting bank account"""
        credentials = {
            'username': 'testuser',
            'password': 'testpass',
            'agency': '1234',
            'account': '567890'
        }
        
        result = self.service.connect_account('001', credentials)
        
        self.assertIn('access_token', result)
        self.assertIn('refresh_token', result)
        self.assertIn('account_info', result)
        self.assertEqual(result['account_info']['agency'], '1234')
    
    def test_get_account_info(self):
        """Test getting account information"""
        result = self.service.get_account_info(self.bank_account)
        
        self.assertIn('balance', result)
        self.assertIn('available_balance', result)
        self.assertIn('account_status', result)
        self.assertEqual(result['account_status'], 'active')
    
    def test_get_transactions(self):
        """Test fetching transactions"""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        transactions = self.service.get_transactions(
            self.bank_account,
            start_date,
            end_date
        )
        
        self.assertIsInstance(transactions, list)
        if transactions:
            transaction = transactions[0]
            self.assertIn('external_id', transaction)
            self.assertIn('amount', transaction)
            self.assertIn('description', transaction)
            self.assertIn('transaction_date', transaction)


class BankingSyncServiceTest(BankingServicesTestCase):
    """Test Banking Sync service"""
    
    def setUp(self):
        super().setUp()
        self.service = BankingSyncService()
    
    @patch.object(OpenBankingService, 'get_account_info')
    @patch.object(OpenBankingService, 'get_transactions')
    def test_sync_account(self, mock_get_transactions, mock_get_account_info):
        """Test syncing bank account"""
        # Mock account info
        mock_get_account_info.return_value = {
            'balance': 5000.00,
            'available_balance': 4500.00,
            'account_status': 'active'
        }
        
        # Mock transactions
        mock_get_transactions.return_value = [
            {
                'external_id': 'trans_001',
                'transaction_type': 'credit',
                'amount': 1000.00,
                'description': 'Payment received',
                'transaction_date': timezone.now().isoformat(),
                'counterpart_name': 'Client ABC'
            },
            {
                'external_id': 'trans_002',
                'transaction_type': 'debit',
                'amount': -250.00,
                'description': 'Office supplies',
                'transaction_date': (timezone.now() - timedelta(days=1)).isoformat(),
                'counterpart_name': 'Office Store'
            }
        ]
        
        # Run sync
        sync_log = self.service.sync_account(self.bank_account, days_back=7)
        
        # Verify sync log
        self.assertEqual(sync_log.status, 'completed')
        self.assertEqual(sync_log.transactions_found, 2)
        self.assertEqual(sync_log.transactions_new, 2)
        
        # Verify account was updated
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.current_balance, Decimal('5000.00'))
        self.assertEqual(self.bank_account.available_balance, Decimal('4500.00'))
        
        # Verify transactions were created
        transactions = Transaction.objects.filter(bank_account=self.bank_account)
        self.assertEqual(transactions.count(), 2)
        
        # Check transaction details
        trans1 = transactions.get(external_id='trans_001')
        self.assertEqual(trans1.amount, Decimal('1000.00'))
        self.assertEqual(trans1.description, 'Payment received')
        
    def test_sync_account_failure(self):
        """Test sync failure handling"""
        # Remove access token to cause failure
        self.bank_account.access_token = ''
        self.bank_account.save()
        
        # Run sync
        with self.assertRaises(Exception):
            self.service.sync_account(self.bank_account)
        
        # Verify account status
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.status, 'error')
    
    @patch.object(OpenBankingService, 'get_account_info')
    @patch.object(OpenBankingService, 'get_transactions')
    def test_sync_duplicate_transactions(self, mock_get_transactions, mock_get_account_info):
        """Test handling duplicate transactions"""
        # Create existing transaction
        Transaction.objects.create(
            bank_account=self.bank_account,
            external_id='trans_001',
            transaction_type='credit',
            amount=Decimal('1000.00'),
            description='Existing transaction',
            transaction_date=timezone.now()
        )
        
        # Mock returns
        mock_get_account_info.return_value = {
            'balance': 5000.00,
            'available_balance': 5000.00
        }
        
        mock_get_transactions.return_value = [
            {
                'external_id': 'trans_001',
                'transaction_type': 'credit',
                'amount': 1000.00,
                'description': 'Updated description',
                'transaction_date': timezone.now().isoformat(),
                'counterpart_name': 'Client ABC'
            }
        ]
        
        # Run sync
        sync_log = self.service.sync_account(self.bank_account)
        
        # Verify only update occurred
        self.assertEqual(sync_log.transactions_found, 1)
        self.assertEqual(sync_log.transactions_new, 0)
        self.assertEqual(sync_log.transactions_updated, 1)
        
        # Verify transaction was updated
        transaction = Transaction.objects.get(external_id='trans_001')
        self.assertEqual(transaction.description, 'Updated description')