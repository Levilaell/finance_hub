"""
Comprehensive tests for AI Service
Testes abrangentes para o serviço de IA
"""
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock, Mock
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.companies.models import Company, SubscriptionPlan
from apps.ai_insights.models import AICredit, AICreditTransaction, AIConversation, AIMessage
from apps.ai_insights.services.ai_service import AIService
from apps.ai_insights.services.credit_service import InsufficientCreditsError

User = get_user_model()


class AIServiceComprehensiveTest(TestCase):
    """Comprehensive tests for AIService functionality"""
    
    def setUp(self):
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
            max_ai_requests_per_month=1000
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user,
            cnpj='12345678901234',
            company_type='ltda',
            business_sector='technology'
        )
        self.company.subscription_plan = self.plan
        self.company.subscription_status = 'active'
        self.company.save()
        
        self.conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Conversation'
        )
        
        # Create credit balance
        AICredit.objects.create(
            company=self.company,
            balance=100,
            monthly_allowance=100
        )
    
    @patch('apps.ai_insights.services.ai_service.openai.ChatCompletion.create')
    def test_process_message_success(self, mock_openai):
        """Test successful message processing"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='Your top expenses are salaries (50%) and rent (25%).'))
        ]
        mock_response.usage.total_tokens = 750
        mock_openai.return_value = mock_response
        
        # Process message
        result = AIService.process_message(
            conversation=self.conversation,
            user_message='What are my top expenses this month?',
            context_data=None,
            request_type='analysis'
        )
        
        # Verify response structure
        self.assertIn('ai_message', result)
        self.assertIn('credits_used', result)
        self.assertIn('credits_remaining', result)
        self.assertIn('insights', result)
        
        # Verify content
        self.assertEqual(result['ai_message'].content, 'Your top expenses are salaries (50%) and rent (25%).')
        self.assertGreater(result['credits_used'], 0)
        
        # Verify messages were saved
        messages = AIMessage.objects.filter(conversation=self.conversation)
        self.assertEqual(messages.count(), 2)  # User + Assistant
        
        user_msg = messages.filter(role='user').first()
        self.assertEqual(user_msg.content, 'What are my top expenses this month?')
        self.assertEqual(user_msg.type, 'text')
        
        assistant_msg = messages.filter(role='assistant').first()
        self.assertEqual(assistant_msg.content, 'Your top expenses are salaries (50%) and rent (25%).')
        self.assertEqual(assistant_msg.tokens_used, 750)
        self.assertGreater(assistant_msg.credits_used, 0)
    
    @patch('apps.ai_insights.services.ai_service.openai.ChatCompletion.create')
    def test_process_message_with_context_data(self, mock_openai):
        """Test message processing with context data"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='Based on your expense data, I recommend optimizing supplier costs.'))
        ]
        mock_response.usage.total_tokens = 1200
        mock_openai.return_value = mock_response
        
        # Context data
        context_data = {
            "total_expenses": 50000,
            "top_categories": ["Suppliers", "Rent", "Salaries"]
        }
        
        # Process message
        result = AIService.process_message(
            conversation=self.conversation,
            user_message='Analyze my expenses and give recommendations',
            context_data=context_data,
            request_type='analysis'
        )
        
        # Verify context was used
        self.assertIsNotNone(result['ai_message'])
        self.assertEqual(result['ai_message'].structured_data, context_data)
        
        # Verify message was saved with context
        assistant_msg = AIMessage.objects.filter(
            conversation=self.conversation,
            role='assistant'
        ).first()
        self.assertEqual(assistant_msg.structured_data, context_data)
    
    def test_process_message_insufficient_credits(self):
        """Test processing message with insufficient credits"""
        # Set low credit balance
        credit = AICredit.objects.get(company=self.company)
        credit.balance = 0
        credit.bonus_credits = 0
        credit.save()
        
        # Should raise InsufficientCreditsError
        with self.assertRaises(InsufficientCreditsError):
            AIService.process_message(
                conversation=self.conversation,
                user_message='Analyze my finances',
                request_type='analysis'
            )
    
    def test_model_costs_configuration(self):
        """Test AI model costs configuration"""
        # Verify model costs are properly configured
        self.assertIn('gpt-4o', AIService.MODEL_COSTS)
        self.assertIn('gpt-4o-mini', AIService.MODEL_COSTS)
        
        # Verify costs are reasonable
        self.assertGreater(AIService.MODEL_COSTS['gpt-4o'], AIService.MODEL_COSTS['gpt-4o-mini'])
        self.assertGreater(AIService.MODEL_COSTS['gpt-4o-mini'], 0)
    
    def test_system_prompts_configuration(self):
        """Test system prompts are properly configured"""
        # Verify all required prompts exist
        required_prompts = ['financial_advisor', 'analysis', 'recommendation']
        for prompt_key in required_prompts:
            self.assertIn(prompt_key, AIService.SYSTEM_PROMPTS)
            self.assertIsInstance(AIService.SYSTEM_PROMPTS[prompt_key], str)
            self.assertGreater(len(AIService.SYSTEM_PROMPTS[prompt_key]), 50)
    
    @patch('apps.ai_insights.services.cache_service.CacheService.get_financial_context')
    def test_format_financial_context(self, mock_cache):
        """Test formatting financial context for AI prompts"""
        # Mock cached financial context
        mock_context = {
            'company': {
                'name': 'Test Company',
                'sector': 'Technology',
                'employees': 50,
                'monthly_revenue': 100000.00
            },
            'accounts': {
                'count': 3,
                'total_balance': 75000.00
            },
            'current_month': {
                'income': 120000.00,
                'expense': -80000.00,
                'net': 40000.00,
                'transactions': 150
            },
            'last_month': {
                'income': 110000.00,
                'expense': -75000.00,
                'net': 35000.00
            },
            'top_expenses': [
                {'category': 'Salários', 'total': -45000.00},
                {'category': 'Aluguel', 'total': -15000.00}
            ]
        }
        mock_cache.return_value = mock_context
        
        # Test formatting
        formatted = AIService._format_financial_context(mock_context)
        
        # Verify content
        self.assertIn('Test Company', formatted)
        self.assertIn('Technology', formatted)
        self.assertIn('R$ 100,000.00', formatted)
        self.assertIn('Salários', formatted)
        self.assertIn('R$ 45,000.00', formatted)
    
    @patch('apps.banking.models.BankAccount.objects.filter')
    def test_generate_automated_insights(self, mock_bank_filter):
        """Test automated insight generation"""
        # Mock bank account data
        mock_accounts = MagicMock()
        mock_accounts.aggregate.return_value = {'total': Decimal('25000.00')}
        mock_bank_filter.return_value = mock_accounts
        
        # Mock transaction data for cash flow analysis
        with patch('apps.banking.models.Transaction.objects.filter') as mock_trans_filter:
            mock_transactions = MagicMock()
            mock_transactions.aggregate.return_value = {'total': Decimal('-90000.00')}
            mock_trans_filter.return_value = mock_transactions
            
            insights = AIService.generate_automated_insights(self.company)
            
            # Should return a list of insights
            self.assertIsInstance(insights, list)
            
            # If cash flow is critical, should generate cash flow insight
            if insights:
                cash_flow_insights = [i for i in insights if i.type == 'cash_flow']
                if cash_flow_insights:
                    insight = cash_flow_insights[0]
                    self.assertEqual(insight.priority, 'critical')
                    self.assertIn('Fluxo de caixa', insight.title)
    
    def test_get_functions_structure(self):
        """Test function definitions for OpenAI function calling"""
        functions = AIService._get_functions()
        
        # Should return a list of function definitions
        self.assertIsInstance(functions, list)
        self.assertGreater(len(functions), 0)
        
        # Check create_insight function
        create_insight = next((f for f in functions if f['name'] == 'create_insight'), None)
        self.assertIsNotNone(create_insight)
        self.assertIn('description', create_insight)
        self.assertIn('parameters', create_insight)
        
        # Check required parameters
        params = create_insight['parameters']
        self.assertIn('properties', params)
        self.assertIn('required', params)
        
        required_fields = ['type', 'priority', 'title', 'description', 'action_items']
        for field in required_fields:
            self.assertIn(field, params['required'])
    
    @patch('apps.ai_insights.services.ai_service.openai.ChatCompletion.create')
    @patch('apps.ai_insights.services.cache_service.CacheService.get_financial_context')
    def test_prepare_messages_with_context(self, mock_cache, mock_openai):
        """Test message preparation with financial context"""
        # Mock financial context
        mock_cache.return_value = {
            'company': {'name': 'Test Company'},
            'current_month': {'income': 50000, 'expense': -30000}
        }
        
        # Create some existing messages
        AIMessage.objects.create(
            conversation=self.conversation,
            role='user',
            content='What are my expenses?'
        )
        AIMessage.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Your main expenses are salaries and rent.'
        )
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='Based on your previous question...'))
        ]
        mock_response.usage.total_tokens = 800
        mock_openai.return_value = mock_response
        
        # Process follow-up message
        result = AIService.process_message(
            conversation=self.conversation,
            user_message='Can you give me more details?',
            request_type='general'
        )
        
        # Verify OpenAI was called with proper message structure
        self.assertTrue(mock_openai.called)
        call_args = mock_openai.call_args[1]
        messages_sent = call_args['messages']
        
        # Should include system messages + conversation history + new message
        self.assertGreater(len(messages_sent), 3)
        
        # Verify system prompts are included
        system_messages = [msg for msg in messages_sent if msg['role'] == 'system']
        self.assertGreater(len(system_messages), 0)
        
        # Last message should be the new user message
        last_message = messages_sent[-1]
        self.assertEqual(last_message['role'], 'user')
        self.assertEqual(last_message['content'], 'Can you give me more details?')
    
    def test_error_handling_openai_api_failure(self):
        """Test error handling when OpenAI API fails"""
        with patch('apps.ai_insights.services.ai_service.openai.ChatCompletion.create') as mock_openai:
            # Mock API failure
            mock_openai.side_effect = Exception("API Error")
            
            # Should handle error gracefully by raising the exception
            with self.assertRaises(Exception):
                AIService.process_message(
                    conversation=self.conversation,
                    user_message='Test message',
                    request_type='general'
                )
    
    def test_detect_insights_in_content(self):
        """Test automatic insight detection from AI response content"""
        # Content with critical keywords and monetary values
        content = """URGENTE: Sua empresa tem um risco crítico de fluxo de caixa. 
        Você pode economizar R$ 15.000,00 por mês renegociando contratos com fornecedores.
        É importante tomar ação imediata para evitar problemas de liquidez."""
        
        insights = AIService._detect_insights_in_content(content, self.conversation)
        
        # Should detect insight due to critical keywords and monetary value
        self.assertGreater(len(insights), 0)
        
        if insights:
            insight = insights[0]
            self.assertEqual(insight.company, self.company)
            self.assertEqual(insight.conversation, self.conversation)
            self.assertEqual(insight.priority, 'critical')
            self.assertEqual(insight.potential_impact, 15000.0)
            self.assertTrue(insight.is_automated)
    
    def test_process_function_call(self):
        """Test processing OpenAI function calls to create insights"""
        # Mock function call
        mock_function_call = MagicMock()
        mock_function_call.name = 'create_insight'
        mock_function_call.arguments = json.dumps({
            'type': 'cost_saving',
            'priority': 'high',
            'title': 'Optimize supplier costs',
            'description': 'Renegotiate contracts with top 3 suppliers',
            'action_items': ['Contact suppliers', 'Compare prices', 'Negotiate terms'],
            'potential_impact': 5000.0,
            'expires_days': 30
        })
        
        insights = AIService._process_function_call(mock_function_call, self.conversation)
        
        # Should create one insight
        self.assertEqual(len(insights), 1)
        
        insight = insights[0]
        self.assertEqual(insight.type, 'cost_saving')
        self.assertEqual(insight.priority, 'high')
        self.assertEqual(insight.title, 'Optimize supplier costs')
        self.assertEqual(insight.potential_impact, 5000.0)
        self.assertEqual(len(insight.action_items), 3)
        self.assertIsNotNone(insight.expires_at)