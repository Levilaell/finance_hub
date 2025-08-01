"""
Integration tests for companies app views and API endpoints
"""
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import timedelta
from unittest.mock import patch

from apps.companies.models import Company, SubscriptionPlan, ResourceUsage
from apps.banking.models import BankAccount
from .factories import (
    UserFactory, CompanyFactory, SubscriptionPlanFactory, 
    ResourceUsageFactory, TrialCompanyFactory, ActiveCompanyFactory
)
from .test_utils import CompaniesBaseTestCase, assert_subscription_status_valid

User = get_user_model()


class PublicSubscriptionPlansViewTest(APITestCase):
    """Test PublicSubscriptionPlansView (no authentication required)"""
    
    def setUp(self):
        self.url = reverse('companies:public-plans')
        
        # Create test plans
        self.active_plan = SubscriptionPlanFactory(
            name='Basic',
            is_active=True,
            display_order=1
        )
        self.inactive_plan = SubscriptionPlanFactory(
            name='Inactive',
            is_active=False,
            display_order=2
        )
    
    def test_get_public_plans_success(self):
        """Test getting public subscription plans"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        # Should only return active plans
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Basic')
    
    def test_public_plans_ordering(self):
        """Test that plans are ordered by display_order"""
        plan2 = SubscriptionPlanFactory(
            name='Premium',
            is_active=True,
            display_order=0  # Should come first
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Premium')  # display_order 0
        self.assertEqual(response.data[1]['name'], 'Basic')    # display_order 1
    
    def test_public_plans_no_authentication_required(self):
        """Test that no authentication is required for public plans"""
        # Ensure no user is authenticated
        self.client.force_authenticate(user=None)
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SubscriptionPlansViewTest(CompaniesBaseTestCase):
    """Test SubscriptionPlansView (authenticated)"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('companies:plans')
    
    def test_get_plans_requires_authentication(self):
        """Test that authenticated endpoint requires authentication"""
        self.assert_requires_authentication(self.url)
    
    def test_get_plans_success(self):
        """Test getting subscription plans when authenticated"""
        self.authenticate_user(self.user1)
        
        response = self.client.get(self.url)
        
        self.assert_api_success(response)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        
        # Check plan structure
        plan_data = response.data[0]
        expected_fields = [
            'id', 'name', 'slug', 'price_monthly', 'price_yearly',
            'max_transactions', 'max_bank_accounts', 'max_ai_requests',
            'has_ai_insights', 'has_advanced_reports', 'yearly_discount'
        ]
        
        for field in expected_fields:
            self.assertIn(field, plan_data)


