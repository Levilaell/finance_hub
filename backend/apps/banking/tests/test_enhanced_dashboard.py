"""
Tests for Enhanced Dashboard endpoint
"""
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from django.core.cache import cache

from apps.authentication.models import User
from apps.companies.models import Company, CompanyUser, SubscriptionPlan
from apps.banking.models import BankAccount, Transaction, Budget, FinancialGoal, BankProvider, TransactionCategory


class TestEnhancedDashboardView(APITestCase):
    """Test enhanced dashboard endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Clear cache before each test
        cache.clear()
        
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            plan_type='starter',
            price_monthly=29.00,
            price_yearly=290.00,
            max_users=3,
            max_bank_accounts=2,
            max_transactions=500
        )
        
        # Create user and company
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user,
            subscription_plan=self.plan,
            subscription_status='active'
        )
        
        CompanyUser.objects.create(
            user=self.user,
            company=self.company,
            role='owner'
        )
        
        # Set company on user
        self.user.company = self.company
        self.user.save()
        
        # Create categories
        self.income_category = TransactionCategory.objects.create(
            slug='income',
            name='Income',
            category_type='income',
            icon='trending-up',
            color='#10B981'
        )
        
        self.expense_category = TransactionCategory.objects.create(
            slug='expenses',
            name='Expenses',
            category_type='expense',
            icon='trending-down',
            color='#EF4444'
        )
        
        # Create bank provider
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='001',
            is_active=True
        )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    def test_enhanced_dashboard_without_data(self):
        """Test dashboard returns correctly with no data"""
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure - actual response doesn't have nested 'basic_data'
        self.assertIn('current_balance', response.data)
        self.assertIn('monthly_income', response.data)
        self.assertIn('monthly_expenses', response.data)
        self.assertIn('monthly_net', response.data)
        self.assertIn('budgets_summary', response.data)
        self.assertIn('goals_summary', response.data)
        self.assertIn('monthly_trends', response.data)
        self.assertIn('expense_trends', response.data)
        self.assertIn('financial_insights', response.data)
        
        # Check basic data values
        self.assertEqual(response.data['current_balance'], 0)
        self.assertEqual(response.data['monthly_income'], 0)
        self.assertEqual(response.data['monthly_expenses'], 0)
        self.assertEqual(response.data['monthly_net'], 0)
        self.assertEqual(response.data['accounts_count'], 0)
        self.assertEqual(response.data['transactions_count'], 0)
        self.assertEqual(len(response.data['recent_transactions']), 0)
    
    def test_enhanced_dashboard_with_bank_account(self):
        """Test dashboard with bank account data"""
        # Create bank account
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            current_balance=Decimal('5000.00'),
            currency='BRL',
            is_active=True
        )
        
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(response.data['current_balance'], 5000)
        self.assertEqual(response.data['accounts_count'], 1)
    
    def test_enhanced_dashboard_with_transactions(self):
        """Test dashboard with transaction data"""
        # Create bank account
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            current_balance=Decimal('5000.00')
        )
        
        # Create transactions for current month
        today = timezone.now().date()
        
        # Income transaction
        Transaction.objects.create(
            account=account,
            company=self.company,
            transaction_type='credit',
            amount=Decimal('3000.00'),
            description='Client payment',
            transaction_date=today,
            category=self.income_category
        )
        
        # Expense transaction
        Transaction.objects.create(
            account=account,
            company=self.company,
            transaction_type='debit',
            amount=Decimal('1000.00'),
            description='Office rent',
            transaction_date=today,
            category=self.expense_category
        )
        
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(response.data['monthly_income'], 3000)
        self.assertEqual(response.data['monthly_expenses'], 1000)
        self.assertEqual(response.data['monthly_net'], 2000)
        self.assertEqual(response.data['transactions_count'], 2)
        self.assertEqual(len(response.data['recent_transactions']), 2)
    
    def test_enhanced_dashboard_with_budgets(self):
        """Test dashboard with budget data"""
        # Create budgets
        Budget.objects.create(
            company=self.company,
            category=self.expense_category,
            name='Monthly Expenses',
            amount=Decimal('2000.00'),
            period='monthly',
            alert_threshold=80,
            start_date=timezone.now().date().replace(day=1)
        )
        
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        budget_summary = response.data['budgets_summary']
        self.assertEqual(budget_summary['total_budget_amount'], 2000)
        self.assertEqual(budget_summary['total_spent'], 0)
        self.assertEqual(len(response.data['active_budgets']), 1)
    
    def test_enhanced_dashboard_with_goals(self):
        """Test dashboard with financial goals"""
        # Create goal
        FinancialGoal.objects.create(
            company=self.company,
            name='Emergency Fund',
            goal_type='emergency_fund',
            target_amount=Decimal('10000.00'),
            current_amount=Decimal('2500.00'),
            target_date=timezone.now().date() + timedelta(days=180)
        )
        
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        goals_summary = response.data['goals_summary']
        self.assertEqual(goals_summary['total_goals'], 1)
        self.assertEqual(goals_summary['total_target_amount'], 10000)
        self.assertEqual(goals_summary['total_current_amount'], 2500)
    
    def test_enhanced_dashboard_monthly_trends(self):
        """Test dashboard monthly trends calculation"""
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            current_balance=Decimal('5000.00')
        )
        
        # Create transactions for last 3 months
        today = timezone.now().date()
        
        for i in range(3):
            month_date = today - timedelta(days=30 * i)
            
            # Income
            Transaction.objects.create(
                account=account,
                company=self.company,
                transaction_type='credit',
                amount=Decimal('5000.00'),
                description=f'Income month {i}',
                transaction_date=month_date,
                category=self.income_category
            )
            
            # Expense
            Transaction.objects.create(
                account=account,
                company=self.company,
                transaction_type='debit',
                amount=Decimal('3000.00'),
                description=f'Expense month {i}',
                transaction_date=month_date,
                category=self.expense_category
            )
        
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        monthly_trends = response.data['monthly_trends']
        self.assertGreater(len(monthly_trends), 0)
        
        # Check first month data
        current_month = monthly_trends[0]
        self.assertEqual(current_month['income'], 5000)
        self.assertEqual(current_month['expenses'], 3000)
        self.assertEqual(current_month['net_flow'], 2000)
    
    def test_enhanced_dashboard_caching(self):
        """Test dashboard caching functionality"""
        # First request - should hit database
        with self.assertNumQueries(10):  # Adjust based on actual queries
            response1 = self.client.get(reverse('banking:enhanced-dashboard'))
            self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second request - should hit cache
        with self.assertNumQueries(1):  # Only user/company query
            response2 = self.client.get(reverse('banking:enhanced-dashboard'))
            self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Data should be identical
        self.assertEqual(response1.data, response2.data)
    
    def test_enhanced_dashboard_authentication_required(self):
        """Test dashboard requires authentication"""
        self.client.force_authenticate(user=None)
        
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_enhanced_dashboard_company_isolation(self):
        """Test dashboard only shows data from user's company"""
        # Create another company with data
        other_user = User.objects.create_user(
            email='other@example.com',
            username='other@example.com',
            password='TestPass123!'
        )
        
        other_company = Company.objects.create(
            name='Other Company',
            owner=other_user,
            subscription_plan=self.plan
        )
        
        # Create account for other company
        BankAccount.objects.create(
            company=other_company,
            bank_provider=self.bank_provider,
            account_type='checking',
            current_balance=Decimal('10000.00')
        )
        
        # Request dashboard as original user
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should not see other company's data
        self.assertEqual(response.data['current_balance'], 0)  # No accounts for this company
        self.assertEqual(response.data['accounts_count'], 0)
    
    def test_enhanced_dashboard_error_handling(self):
        """Test dashboard handles errors gracefully"""
        # Mock cache service to raise exception
        with patch('apps.banking.views.cache_service.get_or_set') as mock_cache:
            mock_cache.side_effect = Exception('Cache error')
            
            response = self.client.get(reverse('banking:enhanced-dashboard'))
            
            # Should still return data despite cache error
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('current_balance', response.data)
    
    def test_enhanced_dashboard_performance(self):
        """Test dashboard performance with large dataset"""
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            current_balance=Decimal('50000.00')
        )
        
        # Create many transactions
        transactions = []
        for i in range(100):
            transactions.append(
                Transaction(
                    account=account,
                    company=self.company,
                    transaction_type='credit' if i % 2 == 0 else 'debit',
                    amount=Decimal('100.00'),
                    description=f'Transaction {i}',
                    transaction_date=timezone.now().date() - timedelta(days=i),
                    category=self.income_category if i % 2 == 0 else self.expense_category
                )
            )
        Transaction.objects.bulk_create(transactions)
        
        # Measure response time
        import time
        start_time = time.time()
        
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        
        end_time = time.time()
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 2.0)  # Should respond in less than 2 seconds
        
        # Check data accuracy
        self.assertEqual(response.data['transactions_count'], 100)


