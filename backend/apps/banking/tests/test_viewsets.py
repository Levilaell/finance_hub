"""
Comprehensive tests for Banking app ViewSets
Testing API endpoints, permissions, and business logic
"""
import json
import uuid
from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import patch, Mock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.banking.models import (
    BankProvider,
    BankAccount,
    TransactionCategory,
    Transaction,
    Budget,
    FinancialGoal,
    BankSync
)
from apps.companies.models import Company, SubscriptionPlan

User = get_user_model()


class BankingAPITestCase(APITestCase):
    """Base test case for banking API tests"""
    
    def setUp(self):
        """Set up test data"""
        # Create subscription plan
        self.subscription_plan = SubscriptionPlan.objects.create(
            name='Basic',
            price=Decimal('29.90'),
            max_accounts=5,
            max_transactions=1000
        )
        
        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            document_number='12345678000199',
            subscription_plan=self.subscription_plan,
            owner=self.user
        )
        
        # Associate user with company
        self.user.company = self.company
        self.user.save()
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='TEST001'
        )
        
        # Create category
        self.category = TransactionCategory.objects.create(
            name='Test Category',
            slug='test-category',
            category_type='expense'
        )
        
        # Create bank account
        self.bank_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='567890',
            status='active',
            current_balance=Decimal('1000.00')
        )
        
        # Setup API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)


