"""
Test payment webhook views
Tests for stripe_webhook and mercadopago_webhook views
"""
import json
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.companies.models import Company, SubscriptionPlan

User = get_user_model()


class TestStripeWebhookView(TestCase):
    """Test Stripe webhook endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/payments/webhooks/stripe/'
    
    @patch('apps.payments.views.PaymentService')
    @patch('apps.payments.views.logger')
    def test_stripe_webhook_success(self, mock_logger, mock_service_class):
        """Test successful Stripe webhook processing"""
        # Setup mock
        mock_service = Mock()
        mock_service.handle_webhook.return_value = {
            'event_type': 'customer.subscription.created',
            'event_id': 'evt_123',
            'data': {}
        }
        mock_service_class.return_value = mock_service
        
        # Send webhook
        webhook_data = {
            'id': 'evt_123',
            'type': 'customer.subscription.created',
            'data': {'object': {'id': 'sub_123'}}
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(webhook_data),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='sig_123'
        )
        
        # Verify
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        mock_service_class.assert_called_once_with(gateway_name='stripe')
        mock_service.handle_webhook.assert_called_once()
        mock_logger.info.assert_called()
    
    @patch('apps.payments.views.PaymentService')
    @patch('apps.payments.views.logger')
    def test_stripe_webhook_error(self, mock_logger, mock_service_class):
        """Test Stripe webhook with error"""
        # Setup mock to raise exception
        mock_service = Mock()
        mock_service.handle_webhook.side_effect = Exception('Invalid signature')
        mock_service_class.return_value = mock_service
        
        # Send webhook
        response = self.client.post(
            self.url,
            data='invalid data',
            content_type='application/json'
        )
        
        # Verify
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid signature')
        mock_logger.error.assert_called()
    
    def test_stripe_webhook_allows_anonymous(self):
        """Test that Stripe webhook allows anonymous access"""
        # Ensure no authentication required
        response = self.client.post(self.url, data={})
        
        # Should not return 401 (might return 400 for bad request)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @patch('apps.payments.views.PaymentService')
    def test_stripe_webhook_different_event_types(self, mock_service_class):
        """Test handling different Stripe event types"""
        event_types = [
            'customer.subscription.created',
            'customer.subscription.updated',
            'customer.subscription.deleted',
            'invoice.payment_succeeded',
            'invoice.payment_failed',
            'payment_intent.succeeded',
            'payment_intent.payment_failed'
        ]
        
        for event_type in event_types:
            # Setup mock
            mock_service = Mock()
            mock_service.handle_webhook.return_value = {
                'event_type': event_type,
                'event_id': f'evt_{event_type}',
                'data': {}
            }
            mock_service_class.return_value = mock_service
            
            # Send webhook
            webhook_data = {
                'id': f'evt_{event_type}',
                'type': event_type,
                'data': {'object': {}}
            }
            
            response = self.client.post(
                self.url,
                data=json.dumps(webhook_data),
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='sig_123'
            )
            
            # Verify
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], 'success')
    
    @patch('apps.payments.views.PaymentService')
    def test_stripe_webhook_with_headers(self, mock_service_class):
        """Test Stripe webhook properly passes signature header"""
        # Setup mock
        mock_service = Mock()
        mock_service.handle_webhook.return_value = {
            'event_type': 'test',
            'event_id': 'evt_test',
            'data': {}
        }
        mock_service_class.return_value = mock_service
        
        # Send webhook with specific signature
        signature = 'v1=5257a869e7ecb....'
        response = self.client.post(
            self.url,
            data='webhook body',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE=signature
        )
        
        # Verify handle_webhook was called with request
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        call_args = mock_service.handle_webhook.call_args[0][0]
        self.assertEqual(call_args.META.get('HTTP_STRIPE_SIGNATURE'), signature)


class TestMercadoPagoWebhookView(TestCase):
    """Test MercadoPago webhook endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/payments/webhooks/mercadopago/'
    
    @patch('apps.payments.views.PaymentService')
    @patch('apps.payments.views.logger')
    def test_mercadopago_webhook_success(self, mock_logger, mock_service_class):
        """Test successful MercadoPago webhook processing"""
        # Setup mock
        mock_service = Mock()
        mock_service.handle_webhook.return_value = {
            'event_type': 'payment',
            'event_id': 'evt_mp_123',
            'data': {}
        }
        mock_service_class.return_value = mock_service
        
        # Send webhook (MercadoPago uses query params)
        response = self.client.post(
            f'{self.url}?id=evt_mp_123&topic=payment',
            data={},
            content_type='application/json'
        )
        
        # Verify
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        mock_service_class.assert_called_once_with(gateway_name='mercadopago')
        mock_service.handle_webhook.assert_called_once()
        mock_logger.info.assert_called()
    
    @patch('apps.payments.views.PaymentService')
    @patch('apps.payments.views.logger')
    def test_mercadopago_webhook_error(self, mock_logger, mock_service_class):
        """Test MercadoPago webhook with error"""
        # Setup mock to raise exception
        mock_service = Mock()
        mock_service.handle_webhook.side_effect = Exception('Processing error')
        mock_service_class.return_value = mock_service
        
        # Send webhook
        response = self.client.post(self.url)
        
        # Verify
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Processing error')
        mock_logger.error.assert_called()
    
    def test_mercadopago_webhook_allows_anonymous(self):
        """Test that MercadoPago webhook allows anonymous access"""
        # Ensure no authentication required
        response = self.client.post(self.url, data={})
        
        # Should not return 401
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @patch('apps.payments.views.PaymentService')
    def test_mercadopago_webhook_get_method(self, mock_service_class):
        """Test MercadoPago webhook with GET method"""
        # Setup mock
        mock_service = Mock()
        mock_service.handle_webhook.return_value = {
            'event_type': 'payment',
            'event_id': 'evt_mp_123',
            'data': {}
        }
        mock_service_class.return_value = mock_service
        
        # MercadoPago sometimes uses GET for webhooks
        response = self.client.get(
            f'{self.url}?id=evt_mp_123&topic=payment'
        )
        
        # Verify
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
    
    @patch('apps.payments.views.PaymentService')
    def test_mercadopago_webhook_different_topics(self, mock_service_class):
        """Test handling different MercadoPago topics"""
        topics = [
            'payment',
            'subscription',
            'invoice',
            'merchant_order'
        ]
        
        for topic in topics:
            # Setup mock
            mock_service = Mock()
            mock_service.handle_webhook.return_value = {
                'event_type': topic,
                'event_id': f'evt_{topic}',
                'data': {}
            }
            mock_service_class.return_value = mock_service
            
            # Send webhook
            response = self.client.post(
                f'{self.url}?id=evt_{topic}&topic={topic}',
                data={},
                content_type='application/json'
            )
            
            # Verify
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], 'success')