class TestEnhancedDashboardIntegration(TestCase):
    """Integration tests for enhanced dashboard"""
    
    def setUp(self):
        """Set up integration test data"""
        # Create complete test scenario
        self.user = User.objects.create_user(
            email='integration@test.com',
            username='integration@test.com',
            password='TestPass123!'
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00,
            max_bank_accounts=5
        )
        
        self.company = Company.objects.create(
            name='Integration Test Co',
            owner=self.user,
            subscription_plan=self.plan
        )
        
        CompanyUser.objects.create(
            user=self.user,
            company=self.company,
            role='owner'
        )
        
        self.user.company = self.company
        self.user.save()
    
    def test_complete_dashboard_flow(self):
        """Test complete dashboard flow from login to data display"""
        # Login
        self.client.login(email='integration@test.com', password='TestPass123!')
        
        # Access dashboard
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all sections are present
        required_sections = [
            'current_balance', 'monthly_income', 'budgets_summary', 'goals_summary',
            'monthly_trends', 'expense_trends', 'financial_insights'
        ]
        
        for section in required_sections:
            self.assertIn(section, response.data)
            self.assertIsNotNone(response.data[section])
    
    def test_dashboard_with_real_banking_flow(self):
        """Test dashboard after simulating real banking operations"""
        self.client.force_login(self.user)
        
        # Create bank provider
        provider = BankProvider.objects.create(
            name='Banco do Brasil',
            code='001'
        )
        
        # Connect bank account
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=provider,
            account_type='checking',
            current_balance=Decimal('10000.00')
        )
        
        # Create realistic transaction categories
        salary_cat = TransactionCategory.objects.create(
            slug='salary',
            name='Salary',
            category_type='income'
        )
        
        rent_cat = TransactionCategory.objects.create(
            slug='rent',
            name='Rent',
            category_type='expense'
        )
        
        # Add transactions
        Transaction.objects.create(
            account=account,
            company=self.company,
            transaction_type='credit',
            amount=Decimal('8000.00'),
            description='Monthly salary',
            transaction_date=timezone.now().date(),
            category=salary_cat
        )
        
        Transaction.objects.create(
            account=account,
            company=self.company,
            transaction_type='debit',
            amount=Decimal('2500.00'),
            description='Office rent',
            transaction_date=timezone.now().date(),
            category=rent_cat
        )
        
        # Create budget
        Budget.objects.create(
            company=self.company,
            category=rent_cat,
            name='Rent Budget',
            amount=Decimal('3000.00'),
            period='monthly'
        )
        
        # Access dashboard
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify calculations
        self.assertEqual(response.data['current_balance'], 10000)
        self.assertEqual(response.data['monthly_income'], 8000)
        self.assertEqual(response.data['monthly_expenses'], 2500)
        self.assertEqual(response.data['monthly_net'], 5500)
        
        # Verify budget calculations
        budget_summary = response.data['budgets_summary']
        self.assertEqual(budget_summary['total_budget_amount'], 3000)
        self.assertEqual(budget_summary['total_spent'], 2500)