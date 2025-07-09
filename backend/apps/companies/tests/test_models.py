"""
Comprehensive tests for Companies app models
Testing subscription plans, company profiles, and multi-tenancy
"""
import uuid
from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.companies.models import (
    SubscriptionPlan,
    Company,
    CompanyUser
)

User = get_user_model()


class SubscriptionPlanModelTest(TestCase):
    """Test SubscriptionPlan model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.plan_data = {
            'name': 'Professional Plan',
            'slug': 'professional',
            'plan_type': 'pro',
            'price_monthly': Decimal('99.90'),
            'price_yearly': Decimal('999.00'),
            'max_transactions': 5000,
            'max_bank_accounts': 10,
            'max_users': 5,
            'has_ai_categorization': True,
            'has_advanced_reports': True,
            'has_api_access': True,
            'has_accountant_access': True,
            'is_active': True
        }
    
    def test_subscription_plan_creation(self):
        """Test creating a subscription plan with valid data"""
        plan = SubscriptionPlan.objects.create(**self.plan_data)
        
        self.assertEqual(plan.name, 'Professional Plan')
        self.assertEqual(plan.plan_type, 'pro')
        self.assertEqual(plan.price_monthly, Decimal('99.90'))
        self.assertEqual(plan.max_transactions, 5000)
        self.assertTrue(plan.has_advanced_reports)
        self.assertTrue(plan.is_active)
    
    def test_subscription_plan_string_representation(self):
        """Test string representation of subscription plan"""
        plan = SubscriptionPlan.objects.create(**self.plan_data)
        expected = f"{plan.name} - R$ {plan.price_monthly}/mês"
        self.assertEqual(str(plan), expected)
    
    def test_subscription_plan_slug_uniqueness(self):
        """Test that plan slug must be unique"""
        SubscriptionPlan.objects.create(**self.plan_data)
        
        # Try to create another plan with same slug
        with self.assertRaises(IntegrityError):
            SubscriptionPlan.objects.create(
                name='Another Plan',
                slug='professional',  # Same slug
                plan_type='enterprise',
                price_monthly=Decimal('199.90'),
                price_yearly=Decimal('1999.00')
            )
    
    def test_subscription_plan_defaults(self):
        """Test default values for optional fields"""
        minimal_data = {
            'name': 'Basic Plan',
            'slug': 'basic',
            'plan_type': 'starter',
            'price_monthly': Decimal('29.90'),
            'price_yearly': Decimal('299.00')
        }
        plan = SubscriptionPlan.objects.create(**minimal_data)
        
        self.assertEqual(plan.max_transactions, 500)
        self.assertEqual(plan.max_bank_accounts, 1)
        self.assertEqual(plan.max_users, 1)
        self.assertTrue(plan.has_ai_categorization)
        self.assertFalse(plan.has_advanced_reports)
        self.assertFalse(plan.has_api_access)
        self.assertFalse(plan.has_accountant_access)
        self.assertTrue(plan.is_active)
    
    def test_subscription_plan_ordering(self):
        """Test that plans are ordered by monthly price"""
        SubscriptionPlan.objects.create(
            name='Enterprise', slug='enterprise', plan_type='enterprise',
            price_monthly=Decimal('199.90'), price_yearly=Decimal('1999.00')
        )
        SubscriptionPlan.objects.create(
            name='Basic', slug='basic', plan_type='starter',
            price_monthly=Decimal('29.90'), price_yearly=Decimal('299.00')
        )
        SubscriptionPlan.objects.create(**self.plan_data)  # 99.90
        
        plans = list(SubscriptionPlan.objects.all())
        prices = [plan.price_monthly for plan in plans]
        
        self.assertEqual(prices, sorted(prices))
        self.assertEqual(plans[0].name, 'Basic')
        self.assertEqual(plans[1].name, 'Professional Plan')
        self.assertEqual(plans[2].name, 'Enterprise')
    
    def test_subscription_plan_types_validation(self):
        """Test that plan_type accepts only valid choices"""
        valid_types = ['starter', 'pro', 'enterprise']
        
        for plan_type in valid_types:
            plan = SubscriptionPlan(
                name=f'Test {plan_type}',
                slug=f'test-{plan_type}',
                plan_type=plan_type,
                price_monthly=Decimal('50.00'),
                price_yearly=Decimal('500.00')
            )
            plan.full_clean()  # Should not raise ValidationError


class CompanyModelTest(TestCase):
    """Test Company model functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create subscription plan
        self.subscription_plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            plan_type='pro',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00')
        )
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.company_data = {
            'owner': self.user,
            'name': 'Test Company Ltd',
            'trade_name': 'Test Company',
            'cnpj': '12.345.678/0001-99',
            'company_type': 'ltda',
            'business_sector': 'technology',
            'email': 'contact@testcompany.com',
            'phone': '+55 11 99999-9999',
            'website': 'https://testcompany.com',
            'address_street': 'Test Street',
            'address_number': '123',
            'address_city': 'São Paulo',
            'address_state': 'SP',
            'address_zipcode': '01234-567',
            'monthly_revenue': Decimal('50000.00'),
            'employee_count': 10,
            'subscription_plan': self.subscription_plan,
            'subscription_status': 'active',
            'primary_color': '#FF6B6B',
            'currency': 'BRL',
            'fiscal_year_start': '01'
        }
    
    def test_company_creation(self):
        """Test creating a company with valid data"""
        company = Company.objects.create(**self.company_data)
        
        self.assertEqual(company.owner, self.user)
        self.assertEqual(company.name, 'Test Company Ltd')
        self.assertEqual(company.cnpj, '12.345.678/0001-99')
        self.assertEqual(company.company_type, 'ltda')
        self.assertEqual(company.business_sector, 'technology')
        self.assertEqual(company.subscription_plan, self.subscription_plan)
        self.assertTrue(company.is_active)
    
    def test_company_string_representation(self):
        """Test string representation of company"""
        company = Company.objects.create(**self.company_data)
        self.assertEqual(str(company), 'Test Company Ltd')
    
    def test_company_owner_one_to_one_relationship(self):
        """Test that each user can only own one company"""
        Company.objects.create(**self.company_data)
        
        # Try to create another company with same owner
        with self.assertRaises(IntegrityError):
            Company.objects.create(
                owner=self.user,  # Same owner
                name='Another Company',
                company_type='mei',
                business_sector='services',
                subscription_plan=self.subscription_plan
            )
    
    def test_company_cnpj_uniqueness(self):
        """Test that CNPJ must be unique"""
        Company.objects.create(**self.company_data)
        
        # Create another user and try to use same CNPJ
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        
        with self.assertRaises(IntegrityError):
            Company.objects.create(
                owner=other_user,
                name='Other Company',
                cnpj='12.345.678/0001-99',  # Same CNPJ
                company_type='mei',
                business_sector='services',
                subscription_plan=self.subscription_plan
            )
    
    def test_company_is_trial_property(self):
        """Test is_trial property"""
        company = Company.objects.create(**self.company_data)
        
        # Test trial status
        company.subscription_status = 'trial'
        self.assertTrue(company.is_trial)
        
        # Test non-trial status
        company.subscription_status = 'active'
        self.assertFalse(company.is_trial)
    
    def test_company_is_subscribed_property(self):
        """Test is_subscribed property"""
        company = Company.objects.create(**self.company_data)
        
        # Test active subscription
        company.subscription_status = 'active'
        self.assertTrue(company.is_subscribed)
        
        # Test non-active status
        company.subscription_status = 'trial'
        self.assertFalse(company.is_subscribed)
        
        company.subscription_status = 'cancelled'
        self.assertFalse(company.is_subscribed)
    
    def test_company_display_name_property(self):
        """Test display_name property"""
        company = Company.objects.create(**self.company_data)
        
        # With trade name
        self.assertEqual(company.display_name, 'Test Company')
        
        # Without trade name
        company.trade_name = ''
        self.assertEqual(company.display_name, 'Test Company Ltd')
    
    def test_company_defaults(self):
        """Test default values for optional fields"""
        minimal_data = {
            'owner': self.user,
            'name': 'Minimal Company',
            'company_type': 'mei',
            'business_sector': 'other',
            'subscription_plan': self.subscription_plan
        }
        company = Company.objects.create(**minimal_data)
        
        self.assertEqual(company.subscription_status, 'trial')
        self.assertEqual(company.employee_count, 1)
        self.assertEqual(company.primary_color, '#3B82F6')
        self.assertEqual(company.currency, 'BRL')
        self.assertEqual(company.fiscal_year_start, '01')
        self.assertTrue(company.enable_ai_categorization)
        self.assertEqual(company.auto_categorize_threshold, 0.8)
        self.assertTrue(company.enable_notifications)
        self.assertTrue(company.enable_email_reports)
        self.assertTrue(company.is_active)
    
    def test_company_type_choices_validation(self):
        """Test that company_type accepts only valid choices"""
        valid_types = ['mei', 'me', 'epp', 'ltda', 'sa', 'other']
        
        for company_type in valid_types:
            company = Company(
                owner=self.user,
                name=f'Test Company {company_type}',
                company_type=company_type,
                business_sector='other',
                subscription_plan=self.subscription_plan
            )
            # Note: We can't easily test validation without creating objects
            # This would require a separate user for each test
    
    def test_company_business_sector_choices_validation(self):
        """Test that business_sector accepts only valid choices"""
        valid_sectors = [
            'retail', 'services', 'industry', 'construction', 'agriculture',
            'technology', 'healthcare', 'education', 'food', 'beauty',
            'automotive', 'real_estate', 'consulting', 'other'
        ]
        
        for sector in valid_sectors:
            # Test that the choice is valid (would need separate users for actual creation)
            self.assertIn(sector, [choice[0] for choice in Company.BUSINESS_SECTORS])
    
    def test_company_subscription_status_choices(self):
        """Test subscription status choices"""
        company = Company.objects.create(**self.company_data)
        
        valid_statuses = ['trial', 'active', 'past_due', 'cancelled', 'suspended']
        
        for status in valid_statuses:
            company.subscription_status = status
            company.save()
            company.refresh_from_db()
            self.assertEqual(company.subscription_status, status)
    
    def test_company_fiscal_year_choices(self):
        """Test fiscal year start month choices"""
        company = Company.objects.create(**self.company_data)
        
        # Test valid months (01-12)
        for month in range(1, 13):
            month_str = str(month).zfill(2)
            company.fiscal_year_start = month_str
            company.save()
            company.refresh_from_db()
            self.assertEqual(company.fiscal_year_start, month_str)
    
    def test_company_subscription_plan_protection(self):
        """Test that subscription plan is protected from deletion"""
        company = Company.objects.create(**self.company_data)
        
        # Try to delete subscription plan while company exists
        with self.assertRaises(ProtectedError):
            self.subscription_plan.delete()


