"""
E2E test for complete user flow: Registration -> Plan Selection -> Payment -> Login
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
    STRIPE_TEST_MODE=True
)
class TestUserRegistrationPaymentFlow(TransactionTestCase):
    """
    Test complete user journey from registration through payment to login
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
            has_advanced_reports=False,
            stripe_price_id_monthly='price_starter_monthly',
            stripe_price_id_yearly='price_starter_yearly'
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
            has_advanced_reports=True,
            stripe_price_id_monthly='price_pro_monthly',
            stripe_price_id_yearly='price_pro_yearly'
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
            has_api_access=True,
            has_white_label=True,
            stripe_price_id_monthly='price_enterprise_monthly',
            stripe_price_id_yearly='price_enterprise_yearly'
        )
    
    @patch('apps.notifications.email_service.EmailService.send_verification_email')
    @patch('apps.payments.payment_service.StripeGateway.create_customer')
    @patch('apps.payments.payment_service.StripeGateway.create_payment_method')
    @patch('apps.payments.payment_service.StripeGateway.attach_payment_method')
    @patch('apps.payments.payment_service.StripeGateway.create_subscription')
    @patch('apps.payments.payment_service.StripeGateway.confirm_payment_intent')
    def test_complete_registration_payment_flow(
        self,
        mock_confirm_payment,
        mock_create_subscription,
        mock_attach_payment,
        mock_create_payment_method,
        mock_create_customer,
        mock_send_email
    ):
        """
        Test complete flow:
        1. User registration with company
        2. Email verification
        3. Plan selection
        4. Payment method setup
        5. Subscription creation
        6. Payment confirmation
        7. Login with active subscription
        """
        
        print("\n" + "="*60)
        print("STARTING E2E TEST: REGISTRATION -> PAYMENT -> LOGIN")
        print("="*60)
        
        # Mock Stripe responses
        mock_create_customer.return_value = {
            'id': 'cus_test123',
            'email': 'novo.usuario@empresa.com.br'
        }
        
        mock_create_payment_method.return_value = {
            'id': 'pm_test123',
            'type': 'card',
            'card': {
                'brand': 'visa',
                'last4': '4242',
                'exp_month': 12,
                'exp_year': 2025
            }
        }
        
        mock_attach_payment.return_value = {
            'id': 'pm_test123',
            'customer': 'cus_test123'
        }
        
        mock_create_subscription.return_value = {
            'id': 'sub_test123',
            'status': 'active',
            'current_period_start': int(timezone.now().timestamp()),
            'current_period_end': int((timezone.now() + timedelta(days=30)).timestamp()),
            'latest_invoice': {
                'payment_intent': 'pi_test123',
                'status': 'paid'
            }
        }
        
        mock_confirm_payment.return_value = {
            'id': 'pi_test123',
            'status': 'succeeded',
            'amount': 9900,  # R$ 99,00 in cents
            'currency': 'brl'
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
        self.assertIn('company', response.data)
        
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
        self.assertEqual(company.subscription_status, 'trial')
        self.assertEqual(company.stripe_customer_id, 'cus_test123')
        
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
        self.assertEqual(len(response.data), 3)
        
        print("Available plans:")
        for plan in response.data:
            print(f"  - {plan['name']}: R$ {plan['price_monthly']}/mês")
        
        # Step 4: Select Pro Plan
        print("\n>>> STEP 4: Select Pro Plan")
        selected_plan = self.pro_plan
        print(f"Selected: {selected_plan.name} - R$ {selected_plan.price_monthly}/mês")
        
        # Step 5: Setup Payment Method
        print("\n>>> STEP 5: Setup Payment Method")
        payment_method_data = {
            'type': 'card',
            'card_number': '4242424242424242',
            'exp_month': 12,
            'exp_year': 2025,
            'cvc': '123',
            'billing_details': {
                'name': 'Novo Usuário',
                'email': 'novo.usuario@empresa.com.br',
                'phone': '+5511987654321',
                'address': {
                    'line1': 'Rua Teste, 123',
                    'city': 'São Paulo',
                    'state': 'SP',
                    'postal_code': '01234-567',
                    'country': 'BR'
                }
            }
        }
        
        response = self.client.post(
            reverse('payments:payment-method-create'),
            payment_method_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        payment_method = PaymentMethod.objects.get(user=user)
        self.assertEqual(payment_method.stripe_payment_method_id, 'pm_test123')
        self.assertTrue(payment_method.is_default)
        print("✓ Payment method created and attached")
        
        # Step 6: Create Subscription
        print("\n>>> STEP 6: Create Subscription")
        subscription_data = {
            'plan_slug': 'pro',
            'payment_method_id': payment_method.id,
            'billing_cycle': 'monthly'
        }
        
        response = self.client.post(
            reverse('companies:subscription-create'),
            subscription_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify subscription creation
        subscription = Subscription.objects.get(company=company)
        self.assertEqual(subscription.plan, self.pro_plan)
        self.assertEqual(subscription.status, 'active')
        self.assertEqual(subscription.stripe_subscription_id, 'sub_test123')
        
        # Verify company upgrade
        company.refresh_from_db()
        self.assertEqual(company.subscription_plan, self.pro_plan)
        self.assertEqual(company.subscription_status, 'active')
        
        print(f"✓ Subscription created: {subscription.plan.name}")
        print(f"✓ Company upgraded to: {company.subscription_plan.name}")
        
        # Step 7: Verify Payment
        print("\n>>> STEP 7: Verify Payment")
        payment = Payment.objects.get(subscription=subscription)
        self.assertEqual(payment.amount, Decimal('99.00'))
        self.assertEqual(payment.status, 'completed')
        self.assertEqual(payment.payment_method, payment_method)
        print(f"✓ Payment confirmed: R$ {payment.amount}")
        
        # Step 8: Check Notifications
        print("\n>>> STEP 8: Check Notifications")
        response = self.client.get(reverse('notifications:notification-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        notifications = response.data['results']
        notification_types = [n['notification_type'] for n in notifications]
        
        # Should have notifications for: welcome, email_verified, subscription_created, payment_received
        self.assertIn('welcome', notification_types)
        self.assertIn('email_verified', notification_types)
        self.assertIn('subscription_created', notification_types)
        self.assertIn('payment_received', notification_types)
        
        print(f"✓ {len(notifications)} notifications received")
        
        # Step 9: Logout
        print("\n>>> STEP 9: Logout")
        response = self.client.post(reverse('authentication:logout'), {
            'refresh': refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("✓ Logged out successfully")
        
        # Clear authentication
        self.client.credentials()
        
        # Step 10: Login Again
        print("\n>>> STEP 10: Login with Active Subscription")
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
        
        # Step 11: Access Pro Features
        print("\n>>> STEP 11: Access Pro Features")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["tokens"]["access"]}')
        
        # Try to access a Pro feature (AI categorization)
        response = self.client.get(reverse('categories:ai-suggestions'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("✓ Pro features accessible")
        
        # Final Summary
        print("\n" + "="*60)
        print("E2E TEST COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"User: {user.email}")
        print(f"Company: {company.name}")
        print(f"Plan: {company.subscription_plan.name} (R$ {company.subscription_plan.price_monthly}/mês)")
        print(f"Status: {company.subscription_status}")
        print(f"Payment Method: •••• 4242")
        print("="*60)


class TestTrialToPaymentConversion(TransactionTestCase):
    """
    Test trial user converting to paid subscription
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
            trial_days=14,
            stripe_price_id_monthly='price_starter_monthly'
        )
        
        self.pro_plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00,
            price_yearly=990.00,
            trial_days=14,
            stripe_price_id_monthly='price_pro_monthly'
        )
    
    @patch('apps.notifications.email_service.EmailService.send_verification_email')
    @patch('apps.payments.payment_service.StripeGateway.create_customer')
    def test_trial_expiration_and_conversion(self, mock_create_customer, mock_send_email):
        """
        Test trial period expiration and conversion to paid plan
        """
        
        print("\n" + "="*60)
        print("TESTING TRIAL TO PAID CONVERSION")
        print("="*60)
        
        mock_create_customer.return_value = {'id': 'cus_trial123'}
        
        # Create user in trial
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
        self.assertEqual(company.subscription_status, 'trial')
        self.assertIsNotNone(company.trial_ends_at)
        
        trial_days_remaining = (company.trial_ends_at - timezone.now().date()).days
        print(f"✓ Trial started: {trial_days_remaining} days remaining")
        
        # Set authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["tokens"]["access"]}')
        
        # Check trial status endpoint
        response = self.client.get(reverse('companies:trial-status'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'trial')
        self.assertEqual(response.data['days_remaining'], trial_days_remaining)
        
        # Simulate trial near expiration
        print("\n>>> Simulating Trial Near Expiration")
        company.trial_ends_at = timezone.now().date() + timedelta(days=3)
        company.save()
        
        response = self.client.get(reverse('companies:trial-status'))
        self.assertEqual(response.data['days_remaining'], 3)
        self.assertTrue(response.data['show_upgrade_prompt'])
        print("✓ Upgrade prompt shown (3 days remaining)")
        
        # Convert to paid plan
        print("\n>>> Converting to Paid Plan")
        with patch('apps.payments.payment_service.StripeGateway.create_payment_method') as mock_pm, \
             patch('apps.payments.payment_service.StripeGateway.attach_payment_method') as mock_attach, \
             patch('apps.payments.payment_service.StripeGateway.create_subscription') as mock_sub:
            
            mock_pm.return_value = {'id': 'pm_trial123'}
            mock_attach.return_value = {'id': 'pm_trial123'}
            mock_sub.return_value = {
                'id': 'sub_trial123',
                'status': 'active',
                'current_period_end': int((timezone.now() + timedelta(days=30)).timestamp())
            }
            
            # Create payment method
            response = self.client.post(reverse('payments:payment-method-create'), {
                'type': 'card',
                'card_number': '5555555555554444',
                'exp_month': 12,
                'exp_year': 2025,
                'cvc': '123'
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            payment_method = PaymentMethod.objects.get(user=user)
            
            # Create subscription
            response = self.client.post(reverse('companies:subscription-create'), {
                'plan_slug': 'pro',
                'payment_method_id': payment_method.id,
                'billing_cycle': 'monthly'
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify conversion
        company.refresh_from_db()
        self.assertEqual(company.subscription_plan.slug, 'pro')
        self.assertEqual(company.subscription_status, 'active')
        self.assertIsNone(company.trial_ends_at)
        
        print("✓ Successfully converted to Pro plan")
        print(f"✓ New status: {company.subscription_status}")
        print("="*60)


class TestPaymentFailureAndRetry(TransactionTestCase):
    """
    Test payment failure scenarios and retry logic
    """
    
    def setUp(self):
        self.client = APIClient()
        self._create_test_data()
    
    def _create_test_data(self):
        """Create test data"""
        self.plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00,
            stripe_price_id_monthly='price_pro_monthly'
        )
        
        # Create user with company
        self.user = User.objects.create_user(
            email='payment.test@empresa.com.br',
            password='TestPass123!',
            first_name='Payment',
            last_name='Test'
        )
        
        self.company = Company.objects.create(
            name='Payment Test Company',
            owner=self.user,
            subscription_plan=self.plan,
            subscription_status='trial',
            stripe_customer_id='cus_payment_test'
        )
        
        CompanyUser.objects.create(
            user=self.user,
            company=self.company,
            role='owner'
        )
    
    @patch('apps.payments.payment_service.StripeGateway.create_payment_method')
    @patch('apps.payments.payment_service.StripeGateway.attach_payment_method')
    @patch('apps.payments.payment_service.StripeGateway.create_subscription')
    def test_payment_failure_and_retry(self, mock_create_sub, mock_attach, mock_create_pm):
        """
        Test payment failure handling and retry mechanism
        """
        
        print("\n" + "="*60)
        print("TESTING PAYMENT FAILURE AND RETRY")
        print("="*60)
        
        # Login
        response = self.client.post(reverse('authentication:login'), {
            'email': 'payment.test@empresa.com.br',
            'password': 'TestPass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["tokens"]["access"]}')
        
        # Mock successful payment method creation
        mock_create_pm.return_value = {'id': 'pm_fail123'}
        mock_attach.return_value = {'id': 'pm_fail123'}
        
        # First attempt - payment fails
        print("\n>>> First Payment Attempt (Will Fail)")
        mock_create_sub.return_value = {
            'id': 'sub_fail123',
            'status': 'incomplete',
            'latest_invoice': {
                'payment_intent': {
                    'status': 'requires_payment_method',
                    'client_secret': 'pi_fail_secret'
                }
            }
        }
        
        # Create payment method
        response = self.client.post(reverse('payments:payment-method-create'), {
            'type': 'card',
            'card_number': '4000000000000002',  # Card that triggers decline
            'exp_month': 12,
            'exp_year': 2025,
            'cvc': '123'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        payment_method = PaymentMethod.objects.get(user=self.user)
        
        # Try to create subscription
        response = self.client.post(reverse('companies:subscription-create'), {
            'plan_slug': 'pro',
            'payment_method_id': payment_method.id,
            'billing_cycle': 'monthly'
        })
        
        # Should return payment required status
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.assertIn('client_secret', response.data)
        print("✓ Payment failed as expected")
        print(f"✓ Status: {response.data['status']}")
        
        # Verify subscription is incomplete
        subscription = Subscription.objects.get(company=self.company)
        self.assertEqual(subscription.status, 'incomplete')
        
        # Second attempt - payment succeeds
        print("\n>>> Second Payment Attempt (Will Succeed)")
        
        # Create new payment method
        mock_create_pm.return_value = {'id': 'pm_success123'}
        mock_attach.return_value = {'id': 'pm_success123'}
        
        response = self.client.post(reverse('payments:payment-method-create'), {
            'type': 'card',
            'card_number': '4242424242424242',  # Valid card
            'exp_month': 12,
            'exp_year': 2025,
            'cvc': '123'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        new_payment_method = PaymentMethod.objects.filter(user=self.user).last()
        
        # Mock successful subscription update
        with patch('apps.payments.payment_service.StripeGateway.update_subscription_payment_method') as mock_update:
            mock_update.return_value = {
                'id': 'sub_fail123',
                'status': 'active',
                'latest_invoice': {
                    'payment_intent': {
                        'status': 'succeeded'
                    }
                }
            }
            
            # Retry payment with new method
            response = self.client.post(
                reverse('payments:retry-payment', kwargs={'subscription_id': subscription.id}),
                {'payment_method_id': new_payment_method.id}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify subscription is now active
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'active')
        
        self.company.refresh_from_db()
        self.assertEqual(self.company.subscription_status, 'active')
        
        print("✓ Payment retry successful")
        print(f"✓ Subscription status: {subscription.status}")
        print("="*60)