"""
Integration tests for company module security fixes
"""
import threading
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta

from apps.companies.models import Company, ResourceUsage
from apps.companies.permissions import IsCompanyOwner, IsCompanyOwnerOrStaff
from apps.banking.models import BankAccount, Transaction

User = get_user_model()


class CompanySecurityTestCase(APITestCase):
    """Test security fixes for company module"""
    
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create companies
        self.company1 = Company.objects.create(
            owner=self.user1,
            name='Company 1'
        )
        self.company2 = Company.objects.create(
            owner=self.user2,
            name='Company 2'
        )
        
        # Create bank accounts for testing isolation
        self.bank1 = BankAccount.objects.create(
            company=self.company1,
            name='Bank 1',
            account_number='12345'
        )
        self.bank2 = BankAccount.objects.create(
            company=self.company2,
            name='Bank 2',
            account_number='67890'
        )
    
    def test_middleware_blocks_expired_trial(self):
        """Test that TrialExpirationMiddleware blocks expired trials"""
        # Set trial to expired
        self.company1.subscription.trial_ends_at = timezone.now() - timedelta(days=1)
        self.company1.subscription.status = 'trial'
        self.company1.subscription.save()
        
        self.client.force_authenticate(user=self.user1)
        
        # Try to access protected endpoint
        response = self.client.get(reverse('companies:usage-limits'))
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.assertIn('trial_expired', response.data.get('error', ''))
    
    def test_permission_checks_prevent_cross_company_access(self):
        """Test that permission checks prevent cross-company data access"""
        self.client.force_authenticate(user=self.user1)
        
        # Try to access company2's data (should fail)
        permission = IsCompanyOwner()
        request = type('Request', (), {'user': self.user1})()
        
        # Test company object
        self.assertFalse(permission.has_object_permission(request, None, self.company2))
        self.assertTrue(permission.has_object_permission(request, None, self.company1))
        
        # Test related object
        self.assertFalse(permission.has_object_permission(request, None, self.bank2))
        self.assertTrue(permission.has_object_permission(request, None, self.bank1))
    
    def test_view_company_isolation(self):
        """Test that views properly isolate company data"""
        # User1 should only see their company data
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(reverse('companies:detail'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.company1.id))
        self.assertEqual(response.data['name'], 'Company 1')
        
        # User2 should see their own company
        self.client.force_authenticate(user=self.user2)
        
        response = self.client.get(reverse('companies:detail'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.company2.id))
        self.assertEqual(response.data['name'], 'Company 2')
    
    def test_usage_limits_isolation(self):
        """Test that usage limits are properly isolated by company"""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(reverse('companies:usage-limits'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify bank account count is isolated
        self.assertEqual(response.data['bank_accounts']['used'], 1)  # Only company1's bank
    
    def test_staff_user_access(self):
        """Test that staff users can access any company data"""
        self.client.force_authenticate(user=self.staff_user)
        
        permission = IsCompanyOwnerOrStaff()
        request = type('Request', (), {'user': self.staff_user})()
        
        # Staff should access both companies
        self.assertTrue(permission.has_object_permission(request, None, self.company1))
        self.assertTrue(permission.has_object_permission(request, None, self.company2))


class AtomicUsageTrackingTestCase(TransactionTestCase):
    """Test atomic usage tracking to prevent race conditions"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company'
        )
    
    def test_increment_usage_is_atomic(self):
        """Test that increment_usage prevents race conditions"""
        initial_transactions = self.company.current_month_transactions
        
        def increment_transactions():
            # Reload company to simulate separate request
            company = Company.objects.get(pk=self.company.pk)
            company.increment_usage('transactions')
        
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
        self.company.refresh_from_db()
        expected_count = initial_transactions + num_threads
        self.assertEqual(self.company.current_month_transactions, expected_count)
        
        # Verify ResourceUsage is also updated
        usage = ResourceUsage.get_or_create_current_month(self.company)
        self.assertEqual(usage.transactions_count, expected_count)
    
    def test_reset_usage_is_atomic(self):
        """Test that reset_monthly_usage is atomic"""
        # Set some initial values
        self.company.current_month_transactions = 100
        self.company.current_month_ai_requests = 50
        self.company.save()
        
        # Reset usage
        self.company.reset_monthly_usage()
        
        # Verify both counters are reset
        self.assertEqual(self.company.current_month_transactions, 0)
        self.assertEqual(self.company.current_month_ai_requests, 0)


class CompanyValidationMixinTestCase(APITestCase):
    """Test CompanyValidationMixin functionality"""
    
    def setUp(self):
        self.user_without_company = User.objects.create_user(
            email='nocompany@test.com',
            password='testpass123'
        )
        self.user_with_company = User.objects.create_user(
            email='withcompany@test.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            owner=self.user_with_company,
            name='Test Company'
        )
    
    def test_user_without_company_gets_404(self):
        """Test that users without companies get proper error"""
        self.client.force_authenticate(user=self.user_without_company)
        
        response = self.client.get(reverse('companies:detail'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Company not found')
    
    def test_user_with_company_gets_data(self):
        """Test that users with companies can access their data"""
        self.client.force_authenticate(user=self.user_with_company)
        
        response = self.client.get(reverse('companies:detail'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Company')


class SubscriptionConsolidationTestCase(TestCase):
    """Test subscription model consolidation"""
    
    def test_company_subscription_properties(self):
        """Test that Company properties proxy to Subscription correctly"""
        user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        company = Company.objects.create(
            owner=user,
            name='Test Company'
        )
        
        # Verify subscription was created automatically
        self.assertIsNotNone(company.subscription)
        self.assertEqual(company.subscription_status, 'trial')
        self.assertEqual(company.billing_cycle, 'monthly')
        self.assertIsNotNone(company.trial_ends_at)
        
        # Test trial active
        self.assertTrue(company.is_trial_active)
        self.assertGreater(company.days_until_trial_ends, 0)