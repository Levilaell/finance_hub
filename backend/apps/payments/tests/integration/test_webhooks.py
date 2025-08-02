"""
Integration tests for payment webhooks
"""
import json
from decimal import Decimal
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.payments.models import (
    Subscription,
    Payment,
    FailedWebhook,
)
from apps.payments.tests.factories import (
    SubscriptionPlanFactory,
    SubscriptionFactory,
    PaymentMethodFactory,
    FailedWebhookFactory,
)
from apps.companies.tests.factories import CompanyFactory
from apps.payments.services.webhook_handler import WebhookHandler


class StripeWebhookIntegrationTest(TestCase):
    """Integration tests for Stripe webhook handling"""
    
    def setUp(self):
        self.client = Client()
        self.webhook_url = reverse('payments:stripe-webhook')
        self.webhook_handler = WebhookHandler()
        
        # Create test data
        self.company = CompanyFactory()
        self.plan = SubscriptionPlanFactory()
        self.subscription = SubscriptionFactory(
            company=self.company,
            plan=self.plan,
            stripe_subscription_id='sub_test123'
        )
    
    def _send_webhook(self, event_type, event_data, event_id=None):
        """Helper method to send webhook request"""
        if not event_id:
            event_id = f'evt_{timezone.now().timestamp()}'
        
        payload = {
            'id': event_id,
            'type': event_type,
            'data': event_data,
            'created': int(timezone.now().timestamp())
        }
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = Mock(
                id=event_id,
                type=event_type,
                data=event_data
            )
            
            response = self.client.post(
                self.webhook_url,
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='test_signature'
            )
        
        return response
    
    def test_invoice_payment_succeeded_flow(self):
        """Test successful invoice payment flow"""
        # Set up payment method
        payment_method = PaymentMethodFactory(
            company=self.company,
            stripe_payment_method_id='pm_test123'
        )
        
        event_data = {
            'object': {
                'id': 'in_test123',
                'subscription': 'sub_test123',
                'customer': 'cus_test123',
                'amount_paid': 1999,  # Amount in cents
                'currency': 'brl',
                'payment_intent': 'pi_test123',
                'number': 'INV-0001',
                'payment_method': 'pm_test123'
            }
        }
        
        response = self._send_webhook('invoice.payment_succeeded', event_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify payment was created
        payment = Payment.objects.get(stripe_invoice_id='in_test123')
        self.assertEqual(payment.company, self.company)
        self.assertEqual(payment.amount, Decimal('19.99'))
        self.assertEqual(payment.status, 'succeeded')
        self.assertIsNotNone(payment.paid_at)
    
    def test_invoice_payment_failed_flow(self):
        """Test failed invoice payment flow"""
        event_data = {
            'object': {
                'id': 'in_test456',
                'subscription': 'sub_test123',
                'customer': 'cus_test123',
                'amount_due': 1999,
                'currency': 'brl',
                'payment_intent': 'pi_test456',
                'number': 'INV-0002'
            }
        }
        
        response = self._send_webhook('invoice.payment_failed', event_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify failed payment was created
        payment = Payment.objects.get(stripe_invoice_id='in_test456')
        self.assertEqual(payment.status, 'failed')
    
    def test_subscription_created_flow(self):
        """Test subscription created webhook flow"""
        new_company = CompanyFactory()
        
        event_data = {
            'object': {
                'id': 'sub_new789',
                'customer': 'cus_new789',
                'status': 'active',
                'current_period_start': int(timezone.now().timestamp()),
                'current_period_end': int((timezone.now() + timedelta(days=30)).timestamp()),
                'items': {
                    'data': [{
                        'price': {
                            'id': 'price_test123',
                            'product': 'prod_test123'
                        }
                    }]
                },
                'metadata': {
                    'company_id': str(new_company.id),
                    'plan_id': str(self.plan.id)
                }
            }
        }
        
        response = self._send_webhook('customer.subscription.created', event_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify subscription was created/updated
        subscription = Subscription.objects.get(stripe_subscription_id='sub_new789')
        self.assertEqual(subscription.company, new_company)
        self.assertEqual(subscription.status, 'active')
        self.assertTrue(subscription.is_active)
    
    def test_subscription_updated_flow(self):
        """Test subscription updated webhook flow"""
        event_data = {
            'object': {
                'id': 'sub_test123',
                'status': 'past_due',
                'cancel_at_period_end': False,
                'current_period_start': int(timezone.now().timestamp()),
                'current_period_end': int((timezone.now() + timedelta(days=30)).timestamp())
            }
        }
        
        response = self._send_webhook('customer.subscription.updated', event_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify subscription was updated
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, 'past_due')
    
    def test_subscription_deleted_flow(self):
        """Test subscription cancelled/deleted webhook flow"""
        event_data = {
            'object': {
                'id': 'sub_test123',
                'status': 'canceled',
                'canceled_at': int(timezone.now().timestamp())
            }
        }
        
        response = self._send_webhook('customer.subscription.deleted', event_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify subscription was cancelled
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, 'cancelled')
        self.assertFalse(self.subscription.is_active)
        self.assertIsNotNone(self.subscription.cancelled_at)
    
    def test_duplicate_webhook_handling(self):
        """Test handling of duplicate webhook events"""
        event_id = 'evt_duplicate123'
        event_data = {'object': {'id': 'test123'}}
        
        # Send first webhook
        response1 = self._send_webhook('invoice.payment_succeeded', event_data, event_id)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Send duplicate webhook
        response2 = self._send_webhook('invoice.payment_succeeded', event_data, event_id)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Both should succeed but handler should handle idempotency
    
    def test_webhook_error_handling(self):
        """Test webhook error handling and retry logic"""
        event_data = {
            'object': {
                'id': 'invalid_id',
                'subscription': 'sub_nonexistent'
            }
        }
        
        response = self._send_webhook('customer.subscription.updated', event_data)
        
        # Should still return 200 to prevent Stripe retries
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_webhook_signature_validation(self):
        """Test webhook signature validation"""
        payload = {
            'id': 'evt_test123',
            'type': 'invoice.payment_succeeded',
            'data': {'object': {'id': 'in_test123'}}
        }
        
        # Send without mocking signature validation
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_signature'
        )
        
        # Should reject invalid signature
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_webhook_retry_mechanism(self):
        """Test webhook retry mechanism for failed events"""
        # Create a failed webhook event
        failed_event = FailedWebhookFactory(
            event_type='invoice.payment_succeeded',
            retry_count=1,
            error_message='Temporary failure',
            event_data={
                'object': {
                    'id': 'in_retry123',
                    'subscription': 'sub_test123',
                    'amount_paid': 1999,
                    'currency': 'brl'
                }
            }
        )
        
        # Test that failed webhook can be retried
        self.assertTrue(failed_event.should_retry())
        
        # Increment retry
        failed_event.increment_retry()
        self.assertEqual(failed_event.retry_count, 2)
        self.assertGreater(failed_event.next_retry_at, timezone.now())