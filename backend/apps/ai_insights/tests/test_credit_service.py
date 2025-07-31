"""
Tests for Credit Service
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.companies.models import Company, SubscriptionPlan, CompanyUser, PaymentMethod
from apps.ai_insights.models import AICredit, AICreditTransaction
from apps.ai_insights.services.credit_service import CreditService, InsufficientCreditsError

User = get_user_model()


class CreditServiceTest(TestCase):
    """Test CreditService functionality"""
    
    def setUp(self):
        """Setup test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create plan
        self.plan = SubscriptionPlan.objects.create(
            name='Professional',
            slug='professional',
            plan_type='professional',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00'),
            max_bank_accounts=10,
            max_transactions=5000
        )
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user,
            cnpj='12345678901234',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.plan,
            subscription_status='active'
        )
        
        # Create company user
        CompanyUser.objects.create(
            user=self.user,
            company=self.company,
            role='admin',
            is_active=True
        )
    
    def test_check_credits_new_company(self):
        """Test checking credits for new company (auto-creation)"""
        # Company has no AICredit record yet
        self.assertFalse(AICredit.objects.filter(company=self.company).exists())
        
        # Mock company.can_use_ai_insight()
        with patch.object(self.company, 'can_use_ai_insight', return_value=(True, 'OK')):
            has_credits, message = CreditService.check_credits(self.company)
        
        # Should create AICredit record and return True
        self.assertTrue(has_credits)
        self.assertIn('créditos disponíveis', message)
        
        # Should have created AICredit with initial credits
        ai_credit = AICredit.objects.get(company=self.company)
        self.assertEqual(ai_credit.monthly_allowance, 100)  # Professional plan
        self.assertEqual(ai_credit.bonus_credits, 10)  # Welcome bonus
        self.assertEqual(ai_credit.balance, 100)  # Monthly allowance
    
    def test_check_credits_no_permission(self):
        """Test checking credits when company can't use AI"""
        with patch.object(self.company, 'can_use_ai_insight', 
                         return_value=(False, 'Plan não permite AI')):
            has_credits, message = CreditService.check_credits(self.company)
        
        self.assertFalse(has_credits)
        self.assertEqual(message, 'Plan não permite AI')
    
    def test_check_credits_no_balance(self):
        """Test checking credits with zero balance"""
        # Create AICredit with no balance
        AICredit.objects.create(
            company=self.company,
            balance=0,
            monthly_allowance=100,
            bonus_credits=0
        )
        
        with patch.object(self.company, 'can_use_ai_insight', return_value=(True, 'OK')):
            has_credits, message = CreditService.check_credits(self.company)
        
        self.assertFalse(has_credits)
        self.assertIn('Sem créditos disponíveis', message)
    
    def test_use_credits_success(self):
        """Test using credits successfully"""
        # Create AICredit with balance
        ai_credit = AICredit.objects.create(
            company=self.company,
            balance=50,
            monthly_allowance=100,
            bonus_credits=25
        )
        
        # Use 10 credits
        result = CreditService.use_credits(
            company=self.company,
            amount=10,
            description='Test usage',
            user=self.user
        )
        
        # Check result
        self.assertEqual(result['credits_used'], 10)
        self.assertEqual(result['credits_remaining'], 65)  # 40 + 25
        
        # Check database
        ai_credit.refresh_from_db()
        self.assertEqual(ai_credit.balance, 40)  # 50 - 10
        self.assertEqual(ai_credit.bonus_credits, 25)  # Unchanged
        
        # Check transaction was created
        transaction = AICreditTransaction.objects.get(company=self.company)
        self.assertEqual(transaction.type, 'usage')
        self.assertEqual(transaction.amount, -10)
        self.assertEqual(transaction.user, self.user)
    
    def test_use_credits_with_bonus(self):
        """Test using credits that require using bonus credits"""
        # Create AICredit with small balance but bonus credits
        ai_credit = AICredit.objects.create(
            company=self.company,
            balance=5,
            monthly_allowance=100,
            bonus_credits=20
        )
        
        # Use 15 credits (more than balance)
        result = CreditService.use_credits(
            company=self.company,
            amount=15,
            description='Test usage with bonus',
            user=self.user
        )
        
        # Check result
        self.assertEqual(result['credits_used'], 15)
        self.assertEqual(result['credits_remaining'], 10)  # 0 + 10
        
        # Check database
        ai_credit.refresh_from_db()
        self.assertEqual(ai_credit.balance, 0)  # Used all balance
        self.assertEqual(ai_credit.bonus_credits, 10)  # 20 - 10
    
    def test_use_credits_insufficient(self):
        """Test using credits with insufficient balance"""
        # Create AICredit with low balance
        AICredit.objects.create(
            company=self.company,
            balance=5,
            monthly_allowance=100,
            bonus_credits=10
        )
        
        # Try to use more credits than available
        with self.assertRaises(InsufficientCreditsError) as context:
            CreditService.use_credits(
                company=self.company,
                amount=20,  # More than 15 available
                description='Test insufficient',
                user=self.user
            )
        
        self.assertIn('Créditos insuficientes', str(context.exception))
        self.assertIn('Disponível: 15', str(context.exception))
        self.assertIn('Necessário: 20', str(context.exception))
    
    def test_add_credits(self):
        """Test adding credits to company"""
        # Create AICredit
        ai_credit = AICredit.objects.create(
            company=self.company,
            balance=50,
            monthly_allowance=100,
            bonus_credits=0
        )
        
        # Add credits
        transaction = CreditService.add_credits(
            company=self.company,
            amount=25,
            transaction_type='purchase',
            description='Credit purchase',
            user=self.user
        )
        
        # Check transaction
        self.assertEqual(transaction.type, 'purchase')
        self.assertEqual(transaction.amount, 25)
        self.assertEqual(transaction.balance_before, 50)
        self.assertEqual(transaction.balance_after, 75)
        
        # Check database
        ai_credit.refresh_from_db()
        self.assertEqual(ai_credit.balance, 75)
        self.assertEqual(ai_credit.total_purchased, 25)
    
    def test_add_bonus_credits(self):
        """Test adding bonus credits"""
        # Create AICredit
        ai_credit = AICredit.objects.create(
            company=self.company,
            balance=50,
            monthly_allowance=100,
            bonus_credits=0
        )
        
        # Add bonus credits
        transaction = CreditService.add_credits(
            company=self.company,
            amount=15,
            transaction_type='bonus',
            description='Bonus credits',
            user=self.user
        )
        
        # Check database
        ai_credit.refresh_from_db()
        self.assertEqual(ai_credit.balance, 50)  # Unchanged
        self.assertEqual(ai_credit.bonus_credits, 15)  # Added to bonus
        self.assertEqual(ai_credit.total_purchased, 0)  # Not counted as purchase
    
    @patch('apps.ai_insights.services.credit_service.CreditService._process_payment')
    def test_purchase_credits_success(self, mock_payment):
        """Test successful credit purchase"""
        # Mock payment method
        payment_method = PaymentMethod.objects.create(
            company=self.company,
            stripe_payment_method_id='pm_test123',
            card_last4='1234',
            card_brand='visa',
            is_active=True
        )
        
        # Mock payment processing
        mock_payment.return_value = {
            'success': True,
            'payment_id': 'pi_test123',
            'status': 'succeeded',
            'gateway': 'stripe'
        }
        
        # Purchase credits
        result = CreditService.purchase_credits(
            company=self.company,
            amount=100,  # Valid package
            payment_method_id=payment_method.id,
            user=self.user
        )
        
        # Check result
        self.assertIn('transaction', result)
        self.assertIn('payment_id', result)
        self.assertIn('new_balance', result)
        
        # Check transaction was created
        transaction = AICreditTransaction.objects.get(
            company=self.company,
            type='purchase'
        )
        self.assertEqual(transaction.amount, 100)
        self.assertEqual(transaction.payment_id, 'pi_test123')
        
        # Check payment was processed
        mock_payment.assert_called_once()
    
    def test_purchase_credits_invalid_package(self):
        """Test purchasing invalid credit package"""
        with self.assertRaises(ValueError) as context:
            CreditService.purchase_credits(
                company=self.company,
                amount=75,  # Not a valid package
                payment_method_id='pm_test123',
                user=self.user
            )
        
        self.assertIn('Pacote inválido: 75 créditos', str(context.exception))
    
    @patch('apps.ai_insights.services.credit_service.CreditService._process_payment')
    def test_purchase_credits_payment_failure(self, mock_payment):
        """Test credit purchase with payment failure"""
        # Mock payment method
        payment_method = PaymentMethod.objects.create(
            company=self.company,
            stripe_payment_method_id='pm_test123',
            card_last4='1234',
            card_brand='visa',
            is_active=True
        )
        
        # Mock payment failure
        mock_payment.return_value = {
            'success': False,
            'error': 'Card declined'
        }
        
        # Purchase should fail
        with self.assertRaises(Exception) as context:
            CreditService.purchase_credits(
                company=self.company,
                amount=100,
                payment_method_id=payment_method.id,
                user=self.user
            )
        
        self.assertIn('Erro no pagamento: Card declined', str(context.exception))
    
    def test_get_monthly_allowance(self):
        """Test getting monthly allowance based on plan"""
        # Test professional plan
        allowance = CreditService._get_monthly_allowance(self.company)
        self.assertEqual(allowance, 100)
        
        # Test starter plan
        self.company.subscription_plan.plan_type = 'starter'
        self.company.subscription_plan.save()
        allowance = CreditService._get_monthly_allowance(self.company)
        self.assertEqual(allowance, 0)
        
        # Test enterprise plan
        self.company.subscription_plan.plan_type = 'enterprise'
        self.company.subscription_plan.save()
        allowance = CreditService._get_monthly_allowance(self.company)
        self.assertEqual(allowance, 1000)
        
        # Test no plan
        self.company.subscription_plan = None
        self.company.save()
        allowance = CreditService._get_monthly_allowance(self.company)
        self.assertEqual(allowance, 0)
    
    def test_should_reset_monthly_credits(self):
        """Test monthly credit reset detection"""
        from datetime import timedelta
        
        # Create AICredit with old reset date
        ai_credit = AICredit.objects.create(
            company=self.company,
            balance=50,
            monthly_allowance=100,
            last_reset=timezone.now() - timedelta(days=35)  # More than 30 days ago
        )
        
        # Should need reset
        should_reset = CreditService._should_reset_monthly_credits(ai_credit)
        self.assertTrue(should_reset)
        
        # Update to current month
        ai_credit.last_reset = timezone.now()
        ai_credit.save()
        
        # Should not need reset
        should_reset = CreditService._should_reset_monthly_credits(ai_credit)
        self.assertFalse(should_reset)
    
    def test_reset_monthly_credits(self):
        """Test monthly credit reset"""
        from datetime import timedelta
        
        # Create AICredit with partial balance and old reset
        ai_credit = AICredit.objects.create(
            company=self.company,
            balance=30,  # Partial balance
            monthly_allowance=100,
            bonus_credits=5,
            last_reset=timezone.now() - timedelta(days=35)
        )
        
        # Reset credits
        CreditService._reset_monthly_credits(ai_credit)
        
        # Check reset
        ai_credit.refresh_from_db()
        self.assertEqual(ai_credit.balance, 100)  # Full allowance
        self.assertEqual(ai_credit.bonus_credits, 5)  # Unchanged
        
        # Check transaction was created
        transaction = AICreditTransaction.objects.get(
            company=self.company,
            type='monthly_reset'
        )
        self.assertEqual(transaction.amount, 70)  # 100 - 30
    
    def test_get_credit_history(self):
        """Test getting credit history and statistics"""
        # Create AICredit
        ai_credit = AICredit.objects.create(
            company=self.company,
            balance=75,
            monthly_allowance=100,
            bonus_credits=15,
            total_purchased=50
        )
        
        # Create some transactions
        AICreditTransaction.objects.create(
            company=self.company,
            type='purchase',
            amount=50,
            balance_before=25,
            balance_after=75,
            description='Purchase'
        )
        
        AICreditTransaction.objects.create(
            company=self.company,
            type='usage',
            amount=-10,
            balance_before=85,
            balance_after=75,
            description='Usage'
        )
        
        # Get history
        history = CreditService.get_credit_history(self.company, days=30)
        
        # Check current balances
        self.assertEqual(history['current_balance'], 75)
        self.assertEqual(history['bonus_credits'], 15)
        self.assertEqual(history['total_available'], 90)
        self.assertEqual(history['monthly_allowance'], 100)
        self.assertEqual(history['total_purchased'], 50)
        
        # Check statistics
        self.assertIn('statistics', history)
        stats = history['statistics']
        self.assertIn('purchase', stats)
        self.assertIn('usage', stats)
        self.assertEqual(stats['purchase']['count'], 1)
        self.assertEqual(stats['usage']['count'], 1)
    
    def test_credit_costs_mapping(self):
        """Test credit costs for different request types"""
        self.assertEqual(CreditService.CREDIT_COSTS['general'], 1)
        self.assertEqual(CreditService.CREDIT_COSTS['analysis'], 3)
        self.assertEqual(CreditService.CREDIT_COSTS['report'], 5)
        self.assertEqual(CreditService.CREDIT_COSTS['recommendation'], 2)
    
    def test_credit_packages_pricing(self):
        """Test credit package pricing"""
        self.assertEqual(CreditService.CREDIT_PACKAGES[10], Decimal('9.90'))
        self.assertEqual(CreditService.CREDIT_PACKAGES[100], Decimal('79.90'))
        self.assertEqual(CreditService.CREDIT_PACKAGES[1000], Decimal('599.90'))
        
        # Test per-credit cost calculation
        cost_per_credit_10 = CreditService.CREDIT_PACKAGES[10] / 10
        cost_per_credit_1000 = CreditService.CREDIT_PACKAGES[1000] / 1000
        
        # Higher packages should have lower per-credit cost
        self.assertGreater(cost_per_credit_10, cost_per_credit_1000)