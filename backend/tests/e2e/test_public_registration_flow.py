"""
E2E test for public registration flow through landing page
"""
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import json

from apps.authentication.models import User, EmailVerification
from apps.companies.models import Company, CompanyUser, SubscriptionPlan


class TestPublicRegistrationFlow(TransactionTestCase):
    """
    Test the complete public user journey from landing page through registration
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
            gateway_plan_id='price_starter_monthly'
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
            gateway_plan_id='price_pro_monthly'
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
            has_accountant_access=True,
            gateway_plan_id='price_enterprise_monthly'
        )
    
    def test_public_api_endpoints(self):
        """Test public API endpoints for plans and registration"""
        
        print("\n" + "="*60)
        print("TESTING PUBLIC API ENDPOINTS")
        print("="*60)
        
        # Test 1: Get subscription plans (public endpoint)
        print("\n>>> Test 1: Get Subscription Plans")
        response = self.client.get(reverse('companies:public:subscription-plans'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Verify plan data structure
        for plan in response.data:
            self.assertIn('id', plan)
            self.assertIn('name', plan)
            self.assertIn('slug', plan)
            self.assertIn('price_monthly', plan)
            self.assertIn('price_yearly', plan)
            self.assertIn('features', plan)
            self.assertIn('max_users', plan)
            self.assertIn('max_bank_accounts', plan)
            
            print(f"  ✓ {plan['name']}: R$ {plan['price_monthly']}/mês")
        
        # Test 2: Check email availability
        print("\n>>> Test 2: Check Email Availability")
        response = self.client.post(
            reverse('companies:public:check-email'),
            {'email': 'novo@empresa.com.br'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['available'])
        print("  ✓ Email available for registration")
        
        # Test 3: Validate company name
        print("\n>>> Test 3: Validate Company Name")
        response = self.client.post(
            reverse('companies:public:validate-company'),
            {'name': 'Minha Nova Empresa'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        print("  ✓ Company name valid")
    
    @patch('apps.notifications.email_service.EmailService.send_verification_email')
    @patch('apps.payments.payment_service.StripeGateway.create_customer')
    def test_registration_with_plan_selection(self, mock_create_customer, mock_send_email):
        """Test registration flow with immediate plan selection"""
        
        print("\n" + "="*60)
        print("TESTING REGISTRATION WITH PLAN SELECTION")
        print("="*60)
        
        mock_create_customer.return_value = {'id': 'cus_public123'}
        
        # Step 1: User selects Pro plan from landing page
        print("\n>>> Step 1: User Selects Pro Plan")
        selected_plan = self.pro_plan
        print(f"  Selected: {selected_plan.name} - R$ {selected_plan.price_monthly}/mês")
        
        # Step 2: Registration with plan preference
        print("\n>>> Step 2: Registration with Plan Preference")
        registration_data = {
            'email': 'plano.pro@empresa.com.br',
            'password': 'SenhaSegura123!',
            'password2': 'SenhaSegura123!',
            'first_name': 'Cliente',
            'last_name': 'Pro',
            'phone': '+5511999888777',
            'company_name': 'Empresa Pro Ltda',
            'company_type': 'ltda',
            'business_sector': 'retail',
            'selected_plan_slug': 'pro',  # Plan selected from landing
            'cnpj': '12.345.678/0001-90'
        }
        
        response = self.client.post(
            reverse('companies:public:register-with-plan'),
            registration_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify response includes plan info
        self.assertIn('user', response.data)
        self.assertIn('company', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('selected_plan', response.data)
        
        user = User.objects.get(email='plano.pro@empresa.com.br')
        company = Company.objects.get(owner=user)
        
        print(f"  ✓ User created: {user.email}")
        print(f"  ✓ Company created: {company.name}")
        print(f"  ✓ Selected plan stored: {response.data['selected_plan']['name']}")
        
        # Company should still be on trial/starter until payment
        self.assertEqual(company.subscription_plan, self.starter_plan)
        self.assertEqual(company.subscription_status, 'trial')
        
        # Step 3: User continues to payment
        print("\n>>> Step 3: Continue to Payment")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["tokens"]["access"]}')
        
        # Get payment setup info
        response = self.client.get(reverse('companies:payment-setup'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('selected_plan', response.data)
        self.assertIn('stripe_public_key', response.data)
        self.assertEqual(response.data['selected_plan']['slug'], 'pro')
        
        print("  ✓ Payment setup ready")
        print(f"  ✓ Plan to purchase: {response.data['selected_plan']['name']}")
    
    @patch('apps.notifications.email_service.EmailService.send_verification_email')
    @patch('apps.payments.payment_service.StripeGateway.create_customer')
    @patch('apps.payments.payment_service.MercadoPagoGateway.create_payment')
    def test_registration_with_brazilian_payment(self, mock_mp_payment, mock_create_customer, mock_send_email):
        """Test registration with Brazilian payment methods (PIX, Boleto)"""
        
        print("\n" + "="*60)
        print("TESTING BRAZILIAN PAYMENT METHODS")
        print("="*60)
        
        mock_create_customer.return_value = {'id': 'cus_brazil123'}
        
        # Register user
        response = self.client.post(reverse('authentication:register'), {
            'email': 'pix.user@empresa.com.br',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Usuario',
            'last_name': 'PIX',
            'company_name': 'Empresa PIX',
            'company_type': 'mei',
            'business_sector': 'services'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(email='pix.user@empresa.com.br')
        company = Company.objects.get(owner=user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["tokens"]["access"]}')
        
        # Test PIX payment
        print("\n>>> Testing PIX Payment")
        mock_mp_payment.return_value = {
            'id': 'pix_payment_123',
            'status': 'pending',
            'payment_method': 'pix',
            'pix_qr_code': 'data:image/png;base64,iVBORw0KGgoAAAANS...',
            'pix_qr_code_text': '00020126330014BR.GOV.BCB.PIX...',
            'expiration_date': (timezone.now() + timedelta(minutes=30)).isoformat()
        }
        
        response = self.client.post(reverse('payments:create-brazilian-payment'), {
            'plan_slug': 'pro',
            'payment_method': 'pix',
            'billing_cycle': 'monthly'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('qr_code', response.data)
        self.assertIn('qr_code_text', response.data)
        self.assertIn('expiration_date', response.data)
        
        print("  ✓ PIX QR Code generated")
        print("  ✓ Payment pending confirmation")
        
        # Simulate PIX payment confirmation
        with patch('apps.payments.payment_service.MercadoPagoGateway.check_payment_status') as mock_check:
            mock_check.return_value = {'status': 'approved'}
            
            # Webhook simulation
            response = self.client.post(
                reverse('payments:mercadopago-webhook'),
                {
                    'type': 'payment',
                    'data': {'id': 'pix_payment_123'},
                    'action': 'payment.updated'
                },
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify subscription activation
        company.refresh_from_db()
        self.assertEqual(company.subscription_plan.slug, 'pro')
        self.assertEqual(company.subscription_status, 'active')
        
        print("  ✓ PIX payment confirmed")
        print("  ✓ Subscription activated")
        
        # Test Boleto payment
        print("\n>>> Testing Boleto Payment")
        # Create another user for boleto test
        response = self.client.post(reverse('authentication:register'), {
            'email': 'boleto.user@empresa.com.br',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Usuario',
            'last_name': 'Boleto',
            'company_name': 'Empresa Boleto',
            'company_type': 'mei',
            'business_sector': 'retail'
        })
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["tokens"]["access"]}')
        
        mock_mp_payment.return_value = {
            'id': 'boleto_payment_123',
            'status': 'pending',
            'payment_method': 'boleto',
            'boleto_url': 'https://www.mercadopago.com.br/payments/123/boleto',
            'boleto_barcode': '23793381286000000123450000000000000000000000',
            'expiration_date': (timezone.now() + timedelta(days=3)).isoformat()
        }
        
        response = self.client.post(reverse('payments:create-brazilian-payment'), {
            'plan_slug': 'starter',
            'payment_method': 'boleto',
            'billing_cycle': 'yearly'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('boleto_url', response.data)
        self.assertIn('boleto_barcode', response.data)
        
        print("  ✓ Boleto generated")
        print("  ✓ Barcode available for payment")
        
        print("\n" + "="*60)
        print("BRAZILIAN PAYMENT TESTS COMPLETED")
        print("="*60)


class TestFreeTrialFlow(TransactionTestCase):
    """Test free trial registration and limitations"""
    
    def setUp(self):
        self.client = APIClient()
        self._create_subscription_plans()
    
    def _create_subscription_plans(self):
        """Create subscription plans with trial periods"""
        self.starter_plan = SubscriptionPlan.objects.create(
            name='Starter',
            slug='starter',
            plan_type='starter',
            price_monthly=29.00,
            max_bank_accounts=2,
            max_transactions=500
        )
        
        self.pro_plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00,
            max_bank_accounts=5,
            max_transactions=2000,
            has_ai_categorization=True
        )
    
    @patch('apps.notifications.email_service.EmailService.send_verification_email')
    @patch('apps.payments.payment_service.StripeGateway.create_customer')
    def test_free_trial_limitations(self, mock_create_customer, mock_send_email):
        """Test free trial registration and feature limitations"""
        
        print("\n" + "="*60)
        print("TESTING FREE TRIAL FLOW")
        print("="*60)
        
        mock_create_customer.return_value = {'id': 'cus_trial456'}
        
        # Register for free trial
        print("\n>>> Registering for Free Trial")
        response = self.client.post(reverse('authentication:register'), {
            'email': 'trial@empresa.com.br',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Trial',
            'last_name': 'User',
            'company_name': 'Trial Company',
            'company_type': 'ltda',
            'business_sector': 'technology'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(email='trial@empresa.com.br')
        company = Company.objects.get(owner=user)
        
        # Verify trial setup
        self.assertEqual(company.subscription_status, 'trial')
        self.assertIsNotNone(company.trial_ends_at)
        trial_days = (company.trial_ends_at - timezone.now().date()).days
        self.assertEqual(trial_days, 13)  # 14 days minus today
        
        print(f"  ✓ Trial activated: {trial_days + 1} days")
        print(f"  ✓ Plan: {company.subscription_plan.name}")
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["tokens"]["access"]}')
        
        # Test trial limitations
        print("\n>>> Testing Trial Limitations")
        
        # Can access basic features
        response = self.client.get(reverse('banking:bank-account-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("  ✓ Can access bank accounts")
        
        # Cannot access Pro features (AI categorization)
        response = self.client.get(reverse('categories:ai-suggestions'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("  ✓ Cannot access Pro features (expected)")
        
        # Check trial status
        response = self.client.get(reverse('companies:trial-status'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'trial')
        self.assertIn('days_remaining', response.data)
        self.assertIn('features_available', response.data)
        
        print(f"  ✓ Trial status: {response.data['days_remaining']} days remaining")
        
        # Test usage limits
        print("\n>>> Testing Usage Limits")
        
        # Check current usage
        response = self.client.get(reverse('companies:usage-stats'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bank_accounts_used'], 0)
        self.assertEqual(response.data['bank_accounts_limit'], 2)
        self.assertEqual(response.data['transactions_used'], 0)
        self.assertEqual(response.data['transactions_limit'], 500)
        
        print("  ✓ Usage tracking active")
        print(f"  ✓ Bank accounts: 0/{response.data['bank_accounts_limit']}")
        print(f"  ✓ Transactions: 0/{response.data['transactions_limit']}")
        
        print("\n" + "="*60)
        print("FREE TRIAL TESTS COMPLETED")
        print("="*60)