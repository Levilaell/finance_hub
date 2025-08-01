"""
Unit tests for AIService
Tests AI message processing, insight generation, and OpenAI integration
"""
import pytest
import json
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.companies.models import Company
from apps.banking.models import BankAccount, Transaction
from apps.ai_insights.models import (
    AIConversation, 
    AIMessage, 
    AICredit,
    AICreditTransaction,
    AIInsight
)
from apps.ai_insights.services.ai_service import AIService
from apps.ai_insights.services.credit_service import InsufficientCreditsError
from apps.ai_insights.services.openai_wrapper import OpenAIError

User = get_user_model()


class TestAIService(TestCase):
    """Test AIService functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(
            name='Test Company',
            business_sector='Technology',
            employee_count=15,
            monthly_revenue=Decimal('75000.00')
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Conversation',
            financial_context={
                'company': {'name': 'Test Company', 'sector': 'Technology'},
                'current_month': {'income': 75000, 'expense': -45000, 'net': 30000}
            }
        )
        
        self.credit = AICredit.objects.create(
            company=self.company,
            balance=100,
            monthly_allowance=50
        )
    
    def test_model_costs_configuration(self):
        """Test AI model costs are properly configured"""
        expected_costs = {
            'gpt-4o': 5,
            'gpt-4o-mini': 1
        }
        
        self.assertEqual(AIService.MODEL_COSTS, expected_costs)
    
    def test_system_prompts_configuration(self):
        """Test system prompts are properly configured"""
        self.assertIn('financial_advisor', AIService.SYSTEM_PROMPTS)
        self.assertIn('analysis', AIService.SYSTEM_PROMPTS)
        self.assertIn('recommendation', AIService.SYSTEM_PROMPTS)
        
        # Verify prompts contain expected content
        advisor_prompt = AIService.SYSTEM_PROMPTS['financial_advisor']
        self.assertIn('consultor financeiro', advisor_prompt)
        self.assertIn('brasileiro', advisor_prompt)
    
    @patch('apps.ai_insights.services.ai_service.openai_wrapper')
    @patch('apps.ai_insights.services.ai_service.CreditService')
    def test_process_message_success(self, mock_credit_service, mock_openai):
        """Test successful message processing"""
        # Mock credit service
        mock_credit_service.use_credits.return_value = {
            'credits_remaining': 95,
            'transaction': Mock()
        }
        
        # Mock OpenAI response
        mock_openai.create_completion.return_value = {
            'content': 'Based on your financial data, your expenses are well controlled.',
            'usage': {'total_tokens': 150},
            'model': 'gpt-4o-mini'
        }
        
        # Process message
        result = AIService.process_message(
            conversation=self.conversation,
            user_message='How are my expenses this month?',
            context_data={},
            request_type='general'
        )
        
        # Verify result structure
        self.assertIn('ai_message', result)
        self.assertIn('credits_used', result)
        self.assertIn('credits_remaining', result)
        self.assertIn('insights', result)
        
        # Verify AI message was created
        ai_message = result['ai_message']
        self.assertIsInstance(ai_message, AIMessage)
        self.assertEqual(ai_message.role, 'assistant')
        self.assertEqual(ai_message.conversation, self.conversation)
        self.assertEqual(ai_message.credits_used, 1)  # gpt-4o-mini cost
        
        # Verify credits were used
        mock_credit_service.use_credits.assert_called_once()
        
        # Verify OpenAI was called
        mock_openai.create_completion.assert_called_once()
    
    @patch('apps.ai_insights.services.ai_service.openai_wrapper')
    @patch('apps.ai_insights.services.ai_service.CreditService')
    def test_process_message_with_analysis_type(self, mock_credit_service, mock_openai):
        """Test processing analysis type message uses more expensive model"""
        # Mock credit service
        mock_credit_service.use_credits.return_value = {
            'credits_remaining': 90,
            'transaction': Mock()
        }
        
        # Mock OpenAI response
        mock_openai.create_completion.return_value = {
            'content': 'Detailed financial analysis: Your cash flow shows...',
            'usage': {'total_tokens': 500},
            'model': 'gpt-4o'
        }
        
        # Process analysis message
        result = AIService.process_message(
            conversation=self.conversation,
            user_message='Provide detailed analysis of my financial situation',
            context_data={},
            request_type='analysis'
        )
        
        # Verify more expensive model was used
        ai_message = result['ai_message']
        self.assertEqual(ai_message.credits_used, 5)  # gpt-4o cost
        
        # Verify OpenAI was called with correct model
        call_args = mock_openai.create_completion.call_args
        self.assertEqual(call_args[1]['model'], 'gpt-4o')
    
    @patch('apps.ai_insights.services.ai_service.CreditService')
    def test_process_message_insufficient_credits(self, mock_credit_service):
        """Test handling insufficient credits"""
        # Mock insufficient credits
        mock_credit_service.use_credits.side_effect = InsufficientCreditsError(
            "Insufficient credits"
        )
        
        # Should raise exception
        with self.assertRaises(InsufficientCreditsError):
            AIService.process_message(
                conversation=self.conversation,
                user_message='Test message',
                context_data={},
                request_type='general'
            )
    
    @patch('apps.ai_insights.services.ai_service.openai_wrapper')
    @patch('apps.ai_insights.services.ai_service.CreditService')
    def test_process_message_with_fallback(self, mock_credit_service, mock_openai):
        """Test handling OpenAI service fallback"""
        # Mock credit service
        mock_credit_service.use_credits.return_value = {
            'credits_remaining': 95,
            'transaction': Mock()
        }
        mock_credit_service.add_credits.return_value = None
        
        # Mock fallback response
        mock_openai.create_completion.return_value = {
            'content': 'Service temporarily unavailable. Please try again later.',
            'usage': {'total_tokens': 50},
            'model': 'fallback',
            'is_fallback': True
        }
        
        # Process message
        result = AIService.process_message(
            conversation=self.conversation,
            user_message='Test message',
            context_data={},
            request_type='general'
        )
        
        # Verify fallback behavior
        self.assertTrue(result['is_fallback'])
        self.assertEqual(result['credits_used'], 0)  # Credits refunded
        
        # Verify credits were refunded
        mock_credit_service.add_credits.assert_called_once()
    
    @patch('apps.ai_insights.services.ai_service.openai_wrapper')
    @patch('apps.ai_insights.services.ai_service.CreditService')
    def test_process_message_openai_error(self, mock_credit_service, mock_openai):
        """Test handling OpenAI API errors"""
        # Mock credit service
        mock_credit_service.use_credits.return_value = {
            'credits_remaining': 95,
            'transaction': Mock()
        }
        mock_credit_service.add_credits.return_value = None
        
        # Mock OpenAI error
        mock_openai.create_completion.side_effect = OpenAIError("API rate limit exceeded")
        
        # Should raise OpenAI error after refunding credits
        with self.assertRaises(OpenAIError):
            AIService.process_message(
                conversation=self.conversation,
                user_message='Test message',
                context_data={},
                request_type='general'
            )
        
        # Verify credits were refunded
        mock_credit_service.add_credits.assert_called_once()
    
    def test_prepare_messages_basic(self):
        """Test message preparation for OpenAI"""
        with patch('apps.ai_insights.services.ai_service.CacheService.get_financial_context') as mock_cache:
            mock_cache.return_value = {
                'company': {'name': 'Test Company', 'sector': 'Tech'},
                'accounts': {'total_balance': 50000, 'count': 2}
            }
            
            messages = AIService._prepare_messages(
                conversation=self.conversation,
                user_message='What is my current financial situation?',
                context_data={},
                request_type='general'
            )
            
            # Verify message structure
            self.assertIsInstance(messages, list)
            self.assertTrue(len(messages) >= 3)  # System prompt + context + user message
            
            # Verify system prompt
            self.assertEqual(messages[0]['role'], 'system')
            self.assertIn('consultor financeiro', messages[0]['content'])
            
            # Verify financial context
            self.assertEqual(messages[1]['role'], 'system')
            self.assertIn('Contexto financeiro atual', messages[1]['content'])
            
            # Verify user message
            self.assertEqual(messages[-1]['role'], 'user')
            self.assertEqual(messages[-1]['content'], 'What is my current financial situation?')
    
    def test_prepare_messages_with_history(self):
        """Test message preparation includes conversation history"""
        # Create message history
        AIMessage.objects.create(
            conversation=self.conversation,
            role='user',
            content='Previous user message'
        )
        
        AIMessage.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Previous AI response'
        )
        
        with patch('apps.ai_insights.services.ai_service.CacheService.get_financial_context') as mock_cache:
            mock_cache.return_value = {}
            
            messages = AIService._prepare_messages(
                conversation=self.conversation,
                user_message='Current user message',
                context_data={},
                request_type='general'
            )
            
            # Should include history messages
            user_messages = [msg for msg in messages if msg['role'] == 'user']
            assistant_messages = [msg for msg in messages if msg['role'] == 'assistant']
            
            self.assertEqual(len(user_messages), 2)  # Previous + current
            self.assertEqual(len(assistant_messages), 1)  # Previous
    
    def test_format_financial_context_complete(self):
        """Test financial context formatting with complete data"""
        context = {
            'company': {
                'name': 'Test Corp',
                'sector': 'Technology',
                'employees': 25,
                'monthly_revenue': 100000.00
            },
            'accounts': {
                'total_balance': 75000.00,
                'count': 3
            },
            'current_month': {
                'income': 120000.00,
                'expense': -85000.00,
                'net': 35000.00,
                'transactions': 45
            },
            'last_month': {
                'income': 110000.00,
                'expense': -80000.00,
                'net': 30000.00
            },
            'top_expenses': [
                {'category': 'Salaries', 'total': -45000.00},
                {'category': 'Rent', 'total': -15000.00}
            ]
        }
        
        formatted = AIService._format_financial_context(context)
        
        # Verify all sections are included
        self.assertIn('Test Corp', formatted)
        self.assertIn('Technology', formatted)
        self.assertIn('R$ 100.000,00', formatted)
        self.assertIn('3 contas', formatted)
        self.assertIn('Receitas: R$ 120.000,00', formatted)
        self.assertIn('Principais despesas:', formatted)
        self.assertIn('Salaries: R$ 45.000,00', formatted)
    
    def test_format_financial_context_empty(self):
        """Test financial context formatting with no data"""
        context = {}
        formatted = AIService._format_financial_context(context)
        
        self.assertEqual(formatted, "Sem dados financeiros disponíveis")
    
    def test_detect_insights_in_content_critical(self):
        """Test insight detection for critical content"""
        content = "URGENTE: Seu fluxo de caixa está crítico. Você tem apenas R$ 5.000 em reservas e despesas mensais de R$ 25.000. Ação imediata necessária."
        
        insights = AIService._detect_insights_in_content(
            content=content,
            conversation=self.conversation
        )
        
        # Should detect critical insight
        self.assertEqual(len(insights), 1)
        insight = insights[0]
        self.assertEqual(insight.priority, 'critical')
        self.assertEqual(insight.company, self.company)
        self.assertTrue(insight.is_automated)
    
    def test_detect_insights_in_content_with_monetary_values(self):
        """Test insight detection extracts monetary values"""
        content = "Você pode economizar R$ 15.000 por mês otimizando seus processos. Esta é uma oportunidade significativa."
        
        insights = AIService._detect_insights_in_content(
            content=content,
            conversation=self.conversation
        )
        
        # Should detect insight with potential impact
        self.assertEqual(len(insights), 1)
        insight = insights[0]
        self.assertEqual(insight.potential_impact, 15000.00)
        self.assertEqual(insight.type, 'opportunity')
    
    def test_detect_insights_in_content_no_trigger(self):
        """Test insight detection when no triggers are found"""
        content = "Seus números estão normais. Continue acompanhando mensalmente."
        
        insights = AIService._detect_insights_in_content(
            content=content,
            conversation=self.conversation
        )
        
        # Should not detect any insights
        self.assertEqual(len(insights), 0)
    
    @patch('apps.ai_insights.services.ai_service.AnomalyDetectionService')
    def test_generate_automated_insights(self, mock_anomaly_service):
        """Test automated insight generation"""
        # Create bank accounts and transactions for the company
        account = BankAccount.objects.create(
            company=self.company,
            name='Main Account',
            account_type='checking',
            balance=25000.00
        )
        
        Transaction.objects.create(
            company=self.company,
            bank_account=account,
            description='Office Rent',
            amount=-5000.00,
            date=timezone.now().date()
        )
        
        # Mock anomaly service
        mock_anomaly_instance = Mock()
        mock_anomaly_instance.generate_automated_insights.return_value = [
            {
                'type': 'anomaly',
                'priority': 'high',
                'title': 'Unusual transaction detected',
                'description': 'Large expense outside normal pattern',
                'action_items': ['Review transaction details'],
                'potential_impact': 1000.00,
                'data_context': {'transaction_id': 123}
            }
        ]
        mock_anomaly_service.return_value = mock_anomaly_instance
        
        # Generate insights
        insights = AIService.generate_automated_insights(self.company)
        
        # Verify insights were generated
        self.assertTrue(len(insights) > 0)
        
        # Find the anomaly insight
        anomaly_insights = [i for i in insights if i.type == 'anomaly']
        self.assertTrue(len(anomaly_insights) > 0)
    
    def test_analyze_cash_flow_critical(self):
        """Test cash flow analysis detects critical situation"""
        # Create bank account with low balance
        BankAccount.objects.create(
            company=self.company,
            name='Main Account',
            account_type='checking',
            balance=5000.00,  # Low balance
            is_active=True
        )
        
        # Create high monthly expenses
        for i in range(30):  # 30 days of expenses
            Transaction.objects.create(
                company=self.company,
                description=f'Daily expense {i}',
                amount=-200.00,  # R$ 6,000 per month
                date=timezone.now().date()
            )
        
        # Analyze cash flow
        insight = AIService._analyze_cash_flow(self.company)
        
        # Should generate critical cash flow insight
        self.assertIsNotNone(insight)
        self.assertEqual(insight.type, 'cash_flow')
        self.assertEqual(insight.priority, 'critical')
        self.assertIn('crítico', insight.title)
    
    def test_analyze_cash_flow_healthy(self):
        """Test cash flow analysis with healthy situation"""
        # Create bank account with good balance
        BankAccount.objects.create(
            company=self.company,
            name='Main Account',
            account_type='checking',
            balance=50000.00,  # Good balance
            is_active=True
        )
        
        # Create moderate monthly expenses
        for i in range(10):
            Transaction.objects.create(
                company=self.company,
                description=f'Expense {i}',
                amount=-500.00,  # R$ 5,000 per month
                date=timezone.now().date()
            )
        
        # Analyze cash flow
        insight = AIService._analyze_cash_flow(self.company)
        
        # Should not generate insight for healthy cash flow
        self.assertIsNone(insight)
    
    def test_analyze_expenses_increase(self):
        """Test expense analysis detects increase"""
        from datetime import timedelta
        
        # Create historical expenses (lower)
        historical_date = timezone.now() - timedelta(days=60)
        for i in range(10):
            Transaction.objects.create(
                company=self.company,
                description=f'Historical expense {i}',
                amount=-1000.00,  # R$ 10,000 historical average
                date=historical_date.date()
            )
        
        # Create current month expenses (higher)
        current_date = timezone.now()
        for i in range(15):
            Transaction.objects.create(
                company=self.company,
                description=f'Current expense {i}',
                amount=-1500.00,  # R$ 22,500 current month (50% increase)
                date=current_date.date()
            )
        
        # Analyze expenses
        insights = AIService._analyze_expenses(self.company)
        
        # Should detect expense increase
        self.assertTrue(len(insights) > 0)
        expense_insight = insights[0]
        self.assertEqual(expense_insight.type, 'cost_saving')
        self.assertEqual(expense_insight.priority, 'high')
        self.assertIn('Aumento', expense_insight.title)
    
    def test_analyze_trends_revenue_decline(self):
        """Test trend analysis detects revenue decline"""
        from datetime import timedelta
        
        # Create declining revenue trend
        base_date = timezone.now().replace(day=1)
        
        # Older months (higher revenue)
        for month_offset in range(3, 6):
            month_date = base_date - timedelta(days=30 * month_offset)
            Transaction.objects.create(
                company=self.company,
                description=f'Revenue month {month_offset}',
                amount=50000.00,  # Higher revenue
                date=month_date.date()
            )
        
        # Recent months (lower revenue)
        for month_offset in range(0, 3):
            month_date = base_date - timedelta(days=30 * month_offset)
            Transaction.objects.create(
                company=self.company,
                description=f'Revenue month {month_offset}',
                amount=30000.00,  # Lower revenue (40% decline)
                date=month_date.date()
            )
        
        # Analyze trends
        insights = AIService._analyze_trends(self.company)
        
        # Should detect revenue decline
        self.assertTrue(len(insights) > 0)
        trend_insight = insights[0]
        self.assertEqual(trend_insight.type, 'trend')
        self.assertEqual(trend_insight.priority, 'high')
        self.assertIn('queda', trend_insight.title)


class TestAIServiceIntegration(TestCase):
    """Test AIService integration with other services"""
    
    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(
            name='Integration Test Company',
            business_sector='Services'
        )
        
        self.user = User.objects.create_user(
            email='integration@example.com',
            password='testpass123'
        )
        
        self.conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Integration Test'
        )
        
        self.credit = AICredit.objects.create(
            company=self.company,
            balance=50
        )
    
    @patch('apps.ai_insights.services.ai_service.openai_wrapper')
    @patch('apps.ai_insights.services.ai_service.CreditService')
    @patch('apps.ai_insights.services.ai_service.CacheService')
    def test_full_message_processing_workflow(self, mock_cache, mock_credit, mock_openai):
        """Test complete message processing workflow"""
        # Mock dependencies
        mock_cache.get_financial_context.return_value = {
            'company': {'name': 'Integration Test Company'},
            'current_month': {'income': 50000, 'expense': -30000}
        }
        
        mock_credit.use_credits.return_value = {
            'credits_remaining': 45,
            'transaction': Mock()
        }
        
        mock_openai.create_completion.return_value = {
            'content': 'Your financial situation looks stable with R$ 20,000 net income.',
            'usage': {'total_tokens': 120},
            'model': 'gpt-4o-mini'
        }
        
        # Process message
        result = AIService.process_message(
            conversation=self.conversation,
            user_message='How is my financial situation?',
            context_data={'analysis_type': 'overview'},
            request_type='general'
        )
        
        # Verify all integrations worked
        mock_cache.get_financial_context.assert_called_once()
        mock_credit.use_credits.assert_called_once()
        mock_openai.create_completion.assert_called_once()
        
        # Verify conversation metrics updated
        self.conversation.refresh_from_db()
        # Note: In real implementation, conversation metrics would be updated
        
        # Verify message created
        messages = AIMessage.objects.filter(conversation=self.conversation)
        self.assertEqual(messages.count(), 2)  # User + AI message