class TestWebhookIntegration(TestCase):
    """Test webhook integration scenarios"""
    
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            slug='pro-plan',
            plan_type='pro',
            price_monthly=99.90,
            price_yearly=999.00,
            gateway_plan_id='price_123'
        )
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan,
            subscription_id='sub_123',
            subscription_status='active'
        )
    
    @patch('apps.payments.payment_service.StripeGateway')
    def test_stripe_subscription_created_integration(self, mock_stripe_class):
        """Test full integration of subscription created webhook"""
        # Setup mock gateway
        mock_gateway = Mock()
        mock_gateway.handle_webhook.return_value = {
            'event_type': 'customer.subscription.created',
            'event_id': 'evt_123',
            'data': {'object': {'id': 'sub_123', 'status': 'active'}}
        }
        mock_stripe_class.return_value = mock_gateway
        
        # Update company to pending status
        self.company.subscription_status = 'pending'
        self.company.save()
        
        # Send webhook
        client = APIClient()
        url = '/api/payments/webhooks/stripe/'
        
        webhook_data = {
            'id': 'evt_123',
            'type': 'customer.subscription.created',
            'data': {'object': {'id': 'sub_123', 'status': 'active'}}
        }
        
        response = client.post(
            url,
            data=json.dumps(webhook_data),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='sig_123'
        )
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify company was updated
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_status, 'active')
    
    @patch('apps.payments.payment_service.StripeGateway')
    def test_stripe_subscription_cancelled_integration(self, mock_stripe_class):
        """Test full integration of subscription cancelled webhook"""
        # Setup mock gateway
        mock_gateway = Mock()
        mock_gateway.handle_webhook.return_value = {
            'event_type': 'customer.subscription.deleted',
            'event_id': 'evt_456',
            'data': {'object': {'id': 'sub_123'}}
        }
        mock_stripe_class.return_value = mock_gateway
        
        # Send webhook
        client = APIClient()
        url = '/api/payments/webhooks/stripe/'
        
        webhook_data = {
            'id': 'evt_456',
            'type': 'customer.subscription.deleted',
            'data': {'object': {'id': 'sub_123'}}
        }
        
        response = client.post(
            url,
            data=json.dumps(webhook_data),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='sig_456'
        )
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify company was updated
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_status, 'cancelled')
        self.assertIsNotNone(self.company.subscription_end_date)
    
    def test_concurrent_webhooks(self):
        """Test handling concurrent webhook requests"""
        # This tests that webhooks can be processed concurrently
        # In a real scenario, you'd want to ensure idempotency
        
        client = APIClient()
        url = '/api/payments/webhooks/stripe/'
        
        with patch('apps.payments.views.PaymentService') as mock_service_class:
            mock_service = Mock()
            mock_service.handle_webhook.return_value = {
                'event_type': 'test',
                'event_id': 'evt_test',
                'data': {}
            }
            mock_service_class.return_value = mock_service
            
            # Send multiple webhooks
            for i in range(5):
                response = client.post(
                    url,
                    data=json.dumps({'id': f'evt_{i}', 'type': 'test'}),
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify all were processed
            self.assertEqual(mock_service.handle_webhook.call_count, 5)