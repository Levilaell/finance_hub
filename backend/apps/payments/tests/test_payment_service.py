"""
Test payment service and gateway implementations
Tests for PaymentService, StripeGateway, and MercadoPagoGateway
"""
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.companies.models import Company, SubscriptionPlan

User = get_user_model()


class TestPaymentGatewayBase(TestCase):
    """Test the abstract PaymentGateway base class"""
    
    def test_abstract_methods(self):
        """Test that PaymentGateway is abstract and cannot be instantiated"""
        from apps.payments.payment_service import PaymentGateway
        with self.assertRaises(TypeError):
            PaymentGateway()
    
    def test_abstract_method_definitions(self):
        """Test that all abstract methods are defined"""
        from apps.payments.payment_service import PaymentGateway
        abstract_methods = [
            'create_customer',
            'create_subscription',
            'cancel_subscription',
            'update_subscription',
            'create_payment_method',
            'charge_customer',
            'refund_payment',
            'get_subscription_status',
            'handle_webhook'
        ]
        
        for method_name in abstract_methods:
            self.assertTrue(hasattr(PaymentGateway, method_name))


@override_settings(
    STRIPE_SECRET_KEY='sk_test_fake',
    STRIPE_WEBHOOK_SECRET='whsec_test_fake'
)
class TestStripeGateway(TestCase):
    """Test StripeGateway implementation"""
    
    def setUp(self):
        # Create a mock stripe module
        self.mock_stripe_module = MagicMock()
        self.mock_stripe_module.api_key = None
        sys.modules['stripe'] = self.mock_stripe_module
        
    def tearDown(self):
        # Clean up
        if 'stripe' in sys.modules:
            del sys.modules['stripe']
    
    @patch('apps.payments.payment_service.logger')
    def test_init_without_stripe_library(self, mock_logger):
        """Test initialization when stripe library is not installed"""
        # Remove stripe from modules
        if 'stripe' in sys.modules:
            del sys.modules['stripe']
            
        from apps.payments.payment_service import StripeGateway
        with self.assertRaises(ImportError):
            StripeGateway()
        mock_logger.error.assert_called()
    
    def test_create_customer(self):
        """Test creating a Stripe customer"""
        from apps.payments.payment_service import StripeGateway
        
        # Setup mock
        mock_customer = Mock(id='cus_123')
        self.mock_stripe_module.Customer.create.return_value = mock_customer
        
        gateway = StripeGateway()
        
        # Test data
        user_data = {
            'email': 'test@example.com',
            'name': 'Test User',
            'user_id': 1,
            'company_id': 2
        }
        
        # Create customer
        result = gateway.create_customer(user_data)
        
        # Verify
        self.mock_stripe_module.Customer.create.assert_called_once_with(
            email='test@example.com',
            name='Test User',
            metadata={
                'user_id': 1,
                'company_id': 2
            }
        )
        
        self.assertEqual(result['customer_id'], 'cus_123')
        self.assertEqual(result['gateway'], 'stripe')
        self.assertEqual(result['data'], mock_customer)
    
    def test_create_subscription(self):
        """Test creating a Stripe subscription"""
        from apps.payments.payment_service import StripeGateway
        
        # Setup mock
        mock_subscription = Mock(
            id='sub_123',
            status='incomplete',
            latest_invoice=Mock(
                payment_intent=Mock(client_secret='pi_secret')
            )
        )
        self.mock_stripe_module.Subscription.create.return_value = mock_subscription
        
        gateway = StripeGateway()
        
        # Create subscription
        result = gateway.create_subscription('cus_123', 'price_123')
        
        # Verify
        self.mock_stripe_module.Subscription.create.assert_called_once_with(
            customer='cus_123',
            items=[{'price': 'price_123'}],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent']
        )
        
        self.assertEqual(result['subscription_id'], 'sub_123')
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['client_secret'], 'pi_secret')
    
    def test_cancel_subscription(self):
        """Test canceling a Stripe subscription"""
        from apps.payments.payment_service import StripeGateway
        
        # Setup mock
        mock_subscription = Mock(cancel_at_period_end=True)
        self.mock_stripe_module.Subscription.modify.return_value = mock_subscription
        
        gateway = StripeGateway()
        
        # Cancel subscription
        result = gateway.cancel_subscription('sub_123')
        
        # Verify
        self.mock_stripe_module.Subscription.modify.assert_called_once_with(
            'sub_123',
            cancel_at_period_end=True
        )
        self.assertTrue(result)
    
    def test_handle_webhook(self):
        """Test handling Stripe webhook"""
        from apps.payments.payment_service import StripeGateway
        
        # Setup mock
        mock_event = {
            'id': 'evt_123',
            'type': 'customer.subscription.created',
            'data': {'object': {'id': 'sub_123'}}
        }
        self.mock_stripe_module.Webhook.construct_event.return_value = mock_event
        
        gateway = StripeGateway()
        
        # Handle webhook
        result = gateway.handle_webhook(b'payload', 'sig_123')
        
        # Verify
        self.mock_stripe_module.Webhook.construct_event.assert_called_once()
        self.assertEqual(result['event_type'], 'customer.subscription.created')
        self.assertEqual(result['event_id'], 'evt_123')


