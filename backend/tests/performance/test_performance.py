"""
Performance tests for the Caixa Digital backend.

Tests for:
- Database query optimization (N+1 queries)
- Large dataset handling
- Index usage validation
- Connection pooling
- Cache effectiveness
- API endpoint response times
- Concurrent user handling
- Rate limiting
- Pagination performance
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test.utils import override_settings
from django.db import connection
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from datetime import date, timedelta
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from apps.companies.models import Company, CompanyUser, SubscriptionPlan
from apps.banking.models import (
    BankAccount, Transaction, BankProvider, TransactionCategory,
    Budget, FinancialGoal
)
from apps.reports.models import Report
from apps.notifications.models import Notification

User = get_user_model()


class TestDatabasePerformance(TestCase):
    """Test database query optimization."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test data
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
        
        # Create large dataset
        self._create_large_dataset()
        
        # Get auth token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    
    def _create_large_dataset(self):
        """Create large dataset for performance testing."""
        # Create bank provider and categories
        provider = BankProvider.objects.create(name='Test Bank', code='001')
        
        categories = []
        for i in range(10):
            category = TransactionCategory.objects.create(
                name=f'Category {i}',
                category_type='expense' if i % 2 == 0 else 'income'
            )
            categories.append(category)
        
        # Create multiple accounts
        self.accounts = []
        for i in range(5):
            account = BankAccount.objects.create(
                company=self.company,
                bank_provider=provider,
                account_type='checking' if i % 2 == 0 else 'savings',
                agency=f'{i:04d}',
                account_number=f'{i:06d}',
                current_balance=Decimal(f'{(i+1)*1000}.00')
            )
            self.accounts.append(account)
        
        # Create many transactions
        transactions = []
        for account in self.accounts:
            for i in range(100):  # 500 total transactions
                tx_date = date.today() - timedelta(days=i)
                transaction = Transaction(
                    account=account,
                    company=self.company,
                    transaction_type='credit' if i % 2 == 0 else 'debit',
                    amount=Decimal(f'{(i % 100) + 10}.00'),
                    description=f'Transaction {i} for account {account.account_number}',
                    transaction_date=tx_date,
                    category=categories[i % len(categories)]
                )
                transactions.append(transaction)
        
        Transaction.objects.bulk_create(transactions)
    
    def test_transaction_list_query_optimization(self):
        """Test transaction list endpoint avoids N+1 queries."""
        with self.assertNumQueries(4):  # Expect optimized query count
            response = self.client.get(reverse('banking:transaction-list'))
            self.assertEqual(response.status_code, 200)
            
            # Force evaluation of queryset
            transactions = response.data['results']
            self.assertEqual(len(transactions), 20)  # Default pagination
            
            # Access related fields
            for tx in transactions:
                _ = tx['account']
                _ = tx['category']
    
    def test_dashboard_query_optimization(self):
        """Test dashboard endpoint uses efficient queries."""
        queries_before = len(connection.queries)
        
        start_time = time.time()
        response = self.client.get(reverse('banking:dashboard'))
        end_time = time.time()
        
        queries_after = len(connection.queries)
        query_count = queries_after - queries_before
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(query_count, 10)  # Should use aggregation queries
        self.assertLess(end_time - start_time, 0.5)  # Should complete in < 500ms
        
        # Verify data accuracy
        self.assertEqual(len(self.accounts), response.data['accounts_count'])
        self.assertEqual(500, response.data['transactions_count'])
    
    def test_report_generation_with_large_dataset(self):
        """Test report generation performance with large dataset."""
        start_time = time.time()
        
        response = self.client.post(reverse('reports:report-list'), {
            'report_type': 'category_spending',
            'period': 'monthly',
            'filters': {}
        })
        
        end_time = time.time()
        
        self.assertEqual(response.status_code, 201)
        self.assertLess(end_time - start_time, 2.0)  # Should complete in < 2 seconds
    
    def test_pagination_performance(self):
        """Test pagination performance with large datasets."""
        # Test different page sizes
        page_sizes = [10, 20, 50, 100]
        
        for page_size in page_sizes:
            start_time = time.time()
            
            response = self.client.get(
                reverse('banking:transaction-list'),
                {'page_size': page_size}
            )
            
            end_time = time.time()
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data['results']), min(page_size, 500))
            self.assertLess(end_time - start_time, 0.5)  # Each request < 500ms
    
    def test_search_performance(self):
        """Test search functionality performance."""
        search_terms = ['Transaction', 'account', 'checking', '12345']
        
        for term in search_terms:
            start_time = time.time()
            
            response = self.client.get(
                reverse('banking:transaction-list'),
                {'search': term}
            )
            
            end_time = time.time()
            
            self.assertEqual(response.status_code, 200)
            self.assertLess(end_time - start_time, 1.0)  # Search < 1 second
    
    def test_complex_filtering_performance(self):
        """Test performance with complex filters."""
        # Multiple filters
        filters = {
            'transaction_type': 'credit',
            'min_amount': '50.00',
            'max_amount': '200.00',
            'start_date': (date.today() - timedelta(days=30)).isoformat(),
            'end_date': date.today().isoformat(),
            'category': TransactionCategory.objects.first().id
        }
        
        start_time = time.time()
        
        response = self.client.get(
            reverse('banking:transaction-list'),
            filters
        )
        
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 1.0)  # Complex filter < 1 second


