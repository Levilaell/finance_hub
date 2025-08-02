"""
Integration tests for payment API views
"""
import json
from decimal import Decimal
from unittest.mock import patch, Mock

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.payments.models import (
    SubscriptionPlan,
    Subscription,
    PaymentMethod,
    Payment,
    UsageRecord,
)
from apps.payments.tests.factories import (
    SubscriptionPlanFactory,
    SubscriptionFactory,
    PaymentMethodFactory,
    PaymentFactory,
    UsageRecordFactory,
)
from apps.companies.tests.factories import CompanyFactory, UserFactory


class PaymentAPITestCase(TestCase):
    """Base test case for payment API tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.company = CompanyFactory(owner=self.user)
        self.client.force_authenticate(user=self.user)
        
        # Set up the user's company association
        self.user.current_company = self.company
        self.user.save()


class SubscriptionPlanAPITest(PaymentAPITestCase):
    """Test cases for subscription plan API endpoints"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('payments:subscription-plans')
        
        # Create test plans
        self.basic_plan = SubscriptionPlanFactory(
            name='starter',
            display_name='Starter Plan',
            price_monthly=Decimal('9.99'),
            price_yearly=Decimal('99.90'),
            is_active=True
        )
        self.premium_plan = SubscriptionPlanFactory(
            name='professional',
            display_name='Professional Plan',
            price_monthly=Decimal('19.99'),
            price_yearly=Decimal('199.90'),
            is_active=True
        )
        self.inactive_plan = SubscriptionPlanFactory(
            name='enterprise',
            is_active=False
        )
    
    def test_list_subscription_plans(self):
        """Test listing all active subscription plans"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only active plans
        
        # Check ordering by price
        self.assertEqual(response.data[0]['name'], 'starter')
        self.assertEqual(response.data[1]['name'], 'professional')
    
    def test_list_plans_unauthenticated(self):
        """Test listing plans without authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        
        # Plans should be publicly accessible
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_plan_details_in_response(self):
        """Test plan details are properly serialized"""
        response = self.client.get(self.url)
        
        basic_plan_data = response.data[0]
        self.assertEqual(basic_plan_data['name'], 'starter')
        self.assertEqual(basic_plan_data['display_name'], 'Starter Plan')
        self.assertEqual(float(basic_plan_data['monthly_price']), 9.99)
        self.assertEqual(float(basic_plan_data['yearly_price']), 99.90)
        self.assertIn('features', basic_plan_data)
        self.assertIn('max_transactions', basic_plan_data)


class SubscriptionStatusAPITest(PaymentAPITestCase):
    """Test cases for subscription status API endpoint"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('payments:subscription-status')
        
        # Create a subscription for the company
        self.plan = SubscriptionPlanFactory(
            max_transactions=500,
            max_bank_accounts=5,
            max_ai_requests=100
        )
        self.subscription = SubscriptionFactory(
            company=self.company,
            plan=self.plan,
            status='active'
        )
        
        # Create usage records
        UsageRecordFactory(
            company=self.company,
            type='transaction',
            count=150
        )
        UsageRecordFactory(
            company=self.company,
            type='bank_account',
            count=2
        )
        UsageRecordFactory(
            company=self.company,
            type='ai_request',
            count=25
        )
    
    def test_get_subscription_status(self):
        """Test getting subscription status"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.company.id)
        self.assertEqual(response.data['name'], self.company.name)
        
        # Check subscription data
        self.assertIn('subscription', response.data)
        self.assertEqual(response.data['subscription']['status'], 'active')
        
        # Check usage data
        self.assertIn('current_usage', response.data)
        usage = response.data['current_usage']
        
        # Transaction usage
        self.assertEqual(usage['transaction']['count'], 150)
        self.assertEqual(usage['transaction']['limit'], 500)
        self.assertEqual(usage['transaction']['percentage'], 30.0)
        
        # Bank account usage
        self.assertEqual(usage['bank_account']['count'], 2)
        self.assertEqual(usage['bank_account']['limit'], 5)
        self.assertEqual(usage['bank_account']['percentage'], 40.0)
        
        # AI request usage
        self.assertEqual(usage['ai_request']['count'], 25)
        self.assertEqual(usage['ai_request']['limit'], 100)
        self.assertEqual(usage['ai_request']['percentage'], 25.0)
    
    def test_get_status_no_subscription(self):
        """Test getting status when company has no subscription"""
        # Delete the subscription
        self.subscription.delete()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['subscription'])
        # Should still return usage data with default limits
    
    def test_get_status_unauthenticated(self):
        """Test getting status without authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CheckoutAPITest(PaymentAPITestCase):
    """Test cases for checkout API endpoints"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('payments:checkout-create')
        self.plan = SubscriptionPlanFactory()
    
    @patch('apps.payments.services.stripe_service.StripeService.create_checkout_session')
    def test_create_checkout_session(self, mock_create_session):
        """Test creating a checkout session"""
        mock_create_session.return_value = {
            'session_id': 'cs_test123',
            'checkout_url': 'https://checkout.stripe.com/pay/cs_test123'
        }
        
        data = {
            'plan_id': self.plan.id,
            'billing_period': 'monthly',
            'success_url': 'https://example.com/success',
            'cancel_url': 'https://example.com/cancel'
        }
        
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['session_id'], 'cs_test123')
        self.assertEqual(response.data['checkout_url'], 'https://checkout.stripe.com/pay/cs_test123')
    
    def test_create_checkout_invalid_plan(self):
        """Test creating checkout with invalid plan ID"""
        data = {
            'plan_id': 9999,  # Non-existent plan
            'billing_period': 'monthly',
            'success_url': 'https://example.com/success',
            'cancel_url': 'https://example.com/cancel'
        }
        
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_validate_checkout_session(self):
        """Test validating a completed checkout session"""
        url = reverse('payments:checkout-validate')
        data = {'session_id': 'cs_test123'}
        
        with patch('apps.payments.services.stripe_service.StripeService.validate_checkout_session') as mock_validate:
            mock_validate.return_value = {'status': 'success'}
            response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')


