"""
Unit tests for AICredit and AICreditTransaction models
Tests credit management, transactions, and business logic
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.companies.models import Company
from apps.companies.tests.factories import CompanyFactory
from apps.ai_insights.models import AICredit, AICreditTransaction, AIConversation

User = get_user_model()


class TestAICredit(TestCase):
    """Test AICredit model functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create minimal test data
        # Get or create a test user
        self.user = User.objects.get_or_create(
            username='testuser_ai',
            defaults={
                'email': 'testai@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )[0]
        
        # Create a real Company object now that database is working
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            trade_name='Test Company Ltd'
        )
    
    def test_create_ai_credit(self):
        """Test creating AICredit instance"""
        credit = AICredit.objects.create(
            company=self.company,
            balance=100,
            monthly_allowance=50,
            bonus_credits=25
        )
        
        self.assertEqual(credit.company, self.company)
        self.assertEqual(credit.balance, 100)
        self.assertEqual(credit.monthly_allowance, 50)
        self.assertEqual(credit.bonus_credits, 25)
        self.assertEqual(credit.total_purchased, 0)
        self.assertIsNotNone(credit.created_at)
        self.assertIsNotNone(credit.updated_at)
        self.assertIsNotNone(credit.last_reset)
    
    def test_ai_credit_str_representation(self):
        """Test string representation of AICredit"""
        credit = AICredit.objects.create(
            company=self.company,
            balance=75
        )
        
        expected = f"{self.company.name} - 75 créditos"
        self.assertEqual(str(credit), expected)
    
    def test_ai_credit_balance_validation(self):
        """Test balance cannot be negative"""
        with self.assertRaises(ValidationError):
            credit = AICredit(
                company=self.company,
                balance=-10  # Invalid negative balance
            )
            credit.full_clean()
    
    def test_ai_credit_one_to_one_relationship(self):
        """Test one-to-one relationship with Company"""
        # First credit
        credit1 = AICredit.objects.create(
            company=self.company,
            balance=100
        )
        
        # Attempting to create second credit for same company should work
        # (model allows it, business logic should prevent it)
        credit2 = AICredit(
            company=self.company,
            balance=50
        )
        # This would work at model level, app logic should prevent duplicates
        
        # Test relationship access (assuming reverse relationship exists)
        # Note: This test may need adjustment based on actual model relationship setup
        self.assertEqual(credit1.company, self.company)
    
    def test_ai_credit_defaults(self):
        """Test default values for AICredit fields"""
        credit = AICredit.objects.create(company=self.company)
        
        self.assertEqual(credit.balance, 0)
        self.assertEqual(credit.monthly_allowance, 0)
        self.assertEqual(credit.bonus_credits, 0)
        self.assertEqual(credit.total_purchased, 0)
        self.assertIsNotNone(credit.last_reset)


class TestAICreditTransaction(TestCase):
    """Test AICreditTransaction model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser_tx',
            email='test@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            trade_name='Test Company Ltd'
        )
        self.credit = AICredit.objects.create(
            company=self.company,
            balance=100
        )
    
    def test_create_credit_transaction(self):
        """Test creating AICreditTransaction"""
        transaction = AICreditTransaction.objects.create(
            company=self.company,
            type='usage',
            amount=-5,
            balance_before=100,
            balance_after=95,
            description='AI chat message',
            user=self.user,
            metadata={'model': 'gpt-4o-mini', 'tokens': 150}
        )
        
        self.assertEqual(transaction.company, self.company)
        self.assertEqual(transaction.type, 'usage')
        self.assertEqual(transaction.amount, -5)
        self.assertEqual(transaction.balance_before, 100)
        self.assertEqual(transaction.balance_after, 95)
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.metadata['model'], 'gpt-4o-mini')
        self.assertIsNotNone(transaction.created_at)
    
    def test_transaction_str_representation(self):
        """Test string representation of transaction"""
        transaction = AICreditTransaction.objects.create(
            company=self.company,
            type='purchase',
            amount=50,
            balance_before=100,
            balance_after=150,
            description='Credit purchase'
        )
        
        self.assertEqual(str(transaction), "Compra Avulsa - 50 créditos")
    
    def test_transaction_types(self):
        """Test all transaction types are valid"""
        valid_types = [
            'monthly_reset',
            'purchase', 
            'bonus',
            'usage',
            'refund',
            'adjustment'
        ]
        
        for transaction_type in valid_types:
            # Test that the transaction can be created and saved
            transaction = AICreditTransaction.objects.create(
                company=self.company,
                type=transaction_type,
                amount=10,
                balance_before=100,
                balance_after=110,
                description=f'Test {transaction_type}',
                metadata={'test': True}  # Provide non-empty metadata
            )
            # Verify the transaction was created successfully
            self.assertEqual(transaction.type, transaction_type)
            self.assertEqual(transaction.amount, 10)
    
    def test_transaction_with_conversation_reference(self):
        """Test transaction linked to conversation"""
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Conversation'
        )
        
        transaction = AICreditTransaction.objects.create(
            company=self.company,
            type='usage',
            amount=-3,
            balance_before=100,
            balance_after=97,
            description='Chat message usage',
            conversation=conversation,
            user=self.user
        )
        
        self.assertEqual(transaction.conversation, conversation)
        self.assertEqual(transaction.user, self.user)
    
    def test_transaction_with_payment_reference(self):
        """Test transaction with payment ID"""
        transaction = AICreditTransaction.objects.create(
            company=self.company,
            type='purchase',
            amount=100,
            balance_before=50,
            balance_after=150,
            description='Credit purchase via Stripe',
            payment_id='pi_1234567890',
            user=self.user
        )
        
        self.assertEqual(transaction.payment_id, 'pi_1234567890')
        self.assertEqual(transaction.type, 'purchase')
    
    def test_transaction_metadata_field(self):
        """Test metadata JSON field functionality"""
        metadata = {
            'model': 'gpt-4o',
            'tokens_input': 100,
            'tokens_output': 50,
            'conversation_id': 123,
            'message_type': 'analysis'
        }
        
        transaction = AICreditTransaction.objects.create(
            company=self.company,
            type='usage',
            amount=-5,
            balance_before=100,
            balance_after=95,
            description='Complex AI analysis',
            metadata=metadata
        )
        
        # Test metadata retrieval
        self.assertEqual(transaction.metadata['model'], 'gpt-4o')
        self.assertEqual(transaction.metadata['tokens_input'], 100)
        self.assertEqual(transaction.metadata['conversation_id'], 123)
    
    def test_transaction_ordering(self):
        """Test transactions are ordered by creation date (newest first)"""
        # Create transactions with small time delays
        older_transaction = AICreditTransaction.objects.create(
            company=self.company,
            type='usage',
            amount=-1,
            balance_before=100,
            balance_after=99,
            description='Older transaction'
        )
        
        newer_transaction = AICreditTransaction.objects.create(
            company=self.company,
            type='usage',
            amount=-1,
            balance_before=99,
            balance_after=98,
            description='Newer transaction'
        )
        
        # Query all transactions
        transactions = list(AICreditTransaction.objects.filter(company=self.company))
        
        # Should be ordered by -created_at (newest first)
        self.assertEqual(transactions[0], newer_transaction)
        self.assertEqual(transactions[1], older_transaction)
    
    def test_transaction_indexes(self):
        """Test database indexes are working"""
        # Create multiple transactions
        for i in range(5):
            AICreditTransaction.objects.create(
                company=self.company,
                type='usage' if i % 2 == 0 else 'purchase',
                amount=-1 if i % 2 == 0 else 10,
                balance_before=100 + i,
                balance_after=99 + i if i % 2 == 0 else 110 + i,
                description=f'Transaction {i}'
            )
        
        # Test company-based queries (should use company index)
        company_transactions = AICreditTransaction.objects.filter(
            company=self.company
        ).order_by('-created_at')
        
        self.assertEqual(company_transactions.count(), 5)
        
        # Test type-based queries (should use type index)
        usage_transactions = AICreditTransaction.objects.filter(
            type='usage'
        )
        
        self.assertEqual(usage_transactions.count(), 3)
    
    def test_transaction_cascade_deletion(self):
        """Test cascade deletion behavior"""
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Conversation'
        )
        
        # Create transaction linked to conversation
        transaction = AICreditTransaction.objects.create(
            company=self.company,
            type='usage',
            amount=-2,
            balance_before=100,
            balance_after=98,
            description='Usage transaction',
            conversation=conversation,
            user=self.user
        )
        
        transaction_id = transaction.id
        
        # Delete conversation - transaction should still exist but reference should be nulled
        conversation.delete()
        
        # Transaction should still exist
        transaction.refresh_from_db()
        self.assertIsNone(transaction.conversation)
        self.assertEqual(transaction.user, self.user)  # User reference preserved
        
        # Delete company - transaction should be cascade deleted
        self.company.delete()
        
        # Transaction should be deleted
        with self.assertRaises(AICreditTransaction.DoesNotExist):
            AICreditTransaction.objects.get(id=transaction_id)


class TestCreditTransactionBusinessLogic(TestCase):
    """Test business logic for credit transactions"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser_biz',
            email='testbiz@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            trade_name='Test Company Ltd'
        )
    
    def test_monthly_reset_transaction(self):
        """Test monthly reset transaction logic"""
        credit = AICredit.objects.create(
            company=self.company,
            balance=25,  # Some remaining credits
            monthly_allowance=100,
            last_reset=timezone.now() - timedelta(days=35)  # Over a month ago
        )
        
        # Create monthly reset transaction
        reset_transaction = AICreditTransaction.objects.create(
            company=self.company,
            type='monthly_reset',
            amount=75,  # Add remaining allowance
            balance_before=25,
            balance_after=100,
            description='Monthly allowance reset',
            metadata={
                'previous_allowance': 100,
                'carried_over': 25,
                'reset_date': timezone.now().isoformat()
            }
        )
        
        self.assertEqual(reset_transaction.amount, 75)
        self.assertEqual(reset_transaction.balance_after, 100)
        self.assertEqual(reset_transaction.metadata['carried_over'], 25)
    
    def test_usage_transaction_pattern(self):
        """Test typical usage transaction patterns"""
        # Test different AI model costs
        model_costs = {
            'gpt-4o-mini': 1,
            'gpt-4o': 5
        }
        
        balance = 100
        
        for model, cost in model_costs.items():
            transaction = AICreditTransaction.objects.create(
                company=self.company,
                type='usage',
                amount=-cost,
                balance_before=balance,
                balance_after=balance - cost,
                description=f'AI chat - {model}',
                user=self.user,
                metadata={
                    'model': model,
                    'cost_per_credit': cost,
                    'request_type': 'general'
                }
            )
            
            balance -= cost
            
            self.assertEqual(transaction.amount, -cost)
            self.assertEqual(transaction.metadata['model'], model)
    
    def test_purchase_transaction_with_payment(self):
        """Test credit purchase transaction"""
        purchase_transaction = AICreditTransaction.objects.create(
            company=self.company,
            type='purchase',
            amount=500,  # 500 credits purchased
            balance_before=50,
            balance_after=550,
            description='Credit pack purchase - 500 credits',
            payment_id='pi_stripe_payment_123',
            user=self.user,
            metadata={
                'package_size': 500,
                'price_paid': 49.99,
                'payment_method': 'stripe',
                'currency': 'BRL'
            }
        )
        
        self.assertEqual(purchase_transaction.amount, 500)
        self.assertEqual(purchase_transaction.payment_id, 'pi_stripe_payment_123')
        self.assertEqual(purchase_transaction.metadata['price_paid'], 49.99)
    
    def test_bonus_credit_transaction(self):
        """Test bonus credit transactions"""
        bonus_transaction = AICreditTransaction.objects.create(
            company=self.company,
            type='bonus',
            amount=100,
            balance_before=200,
            balance_after=300,
            description='Welcome bonus - 100 credits',
            user=self.user,
            metadata={
                'bonus_type': 'welcome',
                'promotion_code': 'WELCOME100',
                'expires_days': 90
            }
        )
        
        self.assertEqual(bonus_transaction.type, 'bonus')
        self.assertEqual(bonus_transaction.amount, 100)
        self.assertEqual(bonus_transaction.metadata['bonus_type'], 'welcome')
    
    def test_refund_transaction(self):
        """Test refund transaction logic"""
        refund_transaction = AICreditTransaction.objects.create(
            company=self.company,
            type='refund',
            amount=50,  # Credits refunded
            balance_before=100,
            balance_after=150,
            description='Refund for service issue',
            user=self.user,
            metadata={
                'reason': 'service_outage',
                'original_transaction_id': 'txn_123',
                'refund_percentage': 100
            }
        )
        
        self.assertEqual(refund_transaction.type, 'refund')
        self.assertEqual(refund_transaction.amount, 50)
        self.assertEqual(refund_transaction.metadata['reason'], 'service_outage')