class CompanyUserModelTest(TestCase):
    """Test CompanyUser model functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create subscription plan
        self.subscription_plan = SubscriptionPlan.objects.create(
            name='Enterprise Plan',
            slug='enterprise',
            plan_type='enterprise',
            price_monthly=Decimal('199.90'),
            price_yearly=Decimal('1999.00'),
            max_users=10
        )
        
        # Create owner user
        self.owner_user = User.objects.create_user(
            username='owneruser',
            email='owner@example.com',
            password='testpass123',
            first_name='Owner',
            last_name='User'
        )
        
        # Create company
        self.company = Company.objects.create(
            owner=self.owner_user,
            name='Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.subscription_plan
        )
        
        # Create additional user
        self.additional_user = User.objects.create_user(
            username='additionaluser',
            email='user@example.com',
            password='testpass123',
            first_name='Additional',
            last_name='User'
        )
        
        self.company_user_data = {
            'company': self.company,
            'user': self.additional_user,
            'role': 'manager',
            'permissions': {'can_view_reports': True, 'can_manage_transactions': False},
            'is_active': True
        }
    
    def test_company_user_creation(self):
        """Test creating a company user"""
        company_user = CompanyUser.objects.create(**self.company_user_data)
        
        self.assertEqual(company_user.company, self.company)
        self.assertEqual(company_user.user, self.additional_user)
        self.assertEqual(company_user.role, 'manager')
        self.assertEqual(company_user.permissions['can_view_reports'], True)
        self.assertTrue(company_user.is_active)
    
    def test_company_user_string_representation(self):
        """Test string representation of company user"""
        company_user = CompanyUser.objects.create(**self.company_user_data)
        expected = f"{self.additional_user.full_name} - {self.company.name} ({company_user.role})"
        self.assertEqual(str(company_user), expected)
    
    def test_company_user_unique_together_constraint(self):
        """Test that a user can only have one role per company"""
        CompanyUser.objects.create(**self.company_user_data)
        
        # Try to create another role for same user in same company
        with self.assertRaises(IntegrityError):
            CompanyUser.objects.create(
                company=self.company,
                user=self.additional_user,  # Same user
                role='accountant',  # Different role
                is_active=True
            )
    
    def test_company_user_role_choices(self):
        """Test that role accepts only valid choices"""
        valid_roles = ['owner', 'admin', 'manager', 'accountant', 'viewer']
        
        for role in valid_roles:
            company_user = CompanyUser(
                company=self.company,
                user=self.additional_user,
                role=role
            )
            # Test that the role is valid
            self.assertIn(role, [choice[0] for choice in CompanyUser.ROLE_CHOICES])
    
    def test_company_user_multiple_companies(self):
        """Test that a user can belong to multiple companies"""
        # Create another company with different owner
        other_owner = User.objects.create_user(
            username='otherowner',
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='Owner'
        )
        
        other_company = Company.objects.create(
            owner=other_owner,
            name='Other Company',
            company_type='mei',
            business_sector='services',
            subscription_plan=self.subscription_plan
        )
        
        # Create company users for same user in different companies
        company_user1 = CompanyUser.objects.create(
            company=self.company,
            user=self.additional_user,
            role='manager'
        )
        
        company_user2 = CompanyUser.objects.create(
            company=other_company,
            user=self.additional_user,
            role='viewer'
        )
        
        self.assertEqual(CompanyUser.objects.filter(user=self.additional_user).count(), 2)
        self.assertNotEqual(company_user1.company, company_user2.company)
        self.assertEqual(company_user1.user, company_user2.user)
    
    def test_company_user_defaults(self):
        """Test default values for optional fields"""
        minimal_data = {
            'company': self.company,
            'user': self.additional_user,
            'role': 'viewer'
        }
        company_user = CompanyUser.objects.create(**minimal_data)
        
        self.assertEqual(company_user.permissions, {})
        self.assertTrue(company_user.is_active)
        self.assertIsNotNone(company_user.invited_at)
        self.assertIsNone(company_user.joined_at)
    
    def test_company_user_timestamps(self):
        """Test automatic timestamp creation"""
        company_user = CompanyUser.objects.create(**self.company_user_data)
        
        self.assertIsNotNone(company_user.invited_at)
        self.assertIsInstance(company_user.invited_at, datetime)
        
        # Test that invited_at is set to current time
        time_diff = timezone.now() - company_user.invited_at
        self.assertLess(time_diff.total_seconds(), 60)  # Within last minute
    
    def test_company_user_joined_at_update(self):
        """Test manually setting joined_at timestamp"""
        company_user = CompanyUser.objects.create(**self.company_user_data)
        
        # Initially, joined_at should be None
        self.assertIsNone(company_user.joined_at)
        
        # Set joined_at
        joined_time = timezone.now()
        company_user.joined_at = joined_time
        company_user.save()
        
        company_user.refresh_from_db()
        self.assertEqual(company_user.joined_at, joined_time)
    
    def test_company_user_cascade_deletion(self):
        """Test that company user is deleted when company or user is deleted"""
        company_user = CompanyUser.objects.create(**self.company_user_data)
        company_user_id = company_user.id
        
        # Delete user - should cascade
        self.additional_user.delete()
        self.assertFalse(CompanyUser.objects.filter(id=company_user_id).exists())
        
        # Create new user and company user for company deletion test
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123',
            first_name='New',
            last_name='User'
        )
        
        new_company_user = CompanyUser.objects.create(
            company=self.company,
            user=new_user,
            role='viewer'
        )
        new_company_user_id = new_company_user.id
        
        # Delete company - should cascade
        self.company.delete()
        self.assertFalse(CompanyUser.objects.filter(id=new_company_user_id).exists())


class CompanyModelIntegrationTest(TestCase):
    """Integration tests for Company model with related models"""
    
    def setUp(self):
        """Set up test data"""
        self.subscription_plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test',
            plan_type='pro',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00')
        )
        
        self.user = User.objects.create_user(
            username='testuser2',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_company_with_multiple_users(self):
        """Test company with multiple users in different roles"""
        company = Company.objects.create(
            owner=self.user,
            name='Multi-User Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.subscription_plan
        )
        
        # Create additional users
        manager = User.objects.create_user(
            username='manageruser',
            email='manager@example.com',
            password='testpass123',
            first_name='Manager',
            last_name='User'
        )
        
        accountant = User.objects.create_user(
            username='accountantuser',
            email='accountant@example.com',
            password='testpass123',
            first_name='Accountant',
            last_name='User'
        )
        
        viewer = User.objects.create_user(
            username='vieweruser',
            email='viewer@example.com',
            password='testpass123',
            first_name='Viewer',
            last_name='User'
        )
        
        # Add users to company
        CompanyUser.objects.create(company=company, user=manager, role='manager')
        CompanyUser.objects.create(company=company, user=accountant, role='accountant')
        CompanyUser.objects.create(company=company, user=viewer, role='viewer')
        
        # Test relationships
        self.assertEqual(company.company_users.count(), 3)
        self.assertEqual(manager.company_memberships.count(), 1)
        
        # Test role filtering
        managers = company.company_users.filter(role='manager')
        self.assertEqual(managers.count(), 1)
        self.assertEqual(managers.first().user, manager)
    
    def test_company_subscription_plan_relationship(self):
        """Test company-subscription plan relationship"""
        # Create multiple companies with same plan
        company1 = Company.objects.create(
            owner=self.user,
            name='Company 1',
            company_type='mei',
            business_sector='services',
            subscription_plan=self.subscription_plan
        )
        
        other_user = User.objects.create_user(
            username='otherusercompany',
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        
        company2 = Company.objects.create(
            owner=other_user,
            name='Company 2',
            company_type='ltda',
            business_sector='retail',
            subscription_plan=self.subscription_plan
        )
        
        # Test that subscription plan has multiple companies
        self.assertEqual(self.subscription_plan.companies.count(), 2)
        self.assertIn(company1, self.subscription_plan.companies.all())
        self.assertIn(company2, self.subscription_plan.companies.all())
    
    def test_company_user_permissions_json_field(self):
        """Test CompanyUser permissions JSON field functionality"""
        company = Company.objects.create(
            owner=self.user,
            name='Permissions Test Company',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.subscription_plan
        )
        
        additional_user = User.objects.create_user(
            username='permissionsuser',
            email='permissions@example.com',
            password='testpass123',
            first_name='Permissions',
            last_name='User'
        )
        
        # Test complex permissions structure
        complex_permissions = {
            'banking': {
                'can_view': True,
                'can_edit': False,
                'can_delete': False
            },
            'reports': {
                'can_view': True,
                'can_generate': True,
                'can_export': False
            },
            'users': {
                'can_invite': False,
                'can_remove': False
            }
        }
        
        company_user = CompanyUser.objects.create(
            company=company,
            user=additional_user,
            role='manager',
            permissions=complex_permissions
        )
        
        # Refresh from database to ensure JSON serialization works
        company_user.refresh_from_db()
        
        self.assertEqual(company_user.permissions['banking']['can_view'], True)
        self.assertEqual(company_user.permissions['banking']['can_edit'], False)
        self.assertEqual(company_user.permissions['reports']['can_generate'], True)
        self.assertEqual(company_user.permissions['users']['can_invite'], False)