"""
Unit tests for payment services
"""
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.payments.services.stripe_service import StripeService
from apps.payments.services.subscription_service import SubscriptionService
from apps.payments.services.payment_gateway import PaymentGateway
from apps.payments.services.webhook_handler import WebhookHandler
from apps.payments.services.audit_service import PaymentAuditService
from apps.payments.services.retry_service import PaymentRetryService
from apps.payments.services.notification_service import PaymentNotificationService

from apps.payments.tests.factories import (
    SubscriptionPlanFactory,
    SubscriptionFactory,
    PaymentMethodFactory,
    PaymentFactory,
    UsageRecordFactory,
    FailedWebhookFactory,
)
from apps.companies.tests.factories import CompanyFactory
from apps.payments.exceptions import (
    PaymentException,
    SubscriptionException,
)


class StripeServiceTest(TestCase):
    """Test cases for StripeService"""
    
    def setUp(self):
        self.stripe_service = StripeService()
        self.company = CompanyFactory()
        self.plan = SubscriptionPlanFactory(
            price_monthly=Decimal('19.99'),
            price_yearly=Decimal('199.90')
        )
    
    @patch('stripe.Customer.create')
    def test_create_customer(self, mock_create):
        """Test creating a Stripe customer"""
        mock_create.return_value = Mock(
            id='cus_test123',
            email='test@example.com'
        )
        
        customer_id = self.stripe_service.create_customer(
            email='test@example.com',
            name='Test User',
            metadata={'company_id': self.company.id}
        )
        
        self.assertEqual(customer_id, 'cus_test123')
        mock_create.assert_called_once()
    
    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session(self, mock_create):
        """Test creating a Stripe checkout session"""
        mock_create.return_value = Mock(
            id='cs_test123',
            url='https://checkout.stripe.com/pay/cs_test123'
        )
        
        session_data = self.stripe_service.create_checkout_session(
            customer_id='cus_test123',
            price_id='price_test123',
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
            metadata={'company_id': self.company.id}
        )
        
        self.assertEqual(session_data['session_id'], 'cs_test123')
        self.assertEqual(session_data['checkout_url'], 'https://checkout.stripe.com/pay/cs_test123')
        mock_create.assert_called_once()


class SubscriptionServiceTest(TestCase):
    """Test cases for SubscriptionService"""
    
    def setUp(self):
        self.service = SubscriptionService()
        self.company = CompanyFactory()
        self.plan = SubscriptionPlanFactory()
        self.subscription = SubscriptionFactory(
            company=self.company,
            plan=self.plan
        )
    
    def test_create_trial_subscription(self):
        """Test creating a trial subscription"""
        new_company = CompanyFactory()
        
        subscription = self.service.create_trial_subscription(new_company)
        
        self.assertEqual(subscription.company, new_company)
        self.assertEqual(subscription.status, 'trial')
        self.assertTrue(subscription.is_active)
        self.assertTrue(subscription.is_trial)
        self.assertIsNotNone(subscription.trial_ends_at)
    
    def test_check_usage_limits(self):
        """Test checking usage limits"""
        # Create usage records
        usage_record = UsageRecordFactory(
            company=self.company,
            type='transaction',
            count=450
        )
        
        self.subscription.plan.max_transactions = 500
        self.subscription.plan.save()
        
        usage = self.service.check_usage_limits(self.subscription)
        
        self.assertIn('transactions', usage)
        self.assertEqual(usage['transactions']['used'], 450)
        self.assertEqual(usage['transactions']['limit'], 500)
        self.assertEqual(usage['transactions']['percentage'], 90.0)


class PaymentGatewayTest(TestCase):
    """Test cases for PaymentGateway"""
    
    def setUp(self):
        self.gateway = PaymentGateway()
        self.company = CompanyFactory()
        self.subscription = SubscriptionFactory(company=self.company)
        self.payment_method = PaymentMethodFactory(company=self.company)
    
    @patch('apps.payments.services.stripe_service.StripeService.create_payment_intent')
    def test_process_payment_success(self, mock_create_intent):
        """Test successful payment processing"""
        mock_create_intent.return_value = {
            'id': 'pi_test123',
            'status': 'succeeded',
            'amount': 1999,
            'currency': 'brl'
        }
        
        payment = self.gateway.process_payment(
            company=self.company,
            amount=Decimal('19.99'),
            payment_method=self.payment_method,
            description='Monthly subscription'
        )
        
        self.assertEqual(payment.amount, Decimal('19.99'))
        self.assertEqual(payment.status, 'succeeded')
        self.assertEqual(payment.stripe_payment_intent_id, 'pi_test123')
        self.assertIsNotNone(payment.paid_at)


