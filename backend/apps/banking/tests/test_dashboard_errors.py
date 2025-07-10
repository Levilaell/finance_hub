"""
Specific tests to prevent dashboard errors from recurring
"""
import json
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from apps.authentication.models import User
from apps.companies.models import Company, CompanyUser, SubscriptionPlan
from apps.banking.models import BankAccount, BankProvider


class TestDashboardErrorPrevention(APITestCase):
    """Tests to prevent specific dashboard errors"""
    
    def setUp(self):
        """Set up test data"""
        # Create minimal required data
        self.plan = SubscriptionPlan.objects.create(
            name='Test',
            slug='test',
            plan_type='starter',
            price_monthly=0,
            price_yearly=0
        )
        
        self.user = User.objects.create_user(
            email='error@test.com',
            username='error@test.com',
            password='Test123!'
        )
        
        self.company = Company.objects.create(
            name='Error Test Co',
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
    
    def test_dashboard_without_cache_service(self):
        """Test dashboard works even if cache service fails"""
        self.client.force_authenticate(user=self.user)
        
        # Mock cache service to be None (simulating import failure)
        with patch('apps.banking.views.cache_service', None):
            response = self.client.get(reverse('banking:enhanced-dashboard'))
            
            # Should not return 500 error
            self.assertNotEqual(response.status_code, 500)
            # Should return data or handle gracefully
            self.assertIn(response.status_code, [200, 503])  # OK or Service Unavailable
    
    def test_dashboard_with_redis_down(self):
        """Test dashboard works when Redis is down"""
        self.client.force_authenticate(user=self.user)
        
        # Mock cache operations to fail
        with patch('django.core.cache.cache.get') as mock_get:
            mock_get.side_effect = Exception('Redis connection error')
            
            response = self.client.get(reverse('banking:enhanced-dashboard'))
            
            # Should not return 500 error
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('basic_data', response.data)
    
    def test_dashboard_with_missing_company(self):
        """Test dashboard when user has no company"""
        # Create user without company
        orphan_user = User.objects.create_user(
            email='orphan@test.com',
            username='orphan@test.com',
            password='Test123!'
        )
        
        self.client.force_authenticate(user=orphan_user)
        
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        
        # Should return appropriate error, not 500
        self.assertIn(response.status_code, [400, 403, 404])
        self.assertNotEqual(response.status_code, 500)
    
    def test_dashboard_with_database_error(self):
        """Test dashboard handles database errors gracefully"""
        self.client.force_authenticate(user=self.user)
        
        # Mock database query to fail
        with patch('apps.banking.models.BankAccount.objects.filter') as mock_filter:
            mock_filter.side_effect = Exception('Database connection error')
            
            response = self.client.get(reverse('banking:enhanced-dashboard'))
            
            # Should handle error gracefully
            self.assertIn(response.status_code, [500, 503])
            if response.status_code == 500:
                # Check error message is appropriate
                self.assertIn('error', response.data)
    
    def test_dashboard_with_circular_import(self):
        """Test dashboard doesn't have circular import issues"""
        # This test ensures the import structure is correct
        try:
            from apps.banking.views import EnhancedDashboardView
            from apps.banking.cache_service import cache_service
            
            # Should be able to import without errors
            self.assertIsNotNone(EnhancedDashboardView)
            self.assertIsNotNone(cache_service)
        except ImportError as e:
            self.fail(f"Import error detected: {e}")
    
    def test_dashboard_with_null_values(self):
        """Test dashboard handles null values in data"""
        self.client.force_authenticate(user=self.user)
        
        # Create account with null values
        provider = BankProvider.objects.create(name='Test', code='001')
        BankAccount.objects.create(
            company=self.company,
            bank_provider=provider,
            account_type='checking',
            current_balance=None  # Null balance
        )
        
        response = self.client.get(reverse('banking:enhanced-dashboard'))
        
        # Should handle null values without 500 error
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('basic_data', response.data)
    
    def test_dashboard_concurrent_requests(self):
        """Test dashboard handles concurrent requests"""
        self.client.force_authenticate(user=self.user)
        
        # Simulate concurrent requests
        import threading
        results = []
        
        def make_request():
            response = self.client.get(reverse('banking:enhanced-dashboard'))
            results.append(response.status_code)
        
        threads = []
        for _ in range(5):
            t = threading.Thread(target=make_request)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All requests should succeed
        for status_code in results:
            self.assertEqual(status_code, status.HTTP_200_OK)


class TestDashboardImportError(TestCase):
    """Test specific import error that caused 500"""
    
    def test_cache_service_import(self):
        """Test cache_service can be imported correctly"""
        # This simulates the exact error that was happening
        try:
            from apps.banking import views
            
            # Check if cache_service is properly imported in views
            self.assertTrue(hasattr(views, 'cache_service') or 'cache_service' in dir(views))
            
            # Try to access EnhancedDashboardView
            view_class = views.EnhancedDashboardView
            self.assertIsNotNone(view_class)
            
        except ImportError as e:
            self.fail(f"Import error in banking views: {e}")
        except AttributeError as e:
            self.fail(f"Attribute error in banking views: {e}")
    
    def test_all_dashboard_endpoints(self):
        """Test all dashboard-related endpoints are accessible"""
        endpoints = [
            'banking:dashboard',
            'banking:dashboard-enhanced',
        ]
        
        # Create test user
        user = User.objects.create_user(
            email='endpoint@test.com',
            username='endpoint@test.com',
            password='Test123!'
        )
        
        plan = SubscriptionPlan.objects.create(
            name='Test',
            slug='test',
            plan_type='starter',
            price_monthly=0,
            price_yearly=0
        )
        
        company = Company.objects.create(
            name='Test Co',
            owner=user,
            subscription_plan=plan
        )
        
        CompanyUser.objects.create(
            user=user,
            company=company,
            role='owner'
        )
        
        user.company = company
        user.save()
        
        self.client.force_login(user)
        
        for endpoint in endpoints:
            try:
                url = reverse(endpoint)
                response = self.client.get(url)
                
                # Should not get 500 error
                self.assertNotEqual(
                    response.status_code, 
                    500, 
                    f"Endpoint {endpoint} returned 500 error"
                )
                
            except Exception as e:
                self.fail(f"Error accessing {endpoint}: {e}")


class TestDashboardRegressionPrevention(TransactionTestCase):
    """Regression tests to ensure dashboard errors don't reoccur"""
    
    def test_import_chain(self):
        """Test the complete import chain works"""
        # Test importing in the same order as the application
        from apps.banking.views import EnhancedDashboardView
        from apps.banking.cache_service import cache_service
        from apps.banking.serializers import (
            BankAccountSerializer,
            TransactionSerializer
        )
        
        # All imports should work
        self.assertIsNotNone(EnhancedDashboardView)
        self.assertIsNotNone(cache_service)
        self.assertIsNotNone(BankAccountSerializer)
        self.assertIsNotNone(TransactionSerializer)
    
    def test_cache_service_functionality(self):
        """Test cache service basic functionality"""
        from apps.banking.cache_service import cache_service
        
        # Test basic operations
        key = 'test_key'
        value = {'test': 'data'}
        
        # Use get_or_set method
        def get_value():
            return value
        
        # Set and get value
        retrieved = cache_service.get_or_set(key, get_value, timeout=60)
        self.assertEqual(retrieved, value)
        
        # Get existing value
        from django.core.cache import cache
        retrieved = cache.get(key)
        self.assertEqual(retrieved, value)
        
        # Delete value
        cache.delete(key)
        retrieved = cache.get(key)
        self.assertIsNone(retrieved)
    
    def test_dashboard_url_patterns(self):
        """Test dashboard URL patterns are correctly configured"""
        from django.urls import resolve
        
        # Test URL resolution
        enhanced_url = '/api/banking/dashboard/enhanced/'
        
        try:
            match = resolve(enhanced_url)
            self.assertEqual(match.url_name, 'enhanced-dashboard')
            self.assertEqual(match.app_name, 'banking')
        except Exception as e:
            self.fail(f"URL resolution failed: {e}")