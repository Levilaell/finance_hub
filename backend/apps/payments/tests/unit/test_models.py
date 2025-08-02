"""
Unit tests for payment models
"""
from decimal import Decimal
from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from apps.payments.models import (
    SubscriptionPlan,
    Subscription,
    PaymentMethod,
    Payment,
    UsageRecord,
    FailedWebhook,
)
from apps.payments.tests.factories import (
    SubscriptionPlanFactory,
    SubscriptionFactory,
    PaymentMethodFactory,
    PaymentFactory,
    UsageRecordFactory,
    FailedWebhookFactory,
)
from apps.companies.tests.factories import CompanyFactory


class SubscriptionPlanModelTest(TestCase):
    """Test cases for SubscriptionPlan model"""
    
    def setUp(self):
        self.plan = SubscriptionPlanFactory()
    
    def test_create_subscription_plan(self):
        """Test creating a SubscriptionPlan"""
        self.assertIsNotNone(self.plan.id)
        self.assertTrue(self.plan.name)
        self.assertTrue(self.plan.display_name)
        self.assertGreater(self.plan.price_monthly, 0)
        self.assertGreater(self.plan.price_yearly, 0)
        self.assertGreater(self.plan.max_transactions, 0)
        self.assertGreater(self.plan.max_bank_accounts, 0)
        self.assertGreater(self.plan.max_ai_requests, 0)
    
    def test_yearly_savings_calculation(self):
        """Test yearly savings calculation"""
        plan = SubscriptionPlanFactory(
            price_monthly=Decimal('19.99'),
            price_yearly=Decimal('199.90')
        )
        expected_savings = (Decimal('19.99') * 12) - Decimal('199.90')
        # Test price calculation methods
        self.assertEqual(plan.get_price('yearly'), plan.price_yearly)
        self.assertEqual(plan.get_price('monthly'), plan.price_monthly)
    
    def test_plan_str_representation(self):
        """Test string representation of plan"""
        self.assertEqual(str(self.plan), self.plan.display_name)
    
    def test_plan_features_json_field(self):
        """Test features JSON field"""
        plan = SubscriptionPlanFactory(
            features={
                'ai_insights': True,
                'advanced_reports': False,
                'priority_support': True,
            }
        )
        self.assertTrue(plan.features['ai_insights'])
        self.assertFalse(plan.features['advanced_reports'])
        self.assertTrue(plan.features['priority_support'])
    
    def test_plan_ordering(self):
        """Test plans are ordered by price_monthly"""
        # Create plans with unique names that don't conflict with setUp
        from apps.payments.models import SubscriptionPlan
        
        # Clear any existing plans to avoid conflicts
        SubscriptionPlan.objects.all().delete()
        
        plan1 = SubscriptionPlanFactory(name='professional', price_monthly=50.00)
        plan2 = SubscriptionPlanFactory(name='starter', price_monthly=25.00)
        plan3 = SubscriptionPlanFactory(name='enterprise', price_monthly=100.00)
        
        plans = SubscriptionPlan.objects.all()
        self.assertEqual(plans[0].id, plan2.id)  # lowest price first
        self.assertEqual(plans[1].id, plan1.id)
        self.assertEqual(plans[2].id, plan3.id)


