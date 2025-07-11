"""
E2E tests for complete user journeys from registration to report generation
"""
from decimal import Decimal
from datetime import date, timedelta
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import json
from django.test import override_settings

from apps.authentication.models import User, EmailVerification
from apps.companies.models import Company, CompanyUser, SubscriptionPlan
from apps.banking.models import BankProvider, BankAccount, Transaction, TransactionCategory, Budget, FinancialGoal
from apps.reports.models import Report
from apps.notifications.models import Notification
from apps.categories.models import CategoryRule, AITrainingData


@override_settings(
    FIELD_ENCRYPTION_KEY='0WbpgW5gcVxJvLds2p7Up2S-2FvUcDeYBs7KUZxQqMc=',
    AI_CATEGORIZATION_ENABLED=False
)
class TestCompleteUserJourney(TransactionTestCase):
    """
    Test complete user journey from registration to becoming a paying customer
    with full utilization of the platform features
    """
    
    def setUp(self):
        self.client = APIClient()
        self._create_initial_data()
    
    def _create_initial_data(self):
        """Create initial data required for the system"""
        # Create subscription plans
        self.starter_plan = SubscriptionPlan.objects.create(
            name='Starter',
            slug='starter',
            plan_type='starter',
            price_monthly=29.00,
            price_yearly=290.00,
            max_users=3,
            max_bank_accounts=2,
            max_transactions=500,
            has_ai_categorization=False,
            has_advanced_reports=False
        )
        
        self.pro_plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00,
            price_yearly=990.00,
            max_users=10,
            max_bank_accounts=5,
            max_transactions=2000,
            has_ai_categorization=True,
            has_advanced_reports=True
        )
        
        # Create bank providers
        self.bank_provider_itau = BankProvider.objects.create(
            name='Itaú',
            code='341',
            is_active=True
        )
        
        self.bank_provider_bb = BankProvider.objects.create(
            name='Banco do Brasil',
            code='001',
            is_active=True
        )
        
        # Create default categories
        self._create_default_categories()
    
    def _create_default_categories(self):
        """Create default transaction categories"""
        self.categories = {}
        
        # Income categories
        self.categories['sales'] = TransactionCategory.objects.create(
            slug='sales',
            name='Vendas',
            category_type='income',
            icon='trending-up',
            color='#10B981'
        )
        
        self.categories['services'] = TransactionCategory.objects.create(
            slug='services',
            name='Serviços',
            category_type='income',
            icon='briefcase',
            color='#6366F1'
        )
        
        # Expense categories
        self.categories['payroll'] = TransactionCategory.objects.create(
            slug='payroll',
            name='Folha de Pagamento',
            category_type='expense',
            icon='users',
            color='#F59E0B'
        )
        
        self.categories['rent'] = TransactionCategory.objects.create(
            slug='rent',
            name='Aluguel',
            category_type='expense',
            icon='home',
            color='#EF4444'
        )
        
        self.categories['supplies'] = TransactionCategory.objects.create(
            slug='supplies',
            name='Material de Escritório',
            category_type='expense',
            icon='paperclip',
            color='#8B5CF6'
        )
    
    @patch('apps.notifications.email_service.EmailService.send_verification_email')
    def test_new_business_owner_complete_journey(self, mock_verification):
        """
        Test complete journey of a new business owner:
        1. Registration with company creation
        2. Email verification
        3. Bank account connection
        4. Transaction import and categorization
        5. Budget creation
        6. Financial goal setting
        7. Report generation
        8. Team member invitation
        9. Subscription upgrade
        """
        
        # Step 1: User Registration
        print("\n=== Step 1: User Registration ===")
        registration_data = {
            'email': 'joao.silva@minhaempresa.com.br',
            'password': 'SenhaSegura123!',
            'password2': 'SenhaSegura123!',
            'first_name': 'João',
            'last_name': 'Silva',
            'phone': '+5511999887766',
            'company_name': 'Minha Empresa Ltda',
            'company_type': 'ltda',
            'business_sector': 'retail'
        }
        
        response = self.client.post(reverse('authentication:register'), registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        
        # Verify user and company were created
        user = User.objects.get(email='joao.silva@minhaempresa.com.br')
        company = Company.objects.get(owner=user)
        self.assertEqual(company.name, 'Minha Empresa Ltda')
        self.assertEqual(company.subscription_plan, self.starter_plan)
        self.assertEqual(company.subscription_status, 'trial')
        
        # Disable AI categorization for this test
        company.is_test_company = True
        company.save()
        
        # Set authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["tokens"]["access"]}')
        
        # Step 2: Email Verification
        print("\n=== Step 2: Email Verification ===")
        verification = EmailVerification.objects.get(user=user)
        response = self.client.post(reverse('authentication:verify_email'), {
            'token': verification.token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        
        # Step 3: Complete Company Profile
        print("\n=== Step 3: Complete Company Profile ===")
        profile_data = {
            'cnpj': '12.345.678/0001-90',
            'trade_name': 'Minha Empresa',
            'email': 'contato@minhaempresa.com.br',
            'phone': '+551133334444',
            'website': 'https://minhaempresa.com.br',
            'address_street': 'Rua das Empresas',
            'address_number': '123',
            'address_neighborhood': 'Centro',
            'address_city': 'São Paulo',
            'address_state': 'SP',
            'address_country': 'Brasil',
            'address_zip_code': '01234-567'
        }
        
        response = self.client.patch(
            reverse('companies:company-update'),
            profile_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 4: Connect Bank Account
        print("\n=== Step 4: Connect Bank Account ===")
        # Connect to Itaú
        response = self.client.post(reverse('banking:bank-account-list'), {
            'bank_provider_id': self.bank_provider_itau.id,
            'account_type': 'checking',
            'agency': '0001',
            'account_number': '12345-6',
            'current_balance': '50000.00'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        account_itau = BankAccount.objects.get(pk=response.data['id'])
        account_itau.refresh_from_db()
        
        # Set up the account with proper tokens for sync
        account_itau.access_token = 'pluggy_token_123'
        account_itau.refresh_token = 'refresh_token_123'
        account_itau.external_id = 'acc_123'
        account_itau.current_balance = Decimal('50000.00')
        account_itau.save()
        self.assertEqual(account_itau.current_balance, Decimal('50000.00'))
        
        # Step 5: Import Transactions
        print("\n=== Step 5: Import Transactions ===")
        with patch('apps.banking.services.OpenBankingService.get_account_info') as mock_account_info, \
             patch('apps.banking.services.OpenBankingService.get_transactions') as mock_get_transactions:
            # Mock account info response
            mock_account_info.return_value = {
                'balance': 50000.00,
                'available_balance': 50000.00,
                'currency': 'BRL'
            }
            
            # Mock transaction data
            today = date.today()
            mock_transactions = []
            
            # Sales transactions
            for i in range(5):
                mock_transactions.append({
                    'external_id': f'sale_{i}',
                    'transaction_date': (timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i*2)).isoformat(),
                    'description': f'Venda #{1000+i} - Cliente ABC',
                    'amount': 2500.00,
                    'transaction_type': 'credit',
                    'status': 'processed'
                })
            
            # Expense transactions
            mock_transactions.extend([
                {
                    'external_id': 'payroll_1',
                    'transaction_date': (timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=5)).isoformat(),
                    'description': 'Pagamento Folha de Pagamento',
                    'amount': 8000.00,
                    'transaction_type': 'debit',
                    'status': 'processed'
                },
                {
                    'external_id': 'rent_1',
                    'transaction_date': (timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)).isoformat(),
                    'description': 'Aluguel Escritório',
                    'amount': 3000.00,
                    'transaction_type': 'debit',
                    'status': 'processed'
                },
                {
                    'external_id': 'supplies_1',
                    'transaction_date': timezone.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
                    'description': 'Compra Material Escritório',
                    'amount': 500.00,
                    'transaction_type': 'debit',
                    'status': 'processed'
                }
            ])
            
            mock_get_transactions.return_value = mock_transactions
            
            # Sync transactions
            response = self.client.post(
                reverse('banking:sync-account', kwargs={'account_id': account_itau.id})
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify transactions were imported
            transactions = Transaction.objects.filter(account=account_itau)
            self.assertEqual(transactions.count(), 8)
            
            # Update balance
            account_itau.current_balance = Decimal('51000.00')  # 50000 + 12500 - 11500
            account_itau.save()
        
        # Step 6: Set Up Category Rules
        print("\n=== Step 6: Set Up Category Rules ===")
        rules_data = [
            {
                'category': self.categories['sales'].id,
                'rule_type': 'keyword',
                'conditions': {'keywords': ['venda', 'cliente', 'pedido']},
                'priority': 1,
                'is_active': True
            },
            {
                'category': self.categories['payroll'].id,
                'rule_type': 'keyword',
                'conditions': {'keywords': ['folha', 'pagamento', 'salário']},
                'priority': 2,
                'is_active': True
            },
            {
                'category': self.categories['rent'].id,
                'rule_type': 'keyword',
                'conditions': {'keywords': ['aluguel', 'escritório', 'locação']},
                'priority': 3,
                'is_active': True
            }
        ]
        
        for rule_data in rules_data:
            response = self.client.post(
                reverse('categories:category-rule-list'),
                rule_data,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Apply rules to existing transactions
        response = self.client.post(
            reverse('categories:bulk-categorize'),
            {'apply_rules': True},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 7: Create Budgets
        print("\n=== Step 7: Create Budgets ===")
        budgets_data = [
            {
                'name': 'Folha de Pagamento',
                'category': self.categories['payroll'].id,
                'amount': '10000.00',
                'period': 'monthly',
                'alert_threshold': 80
            },
            {
                'name': 'Aluguel',
                'category': self.categories['rent'].id,
                'amount': '3000.00',
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
        
        # Step 8: Set Financial Goals
        print("\n=== Step 8: Set Financial Goals ===")
        goals_data = [
            {
                'name': 'Reserva de Emergência',
                'description': 'Reserva para 6 meses de operação',
                'goal_type': 'emergency_fund',
                'target_amount': '100000.00',
                'current_amount': '51000.00',
                'target_date': (date.today() + timedelta(days=180)).isoformat()
            },
            {
                'name': 'Expansão do Negócio',
                'description': 'Capital para abrir nova filial',
                'goal_type': 'investment',
                'target_amount': '200000.00',
                'current_amount': '0.00',
                'target_date': (date.today() + timedelta(days=365)).isoformat()
            }
        ]
        
        for goal_data in goals_data:
            response = self.client.post(
                reverse('banking:financial-goal-list'),
                goal_data
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 9: Generate Reports
        print("\n=== Step 9: Generate Reports ===")
        # Generate monthly cash flow report
        response = self.client.post(reverse('reports:report-list'), {
            'report_type': 'cash_flow',
            'period': 'monthly',
            'start_date': (date.today() - timedelta(days=30)).isoformat(),
            'end_date': date.today().isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cash_flow_report = Report.objects.get(pk=response.data['id'])
        
        # Generate income vs expenses report
        response = self.client.post(reverse('reports:report-list'), {
            'report_type': 'income_vs_expenses',
            'period': 'monthly'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 10: Invite Team Member
        print("\n=== Step 10: Invite Team Member ===")
        with patch('apps.notifications.email_service.EmailService.send_invitation_email') as mock_invite:
            response = self.client.post(reverse('companies:invite-user'), {
                'email': 'contador@minhaempresa.com.br',
                'role': 'admin',
                'message': 'Olá, gostaria de convidá-lo para gerenciar as finanças da empresa.'
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            mock_invite.assert_called_once()
        
        # Step 11: Check Notifications
        print("\n=== Step 11: Check Notifications ===")
        response = self.client.get(reverse('notifications:notification-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have notifications for: welcome, email verified, bank connected, etc.
        self.assertGreater(len(response.data['results']), 0)
        
        # Step 12: Upgrade Subscription
        print("\n=== Step 12: Upgrade Subscription ===")
        with patch('apps.payments.payment_service.StripeGateway.create_subscription') as mock_stripe:
            mock_stripe.return_value = {
                'id': 'sub_123',
                'status': 'active',
                'current_period_end': int((timezone.now() + timedelta(days=30)).timestamp())
            }
            
            response = self.client.post(reverse('companies:subscription-upgrade'), {
                'plan_slug': 'pro',
                'payment_method_id': 'pm_test_visa',
                'billing_cycle': 'monthly'
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            company.refresh_from_db()
            self.assertEqual(company.subscription_plan.slug, 'pro')
            self.assertEqual(company.subscription_status, 'active')
        
        # Step 13: Use AI Categorization (Pro Feature)
        print("\n=== Step 13: Use AI Categorization ===")
        with patch('apps.categories.services.AICategorizationService.categorize_transaction') as mock_ai:
            mock_ai.return_value = {
                'category_id': self.categories['supplies'].id,
                'confidence': 0.95,
                'reasoning': 'Transaction description matches office supplies pattern'
            }
            
            # Create new transaction to test AI
            response = self.client.post(reverse('banking:transaction-list'), {
                'account': str(account_itau.id),
                'transaction_type': 'debit',
                'amount': '1200.00',
                'description': 'Compra de computadores e impressoras',
                'transaction_date': date.today().isoformat()
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verify AI categorization happened
            transaction = Transaction.objects.get(pk=response.data['id'])
            self.assertEqual(transaction.category.slug, 'supplies')
        
        # Final Verification: Check Dashboard
        print("\n=== Final Verification: Dashboard ===")
        response = self.client.get(reverse('banking:bank-account-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all data is properly set up
        self.assertEqual(BankAccount.objects.filter(company=company).count(), 1)
        self.assertEqual(Transaction.objects.filter(company=company).count(), 9)
        self.assertEqual(Budget.objects.filter(company=company).count(), 2)
        self.assertEqual(FinancialGoal.objects.filter(company=company).count(), 2)
        self.assertEqual(Report.objects.filter(company=company).count(), 2)
        
        print("\n=== Journey Complete! ===")
        print(f"Company: {company.name}")
        print(f"Plan: {company.subscription_plan.name}")
        print(f"Bank Accounts: {BankAccount.objects.filter(company=company).count()}")
        print(f"Transactions: {Transaction.objects.filter(company=company).count()}")
        print(f"Reports Generated: {Report.objects.filter(company=company).count()}")


class TestMultiCompanyUserJourney(TransactionTestCase):
    """
    Test user managing multiple companies
    """
    
    def setUp(self):
        self.client = APIClient()
        self._create_initial_data()
    
    def _create_initial_data(self):
        """Create initial data"""
        # Create subscription plans
        self.pro_plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00,
            price_yearly=990.00,
            max_users=10,
            max_bank_accounts=5
        )
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Banco do Brasil',
            code='001',
            is_active=True
        )
        
        # Create categories
        self.category_income = TransactionCategory.objects.create(
            slug='sales',
            name='Sales',
            category_type='income'
        )
        
        self.category_expense = TransactionCategory.objects.create(
            slug='expenses',
            name='Expenses',
            category_type='expense'
        )
    
    def test_user_with_multiple_companies(self):
        """
        Test user who owns one company and is invited to another
        """
        
        # Create first user with company
        print("\n=== Creating First Company ===")
        response = self.client.post(reverse('authentication:register'), {
            'email': 'owner1@company1.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Owner',
            'last_name': 'One',
            'company_name': 'Company One',
            'company_type': 'ltda',
            'business_sector': 'retail'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user1 = User.objects.get(email='owner1@company1.com')
        company1 = Company.objects.get(owner=user1)
        token1 = response.data['tokens']['access']
        
        # Create second user with company
        print("\n=== Creating Second Company ===")
        response = self.client.post(reverse('authentication:register'), {
            'email': 'owner2@company2.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Owner',
            'last_name': 'Two',
            'company_name': 'Company Two',
            'company_type': 'ltda',
            'business_sector': 'services'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user2 = User.objects.get(email='owner2@company2.com')
        company2 = Company.objects.get(owner=user2)
        token2 = response.data['tokens']['access']
        
        # Owner2 invites Owner1 to Company Two
        print("\n=== Cross-Company Invitation ===")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        
        with patch('apps.notifications.email_service.EmailService.send_invitation_email'):
            response = self.client.post(reverse('companies:invite-user'), {
                'email': 'owner1@company1.com',
                'role': 'admin'
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Owner1 now has access to both companies
        print("\n=== Testing Multi-Company Access ===")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token1}')
        
        # List all companies user has access to
        response = self.client.get(reverse('companies:company-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Create data in each company
        for company in [company1, company2]:
            # Simulate company context switching
            user1.company = company
            user1.save()
            
            # Create bank account
            response = self.client.post(reverse('banking:bank-account-list'), {
                'bank_provider_id': self.bank_provider.id,
                'account_type': 'checking',
                'agency': '0001',
                'account_number': f'{company.id:06d}',
                'current_balance': '10000.00'
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            account = BankAccount.objects.get(pk=response.data['id'])
            
            # Create transactions
            response = self.client.post(reverse('banking:transaction-list'), {
                'account': str(account.id),
                'transaction_type': 'credit',
                'amount': '5000.00',
                'description': f'Revenue for {company.name}',
                'transaction_date': date.today().isoformat(),
                'category': self.category_income.id
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify data isolation
        print("\n=== Verifying Data Isolation ===")
        
        # Company 1 context
        user1.company = company1
        user1.save()
        
        response = self.client.get(reverse('banking:transaction-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        transactions_company1 = response.data['results']
        self.assertEqual(len(transactions_company1), 1)
        self.assertIn('Company One', transactions_company1[0]['description'])
        
        # Company 2 context
        user1.company = company2
        user1.save()
        
        response = self.client.get(reverse('banking:transaction-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        transactions_company2 = response.data['results']
        self.assertEqual(len(transactions_company2), 1)
        self.assertIn('Company Two', transactions_company2[0]['description'])
        
        print("\n=== Multi-Company Journey Complete! ===")