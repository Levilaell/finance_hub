"""
Authentication views tests
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.companies.models import Company, SubscriptionPlan

User = get_user_model()


class AuthenticationTestCase(APITestCase):
    """Base test case for authentication tests"""
    
    def setUp(self):
        # Create test subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            plan_type='starter',
            price_monthly=29.90,
            price_yearly=299.00,
            max_transactions=500,
            max_bank_accounts=1,
            max_users=1
        )


class RegistrationTestCase(AuthenticationTestCase):
    """Test user registration"""
    
    def test_registration_success(self):
        """Test successful user registration"""
        url = reverse('authentication:register')
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '11999999999',
            'company_name': 'Test Company',
            'company_type': 'mei',
            'business_sector': 'services'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('user', response.data)
        
        # Check user was created
        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.first_name, 'Test')
        
        # Check company was created
        company = Company.objects.get(owner=user)
        self.assertEqual(company.name, 'Test Company')
        self.assertEqual(company.subscription_plan, self.plan)
    
    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        url = reverse('authentication:register')
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'password2': 'DifferentPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'company_name': 'Test Company',
            'company_type': 'mei',
            'business_sector': 'services'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_registration_duplicate_email(self):
        """Test registration with existing email"""
        # Create existing user
        User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='ExistingPass123!'
        )
        
        url = reverse('authentication:register')
        data = {
            'email': 'existing@example.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'company_name': 'Test Company',
            'company_type': 'mei',
            'business_sector': 'services'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTestCase(AuthenticationTestCase):
    """Test user login"""
    
    def setUp(self):
        super().setUp()
        # Create test user
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        # Create company for user
        Company.objects.create(
            owner=self.user,
            name='Test Company',
            company_type='mei',
            business_sector='services',
            subscription_plan=self.plan
        )
    
    def test_login_success(self):
        """Test successful login"""
        url = reverse('authentication:login')
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertIn('user', response.data)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        url = reverse('authentication:login')
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_inactive_user(self):
        """Test login with inactive user"""
        self.user.is_active = False
        self.user.save()
        
        url = reverse('authentication:login')
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileTestCase(AuthenticationTestCase):
    """Test user profile operations"""
    
    def setUp(self):
        super().setUp()
        # Create test user
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        # Create company
        Company.objects.create(
            owner=self.user,
            name='Test Company',
            company_type='mei',
            business_sector='services',
            subscription_plan=self.plan
        )
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    def test_get_profile(self):
        """Test getting user profile"""
        url = reverse('authentication:profile')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
    
    def test_update_profile(self):
        """Test updating user profile"""
        url = reverse('authentication:profile')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '11888888888'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        
        # Verify in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.phone, '11888888888')
    
    def test_change_password(self):
        """Test changing password"""
        url = reverse('authentication:change_password')
        data = {
            'old_password': 'TestPass123!',
            'new_password': 'NewTestPass123!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify new password works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewTestPass123!'))
    
    def test_change_password_wrong_old(self):
        """Test changing password with wrong old password"""
        url = reverse('authentication:change_password')
        data = {
            'old_password': 'WrongOldPass!',
            'new_password': 'NewTestPass123!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TokenRefreshTestCase(AuthenticationTestCase):
    """Test token refresh"""
    
    def setUp(self):
        super().setUp()
        # Create and login user
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPass123!'
        )
        
        # Get tokens
        login_url = reverse('authentication:login')
        response = self.client.post(login_url, {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }, format='json')
        
        self.refresh_token = response.data['tokens']['refresh']
    
    def test_token_refresh(self):
        """Test refreshing access token"""
        url = reverse('authentication:token_refresh')
        data = {'refresh': self.refresh_token}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)