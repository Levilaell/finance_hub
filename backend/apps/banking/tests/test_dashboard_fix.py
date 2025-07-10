"""
Quick test to verify the dashboard enhanced endpoint is working
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from apps.authentication.models import User
from apps.companies.models import Company, CompanyUser, SubscriptionPlan


class TestDashboardEnhancedFix(APITestCase):
    """Test that the dashboard enhanced endpoint is working correctly"""
    
    def setUp(self):
        """Set up test data"""
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            plan_type='starter',
            price_monthly=0,
            price_yearly=0
        )
        
        # Create user and company
        self.user = User.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='TestPass123!'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user,
            subscription_plan=self.plan,
            subscription_status='active'
        )
        
        CompanyUser.objects.create(
            user=self.user,
            company=self.company,
            role='owner'
        )
        
        # Set company on user
        self.user.company = self.company
        self.user.save()
    
    def test_dashboard_enhanced_endpoint_works(self):
        """Test that the enhanced dashboard endpoint returns 200 OK"""
        # Authenticate
        self.client.force_authenticate(user=self.user)
        
        # Make request
        response = self.client.get('/api/banking/dashboard/enhanced/')
        
        # Should NOT return 500 error
        self.assertNotEqual(response.status_code, 500)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check basic response structure
        self.assertIsInstance(response.data, dict)
        self.assertIn('current_balance', response.data)
        
        print(f"\n✅ Dashboard Enhanced endpoint is working!")
        print(f"   Status: {response.status_code}")
        print(f"   Has current_balance: {response.data.get('current_balance', 0)}")
        print(f"   Response keys: {list(response.data.keys())[:5]}...")
    
    def test_dashboard_enhanced_with_login(self):
        """Test dashboard after normal login flow"""
        # Login
        login_response = self.client.post(reverse('authentication:login'), {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        token = login_response.data['tokens']['access']
        
        # Use token for authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Access dashboard
        response = self.client.get('/api/banking/dashboard/enhanced/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"\n✅ Dashboard works after login!")
        print(f"   Authenticated as: {self.user.email}")
        print(f"   Company: {self.company.name}")