"""
Tests for AI Insights models
"""
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.companies.models import Company, Plan, Subscription
from apps.ai_insights.models import (
    AICredit, AICreditTransaction, AIConversation, 
    AIMessage, AIInsight
)

User = get_user_model()


class AICreditModelTest(TestCase):
    """Test AICredit model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.plan = Plan.objects.create(
            name='Professional',
            plan_type='professional',
            price=Decimal('99.90'),
            max_bank_accounts=10,
            max_transactions=5000,
            max_users=5
        )
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user,
            document='12345678901234'
        )
        Subscription.objects.create(
            company=self.company,
            plan=self.plan,
            status='active'
        )
    
    def test_create_ai_credit(self):
        """Test creating AI credit for company"""
        credit = AICredit.objects.create(
            company=self.company,
            balance=100,
            monthly_allowance=100
        )
        
        self.assertEqual(credit.balance, 100)
        self.assertEqual(credit.monthly_allowance, 100)
        self.assertEqual(credit.bonus_credits, 0)
        self.assertEqual(credit.total_purchased, 0)
        self.assertIsNotNone(credit.last_reset)
    
    def test_unique_credit_per_company(self):
        """Test that only one AICredit can exist per company"""
        AICredit.objects.create(
            company=self.company,
            balance=100
        )
        
        # Try to create another credit for same company
        with self.assertRaises(Exception):
            AICredit.objects.create(
                company=self.company,
                balance=200
            )
    
    def test_string_representation(self):
        """Test string representation of AICredit"""
        credit = AICredit.objects.create(
            company=self.company,
            balance=150
        )
        
        expected = f"AI Credits - {self.company.name}: 150"
        self.assertEqual(str(credit), expected)


class AICreditTransactionModelTest(TestCase):
    """Test AICreditTransaction model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user
        )
        self.credit = AICredit.objects.create(
            company=self.company,
            balance=100
        )
    
    def test_create_credit_transaction(self):
        """Test creating credit transaction"""
        transaction = AICreditTransaction.objects.create(
            company=self.company,
            type='usage',
            amount=-5,
            balance_before=100,
            balance_after=95,
            description='Chat message',
            user=self.user
        )
        
        self.assertEqual(transaction.type, 'usage')
        self.assertEqual(transaction.amount, -5)
        self.assertEqual(transaction.balance_before, 100)
        self.assertEqual(transaction.balance_after, 95)
        self.assertEqual(transaction.user, self.user)
    
    def test_transaction_types(self):
        """Test different transaction types"""
        transaction_types = [
            ('monthly_reset', 100, 'Monthly reset'),
            ('purchase', 50, 'Purchased 50 credits'),
            ('bonus', 10, 'Bonus credits'),
            ('usage', -5, 'Used for chat'),
            ('refund', 5, 'Refunded credits'),
            ('adjustment', -10, 'Manual adjustment')
        ]
        
        for trans_type, amount, desc in transaction_types:
            trans = AICreditTransaction.objects.create(
                company=self.company,
                type=trans_type,
                amount=amount,
                balance_before=100,
                balance_after=100 + amount,
                description=desc
            )
            self.assertEqual(trans.type, trans_type)
            self.assertEqual(trans.amount, amount)
    
    def test_metadata_field(self):
        """Test storing metadata in transaction"""
        metadata = {
            'tokens': 1500,
            'model': 'gpt-4',
            'conversation_id': 'conv-123'
        }
        
        transaction = AICreditTransaction.objects.create(
            company=self.company,
            type='usage',
            amount=-3,
            balance_before=100,
            balance_after=97,
            description='AI analysis',
            metadata=metadata
        )
        
        self.assertEqual(transaction.metadata['tokens'], 1500)
        self.assertEqual(transaction.metadata['model'], 'gpt-4')


class AIConversationModelTest(TestCase):
    """Test AIConversation model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user
        )
    
    def test_create_conversation(self):
        """Test creating AI conversation"""
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Financial Analysis'
        )
        
        self.assertEqual(conversation.company, self.company)
        self.assertEqual(conversation.user, self.user)
        self.assertEqual(conversation.title, 'Financial Analysis')
        self.assertEqual(conversation.status, 'active')
        self.assertEqual(conversation.message_count, 0)
        self.assertEqual(conversation.total_credits_used, 0)
    
    def test_conversation_status_choices(self):
        """Test conversation status transitions"""
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Conversation'
        )
        
        # Test status changes
        for status in ['active', 'archived', 'deleted']:
            conversation.status = status
            conversation.save()
            self.assertEqual(conversation.status, status)
    
    def test_financial_context_storage(self):
        """Test storing financial context"""
        context = {
            'current_balance': 50000.00,
            'monthly_revenue': 150000.00,
            'top_expenses': ['Salaries', 'Rent', 'Suppliers']
        }
        
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Analysis',
            financial_context=context
        )
        
        self.assertEqual(conversation.financial_context['current_balance'], 50000.00)
        self.assertIn('Salaries', conversation.financial_context['top_expenses'])


class AIMessageModelTest(TestCase):
    """Test AIMessage model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user
        )
        self.conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Chat'
        )
    
    def test_create_message(self):
        """Test creating AI message"""
        message = AIMessage.objects.create(
            conversation=self.conversation,
            role='user',
            type='text',
            content='What are my top expenses?'
        )
        
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.type, 'text')
        self.assertEqual(message.content, 'What are my top expenses?')
        self.assertEqual(message.credits_used, 0)
    
    def test_assistant_message_with_credits(self):
        """Test assistant message with credits and tokens"""
        message = AIMessage.objects.create(
            conversation=self.conversation,
            role='assistant',
            type='analysis',
            content='Your top expenses are...',
            credits_used=5,
            tokens_used=1500,
            model_used='gpt-4-turbo-preview'
        )
        
        self.assertEqual(message.role, 'assistant')
        self.assertEqual(message.type, 'analysis')
        self.assertEqual(message.credits_used, 5)
        self.assertEqual(message.tokens_used, 1500)
        self.assertEqual(message.model_used, 'gpt-4-turbo-preview')
    
    def test_message_with_structured_data(self):
        """Test message with structured data for charts"""
        structured_data = {
            'chart_type': 'pie',
            'data': [
                {'category': 'Salaries', 'value': 45000},
                {'category': 'Rent', 'value': 15000},
                {'category': 'Supplies', 'value': 10000}
            ]
        }
        
        message = AIMessage.objects.create(
            conversation=self.conversation,
            role='assistant',
            type='chart',
            content='Here is your expense breakdown',
            structured_data=structured_data
        )
        
        self.assertEqual(message.structured_data['chart_type'], 'pie')
        self.assertEqual(len(message.structured_data['data']), 3)
    
    def test_message_feedback(self):
        """Test user feedback on messages"""
        message = AIMessage.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Analysis complete'
        )
        
        # Add feedback
        message.helpful = True
        message.user_feedback = 'Very helpful analysis!'
        message.save()
        
        self.assertTrue(message.helpful)
        self.assertEqual(message.user_feedback, 'Very helpful analysis!')


