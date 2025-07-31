"""
Tests for AI Insights services
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.companies.models import Company, SubscriptionPlan
from apps.ai_insights.models import AICredit, AICreditTransaction, AIConversation, AIMessage
from apps.ai_insights.services.credit_service import CreditService, InsufficientCreditsError
from apps.ai_insights.services.ai_service import AIService

User = get_user_model()


class CreditServiceTest(TestCase):
    """Test CreditService functionality"""
    
    def setUp(self):
        self.service = CreditService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Professional',
            slug='professional',
            plan_type='professional',
            price_monthly=Decimal('99.90'),
            price_yearly=Decimal('999.00'),
            max_bank_accounts=10
        )
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user,
            cnpj='12345678901234',
            company_type='ltda',
            business_sector='technology'
        )
        # Set subscription plan on company
        self.company.subscription_plan = self.plan
        self.company.subscription_status = 'active'
        self.company.save()
    
    def test_check_credits(self):
        """Test checking credit availability"""
        # First call should create credits and return availability
        has_credits, message = self.service.check_credits(self.company)
        self.assertTrue(has_credits)
        self.assertIn('créditos disponíveis', message)
        
        # Verify credit was created
        credit = AICredit.objects.get(company=self.company)
        self.assertIsNotNone(credit)
    
    def test_check_credits_with_balance(self):
        """Test checking credits with existing balance"""
        # Create credit with balance
        AICredit.objects.create(
            company=self.company,
            balance=50
        )
        
        # Test sufficient credits
        has_credits, message = self.service.check_credits(self.company)
        self.assertTrue(has_credits)
        self.assertIn('50', message)
        
        # Test no credits
        credit = AICredit.objects.get(company=self.company)
        credit.balance = 0
        credit.bonus_credits = 0
        credit.save()
        
        has_credits, message = self.service.check_credits(self.company)
        self.assertFalse(has_credits)
        self.assertIn('Sem créditos', message)
    
    def test_use_credits(self):
        """Test using credits"""
        # Create initial balance
        credit = AICredit.objects.create(
            company=self.company,
            balance=50
        )
        
        # Use credits
        result = self.service.use_credits(
            company=self.company,
            amount=5,
            description='Test usage',
            metadata={'test': True}
        )
        
        self.assertEqual(result['credits_used'], 5)
        self.assertEqual(result['credits_remaining'], 45)
        
        # Check transaction was created
        transaction = result['transaction']
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, -5)
        self.assertEqual(transaction.balance_before, 50)
        self.assertEqual(transaction.balance_after, 45)
        self.assertTrue(transaction.metadata['test'])
    
    def test_use_credits_insufficient(self):
        """Test using credits with insufficient balance"""
        AICredit.objects.create(
            company=self.company,
            balance=3
        )
        
        # Try to use more than available
        with self.assertRaises(InsufficientCreditsError):
            self.service.use_credits(
                company=self.company,
                amount=5,
                description='Test usage'
            )
    
    def test_add_credits(self):
        """Test adding credits"""
        credit = AICredit.objects.create(
            company=self.company,
            balance=10
        )
        
        # Add purchased credits
        new_balance = self.service.add_credits(
            company=self.company,
            amount=100,
            transaction_type='purchase',
            description='Purchased 100 credits',
            metadata={'payment_id': 'pay_123'}
        )
        
        self.assertEqual(new_balance, 110)
        
        # Check credit was updated
        credit.refresh_from_db()
        self.assertEqual(credit.balance, 110)
        self.assertEqual(credit.total_purchased, 100)
        
        # Check transaction
        transaction = AICreditTransaction.objects.filter(
            company=self.company,
            type='purchase'
        ).first()
        
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, 100)
        self.assertEqual(transaction.metadata['payment_id'], 'pay_123')
    
    def test_monthly_credit_reset(self):
        """Test monthly credit reset functionality"""
        # Create old credit record
        old_date = timezone.now() - timezone.timedelta(days=35)
        credit = AICredit.objects.create(
            company=self.company,
            balance=5,
            monthly_allowance=100,
            last_reset=old_date
        )
        
        # Check credits should trigger reset
        has_credits, message = self.service.check_credits(self.company)
        
        # Verify reset occurred
        credit.refresh_from_db()
        self.assertEqual(credit.balance, 100)  # Reset to monthly allowance
        
        # Check transaction was created
        transaction = AICreditTransaction.objects.filter(
            company=self.company,
            type='monthly_reset'
        ).first()
        
        self.assertIsNotNone(transaction)
    
    def test_get_credit_history(self):
        """Test getting credit history and statistics"""
        # Create some transactions
        AICredit.objects.create(
            company=self.company,
            balance=50,
            monthly_allowance=100,
            total_purchased=200
        )
        
        AICreditTransaction.objects.create(
            company=self.company,
            type='usage',
            amount=-5,
            balance_before=50,
            balance_after=45,
            description='Test usage'
        )
        
        # Get history
        history = self.service.get_credit_history(self.company, days=30)
        
        self.assertEqual(history['current_balance'], 50)
        self.assertEqual(history['monthly_allowance'], 100)
        self.assertEqual(history['total_purchased'], 200)
        self.assertIn('usage', history['statistics'])


class AIServiceTest(TestCase):
    """Test AIService functionality"""
    
    def setUp(self):
        self.service = AIService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user,
            cnpj='12345678901234',
            company_type='ltda',
            business_sector='technology'
        )
        self.conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Conversation'
        )
        
        # Create credit balance
        AICredit.objects.create(
            company=self.company,
            balance=100
        )
    
    @patch('apps.ai_insights.services.ai_service.openai.OpenAI')
    def test_process_message(self, mock_openai_class):
        """Test processing a chat message"""
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='Your top expenses are salaries and rent.'))
        ]
        mock_response.usage.total_tokens = 500
        mock_client.chat.completions.create.return_value = mock_response
        
        # Process message
        result = self.service.process_message(
            company=self.company,
            user=self.user,
            conversation=self.conversation,
            message='What are my top expenses?'
        )
        
        self.assertIn('message_id', result)
        self.assertIn('content', result)
        self.assertEqual(result['content'], 'Your top expenses are salaries and rent.')
        self.assertIn('credits_used', result)
        self.assertGreater(result['credits_used'], 0)
        
        # Check message was saved
        messages = AIMessage.objects.filter(conversation=self.conversation)
        self.assertEqual(messages.count(), 2)  # User + Assistant
        
        user_msg = messages.filter(role='user').first()
        self.assertEqual(user_msg.content, 'What are my top expenses?')
        
        assistant_msg = messages.filter(role='assistant').first()
        self.assertEqual(assistant_msg.content, 'Your top expenses are salaries and rent.')
        self.assertEqual(assistant_msg.tokens_used, 500)
    
    @patch('apps.ai_insights.services.ai_service.openai.OpenAI')
    def test_process_message_insufficient_credits(self, mock_openai_class):
        """Test processing message with insufficient credits"""
        # Set low credit balance
        credit = AICredit.objects.get(company=self.company)
        credit.balance = 0
        credit.save()
        
        # Try to process message
        with self.assertRaises(InsufficientCreditsError):
            self.service.process_message(
                company=self.company,
                user=self.user,
                conversation=self.conversation,
                message='Analyze my finances'
            )
    
    def test_build_context(self):
        """Test building financial context"""
        # Mock financial data
        with patch.object(self.service, '_get_financial_summary') as mock_summary:
            mock_summary.return_value = {
                'current_balance': 50000.00,
                'monthly_income': 100000.00,
                'monthly_expenses': 80000.00,
                'top_expense_categories': [
                    {'name': 'Salaries', 'amount': 40000.00, 'percentage': 50.0}
                ]
            }
            
            context = self.service._build_context(self.company)
            
        self.assertIn('company_name', context)
        self.assertEqual(context['company_name'], 'Test Company')
        self.assertEqual(context['current_balance'], 50000.00)
        self.assertEqual(context['monthly_income'], 100000.00)
        self.assertIsInstance(context['top_expense_categories'], list)
    
    @patch('apps.ai_insights.services.ai_service.openai.OpenAI')
    def test_generate_automated_insights(self, mock_openai_class):
        """Test generating automated insights"""
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='''
            {
                "insights": [
                    {
                        "type": "cost_saving",
                        "priority": "high",
                        "title": "Reduce supplier costs",
                        "description": "Renegotiate with top 3 suppliers",
                        "potential_impact": 5000.00,
                        "action_items": ["Contact suppliers", "Compare alternatives"]
                    }
                ]
            }
            '''))
        ]
        mock_response.usage.total_tokens = 1000
        mock_client.chat.completions.create.return_value = mock_response
        
        insights = self.service.generate_automated_insights(self.company)
        
        self.assertIsInstance(insights, list)
        self.assertGreater(len(insights), 0)
        
        # Check insight structure
        insight = insights[0]
        self.assertEqual(insight['type'], 'cost_saving')
        self.assertEqual(insight['priority'], 'high')
        self.assertEqual(insight['potential_impact'], 5000.00)
        self.assertIsInstance(insight['action_items'], list)
    
    def test_calculate_credits_simple(self):
        """Test credit calculation for simple message"""
        credits = self.service._calculate_credits(
            request_type='general',
            tokens_used=500,
            has_analysis=False,
            insights_count=0
        )
        
        self.assertEqual(credits, 1)  # Base cost for general message
    
    def test_calculate_credits_with_analysis(self):
        """Test credit calculation with analysis"""
        credits = self.service._calculate_credits(
            request_type='analysis',
            tokens_used=2500,
            has_analysis=True,
            insights_count=3
        )
        
        # Base (3) + tokens (2) + insights (1.5) = 6.5 -> 7
        self.assertEqual(credits, 7)
    
    def test_calculate_credits_report(self):
        """Test credit calculation for report"""
        credits = self.service._calculate_credits(
            request_type='report',
            tokens_used=5000,
            has_analysis=True,
            insights_count=5
        )
        
        # Base (10) + tokens (5) + insights (2.5) = 17.5 -> 18
        self.assertEqual(credits, 18)
    
    @patch('apps.ai_insights.services.ai_service.requests.post')
    def test_moderate_content(self, mock_post):
        """Test content moderation"""
        # Mock moderation API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [{
                'flagged': False,
                'categories': {
                    'hate': False,
                    'violence': False,
                    'self-harm': False,
                    'sexual': False
                }
            }]
        }
        mock_post.return_value = mock_response
        
        is_safe = self.service._moderate_content("What are my expenses?")
        self.assertTrue(is_safe)
        
        # Test flagged content
        mock_response.json.return_value = {
            'results': [{
                'flagged': True,
                'categories': {'hate': True}
            }]
        }
        
        is_safe = self.service._moderate_content("Inappropriate content")
        self.assertFalse(is_safe)