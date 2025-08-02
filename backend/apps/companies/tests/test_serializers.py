"""
Unit tests for companies app serializers
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.companies.serializers import (
    SubscriptionPlanSerializer,
    CompanySerializer,
    UsageLimitsSerializer,
    SubscriptionStatusSerializer
)
from .factories import (
    UserFactory, CompanyFactory, SubscriptionPlanFactory, 
    TrialCompanyFactory, ActiveCompanyFactory
)
from .test_utils import CompaniesUnitTestCase

User = get_user_model()


class SubscriptionPlanSerializerTest(TestCase):
    """Test SubscriptionPlanSerializer functionality"""
    
    def test_subscription_plan_serialization(self):
        """Test basic subscription plan serialization"""
        plan = SubscriptionPlanFactory(
            name='Premium',
            slug='premium',
            price_monthly=Decimal('19.99'),
            price_yearly=Decimal('199.99'),
            max_transactions=2000,
            max_bank_accounts=5,
            max_ai_requests_per_month=200,
            enable_ai_insights=True,
            has_advanced_reports=True
        )
        
        serializer = SubscriptionPlanSerializer(plan)
        data = serializer.data
        
        # Check all required fields are present
        expected_fields = [
            'id', 'name', 'slug', 'price_monthly', 'price_yearly', 'yearly_discount',
            'max_transactions', 'max_bank_accounts', 'max_ai_requests_per_month',
            'enable_ai_insights', 'has_advanced_reports'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        # Check field values
        self.assertEqual(data['name'], 'Premium')
        self.assertEqual(data['slug'], 'premium')
        self.assertEqual(Decimal(data['price_monthly']), Decimal('19.99'))
        self.assertEqual(Decimal(data['price_yearly']), Decimal('199.99'))
        self.assertEqual(data['max_transactions'], 2000)
        self.assertEqual(data['max_bank_accounts'], 5)
        self.assertEqual(data['max_ai_requests_per_month'], 200)
        self.assertTrue(data['enable_ai_insights'])
        self.assertTrue(data['has_advanced_reports'])
    
    def test_yearly_discount_calculation(self):
        """Test yearly discount calculation"""
        # Plan with discount
        plan = SubscriptionPlanFactory(
            price_monthly=Decimal('20.00'),
            price_yearly=Decimal('200.00')  # 17% discount (240 - 200 = 40, 40/240 = 16.67%)
        )
        
        serializer = SubscriptionPlanSerializer(plan)
        data = serializer.data
        
        expected_discount = int(((Decimal('20.00') * 12 - Decimal('200.00')) / (Decimal('20.00') * 12)) * 100)
        self.assertEqual(data['yearly_discount'], expected_discount)
    
    def test_yearly_discount_zero_monthly_price(self):
        """Test yearly discount calculation with zero monthly price"""
        plan = SubscriptionPlanFactory(
            price_monthly=Decimal('0.00'),
            price_yearly=Decimal('0.00')
        )
        
        serializer = SubscriptionPlanSerializer(plan)
        data = serializer.data
        
        self.assertEqual(data['yearly_discount'], 0)
    
    def test_multiple_plans_serialization(self):
        """Test serializing multiple subscription plans"""
        plan1 = SubscriptionPlanFactory(name='Basic')
        plan2 = SubscriptionPlanFactory(name='Premium')
        
        plans = [plan1, plan2]
        serializer = SubscriptionPlanSerializer(plans, many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], 'Basic')
        self.assertEqual(data[1]['name'], 'Premium')


class CompanySerializerTest(CompaniesUnitTestCase):
    """Test CompanySerializer functionality"""
    
    def test_company_serialization(self):
        """Test basic company serialization"""
        plan = SubscriptionPlanFactory(name='Premium')
        user = UserFactory(email='owner@test.com')
        company = CompanyFactory(
            owner=user,
            name='Test Company',
            subscription_plan=plan,
            subscription_status='active',
            billing_cycle='yearly',
            current_month_transactions=100,
            current_month_ai_requests=25
        )
        
        serializer = CompanySerializer(company)
        data = serializer.data
        
        # Check all required fields are present
        expected_fields = [
            'id', 'name', 'owner_email', 'subscription_plan', 'subscription_status',
            'billing_cycle', 'trial_ends_at', 'is_trial_active', 'days_until_trial_ends',
            'current_month_transactions', 'current_month_ai_requests', 'created_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        # Check field values
        self.assertEqual(data['name'], 'Test Company')
        self.assertEqual(data['owner_email'], 'owner@test.com')
        self.assertEqual(data['subscription_status'], 'active')
        self.assertEqual(data['billing_cycle'], 'yearly')
        self.assertEqual(data['current_month_transactions'], 100)
        self.assertEqual(data['current_month_ai_requests'], 25)
        
        # Check nested subscription plan
        self.assertIsInstance(data['subscription_plan'], dict)
        self.assertEqual(data['subscription_plan']['name'], 'Premium')
    
    def test_company_with_no_plan(self):
        """Test serializing company with no subscription plan"""
        user = UserFactory()
        company = CompanyFactory(owner=user, subscription_plan=None)
        
        serializer = CompanySerializer(company)
        data = serializer.data
        
        self.assertIsNone(data['subscription_plan'])
    
    def test_trial_properties_serialization(self):
        """Test trial-related properties serialization"""
        # Active trial
        company = TrialCompanyFactory()
        serializer = CompanySerializer(company)
        data = serializer.data
        
        self.assertTrue(data['is_trial_active'])
        self.assertGreater(data['days_until_trial_ends'], 0)
        self.assertIsNotNone(data['trial_ends_at'])
        
        # Expired trial
        expired_company = CompanyFactory(
            subscription_status='trial',
            trial_ends_at=timezone.now() - timedelta(days=1)
        )
        serializer = CompanySerializer(expired_company)
        data = serializer.data
        
        self.assertFalse(data['is_trial_active'])
        self.assertEqual(data['days_until_trial_ends'], 0)
    
    def test_read_only_fields(self):
        """Test that read-only fields cannot be updated"""
        user = UserFactory()
        company = CompanyFactory(owner=user)
        
        # Try to update read-only fields
        update_data = {
            'name': 'Updated Company',
            'owner_email': 'newemail@test.com',  # read-only
            'subscription_status': 'active',  # read-only
            'current_month_transactions': 999,  # read-only
            'current_month_ai_requests': 999,  # read-only
        }
        
        serializer = CompanySerializer(company, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_company = serializer.save()
        
        # Only non-read-only fields should be updated
        self.assertEqual(updated_company.name, 'Updated Company')
        self.assertEqual(updated_company.owner.email, user.email)  # unchanged
        self.assertEqual(updated_company.subscription_status, company.subscription_status)  # unchanged
        self.assertEqual(updated_company.current_month_transactions, company.current_month_transactions)  # unchanged


class UsageLimitsSerializerTest(TestCase):
    """Test UsageLimitsSerializer functionality"""
    
    def test_usage_limits_serialization(self):
        """Test usage limits serialization"""
        usage_data = {
            'transactions': {
                'used': 150,
                'limit': 500,
                'percentage': 30
            },
            'bank_accounts': {
                'used': 2,
                'limit': 5,
                'percentage': 40
            },
            'ai_requests': {
                'used': 75,
                'limit': 100,
                'percentage': 75
            }
        }
        
        serializer = UsageLimitsSerializer(data=usage_data)
        self.assertTrue(serializer.is_valid())
        
        # Check serialized data structure
        data = serializer.validated_data
        self.assertIn('transactions', data)
        self.assertIn('bank_accounts', data)
        self.assertIn('ai_requests', data)
        
        # Check nested dict structure
        for key in ['transactions', 'bank_accounts', 'ai_requests']:
            self.assertIsInstance(data[key], dict)
            self.assertIn('used', data[key])
            self.assertIn('limit', data[key])
            self.assertIn('percentage', data[key])
    
    def test_usage_limits_validation(self):
        """Test usage limits validation"""
        # Valid data
        valid_data = {
            'transactions': {'used': 100, 'limit': 500, 'percentage': 20},
            'bank_accounts': {'used': 1, 'limit': 2, 'percentage': 50},
            'ai_requests': {'used': 25, 'limit': 100, 'percentage': 25}
        }
        
        serializer = UsageLimitsSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Invalid data (missing required fields)
        invalid_data = {
            'transactions': {'used': 100}  # missing limit and percentage
        }
        
        serializer = UsageLimitsSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())


class SubscriptionStatusSerializerTest(CompaniesUnitTestCase):
    """Test SubscriptionStatusSerializer functionality"""
    
    def test_subscription_status_serialization(self):
        """Test subscription status serialization"""
        plan = SubscriptionPlanFactory(name='Premium')
        
        status_data = {
            'subscription_status': 'active',
            'plan': plan,
            'trial_days_left': 0,
            'trial_ends_at': None,
            'requires_payment_setup': False,
            'has_payment_method': True
        }
        
        serializer = SubscriptionStatusSerializer(status_data)
        data = serializer.data
        
        # Check all required fields are present
        expected_fields = [
            'subscription_status', 'plan', 'trial_days_left', 
            'trial_ends_at', 'requires_payment_setup', 'has_payment_method'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        # Check field values
        self.assertEqual(data['subscription_status'], 'active')
        self.assertEqual(data['trial_days_left'], 0)
        self.assertIsNone(data['trial_ends_at'])
        self.assertFalse(data['requires_payment_setup'])
        self.assertTrue(data['has_payment_method'])
        
        # Check nested plan serialization
        self.assertIsInstance(data['plan'], dict)
        self.assertEqual(data['plan']['name'], 'Premium')
    
    def test_subscription_status_with_trial(self):
        """Test subscription status serialization with trial"""
        trial_end = timezone.now() + timedelta(days=5)
        
        status_data = {
            'subscription_status': 'trial',
            'plan': None,
            'trial_days_left': 5,
            'trial_ends_at': trial_end,
            'requires_payment_setup': True,
            'has_payment_method': False
        }
        
        serializer = SubscriptionStatusSerializer(status_data)
        data = serializer.data
        
        self.assertEqual(data['subscription_status'], 'trial')
        self.assertEqual(data['trial_days_left'], 5)
        self.assertIsNotNone(data['trial_ends_at'])
        self.assertTrue(data['requires_payment_setup'])
        self.assertFalse(data['has_payment_method'])
        self.assertIsNone(data['plan'])
    
    def test_subscription_status_validation(self):
        """Test subscription status validation"""
        # Valid data
        valid_data = {
            'subscription_status': 'active',
            'plan': None,
            'trial_days_left': 0,
            'trial_ends_at': None,
            'requires_payment_setup': False,
            'has_payment_method': True
        }
        
        serializer = SubscriptionStatusSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Missing required fields should fail
        invalid_data = {
            'subscription_status': 'active'
            # missing other required fields
        }
        
        serializer = SubscriptionStatusSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())


class SerializerIntegrationTest(CompaniesUnitTestCase):
    """Test serializer integration scenarios"""
    
    def test_company_with_nested_plan_serialization(self):
        """Test company serialization with nested subscription plan"""
        plan = SubscriptionPlanFactory(
            name='Enterprise',
            price_monthly=Decimal('49.99'),
            enable_ai_insights=True,
            has_advanced_reports=True
        )
        user = UserFactory(email='test@example.com')
        company = CompanyFactory(
            owner=user,
            name='Enterprise Corp',
            subscription_plan=plan
        )
        
        serializer = CompanySerializer(company)
        data = serializer.data
        
        # Check that nested plan is properly serialized
        plan_data = data['subscription_plan']
        self.assertEqual(plan_data['name'], 'Enterprise')
        self.assertEqual(Decimal(plan_data['price_monthly']), Decimal('49.99'))
        self.assertTrue(plan_data['enable_ai_insights'])
        self.assertTrue(plan_data['has_advanced_reports'])
        
        # Check that yearly discount is calculated
        self.assertIn('yearly_discount', plan_data)
    
    def test_serializer_data_consistency(self):
        """Test that serializers maintain data consistency"""
        plan = SubscriptionPlanFactory()
        company = CompanyFactory(subscription_plan=plan)
        
        # Serialize company
        company_serializer = CompanySerializer(company)
        company_data = company_serializer.data
        
        # Serialize plan separately
        plan_serializer = SubscriptionPlanSerializer(plan)
        plan_data = plan_serializer.data
        
        # Nested plan data should match standalone plan data
        nested_plan_data = company_data['subscription_plan']
        
        # Compare key fields
        self.assertEqual(nested_plan_data['id'], plan_data['id'])
        self.assertEqual(nested_plan_data['name'], plan_data['name'])
        self.assertEqual(nested_plan_data['price_monthly'], plan_data['price_monthly'])
        self.assertEqual(nested_plan_data['yearly_discount'], plan_data['yearly_discount'])
    
    def test_serializer_performance_with_multiple_objects(self):
        """Test serializer performance with multiple objects"""
        # Create multiple plans and companies
        plans = [SubscriptionPlanFactory() for _ in range(5)]
        companies = [CompanyFactory(subscription_plan=plans[i % len(plans)]) for i in range(10)]
        
        # Serialize all companies at once
        serializer = CompanySerializer(companies, many=True)
        data = serializer.data
        
        # Check that all companies are serialized
        self.assertEqual(len(data), 10)
        
        # Check that each company has properly nested plan data
        for company_data in data:
            self.assertIn('subscription_plan', company_data)
            if company_data['subscription_plan']:
                self.assertIn('name', company_data['subscription_plan'])
                self.assertIn('price_monthly', company_data['subscription_plan'])