"""
Unit tests for CreditService
Tests credit management, transactions, and business logic
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.companies.models import Company
from apps.ai_insights.models import (
    AICredit, 
    AICreditTransaction, 
    AIConversation,
    AIMessage
)
from apps.ai_insights.services.credit_service import (
    CreditService, 
    InsufficientCreditsError
)

User = get_user_model()


class TestCreditService(TestCase):
    """Test CreditService functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(
            name='Test Company',
            business_sector='Technology'
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Conversation'
        )
        
        self.credit = AICredit.objects.create(
            company=self.company,
            balance=100,
            monthly_allowance=50,
            bonus_credits=25
        )
    
    def test_get_or_create_credit_existing(self):
        """Test getting existing credit"""
        credit = CreditService.get_or_create_credit(self.company)
        
        self.assertEqual(credit, self.credit)
        self.assertEqual(credit.balance, 100)
    
    def test_get_or_create_credit_new(self):
        """Test creating new credit for company without one"""
        new_company = Company.objects.create(
            name='New Company',
            business_sector='Services'
        )
        
        credit = CreditService.get_or_create_credit(new_company)
        
        self.assertIsNotNone(credit)
        self.assertEqual(credit.company, new_company)
        self.assertEqual(credit.balance, 0)
        self.assertEqual(credit.monthly_allowance, 0)
    
    def test_check_credits_sufficient(self):
        """Test checking credits when sufficient"""
        has_credits, message = CreditService.check_credits(self.company)
        
        self.assertTrue(has_credits)
        self.assertIsNone(message)
    
    def test_check_credits_insufficient(self):
        """Test checking credits when insufficient"""
        # Set balance to zero
        self.credit.balance = 0
        self.credit.save()
        
        has_credits, message = CreditService.check_credits(self.company)
        
        self.assertFalse(has_credits)
        self.assertIsNotNone(message)
        self.assertIn('insuficientes', message)
    
    def test_use_credits_success(self):
        """Test successful credit usage"""
        initial_balance = self.credit.balance
        amount_to_use = 5
        
        result = CreditService.use_credits(
            company=self.company,
            amount=amount_to_use,
            description='Test AI usage',
            metadata={'model': 'gpt-4o-mini'},
            user=self.user,
            conversation=self.conversation
        )
        
        # Verify result
        self.assertIn('credits_remaining', result)
        self.assertIn('transaction', result)
        self.assertEqual(result['credits_remaining'], initial_balance - amount_to_use)
        
        # Verify credit balance updated
        self.credit.refresh_from_db()
        self.assertEqual(self.credit.balance, initial_balance - amount_to_use)
        
        # Verify transaction created
        transaction = result['transaction']
        self.assertIsInstance(transaction, AICreditTransaction)
        self.assertEqual(transaction.company, self.company)
        self.assertEqual(transaction.type, 'usage')
        self.assertEqual(transaction.amount, -amount_to_use)
        self.assertEqual(transaction.balance_before, initial_balance)
        self.assertEqual(transaction.balance_after, initial_balance - amount_to_use)
    
    def test_use_credits_insufficient(self):
        """Test credit usage when insufficient balance"""
        # Set low balance
        self.credit.balance = 2
        self.credit.save()
        
        # Try to use more credits than available
        with self.assertRaises(InsufficientCreditsError) as context:
            CreditService.use_credits(
                company=self.company,
                amount=5,
                description='Test usage'
            )
        
        self.assertIn('Créditos insuficientes', str(context.exception))
        
        # Verify balance unchanged
        self.credit.refresh_from_db()
        self.assertEqual(self.credit.balance, 2)
    
    def test_use_credits_with_bonus(self):
        """Test credit usage includes bonus credits"""
        # Set regular balance low but bonus credits available
        self.credit.balance = 2
        self.credit.bonus_credits = 10
        self.credit.save()
        
        result = CreditService.use_credits(
            company=self.company,
            amount=5,
            description='Test with bonus'
        )
        
        # Should succeed using regular + bonus credits
        self.assertEqual(result['credits_remaining'], 7)  # 2 + 10 - 5
        
        # Verify balances updated correctly
        self.credit.refresh_from_db()
        # Implementation detail: how bonus vs regular credits are deducted
        total_remaining = self.credit.balance + self.credit.bonus_credits
        self.assertEqual(total_remaining, 7)
    
    def test_add_credits_purchase(self):
        """Test adding credits via purchase"""
        initial_balance = self.credit.balance
        amount_to_add = 50
        
        result = CreditService.add_credits(
            company=self.company,
            amount=amount_to_add,
            transaction_type='purchase',
            description='Credit purchase',
            metadata={'payment_id': 'pay_123'},
            user=self.user
        )
        
        # Verify result
        self.assertIn('new_balance', result)
        self.assertIn('transaction', result)
        self.assertEqual(result['new_balance'], initial_balance + amount_to_add)
        
        # Verify credit balance updated
        self.credit.refresh_from_db()
        self.assertEqual(self.credit.balance, initial_balance + amount_to_add)
        
        # Verify transaction created
        transaction = result['transaction']
        self.assertEqual(transaction.type, 'purchase')
        self.assertEqual(transaction.amount, amount_to_add)
        self.assertEqual(transaction.metadata['payment_id'], 'pay_123')
    
    def test_add_credits_bonus(self):
        """Test adding bonus credits"""
        initial_bonus = self.credit.bonus_credits
        amount_to_add = 25
        
        result = CreditService.add_credits(
            company=self.company,
            amount=amount_to_add,
            transaction_type='bonus',
            description='Welcome bonus',
            metadata={'bonus_type': 'welcome'},
            add_to_bonus=True
        )
        
        # Verify bonus credits updated
        self.credit.refresh_from_db()
        self.assertEqual(self.credit.bonus_credits, initial_bonus + amount_to_add)
        
        # Verify transaction
        transaction = result['transaction']
        self.assertEqual(transaction.type, 'bonus')
        self.assertEqual(transaction.metadata['bonus_type'], 'welcome')
    
    def test_add_credits_refund(self):
        """Test adding credits as refund"""
        initial_balance = self.credit.balance
        refund_amount = 10
        
        result = CreditService.add_credits(
            company=self.company,
            amount=refund_amount,
            transaction_type='refund',
            description='Refund for service issue',
            metadata={'reason': 'api_error', 'original_transaction': 'txn_123'}
        )
        
        # Verify refund processed
        self.credit.refresh_from_db()
        self.assertEqual(self.credit.balance, initial_balance + refund_amount)
        
        # Verify transaction
        transaction = result['transaction']
        self.assertEqual(transaction.type, 'refund')
        self.assertEqual(transaction.metadata['reason'], 'api_error')
    
    @patch('apps.ai_insights.services.credit_service.timezone')
    def test_monthly_reset_needed(self, mock_timezone):
        """Test detecting when monthly reset is needed"""
        from datetime import timedelta
        
        # Mock current time
        current_time = timezone.now()
        mock_timezone.now.return_value = current_time
        
        # Set last reset to over a month ago
        self.credit.last_reset = current_time - timedelta(days=35)
        self.credit.save()
        
        needs_reset = CreditService._monthly_reset_needed(self.credit)
        self.assertTrue(needs_reset)
        
        # Set last reset to recent
        self.credit.last_reset = current_time - timedelta(days=15)
        self.credit.save()
        
        needs_reset = CreditService._monthly_reset_needed(self.credit)
        self.assertFalse(needs_reset)
    
    def test_perform_monthly_reset(self):
        """Test monthly reset functionality"""
        from datetime import timedelta
        
        # Set up scenario needing reset
        self.credit.balance = 30  # Some remaining credits
        self.credit.monthly_allowance = 100
        self.credit.last_reset = timezone.now() - timedelta(days=35)
        self.credit.save()
        
        result = CreditService.perform_monthly_reset(self.company)
        
        # Verify reset occurred
        self.assertIsNotNone(result)
        self.credit.refresh_from_db()
        
        # Verify balance reset to allowance
        self.assertEqual(self.credit.balance, self.credit.monthly_allowance)
        
        # Verify last_reset updated
        self.assertTrue(self.credit.last_reset > timezone.now() - timedelta(minutes=1))
        
        # Verify transaction created
        reset_transactions = AICreditTransaction.objects.filter(
            company=self.company,
            type='monthly_reset'
        )
        self.assertTrue(reset_transactions.exists())
    
    def test_perform_monthly_reset_not_needed(self):
        """Test monthly reset when not needed"""
        # Recent reset
        self.credit.last_reset = timezone.now()
        self.credit.save()
        
        result = CreditService.perform_monthly_reset(self.company)
        
        # Should not perform reset
        self.assertIsNone(result)
    
    @patch('stripe.PaymentIntent.create')
    def test_purchase_credits_stripe(self, mock_stripe):
        """Test credit purchase via Stripe"""
        # Mock Stripe response
        mock_stripe.return_value = Mock(
            id='pi_test_123',
            status='requires_payment_method',
            client_secret='pi_test_123_secret_abc'
        )
        
        result = CreditService.purchase_credits(
            company=self.company,
            amount=500,
            payment_method_id='pm_test_card',
            user=self.user
        )
        
        # Verify Stripe called
        mock_stripe.assert_called_once()
        call_args = mock_stripe.call_args[1]
        self.assertEqual(call_args['amount'], 4999)  # 500 credits * 9.99 in cents
        self.assertEqual(call_args['currency'], 'brl')
        
        # Verify result structure
        self.assertIn('payment_intent', result)
        self.assertIn('client_secret', result)
    
    def test_get_credit_packages(self):
        """Test credit package configuration"""
        packages = CreditService.get_credit_packages()
        
        self.assertIsInstance(packages, list)
        self.assertTrue(len(packages) > 0)
        
        # Verify package structure
        for package in packages:
            self.assertIn('credits', package)
            self.assertIn('price', package)
            self.assertIn('price_per_credit', package)
            self.assertTrue(package['credits'] > 0)
            self.assertTrue(package['price'] > 0)
    
    def test_calculate_credit_cost(self):
        """Test credit cost calculation"""
        # Test different amounts
        test_cases = [
            (100, 999),    # 100 credits = R$ 9.99
            (500, 4999),   # 500 credits = R$ 49.99 
            (1000, 7999),  # 1000 credits = R$ 79.99 (bulk discount)
        ]
        
        for credits, expected_cents in test_cases:
            cost = CreditService._calculate_credit_cost(credits)
            self.assertEqual(cost, expected_cents)
    
    def test_get_usage_statistics(self):
        """Test usage statistics calculation"""
        # Create usage transactions
        for i in range(5):
            AICreditTransaction.objects.create(
                company=self.company,
                type='usage',
                amount=-2,
                balance_before=100 - (i * 2),
                balance_after=98 - (i * 2),
                description=f'Usage {i}',
                metadata={'model': 'gpt-4o-mini'}
            )
        
        stats = CreditService.get_usage_statistics(self.company)
        
        # Verify statistics
        self.assertIn('total_used', stats)
        self.assertIn('this_month', stats)
        self.assertIn('by_model', stats)
        self.assertIn('average_per_day', stats)
        
        self.assertEqual(stats['total_used'], 10)  # 5 transactions * 2 credits each
    
    def test_predict_usage_trend(self):
        """Test usage trend prediction"""
        from datetime import timedelta
        
        # Create usage pattern over time
        base_date = timezone.now() - timedelta(days=30)
        for i in range(30):
            date = base_date + timedelta(days=i)
            AICreditTransaction.objects.create(
                company=self.company,
                type='usage',
                amount=-3,  # Consistent daily usage
                balance_before=100,
                balance_after=97,
                description=f'Daily usage {i}',
                created_at=date
            )
        
        prediction = CreditService.predict_usage_trend(self.company, days=30)
        
        # Verify prediction structure
        self.assertIn('predicted_usage', prediction)
        self.assertIn('confidence', prediction)
        self.assertIn('trend', prediction)
        
        # Should predict ~90 credits for 30 days (3 per day)
        self.assertAlmostEqual(prediction['predicted_usage'], 90, delta=10)
    
    def test_check_low_balance_alert(self):
        """Test low balance alert logic"""
        # Set low balance
        self.credit.balance = 5
        self.credit.monthly_allowance = 100
        self.credit.save()
        
        alert = CreditService.check_low_balance_alert(self.company)
        
        # Should trigger low balance alert
        self.assertIsNotNone(alert)
        self.assertEqual(alert['level'], 'critical')
        self.assertIn('5%', alert['message'])  # 5 out of 100
        
        # Set adequate balance
        self.credit.balance = 50
        self.credit.save()
        
        alert = CreditService.check_low_balance_alert(self.company)
        
        # Should not trigger alert
        self.assertIsNone(alert)
    
    def test_estimate_runway(self):
        """Test credit runway estimation"""
        from datetime import timedelta
        
        # Create recent usage pattern
        for i in range(7):  # Last 7 days
            date = timezone.now() - timedelta(days=i)
            AICreditTransaction.objects.create(
                company=self.company,
                type='usage',
                amount=-5,  # 5 credits per day
                balance_before=100,
                balance_after=95,
                description=f'Usage day {i}',
                created_at=date
            )
        
        runway = CreditService.estimate_runway(self.company)
        
        # With 100 credits and 5 credits/day usage, should be ~20 days
        self.assertAlmostEqual(runway['days'], 20, delta=2)
        self.assertIn('warning_level', runway)
        
        # Test with no usage history
        AICreditTransaction.objects.filter(company=self.company).delete()
        runway = CreditService.estimate_runway(self.company)
        
        self.assertIsNone(runway['days'])  # Cannot predict without history