class CompanyDetailViewTest(CompaniesBaseTestCase):
    """Test CompanyDetailView"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('companies:detail')
    
    def test_get_company_detail_requires_authentication(self):
        """Test that company detail requires authentication"""
        self.assert_requires_authentication(self.url)
    
    def test_get_company_detail_success(self):
        """Test getting company details"""
        self.authenticate_user(self.user1)
        
        response = self.client.get(self.url)
        
        self.assert_api_success(response)
        self.assert_company_isolation(response, self.company1)
        
        # Check response structure
        expected_fields = [
            'id', 'name', 'owner_email', 'subscription_plan', 'subscription_status',
            'billing_cycle', 'trial_ends_at', 'is_trial_active', 'days_until_trial_ends',
            'current_month_transactions', 'current_month_ai_requests', 'created_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, response.data)
        
        # Check company data
        self.assertEqual(response.data['name'], self.company1.name)
        self.assertEqual(response.data['owner_email'], self.user1.email)
    
    def test_get_company_detail_without_company(self):
        """Test getting company details for user without company"""
        user_without_company = UserFactory()
        self.authenticate_user(user_without_company)
        
        response = self.client.get(self.url)
        
        self.assert_api_error(response, status.HTTP_404_NOT_FOUND, 'error')
        self.assertEqual(response.data['error'], 'Company not found')
    
    def test_company_isolation(self):
        """Test that users can only see their own company"""
        # User1 should see company1
        self.authenticate_user(self.user1)
        response = self.client.get(self.url)
        self.assert_api_success(response)
        self.assertEqual(response.data['id'], str(self.company1.id))
        
        # User2 should see company2
        self.authenticate_user(self.user2)
        response = self.client.get(self.url)
        self.assert_api_success(response)
        self.assertEqual(response.data['id'], str(self.company2.id))


class UsageLimitsViewTest(CompaniesBaseTestCase):
    """Test UsageLimitsView"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('companies:usage-limits')
        
        # Create bank accounts for testing
        self.bank1 = BankAccount.objects.create(
            company=self.company1,
            name='Bank 1',
            account_number='12345',
            is_active=True
        )
        self.bank2 = BankAccount.objects.create(
            company=self.company2,
            name='Bank 2',
            account_number='67890',
            is_active=True
        )
    
    def test_get_usage_limits_requires_authentication(self):
        """Test that usage limits requires authentication"""
        self.assert_requires_authentication(self.url)
    
    def test_get_usage_limits_success(self):
        """Test getting usage limits"""
        # Set some usage for company1
        self.simulate_usage(self.company1, transactions=150, ai_requests=25)
        
        self.authenticate_user(self.user1)
        response = self.client.get(self.url)
        
        self.assert_api_success(response)
        
        # Check response structure
        expected_keys = ['transactions', 'bank_accounts', 'ai_requests']
        for key in expected_keys:
            self.assertIn(key, response.data)
            
            # Each usage type should have used, limit, percentage
            usage_data = response.data[key]
            self.assertIn('used', usage_data)
            self.assertIn('limit', usage_data)
            self.assertIn('percentage', usage_data)
        
        # Check specific values
        self.assertEqual(response.data['transactions']['used'], 150)
        self.assertEqual(response.data['transactions']['limit'], self.basic_plan.max_transactions)
        
        self.assertEqual(response.data['bank_accounts']['used'], 1)  # One bank account
        self.assertEqual(response.data['bank_accounts']['limit'], self.basic_plan.max_bank_accounts)
        
        self.assertEqual(response.data['ai_requests']['used'], 25)
        self.assertEqual(response.data['ai_requests']['limit'], self.basic_plan.max_ai_requests)
    
    def test_usage_limits_with_no_plan(self):
        """Test usage limits for company with no subscription plan"""
        company_no_plan = CompanyFactory(
            owner=UserFactory(),
            subscription_plan=None
        )
        
        self.authenticate_user(company_no_plan.owner)
        response = self.client.get(self.url)
        
        self.assert_api_success(response)
        
        # Should use default limits
        self.assertEqual(response.data['transactions']['limit'], 100)
        self.assertEqual(response.data['bank_accounts']['limit'], 2)
        self.assertEqual(response.data['ai_requests']['limit'], 10)
    
    def test_usage_limits_isolation(self):
        """Test that usage limits are isolated by company"""
        # Company1 has 1 bank account
        self.authenticate_user(self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.data['bank_accounts']['used'], 1)
        
        # Company2 has 1 bank account (different from company1)
        self.authenticate_user(self.user2)
        response = self.client.get(self.url)
        self.assertEqual(response.data['bank_accounts']['used'], 1)
    
    def test_usage_limits_percentage_calculation(self):
        """Test that usage percentages are calculated correctly"""
        # Set usage that's exactly 50% of limits
        plan = self.company1.subscription_plan
        self.simulate_usage(
            self.company1,
            transactions=plan.max_transactions // 2,
            ai_requests=plan.max_ai_requests // 2
        )
        
        self.authenticate_user(self.user1)
        response = self.client.get(self.url)
        
        # Percentages should be around 50%
        self.assertAlmostEqual(response.data['transactions']['percentage'], 50, delta=1)
        self.assertAlmostEqual(response.data['ai_requests']['percentage'], 50, delta=1)
    
    def test_usage_limits_creates_resource_usage(self):
        """Test that getting usage limits creates ResourceUsage record"""
        # Ensure no ResourceUsage exists initially
        self.assertEqual(ResourceUsage.objects.filter(company=self.company1).count(), 0)
        
        self.authenticate_user(self.user1)
        response = self.client.get(self.url)
        
        self.assert_api_success(response)
        
        # Should create ResourceUsage record
        self.assertEqual(ResourceUsage.objects.filter(company=self.company1).count(), 1)