class BankAccountViewSetTest(BankingAPITestCase):
    """Test BankAccountViewSet functionality"""
    
    def test_list_bank_accounts(self):
        """Test listing bank accounts for authenticated user's company"""
        url = reverse('bankaccount-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.bank_account.id)
    
    def test_list_accounts_company_isolation(self):
        """Test that users only see their company's accounts"""
        # Create another user and company
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            name='Other User'
        )
        other_company = Company.objects.create(
            name='Other Company',
            document_number='98765432000199',
            subscription_plan=self.subscription_plan,
            owner=other_user
        )
        other_user.company = other_company
        other_user.save()
        
        # Create account for other company
        BankAccount.objects.create(
            company=other_company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='5678',
            account_number='123456'
        )
        
        # Test that original user only sees their company's account
        url = reverse('bankaccount-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.bank_account.id)
    
    def test_create_bank_account(self):
        """Test creating a new bank account"""
        url = reverse('bankaccount-list')
        data = {
            'bank_provider': self.bank_provider.id,
            'account_type': 'savings',
            'agency': '9999',
            'account_number': '888888',
            'nickname': 'Savings Account'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BankAccount.objects.count(), 2)
        
        new_account = BankAccount.objects.get(id=response.data['id'])
        self.assertEqual(new_account.company, self.company)
        self.assertEqual(new_account.nickname, 'Savings Account')
    
    def test_retrieve_bank_account(self):
        """Test retrieving a specific bank account"""
        url = reverse('bankaccount-detail', kwargs={'pk': self.bank_account.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.bank_account.id)
        self.assertEqual(response.data['agency'], '1234')
    
    def test_update_bank_account(self):
        """Test updating a bank account"""
        url = reverse('bankaccount-detail', kwargs={'pk': self.bank_account.id})
        data = {
            'nickname': 'Updated Account Name',
            'is_primary': True
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.bank_account.refresh_from_db()
        self.assertEqual(self.bank_account.nickname, 'Updated Account Name')
        self.assertTrue(self.bank_account.is_primary)
    
    def test_delete_bank_account(self):
        """Test deleting a bank account"""
        url = reverse('bankaccount-detail', kwargs={'pk': self.bank_account.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(BankAccount.objects.filter(id=self.bank_account.id).exists())
    
    @patch('apps.banking.services.BankingSyncService.sync_account')
    def test_sync_account_action(self, mock_sync):
        """Test manual account sync action"""
        # Mock sync service
        mock_sync_result = Mock()
        mock_sync_result.id = 'sync_123'
        mock_sync.return_value = mock_sync_result
        
        url = reverse('bankaccount-sync', kwargs={'pk': self.bank_account.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['sync_id'], 'sync_123')
        mock_sync.assert_called_once_with(self.bank_account)
    
    def test_accounts_summary_action(self):
        """Test accounts summary action"""
        # Create additional account
        BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='savings',
            agency='5555',
            account_number='999999',
            status='active',
            current_balance=Decimal('500.00')
        )
        
        url = reverse('bankaccount-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_accounts'], 2)
        self.assertEqual(response.data['active_accounts'], 2)
        self.assertEqual(response.data['total_balance'], Decimal('1500.00'))
        self.assertEqual(response.data['sync_errors'], 0)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users can't access accounts"""
        self.client.force_authenticate(user=None)
        url = reverse('bankaccount-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TransactionViewSetTest(BankingAPITestCase):
    """Test TransactionViewSet functionality"""
    
    def setUp(self):
        super().setUp()
        # Create test transactions
        self.transaction1 = Transaction.objects.create(
            bank_account=self.bank_account,
            transaction_type='credit',
            amount=Decimal('1000.00'),
            description='Salary',
            transaction_date=timezone.now(),
            category=self.category
        )
        
        self.transaction2 = Transaction.objects.create(
            bank_account=self.bank_account,
            transaction_type='debit',
            amount=Decimal('-50.00'),
            description='Food expense',
            transaction_date=timezone.now() - timedelta(days=1),
            category=self.category
        )
    
    def test_list_transactions(self):
        """Test listing transactions for authenticated user's company"""
        url = reverse('transaction-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Check ordering (newest first)
        self.assertEqual(response.data['results'][0]['id'], str(self.transaction1.id))
    
    def test_transaction_company_isolation(self):
        """Test that users only see their company's transactions"""
        # Create another company and account
        other_company = Company.objects.create(
            name='Other Company',
            document_number='98765432000199',
            subscription_plan=self.subscription_plan,
            owner=User.objects.create_user(
                email='other@example.com',
                password='testpass123',
                name='Other User'
            )
        )
        
        other_account = BankAccount.objects.create(
            company=other_company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='9999',
            account_number='123456'
        )
        
        # Create transaction for other company
        Transaction.objects.create(
            bank_account=other_account,
            transaction_type='credit',
            amount=Decimal('500.00'),
            description='Other transaction',
            transaction_date=timezone.now()
        )
        
        # Test that user only sees their company's transactions
        url = reverse('transaction-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_create_transaction(self):
        """Test creating a new transaction"""
        url = reverse('transaction-list')
        data = {
            'bank_account': self.bank_account.id,
            'transaction_type': 'debit',
            'amount': '-25.00',
            'description': 'Coffee purchase',
            'transaction_date': timezone.now().isoformat(),
            'category': self.category.id
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 3)
        
        new_transaction = Transaction.objects.get(id=response.data['id'])
        self.assertEqual(new_transaction.description, 'Coffee purchase')
        self.assertEqual(new_transaction.amount, Decimal('-25.00'))
    
    def test_transaction_filtering_by_date(self):
        """Test filtering transactions by date range"""
        url = reverse('transaction-list')
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Filter for today only
        response = self.client.get(url, {'start_date': today, 'end_date': today})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.transaction1.id))
    
    def test_transaction_filtering_by_category(self):
        """Test filtering transactions by category"""
        # Create another category and transaction
        other_category = TransactionCategory.objects.create(
            name='Other Category',
            slug='other-category',
            category_type='income'
        )
        
        Transaction.objects.create(
            bank_account=self.bank_account,
            transaction_type='credit',
            amount=Decimal('200.00'),
            description='Other income',
            transaction_date=timezone.now(),
            category=other_category
        )
        
        url = reverse('transaction-list')
        response = self.client.get(url, {'category': self.category.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_transaction_search(self):
        """Test searching transactions by description"""
        url = reverse('transaction-list')
        response = self.client.get(url, {'search': 'Salary'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['description'], 'Salary')
    
    def test_transaction_ordering(self):
        """Test transaction ordering"""
        url = reverse('transaction-list')
        
        # Order by amount ascending
        response = self.client.get(url, {'ordering': 'amount'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        amounts = [Decimal(t['amount']) for t in response.data['results']]
        self.assertEqual(amounts, sorted(amounts))
        
        # Order by amount descending
        response = self.client.get(url, {'ordering': '-amount'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        amounts = [Decimal(t['amount']) for t in response.data['results']]
        self.assertEqual(amounts, sorted(amounts, reverse=True))
    
    def test_transaction_pagination(self):
        """Test transaction pagination"""
        # Create many transactions to test pagination
        for i in range(25):
            Transaction.objects.create(
                bank_account=self.bank_account,
                transaction_type='debit',
                amount=Decimal(f'-{i + 1}.00'),
                description=f'Transaction {i + 1}',
                transaction_date=timezone.now() - timedelta(hours=i)
            )
        
        url = reverse('transaction-list')
        response = self.client.get(url, {'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['next'])
        self.assertEqual(response.data['count'], 27)  # 25 + 2 from setUp


class BudgetViewSetTest(BankingAPITestCase):
    """Test BudgetViewSet functionality"""
    
    def test_list_budgets(self):
        """Test listing budgets for authenticated user's company"""
        # Create test budget
        budget = Budget.objects.create(
            company=self.company,
            name='Monthly Food Budget',
            amount=Decimal('500.00'),
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            created_by=self.user
        )
        
        url = reverse('budget-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], budget.id)
    
    def test_create_budget(self):
        """Test creating a new budget"""
        url = reverse('budget-list')
        data = {
            'name': 'Entertainment Budget',
            'description': 'Monthly entertainment expenses',
            'budget_type': 'monthly',
            'amount': '300.00',
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timedelta(days=30),
            'alert_threshold': 85
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Budget.objects.count(), 1)
        
        new_budget = Budget.objects.get(id=response.data['id'])
        self.assertEqual(new_budget.name, 'Entertainment Budget')
        self.assertEqual(new_budget.company, self.company)
        self.assertEqual(new_budget.created_by, self.user)
    
    def test_budget_company_isolation(self):
        """Test that users only see their company's budgets"""
        # Create another company
        other_company = Company.objects.create(
            name='Other Company',
            document_number='98765432000199',
            subscription_plan=self.subscription_plan,
            owner=User.objects.create_user(
                email='other@example.com',
                password='testpass123',
                name='Other User'
            )
        )
        
        # Create budget for other company
        Budget.objects.create(
            company=other_company,
            name='Other Budget',
            amount=Decimal('1000.00'),
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            created_by=other_company.owner
        )
        
        # Create budget for our company
        Budget.objects.create(
            company=self.company,
            name='Our Budget',
            amount=Decimal('500.00'),
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            created_by=self.user
        )
        
        url = reverse('budget-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Our Budget')


class FinancialGoalViewSetTest(BankingAPITestCase):
    """Test FinancialGoalViewSet functionality"""
    
    def test_list_financial_goals(self):
        """Test listing financial goals for authenticated user's company"""
        # Create test goal
        goal = FinancialGoal.objects.create(
            company=self.company,
            name='Emergency Fund',
            goal_type='emergency_fund',
            target_amount=Decimal('10000.00'),
            target_date=timezone.now().date() + timedelta(days=365),
            created_by=self.user
        )
        
        url = reverse('financialgoal-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], goal.id)
    
    def test_create_financial_goal(self):
        """Test creating a new financial goal"""
        url = reverse('financialgoal-list')
        data = {
            'name': 'Vacation Fund',
            'description': 'Save for summer vacation',
            'goal_type': 'savings',
            'target_amount': '5000.00',
            'target_date': (timezone.now().date() + timedelta(days=180)).isoformat(),
            'is_automatic_tracking': True
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FinancialGoal.objects.count(), 1)
        
        new_goal = FinancialGoal.objects.get(id=response.data['id'])
        self.assertEqual(new_goal.name, 'Vacation Fund')
        self.assertEqual(new_goal.company, self.company)
        self.assertEqual(new_goal.created_by, self.user)
    
    def test_update_financial_goal_progress(self):
        """Test updating financial goal progress"""
        goal = FinancialGoal.objects.create(
            company=self.company,
            name='Investment Goal',
            goal_type='investment',
            target_amount=Decimal('2000.00'),
            target_date=timezone.now().date() + timedelta(days=180),
            created_by=self.user
        )
        
        url = reverse('financialgoal-detail', kwargs={'pk': goal.id})
        data = {
            'current_amount': '500.00'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        goal.refresh_from_db()
        self.assertEqual(goal.current_amount, Decimal('500.00'))
    
    def test_goal_company_isolation(self):
        """Test that users only see their company's goals"""
        # Create another company
        other_company = Company.objects.create(
            name='Other Company',
            document_number='98765432000199',
            subscription_plan=self.subscription_plan,
            owner=User.objects.create_user(
                email='other@example.com',
                password='testpass123',
                name='Other User'
            )
        )
        
        # Create goal for other company
        FinancialGoal.objects.create(
            company=other_company,
            name='Other Goal',
            goal_type='savings',
            target_amount=Decimal('5000.00'),
            target_date=timezone.now().date() + timedelta(days=365),
            created_by=other_company.owner
        )
        
        # Create goal for our company
        FinancialGoal.objects.create(
            company=self.company,
            name='Our Goal',
            goal_type='savings',
            target_amount=Decimal('3000.00'),
            target_date=timezone.now().date() + timedelta(days=365),
            created_by=self.user
        )
        
        url = reverse('financialgoal-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Our Goal')


class TransactionCategoryViewSetTest(BankingAPITestCase):
    """Test TransactionCategoryViewSet functionality"""
    
    def test_list_categories(self):
        """Test listing transaction categories"""
        # Create additional category
        TransactionCategory.objects.create(
            name='Food & Dining',
            slug='food-dining',
            category_type='expense'
        )
        
        url = reverse('transactioncategory-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_categories_are_read_only(self):
        """Test that categories cannot be created via API"""
        url = reverse('transactioncategory-list')
        data = {
            'name': 'New Category',
            'slug': 'new-category',
            'category_type': 'expense'
        }
        response = self.client.post(url, data)
        
        # Should be method not allowed since it's ReadOnlyModelViewSet
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class BankProviderViewSetTest(BankingAPITestCase):
    """Test BankProviderViewSet functionality"""
    
    def test_list_bank_providers(self):
        """Test listing bank providers"""
        # Create additional provider
        BankProvider.objects.create(
            name='Another Bank',
            code='OTHER001'
        )
        
        url = reverse('bankprovider-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_providers_are_read_only(self):
        """Test that providers cannot be created via API"""
        url = reverse('bankprovider-list')
        data = {
            'name': 'New Bank',
            'code': 'NEW001'
        }
        response = self.client.post(url, data)
        
        # Should be method not allowed since it's ReadOnlyModelViewSet
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)