class TestCreditServiceIntegration(TestCase):
    """Test CreditService integration scenarios"""
    
    def setUp(self):
        """Set up integration test data"""
        self.company = Company.objects.create(
            name='Integration Test Company',
            business_sector='Finance'
        )
        
        self.user = User.objects.create_user(
            email='integration@example.com',
            password='testpass123'
        )
        
        self.credit = AICredit.objects.create(
            company=self.company,
            balance=25,
            monthly_allowance=100
        )
    
    def test_concurrent_credit_usage(self):
        """Test concurrent credit usage scenarios"""
        from threading import Thread
        import time
        
        def use_credits(amount):
            try:
                CreditService.use_credits(
                    company=self.company,
                    amount=amount,
                    description='Concurrent usage test'
                )
            except InsufficientCreditsError:
                pass  # Expected for some threads
        
        # Start multiple threads trying to use credits
        threads = []
        for i in range(5):
            thread = Thread(target=use_credits, args=(10,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify balance is consistent (should prevent over-spending)
        self.credit.refresh_from_db()
        self.assertTrue(self.credit.balance >= 0)
        
        # Verify transaction count matches actual usage
        usage_transactions = AICreditTransaction.objects.filter(
            company=self.company,
            type='usage'
        )
        total_used = sum(abs(txn.amount) for txn in usage_transactions)
        expected_balance = 25 - total_used
        self.assertEqual(self.credit.balance, expected_balance)
    
    def test_credit_lifecycle_workflow(self):
        """Test complete credit lifecycle"""
        # 1. Start with fresh company
        new_company = Company.objects.create(
            name='Lifecycle Test Company',
            business_sector='Retail'
        )
        
        # 2. First access creates credit record
        credit = CreditService.get_or_create_credit(new_company)
        self.assertEqual(credit.balance, 0)
        
        # 3. Purchase credits
        with patch('stripe.PaymentIntent.create') as mock_stripe:
            mock_stripe.return_value = Mock(
                id='pi_lifecycle_test',
                status='requires_payment_method'
            )
            
            purchase_result = CreditService.purchase_credits(
                company=new_company,
                amount=200,
                payment_method_id='pm_test',
                user=self.user
            )
        
        # 4. Simulate payment success and add credits
        CreditService.add_credits(
            company=new_company,
            amount=200,
            transaction_type='purchase',
            description='Credit purchase completed',
            metadata={'payment_intent_id': 'pi_lifecycle_test'}
        )
        
        credit.refresh_from_db()
        self.assertEqual(credit.balance, 200)
        
        # 5. Use credits for AI operations
        for i in range(10):
            CreditService.use_credits(
                company=new_company,
                amount=5,
                description=f'AI operation {i}',
                metadata={'model': 'gpt-4o-mini'}
            )
        
        credit.refresh_from_db()
        self.assertEqual(credit.balance, 150)  # 200 - (10 * 5)
        
        # 6. Monthly reset
        credit.monthly_allowance = 100
        credit.save()
        
        reset_result = CreditService.perform_monthly_reset(new_company)
        self.assertIsNotNone(reset_result)
        
        credit.refresh_from_db()
        self.assertEqual(credit.balance, 100)  # Reset to allowance
        
        # 7. Verify transaction history
        transactions = AICreditTransaction.objects.filter(
            company=new_company
        ).order_by('created_at')
        
        transaction_types = [txn.type for txn in transactions]
        self.assertIn('purchase', transaction_types)
        self.assertEqual(transaction_types.count('usage'), 10)
        self.assertIn('monthly_reset', transaction_types)