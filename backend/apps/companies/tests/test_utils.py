"""
Test utilities and helpers for companies app tests
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from apps.companies.models import Company, SubscriptionPlan, ResourceUsage
from .factories import (
    UserFactory, CompanyFactory, SubscriptionPlanFactory, 
    ResourceUsageFactory, TrialCompanyFactory, ActiveCompanyFactory
)

User = get_user_model()


class CompaniesTestMixin:
    """Mixin with common test utilities for companies app"""
    
    def setUp(self):
        """Set up common test data"""
        super().setUp()
        self.client = APIClient()
        
        # Create test users
        self.user1 = UserFactory(email='user1@test.com')
        self.user2 = UserFactory(email='user2@test.com')
        self.staff_user = UserFactory(email='staff@test.com', is_staff=True)
        
        # Create subscription plans
        self.basic_plan = SubscriptionPlanFactory(
            name='Basic',
            slug='basic',
            price_monthly=Decimal('9.99'),
            max_transactions=500,
            max_bank_accounts=2,
            max_ai_requests=50
        )
        self.premium_plan = SubscriptionPlanFactory(
            name='Premium',
            slug='premium',
            price_monthly=Decimal('19.99'),
            max_transactions=2000,
            max_bank_accounts=5,
            max_ai_requests=200,
            has_ai_insights=True
        )
        
        # Create test companies
        self.company1 = CompanyFactory(
            owner=self.user1,
            name='Test Company 1',
            subscription_plan=self.basic_plan
        )
        self.company2 = CompanyFactory(
            owner=self.user2,
            name='Test Company 2',
            subscription_plan=self.premium_plan
        )
    
    def authenticate_user(self, user):
        """Helper to authenticate a user"""
        self.client.force_authenticate(user=user)
    
    def create_usage_record(self, company, transactions=100, ai_requests=10):
        """Helper to create a usage record for testing"""
        return ResourceUsageFactory(
            company=company,
            transactions_count=transactions,
            ai_requests_count=ai_requests
        )
    
    def simulate_usage(self, company, transactions=0, ai_requests=0):
        """Helper to simulate usage for a company"""
        if transactions > 0:
            company.current_month_transactions = transactions
        if ai_requests > 0:
            company.current_month_ai_requests = ai_requests
        company.save()
    
    def expire_trial(self, company):
        """Helper to expire a company's trial"""
        company.trial_ends_at = timezone.now() - timedelta(days=1)
        company.subscription_status = 'trial'
        company.save()
        return company
    
    def activate_subscription(self, company, plan=None):
        """Helper to activate a company's subscription"""
        if plan:
            company.subscription_plan = plan
        company.subscription_status = 'active'
        company.subscription_id = 'sub_test123'
        company.trial_ends_at = None
        company.save()
        return company


class APITestMixin:
    """Mixin for API-specific test utilities"""
    
    def assert_api_success(self, response, expected_status=status.HTTP_200_OK):
        """Assert API response is successful"""
        self.assertEqual(response.status_code, expected_status)
        self.assertIsInstance(response.data, (dict, list))
    
    def assert_api_error(self, response, expected_status=status.HTTP_400_BAD_REQUEST, error_key=None):
        """Assert API response is an error"""
        self.assertEqual(response.status_code, expected_status)
        if error_key:
            self.assertIn(error_key, response.data)
    
    def assert_company_isolation(self, response, company):
        """Assert that response data is isolated to specific company"""
        if isinstance(response.data, dict):
            if 'id' in response.data:
                self.assertEqual(response.data['id'], str(company.id))
        elif isinstance(response.data, list):
            # For list responses, ensure all items belong to company
            for item in response.data:
                if 'company' in item:
                    self.assertEqual(item['company'], company.id)
    
    def get_companies_url(self, endpoint_name):
        """Helper to get companies app URLs"""
        return reverse(f'companies:{endpoint_name}')


class PermissionTestMixin:
    """Mixin for testing permission scenarios"""
    
    def assert_requires_authentication(self, url, method='get'):
        """Assert endpoint requires authentication"""
        self.client.force_authenticate(user=None)
        
        if method.lower() == 'get':
            response = self.client.get(url)
        elif method.lower() == 'post':
            response = self.client.post(url)
        elif method.lower() == 'put':
            response = self.client.put(url)
        elif method.lower() == 'delete':
            response = self.client.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def assert_company_ownership_required(self, url, user_without_access, method='get'):
        """Assert endpoint requires company ownership"""
        self.client.force_authenticate(user=user_without_access)
        
        if method.lower() == 'get':
            response = self.client.get(url)
        elif method.lower() == 'post':
            response = self.client.post(url)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # Should return 404 (company not found) rather than 403
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MockTestMixin:
    """Mixin for common mocking scenarios"""
    
    def mock_stripe_api(self):
        """Mock Stripe API calls"""
        with patch('stripe.Subscription.create') as mock_create, \
             patch('stripe.Subscription.retrieve') as mock_retrieve, \
             patch('stripe.Subscription.modify') as mock_modify:
            
            mock_create.return_value = MagicMock(id='sub_test123', status='active')
            mock_retrieve.return_value = MagicMock(id='sub_test123', status='active')
            mock_modify.return_value = MagicMock(id='sub_test123', status='cancelled')
            
            yield {
                'create': mock_create,
                'retrieve': mock_retrieve,
                'modify': mock_modify
            }
    
    def mock_external_apis(self):
        """Mock external API calls"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'success': True}
            yield mock_post


class CompaniesBaseTestCase(CompaniesTestMixin, APITestMixin, PermissionTestMixin, MockTestMixin, APITestCase):
    """Base test case class for companies app tests with all mixins"""
    pass


class CompaniesUnitTestCase(CompaniesTestMixin, MockTestMixin, TestCase):
    """Base test case for unit tests (without API client)"""
    pass


def create_test_subscription_plans():
    """Helper function to create standard test subscription plans"""
    plans = []
    
    # Basic plan
    basic = SubscriptionPlanFactory(
        name='Basic',
        slug='basic',
        price_monthly=Decimal('9.99'),
        price_yearly=Decimal('99.99'),
        max_transactions=500,
        max_bank_accounts=2,
        max_ai_requests=50,
        has_ai_insights=False,
        has_advanced_reports=False
    )
    plans.append(basic)
    
    # Premium plan
    premium = SubscriptionPlanFactory(
        name='Premium',
        slug='premium',
        price_monthly=Decimal('19.99'),
        price_yearly=Decimal('199.99'),
        max_transactions=2000,
        max_bank_accounts=5,
        max_ai_requests=200,
        has_ai_insights=True,
        has_advanced_reports=True
    )
    plans.append(premium)
    
    return plans


def assert_usage_within_limits(usage_data, plan):
    """Helper to assert usage is within plan limits"""
    assert usage_data['transactions']['used'] <= plan.max_transactions
    assert usage_data['bank_accounts']['used'] <= plan.max_bank_accounts
    assert usage_data['ai_requests']['used'] <= plan.max_ai_requests


def assert_subscription_status_valid(status_data):
    """Helper to validate subscription status response structure"""
    required_fields = [
        'subscription_status', 'plan', 'trial_days_left', 
        'trial_ends_at', 'requires_payment_setup', 'has_payment_method'
    ]
    
    for field in required_fields:
        assert field in status_data, f"Missing field: {field}"
    
    # Validate status is one of allowed values
    valid_statuses = ['trial', 'active', 'cancelled', 'expired', 'suspended']
    assert status_data['subscription_status'] in valid_statuses