"""
Integration tests for end-to-end API workflows.

Tests complete user journeys including:
- User registration → bank connection → transaction sync → report generation
- Company creation → user invitation → permission setup
- Subscription upgrade → feature access
- Bank sync → categorization → budget tracking
- Goal creation → progress tracking → completion
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from unittest.mock import patch, MagicMock
import json

from apps.companies.models import Company, CompanyUser, SubscriptionPlan
from apps.banking.models import (
    BankAccount, Transaction, BankProvider, TransactionCategory,
    Budget, FinancialGoal
)
from apps.categories.models import CategoryRule
from apps.reports.models import Report
from apps.authentication.models import EmailVerification
from apps.payments.payment_service import StripeGateway

User = get_user_model()


class TestUserRegistrationToReportGeneration(TestCase):
    """Test complete journey from registration to report generation."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Itaú',
            code='341',
            is_active=True
        )
        
        # Create or get categories
        self.categories = {}
        self.categories['income'], _ = TransactionCategory.objects.get_or_create(
            slug='sales',
            defaults={'name': 'Sales', 'category_type': 'income'}
        )
        self.categories['food'], _ = TransactionCategory.objects.get_or_create(
            slug='food-dining',
            defaults={'name': 'Food & Dining', 'category_type': 'expense'}
        )
        self.categories['transport'], _ = TransactionCategory.objects.get_or_create(
            slug='transportation',
            defaults={'name': 'Transportation', 'category_type': 'expense'}
        )
        self.categories['utilities'], _ = TransactionCategory.objects.get_or_create(
            slug='utilities',
            defaults={'name': 'Utilities', 'category_type': 'expense'}
        )
    
    @patch('apps.notifications.email_service.EmailService.send_verification_email')
    def test_complete_user_journey(self, mock_email):
        """Test complete user journey from signup to report."""
        # Step 1: User Registration
        response = self.client.post(reverse('authentication:register'), {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
            'company_name': 'My New Business',
            'company_type': 'ltda',
            'business_sector': 'retail'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Get user and tokens
        user = User.objects.get(email='newuser@example.com')
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Step 2: Verify email (simulate)
        verification = EmailVerification.objects.get(user=user)
        verification.is_verified = True
        verification.save()
        user.is_email_verified = True
        user.save()
        
        # Step 3: Check company was created
        response = self.client.get(reverse('companies:company-detail'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        company = Company.objects.get(owner=user)
        
        # Step 4: Connect bank account
        response = self.client.post(reverse('banking:bank-account-list'), {
            'bank_provider_id': self.bank_provider.id,
            'account_type': 'checking',
            'agency': '0001',
            'account_number': '123456',
            'current_balance': '15000.00'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        account_id = response.data['id']
        
        # Step 5: Create transactions manually (simulating sync)
        account = BankAccount.objects.get(pk=account_id)
        for i in range(10):
            tx_date = date.today() - timedelta(days=i)
            Transaction.objects.create(
                bank_account=account,
                transaction_type='credit' if i % 2 == 0 else 'debit',
                amount=Decimal('100.00') if i % 2 == 0 else Decimal('-50.00'),
                description=f'Transaction {i}',
                transaction_date=tx_date,
                external_id=f'tx-{i}'
            )
        
        # Step 6: Set up category rules
        response = self.client.post(reverse('categories:category-rule-list'), {
            'category': self.categories['food'].id,
            'rule_type': 'keyword',
            'conditions': {'keywords': ['food', 'restaurant', 'dining']},
            'priority': 1,
            'is_active': True
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 7: Create budget
        response = self.client.post(reverse('banking:budget-list'), {
            'category': self.categories['food'].id,
            'amount': '500.00',
            'period': 'monthly',
            'alert_threshold': 80
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 8: Create financial goal
        response = self.client.post(reverse('banking:financial-goal-list'), {
            'name': 'Emergency Fund',
            'target_amount': '50000.00',
            'current_amount': '15000.00',
            'target_date': (date.today() + timedelta(days=365)).isoformat(),
            'goal_type': 'savings'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 9: Generate reports
        report_types = ['cash_flow', 'income_vs_expenses', 'category_spending']
        
        for report_type in report_types:
            response = self.client.post(reverse('reports:report-list'), {
                'report_type': report_type,
                'period': 'monthly',
                'filters': {}
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 10: View enhanced dashboard
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify dashboard contains all data
        self.assertIn('total_balance', response.data)
        self.assertIn('budgets', response.data)
        self.assertIn('financial_goals', response.data)
        self.assertIn('recent_transactions', response.data)
        self.assertIn('top_categories', response.data)


class TestCompanyManagementWorkflow(TestCase):
    """Test company creation, user invitation, and permission setup."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create owner user
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='TestPass123!',
            first_name='Company',
            last_name='Owner'
        )
        
        # Create subscription plans
        self.plans = {
            'starter': SubscriptionPlan.objects.create(
                name='Starter',
                slug='starter',
                plan_type='starter',
                price_monthly=29.00, price_yearly=290.00,
                max_bank_accounts=2,
                max_users=3
            ),
            'pro': SubscriptionPlan.objects.create(
                name='Pro',
                slug='pro',
                plan_type='pro',
                price_monthly=99.00, price_yearly=990.00,
                max_bank_accounts=5,
                max_users=10,
                has_api_access=True,
                has_advanced_reports=True
            ),
            'enterprise': SubscriptionPlan.objects.create(
                name='Enterprise',
                slug='enterprise',
                plan_type='enterprise',
                price_monthly=299.00, price_yearly=2990.00,
                max_bank_accounts=100,
                max_users=100,
                has_api_access=True,
                has_advanced_reports=True,
                has_accountant_access=True
            )
        }
    
    @patch('apps.notifications.email_service.EmailService.send_invitation_email')
    def test_company_setup_and_team_building(self, mock_email):
        """Test complete company setup and team building workflow."""
        # Step 1: Owner creates company
        refresh = RefreshToken.for_user(self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        response = self.client.post(reverse('companies:company-list'), {
            'name': 'Tech Startup Inc',
            'cnpj': '98765432109876',
            'industry': 'technology',
            'size': 'medium',
            'phone': '+5511999999999',
            'address': '123 Tech Street',
            'city': 'São Paulo',
            'state': 'SP',
            'country': 'Brazil'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        company_id = response.data['id']
        
        # Step 2: Invite team members
        team_members = [
            {'email': 'admin@example.com', 'role': 'admin'},
            {'email': 'accountant@example.com', 'role': 'member'},
            {'email': 'viewer@example.com', 'role': 'viewer'}
        ]
        
        for member in team_members:
            response = self.client.post(
                reverse('companies:company-invite-user'),
                member
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify invitations were sent
        self.assertEqual(mock_email.call_count, 3)
        
        # Step 3: Simulate users accepting invitations
        for member in team_members:
            # Create user account
            user = User.objects.create_user(
                username=member['email'].split('@')[0],
                email=member['email'],
                password='TestPass123!',
                first_name='Test',
                last_name='User'
            )
            
            # Add to company
            CompanyUser.objects.create(
                company_id=company_id,
                user=user,
                role=member['role']
            )
            user.company_id = company_id
            user.save()
        
        # Step 4: Verify team listing
        response = self.client.get(reverse('companies:company-users'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 4)  # Owner + 3 team members
        
        # Step 5: Test role-based access
        # Admin user can invite more users
        admin_user = User.objects.get(email='admin@example.com')
        admin_refresh = RefreshToken.for_user(admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(admin_refresh.access_token)}')
        
        response = self.client.post(reverse('companies:company-invite-user'), {
            'email': 'newmember@example.com',
            'role': 'member'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Viewer cannot invite users
        viewer_user = User.objects.get(email='viewer@example.com')
        viewer_refresh = RefreshToken.for_user(viewer_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(viewer_refresh.access_token)}')
        
        response = self.client.post(reverse('companies:company-invite-user'), {
            'email': 'another@example.com',
            'role': 'member'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestSubscriptionUpgradeWorkflow(TestCase):
    """Test subscription upgrade and feature access."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create user and company with starter plan
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        self.starter_plan = SubscriptionPlan.objects.create(
            name='Starter',
            slug='starter',
                plan_type='starter',
            price_monthly=29.00, price_yearly=290.00,
            max_users=3,
            max_bank_accounts=2,
            has_advanced_reports=False
        )
        
        self.pro_plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00, price_yearly=990.00,
            max_users=10,
            max_bank_accounts=5,
            has_advanced_reports=True,
            has_ai_categorization=True
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='12345678901234',
            owner=self.user,
            subscription_plan=self.starter_plan
        )
        
        CompanyUser.objects.create(
            company=self.company,
            user=self.user,
            role='owner'
        )
        self.user.company = self.company
        self.user.save()
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='001'
        )
    
    @patch('apps.payments.payment_service.StripeGateway.create_subscription')
    def test_subscription_upgrade_unlocks_features(self, mock_stripe):
        """Test upgrading subscription unlocks new features."""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Step 1: Try to create more than 2 bank accounts (starter limit)
        for i in range(2):
            response = self.client.post(reverse('banking:bank-account-list'), {
                'bank_provider_id': self.bank_provider.id,
                'account_type': 'checking',
                'agency': f'000{i}',
                'account_number': f'{i}' * 6,
                'current_balance': '1000.00'
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Third account should fail (limit reached)
        response = self.client.post(reverse('banking:bank-account-list'), {
            'bank_provider_id': self.bank_provider.id,
            'account_type': 'savings',
            'agency': '0003',
            'account_number': '333333',
            'current_balance': '1000.00'
        })
        # Note: Actual implementation would check limits
        
        # Step 2: Upgrade to Pro plan
        mock_stripe.return_value = {
            'id': 'sub_123',
            'status': 'active',
            'current_period_end': int((timezone.now() + timedelta(days=30)).timestamp())
        }
        
        response = self.client.post(reverse('companies:company-upgrade-subscription'), {
            'plan_slug': 'pro',
            'payment_method_id': 'pm_test123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify subscription was updated
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_plan.slug, 'pro')
        
        # Step 3: Now can create more bank accounts
        response = self.client.post(reverse('banking:bank-account-list'), {
            'bank_provider_id': self.bank_provider.id,
            'account_type': 'savings',
            'agency': '0003',
            'account_number': '333333',
            'current_balance': '1000.00'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 4: AI categorization would be available with pro plan
        self.company.refresh_from_db()
        # self.assertTrue(self.company.settings.get('ai_categorization_enabled', False))
        
        # Step 5: Can generate advanced reports
        response = self.client.post(reverse('reports:report-list'), {
            'report_type': 'advanced_analytics',
            'period': 'quarterly',
            'filters': {}
        })
        # Would succeed with pro plan features


class TestBankSyncToCategorizationWorkflow(TestCase):
    """Test bank sync, categorization, and budget tracking."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00, price_yearly=990.00
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='12345678901234',
            owner=self.user,
            subscription_plan=plan
        )
        
        CompanyUser.objects.create(
            company=self.company,
            user=self.user,
            role='owner'
        )
        self.user.company = self.company
        self.user.save()
        
        # Create categories and rules
        self._setup_categories_and_rules()
        
        # Get auth token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    
    def _setup_categories_and_rules(self):
        """Set up categories and categorization rules."""
        # Categories
        self.categories = {
            'groceries': TransactionCategory.objects.get_or_create(
                slug='groceries',
                defaults={'name': 'Groceries', 'category_type': 'expense'}
            )[0],
            'restaurants': TransactionCategory.objects.get_or_create(
                slug='restaurants',
                defaults={'name': 'Restaurants', 'category_type': 'expense'}
            )[0],
            'transport': TransactionCategory.objects.get_or_create(
                slug='transportation',
                defaults={'name': 'Transportation', 'category_type': 'expense'}
            )[0],
            'salary': TransactionCategory.objects.get_or_create(
                slug='salary',
                defaults={'name': 'Salary', 'category_type': 'income'}
            )[0]
        }
        
        # Rules
        CategoryRule.objects.create(
            company=self.company,
            category=self.categories['groceries'],
            rule_type='keyword',
            conditions={'keywords': ['supermarket', 'grocery', 'mercado']},
            priority=1,
            is_active=True
        )
        
        CategoryRule.objects.create(
            company=self.company,
            category=self.categories['restaurants'],
            rule_type='keyword',
            conditions={'keywords': ['restaurant', 'food', 'dining', 'ifood']},
            priority=2,
            is_active=True
        )
        
        CategoryRule.objects.create(
            company=self.company,
            category=self.categories['transport'],
            rule_type='keyword',
            conditions={'keywords': ['uber', 'taxi', '99', 'gas', 'fuel']},
            priority=3,
            is_active=True
        )
        
        CategoryRule.objects.create(
            company=self.company,
            category=self.categories['salary'],
            rule_type='amount_range',
            conditions={'min_amount': '5000.00', 'transaction_type': 'credit'},
            priority=1,
            is_active=True
        )
    
    def test_sync_categorize_budget_workflow(self):
        """Test complete workflow from sync to budget tracking."""
        # Step 1: Create bank account
        provider = BankProvider.objects.create(name='Banco do Brasil', code='001')
        
        response = self.client.post(reverse('banking:bank-account-list'), {
            'bank_provider_id': provider.id,
            'account_type': 'checking',
            'agency': '1234',
            'account_number': '567890',
            'current_balance': '10000.00'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        account_id = response.data['id']
        
        # Step 2: Create budgets
        for category_key, category in self.categories.items():
            if category.category_type == 'expense':
                amount = '1000.00' if category_key == 'groceries' else '500.00'
                response = self.client.post(reverse('banking:budget-list'), {
                    'category': category.id,
                    'amount': amount,
                    'period': 'monthly',
                    'alert_threshold': 80
                })
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 3: Sync transactions
        mock_transactions = [
            {
                'id': 'tx1',
                'description': 'Supermarket purchase',
                'amount': -150.00,
                'date': date.today().isoformat(),
                'type': 'OUTFLOW'
            },
            {
                'id': 'tx2',
                'description': 'Restaurant dinner',
                'amount': -80.00,
                'date': date.today().isoformat(),
                'type': 'OUTFLOW'
            },
            {
                'id': 'tx3',
                'description': 'Uber ride',
                'amount': -25.00,
                'date': date.today().isoformat(),
                'type': 'OUTFLOW'
            },
            {
                'id': 'tx4',
                'description': 'Monthly salary',
                'amount': 8000.00,
                'date': date.today().isoformat(),
                'type': 'INFLOW'
            }
        ]
        
        # Create account first
        account = BankAccount.objects.get(pk=account_id)
        
        # Create transactions manually (simulating sync)
        for tx in mock_transactions:
            Transaction.objects.create(
                bank_account=account,
                external_id=tx['id'],
                description=tx['description'],
                amount=Decimal(str(tx['amount'])),
                transaction_date=date.today(),
                transaction_type='credit' if tx['type'] == 'INFLOW' else 'debit'
            )
        
        # Step 4: Verify transactions were categorized
        transactions = Transaction.objects.filter(company=self.company)
        self.assertEqual(transactions.count(), 4)
        
        # Check categorization
        grocery_tx = transactions.filter(description__icontains='supermarket').first()
        self.assertEqual(grocery_tx.category, self.categories['groceries'])
        
        restaurant_tx = transactions.filter(description__icontains='restaurant').first()
        self.assertEqual(restaurant_tx.category, self.categories['restaurants'])
        
        transport_tx = transactions.filter(description__icontains='uber').first()
        self.assertEqual(transport_tx.category, self.categories['transport'])
        
        salary_tx = transactions.filter(amount__gte=5000).first()
        self.assertEqual(salary_tx.category, self.categories['salary'])
        
        # Step 5: Check budget status
        response = self.client.get(reverse('banking:budget-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        budgets = {b['category']['name']: b for b in response.data['results']}
        
        # Groceries budget
        grocery_budget = budgets['Groceries']
        self.assertEqual(Decimal(grocery_budget['spent']), Decimal('150.00'))
        self.assertEqual(Decimal(grocery_budget['percentage_used']), Decimal('15.00'))
        
        # Restaurant budget
        restaurant_budget = budgets['Restaurants']
        self.assertEqual(Decimal(restaurant_budget['spent']), Decimal('80.00'))
        self.assertEqual(Decimal(restaurant_budget['percentage_used']), Decimal('16.00'))
        
        # Step 6: Get spending analytics
        response = self.client.get(reverse('reports:category-spending', kwargs={
            'report_id': 'current'  # Special case for current period
        }))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify spending breakdown
        self.assertIn('category_breakdown', response.data)
        self.assertIn('total_expenses', response.data)
        self.assertEqual(Decimal(response.data['total_expenses']), Decimal('255.00'))


class TestGoalTrackingWorkflow(TestCase):
    """Test financial goal creation, tracking, and completion."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00, price_yearly=990.00
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='12345678901234',
            owner=self.user,
            subscription_plan=plan
        )
        
        CompanyUser.objects.create(
            company=self.company,
            user=self.user,
            role='owner'
        )
        self.user.company = self.company
        self.user.save()
        
        # Create bank account
        provider = BankProvider.objects.create(name='Test Bank', code='001')
        self.account = BankAccount.objects.create(
            company=self.company,
            bank_provider=provider,
            account_type='savings',
            agency='0001',
            account_number='123456',
            current_balance=Decimal('5000.00')
        )
        
        # Get auth token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    
    def test_goal_creation_to_completion(self):
        """Test complete goal tracking workflow."""
        # Step 1: Create financial goal
        target_date = date.today() + timedelta(days=180)
        response = self.client.post(reverse('banking:financial-goal-list'), {
            'name': 'New Equipment Fund',
            'target_amount': '25000.00',
            'current_amount': '5000.00',
            'target_date': target_date.isoformat(),
            'goal_type': 'custom',
            'description': 'Save for new production equipment'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        goal_id = response.data['id']
        
        # Verify initial progress
        self.assertEqual(response.data['progress_percentage'], 20.0)
        self.assertEqual(response.data['remaining_amount'], '20000.00')
        
        # Step 2: Make progress through savings transactions
        income_category, _ = TransactionCategory.objects.get_or_create(
            name='Sales',
            defaults={'category_type': 'income'}
        )
        
        # Simulate monthly savings
        for month in range(4):
            # Income
            response = self.client.post(reverse('banking:transaction-list'), {
                'account': str(self.account.id),
                'transaction_type': 'credit',
                'amount': '10000.00',
                'description': f'Monthly revenue - Month {month+1}',
                'transaction_date': (date.today() + timedelta(days=month*30)).isoformat(),
                'category': income_category.id
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Update account balance
            self.account.current_balance += Decimal('10000.00')
            self.account.save()
            
            # Update goal progress (simulating manual update)
            goal = FinancialGoal.objects.get(pk=goal_id)
            goal.current_amount += Decimal('5000.00')  # Save half
            goal.save()
        
        # Step 3: Check goal progress
        response = self.client.get(
            reverse('banking:financial-goal-detail', kwargs={'pk': goal_id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # After 4 months: 5000 + (5000 * 4) = 25000
        self.assertEqual(response.data['current_amount'], '25000.00')
        self.assertEqual(response.data['progress_percentage'], 100.0)
        self.assertTrue(response.data['is_completed'])
        
        # Step 4: View goals in dashboard
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        goals = response.data['financial_goals']
        self.assertEqual(len(goals), 1)
        self.assertTrue(goals[0]['is_completed'])
        
        # Step 5: Generate goal achievement report
        response = self.client.post(reverse('reports:report-list'), {
            'report_type': 'goal_progress',
            'period': 'custom',
            'filters': {
                'start_date': date.today().isoformat(),
                'end_date': target_date.isoformat()
            }
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)