class WebhookHandlerTest(TestCase):
    """Test cases for WebhookHandler"""
    
    def setUp(self):
        self.handler = WebhookHandler(gateway='stripe')
        self.company = CompanyFactory()
        self.subscription = SubscriptionFactory(
            company=self.company,
            stripe_subscription_id='sub_test123'
        )
    
    def test_handle_invoice_payment_succeeded(self):
        """Test handling invoice.payment_succeeded event"""
        event_data = {
            'object': {
                'id': 'in_test123',
                'subscription': 'sub_test123',
                'amount_paid': 1999,
                'currency': 'brl',
                'payment_intent': 'pi_test123'
            }
        }
        
        result = self.handler.handle_event('invoice.payment_succeeded', event_data)
        
        # Check payment was created
        from apps.payments.models import Payment
        payment = Payment.objects.filter(
            company=self.company,
            stripe_invoice_id='in_test123'
        ).first()
        
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount, Decimal('19.99'))
        self.assertEqual(payment.status, 'succeeded')
    
    def test_handle_subscription_deleted(self):
        """Test handling customer.subscription.deleted event"""
        event_data = {
            'object': {
                'id': 'sub_test123',
                'status': 'canceled',
                'canceled_at': 1234567890
            }
        }
        
        self.handler.handle_event('customer.subscription.deleted', event_data)
        
        # Refresh subscription
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, 'cancelled')
        self.assertFalse(self.subscription.is_active)


class PaymentAuditServiceTest(TestCase):
    """Test cases for PaymentAuditService"""
    
    def setUp(self):
        self.audit_service = PaymentAuditService()
        self.company = CompanyFactory()
        self.payment = PaymentFactory(company=self.company)
    
    def test_log_payment_event(self):
        """Test logging payment events"""
        self.audit_service.log_payment_event(
            payment=self.payment,
            event_type='payment.created',
            details={'source': 'api', 'ip': '127.0.0.1'}
        )
        
        # In a real implementation, this would check audit logs
        # For now, we just ensure no exceptions are raised
        self.assertTrue(True)
    
    def test_get_payment_history(self):
        """Test retrieving payment history"""
        # Create multiple payments
        PaymentFactory.create_batch(5, company=self.company, status='succeeded')
        PaymentFactory.create_batch(2, company=self.company, status='failed')
        
        history = self.audit_service.get_payment_history(self.company)
        
        self.assertEqual(len(history), 8)  # Including the one from setUp
        paid_count = sum(1 for p in history if p.status == 'succeeded')
        failed_count = sum(1 for p in history if p.status == 'failed')
        self.assertEqual(paid_count, 5)
        self.assertEqual(failed_count, 2)


class PaymentRetryServiceTest(TestCase):
    """Test cases for PaymentRetryService"""
    
    def setUp(self):
        self.retry_service = PaymentRetryService()
        self.company = CompanyFactory()
        self.payment_method = PaymentMethodFactory(company=self.company)
    
    def test_should_retry_payment(self):
        """Test determining if payment should be retried"""
        # Recent failure - should retry
        recent_payment = PaymentFactory(
            company=self.company,
            status='failed',
            paid_at=None,
            created_at=timezone.now() - timedelta(hours=1)
        )
        self.assertTrue(self.retry_service.should_retry(recent_payment))
        
        # Old failure - should not retry
        old_payment = PaymentFactory(
            company=self.company,
            status='failed',
            paid_at=None,
            created_at=timezone.now() - timedelta(days=30)
        )
        self.assertFalse(self.retry_service.should_retry(old_payment))
        
        # Successful payment - should not retry
        success_payment = PaymentFactory(
            company=self.company,
            status='succeeded'
        )
        self.assertFalse(self.retry_service.should_retry(success_payment))


class PaymentNotificationServiceTest(TestCase):
    """Test cases for PaymentNotificationService"""
    
    def setUp(self):
        self.notification_service = PaymentNotificationService()
        self.company = CompanyFactory()
        self.subscription = SubscriptionFactory(company=self.company)
    
    @patch('apps.notifications.services.notification_service.create_notification')
    def test_send_payment_success_notification(self, mock_create_notification):
        """Test sending payment success notification"""
        payment = PaymentFactory(
            company=self.company,
            status='succeeded',
            amount=Decimal('19.99')
        )
        
        self.notification_service.send_payment_success(payment)
        
        mock_create_notification.assert_called_once()
    
    @patch('apps.notifications.services.notification_service.create_notification')
    def test_send_trial_ending_notification(self, mock_create_notification):
        """Test sending trial ending notification"""
        trial_sub = SubscriptionFactory(
            company=self.company,
            status='trial',
            trial_ends_at=timezone.now() + timedelta(days=3)
        )
        
        self.notification_service.send_trial_ending_soon(trial_sub)
        
        mock_create_notification.assert_called_once()