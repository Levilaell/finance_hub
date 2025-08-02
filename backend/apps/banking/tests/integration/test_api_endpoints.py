"""
Integration tests for banking API endpoints
"""
import json
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.banking.models import (
    PluggyConnector,
    PluggyItem,
    BankAccount,
    Transaction,
    TransactionCategory
)
from apps.banking.tests.factories.banking_factories import (
    PluggyConnectorFactory,
    PluggyItemFactory,
    BankAccountFactory,
    TransactionFactory,
    TransactionCategoryFactory
)
from apps.companies.tests.factories import CompanyFactory, UserFactory
from rest_framework_simplejwt.tokens import RefreshToken


class BankingAPITestCase(TestCase):
    """Base test case for banking API tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.company = CompanyFactory(owner=self.user)
        
        # Create JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # Authenticate client
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')


class PluggyConnectorAPITest(BankingAPITestCase):
    """Test cases for PluggyConnector API endpoints"""
    
    def setUp(self):
        super().setUp()
        self.url_list = reverse('banking:connector-list')
        self.connector = PluggyConnectorFactory(
            type='PERSONAL_BANK',
            country='BR',
            is_open_finance=True
        )
    
    def test_list_connectors(self):
        """Test listing connectors"""
        # Create additional connectors
        PluggyConnectorFactory.create_batch(3)
        
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
    
    def test_filter_connectors_by_type(self):
        """Test filtering connectors by type"""
        PluggyConnectorFactory(type='BUSINESS_BANK')
        PluggyConnectorFactory(type='INVESTMENT')
        
        response = self.client.get(self.url_list, {'type': 'PERSONAL_BANK'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], 'PERSONAL_BANK')
    
    def test_filter_connectors_by_open_finance(self):
        """Test filtering connectors by Open Finance status"""
        PluggyConnectorFactory(is_open_finance=False)
        
        response = self.client.get(self.url_list, {'is_open_finance': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertTrue(response.data[0]['is_open_finance'])
    
    def test_filter_connectors_by_country(self):
        """Test filtering connectors by country"""
        PluggyConnectorFactory(country='US')
        
        response = self.client.get(self.url_list, {'country': 'BR'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['country'], 'BR')
    
    @patch('apps.banking.views.PluggyClient')
    def test_sync_connectors(self, mock_client_class):
        """Test syncing connectors from Pluggy API"""
        # Mock Pluggy client
        mock_client = Mock()
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = Mock(return_value=None)
        
        mock_connectors = [
            {
                'id': 201,
                'name': 'New Bank',
                'type': 'PERSONAL_BANK',
                'country': 'BR',
                'institutionUrl': 'https://newbank.com',
                'imageUrl': 'https://newbank.com/logo.png',
                'primaryColor': '#FF0000',
                'hasMFA': True,
                'oauth': False,
                'isOpenFinance': True,
                'sandbox': False,
                'products': ['ACCOUNTS', 'TRANSACTIONS'],
                'credentials': []
            }
        ]
        mock_client.get_connectors.return_value = mock_connectors
        
        url = reverse('banking:connector-sync')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['created'], 1)
        
        # Verify connector was created
        connector = PluggyConnector.objects.get(pluggy_id=201)
        self.assertEqual(connector.name, 'New Bank')
        self.assertTrue(connector.has_mfa)
        self.assertTrue(connector.is_open_finance)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated access is forbidden"""
        self.client.credentials()  # Remove auth
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PluggyItemAPITest(BankingAPITestCase):
    """Test cases for PluggyItem API endpoints"""
    
    def setUp(self):
        super().setUp()
        self.url_list = reverse('banking:item-list')
        self.connector = PluggyConnectorFactory()
        self.item = PluggyItemFactory(
            company=self.company,
            connector=self.connector
        )
        self.url_detail = reverse('banking:item-detail', kwargs={'pk': self.item.id})
    
    def test_list_items(self):
        """Test listing items for user's company"""
        # Create items for other company
        other_company = CompanyFactory()
        PluggyItemFactory(company=other_company)
        
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.item.id))
    
    def test_retrieve_item(self):
        """Test retrieving single item"""
        response = self.client.get(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.item.id))
        self.assertIn('connector', response.data)
        self.assertIn('accounts_count', response.data)
    
    @patch('apps.banking.integrations.pluggy.client.PluggyClient')
    @patch('apps.banking.tasks.sync_bank_account.delay')
    def test_sync_item(self, mock_task, mock_client_class):
        """Test syncing a specific item"""
        # Mock Pluggy client
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.update_item.return_value = {
            'id': self.item.pluggy_item_id,
            'status': 'UPDATING',
            'executionStatus': 'IN_PROGRESS',
            'updatedAt': timezone.now().isoformat()
        }
        
        # Mock task
        mock_task.return_value.id = 'test-task-id'
        
        url = reverse('banking:item-sync', kwargs={'pk': self.item.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['task_id'], 'test-task-id')
        
        # Verify update was called
        mock_client.update_item.assert_called_once_with(self.item.pluggy_item_id, {})
        mock_task.assert_called_once_with(str(self.item.id), force_update=True)
    
    @patch('apps.banking.integrations.pluggy.client.PluggyClient')
    def test_send_mfa(self, mock_client_class):
        """Test sending MFA parameters"""
        # Set item to waiting for user input
        self.item.status = 'WAITING_USER_INPUT'
        self.item.save()
        
        # Mock Pluggy client
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.update_item_mfa.return_value = {
            'id': self.item.pluggy_item_id,
            'status': 'UPDATING',
            'executionStatus': 'IN_PROGRESS'
        }
        
        url = reverse('banking:item-send-mfa', kwargs={'pk': self.item.id})
        mfa_data = {'token': '123456'}
        response = self.client.post(url, mfa_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify MFA was sent
        mock_client.update_item_mfa.assert_called_once_with(
            self.item.pluggy_item_id,
            mfa_data
        )
    
    def test_send_mfa_wrong_status(self):
        """Test sending MFA when item is not waiting for input"""
        self.item.status = 'UPDATED'
        self.item.save()
        
        url = reverse('banking:item-send-mfa', kwargs={'pk': self.item.id})
        response = self.client.post(url, {'token': '123456'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    @patch('apps.banking.integrations.pluggy.client.PluggyClient')
    def test_disconnect_item(self, mock_client_class):
        """Test disconnecting an item"""
        # Create accounts for the item
        BankAccountFactory.create_batch(2, item=self.item, company=self.company)
        
        # Mock Pluggy client
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        url = reverse('banking:item-disconnect', kwargs={'pk': self.item.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify item was marked as deleted
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, 'DELETED')
        
        # Verify accounts were soft deleted
        self.assertEqual(
            BankAccount.objects.filter(item=self.item, is_active=True).count(),
            0
        )
        
        # Verify delete was called on Pluggy
        mock_client.delete_item.assert_called_once_with(self.item.pluggy_item_id)


class BankAccountAPITest(BankingAPITestCase):
    """Test cases for BankAccount API endpoints"""
    
    def setUp(self):
        super().setUp()
        self.url_list = reverse('banking:account-list')
        self.item = PluggyItemFactory(company=self.company)
        self.account = BankAccountFactory(
            item=self.item,
            company=self.company,
            balance=Decimal('1000.00')
        )
        self.url_detail = reverse('banking:account-detail', kwargs={'pk': self.account.id})
    
    def test_list_accounts(self):
        """Test listing bank accounts"""
        # Create accounts for other company
        other_company = CompanyFactory()
        BankAccountFactory(company=other_company)
        
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.account.id))
    
    def test_retrieve_account(self):
        """Test retrieving single account"""
        response = self.client.get(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.account.id))
        self.assertIn('connector', response.data)
        self.assertIn('display_name', response.data)
        self.assertIn('masked_number', response.data)
    
    def test_filter_accounts_by_type(self):
        """Test filtering accounts by type"""
        BankAccountFactory(company=self.company, type='CREDIT')
        BankAccountFactory(company=self.company, type='INVESTMENT')
        
        response = self.client.get(self.url_list, {'type': 'BANK'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], 'BANK')
    
    def test_account_summary(self):
        """Test account summary endpoint"""
        # Create multiple accounts
        BankAccountFactory(
            company=self.company,
            type='BANK',
            balance=Decimal('2000.00')
        )
        BankAccountFactory(
            company=self.company,
            type='CREDIT',
            balance=Decimal('-500.00')
        )
        
        url = reverse('banking:account-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_accounts'], 3)
        self.assertEqual(response.data['bank_accounts']['count'], 2)
        self.assertEqual(
            Decimal(response.data['bank_accounts']['total_balance']),
            Decimal('3000.00')
        )
        self.assertEqual(response.data['credit_accounts']['count'], 1)
        self.assertEqual(
            Decimal(response.data['credit_accounts']['total_balance']),
            Decimal('-500.00')
        )


class TransactionAPITest(BankingAPITestCase):
    """Test cases for Transaction API endpoints"""
    
    def setUp(self):
        super().setUp()
        self.url_list = reverse('banking:transaction-list')
        self.account = BankAccountFactory(company=self.company)
        self.category = TransactionCategoryFactory(company=self.company)
        self.transaction = TransactionFactory(
            account=self.account,
            company=self.company,
            category=self.category,
            amount=Decimal('100.00'),
            type='DEBIT'
        )
        self.url_detail = reverse('banking:transaction-detail', kwargs={'pk': self.transaction.id})
    
    def test_list_transactions(self):
        """Test listing transactions with pagination"""
        # Create additional transactions
        TransactionFactory.create_batch(
            55,
            account=self.account,
            company=self.company
        )
        
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 56)
        self.assertEqual(len(response.data['results']), 50)  # Default page size
        self.assertIn('next', response.data)
    
    def test_filter_transactions_by_account(self):
        """Test filtering transactions by account"""
        other_account = BankAccountFactory(company=self.company)
        TransactionFactory(account=other_account, company=self.company)
        
        response = self.client.get(self.url_list, {'account_id': str(self.account.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(
            response.data['results'][0]['id'],
            str(self.transaction.id)
        )
    
    def test_filter_transactions_by_date_range(self):
        """Test filtering transactions by date range"""
        # Create transactions with different dates
        old_transaction = TransactionFactory(
            account=self.account,
            company=self.company,
            date=timezone.now() - timedelta(days=60)
        )
        
        start_date = (timezone.now() - timedelta(days=30)).date()
        end_date = timezone.now().date()
        
        response = self.client.get(self.url_list, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(
            response.data['results'][0]['id'],
            str(self.transaction.id)
        )
    
    def test_filter_transactions_by_type(self):
        """Test filtering transactions by type"""
        TransactionFactory(
            account=self.account,
            company=self.company,
            type='CREDIT'
        )
        
        response = self.client.get(self.url_list, {'type': 'DEBIT'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['type'], 'DEBIT')
    
    def test_search_transactions(self):
        """Test searching transactions by description"""
        self.transaction.description = 'Coffee Shop Purchase'
        self.transaction.save()
        
        TransactionFactory(
            account=self.account,
            company=self.company,
            description='Grocery Store'
        )
        
        response = self.client.get(self.url_list, {'search': 'coffee'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertIn('Coffee', response.data['results'][0]['description'])
    
    def test_create_manual_transaction(self):
        """Test creating a manual transaction"""
        data = {
            'account': str(self.account.id),
            'type': 'DEBIT',
            'amount': '50.00',
            'description': 'Manual transaction',
            'date': timezone.now().isoformat(),
            'category': str(self.category.id)
        }
        
        response = self.client.post(self.url_list, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 2)
        
        new_transaction = Transaction.objects.get(id=response.data['id'])
        self.assertEqual(new_transaction.description, 'Manual transaction')
        self.assertEqual(new_transaction.amount, Decimal('50.00'))
    
    def test_update_transaction_category(self):
        """Test updating transaction category"""
        new_category = TransactionCategoryFactory(company=self.company)
        
        data = {'category': str(new_category.id)}
        response = self.client.patch(self.url_detail, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.category, new_category)
    
    def test_bulk_categorize_transactions(self):
        """Test bulk categorization of transactions"""
        # Create additional transactions
        trans2 = TransactionFactory(account=self.account, company=self.company)
        trans3 = TransactionFactory(account=self.account, company=self.company)
        
        new_category = TransactionCategoryFactory(company=self.company)
        
        url = reverse('banking:transaction-bulk-categorize')
        data = {
            'transaction_ids': [
                str(self.transaction.id),
                str(trans2.id),
                str(trans3.id)
            ],
            'category_id': str(new_category.id)
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated'], 3)
        
        # Verify all transactions were updated
        for trans in [self.transaction, trans2, trans3]:
            trans.refresh_from_db()
            self.assertEqual(trans.category, new_category)
    
    def test_soft_delete_transaction(self):
        """Test soft deleting a transaction"""
        response = self.client.delete(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.transaction.refresh_from_db()
        self.assertTrue(self.transaction.is_deleted)
        self.assertIsNotNone(self.transaction.deleted_at)
        
        # Verify it's excluded from active transactions
        active_transactions = Transaction.active.filter(id=self.transaction.id)
        self.assertEqual(active_transactions.count(), 0)


class TransactionCategoryAPITest(BankingAPITestCase):
    """Test cases for TransactionCategory API endpoints"""
    
    def setUp(self):
        super().setUp()
        self.url_list = reverse('banking:category-list')
        self.category = TransactionCategoryFactory(company=self.company)
        self.url_detail = reverse('banking:category-detail', kwargs={'pk': self.category.id})
    
    def test_list_categories(self):
        """Test listing categories including system categories"""
        # Create system category
        system_category = TransactionCategoryFactory(
            company=None,
            is_system=True
        )
        
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Check both company and system categories are returned
        category_ids = [c['id'] for c in response.data]
        self.assertIn(str(self.category.id), category_ids)
        self.assertIn(str(system_category.id), category_ids)
    
    def test_create_category(self):
        """Test creating a new category"""
        data = {
            'name': 'New Category',
            'type': 'expense',
            'icon': '💰',
            'color': '#FF5733'
        }
        
        response = self.client.post(self.url_list, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        new_category = TransactionCategory.objects.get(id=response.data['id'])
        self.assertEqual(new_category.name, 'New Category')
        self.assertEqual(new_category.company, self.company)
        self.assertEqual(new_category.slug, 'new-category')
    
    def test_create_subcategory(self):
        """Test creating a subcategory"""
        parent = TransactionCategoryFactory(company=self.company)
        
        data = {
            'name': 'Subcategory',
            'type': 'expense',
            'parent': str(parent.id)
        }
        
        response = self.client.post(self.url_list, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        subcategory = TransactionCategory.objects.get(id=response.data['id'])
        self.assertEqual(subcategory.parent, parent)
        self.assertEqual(response.data['full_name'], f'{parent.name} > Subcategory')
    
    def test_update_category(self):
        """Test updating a category"""
        data = {
            'name': 'Updated Name',
            'color': '#00FF00'
        }
        
        response = self.client.patch(self.url_detail, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Updated Name')
        self.assertEqual(self.category.color, '#00FF00')
    
    def test_delete_category(self):
        """Test deleting a category"""
        response = self.client.delete(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        self.assertFalse(
            TransactionCategory.objects.filter(id=self.category.id).exists()
        )
    
    def test_cannot_delete_category_with_transactions(self):
        """Test that categories with transactions cannot be deleted"""
        # Create transaction using this category
        TransactionFactory(
            company=self.company,
            category=self.category
        )
        
        response = self.client.delete(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Category should still exist
        self.assertTrue(
            TransactionCategory.objects.filter(id=self.category.id).exists()
        )