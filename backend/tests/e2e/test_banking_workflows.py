"""
E2E tests for complete banking workflows
"""
from decimal import Decimal
from datetime import date, timedelta
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock, call
import json

from apps.authentication.models import User
from apps.companies.models import Company, CompanyUser, SubscriptionPlan
from apps.banking.models import (
    BankProvider, BankAccount, Transaction, TransactionCategory,
    Budget, FinancialGoal, RecurringTransaction, BankConnection
)
from apps.categories.models import CategoryRule, AITrainingData, CategorySuggestion
from apps.notifications.models import Notification


class TestCompleteBankingWorkflow(TransactionTestCase):
    """
    Test complete banking workflows including:
    - Multi-bank connections
    - Transaction synchronization
    - Automatic categorization
    - Budget tracking
    - Financial goals
    - Recurring transactions
    """
    
    def setUp(self):
        self.client = APIClient()
        self._create_test_data()
    
    def _create_test_data(self):
        """Create initial test data"""
        # Create user and company
        self.user = User.objects.create_user(
            username='banking_user',
            email='banking@test.com',
            password='TestPass123!',
            first_name='Banking',
            last_name='User'
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00,
            price_yearly=990.00,
            max_bank_accounts=5,
            has_ai_categorization=True
        )
        
        self.company = Company.objects.create(
            name='Test Banking Company',
            cnpj='12345678901234',
            owner=self.user,
            subscription_plan=self.plan,
            subscription_status='active'
        )
        
        CompanyUser.objects.create(
            company=self.company,
            user=self.user,
            role='owner'
        )
        
        # Create bank providers
        self.providers = {
            'itau': BankProvider.objects.create(
                name='Itaú',
                code='341',
                is_active=True
            ),
            'bradesco': BankProvider.objects.create(
                name='Bradesco',
                code='237',
                is_active=True
            ),
            'nubank': BankProvider.objects.create(
                name='Nubank',
                code='260',
                is_active=True
            )
        }
        
        # Create categories
        self._create_categories()
        
        # Authenticate
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    
    def _create_categories(self):
        """Create transaction categories"""
        self.categories = {}
        
        # Income
        self.categories['sales'] = TransactionCategory.objects.create(
            slug='sales',
            name='Vendas',
            category_type='income'
        )
        
        self.categories['investments'] = TransactionCategory.objects.create(
            slug='investments',
            name='Rendimentos',
            category_type='income'
        )
        
        # Expenses
        self.categories['suppliers'] = TransactionCategory.objects.create(
            slug='suppliers',
            name='Fornecedores',
            category_type='expense'
        )
        
        self.categories['taxes'] = TransactionCategory.objects.create(
            slug='taxes',
            name='Impostos',
            category_type='expense'
        )
        
        self.categories['payroll'] = TransactionCategory.objects.create(
            slug='payroll',
            name='Folha de Pagamento',
            category_type='expense'
        )
        
        self.categories['utilities'] = TransactionCategory.objects.create(
            slug='utilities',
            name='Utilidades',
            category_type='expense'
        )
    
    @patch('apps.banking.belvo_client.BelvoClient')
    @patch('apps.banking.pluggy_client.PluggyClient')
    def test_multi_bank_connection_and_sync(self, mock_pluggy, mock_belvo):
        """
        Test connecting multiple bank accounts and syncing transactions
        """
        print("\n=== Multi-Bank Connection Test ===")
        
        # Step 1: Connect Itaú account via Belvo
        print("\n--- Connecting Itaú via Belvo ---")
        mock_belvo_instance = MagicMock()
        mock_belvo.return_value = mock_belvo_instance
        
        mock_belvo_instance.create_link.return_value = {
            'id': 'belvo_link_itau',
            'institution': 'itau',
            'status': 'valid'
        }
        
        mock_belvo_instance.get_accounts.return_value = [{
            'id': 'itau_acc_1',
            'name': 'Conta Corrente Itaú',
            'number': '12345-6',
            'agency': '0001',
            'balance': {'current': 100000.00},
            'type': 'CHECKING_ACCOUNT'
        }]
        
        response = self.client.post(reverse('banking:bank-account-list'), {
            'bank_provider_id': self.providers['itau'].id,
            'account_type': 'checking',
            'agency': '0001',
            'account_number': '12345-6',
            'current_balance': '100000.00',
            'access_token': 'belvo_token_itau'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        itau_account = BankAccount.objects.get(pk=response.data['id'])
        
        # Step 2: Connect Bradesco account via Pluggy
        print("\n--- Connecting Bradesco via Pluggy ---")
        mock_pluggy_instance = MagicMock()
        mock_pluggy.return_value = mock_pluggy_instance
        
        # Mock async methods
        async def mock_create_item():
            return {
                'id': 'pluggy_item_bradesco',
                'connector': {'name': 'Bradesco'},
                'status': 'UPDATED'
            }
        
        async def mock_get_accounts():
            return [{
                'id': 'bradesco_acc_1',
                'name': 'Conta Corrente',
                'number': '98765-4',
                'branch': '5678',
                'balance': 50000.00,
                'type': 'BANK'
            }]
        
        mock_pluggy_instance.create_item = mock_create_item
        mock_pluggy_instance.get_accounts = mock_get_accounts
        
        response = self.client.post(reverse('banking:bank-account-list'), {
            'bank_provider_id': self.providers['bradesco'].id,
            'account_type': 'checking',
            'agency': '5678',
            'account_number': '98765-4',
            'current_balance': '50000.00',
            'access_token': 'pluggy_token_bradesco'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        bradesco_account = BankAccount.objects.get(pk=response.data['id'])
        
        # Step 3: Connect Nubank manually (no integration)
        print("\n--- Connecting Nubank manually ---")
        response = self.client.post(reverse('banking:bank-account-list'), {
            'bank_provider_id': self.providers['nubank'].id,
            'account_type': 'checking',
            'agency': '0001',
            'account_number': '999999',
            'current_balance': '25000.00'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        nubank_account = BankAccount.objects.get(pk=response.data['id'])
        
        # Step 4: Sync transactions from all accounts
        print("\n--- Syncing Transactions ---")
        
        # Mock Itaú transactions
        today = date.today()
        mock_belvo_instance.get_transactions.return_value = [
            {
                'id': 'itau_tx_1',
                'account': 'itau_acc_1',
                'date': today.isoformat(),
                'description': 'Venda Cartão - Cliente XYZ',
                'amount': 5000.00,
                'type': 'INFLOW',
                'status': 'PROCESSED'
            },
            {
                'id': 'itau_tx_2',
                'account': 'itau_acc_1',
                'date': (today - timedelta(days=1)).isoformat(),
                'description': 'Pagamento Fornecedor ABC',
                'amount': -3000.00,
                'type': 'OUTFLOW',
                'status': 'PROCESSED'
            },
            {
                'id': 'itau_tx_3',
                'account': 'itau_acc_1',
                'date': (today - timedelta(days=2)).isoformat(),
                'description': 'DAS - Simples Nacional',
                'amount': -1200.00,
                'type': 'OUTFLOW',
                'status': 'PROCESSED'
            }
        ]
        
        response = self.client.post(
            reverse('banking:sync-account', kwargs={'account_id': itau_account.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify transactions were imported
        itau_transactions = Transaction.objects.filter(account=itau_account)
        self.assertEqual(itau_transactions.count(), 3)
        
        # Step 5: Set up automatic categorization rules
        print("\n--- Setting Up Categorization Rules ---")
        rules = [
            {
                'category': self.categories['sales'].id,
                'rule_type': 'keyword',
                'conditions': {'keywords': ['venda', 'cartão', 'cliente']},
                'priority': 1,
                'is_active': True
            },
            {
                'category': self.categories['suppliers'].id,
                'rule_type': 'keyword',
                'conditions': {'keywords': ['fornecedor', 'compra', 'pagamento']},
                'priority': 2,
                'is_active': True
            },
            {
                'category': self.categories['taxes'].id,
                'rule_type': 'keyword',
                'conditions': {'keywords': ['das', 'simples', 'imposto', 'taxa']},
                'priority': 3,
                'is_active': True
            }
        ]
        
        for rule_data in rules:
            response = self.client.post(
                reverse('categories:category-rule-list'),
                rule_data,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Apply rules to categorize transactions
        response = self.client.post(
            reverse('categories:bulk-categorize'),
            {'apply_rules': True},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify categorization
        categorized_transactions = Transaction.objects.filter(
            account=itau_account,
            category__isnull=False
        )
        self.assertEqual(categorized_transactions.count(), 3)
        
        # Step 6: Create budgets for expense tracking
        print("\n--- Creating Budgets ---")
        budgets_data = [
            {
                'name': 'Fornecedores',
                'category': self.categories['suppliers'].id,
                'amount': '20000.00',
                'period': 'monthly',
                'alert_threshold': 80
            },
            {
                'name': 'Impostos',
                'category': self.categories['taxes'].id,
                'amount': '5000.00',
                'period': 'monthly',
                'alert_threshold': 90
            },
            {
                'name': 'Folha de Pagamento',
                'category': self.categories['payroll'].id,
                'amount': '50000.00',
                'period': 'monthly',
                'alert_threshold': 100
            }
        ]
        
        for budget_data in budgets_data:
            response = self.client.post(
                reverse('banking:budget-list'),
                budget_data
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check budget status
        response = self.client.get(reverse('banking:budget-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        budgets = response.data['results']
        
        # Find suppliers budget
        suppliers_budget = next(b for b in budgets if b['name'] == 'Fornecedores')
        self.assertEqual(Decimal(suppliers_budget['spent_amount']), Decimal('3000.00'))
        self.assertEqual(Decimal(suppliers_budget['percentage_used']), Decimal('15.00'))
        
        # Step 7: Set up recurring transaction detection
        print("\n--- Setting Up Recurring Transactions ---")
        
        # Add more historical transactions to detect patterns
        recurring_transactions = []
        for month in range(3):
            base_date = today - timedelta(days=30 * (month + 1))
            
            # Monthly rent
            recurring_transactions.append(
                Transaction.objects.create(
                    account=itau_account,
                    company=self.company,
                    transaction_type='debit',
                    amount=Decimal('5000.00'),
                    description='Aluguel Escritório',
                    transaction_date=base_date,
                    category=self.categories['utilities']
                )
            )
            
            # Monthly payroll
            recurring_transactions.append(
                Transaction.objects.create(
                    account=itau_account,
                    company=self.company,
                    transaction_type='debit',
                    amount=Decimal('45000.00'),
                    description='Folha de Pagamento',
                    transaction_date=base_date + timedelta(days=5),
                    category=self.categories['payroll']
                )
            )
        
        # Create recurring transaction records
        RecurringTransaction.objects.create(
            company=self.company,
            description='Aluguel Escritório',
            expected_amount=Decimal('5000.00'),
            frequency='monthly',
            category=self.categories['utilities'],
            is_active=True
        )
        
        RecurringTransaction.objects.create(
            company=self.company,
            description='Folha de Pagamento',
            expected_amount=Decimal('45000.00'),
            frequency='monthly',
            category=self.categories['payroll'],
            is_active=True
        )
        
        # Step 8: Create and track financial goals
        print("\n--- Creating Financial Goals ---")
        goals_data = [
            {
                'name': 'Capital de Giro',
                'description': 'Manter 3 meses de operação',
                'goal_type': 'savings',
                'target_amount': '200000.00',
                'current_amount': '175000.00',  # Sum of all accounts
                'target_date': (today + timedelta(days=90)).isoformat()
            },
            {
                'name': 'Redução de Custos',
                'description': 'Reduzir despesas em 10%',
                'goal_type': 'expense_reduction',
                'target_amount': '45000.00',  # Current: 50000
                'current_amount': '50000.00',
                'target_date': (today + timedelta(days=180)).isoformat()
            }
        ]
        
        for goal_data in goals_data:
            response = self.client.post(
                reverse('banking:financial-goal-list'),
                goal_data
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check goal progress
        response = self.client.get(reverse('banking:financial-goal-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        goals = response.data['results']
        
        capital_goal = next(g for g in goals if g['name'] == 'Capital de Giro')
        self.assertEqual(capital_goal['progress_percentage'], 87.5)  # 175000/200000
        
        # Step 9: Test account aggregation
        print("\n--- Testing Account Aggregation ---")
        response = self.client.get(reverse('banking:bank-account-summary'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        summary = response.data
        self.assertEqual(len(summary['accounts']), 3)
        self.assertEqual(Decimal(summary['total_balance']), Decimal('175000.00'))
        
        # Step 10: Test transaction search and filtering
        print("\n--- Testing Transaction Search ---")
        
        # Search by description
        response = self.client.get(
            reverse('banking:transaction-list'),
            {'search': 'fornecedor'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Filter by category
        response = self.client.get(
            reverse('banking:transaction-list'),
            {'category': self.categories['sales'].id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Filter by date range
        response = self.client.get(
            reverse('banking:transaction-list'),
            {
                'date_from': (today - timedelta(days=7)).isoformat(),
                'date_to': today.isoformat()
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        print("\n=== Banking Workflow Complete! ===")
        print(f"Connected Banks: {BankAccount.objects.filter(company=self.company).count()}")
        print(f"Total Transactions: {Transaction.objects.filter(company=self.company).count()}")
        print(f"Categorized: {Transaction.objects.filter(company=self.company, category__isnull=False).count()}")
        print(f"Budgets: {Budget.objects.filter(company=self.company).count()}")
        print(f"Goals: {FinancialGoal.objects.filter(company=self.company).count()}")


class TestBankConnectionFailureRecovery(TransactionTestCase):
    """
    Test bank connection failures and recovery workflows
    """
    
    def setUp(self):
        self.client = APIClient()
        self._create_test_data()
    
    def _create_test_data(self):
        """Create initial test data"""
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00,
            price_yearly=990.00
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user,
            subscription_plan=self.plan
        )
        
        CompanyUser.objects.create(
            company=self.company,
            user=self.user,
            role='owner'
        )
        
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='001',
            is_active=True
        )
        
        # Authenticate
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    
    @patch('apps.banking.belvo_client.BelvoClient')
    def test_bank_connection_failure_and_retry(self, mock_belvo):
        """
        Test handling of bank connection failures and retry logic
        """
        print("\n=== Bank Connection Failure Test ===")
        
        # Step 1: Initial connection attempt fails
        print("\n--- Initial Connection Failure ---")
        mock_belvo_instance = MagicMock()
        mock_belvo.return_value = mock_belvo_instance
        
        mock_belvo_instance.create_link.side_effect = Exception("Connection timeout")
        
        response = self.client.post(reverse('banking:bank-account-list'), {
            'bank_provider_id': self.bank_provider.id,
            'account_type': 'checking',
            'agency': '0001',
            'account_number': '12345',
            'current_balance': '1000.00',
            'access_token': 'test_token'
        })
        # Should handle the error gracefully
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])
        
        # Step 2: Retry with success
        print("\n--- Retry Connection ---")
        mock_belvo_instance.create_link.side_effect = None
        mock_belvo_instance.create_link.return_value = {
            'id': 'link_123',
            'status': 'valid'
        }
        
        mock_belvo_instance.get_accounts.return_value = [{
            'id': 'acc_123',
            'number': '12345',
            'agency': '0001',
            'balance': {'current': 1000.00}
        }]
        
        response = self.client.post(reverse('banking:bank-account-list'), {
            'bank_provider_id': self.bank_provider.id,
            'account_type': 'checking',
            'agency': '0001',
            'account_number': '12345',
            'current_balance': '1000.00',
            'access_token': 'test_token'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 3: Test sync failure recovery
        print("\n--- Sync Failure and Recovery ---")
        account = BankAccount.objects.get(pk=response.data['id'])
        
        # First sync fails
        mock_belvo_instance.get_transactions.side_effect = Exception("API rate limit")
        
        response = self.client.post(
            reverse('banking:sync-account', kwargs={'account_id': account.id})
        )
        # Should handle error
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])
        
        # Check sync status
        account.refresh_from_db()
        self.assertIn(account.last_sync_status, ['failed', 'error', None])
        
        # Retry sync successfully
        mock_belvo_instance.get_transactions.side_effect = None
        mock_belvo_instance.get_transactions.return_value = [{
            'id': 'tx_1',
            'date': date.today().isoformat(),
            'description': 'Test transaction',
            'amount': 100.00,
            'type': 'INFLOW'
        }]
        
        response = self.client.post(
            reverse('banking:sync-account', kwargs={'account_id': account.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify sync completed
        account.refresh_from_db()
        self.assertEqual(account.last_sync_status, 'success')
        self.assertEqual(Transaction.objects.filter(account=account).count(), 1)
        
        print("\n=== Connection Recovery Complete! ===")