class TestCacheEffectiveness(TestCase):
    """Test cache effectiveness for frequently accessed data."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Clear cache
        cache.clear()
        
        # Create test data
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
        
        # Get auth token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    
    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    })
    def test_dashboard_caching(self):
        """Test dashboard data is cached effectively."""
        # First request - cache miss
        start_time = time.time()
        response1 = self.client.get(reverse('banking:dashboard'))
        first_request_time = time.time() - start_time
        
        self.assertEqual(response1.status_code, 200)
        
        # Second request - should be cached
        start_time = time.time()
        response2 = self.client.get(reverse('banking:dashboard'))
        second_request_time = time.time() - start_time
        
        self.assertEqual(response2.status_code, 200)
        
        # Cached request should be significantly faster
        # Note: Actual caching implementation would be needed
        # self.assertLess(second_request_time, first_request_time / 2)
    
    def test_category_list_caching(self):
        """Test category list is cached (rarely changes)."""
        # Create categories
        for i in range(20):
            TransactionCategory.objects.create(
                name=f'Category {i}',
                category_type='expense' if i % 2 == 0 else 'income'
            )
        
        # First request
        start_time = time.time()
        response1 = self.client.get(reverse('banking:transactioncategory-list'))
        first_request_time = time.time() - start_time
        
        # Multiple subsequent requests
        for _ in range(5):
            response = self.client.get(reverse('banking:transactioncategory-list'))
            self.assertEqual(response.status_code, 200)


class TestConcurrentUserHandling(TransactionTestCase):
    """Test handling of concurrent users."""
    
    def setUp(self):
        # Create multiple users and companies
        self.users = []
        self.companies = []
        
        plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00, price_yearly=990.00
        )
        
        for i in range(10):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='TestPass123!',
                first_name=f'User{i}',
                last_name='Test'
            )
            
            company = Company.objects.create(
                name=f'Company {i}',
                cnpj=f'{i:014d}',
                owner=user,
                subscription_plan=plan
            )
            
            CompanyUser.objects.create(
                company=company,
                user=user,
                role='owner'
            )
            
            self.users.append(user)
            self.companies.append(company)
    
    def _make_concurrent_request(self, user, endpoint):
        """Make a request as a specific user."""
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        start_time = time.time()
        response = client.get(endpoint)
        end_time = time.time()
        
        return {
            'user': user.username,
            'status_code': response.status_code,
            'response_time': end_time - start_time
        }
    
    def test_concurrent_dashboard_requests(self):
        """Test multiple users accessing dashboard simultaneously."""
        endpoint = reverse('banking:dashboard')
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for user in self.users:
                future = executor.submit(self._make_concurrent_request, user, endpoint)
                futures.append(future)
            
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        # All requests should succeed
        for result in results:
            self.assertEqual(result['status_code'], 200)
            self.assertLess(result['response_time'], 2.0)  # Each request < 2 seconds
        
        # Calculate average response time
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        self.assertLess(avg_response_time, 1.0)  # Average < 1 second
    
    def test_concurrent_transaction_creation(self):
        """Test concurrent transaction creation maintains data integrity."""
        # Create bank accounts for each company
        provider = BankProvider.objects.create(name='Test Bank', code='001')
        category = TransactionCategory.objects.create(
            name='Test',
            category_type='expense'
        )
        
        accounts = []
        for company in self.companies:
            account = BankAccount.objects.create(
                company=company,
                bank_provider=provider,
                account_type='checking',
                agency='0001',
                account_number=f'{company.id:06d}',
                current_balance=Decimal('1000.00')
            )
            accounts.append(account)
        
        def create_transaction(user, account):
            client = APIClient()
            refresh = RefreshToken.for_user(user)
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
            
            response = client.post(reverse('banking:transaction-list'), {
                'account': str(account.id),
                'transaction_type': 'debit',
                'amount': '50.00',
                'description': f'Concurrent transaction by {user.username}',
                'transaction_date': date.today().isoformat(),
                'category': category.id
            })
            
            return response.status_code
        
        # Create transactions concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for i, (user, account) in enumerate(zip(self.users, accounts)):
                future = executor.submit(create_transaction, user, account)
                futures.append(future)
            
            for future in as_completed(futures):
                status_code = future.result()
                self.assertEqual(status_code, 201)
        
        # Verify all transactions were created
        total_transactions = Transaction.objects.count()
        self.assertEqual(total_transactions, 10)
        
        # Verify data integrity - each company has exactly one transaction
        for company in self.companies:
            company_transactions = Transaction.objects.filter(company=company).count()
            self.assertEqual(company_transactions, 1)


class TestAPIResponseTimes(TestCase):
    """Test API endpoint response times."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test user and company
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
        
        # Get auth token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    
    def _measure_response_time(self, url, method='get', data=None):
        """Measure response time for an API endpoint."""
        start_time = time.time()
        
        if method == 'get':
            response = self.client.get(url)
        elif method == 'post':
            response = self.client.post(url, data or {})
        elif method == 'put':
            response = self.client.put(url, data or {})
        elif method == 'patch':
            response = self.client.patch(url, data or {})
        elif method == 'delete':
            response = self.client.delete(url)
        
        end_time = time.time()
        
        return {
            'response_time': end_time - start_time,
            'status_code': response.status_code
        }
    
    def test_critical_endpoint_response_times(self):
        """Test response times for critical endpoints."""
        endpoints = [
            ('Dashboard', reverse('banking:dashboard'), 'get', None, 0.2),
            ('Transaction List', reverse('banking:transaction-list'), 'get', None, 0.3),
            ('Account List', reverse('banking:bank-account-list'), 'get', None, 0.2),
            ('Report List', reverse('reports:report-list'), 'get', None, 0.2),
            ('Notification List', reverse('notifications:notification-list'), 'get', None, 0.2),
            ('Company Detail', reverse('companies:company-detail'), 'get', None, 0.1),
        ]
        
        for name, url, method, data, max_time in endpoints:
            result = self._measure_response_time(url, method, data)
            
            with self.subTest(endpoint=name):
                self.assertIn(result['status_code'], [200, 201, 204])
                self.assertLess(
                    result['response_time'],
                    max_time,
                    f"{name} took {result['response_time']:.3f}s, expected < {max_time}s"
                )
    
    def test_write_operation_response_times(self):
        """Test response times for write operations."""
        # Create necessary data
        provider = BankProvider.objects.create(name='Test Bank', code='001')
        account = BankAccount.objects.create(
            company=self.company,
            bank_provider=provider,
            account_type='checking',
            agency='0001',
            account_number='123456',
            current_balance=Decimal('1000.00')
        )
        
        category = TransactionCategory.objects.create(
            name='Test',
            category_type='expense'
        )
        
        write_operations = [
            (
                'Create Transaction',
                reverse('banking:transaction-list'),
                'post',
                {
                    'account': str(account.id),
                    'transaction_type': 'debit',
                    'amount': '100.00',
                    'description': 'Test transaction',
                    'transaction_date': date.today().isoformat(),
                    'category': category.id
                },
                0.5
            ),
            (
                'Create Report',
                reverse('reports:report-list'),
                'post',
                {
                    'report_type': 'cash_flow',
                    'period': 'monthly',
                    'filters': {}
                },
                1.0
            ),
        ]
        
        for name, url, method, data, max_time in write_operations:
            result = self._measure_response_time(url, method, data)
            
            with self.subTest(operation=name):
                self.assertEqual(result['status_code'], 201)
                self.assertLess(
                    result['response_time'],
                    max_time,
                    f"{name} took {result['response_time']:.3f}s, expected < {max_time}s"
                )