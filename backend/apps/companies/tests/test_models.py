"""
Unit tests for companies app models
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction, IntegrityError
from datetime import timedelta
import threading
from unittest.mock import patch

from apps.companies.models import Company, SubscriptionPlan, ResourceUsage
from .factories import (
    UserFactory, CompanyFactory, SubscriptionPlanFactory, 
    ResourceUsageFactory, TrialCompanyFactory, ActiveCompanyFactory
)
from .test_utils import CompaniesUnitTestCase

User = get_user_model()


class SubscriptionPlanModelTest(TestCase):
    """Test SubscriptionPlan model functionality"""
    
    def test_subscription_plan_creation(self):
        """Test basic subscription plan creation"""
        plan = SubscriptionPlanFactory(
            name='Test Plan',
            slug='test-plan',
            price_monthly=Decimal('19.99'),
            price_yearly=Decimal('199.99')
        )
        
        self.assertEqual(plan.name, 'Test Plan')
        self.assertEqual(plan.slug, 'test-plan')
        self.assertEqual(plan.price_monthly, Decimal('19.99'))
        self.assertEqual(plan.price_yearly, Decimal('199.99'))
        self.assertTrue(plan.is_active)
    
    def test_subscription_plan_str(self):
        """Test string representation of subscription plan"""
        plan = SubscriptionPlanFactory(
            name='Premium',
            price_monthly=Decimal('29.99')
        )
        
        expected = "Premium - $29.99/mo"
        self.assertEqual(str(plan), expected)
    
    def test_subscription_plan_ordering(self):
        """Test subscription plan ordering"""
        plan1 = SubscriptionPlanFactory(display_order=2, price_monthly=Decimal('19.99'))
        plan2 = SubscriptionPlanFactory(display_order=1, price_monthly=Decimal('9.99'))
        plan3 = SubscriptionPlanFactory(display_order=2, price_monthly=Decimal('29.99'))
        
        plans = SubscriptionPlan.objects.all()
        
        # Should be ordered by display_order, then price_monthly
        self.assertEqual(list(plans), [plan2, plan1, plan3])
    
    def test_subscription_plan_unique_slug(self):
        """Test that subscription plan slugs must be unique"""
        SubscriptionPlanFactory(slug='premium')
        
        with self.assertRaises(IntegrityError):
            SubscriptionPlanFactory(slug='premium')


class CompanyModelTest(CompaniesUnitTestCase):
    """Test Company model functionality"""
    
    def test_company_creation(self):
        """Test basic company creation"""
        user = UserFactory()
        company = CompanyFactory(owner=user, name='Test Company')
        
        self.assertEqual(company.owner, user)
        self.assertEqual(company.name, 'Test Company')
        self.assertEqual(company.subscription_status, 'trial')
        self.assertEqual(company.billing_cycle, 'monthly')
        self.assertTrue(company.is_active)
        self.assertEqual(company.current_month_transactions, 0)
        self.assertEqual(company.current_month_ai_requests, 0)
    
    def test_company_trial_auto_setup(self):
        """Test that trial is automatically set up on company creation"""
        user = UserFactory()
        company = CompanyFactory(owner=user)
        
        self.assertEqual(company.subscription_status, 'trial')
        self.assertIsNotNone(company.trial_ends_at)
        
        # Trial should end approximately 14 days from now
        expected_trial_end = timezone.now() + timedelta(days=14)
        time_diff = abs((company.trial_ends_at - expected_trial_end).total_seconds())
        self.assertLess(time_diff, 60, "Trial end date should be within 1 minute of expected")
    
    def test_company_str(self):
        """Test string representation of company"""
        company = CompanyFactory(name='Acme Corp')
        self.assertEqual(str(company), 'Acme Corp')
    
    def test_is_trial_active_property(self):
        """Test is_trial_active property"""
        # Active trial
        company = TrialCompanyFactory()
        self.assertTrue(company.is_trial_active)
        
        # Expired trial
        expired_company = CompanyFactory(
            subscription_status='trial',
            trial_ends_at=timezone.now() - timedelta(days=1)
        )
        self.assertFalse(expired_company.is_trial_active)
        
        # Active subscription (not trial)
        active_company = ActiveCompanyFactory()
        self.assertFalse(active_company.is_trial_active)
    
    def test_days_until_trial_ends(self):
        """Test days_until_trial_ends property"""
        # Active trial
        trial_end = timezone.now() + timedelta(days=5)
        company = CompanyFactory(
            subscription_status='trial',
            trial_ends_at=trial_end
        )
        self.assertEqual(company.days_until_trial_ends, 5)
        
        # Expired trial
        expired_company = CompanyFactory(
            subscription_status='trial',
            trial_ends_at=timezone.now() - timedelta(days=1)
        )
        self.assertEqual(expired_company.days_until_trial_ends, 0)
        
        # Non-trial company
        active_company = ActiveCompanyFactory()
        self.assertEqual(active_company.days_until_trial_ends, 0)
    
    def test_can_use_feature(self):
        """Test can_use_feature method"""
        # Company with no plan
        company = CompanyFactory(subscription_plan=None)
        self.assertFalse(company.can_use_feature('ai_insights'))
        self.assertFalse(company.can_use_feature('advanced_reports'))
        
        # Company with plan that has AI insights
        plan = SubscriptionPlanFactory(
            has_ai_insights=True,
            has_advanced_reports=False
        )
        company = CompanyFactory(subscription_plan=plan)
        self.assertTrue(company.can_use_feature('ai_insights'))
        self.assertFalse(company.can_use_feature('advanced_reports'))
    
    def test_check_limit(self):
        """Test check_limit method"""
        plan = SubscriptionPlanFactory(
            max_transactions=100,
            max_bank_accounts=2,
            max_ai_requests=50
        )
        company = CompanyFactory(
            subscription_plan=plan,
            current_month_transactions=80,
            current_month_ai_requests=45
        )
        
        # Under limit
        is_reached, message = company.check_limit('transactions')
        self.assertFalse(is_reached)
        self.assertEqual(message, "80/100")
        
        # At limit
        company.current_month_transactions = 100
        is_reached, message = company.check_limit('transactions')
        self.assertTrue(is_reached)
        self.assertEqual(message, "100/100")
        
        # Over limit
        company.current_month_ai_requests = 60
        is_reached, message = company.check_limit('ai_requests')
        self.assertTrue(is_reached)
        self.assertEqual(message, "60/50")
        
        # Unknown limit type
        is_reached, message = company.check_limit('unknown')
        self.assertFalse(is_reached)
        self.assertEqual(message, "Unknown limit type")
    
    def test_increment_usage_atomic(self):
        """Test that increment_usage is atomic and thread-safe"""
        company = CompanyFactory(current_month_transactions=0)
        
        def increment_transactions():
            fresh_company = Company.objects.get(pk=company.pk)
            fresh_company.increment_usage('transactions')
        
        # Run multiple threads to simulate concurrent requests
        threads = []
        num_threads = 10
        
        for _ in range(num_threads):
            thread = threading.Thread(target=increment_transactions)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Refresh and check final count
        company.refresh_from_db()
        self.assertEqual(company.current_month_transactions, num_threads)
    
    def test_increment_usage_creates_resource_usage(self):
        """Test that increment_usage creates/updates ResourceUsage records"""
        company = CompanyFactory(current_month_transactions=0)
        
        # Should have no ResourceUsage initially
        self.assertEqual(ResourceUsage.objects.filter(company=company).count(), 0)
        
        # Increment usage
        company.increment_usage('transactions')
        
        # Should create ResourceUsage record
        usage_records = ResourceUsage.objects.filter(company=company)
        self.assertEqual(usage_records.count(), 1)
        
        usage = usage_records.first()
        self.assertEqual(usage.transactions_count, 1)
        self.assertEqual(usage.ai_requests_count, 0)
    
    def test_increment_ai_usage(self):
        """Test incrementing AI usage"""
        company = CompanyFactory(current_month_ai_requests=5)
        
        company.increment_usage('ai_requests')
        
        company.refresh_from_db()
        self.assertEqual(company.current_month_ai_requests, 6)
    
    def test_reset_monthly_usage(self):
        """Test reset_monthly_usage method"""
        company = CompanyFactory(
            current_month_transactions=100,
            current_month_ai_requests=50
        )
        
        company.reset_monthly_usage()
        
        self.assertEqual(company.current_month_transactions, 0)
        self.assertEqual(company.current_month_ai_requests, 0)
    
    def test_company_one_to_one_with_user(self):
        """Test that company has one-to-one relationship with user"""
        user = UserFactory()
        company = CompanyFactory(owner=user)
        
        # User should have access to company via reverse relation
        self.assertEqual(user.company, company)
        
        # Cannot create another company for same user
        with self.assertRaises(IntegrityError):
            CompanyFactory(owner=user)


class ResourceUsageModelTest(CompaniesUnitTestCase):
    """Test ResourceUsage model functionality"""
    
    def test_resource_usage_creation(self):
        """Test basic resource usage creation"""
        company = CompanyFactory()
        usage = ResourceUsageFactory(
            company=company,
            transactions_count=100,
            ai_requests_count=25
        )
        
        self.assertEqual(usage.company, company)
        self.assertEqual(usage.transactions_count, 100)
        self.assertEqual(usage.ai_requests_count, 25)
        self.assertIsNotNone(usage.month)
        self.assertIsNotNone(usage.created_at)
    
    def test_resource_usage_str(self):
        """Test string representation of resource usage"""
        company = CompanyFactory(name='Test Company')
        usage = ResourceUsageFactory(
            company=company,
            month=timezone.now().replace(day=1).date()
        )
        
        expected_month = timezone.now().strftime('%B %Y')
        expected = f"Test Company - {expected_month}"
        self.assertEqual(str(usage), expected)
    
    def test_resource_usage_unique_company_month(self):
        """Test that company-month combination must be unique"""
        company = CompanyFactory()
        month = timezone.now().replace(day=1).date()
        
        ResourceUsageFactory(company=company, month=month)
        
        # Should not be able to create another record for same company-month
        with self.assertRaises(IntegrityError):
            ResourceUsageFactory(company=company, month=month)
    
    def test_get_or_create_current_month(self):
        """Test get_or_create_current_month class method"""
        company = CompanyFactory(
            current_month_transactions=50,
            current_month_ai_requests=10
        )
        
        # Should create new record
        usage = ResourceUsage.get_or_create_current_month(company)
        self.assertEqual(usage.company, company)
        self.assertEqual(usage.transactions_count, 50)
        self.assertEqual(usage.ai_requests_count, 10)
        
        # Should return existing record on second call
        usage2 = ResourceUsage.get_or_create_current_month(company)
        self.assertEqual(usage.id, usage2.id)
    
    def test_resource_usage_ordering(self):
        """Test resource usage ordering (most recent first)"""
        company = CompanyFactory()
        
        # Create usage records for different months
        month1 = timezone.now().replace(day=1).date()
        month2 = (timezone.now() - timedelta(days=32)).replace(day=1).date()
        month3 = (timezone.now() - timedelta(days=65)).replace(day=1).date()
        
        usage1 = ResourceUsageFactory(company=company, month=month1)
        usage2 = ResourceUsageFactory(company=company, month=month2)
        usage3 = ResourceUsageFactory(company=company, month=month3)
        
        # Should be ordered by month descending (most recent first)
        usage_list = list(ResourceUsage.objects.filter(company=company))
        self.assertEqual(usage_list, [usage1, usage2, usage3])


class ModelIntegrationTest(CompaniesUnitTestCase):
    """Test integration between models"""
    
    def test_company_subscription_plan_integration(self):
        """Test integration between Company and SubscriptionPlan"""
        plan = SubscriptionPlanFactory(
            name='Premium',
            max_transactions=1000,
            has_ai_insights=True
        )
        company = CompanyFactory(subscription_plan=plan)
        
        # Test feature access through plan
        self.assertTrue(company.can_use_feature('ai_insights'))
        
        # Test limit checking through plan
        company.current_month_transactions = 500
        is_reached, message = company.check_limit('transactions')
        self.assertFalse(is_reached)
        self.assertEqual(message, "500/1000")
    
    def test_company_resource_usage_integration(self):
        """Test integration between Company and ResourceUsage"""
        company = CompanyFactory()
        
        # Increment usage should create ResourceUsage record
        company.increment_usage('transactions')
        company.increment_usage('ai_requests')
        
        # Should have one ResourceUsage record for current month
        usage_records = company.usage_history.all()
        self.assertEqual(usage_records.count(), 1)
        
        usage = usage_records.first()
        self.assertEqual(usage.transactions_count, 1)
        self.assertEqual(usage.ai_requests_count, 1)
    
    def test_cascading_delete_protection(self):
        """Test that subscription plans are protected from deletion"""
        plan = SubscriptionPlanFactory()
        company = CompanyFactory(subscription_plan=plan)
        
        # Should not be able to delete plan that's in use
        with self.assertRaises(Exception):
            plan.delete()
    
    def test_company_deletion_cascades_to_usage(self):
        """Test that deleting company cascades to ResourceUsage"""
        company = CompanyFactory()
        ResourceUsageFactory(company=company)
        
        usage_count = ResourceUsage.objects.filter(company=company).count()
        self.assertEqual(usage_count, 1)
        
        # Delete company should cascade to usage records
        company.delete()
        
        usage_count = ResourceUsage.objects.filter(company=company).count()
        self.assertEqual(usage_count, 0)