class PaymentMethodAPITest(PaymentAPITestCase):
    """Test cases for payment method API endpoints"""
    
    def setUp(self):
        super().setUp()
        self.list_url = reverse('payments:payment-methods-list')
        self.payment_method = PaymentMethodFactory(
            company=self.company,
            type='card',
            brand='visa',
            last4='4242'
        )
    
    def test_list_payment_methods(self):
        """Test listing payment methods"""
        # Create additional payment methods
        PaymentMethodFactory(company=self.company, type='card', brand='mastercard')
        PaymentMethodFactory(company=self.company, type='pix')
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    @patch('apps.payments.services.stripe_service.StripeService.attach_payment_method')
    def test_create_payment_method(self, mock_attach):
        """Test creating a new payment method"""
        mock_attach.return_value = {
            'id': 'pm_test123',
            'type': 'card',
            'card': {'brand': 'visa', 'last4': '4242'}
        }
        
        data = {
            'type': 'card',
            'token': 'tok_visa',
            'is_default': True,
            'brand': 'visa',
            'last4': '4242',
            'exp_month': 12,
            'exp_year': 2025
        }
        
        response = self.client.post(self.list_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['type'], 'card')
        self.assertEqual(response.data['brand'], 'visa')
        self.assertTrue(response.data['is_default'])
    
    def test_update_payment_method(self):
        """Test updating a payment method"""
        url = reverse('payments:payment-methods-detail', args=[self.payment_method.id])
        data = {'is_default': True}
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment_method.refresh_from_db()
        self.assertTrue(self.payment_method.is_default)
    
    @patch('apps.payments.services.stripe_service.StripeService.detach_payment_method')
    def test_delete_payment_method(self, mock_detach):
        """Test deleting a payment method"""
        mock_detach.return_value = True
        
        url = reverse('payments:payment-methods-detail', args=[self.payment_method.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PaymentMethod.objects.filter(id=self.payment_method.id).exists())


class PaymentHistoryAPITest(PaymentAPITestCase):
    """Test cases for payment history API endpoint"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('payments:payment-history')
        
        # Create payment history
        self.payments = [
            PaymentFactory(
                company=self.company,
                amount=Decimal('19.99'),
                status='succeeded',
                created_at=timezone.now() - timezone.timedelta(days=i)
            )
            for i in range(5)
        ]
        
        # Add a failed payment
        PaymentFactory(
            company=self.company,
            amount=Decimal('19.99'),
            status='failed'
        )
    
    def test_list_payment_history(self):
        """Test listing payment history"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)
        
        # Check ordering (most recent first)
        dates = [payment['created_at'] for payment in response.data]
        self.assertEqual(dates, sorted(dates, reverse=True))
    
    def test_filter_by_status(self):
        """Test filtering payments by status"""
        response = self.client.get(self.url, {'status': 'succeeded'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        
        for payment in response.data:
            self.assertEqual(payment['status'], 'succeeded')


class SubscriptionCancellationAPITest(PaymentAPITestCase):
    """Test cases for subscription cancellation"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('payments:subscription-cancel')
        self.subscription = SubscriptionFactory(
            company=self.company,
            status='active',
            stripe_subscription_id='sub_test123'
        )
    
    @patch('apps.payments.services.stripe_service.StripeService.cancel_subscription')
    def test_cancel_subscription(self, mock_cancel):
        """Test cancelling an active subscription"""
        mock_cancel.return_value = True
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'cancelled')
        self.assertEqual(response.data['message'], 'Subscription cancelled successfully')
        
        # Check subscription was updated
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, 'cancelled')
        self.assertFalse(self.subscription.is_active)
        self.assertIsNotNone(self.subscription.cancelled_at)
    
    def test_cancel_no_subscription(self):
        """Test cancelling when no active subscription exists"""
        self.subscription.delete()
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class WebhookAPITest(TestCase):
    """Test cases for webhook endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('payments:stripe-webhook')
        self.company = CompanyFactory()
    
    @patch('stripe.Webhook.construct_event')
    def test_valid_webhook_event(self, mock_construct):
        """Test processing valid webhook event"""
        event_data = {
            'id': 'evt_test123',
            'type': 'invoice.payment_succeeded',
            'data': {
                'object': {
                    'id': 'in_test123',
                    'subscription': 'sub_test123',
                    'amount_paid': 1999,
                    'currency': 'brl',
                    'metadata': {'company_id': str(self.company.id)}
                }
            }
        }
        
        mock_construct.return_value = Mock(
            id='evt_test123',
            type='invoice.payment_succeeded',
            data=event_data['data']
        )
        
        response = self.client.post(
            self.url,
            data=json.dumps(event_data),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_invalid_webhook_signature(self):
        """Test webhook with invalid signature"""
        response = self.client.post(
            self.url,
            data=json.dumps({'id': 'evt_test123'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_signature'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)