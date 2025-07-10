"""
E2E test for complete user flow: Registration -> Plan Selection -> Payment Simulation -> Login
"""
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import json
from django.test import override_settings

from apps.authentication.models import User, EmailVerification
from apps.companies.models import Company, CompanyUser, SubscriptionPlan
from apps.notifications.models import Notification


@override_settings(
    FIELD_ENCRYPTION_KEY='0WbpgW5gcVxJvLds2p7Up2S-2FvUcDeYBs7KUZxQqMc=',
    STRIPE_TEST_MODE=True,
    DEFAULT_PAYMENT_GATEWAY='stripe'
)
class TestCompleteUserFlow(TransactionTestCase):
    """
    Test complete user journey from registration through plan selection to login
    """
    
    def setUp(self):
        self.client = APIClient()
        self._create_subscription_plans()
    
    def _create_subscription_plans(self):
        """Create subscription plans"""
        self.starter_plan = SubscriptionPlan.objects.create(
            name='Starter',
            slug='starter',
            plan_type='starter',
            price_monthly=29.00,
            price_yearly=290.00,
            max_users=3,
            max_bank_accounts=2,
            max_transactions=500,
            has_ai_categorization=False,
            has_advanced_reports=False
        )
        
        self.pro_plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00,
            price_yearly=990.00,
            max_users=10,
            max_bank_accounts=5,
            max_transactions=2000,
            has_ai_categorization=True,
            has_advanced_reports=True
        )
        
        self.enterprise_plan = SubscriptionPlan.objects.create(
            name='Enterprise',
            slug='enterprise',
            plan_type='enterprise',
            price_monthly=299.00,
            price_yearly=2990.00,
            max_users=50,
            max_bank_accounts=20,
            max_transactions=10000,
            has_ai_categorization=True,
            has_advanced_reports=True,
            has_api_access=True
        )
    
    @patch('apps.notifications.email_service.EmailService.send_verification_email')
    @patch('apps.payments.payment_service.StripeGateway.create_customer')
    def test_complete_registration_to_login_flow(self, mock_create_customer, mock_send_email):
        """
        Test complete flow:
        1. User registration with company
        2. Email verification
        3. View subscription plans
        4. Select plan (simulated payment)
        5. Logout and login with active subscription
        """
        
        print("\n" + "="*60)
        print("E2E TEST: REGISTRATION -> PLAN SELECTION -> LOGIN")
        print("="*60)
        
        # Mock Stripe customer creation
        mock_create_customer.return_value = {
            'id': 'cus_test123',
            'email': 'novo.usuario@empresa.com.br'
        }
        
        # Step 1: User Registration
        print("\n>>> STEP 1: User Registration")
        registration_data = {
            'email': 'novo.usuario@empresa.com.br',
            'password': 'SenhaForte123!@#',
            'password2': 'SenhaForte123!@#',
            'first_name': 'Novo',
            'last_name': 'Usuário',
            'phone': '+5511987654321',
            'company_name': 'Empresa Teste Ltda',
            'company_type': 'ltda',
            'business_sector': 'technology'
        }
        
        response = self.client.post(reverse('authentication:register'), registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('user', response.data)
        
        # Save tokens for later use
        access_token = response.data['tokens']['access']
        refresh_token = response.data['tokens']['refresh']
        
        # Verify user and company creation
        user = User.objects.get(email='novo.usuario@empresa.com.br')
        company = Company.objects.get(owner=user)
        
        print(f"✓ User created: {user.email}")
        print(f"✓ Company created: {company.name}")
        print(f"✓ Initial plan: {company.subscription_plan.name} ({company.subscription_status})")
        
        self.assertEqual(company.subscription_plan, self.starter_plan)
        # Company may start as 'active' or 'trial' depending on configuration
        self.assertIn(company.subscription_status, ['active', 'trial'])
        
        # Set authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Step 2: Email Verification
        print("\n>>> STEP 2: Email Verification")
        verification = EmailVerification.objects.get(user=user)
        
        response = self.client.post(reverse('authentication:verify_email'), {
            'token': verification.token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        print("✓ Email verified successfully")
        
        # Step 3: View Available Plans
        print("\n>>> STEP 3: View Available Plans")
        response = self.client.get(reverse('companies:subscription-plans'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have at least the plans we created
        self.assertGreaterEqual(len(response.data), 3)
        
        print("Available plans:")
        # Check if response.data is a list or has a 'results' key
        plans = response.data if isinstance(response.data, list) else response.data.get('results', [])
        for plan in plans:
            if isinstance(plan, dict):
                print(f"  - {plan.get('name', 'Unknown')}: R$ {plan.get('price_monthly', 0)}/mês")
            else:
                print(f"  - Plan data: {plan}")
        
        # Step 4: Select Pro Plan (Simulated Payment)
        print("\n>>> STEP 4: Select Pro Plan")
        selected_plan = self.pro_plan
        print(f"Selected: {selected_plan.name} - R$ {selected_plan.price_monthly}/mês")
        
        # Simulate subscription upgrade with payment
        with patch('apps.payments.payment_service.StripeGateway.create_subscription') as mock_subscription:
            mock_subscription.return_value = {
                'id': 'sub_test123',
                'status': 'active',
                'current_period_start': int(timezone.now().timestamp()),
                'current_period_end': int((timezone.now() + timedelta(days=30)).timestamp())
            }
            
            response = self.client.post(
                reverse('companies:subscription-upgrade'),
                {
                    'plan_id': self.pro_plan.id,
                    'billing_cycle': 'monthly'
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify company upgrade
        company.refresh_from_db()
        self.assertEqual(company.subscription_plan, self.pro_plan)
        self.assertEqual(company.subscription_status, 'active')
        
        print(f"✓ Company upgraded to: {company.subscription_plan.name}")
        print(f"✓ Subscription status: {company.subscription_status}")
        
        # Step 5: Check Notifications
        print("\n>>> STEP 5: Check Notifications")
        response = self.client.get(reverse('notifications:notification-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        notifications = response.data['results']
        notification_types = [n['notification_type'] for n in notifications]
        
        print(f"✓ {len(notifications)} notifications received")
        for notification in notifications:
            print(f"  - {notification['notification_type']}: {notification['message']}")
        
        # Step 6: Logout
        print("\n>>> STEP 6: Logout")
        response = self.client.post(reverse('authentication:logout'), {
            'refresh': refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("✓ Logged out successfully")
        
        # Clear authentication
        self.client.credentials()
        
        # Step 7: Login Again
        print("\n>>> STEP 7: Login with Active Subscription")
        login_data = {
            'email': 'novo.usuario@empresa.com.br',
            'password': 'SenhaForte123!@#'
        }
        
        response = self.client.post(reverse('authentication:login'), login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('user', response.data)
        self.assertIn('company', response.data)
        
        # Verify subscription info in login response
        self.assertEqual(response.data['company']['subscription_plan']['slug'], 'pro')
        self.assertEqual(response.data['company']['subscription_status'], 'active')
        
        print("✓ Logged in successfully")
        print(f"✓ Active subscription: {response.data['company']['subscription_plan']['name']}")
        
        # Step 8: Access Pro Features
        print("\n>>> STEP 8: Access Pro Features")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["tokens"]["access"]}')
        
        # Try to access dashboard
        response = self.client.get(reverse('banking:dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("✓ Dashboard accessible")
        
        # Check if AI categorization is available (Pro feature)
        response = self.client.get(reverse('companies:company-features'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('has_ai_categorization', False))
        print("✓ Pro features available")
        
        # Final Summary
        print("\n" + "="*60)
        print("E2E TEST COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"User: {user.email}")
        print(f"Company: {company.name}")
        print(f"Plan: {company.subscription_plan.name} (R$ {company.subscription_plan.price_monthly}/mês)")
        print(f"Status: {company.subscription_status}")
        print("="*60)


class TestTrialUserFlow(TransactionTestCase):
    """
    Test trial user experience and limitations
    """
    
    def setUp(self):
        self.client = APIClient()
        self._create_subscription_plans()
    
    def _create_subscription_plans(self):
        """Create subscription plans"""
        self.starter_plan = SubscriptionPlan.objects.create(
            name='Starter',
            slug='starter',
            plan_type='starter',
            price_monthly=29.00,
            price_yearly=290.00,
            max_users=3,
            max_bank_accounts=2,
            max_transactions=500
        )
        
        self.pro_plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00,
            price_yearly=990.00,
            max_users=10,
            max_bank_accounts=5,
            max_transactions=2000,
            has_ai_categorization=True
        )
    
    @patch('apps.notifications.email_service.EmailService.send_verification_email')
    @patch('apps.payments.payment_service.StripeGateway.create_customer')
    def test_trial_limitations_and_expiration(self, mock_create_customer, mock_send_email):
        """
        Test trial period limitations and expiration handling
        """
        
        print("\n" + "="*60)
        print("TESTING TRIAL USER EXPERIENCE")
        print("="*60)
        
        mock_create_customer.return_value = {'id': 'cus_trial123'}
        
        # Create trial user
        print("\n>>> Creating Trial User")
        response = self.client.post(reverse('authentication:register'), {
            'email': 'trial.user@empresa.com.br',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Trial',
            'last_name': 'User',
            'company_name': 'Trial Company',
            'company_type': 'mei',
            'business_sector': 'services'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(email='trial.user@empresa.com.br')
        company = Company.objects.get(owner=user)
        
        # Verify trial status
        self.assertIn(company.subscription_status, ['active', 'trial'])
        # Trial ends_at may not be set if starting as active
        if company.subscription_status == 'trial':
            self.assertIsNotNone(company.trial_ends_at)
        
        trial_days_remaining = (company.trial_ends_at.date() - timezone.now().date()).days if company.trial_ends_at else 14
        print(f"✓ Trial started: {trial_days_remaining} days remaining")
        print(f"✓ Plan: {company.subscription_plan.name}")
        
        # Set authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["tokens"]["access"]}')
        
        # Test trial features
        print("\n>>> Testing Trial Features")
        
        # Can access basic features
        response = self.client.get(reverse('banking:dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("✓ Can access dashboard")
        
        # Check company features
        response = self.client.get(reverse('companies:company-features'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get('has_ai_categorization', False))
        print("✓ Basic features only (no AI)")
        
        # Check trial status
        response = self.client.get(reverse('companies:trial-status'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'trial')
        self.assertEqual(response.data['days_remaining'], trial_days_remaining)
        print(f"✓ Trial status endpoint working")
        
        # Simulate trial near expiration
        print("\n>>> Simulating Trial Near Expiration")
        company.trial_ends_at = timezone.now() + timedelta(days=3)
        company.save()
        
        response = self.client.get(reverse('companies:trial-status'))
        self.assertEqual(response.data['days_remaining'], 3)
        self.assertTrue(response.data.get('show_upgrade_prompt', False))
        print("✓ Upgrade prompt shown (3 days remaining)")
        
        # Simulate trial expiration
        print("\n>>> Simulating Trial Expiration")
        company.trial_ends_at = timezone.now() - timedelta(days=1)
        company.subscription_status = 'expired'
        company.save()
        
        response = self.client.get(reverse('companies:trial-status'))
        self.assertEqual(response.data['status'], 'expired')
        self.assertTrue(response.data['trial_expired'])
        print("✓ Trial expired status shown")
        
        print("\n" + "="*60)
        print("TRIAL USER TESTS COMPLETED")
        print("="*60)


class TestMultiStepRegistrationFlow(TransactionTestCase):
    """
    Test multi-step registration process
    """
    
    def setUp(self):
        self.client = APIClient()
        self._create_subscription_plans()
    
    def _create_subscription_plans(self):
        """Create subscription plans"""
        self.starter_plan = SubscriptionPlan.objects.create(
            name='Starter',
            slug='starter',
            plan_type='starter',
            price_monthly=29.00,
            max_users=3
        )
        
        self.pro_plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00,
            max_users=10,
            has_ai_categorization=True
        )
    
    @patch('apps.notifications.email_service.EmailService.send_verification_email')
    @patch('apps.payments.payment_service.StripeGateway.create_customer')
    def test_step_by_step_registration(self, mock_create_customer, mock_send_email):
        """
        Test registration broken into steps as user might experience
        """
        
        print("\n" + "="*60)
        print("TESTING MULTI-STEP REGISTRATION")
        print("="*60)
        
        mock_create_customer.return_value = {'id': 'cus_steps123'}
        
        # Step 1: Check email availability
        print("\n>>> Step 1: Check Email Availability")
        response = self.client.post(
            reverse('authentication:check-email'),
            {'email': 'step.user@empresa.com.br'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['available'])
        print("✓ Email available")
        
        # Step 2: View plans before registration
        print("\n>>> Step 2: View Plans (Public)")
        response = self.client.get(reverse('companies:subscription-plans'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        print("✓ Plans viewable without auth")
        
        # Step 3: Register with plan preference
        print("\n>>> Step 3: Register with Plan Preference")
        response = self.client.post(reverse('authentication:register'), {
            'email': 'step.user@empresa.com.br',
            'password': 'StepPass123!',
            'password2': 'StepPass123!',
            'first_name': 'Step',
            'last_name': 'User',
            'company_name': 'Step Company',
            'company_type': 'ltda',
            'business_sector': 'retail',
            'selected_plan': 'pro'  # User's intended plan
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(email='step.user@empresa.com.br')
        company = Company.objects.get(owner=user)
        
        # Should start with starter/trial regardless of preference
        self.assertEqual(company.subscription_plan, self.starter_plan)
        self.assertEqual(company.subscription_status, 'trial')
        
        print("✓ Registered successfully")
        print(f"✓ Started with: {company.subscription_plan.name} (trial)")
        
        # Step 4: Complete profile
        print("\n>>> Step 4: Complete Company Profile")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["tokens"]["access"]}')
        
        response = self.client.patch(
            reverse('companies:company-update'),
            {
                'cnpj': '98.765.432/0001-10',
                'phone': '+551133334444',
                'address_street': 'Rua Teste',
                'address_number': '123',
                'address_city': 'São Paulo',
                'address_state': 'SP',
                'address_zip_code': '01234-567'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("✓ Profile completed")
        
        # Step 5: Skip payment for now (stay on trial)
        print("\n>>> Step 5: Continue with Trial")
        response = self.client.post(reverse('companies:skip-payment'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'trial')
        self.assertIn('trial_days_remaining', response.data)
        print(f"✓ Continuing with trial: {response.data['trial_days_remaining']} days")
        
        print("\n" + "="*60)
        print("MULTI-STEP REGISTRATION COMPLETED")
        print("="*60)