class SubscriptionStatusViewTest(CompaniesBaseTestCase):
    """Test SubscriptionStatusView"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('companies:subscription-status')
    
    def test_get_subscription_status_requires_authentication(self):
        """Test that subscription status requires authentication"""
        self.assert_requires_authentication(self.url)
    
    def test_get_subscription_status_trial(self):
        """Test getting subscription status for trial company"""
        trial_company = TrialCompanyFactory(owner=UserFactory())
        
        self.authenticate_user(trial_company.owner)
        response = self.client.get(self.url)
        
        self.assert_api_success(response)
        assert_subscription_status_valid(response.data)
        
        # Check trial-specific data
        self.assertEqual(response.data['subscription_status'], 'trial')
        self.assertGreater(response.data['trial_days_left'], 0)
        self.assertIsNotNone(response.data['trial_ends_at'])
        self.assertTrue(response.data['requires_payment_setup'])
        self.assertFalse(response.data['has_payment_method'])
    
    def test_get_subscription_status_active(self):
        """Test getting subscription status for active company"""
        active_company = ActiveCompanyFactory(owner=UserFactory())
        
        self.authenticate_user(active_company.owner)
        response = self.client.get(self.url)
        
        self.assert_api_success(response)
        assert_subscription_status_valid(response.data)
        
        # Check active subscription data
        self.assertEqual(response.data['subscription_status'], 'active')
        self.assertEqual(response.data['trial_days_left'], 0)
        self.assertIsNone(response.data['trial_ends_at'])
        self.assertFalse(response.data['requires_payment_setup'])
        self.assertTrue(response.data['has_payment_method'])
    
    def test_subscription_status_with_plan(self):
        """Test subscription status includes plan data"""
        self.authenticate_user(self.user1)
        response = self.client.get(self.url)
        
        self.assert_api_success(response)
        
        # Should include plan data
        self.assertIsNotNone(response.data['plan'])
        plan_data = response.data['plan']
        self.assertEqual(plan_data['name'], self.basic_plan.name)
        self.assertIn('price_monthly', plan_data)
    
    def test_subscription_status_isolation(self):
        """Test that subscription status is isolated by company"""
        # Set different statuses for companies
        self.company1.subscription_status = 'trial'
        self.company1.save()
        
        self.company2.subscription_status = 'active'
        self.company2.save()
        
        # User1 should see trial status
        self.authenticate_user(self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.data['subscription_status'], 'trial')
        
        # User2 should see active status
        self.authenticate_user(self.user2)
        response = self.client.get(self.url)
        self.assertEqual(response.data['subscription_status'], 'active')


class ViewIntegrationTest(CompaniesBaseTestCase):
    """Test integration scenarios across multiple views"""
    
    def test_company_lifecycle_through_apis(self):
        """Test complete company lifecycle through API endpoints"""
        # Create a new user and company
        user = UserFactory()
        company = TrialCompanyFactory(owner=user)
        
        self.authenticate_user(user)
        
        # 1. Get company details
        detail_response = self.client.get(reverse('companies:detail'))
        self.assert_api_success(detail_response)
        self.assertEqual(detail_response.data['subscription_status'], 'trial')
        
        # 2. Check subscription status
        status_response = self.client.get(reverse('companies:subscription-status'))
        self.assert_api_success(status_response)
        self.assertTrue(status_response.data['requires_payment_setup'])
        
        # 3. Check usage limits (should use trial defaults)
        usage_response = self.client.get(reverse('companies:usage-limits'))
        self.assert_api_success(usage_response)
        
        # 4. Simulate usage
        company.increment_usage('transactions')
        company.increment_usage('ai_requests')
        
        # 5. Check updated usage
        usage_response = self.client.get(reverse('companies:usage-limits'))
        self.assert_api_success(usage_response)
        self.assertEqual(usage_response.data['transactions']['used'], 1)
        self.assertEqual(usage_response.data['ai_requests']['used'], 1)
    
    def test_multiple_users_isolation(self):
        """Test that multiple users can't access each other's data"""
        endpoints = [
            'companies:detail',
            'companies:usage-limits',
            'companies:subscription-status'
        ]
        
        for endpoint_name in endpoints:
            url = reverse(endpoint_name)
            
            # User1 should get their data
            self.authenticate_user(self.user1)
            response1 = self.client.get(url)
            self.assert_api_success(response1)
            
            # User2 should get their data (different from user1)
            self.authenticate_user(self.user2)
            response2 = self.client.get(url)
            self.assert_api_success(response2)
            
            # Responses should be different (except for plans endpoint)
            if endpoint_name != 'companies:plans':
                self.assertNotEqual(response1.data, response2.data)
    
    def test_view_error_handling(self):
        """Test error handling across views"""
        user_without_company = UserFactory()
        
        error_endpoints = [
            'companies:detail',
            'companies:usage-limits',
            'companies:subscription-status'
        ]
        
        for endpoint_name in error_endpoints:
            url = reverse(endpoint_name)
            
            self.authenticate_user(user_without_company)
            response = self.client.get(url)
            
            # Should return 404 with proper error message
            self.assert_api_error(response, status.HTTP_404_NOT_FOUND, 'error')
            self.assertEqual(response.data['error'], 'Company not found')
    
    @patch('apps.companies.views.BankAccount.objects')
    def test_view_with_database_error(self, mock_bank_accounts):
        """Test view behavior with database errors"""
        # Mock database error
        mock_bank_accounts.filter.side_effect = Exception("Database connection error")
        
        self.authenticate_user(self.user1)
        response = self.client.get(reverse('companies:usage-limits'))
        
        # Should handle the error gracefully
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def test_concurrent_usage_tracking(self):
        """Test that concurrent API calls handle usage tracking correctly"""
        from threading import Thread
        import time
        
        def make_usage_request():
            # Simulate usage increment through API side effects
            self.company1.increment_usage('transactions')
            time.sleep(0.1)  # Small delay to simulate processing
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = Thread(target=make_usage_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check final usage count
        self.company1.refresh_from_db()
        self.assertEqual(self.company1.current_month_transactions, 5)