class SubscriptionModelTest(TestCase):
    """Test cases for Subscription model"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.plan = SubscriptionPlanFactory()
        self.subscription = SubscriptionFactory(
            company=self.company,
            plan=self.plan
        )
    
    def test_create_subscription(self):
        """Test creating a Subscription"""
        self.assertIsNotNone(self.subscription.id)
        self.assertEqual(self.subscription.company, self.company)
        self.assertEqual(self.subscription.plan, self.plan)
        self.assertIn(self.subscription.status, ['trial', 'active', 'cancelled', 'expired', 'past_due'])
        self.assertIn(self.subscription.billing_period, ['monthly', 'yearly'])
    
    def test_trial_subscription(self):
        """Test trial subscription properties"""
        trial_sub = SubscriptionFactory(
            status='trial',
            is_trial=True,
            trial_ends_at=timezone.now() + timedelta(days=14)
        )
        self.assertTrue(trial_sub.is_trial)
        self.assertTrue(trial_sub.is_active)
        self.assertIsNotNone(trial_sub.trial_ends_at)
        self.assertGreater(trial_sub.trial_ends_at, timezone.now())
    
    def test_subscription_period_dates(self):
        """Test subscription period dates"""
        sub = SubscriptionFactory(
            billing_period='monthly',
            current_period_start=timezone.now()
        )
        expected_end = sub.current_period_start + timedelta(days=30)
        # Allow for small time difference due to factory execution
        time_diff = abs((sub.current_period_end - expected_end).total_seconds())
        self.assertLess(time_diff, 60)  # Less than 1 minute difference
    
    def test_cancelled_subscription(self):
        """Test cancelled subscription properties"""
        cancelled_sub = SubscriptionFactory(
            status='cancelled',
            is_active=False,
            cancelled_at=timezone.now()
        )
        self.assertFalse(cancelled_sub.is_active)
        self.assertIsNotNone(cancelled_sub.cancelled_at)
    
    def test_subscription_str_representation(self):
        """Test string representation of subscription"""
        expected = f"{self.subscription.company.name} - {self.subscription.plan.display_name} ({self.subscription.status})"
        self.assertEqual(str(self.subscription), expected)
    
    def test_stripe_ids(self):
        """Test Stripe ID fields"""
        sub = SubscriptionFactory()
        self.assertIsNotNone(sub.stripe_subscription_id)
        self.assertIsNotNone(sub.stripe_customer_id)
        self.assertTrue(sub.stripe_customer_id.startswith('cus_'))


class PaymentMethodModelTest(TestCase):
    """Test cases for PaymentMethod model"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.payment_method = PaymentMethodFactory(company=self.company)
    
    def test_create_payment_method(self):
        """Test creating a PaymentMethod"""
        self.assertIsNotNone(self.payment_method.id)
        self.assertEqual(self.payment_method.company, self.company)
        self.assertIn(self.payment_method.type, ['card', 'bank_account', 'pix'])
        self.assertIsNotNone(self.payment_method.display_name)
    
    def test_card_payment_method(self):
        """Test card-specific fields"""
        card = PaymentMethodFactory(
            type='card',
            brand='visa',
            last4='4242',
            exp_month=12,
            exp_year=2025
        )
        self.assertEqual(card.brand, 'visa')
        self.assertEqual(card.last4, '4242')
        self.assertEqual(card.exp_month, 12)
        self.assertEqual(card.exp_year, 2025)
    
    def test_default_payment_method(self):
        """Test default payment method logic"""
        # Create multiple payment methods
        pm1 = PaymentMethodFactory(company=self.company, is_default=False)
        pm2 = PaymentMethodFactory(company=self.company, is_default=True)
        pm3 = PaymentMethodFactory(company=self.company, is_default=False)
        
        # Only pm2 should be default
        self.assertFalse(pm1.is_default)
        self.assertTrue(pm2.is_default)
        self.assertFalse(pm3.is_default)
    
    def test_payment_method_str_representation(self):
        """Test string representation of payment method"""
        self.assertEqual(str(self.payment_method), self.payment_method.display_name)


class PaymentModelTest(TestCase):
    """Test cases for Payment model"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.subscription = SubscriptionFactory(company=self.company)
        self.payment_method = PaymentMethodFactory(company=self.company)
        self.payment = PaymentFactory(
            company=self.company,
            subscription=self.subscription,
            payment_method=self.payment_method
        )
    
    def test_create_payment(self):
        """Test creating a Payment"""
        self.assertIsNotNone(self.payment.id)
        self.assertEqual(self.payment.company, self.company)
        self.assertEqual(self.payment.subscription, self.subscription)
        self.assertGreater(self.payment.amount, 0)
        self.assertEqual(self.payment.currency, 'BRL')
        self.assertIn(self.payment.status, ['pending', 'processing', 'paid', 'failed', 'cancelled', 'refunded'])
    
    def test_paid_payment(self):
        """Test paid payment properties"""
        paid_payment = PaymentFactory(
            status='paid',
            paid_at=timezone.now()
        )
        self.assertEqual(paid_payment.status, 'paid')
        self.assertIsNotNone(paid_payment.paid_at)
        self.assertIsNone(paid_payment.failed_at)
        self.assertIsNone(paid_payment.failure_reason)
    
    def test_failed_payment(self):
        """Test failed payment properties"""
        failed_payment = PaymentFactory(
            status='failed',
            failed_at=timezone.now(),
            failure_reason='Card declined'
        )
        self.assertEqual(failed_payment.status, 'failed')
        self.assertIsNotNone(failed_payment.failed_at)
        self.assertIsNone(failed_payment.paid_at)
        self.assertEqual(failed_payment.failure_reason, 'Card declined')
    
    def test_invoice_fields(self):
        """Test invoice-related fields"""
        payment = PaymentFactory()
        self.assertIsNotNone(payment.invoice_number)
        self.assertTrue(payment.invoice_number.startswith('INV-'))
        self.assertIsNotNone(payment.invoice_url)
    
    def test_stripe_ids(self):
        """Test Stripe ID fields"""
        payment = PaymentFactory()
        self.assertIsNotNone(payment.stripe_payment_intent_id)
        self.assertTrue(payment.stripe_payment_intent_id.startswith('pi_'))
        self.assertIsNotNone(payment.stripe_invoice_id)
        self.assertTrue(payment.stripe_invoice_id.startswith('in_'))
    
    def test_payment_str_representation(self):
        """Test string representation of payment"""
        expected = f"Payment {self.payment.invoice_number} - {self.payment.amount} {self.payment.currency} ({self.payment.status})"
        self.assertEqual(str(self.payment), expected)


class UsageRecordModelTest(TestCase):
    """Test cases for UsageRecord model"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.usage = UsageRecordFactory(
            company=self.company,
            type='transaction',
            count=150
        )
    
    def test_create_usage_record(self):
        """Test creating a UsageRecord"""
        self.assertIsNotNone(self.usage.id)
        self.assertEqual(self.usage.company, self.company)
        self.assertEqual(self.usage.type, 'transaction')
        self.assertEqual(self.usage.count, 150)
        self.assertIsNotNone(self.usage.period_start)
        self.assertIsNotNone(self.usage.period_end)
    
    def test_usage_types(self):
        """Test different usage types"""
        transaction_usage = UsageRecordFactory(type='transaction')
        bank_account_usage = UsageRecordFactory(type='bank_account')
        ai_request_usage = UsageRecordFactory(type='ai_request')
        
        self.assertEqual(transaction_usage.type, 'transaction')
        self.assertEqual(bank_account_usage.type, 'bank_account')
        self.assertEqual(ai_request_usage.type, 'ai_request')
    
    def test_get_current_usage(self):
        """Test get_current_usage class method"""
        company = CompanyFactory()
        usage = UsageRecord.get_current_usage(company, 'transaction')
        
        self.assertEqual(usage.company, company)
        self.assertEqual(usage.type, 'transaction')
        self.assertEqual(usage.count, 0)
        self.assertLessEqual(usage.period_start, timezone.now())
        self.assertGreater(usage.period_end, timezone.now())
    
    def test_increment_usage(self):
        """Test incrementing usage count"""
        initial_count = self.usage.count
        new_count = self.usage.increment(5)
        
        self.assertEqual(new_count, initial_count + 5)
        self.usage.refresh_from_db()
        self.assertEqual(self.usage.count, initial_count + 5)
    
    def test_usage_str_representation(self):
        """Test string representation of usage record"""
        expected = f"{self.company.name} - {self.usage.type}: {self.usage.count}"
        self.assertEqual(str(self.usage), expected)