@override_settings(
    MERCADOPAGO_ACCESS_TOKEN='TEST-123456',
    FRONTEND_URL='http://localhost:3000'
)
class TestMercadoPagoGateway(TestCase):
    """Test MercadoPagoGateway implementation"""
    
    def setUp(self):
        # Create a mock mercadopago module
        self.mock_mp_module = MagicMock()
        self.mock_sdk = MagicMock()
        self.mock_mp_module.SDK.return_value = self.mock_sdk
        sys.modules['mercadopago'] = self.mock_mp_module
        
    def tearDown(self):
        # Clean up
        if 'mercadopago' in sys.modules:
            del sys.modules['mercadopago']
    
    @patch('apps.payments.payment_service.logger')
    def test_init_without_mercadopago_library(self, mock_logger):
        """Test initialization when mercadopago library is not installed"""
        # Remove mercadopago from modules
        if 'mercadopago' in sys.modules:
            del sys.modules['mercadopago']
            
        from apps.payments.payment_service import MercadoPagoGateway
        with self.assertRaises(ImportError):
            MercadoPagoGateway()
        mock_logger.error.assert_called()
    
    def test_create_customer(self):
        """Test creating a MercadoPago customer"""
        from apps.payments.payment_service import MercadoPagoGateway
        
        # Setup mock
        mock_customer = Mock()
        mock_customer.create.return_value = {
            'status': 201,
            'response': {'id': 'cus_mp_123'}
        }
        self.mock_sdk.customer.return_value = mock_customer
        
        gateway = MercadoPagoGateway()
        
        # Test data
        user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'doc_type': 'CPF',
            'doc_number': '12345678901'
        }
        
        # Create customer
        result = gateway.create_customer(user_data)
        
        # Verify
        self.assertEqual(result['customer_id'], 'cus_mp_123')
        self.assertEqual(result['gateway'], 'mercadopago')
    
    def test_cancel_subscription(self):
        """Test canceling a MercadoPago subscription"""
        from apps.payments.payment_service import MercadoPagoGateway
        
        # Setup mock
        mock_subscription = Mock()
        mock_subscription.update.return_value = {'status': 200}
        self.mock_sdk.subscription.return_value = mock_subscription
        
        gateway = MercadoPagoGateway()
        
        # Cancel subscription
        result = gateway.cancel_subscription('sub_mp_123')
        
        # Verify
        self.assertTrue(result)
        mock_subscription.update.assert_called_once_with(
            'sub_mp_123',
            {'status': 'cancelled'}
        )
    
    def test_update_subscription_not_implemented(self):
        """Test that update_subscription is not implemented for MercadoPago"""
        from apps.payments.payment_service import MercadoPagoGateway
        
        gateway = MercadoPagoGateway()
        
        with self.assertRaises(NotImplementedError):
            gateway.update_subscription('sub_123', 'plan_456')
    
    def test_handle_webhook(self):
        """Test handling MercadoPago webhook"""
        from apps.payments.payment_service import MercadoPagoGateway
        
        gateway = MercadoPagoGateway()
        
        # Test webhook payload
        payload = {
            'type': 'payment',
            'id': 'evt_mp_123',
            'data': {'id': 'pay_123'}
        }
        
        # Handle webhook
        result = gateway.handle_webhook(payload, None)
        
        # Verify
        self.assertEqual(result['event_type'], 'payment')
        self.assertEqual(result['event_id'], 'evt_mp_123')


