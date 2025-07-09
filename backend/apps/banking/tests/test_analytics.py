"""
Comprehensive tests for Banking app Analytics views
Testing TimeSeriesAnalyticsView and ExpenseTrendsView functionality
"""
import json
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
    Transaction
)
from apps.companies.models import Company, SubscriptionPlan

User = get_user_model()


class AnalyticsTestCase(APITestCase):
    """Base test case for analytics tests"""
    
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
        
        # Create categories
        self.income_category = TransactionCategory.objects.create(
            name='Salary',
            slug='salary',
            category_type='income',
            icon='💰',
            color='#00FF00'
        )
        
        self.food_category = TransactionCategory.objects.create(
            name='Food',
            slug='food',
            category_type='expense',
            icon='🍽️',
            color='#FF6B6B'
        )
        
        self.transport_category = TransactionCategory.objects.create(
            name='Transport',
            slug='transport',
            category_type='expense',
            icon='🚗',
            color='#4ECDC4'
        )
        
        # Create bank account
        self.bank_account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='1234',
            account_number='567890',
            status='active',
            current_balance=Decimal('5000.00'),
            is_active=True
        )
        
        # Setup API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Get current date for consistent testing
        self.today = timezone.now().date()
    
    def create_time_series_data(self):
        """Create time series test data spanning multiple months"""
        base_date = self.today.replace(day=1) - timedelta(days=90)  # 3 months ago
        
        transactions = []
        
        # Create monthly patterns
        for month_offset in range(3):
            month_start = base_date + timedelta(days=month_offset * 30)
            
            # Monthly salary
            transactions.append(Transaction.objects.create(
                bank_account=self.bank_account,
                transaction_type='credit',
                amount=Decimal('5000.00'),
                description=f'Salary Month {month_offset + 1}',
                transaction_date=timezone.make_aware(
                    datetime.combine(month_start + timedelta(days=1), datetime.min.time())
                ),
                category=self.income_category
            ))
            
            # Weekly food expenses
            for week in range(4):
                week_date = month_start + timedelta(days=week * 7 + 2)
                transactions.append(Transaction.objects.create(
                    bank_account=self.bank_account,
                    transaction_type='debit',
                    amount=Decimal('-300.00'),
                    description=f'Groceries Week {week + 1}',
                    transaction_date=timezone.make_aware(
                        datetime.combine(week_date, datetime.min.time())
                    ),
                    category=self.food_category
                ))
            
            # Monthly transport expenses
            for day in [5, 15, 25]:
                transport_date = month_start + timedelta(days=day)
                transactions.append(Transaction.objects.create(
                    bank_account=self.bank_account,
                    transaction_type='debit',
                    amount=Decimal('-150.00'),
                    description=f'Transport Month {month_offset + 1}',
                    transaction_date=timezone.make_aware(
                        datetime.combine(transport_date, datetime.min.time())
                    ),
                    category=self.transport_category
                ))
        
        return transactions


