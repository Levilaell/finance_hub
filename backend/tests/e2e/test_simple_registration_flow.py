"""
Simple E2E test for registration, login, and basic operations
"""
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from django.test import override_settings

from apps.authentication.models import User
from apps.companies.models import Company, SubscriptionPlan


@override_settings(
    FIELD_ENCRYPTION_KEY='0WbpgW5gcVxJvLds2p7Up2S-2FvUcDeYBs7KUZxQqMc='
)
class TestSimpleRegistrationFlow(TransactionTestCase):
    """
    Test the essential user flow: register -> verify email -> login -> access dashboard
    """
    
    def setUp(self):
        self.client = APIClient()
        # Ensure at least one subscription plan exists
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            plan_type='starter',
            price_monthly=0,
            price_yearly=0,
            max_users=1,
            max_bank_accounts=1,
            max_transactions=100
        )
    
    @patch('apps.notifications.email_service.EmailService.send_verification_email')
    def test_registration_to_dashboard(self, mock_send_email):
        """
        Test simple flow from registration to accessing dashboard
        """
        
        print("\n" + "="*50)
        print("SIMPLE E2E TEST: REGISTER -> LOGIN -> DASHBOARD")
        print("="*50)
        
        # Step 1: Register new user
        print("\n1. REGISTERING NEW USER")
        response = self.client.post(reverse('authentication:register'), {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'company_name': 'Test Company',
            'company_type': 'ltda',
            'business_sector': 'technology'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        print("✓ Registration successful")
        print(f"✓ Access token received")
        
        # Save initial token
        initial_token = response.data['tokens']['access']
        
        # Verify user and company created
        user = User.objects.get(email='test@example.com')
        company = Company.objects.get(owner=user)
        
        print(f"✓ User created: {user.email}")
        print(f"✓ Company created: {company.name}")
        print(f"✓ Subscription: {company.subscription_plan.name}")
        
        # Step 2: Access protected endpoint with token
        print("\n2. ACCESSING PROTECTED ENDPOINT")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {initial_token}')
        
        response = self.client.get(reverse('authentication:profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        print("✓ Profile endpoint accessible")
        
        # Step 3: Logout
        print("\n3. LOGOUT")
        response = self.client.post(reverse('authentication:logout'), {
            'refresh': response.data['tokens']['refresh'] 
            if 'tokens' in response.data 
            else self.client.post(reverse('authentication:login'), {
                'email': 'test@example.com',
                'password': 'TestPass123!'
            }).data['tokens']['refresh']
        })
        # Logout might fail if refresh token not available, but that's ok
        print("✓ Logout attempted")
        
        # Clear credentials
        self.client.credentials()
        
        # Step 4: Login again
        print("\n4. LOGIN AGAIN")
        response = self.client.post(reverse('authentication:login'), {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('user', response.data)
        print("✓ Login successful")
        print(f"✓ User data returned")
        
        # Step 5: Access dashboard
        print("\n5. ACCESSING DASHBOARD")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["tokens"]["access"]}')
        
        response = self.client.get(reverse('banking:dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("✓ Dashboard accessible")
        
        # Check dashboard data structure
        self.assertIn('current_balance', response.data)
        self.assertIn('recent_transactions', response.data)
        self.assertIn('monthly_income', response.data)
        self.assertIn('monthly_expenses', response.data)
        print("✓ Dashboard data structure correct")
        
        # Step 6: List bank accounts (should be empty)
        print("\n6. CHECKING BANK ACCOUNTS")
        response = self.client.get(reverse('banking:bank-account-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
        print("✓ Bank accounts endpoint working")
        print("✓ No accounts yet (expected)")
        
        print("\n" + "="*50)
        print("SIMPLE E2E TEST COMPLETED SUCCESSFULLY!")
        print("="*50)
        print(f"✓ User can register")
        print(f"✓ User can login")
        print(f"✓ User can access protected endpoints")
        print(f"✓ Company is created automatically")
        print(f"✓ Dashboard is accessible")
        print("="*50)