"""
Test reports analytics views
Tests for AnalyticsView, DashboardStatsView, CashFlowDataView, CategorySpendingView, and IncomeVsExpensesView
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.banking.models import BankAccount, BankProvider, Transaction, TransactionCategory
from apps.companies.models import Company, SubscriptionPlan
from apps.reports.models import Report, ReportSchedule, ReportTemplate

User = get_user_model()


class TestAnalyticsView(TestCase):
    """Test AnalyticsView"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            slug='pro-plan',
            plan_type='pro',
            price_monthly=99.90,
            price_yearly=999.00
        )
        
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        self.user.company = self.company
        self.user.save()
        
        # Create bank provider and account
        self.provider = BankProvider.objects.create(
            name='Test Bank',
            code='001',
            is_active=True
        )
        
        self.account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.provider,
            account_type='checking',
            account_number='12345',
            agency='0001',
            current_balance=Decimal('5000.00'),
            is_active=True
        )
        
        # Create transaction categories
        self.food_category = TransactionCategory.objects.create(
            name='Food & Dining',
            slug='food-dining-analytics',
            category_type='expense',
            icon='🍽️'
        )
        
        self.transport_category = TransactionCategory.objects.create(
            name='Transport',
            slug='transport-analytics',
            category_type='expense',
            icon='🚗'
        )
        
        self.salary_category = TransactionCategory.objects.create(
            name='Salary',
            slug='salary-analytics',
            category_type='income',
            icon='💰'
        )
        
        # Create transactions for the last 30 days
        now = timezone.now()
        for i in range(30):
            transaction_date = now - timedelta(days=i)
            
            # Income transaction every 10 days
            if i % 10 == 0:
                Transaction.objects.create(
                    bank_account=self.account,
                    external_id=f'income_{i}',
                    description=f'Salary payment',
                    amount=Decimal('3000.00'),
                    transaction_type='credit',
                    transaction_date=transaction_date,
                    posted_date=transaction_date,
                    counterpart_name='Company XYZ',
                    category=self.salary_category
                )
            
            # Daily expenses
            Transaction.objects.create(
                bank_account=self.account,
                external_id=f'food_{i}',
                description=f'Restaurant payment',
                amount=Decimal('-50.00'),
                transaction_type='debit',
                transaction_date=transaction_date,
                posted_date=transaction_date,
                counterpart_name='Restaurant ABC',
                category=self.food_category
            )
            
            if i % 2 == 0:  # Transport expenses every other day
                Transaction.objects.create(
                    bank_account=self.account,
                    external_id=f'transport_{i}',
                    description=f'Uber ride',
                    amount=Decimal('-25.00'),
                    transaction_type='debit',
                    transaction_date=transaction_date,
                    posted_date=transaction_date,
                    counterpart_name='Uber',
                    category=self.transport_category
                )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    def test_get_analytics_default_period(self):
        """Test getting analytics with default 30-day period"""
        url = reverse('reports:analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('period', response.data)
        self.assertIn('summary', response.data)
        self.assertIn('top_income_sources', response.data)
        self.assertIn('top_expense_categories', response.data)
        self.assertIn('weekly_trend', response.data)
        self.assertIn('insights', response.data)
        
        # Check period
        self.assertEqual(response.data['period']['days'], 30)
        
        # Check summary calculations
        summary = response.data['summary']
        self.assertEqual(summary['total_income'], Decimal('9000.00'))  # 3 salary payments
        self.assertEqual(summary['total_expenses'], Decimal('1875.00'))  # 30*50 + 15*25
        self.assertEqual(summary['net_result'], Decimal('7125.00'))
        self.assertEqual(summary['transaction_count'], 48)  # 3 + 30 + 15
        
        # Check top income sources
        self.assertEqual(len(response.data['top_income_sources']), 1)
        self.assertEqual(response.data['top_income_sources'][0]['counterpart_name'], 'Company XYZ')
        
        # Check top expense categories
        self.assertEqual(len(response.data['top_expense_categories']), 2)
        food_expense = next(c for c in response.data['top_expense_categories'] if c['category__name'] == 'Food & Dining')
        self.assertEqual(food_expense['total'], Decimal('-1500.00'))
        
        # Check insights
        self.assertGreater(len(response.data['insights']), 0)
        self.assertEqual(response.data['insights'][0]['type'], 'positive')
    
    def test_get_analytics_custom_period(self):
        """Test getting analytics with custom period"""
        url = reverse('reports:analytics')
        response = self.client.get(url, {'period': '7'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['period']['days'], 7)
        
        # Check calculations for 7-day period
        summary = response.data['summary']
        self.assertEqual(summary['total_income'], Decimal('3000.00'))  # 1 salary payment
        self.assertEqual(summary['total_expenses'], Decimal('450.00'))  # 7*50 + 4*25
        self.assertEqual(summary['transaction_count'], 12)  # 1 + 7 + 4
    
    def test_get_analytics_invalid_period(self):
        """Test getting analytics with invalid period defaults to 30 days"""
        url = reverse('reports:analytics')
        response = self.client.get(url, {'period': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['period']['days'], 30)
    
    def test_weekly_trend_calculation(self):
        """Test weekly trend calculation"""
        url = reverse('reports:analytics')
        response = self.client.get(url, {'period': '28'})  # 4 full weeks
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        weekly_trend = response.data['weekly_trend']
        
        self.assertEqual(len(weekly_trend), 4)  # 4 weeks
        
        # Check first week has data
        first_week = weekly_trend[0]
        self.assertIn('week_start', first_week)
        self.assertIn('week_end', first_week)
        self.assertIn('income', first_week)
        self.assertIn('expenses', first_week)
        self.assertIn('net', first_week)
    
    def test_analytics_no_transactions(self):
        """Test analytics when there are no transactions"""
        # Delete all transactions
        Transaction.objects.all().delete()
        
        url = reverse('reports:analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        summary = response.data['summary']
        self.assertEqual(summary['total_income'], Decimal('0'))
        self.assertEqual(summary['total_expenses'], Decimal('0'))
        self.assertEqual(summary['net_result'], Decimal('0'))
        self.assertEqual(summary['transaction_count'], 0)
        
        # Should still have insights
        self.assertGreater(len(response.data['insights']), 0)
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access is denied"""
        self.client.force_authenticate(user=None)
        
        url = reverse('reports:analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestDashboardStatsView(TestCase):
    """Test DashboardStatsView"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            slug='pro-plan',
            plan_type='pro',
            price_monthly=99.90,
            price_yearly=999.00
        )
        
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        self.user.company = self.company
        self.user.save()
        
        # Create bank accounts
        self.provider = BankProvider.objects.create(
            name='Test Bank',
            code='001',
            is_active=True
        )
        
        self.account1 = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.provider,
            account_type='checking',
            account_number='12345',
            agency='0001',
            current_balance=Decimal('5000.00'),
            is_active=True
        )
        
        self.account2 = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.provider,
            account_type='savings',
            account_number='54321',
            agency='0001',
            current_balance=Decimal('10000.00'),
            is_active=True
        )
        
        # Create current month transactions
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        Transaction.objects.create(
            bank_account=self.account1,
            external_id='income_1',
            description='Salary',
            amount=Decimal('5000.00'),
            transaction_type='credit',
            transaction_date=month_start + timedelta(days=5),
            posted_date=month_start + timedelta(days=5)
        )
        
        Transaction.objects.create(
            bank_account=self.account1,
            external_id='expense_1',
            description='Rent',
            amount=Decimal('-1500.00'),
            transaction_type='debit',
            transaction_date=month_start + timedelta(days=10),
            posted_date=month_start + timedelta(days=10)
        )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    def test_get_dashboard_stats(self):
        """Test getting dashboard statistics"""
        url = reverse('reports:dashboard-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('total_balance', response.data)
        self.assertIn('income_this_month', response.data)
        self.assertIn('expenses_this_month', response.data)
        self.assertIn('net_income', response.data)
        self.assertIn('pending_transactions', response.data)
        self.assertIn('accounts_count', response.data)
        
        # Check calculations
        self.assertEqual(response.data['total_balance'], Decimal('15000.00'))
        self.assertEqual(response.data['income_this_month'], Decimal('5000.00'))
        self.assertEqual(response.data['expenses_this_month'], Decimal('1500.00'))
        self.assertEqual(response.data['net_income'], Decimal('3500.00'))
        self.assertEqual(response.data['accounts_count'], 2)
    
    def test_dashboard_stats_inactive_accounts(self):
        """Test dashboard stats excludes inactive accounts"""
        # Make one account inactive
        self.account2.is_active = False
        self.account2.save()
        
        url = reverse('reports:dashboard-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_balance'], Decimal('5000.00'))
        self.assertEqual(response.data['accounts_count'], 1)
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access is denied"""
        self.client.force_authenticate(user=None)
        
        url = reverse('reports:dashboard-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestCashFlowDataView(TestCase):
    """Test CashFlowDataView"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            slug='pro-plan',
            plan_type='pro',
            price_monthly=99.90,
            price_yearly=999.00
        )
        
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        self.user.company = self.company
        self.user.save()
        
        # Create bank account
        self.provider = BankProvider.objects.create(
            name='Test Bank',
            code='001',
            is_active=True
        )
        
        self.account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.provider,
            account_type='checking',
            account_number='12345',
            agency='0001',
            current_balance=Decimal('5000.00'),
            is_active=True
        )
        
        # Create transactions for different dates
        base_date = timezone.now() - timedelta(days=7)
        
        for i in range(7):
            transaction_date = base_date + timedelta(days=i)
            
            Transaction.objects.create(
                bank_account=self.account,
                external_id=f'income_{i}',
                description='Daily income',
                amount=Decimal('100.00'),
                transaction_type='credit',
                transaction_date=transaction_date,
                posted_date=transaction_date
            )
            
            Transaction.objects.create(
                bank_account=self.account,
                external_id=f'expense_{i}',
                description='Daily expense',
                amount=Decimal('-50.00'),
                transaction_type='debit',
                transaction_date=transaction_date,
                posted_date=transaction_date
            )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    def test_get_cash_flow_data(self):
        """Test getting cash flow data"""
        start_date = (timezone.now().date() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = timezone.now().date().strftime('%Y-%m-%d')
        
        url = reverse('reports:cash-flow-data')
        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 8)  # 7 days + today
        
        # Check first day data
        first_day = response.data[0]
        self.assertIn('date', first_day)
        self.assertIn('income', first_day)
        self.assertIn('expenses', first_day)
        self.assertIn('balance', first_day)
        
        self.assertEqual(first_day['income'], 100.0)
        self.assertEqual(first_day['expenses'], 50.0)
        self.assertEqual(first_day['balance'], 50.0)
        
        # Check running balance
        last_day = response.data[-1]
        self.assertEqual(last_day['balance'], 300.0)  # 6 * (100 - 50)
    
    def test_cash_flow_missing_dates(self):
        """Test cash flow with missing date parameters"""
        url = reverse('reports:cash-flow-data')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'start_date and end_date are required')
    
    def test_cash_flow_invalid_date_format(self):
        """Test cash flow with invalid date format"""
        url = reverse('reports:cash-flow-data')
        response = self.client.get(url, {
            'start_date': 'invalid-date',
            'end_date': '2025-01-31'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid date format. Use YYYY-MM-DD')
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access is denied"""
        self.client.force_authenticate(user=None)
        
        url = reverse('reports:cash-flow-data')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestCategorySpendingView(TestCase):
    """Test CategorySpendingView"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            slug='pro-plan',
            plan_type='pro',
            price_monthly=99.90,
            price_yearly=999.00
        )
        
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        self.user.company = self.company
        self.user.save()
        
        # Create bank account
        self.provider = BankProvider.objects.create(
            name='Test Bank',
            code='001',
            is_active=True
        )
        
        self.account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.provider,
            account_type='checking',
            account_number='12345',
            agency='0001',
            current_balance=Decimal('5000.00'),
            is_active=True
        )
        
        # Create categories
        self.food_category = TransactionCategory.objects.create(
            name='Food & Dining',
            slug='food-dining-analytics',
            category_type='expense',
            icon='🍽️'
        )
        
        self.transport_category = TransactionCategory.objects.create(
            name='Transport',
            slug='transport-analytics',
            category_type='expense',
            icon='🚗'
        )
        
        self.salary_category = TransactionCategory.objects.create(
            name='Salary',
            slug='salary-analytics',
            category_type='income',
            icon='💰'
        )
        
        # Create categorized transactions
        Transaction.objects.create(
            bank_account=self.account,
            external_id='food_1',
            description='Restaurant',
            amount=Decimal('-100.00'),
            transaction_type='debit',
            transaction_date=timezone.now(),
            posted_date=timezone.now(),
            category=self.food_category
        )
        
        Transaction.objects.create(
            bank_account=self.account,
            external_id='food_2',
            description='Groceries',
            amount=Decimal('-200.00'),
            transaction_type='debit',
            transaction_date=timezone.now(),
            posted_date=timezone.now(),
            category=self.food_category
        )
        
        Transaction.objects.create(
            bank_account=self.account,
            external_id='transport_1',
            description='Gas',
            amount=Decimal('-50.00'),
            transaction_type='debit',
            transaction_date=timezone.now(),
            posted_date=timezone.now(),
            category=self.transport_category
        )
        
        Transaction.objects.create(
            bank_account=self.account,
            external_id='salary_1',
            description='Monthly salary',
            amount=Decimal('5000.00'),
            transaction_type='credit',
            transaction_date=timezone.now(),
            posted_date=timezone.now(),
            category=self.salary_category
        )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    def test_get_expense_category_spending(self):
        """Test getting expense category spending"""
        # Use a date range that includes today fully
        start_date = (timezone.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (timezone.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        url = reverse('reports:category-spending')
        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date,
            'type': 'expense'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)  # 2 expense categories
        
        # Check food category
        food_data = next(c for c in response.data if c['category']['name'] == 'Food & Dining')
        self.assertEqual(food_data['amount'], 300.0)
        self.assertEqual(food_data['transaction_count'], 2)
        self.assertAlmostEqual(float(food_data['percentage']), 85.7, places=1)  # 300/350 * 100
        
        # Check transport category
        transport_data = next(c for c in response.data if c['category']['name'] == 'Transport')
        self.assertEqual(transport_data['amount'], 50.0)
        self.assertEqual(transport_data['transaction_count'], 1)
        self.assertAlmostEqual(float(transport_data['percentage']), 14.3, places=1)  # 50/350 * 100
    
    def test_get_income_category_spending(self):
        """Test getting income category spending"""
        # Use a date range that includes today fully
        start_date = (timezone.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (timezone.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        url = reverse('reports:category-spending')
        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date,
            'type': 'income'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # 1 income category
        
        salary_data = response.data[0]
        self.assertEqual(salary_data['category']['name'], 'Salary')
        self.assertEqual(salary_data['amount'], 5000.0)
        self.assertAlmostEqual(float(salary_data['percentage']), 100.0, places=1)
    
    def test_category_spending_missing_dates(self):
        """Test category spending with missing date parameters"""
        url = reverse('reports:category-spending')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access is denied"""
        self.client.force_authenticate(user=None)
        
        url = reverse('reports:category-spending')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestIncomeVsExpensesView(TestCase):
    """Test IncomeVsExpensesView"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            slug='pro-plan',
            plan_type='pro',
            price_monthly=99.90,
            price_yearly=999.00
        )
        
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan,
            enable_ai_categorization=False
        )
        self.user.company = self.company
        self.user.save()
        
        # Create bank account
        self.provider = BankProvider.objects.create(
            name='Test Bank',
            code='001',
            is_active=True
        )
        
        self.account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.provider,
            account_type='checking',
            account_number='12345',
            agency='0001',
            current_balance=Decimal('5000.00'),
            is_active=True
        )
        
        # Create transactions for multiple months
        for month in range(1, 4):  # Jan, Feb, Mar
            # Income
            transaction_date = timezone.make_aware(datetime(2025, month, 15, 10, 0, 0))
            Transaction.objects.create(
                bank_account=self.account,
                external_id=f'income_{month}',
                description='Monthly income',
                amount=Decimal('5000.00'),
                transaction_type='credit',
                transaction_date=transaction_date,
                posted_date=transaction_date
            )
            
            # Expenses
            expense_date = timezone.make_aware(datetime(2025, month, 20, 10, 0, 0))
            Transaction.objects.create(
                bank_account=self.account,
                external_id=f'expense_{month}',
                description='Monthly expenses',
                amount=Decimal(f'-{3000 + month * 100}.00'),
                transaction_type='debit',
                transaction_date=expense_date,
                posted_date=expense_date
            )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    def test_get_income_vs_expenses(self):
        """Test getting income vs expenses monthly data"""
        url = reverse('reports:income-vs-expenses')
        response = self.client.get(url, {
            'start_date': '2025-01-01',
            'end_date': '2025-03-31'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 3)  # 3 months
        
        # Check January data
        jan_data = response.data[0]
        self.assertEqual(jan_data['month'], '2025-01')
        self.assertEqual(jan_data['income'], 5000.0)
        self.assertEqual(jan_data['expenses'], 3100.0)
        self.assertEqual(jan_data['profit'], 1900.0)
        
        # Check March data (expenses increase)
        mar_data = response.data[2]
        self.assertEqual(mar_data['month'], '2025-03')
        self.assertEqual(mar_data['income'], 5000.0)
        self.assertEqual(mar_data['expenses'], 3300.0)
        self.assertEqual(mar_data['profit'], 1700.0)
    
    def test_income_vs_expenses_missing_dates(self):
        """Test income vs expenses with missing date parameters"""
        url = reverse('reports:income-vs-expenses')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_income_vs_expenses_invalid_date_format(self):
        """Test income vs expenses with invalid date format"""
        url = reverse('reports:income-vs-expenses')
        response = self.client.get(url, {
            'start_date': '01/01/2025',  # Wrong format
            'end_date': '2025-03-31'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access is denied"""
        self.client.force_authenticate(user=None)
        
        url = reverse('reports:income-vs-expenses')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)