@override_settings(DEFAULT_PAYMENT_GATEWAY='stripe')
class TestPaymentService(TestCase):
    """Test PaymentService main class"""
    
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
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
            subscription_plan=self.plan
        )
        self.user.company = self.company
        self.user.save()
        
        # Mock payment gateways
        self.mock_stripe_gateway = MagicMock()
        self.mock_mp_gateway = MagicMock()
    
    @patch('apps.payments.payment_service.StripeGateway')
    def test_init_with_default_gateway(self, mock_stripe_class):
        """Test initialization with default gateway"""
        from apps.payments.payment_service import PaymentService
        
        mock_stripe_class.return_value = self.mock_stripe_gateway
        service = PaymentService()
        
        self.assertEqual(service.gateway_name, 'stripe')
        self.assertEqual(service.gateway, self.mock_stripe_gateway)
    
    @patch('apps.payments.payment_service.MercadoPagoGateway')
    def test_init_with_specific_gateway(self, mock_mp_class):
        """Test initialization with specific gateway"""
        from apps.payments.payment_service import PaymentService
        
        mock_mp_class.return_value = self.mock_mp_gateway
        service = PaymentService(gateway_name='mercadopago')
        
        self.assertEqual(service.gateway_name, 'mercadopago')
        self.assertEqual(service.gateway, self.mock_mp_gateway)
    
    def test_init_with_invalid_gateway(self):
        """Test initialization with invalid gateway"""
        from apps.payments.payment_service import PaymentService
        
        with self.assertRaises(ValueError):
            PaymentService(gateway_name='invalid_gateway')
    
    @patch('apps.payments.payment_service.StripeGateway')
    def test_create_customer(self, mock_stripe_class):
        """Test creating a customer"""
        from apps.payments.payment_service import PaymentService
        
        # Setup mock
        self.mock_stripe_gateway.create_customer.return_value = {
            'customer_id': 'cus_123',
            'gateway': 'stripe'
        }
        mock_stripe_class.return_value = self.mock_stripe_gateway
        
        service = PaymentService()
        
        # Create customer
        result = service.create_customer(self.user)
        
        # Verify
        self.mock_stripe_gateway.create_customer.assert_called_once()
        call_args = self.mock_stripe_gateway.create_customer.call_args[0][0]
        self.assertEqual(call_args['email'], 'test@example.com')
        self.assertEqual(call_args['name'], 'Test User')
        
        # Check user was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.payment_customer_id, 'cus_123')
        self.assertEqual(self.user.payment_gateway, 'stripe')
    
    @patch('apps.payments.payment_service.StripeGateway')
    def test_create_subscription(self, mock_stripe_class):
        """Test creating a subscription"""
        from apps.payments.payment_service import PaymentService
        
        # Setup mock
        self.mock_stripe_gateway.create_customer.return_value = {
            'customer_id': 'cus_123',
            'gateway': 'stripe'
        }
        self.mock_stripe_gateway.create_subscription.return_value = {
            'subscription_id': 'sub_123',
            'status': 'incomplete'
        }
        mock_stripe_class.return_value = self.mock_stripe_gateway
        
        service = PaymentService()
        
        # Create subscription
        result = service.create_subscription(self.company, self.plan)
        
        # Verify
        self.mock_stripe_gateway.create_subscription.assert_called_once_with(
            customer_id='cus_123',
            plan_id='price_123'
        )
        
        # Check company was updated
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_id, 'sub_123')
        self.assertEqual(self.company.subscription_status, 'pending')
        self.assertIsNotNone(self.company.subscription_start_date)
    
    @patch('apps.payments.payment_service.StripeGateway')
    def test_cancel_subscription(self, mock_stripe_class):
        """Test canceling a subscription"""
        from apps.payments.payment_service import PaymentService
        
        # Setup company with subscription
        self.company.subscription_id = 'sub_123'
        self.company.save()
        
        # Setup mock
        self.mock_stripe_gateway.cancel_subscription.return_value = True
        mock_stripe_class.return_value = self.mock_stripe_gateway
        
        service = PaymentService()
        
        # Cancel subscription
        result = service.cancel_subscription(self.company)
        
        # Verify
        self.assertTrue(result)
        self.mock_stripe_gateway.cancel_subscription.assert_called_once_with('sub_123')
        
        # Check company was updated
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_status, 'cancelled')
        self.assertIsNotNone(self.company.subscription_end_date)
    
    @patch('apps.payments.payment_service.StripeGateway')
    def test_handle_webhook_stripe(self, mock_stripe_class):
        """Test handling Stripe webhook"""
        from apps.payments.payment_service import PaymentService
        
        # Setup mock
        self.mock_stripe_gateway.handle_webhook.return_value = {
            'event_type': 'customer.subscription.created',
            'event_id': 'evt_123',
            'data': {'object': {'id': 'sub_123'}}
        }
        mock_stripe_class.return_value = self.mock_stripe_gateway
        
        # Setup request mock
        mock_request = Mock()
        mock_request.body = b'webhook payload'
        mock_request.META = {'HTTP_STRIPE_SIGNATURE': 'sig_123'}
        
        service = PaymentService(gateway_name='stripe')
        
        # Handle webhook
        with patch.object(service, '_process_webhook_event') as mock_process:
            result = service.handle_webhook(mock_request)
        
        # Verify
        self.mock_stripe_gateway.handle_webhook.assert_called_once_with(b'webhook payload', 'sig_123')
        mock_process.assert_called_once()
        self.assertEqual(result['event_type'], 'customer.subscription.created')
    
    @patch('apps.payments.payment_service.StripeGateway')
    def test_process_subscription_created_event(self, mock_stripe_class):
        """Test processing subscription created event"""
        from apps.payments.payment_service import PaymentService
        
        # Setup company with subscription
        self.company.subscription_id = 'sub_123'
        self.company.save()
        
        mock_stripe_class.return_value = self.mock_stripe_gateway
        service = PaymentService()
        
        # Process event
        event_data = {
            'event_type': 'customer.subscription.created',
            'data': {'object': {'id': 'sub_123'}}
        }
        
        service._process_webhook_event(event_data)
        
        # Check company was updated
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_status, 'active')
    
    @patch('apps.payments.payment_service.logger')
    @patch('apps.payments.payment_service.StripeGateway')
    def test_process_subscription_event_company_not_found(self, mock_stripe_class, mock_logger):
        """Test processing subscription event when company not found"""
        from apps.payments.payment_service import PaymentService
        
        mock_stripe_class.return_value = self.mock_stripe_gateway
        service = PaymentService()
        
        # Process event for non-existent subscription
        event_data = {
            'event_type': 'customer.subscription.created',
            'data': {'object': {'id': 'sub_unknown'}}
        }
        
        service._process_webhook_event(event_data)
        
        # Should log warning
        mock_logger.warning.assert_called()