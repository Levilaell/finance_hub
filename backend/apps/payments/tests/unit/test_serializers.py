"""
Unit tests for payment serializers
"""
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from apps.payments.serializers import (
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
    PaymentMethodSerializer,
    PaymentSerializer,
    CreateCheckoutSessionSerializer,
    CreatePaymentMethodSerializer,
    CompanySubscriptionSerializer,
    UsageSerializer,
)
from apps.payments.tests.factories import (
    SubscriptionPlanFactory,
    SubscriptionFactory,
    PaymentMethodFactory,
    PaymentFactory,
)
from apps.companies.tests.factories import CompanyFactory


class SubscriptionPlanSerializerTest(TestCase):
    """Test cases for SubscriptionPlanSerializer"""
    
    def setUp(self):
        self.plan = SubscriptionPlanFactory(
            name='premium',
            display_name='Premium Plan',
            monthly_price=Decimal('19.99'),
            yearly_price=Decimal('199.90'),
            max_transactions=2000,
            max_bank_accounts=5,
            max_ai_requests=200,
            features={
                'ai_insights': True,
                'advanced_reports': True,
                'priority_support': True,
                'api_access': False,
            }
        )
        self.serializer = SubscriptionPlanSerializer(instance=self.plan)
    
    def test_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        data = self.serializer.data
        expected_fields = [
            'id', 'name', 'display_name', 'monthly_price', 'yearly_price',
            'yearly_savings', 'max_transactions', 'max_bank_accounts',
            'max_ai_requests', 'features'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
    
    def test_price_formatting(self):
        """Test price fields are properly formatted"""
        data = self.serializer.data
        self.assertEqual(data['monthly_price'], '19.99')
        self.assertEqual(data['yearly_price'], '199.90')
        # Yearly savings = (19.99 * 12) - 199.90 = 239.88 - 199.90 = 39.98
        self.assertEqual(data['yearly_savings'], '39.98')
    
    def test_features_serialization(self):
        """Test features JSON field is properly serialized"""
        data = self.serializer.data
        self.assertTrue(data['features']['ai_insights'])
        self.assertTrue(data['features']['advanced_reports'])
        self.assertTrue(data['features']['priority_support'])
        self.assertFalse(data['features']['api_access'])


class SubscriptionSerializerTest(TestCase):
    """Test cases for SubscriptionSerializer"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.plan = SubscriptionPlanFactory()
        self.subscription = SubscriptionFactory(
            company=self.company,
            plan=self.plan,
            status='active',
            billing_period='monthly'
        )
        self.serializer = SubscriptionSerializer(instance=self.subscription)
    
    def test_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        data = self.serializer.data
        expected_fields = [
            'id', 'plan', 'status', 'billing_period', 'is_active', 'is_trial',
            'trial_ends_at', 'current_period_start', 'current_period_end',
            'cancelled_at', 'created_at'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
    
    def test_nested_plan_serialization(self):
        """Test plan is properly nested in serialization"""
        data = self.serializer.data
        self.assertIsInstance(data['plan'], dict)
        self.assertEqual(data['plan']['id'], self.plan.id)
        self.assertEqual(data['plan']['display_name'], self.plan.display_name)
    
    def test_is_active_and_is_trial(self):
        """Test is_active and is_trial readonly fields"""
        data = self.serializer.data
        self.assertIn('is_active', data)
        self.assertIn('is_trial', data)
        self.assertIn('trial_days_remaining', data)
    
    def test_date_formatting(self):
        """Test date fields are properly formatted"""
        data = self.serializer.data
        # Date fields should be ISO formatted strings
        if data['trial_ends_at']:
            self.assertIsInstance(data['trial_ends_at'], str)
        self.assertIsInstance(data['current_period_start'], str)
        self.assertIsInstance(data['current_period_end'], str)
        self.assertIsInstance(data['created_at'], str)


class PaymentMethodSerializerTest(TestCase):
    """Test cases for PaymentMethodSerializer"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.payment_method = PaymentMethodFactory(
            company=self.company,
            type='card',
            brand='visa',
            last4='4242',
            exp_month=12,
            exp_year=2025,
            is_default=True
        )
        self.serializer = PaymentMethodSerializer(instance=self.payment_method)
    
    def test_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        data = self.serializer.data
        expected_fields = [
            'id', 'type', 'is_default', 'brand', 'last4',
            'exp_month', 'exp_year', 'display_name', 'created_at'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
    
    def test_card_details_serialization(self):
        """Test card details are properly serialized"""
        data = self.serializer.data
        self.assertEqual(data['type'], 'card')
        self.assertEqual(data['brand'], 'visa')
        self.assertEqual(data['last4'], '4242')
        self.assertEqual(data['exp_month'], 12)
        self.assertEqual(data['exp_year'], 2025)
        self.assertTrue(data['is_default'])


class PaymentSerializerTest(TestCase):
    """Test cases for PaymentSerializer"""
    
    def setUp(self):
        self.company = CompanyFactory()
        self.subscription = SubscriptionFactory(company=self.company)
        self.payment_method = PaymentMethodFactory(company=self.company)
        self.payment = PaymentFactory(
            company=self.company,
            subscription=self.subscription,
            payment_method=self.payment_method,
            amount=Decimal('19.99'),
            status='paid'
        )
        self.serializer = PaymentSerializer(instance=self.payment)
    
    def test_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        data = self.serializer.data
        expected_fields = [
            'id', 'amount', 'currency', 'status', 'description',
            'gateway', 'payment_method', 'invoice_number', 'invoice_url',
            'paid_at', 'created_at'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
    
    def test_amount_formatting(self):
        """Test amount is properly formatted"""
        data = self.serializer.data
        self.assertEqual(data['amount'], '19.99')
        self.assertEqual(data['currency'], 'BRL')
    
    def test_nested_payment_method(self):
        """Test payment method is properly nested"""
        data = self.serializer.data
        self.assertIsInstance(data['payment_method'], dict)
        self.assertEqual(data['payment_method']['id'], self.payment_method.id)


class CreateCheckoutSessionSerializerTest(TestCase):
    """Test cases for CreateCheckoutSessionSerializer"""
    
    def test_valid_data(self):
        """Test serializer with valid data"""
        data = {
            'plan_id': 1,
            'billing_period': 'monthly',
            'success_url': 'https://example.com/success',
            'cancel_url': 'https://example.com/cancel'
        }
        serializer = CreateCheckoutSessionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_invalid_billing_period(self):
        """Test serializer with invalid billing period"""
        data = {
            'plan_id': 1,
            'billing_period': 'weekly',  # Invalid
            'success_url': 'https://example.com/success',
            'cancel_url': 'https://example.com/cancel'
        }
        serializer = CreateCheckoutSessionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('billing_period', serializer.errors)
    
    def test_missing_required_fields(self):
        """Test serializer with missing required fields"""
        data = {
            'plan_id': 1,
            # Missing billing_period, success_url, cancel_url
        }
        serializer = CreateCheckoutSessionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('billing_period', serializer.errors)
        self.assertIn('success_url', serializer.errors)
        self.assertIn('cancel_url', serializer.errors)
    
    def test_invalid_urls(self):
        """Test serializer with invalid URLs"""
        data = {
            'plan_id': 1,
            'billing_period': 'monthly',
            'success_url': 'not-a-url',  # Invalid URL
            'cancel_url': 'also-not-a-url'  # Invalid URL
        }
        serializer = CreateCheckoutSessionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('success_url', serializer.errors)
        self.assertIn('cancel_url', serializer.errors)


class CreatePaymentMethodSerializerTest(TestCase):
    """Test cases for CreatePaymentMethodSerializer"""
    
    def test_valid_card_data(self):
        """Test serializer with valid card data"""
        data = {
            'type': 'card',
            'token': 'tok_visa',
            'is_default': True,
            'brand': 'visa',
            'last4': '4242',
            'exp_month': 12,
            'exp_year': 2025
        }
        serializer = CreatePaymentMethodSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_valid_minimal_data(self):
        """Test serializer with minimal required data"""
        data = {
            'type': 'pix',
            'token': 'tok_pix_123'
        }
        serializer = CreatePaymentMethodSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_invalid_type(self):
        """Test serializer with invalid payment type"""
        data = {
            'type': 'bitcoin',  # Invalid type
            'token': 'tok_btc'
        }
        serializer = CreatePaymentMethodSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('type', serializer.errors)
    
    def test_missing_token(self):
        """Test serializer without required token"""
        data = {
            'type': 'card',
            # Missing token
        }
        serializer = CreatePaymentMethodSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)
    
    def test_invalid_expiry_date(self):
        """Test serializer with invalid expiry date"""
        data = {
            'type': 'card',
            'token': 'tok_visa',
            'brand': 'visa',
            'last4': '4242',
            'exp_month': 13,  # Invalid month
            'exp_year': 2020  # Past year
        }
        serializer = CreatePaymentMethodSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # Should fail due to invalid month
        self.assertIn('exp_month', serializer.errors)


class CompanySubscriptionSerializerTest(TestCase):
    """Test cases for CompanySubscriptionSerializer"""
    
    def setUp(self):
        self.company = CompanyFactory(name='Test Company')
        self.plan = SubscriptionPlanFactory()
        self.subscription = SubscriptionFactory(
            company=self.company,
            plan=self.plan,
            status='active'
        )
    
    def test_subscription_status_format(self):
        """Test subscription status serialization format"""
        # Create usage records for testing
        from apps.payments.models import UsageRecord
        UsageRecord.objects.create(
            company=self.company,
            type='transaction',
            count=150,
            period_start=timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            period_end=(timezone.now().replace(day=1) + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)
        )
        
        # Test with the actual company instance
        serializer = CompanySubscriptionSerializer(instance=self.company)
        data = serializer.data
        self.assertEqual(data['name'], 'Test Company')
        self.assertIn('subscription', data)
        self.assertIn('current_usage', data)
        
        # Test subscription is properly serialized
        self.assertIsInstance(data['subscription'], dict)
        self.assertEqual(data['subscription']['status'], 'active')
        
        # Test usage data
        self.assertIn('transaction', data['current_usage'])
        self.assertEqual(data['current_usage']['transaction']['count'], 150)