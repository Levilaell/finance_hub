"""
Comprehensive tests for Companies app subscription management
Testing subscription upgrades, cancellations, and payment integration
"""
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.companies.models import SubscriptionPlan, Company, CompanyUser
from apps.companies.serializers import SubscriptionPlanSerializer

User = get_user_model()


class UpgradeSubscriptionViewTest(TestCase):
    """Test UpgradeSubscriptionView functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create subscription plans
        self.starter_plan = SubscriptionPlan.objects.create(
            name='Starter Plan',
            slug='starter',
            plan_type='starter',
            price_monthly=Decimal('29.90'),
            price_yearly=Decimal('299.00'),
            max_transactions=500,
            max_bank_accounts=1,
            max_users=1
        )
        
        self.pro_plan = SubscriptionPlan.objects.create(
            name='Professional Plan',
            slug='professional',
            plan_type='pro',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00'),
            max_transactions=5000,
            max_bank_accounts=10,
            max_users=5,
            has_advanced_reports=True,
            has_api_access=True
        )
        
        self.enterprise_plan = SubscriptionPlan.objects.create(
            name='Enterprise Plan',
            slug='enterprise',
            plan_type='enterprise',
            price_monthly=Decimal('199.90'),
            price_yearly=Decimal('1999.00'),
            max_transactions=50000,
            max_bank_accounts=50,
            max_users=50,
            has_advanced_reports=True,
            has_api_access=True,
            has_accountant_access=True
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
            owner=self.user,
            name='Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.starter_plan,
            subscription_status='active'
        )
        
        # Authenticate user
        self.client.force_authenticate(user=self.user)
        
        # Mock payment service
        self.payment_service_patcher = patch('apps.payments.payment_service.PaymentService')
        self.mock_payment_service_class = self.payment_service_patcher.start()
        self.mock_payment_service = MagicMock()
        self.mock_payment_service_class.return_value = self.mock_payment_service
    
    def tearDown(self):
        """Clean up patches"""
        self.payment_service_patcher.stop()
    
    def test_upgrade_subscription_success(self):
        """Test successful subscription upgrade"""
        # Mock successful payment processing
        self.mock_payment_service.create_subscription.return_value = {
            'client_secret': 'pi_test_client_secret',
            'subscription_id': 'sub_test_subscription_id'
        }
        
        upgrade_data = {
            'plan_id': self.pro_plan.id
        }
        
        response = self.client.post('/api/companies/subscription/upgrade/', upgrade_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('new_plan', response.data)
        self.assertIn('payment_intent', response.data)
        self.assertIn('subscription_id', response.data)
        
        # Verify company was updated
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_plan, self.pro_plan)
        self.assertEqual(self.company.subscription_status, 'active')
        
        # Verify payment service was called
        self.mock_payment_service.create_subscription.assert_called_once_with(
            self.company, self.pro_plan
        )
    
    def test_upgrade_subscription_with_mercadopago_response(self):
        """Test subscription upgrade with MercadoPago init_point"""
        # Mock MercadoPago payment processing
        self.mock_payment_service.create_subscription.return_value = {
            'init_point': 'https://mercadopago.com/checkout/test',
            'subscription_id': 'sub_test_subscription_id'
        }
        
        upgrade_data = {
            'plan_id': self.enterprise_plan.id
        }
        
        response = self.client.post('/api/companies/subscription/upgrade/', upgrade_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payment_url', response.data)
        self.assertEqual(
            response.data['payment_url'], 
            'https://mercadopago.com/checkout/test'
        )
        
        # Verify company was updated to enterprise plan
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_plan, self.enterprise_plan)
    
    def test_upgrade_subscription_invalid_plan(self):
        """Test upgrade with invalid plan ID"""
        upgrade_data = {
            'plan_id': 99999  # Non-existent plan
        }
        
        response = self.client.post('/api/companies/subscription/upgrade/', upgrade_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify company was not changed
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_plan, self.starter_plan)
    
    def test_upgrade_subscription_payment_failure(self):
        """Test upgrade with payment processing failure"""
        # Mock payment failure
        self.mock_payment_service.create_subscription.side_effect = Exception('Payment failed')
        
        upgrade_data = {
            'plan_id': self.pro_plan.id
        }
        
        response = self.client.post('/api/companies/subscription/upgrade/', upgrade_data)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Payment processing failed. Please try again.')
        
        # Verify company subscription plan was still updated (business logic)
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_plan, self.pro_plan)
    
    def test_upgrade_subscription_serializer_validation(self):
        """Test upgrade with invalid serializer data"""
        upgrade_data = {}  # Missing plan_id
        
        response = self.client.post('/api/companies/subscription/upgrade/', upgrade_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_upgrade_subscription_unauthenticated(self):
        """Test upgrade without authentication"""
        self.client.logout()
        
        upgrade_data = {
            'plan_id': self.pro_plan.id
        }
        
        response = self.client.post('/api/companies/subscription/upgrade/', upgrade_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_upgrade_subscription_without_payment_error(self):
        """Test upgrade fallback when payment service fails to import"""
        # Mock successful payment processing without payment_intent/init_point
        self.mock_payment_service.create_subscription.return_value = {
            'subscription_id': 'sub_test_subscription_id'
        }
        
        upgrade_data = {
            'plan_id': self.pro_plan.id
        }
        
        response = self.client.post('/api/companies/subscription/upgrade/', upgrade_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Subscription upgrade initiated')
    
    def test_upgrade_to_same_plan(self):
        """Test upgrading to the same plan"""
        upgrade_data = {
            'plan_id': self.starter_plan.id  # Same as current plan
        }
        
        response = self.client.post('/api/companies/subscription/upgrade/', upgrade_data)
        
        # Should still work (business decision)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_upgrade_subscription_plan_serialization(self):
        """Test that new plan is properly serialized in response"""
        self.mock_payment_service.create_subscription.return_value = {
            'client_secret': 'pi_test_client_secret',
            'subscription_id': 'sub_test_subscription_id'
        }
        
        upgrade_data = {
            'plan_id': self.pro_plan.id
        }
        
        response = self.client.post('/api/companies/subscription/upgrade/', upgrade_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_plan_data = SubscriptionPlanSerializer(self.pro_plan).data
        self.assertEqual(response.data['new_plan'], expected_plan_data)


class CancelSubscriptionViewTest(TestCase):
    """Test CancelSubscriptionView functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create subscription plan
        self.pro_plan = SubscriptionPlan.objects.create(
            name='Professional Plan',
            slug='professional',
            plan_type='pro',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00')
        )
        
        # Create user and company with active subscription
        self.user = User.objects.create_user(
            username='testuser2',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.pro_plan,
            subscription_status='active',
            subscription_id='sub_test_active'
        )
        
        # Authenticate user
        self.client.force_authenticate(user=self.user)
        
        # Mock payment service
        self.payment_service_patcher = patch('apps.payments.payment_service.PaymentService')
        self.mock_payment_service_class = self.payment_service_patcher.start()
        self.mock_payment_service = MagicMock()
        self.mock_payment_service_class.return_value = self.mock_payment_service
    
    def tearDown(self):
        """Clean up patches"""
        self.payment_service_patcher.stop()
    
    def test_cancel_subscription_success(self):
        """Test successful subscription cancellation"""
        # Mock successful payment cancellation
        self.mock_payment_service.cancel_subscription.return_value = True
        
        response = self.client.post('/api/companies/subscription/cancel/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Subscription cancelled successfully')
        
        # Verify company subscription was cancelled
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_status, 'cancelled')
        
        # Verify payment service was called
        self.mock_payment_service.cancel_subscription.assert_called_once_with(self.company)
    
    def test_cancel_subscription_no_active_subscription(self):
        """Test cancellation when no active subscription exists"""
        # Set company subscription to cancelled
        self.company.subscription_status = 'cancelled'
        self.company.save()
        
        response = self.client.post('/api/companies/subscription/cancel/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'No active subscription to cancel')
        
        # Verify payment service was not called
        self.mock_payment_service.cancel_subscription.assert_not_called()
    
    def test_cancel_subscription_trial_status(self):
        """Test cancellation when subscription is in trial"""
        # Set company subscription to trial
        self.company.subscription_status = 'trial'
        self.company.save()
        
        response = self.client.post('/api/companies/subscription/cancel/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'No active subscription to cancel')
    
    def test_cancel_subscription_payment_failure(self):
        """Test cancellation when payment provider fails"""
        # Mock payment service failure (returns False)
        self.mock_payment_service.cancel_subscription.return_value = False
        
        response = self.client.post('/api/companies/subscription/cancel/')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        self.assertEqual(
            response.data['error'], 
            'Failed to cancel subscription with payment provider'
        )
        
        # Verify company subscription was still cancelled locally
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_status, 'cancelled')
    
    def test_cancel_subscription_payment_exception(self):
        """Test cancellation when payment service raises exception"""
        # Mock payment service exception
        self.mock_payment_service.cancel_subscription.side_effect = Exception('Payment API error')
        
        response = self.client.post('/api/companies/subscription/cancel/')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        self.assertEqual(
            response.data['error'], 
            'Payment cancellation failed. Please contact support.'
        )
        
        # Verify company subscription was still cancelled locally
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_status, 'cancelled')
    
    def test_cancel_subscription_unauthenticated(self):
        """Test cancellation without authentication"""
        self.client.logout()
        
        response = self.client.post('/api/companies/subscription/cancel/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Verify company subscription was not changed
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_status, 'active')
    
    def test_cancel_subscription_past_due_status(self):
        """Test cancellation when subscription is past due"""
        # Set company subscription to past_due
        self.company.subscription_status = 'past_due'
        self.company.save()
        
        response = self.client.post('/api/companies/subscription/cancel/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'No active subscription to cancel')
    
    def test_cancel_subscription_suspended_status(self):
        """Test cancellation when subscription is suspended"""
        # Set company subscription to suspended
        self.company.subscription_status = 'suspended'
        self.company.save()
        
        response = self.client.post('/api/companies/subscription/cancel/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'No active subscription to cancel')


class SubscriptionPlansViewTest(TestCase):
    """Test SubscriptionPlansView functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create subscription plans
        self.starter_plan = SubscriptionPlan.objects.create(
            name='Starter Plan',
            slug='starter',
            plan_type='starter',
            price_monthly=Decimal('29.90'),
            price_yearly=Decimal('299.00'),
            is_active=True
        )
        
        self.pro_plan = SubscriptionPlan.objects.create(
            name='Professional Plan',
            slug='professional',
            plan_type='pro',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00'),
            is_active=True
        )
        
        self.inactive_plan = SubscriptionPlan.objects.create(
            name='Legacy Plan',
            slug='legacy',
            plan_type='pro',
            price_monthly=Decimal('79.90'),
            price_yearly=Decimal('799.00'),
            is_active=False  # Inactive plan
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
            owner=self.user,
            name='Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.starter_plan
        )
        
        # Authenticate user
        self.client.force_authenticate(user=self.user)
    
    def test_list_subscription_plans_success(self):
        """Test successful listing of active subscription plans"""
        response = self.client.get('/api/companies/subscription/plans/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only active plans
        
        # Verify plans are ordered by price
        plans = response.data
        self.assertEqual(plans[0]['slug'], 'starter')
        self.assertEqual(plans[1]['slug'], 'professional')
        
        # Verify inactive plan is not included
        plan_slugs = [plan['slug'] for plan in plans]
        self.assertNotIn('legacy', plan_slugs)
    
    def test_list_subscription_plans_unauthenticated(self):
        """Test listing plans without authentication"""
        self.client.logout()
        
        response = self.client.get('/api/companies/subscription/plans/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_subscription_plans_ordering(self):
        """Test that plans are properly ordered by monthly price"""
        # Create enterprise plan with higher price
        SubscriptionPlan.objects.create(
            name='Enterprise Plan',
            slug='enterprise',
            plan_type='enterprise',
            price_monthly=Decimal('199.90'),
            price_yearly=Decimal('1999.00'),
            is_active=True
        )
        
        response = self.client.get('/api/companies/subscription/plans/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Verify ordering by price
        prices = [Decimal(plan['price_monthly']) for plan in response.data]
        self.assertEqual(prices, sorted(prices))
    
    def test_subscription_plans_serialization(self):
        """Test that plans are properly serialized"""
        response = self.client.get('/api/companies/subscription/plans/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check first plan data
        plan = response.data[0]
        expected_fields = [
            'id', 'name', 'slug', 'plan_type', 'price_monthly', 'price_yearly',
            'max_transactions', 'max_bank_accounts', 'max_users',
            'has_ai_categorization', 'has_advanced_reports', 'has_api_access',
            'has_accountant_access'
        ]
        
        for field in expected_fields:
            self.assertIn(field, plan)


class SubscriptionManagementIntegrationTest(TestCase):
    """Integration tests for subscription management workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create subscription plans
        self.starter_plan = SubscriptionPlan.objects.create(
            name='Starter Plan',
            slug='starter',
            plan_type='starter',
            price_monthly=Decimal('29.90'),
            price_yearly=Decimal('299.00')
        )
        
        self.pro_plan = SubscriptionPlan.objects.create(
            name='Professional Plan',
            slug='professional',
            plan_type='pro',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00')
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
            owner=self.user,
            name='Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.starter_plan,
            subscription_status='trial'
        )
        
        # Authenticate user
        self.client.force_authenticate(user=self.user)
    
    @patch('apps.payments.payment_service.PaymentService')
    def test_complete_subscription_workflow(self, mock_payment_service_class):
        """Test complete workflow: list plans -> upgrade -> cancel"""
        mock_payment_service = MagicMock()
        mock_payment_service_class.return_value = mock_payment_service
        
        # Step 1: List available plans
        plans_response = self.client.get('/api/companies/subscription/plans/')
        self.assertEqual(plans_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(plans_response.data), 2)  # At least our 2 plans
        
        # Step 2: Upgrade to professional plan
        mock_payment_service.create_subscription.return_value = {
            'client_secret': 'pi_test_client_secret',
            'subscription_id': 'sub_test_subscription_id'
        }
        
        upgrade_response = self.client.post('/api/companies/subscription/upgrade/', {
            'plan_id': self.pro_plan.id
        })
        self.assertEqual(upgrade_response.status_code, status.HTTP_200_OK)
        
        # Verify upgrade
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_plan, self.pro_plan)
        self.assertEqual(self.company.subscription_status, 'active')
        
        # Step 3: Cancel subscription
        mock_payment_service.cancel_subscription.return_value = True
        
        cancel_response = self.client.post('/api/companies/subscription/cancel/')
        self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)
        
        # Verify cancellation
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_status, 'cancelled')
    
    @patch('apps.payments.payment_service.PaymentService')
    def test_subscription_status_consistency(self, mock_payment_service_class):
        """Test that subscription status remains consistent across operations"""
        mock_payment_service = MagicMock()
        mock_payment_service_class.return_value = mock_payment_service
        
        # Initial status should be trial
        self.assertEqual(self.company.subscription_status, 'trial')
        
        # Upgrade should change status to active
        mock_payment_service.create_subscription.return_value = {
            'subscription_id': 'sub_test_subscription_id'
        }
        
        self.client.post('/api/companies/subscription/upgrade/', {
            'plan_id': self.pro_plan.id
        })
        
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_status, 'active')
        
        # Cancel should change status to cancelled
        mock_payment_service.cancel_subscription.return_value = True
        
        self.client.post('/api/companies/subscription/cancel/')
        
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_status, 'cancelled')
        
        # Try to cancel again should fail
        cancel_again_response = self.client.post('/api/companies/subscription/cancel/')
        self.assertEqual(cancel_again_response.status_code, status.HTTP_400_BAD_REQUEST)