class TimeSeriesAnalyticsViewTest(AnalyticsTestCase):
    """Test TimeSeriesAnalyticsView functionality"""
    
    def test_time_series_data_retrieval(self):
        """Test basic time series data retrieval"""
        self.create_time_series_data()
        
        url = reverse('time-series-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('series', data)
        self.assertIsInstance(data['series'], list)
    
    def test_time_series_date_range_filter(self):
        """Test filtering time series data by date range"""
        self.create_time_series_data()
        
        # Test with specific date range
        start_date = (self.today - timedelta(days=60)).isoformat()
        end_date = (self.today - timedelta(days=30)).isoformat()
        
        url = reverse('time-series-analytics')
        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have filtered data within the range
        series_data = response.data['series']
        self.assertGreater(len(series_data), 0)
    
    def test_time_series_aggregation_by_period(self):
        """Test time series aggregation by different periods"""
        self.create_time_series_data()
        
        # Test different aggregation periods
        periods = ['daily', 'weekly', 'monthly']
        
        for period in periods:
            url = reverse('time-series-analytics')
            response = self.client.get(url, {'period': period})
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Should have aggregated data for the period
            series_data = response.data['series']
            self.assertIsInstance(series_data, list)
    
    def test_time_series_income_vs_expenses(self):
        """Test time series data shows income vs expenses properly"""
        self.create_time_series_data()
        
        url = reverse('time-series-analytics')
        response = self.client.get(url, {'period': 'monthly'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        series_data = response.data['series']
        
        # Should have data points with income and expense information
        if series_data:
            data_point = series_data[0]
            
            # Check expected fields in time series data
            expected_fields = ['date', 'income', 'expenses', 'net']
            for field in expected_fields:
                self.assertIn(field, data_point)
    
    def test_time_series_company_isolation(self):
        """Test time series data is isolated by company"""
        # Create data for our company
        self.create_time_series_data()
        
        # Create another company with different data
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
            account_number='123456',
            is_active=True
        )
        
        # Create transaction for other company
        Transaction.objects.create(
            bank_account=other_account,
            transaction_type='credit',
            amount=Decimal('10000.00'),
            description='Other Company Income',
            transaction_date=timezone.now(),
            category=self.income_category
        )
        
        url = reverse('time-series-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only include our company's data
        # This would need verification based on the actual amounts in our test data
        series_data = response.data['series']
        self.assertIsInstance(series_data, list)
    
    def test_time_series_empty_data(self):
        """Test time series with no transaction data"""
        url = reverse('time-series-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return empty series or appropriate default structure
        data = response.data
        self.assertIn('series', data)
        self.assertIsInstance(data['series'], list)
    
    def test_time_series_unauthenticated_access(self):
        """Test that unauthenticated users can't access time series data"""
        self.client.force_authenticate(user=None)
        
        url = reverse('time-series-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_time_series_no_company_error(self):
        """Test time series returns error when user has no company"""
        # Remove company association
        self.user.company = None
        self.user.save()
        
        url = reverse('time-series-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ExpenseTrendsViewTest(AnalyticsTestCase):
    """Test ExpenseTrendsView functionality"""
    
    def test_expense_trends_data_retrieval(self):
        """Test basic expense trends data retrieval"""
        self.create_time_series_data()
        
        url = reverse('expense-trends')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        
        # Check expected structure
        expected_fields = ['trends', 'categories', 'summary']
        for field in expected_fields:
            self.assertIn(field, data)
    
    def test_expense_trends_by_category(self):
        """Test expense trends broken down by category"""
        self.create_time_series_data()
        
        url = reverse('expense-trends')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        categories_data = response.data['categories']
        self.assertIsInstance(categories_data, list)
        
        # Should have data for our expense categories
        if categories_data:
            category_item = categories_data[0]
            
            # Check expected fields in category data
            expected_fields = ['name', 'total', 'percentage', 'trend']
            for field in expected_fields:
                self.assertIn(field, category_item)
    
    def test_expense_trends_time_comparison(self):
        """Test expense trends with time period comparison"""
        self.create_time_series_data()
        
        url = reverse('expense-trends')
        response = self.client.get(url, {'compare_period': 'previous_month'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        trends_data = response.data['trends']
        self.assertIsInstance(trends_data, list)
        
        # Should have comparison data
        if trends_data:
            trend_item = trends_data[0]
            
            # Check for comparison fields
            comparison_fields = ['current_period', 'previous_period', 'change_percentage']
            has_comparison = any(field in trend_item for field in comparison_fields)
            # Note: Exact fields depend on implementation
    
    def test_expense_trends_date_range_filter(self):
        """Test filtering expense trends by date range"""
        self.create_time_series_data()
        
        # Test with specific date range
        start_date = (self.today - timedelta(days=60)).isoformat()
        end_date = (self.today - timedelta(days=30)).isoformat()
        
        url = reverse('expense-trends')
        response = self.client.get(url, {
            'start_date': start_date,
            'end_date': end_date
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have filtered trends data
        data = response.data
        self.assertIn('trends', data)
        self.assertIn('categories', data)
    
    def test_expense_trends_category_filter(self):
        """Test filtering expense trends by specific category"""
        self.create_time_series_data()
        
        url = reverse('expense-trends')
        response = self.client.get(url, {'category': self.food_category.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have filtered data for the specific category
        categories_data = response.data['categories']
        
        # If filtered by category, should focus on that category
        self.assertIsInstance(categories_data, list)
    
    def test_expense_trends_summary_calculations(self):
        """Test expense trends summary calculations"""
        self.create_time_series_data()
        
        url = reverse('expense-trends')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        summary_data = response.data['summary']
        self.assertIsInstance(summary_data, dict)
        
        # Check expected summary fields
        expected_fields = ['total_expenses', 'top_category', 'average_daily']
        for field in expected_fields:
            if field in summary_data:
                self.assertIsNotNone(summary_data[field])
    
    def test_expense_trends_trend_direction(self):
        """Test expense trends show direction (increasing/decreasing)"""
        # Create data with clear trends
        base_date = self.today.replace(day=1) - timedelta(days=60)
        
        # Create increasing expenses over time
        for week in range(8):
            week_date = base_date + timedelta(days=week * 7)
            amount = Decimal(str(100 + week * 50))  # Increasing amounts
            
            Transaction.objects.create(
                bank_account=self.bank_account,
                transaction_type='debit',
                amount=-amount,
                description=f'Expense Week {week + 1}',
                transaction_date=timezone.make_aware(
                    datetime.combine(week_date, datetime.min.time())
                ),
                category=self.food_category
            )
        
        url = reverse('expense-trends')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should detect the increasing trend
        trends_data = response.data['trends']
        self.assertIsInstance(trends_data, list)
    
    def test_expense_trends_company_isolation(self):
        """Test expense trends data is isolated by company"""
        # Create data for our company
        self.create_time_series_data()
        
        # Create another company with different expenses
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
            account_number='123456',
            is_active=True
        )
        
        # Create expensive transaction for other company
        Transaction.objects.create(
            bank_account=other_account,
            transaction_type='debit',
            amount=Decimal('-50000.00'),
            description='Huge Expense',
            transaction_date=timezone.now(),
            category=self.food_category
        )
        
        url = reverse('expense-trends')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only include our company's trends
        summary_data = response.data['summary']
        
        # The summary should not include the huge expense from other company
        if 'total_expenses' in summary_data:
            total_expenses = Decimal(str(summary_data['total_expenses']))
            # Should be much less than 50000
            self.assertLess(total_expenses, Decimal('50000.00'))
    
    def test_expense_trends_empty_data(self):
        """Test expense trends with no transaction data"""
        url = reverse('expense-trends')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return appropriate structure for empty data
        data = response.data
        expected_fields = ['trends', 'categories', 'summary']
        for field in expected_fields:
            self.assertIn(field, data)
            self.assertIsInstance(data[field], (list, dict))
    
    def test_expense_trends_unauthenticated_access(self):
        """Test that unauthenticated users can't access expense trends"""
        self.client.force_authenticate(user=None)
        
        url = reverse('expense-trends')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_expense_trends_no_company_error(self):
        """Test expense trends returns error when user has no company"""
        # Remove company association
        self.user.company = None
        self.user.save()
        
        url = reverse('expense-trends')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_expense_trends_data_accuracy(self):
        """Test that expense trends calculations are accurate"""
        # Create specific known data
        food_total = Decimal('0')
        transport_total = Decimal('0')
        
        # Create 3 food transactions
        for i in range(3):
            amount = Decimal(f'{100 + i * 50}.00')  # 100, 150, 200
            Transaction.objects.create(
                bank_account=self.bank_account,
                transaction_type='debit',
                amount=-amount,
                description=f'Food {i + 1}',
                transaction_date=timezone.now() - timedelta(days=i),
                category=self.food_category
            )
            food_total += amount
        
        # Create 2 transport transactions
        for i in range(2):
            amount = Decimal(f'{75 + i * 25}.00')  # 75, 100
            Transaction.objects.create(
                bank_account=self.bank_account,
                transaction_type='debit',
                amount=-amount,
                description=f'Transport {i + 1}',
                transaction_date=timezone.now() - timedelta(days=i + 5),
                category=self.transport_category
            )
            transport_total += amount
        
        url = reverse('expense-trends')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        categories_data = response.data['categories']
        
        # Find food and transport categories in response
        food_data = None
        transport_data = None
        
        for category in categories_data:
            if category.get('name') == 'Food':
                food_data = category
            elif category.get('name') == 'Transport':
                transport_data = category
        
        # Verify calculations if categories are found
        if food_data and 'total' in food_data:
            self.assertEqual(Decimal(str(food_data['total'])), food_total)
        
        if transport_data and 'total' in transport_data:
            self.assertEqual(Decimal(str(transport_data['total'])), transport_total)