class AIInsightModelTest(TestCase):
    """Test AIInsight model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user
        )
    
    def test_create_insight(self):
        """Test creating AI insight"""
        insight = AIInsight.objects.create(
            company=self.company,
            type='cost_saving',
            priority='high',
            title='Reduce supplier costs',
            description='You can save 15% by renegotiating with Supplier X',
            potential_impact=Decimal('5000.00')
        )
        
        self.assertEqual(insight.company, self.company)
        self.assertEqual(insight.type, 'cost_saving')
        self.assertEqual(insight.priority, 'high')
        self.assertEqual(insight.status, 'new')
        self.assertEqual(insight.potential_impact, Decimal('5000.00'))
    
    def test_insight_action_items(self):
        """Test insight with action items"""
        actions = [
            'Contact Supplier X for negotiation',
            'Compare prices with 3 alternatives',
            'Review contract terms'
        ]
        
        insight = AIInsight.objects.create(
            company=self.company,
            type='opportunity',
            priority='medium',
            title='Optimize inventory',
            description='Inventory optimization opportunity',
            action_items=actions
        )
        
        self.assertEqual(len(insight.action_items), 3)
        self.assertIn('Contact Supplier X for negotiation', insight.action_items)
    
    def test_insight_status_workflow(self):
        """Test insight status workflow"""
        insight = AIInsight.objects.create(
            company=self.company,
            type='risk',
            priority='critical',
            title='Cash flow risk',
            description='Low cash reserves detected'
        )
        
        # Progress through statuses
        statuses = ['new', 'viewed', 'in_progress', 'completed']
        for status in statuses:
            insight.status = status
            insight.save()
            self.assertEqual(insight.status, status)
        
        # Test viewed timestamp
        insight.status = 'viewed'
        insight.viewed_at = timezone.now()
        insight.save()
        self.assertIsNotNone(insight.viewed_at)
    
    def test_insight_impact_tracking(self):
        """Test tracking actual impact vs potential"""
        insight = AIInsight.objects.create(
            company=self.company,
            type='cost_saving',
            priority='high',
            title='Reduce costs',
            description='Cost reduction opportunity',
            potential_impact=Decimal('10000.00')
        )
        
        # Mark as completed with actual impact
        insight.status = 'completed'
        insight.action_taken = True
        insight.action_taken_at = timezone.now()
        insight.actual_impact = Decimal('8500.00')
        insight.user_feedback = 'Saved R$ 8,500 following the recommendation'
        insight.save()
        
        self.assertTrue(insight.action_taken)
        self.assertIsNotNone(insight.action_taken_at)
        self.assertEqual(insight.actual_impact, Decimal('8500.00'))
        
        # Calculate effectiveness
        effectiveness = (insight.actual_impact / insight.potential_impact) * 100
        self.assertEqual(effectiveness, 85)  # 85% of predicted savings
    
    def test_insight_expiration(self):
        """Test insight expiration"""
        # Create insight that expires in 7 days
        expires_at = timezone.now() + timedelta(days=7)
        
        insight = AIInsight.objects.create(
            company=self.company,
            type='opportunity',
            priority='low',
            title='Limited time offer',
            description='Special pricing available',
            expires_at=expires_at
        )
        
        self.assertIsNotNone(insight.expires_at)
        self.assertGreater(insight.expires_at, timezone.now())
    
    def test_automated_vs_manual_insights(self):
        """Test differentiating automated vs manual insights"""
        # Automated insight
        auto_insight = AIInsight.objects.create(
            company=self.company,
            type='anomaly',
            priority='high',
            title='Unusual transaction detected',
            description='Large payment outside normal pattern',
            is_automated=True
        )
        
        # Manual insight (from conversation)
        manual_insight = AIInsight.objects.create(
            company=self.company,
            type='growth',
            priority='medium',
            title='Expansion opportunity',
            description='Market analysis suggests expansion',
            is_automated=False
        )
        
        self.assertTrue(auto_insight.is_automated)
        self.assertFalse(manual_insight.is_automated)