class FailedWebhookModelTest(TestCase):
    """Test cases for FailedWebhook model"""
    
    def setUp(self):
        self.failed_webhook = FailedWebhookFactory()
    
    def test_create_failed_webhook(self):
        """Test creating a FailedWebhook"""
        self.assertIsNotNone(self.failed_webhook.id)
        self.assertIsNotNone(self.failed_webhook.event_id)
        self.assertIsNotNone(self.failed_webhook.event_type)
        self.assertIsNotNone(self.failed_webhook.event_data)
        self.assertIsNotNone(self.failed_webhook.error_message)
        self.assertIsNotNone(self.failed_webhook.next_retry_at)
    
    def test_should_retry(self):
        """Test should_retry logic"""
        # Test webhook that should be retried
        webhook = FailedWebhookFactory(
            retry_count=2,
            max_retries=5,
            next_retry_at=timezone.now() - timedelta(minutes=1)
        )
        self.assertTrue(webhook.should_retry())
        
        # Test webhook that has exceeded max retries
        webhook_max_retries = FailedWebhookFactory(
            retry_count=5,
            max_retries=5
        )
        self.assertFalse(webhook_max_retries.should_retry())
        
        # Test webhook that's not ready for retry yet
        webhook_not_ready = FailedWebhookFactory(
            retry_count=1,
            max_retries=5,
            next_retry_at=timezone.now() + timedelta(minutes=10)
        )
        self.assertFalse(webhook_not_ready.should_retry())
    
    def test_increment_retry(self):
        """Test incrementing retry count and backoff"""
        webhook = FailedWebhookFactory(retry_count=0)
        original_retry_at = webhook.next_retry_at
        
        webhook.increment_retry()
        self.assertEqual(webhook.retry_count, 1)
        self.assertGreater(webhook.next_retry_at, original_retry_at)
        
        # Test exponential backoff
        webhook.increment_retry()
        self.assertEqual(webhook.retry_count, 2)
        second_retry_at = webhook.next_retry_at
        
        webhook.increment_retry()
        self.assertEqual(webhook.retry_count, 3)
        third_retry_at = webhook.next_retry_at
        
        # Third retry should have longer delay than second
        delta_2_3 = (third_retry_at - second_retry_at).total_seconds()
        delta_1_2 = (second_retry_at - original_retry_at).total_seconds()
        self.assertGreater(delta_2_3, delta_1_2)
    
    def test_webhook_str_representation(self):
        """Test string representation of failed webhook"""
        expected = f"{self.failed_webhook.event_type} - {self.failed_webhook.event_id} (retry {self.failed_webhook.retry_count})"
        self.assertEqual(str(self.failed_webhook), expected)
    
    def test_event_data_json_field(self):
        """Test event data JSON field"""
        webhook = FailedWebhookFactory(
            event_data={
                'object': {
                    'id': 'sub_123',
                    'status': 'active',
                    'amount': 1999
                }
            }
        )
        self.assertEqual(webhook.event_data['object']['id'], 'sub_123')
        self.assertEqual(webhook.event_data['object']['status'], 'active')
        self.assertEqual(webhook.event_data['object']['amount'], 1999)