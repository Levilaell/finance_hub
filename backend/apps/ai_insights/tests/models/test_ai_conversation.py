"""
Unit tests for AIConversation and AIMessage models
Tests conversation management, message handling, and relationships
"""
import pytest
import json
from datetime import timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.companies.models import Company
from apps.ai_insights.models import (
    AIConversation, 
    AIMessage, 
    AICredit,
    AICreditTransaction
)

User = get_user_model()


class TestAIConversation(TestCase):
    """Test AIConversation model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser_conv',
            email='test@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            trade_name='Test Company Ltd'
        )
    
    def test_create_conversation(self):
        """Test creating AIConversation instance"""
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Financial Analysis Chat',
            status='active'
        )
        
        self.assertEqual(conversation.company, self.company)
        self.assertEqual(conversation.user, self.user)
        self.assertEqual(conversation.title, 'Financial Analysis Chat')
        self.assertEqual(conversation.status, 'active')
        self.assertEqual(conversation.message_count, 0)
        self.assertEqual(conversation.total_credits_used, 0)
        self.assertIsNotNone(conversation.created_at)
        self.assertIsNotNone(conversation.updated_at)
        self.assertIsNone(conversation.last_message_at)
    
    def test_conversation_str_representation(self):
        """Test string representation of conversation"""
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Cash Flow Analysis'
        )
        
        expected = f"Cash Flow Analysis - {self.user.email}"
        self.assertEqual(str(conversation), expected)
    
    def test_conversation_status_choices(self):
        """Test conversation status choices"""
        valid_statuses = ['active', 'archived', 'deleted']
        
        for status in valid_statuses:
            # Test that the conversation can be created and saved
            conversation = AIConversation.objects.create(
                company=self.company,
                user=self.user,
                title=f'Test {status}',
                status=status,
                financial_context={'test': True},
                settings={'test': True}
            )
            # Verify the conversation was created successfully
            self.assertEqual(conversation.status, status)
    
    def test_conversation_financial_context(self):
        """Test financial context JSON field"""
        financial_context = {
            'company': {
                'name': 'Test Company',
                'sector': 'Technology',
                'employees': 10
            },
            'accounts': {
                'total_balance': 50000.00,
                'count': 3
            },
            'current_month': {
                'income': 75000.00,
                'expenses': -45000.00,
                'net': 30000.00
            }
        }
        
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Context Test',
            financial_context=financial_context
        )
        
        self.assertEqual(
            conversation.financial_context['company']['name'], 
            'Test Company'
        )
        self.assertEqual(
            conversation.financial_context['accounts']['total_balance'], 
            50000.00
        )
    
    def test_conversation_settings(self):
        """Test conversation settings JSON field"""
        settings = {
            'ai_persona': 'financial_advisor',
            'language': 'pt-BR',
            'analysis_depth': 'detailed',
            'include_charts': True,
            'notification_preferences': {
                'new_insights': True,
                'critical_alerts': True
            }
        }
        
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Settings Test',
            settings=settings
        )
        
        self.assertEqual(conversation.settings['ai_persona'], 'financial_advisor')
        self.assertTrue(conversation.settings['include_charts'])
        self.assertTrue(
            conversation.settings['notification_preferences']['new_insights']
        )
    
    def test_conversation_ordering(self):
        """Test conversations are ordered by updated_at"""
        # Create conversations with delays
        older_conv = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Older Conversation'
        )
        
        newer_conv = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Newer Conversation'
        )
        
        # Query conversations
        conversations = list(
            AIConversation.objects.filter(company=self.company)
        )
        
        # Should be ordered by -updated_at (newest first)
        self.assertEqual(conversations[0], newer_conv)
        self.assertEqual(conversations[1], older_conv)
    
    def test_conversation_company_relationship(self):
        """Test conversation-company relationship"""
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Company Relationship Test'
        )
        
        # Test forward relationship
        self.assertEqual(conversation.company, self.company)
        
        # Test reverse relationship
        company_conversations = self.company.ai_conversations.all()
        self.assertIn(conversation, company_conversations)
    
    def test_conversation_user_relationship(self):
        """Test conversation-user relationship"""
        conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='User Relationship Test'
        )
        
        # Test forward relationship
        self.assertEqual(conversation.user, self.user)
        
        # Test reverse relationship
        user_conversations = self.user.ai_conversations.all()
        self.assertIn(conversation, user_conversations)
    
    def test_conversation_indexes(self):
        """Test database indexes"""
        # Create multiple conversations
        for i in range(5):
            status = 'active' if i < 3 else 'archived'
            AIConversation.objects.create(
                company=self.company,
                user=self.user,
                title=f'Conversation {i}',
                status=status
            )
        
        # Test company + status index
        active_conversations = AIConversation.objects.filter(
            company=self.company,
            status='active'
        )
        self.assertEqual(active_conversations.count(), 3)
        
        # Test user index
        user_conversations = AIConversation.objects.filter(user=self.user)
        self.assertEqual(user_conversations.count(), 5)


class TestAIMessage(TestCase):
    """Test AIMessage model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser_msg',
            email='test@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            trade_name='Test Company Ltd'
        )
        self.conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Conversation'
        )
    
    def test_create_user_message(self):
        """Test creating user message"""
        message = AIMessage.objects.create(
            conversation=self.conversation,
            role='user',
            type='text',
            content='What are my biggest expenses this month?'
        )
        
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.type, 'text')
        self.assertEqual(message.credits_used, 0)
        self.assertEqual(message.tokens_used, 0)
        self.assertIsNotNone(message.created_at)
    
    def test_create_assistant_message(self):
        """Test creating assistant message"""
        structured_data = {
            'chart_data': [
                {'category': 'Rent', 'amount': 5000},
                {'category': 'Utilities', 'amount': 800},
                {'category': 'Supplies', 'amount': 1200}
            ],
            'chart_type': 'pie'
        }
        
        insights = [
            {
                'type': 'cost_saving',
                'title': 'High utility costs detected',
                'potential_impact': 200.00
            }
        ]
        
        message = AIMessage.objects.create(
            conversation=self.conversation,
            role='assistant',
            type='analysis',
            content='Your biggest expenses this month are rent (R$ 5,000), supplies (R$ 1,200), and utilities (R$ 800).',
            credits_used=3,
            tokens_used=150,
            model_used='gpt-4o-mini',
            structured_data=structured_data,
            insights=insights
        )
        
        self.assertEqual(message.role, 'assistant')
        self.assertEqual(message.type, 'analysis')
        self.assertEqual(message.credits_used, 3)
        self.assertEqual(message.tokens_used, 150)
        self.assertEqual(message.model_used, 'gpt-4o-mini')
        self.assertEqual(len(message.structured_data['chart_data']), 3)
        self.assertEqual(message.insights[0]['type'], 'cost_saving')
    
    def test_message_str_representation(self):
        """Test string representation of message"""
        message = AIMessage.objects.create(
            conversation=self.conversation,
            role='user',
            content='This is a test message with some content to check truncation'
        )
        
        expected = "Usuário: This is a test message with some content to check..."
        self.assertEqual(str(message), expected)
    
    def test_message_role_choices(self):
        """Test message role choices"""
        valid_roles = ['user', 'assistant', 'system']
        
        for role in valid_roles:
            message = AIMessage(
                conversation=self.conversation,
                role=role,
                content=f'Test {role} message'
            )
            # Should not raise validation error
            message.full_clean()
    
    def test_message_type_choices(self):
        """Test message type choices"""
        valid_types = ['text', 'analysis', 'report', 'chart', 'alert']
        
        for message_type in valid_types:
            message = AIMessage(
                conversation=self.conversation,
                role='assistant',
                type=message_type,
                content=f'Test {message_type} message'
            )
            # Should not raise validation error
            message.full_clean()
    
    def test_message_ordering(self):
        """Test messages are ordered by created_at"""
        # Create messages in sequence
        msg1 = AIMessage.objects.create(
            conversation=self.conversation,
            role='user',
            content='First message'
        )
        
        msg2 = AIMessage.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Second message'
        )
        
        msg3 = AIMessage.objects.create(
            conversation=self.conversation,
            role='user',
            content='Third message'
        )
        
        # Query messages
        messages = list(self.conversation.messages.all())
        
        # Should be ordered by created_at (oldest first)
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)
        self.assertEqual(messages[2], msg3)
    
    def test_message_feedback(self):
        """Test message feedback functionality"""
        message = AIMessage.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='AI response to test feedback',
            credits_used=2
        )
        
        # Add positive feedback
        message.helpful = True
        message.user_feedback = 'Very helpful analysis, thank you!'
        message.save()
        
        self.assertTrue(message.helpful)
        self.assertEqual(message.user_feedback, 'Very helpful analysis, thank you!')
        
        # Update to negative feedback
        message.helpful = False
        message.user_feedback = 'Not quite what I was looking for.'
        message.save()
        
        self.assertFalse(message.helpful)
        self.assertEqual(message.user_feedback, 'Not quite what I was looking for.')
    
    def test_message_structured_data(self):
        """Test structured data field functionality"""
        chart_data = {
            'type': 'line_chart',
            'title': 'Revenue Trend',
            'data': [
                {'month': 'Jan', 'revenue': 45000},
                {'month': 'Feb', 'revenue': 52000},
                {'month': 'Mar', 'revenue': 48000}
            ],
            'options': {
                'currency': 'BRL',
                'show_trend': True
            }
        }
        
        message = AIMessage.objects.create(
            conversation=self.conversation,
            role='assistant',
            type='chart',
            content='Here is your revenue trend for the last 3 months.',
            structured_data=chart_data
        )
        
        self.assertEqual(message.structured_data['type'], 'line_chart')
        self.assertEqual(len(message.structured_data['data']), 3)
        self.assertTrue(message.structured_data['options']['show_trend'])
    
    def test_message_insights_field(self):
        """Test insights field functionality"""
        insights = [
            {
                'id': 'insight_1',
                'type': 'trend',
                'title': 'Revenue growth detected',
                'priority': 'medium',
                'potential_impact': 5000.00
            },
            {
                'id': 'insight_2',
                'type': 'opportunity',
                'title': 'Cost optimization opportunity',
                'priority': 'high',
                'potential_impact': 2500.00
            }
        ]
        
        message = AIMessage.objects.create(
            conversation=self.conversation,
            role='assistant',
            type='analysis',
            content='Analysis complete with 2 insights generated.',
            insights=insights
        )
        
        self.assertEqual(len(message.insights), 2)
        self.assertEqual(message.insights[0]['type'], 'trend')
        self.assertEqual(message.insights[1]['priority'], 'high')


class TestConversationMessageIntegration(TestCase):
    """Test integration between conversations and messages"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser_intg',
            email='integration@example.com',
            password='testpass123'
        )
        self.company = Company.objects.create(
            owner=self.user,
            name='Integration Test Company',
            trade_name='Integration Test Company Ltd'
        )
        self.conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Integration Test Chat'
        )
    
    def test_conversation_message_cascade_deletion(self):
        """Test cascade deletion of messages when conversation is deleted"""
        # Create messages
        msg1 = AIMessage.objects.create(
            conversation=self.conversation,
            role='user',
            content='Test message 1'
        )
        
        msg2 = AIMessage.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Test response 1'
        )
        
        message_ids = [msg1.id, msg2.id]
        
        # Delete conversation
        self.conversation.delete()
        
        # Messages should be cascade deleted
        for msg_id in message_ids:
            with self.assertRaises(AIMessage.DoesNotExist):
                AIMessage.objects.get(id=msg_id)
    
    def test_conversation_metrics_update(self):
        """Test conversation metrics are updated with messages"""
        # Initial state
        self.assertEqual(self.conversation.message_count, 0)
        self.assertEqual(self.conversation.total_credits_used, 0)
        self.assertIsNone(self.conversation.last_message_at)
        
        # Create user message
        user_msg = AIMessage.objects.create(
            conversation=self.conversation,
            role='user',
            content='Calculate my monthly expenses'
        )
        
        # Create AI response
        ai_msg = AIMessage.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Your monthly expenses total R$ 15,000',
            credits_used=5,
            tokens_used=200
        )
        
        # Manually update conversation metrics (as would be done in service)
        self.conversation.message_count = 2
        self.conversation.total_credits_used += ai_msg.credits_used
        self.conversation.last_message_at = ai_msg.created_at
        self.conversation.save()
        
        # Verify updates
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.message_count, 2)
        self.assertEqual(self.conversation.total_credits_used, 5)
        self.assertIsNotNone(self.conversation.last_message_at)
    
    def test_conversation_message_relationship(self):
        """Test conversation-message relationship"""
        # Create multiple messages
        messages = []
        for i in range(3):
            msg = AIMessage.objects.create(
                conversation=self.conversation,
                role='user' if i % 2 == 0 else 'assistant',
                content=f'Message {i+1}',
                credits_used=2 if i % 2 == 1 else 0
            )
            messages.append(msg)
        
        # Test forward relationship
        conversation_messages = list(self.conversation.messages.all())
        self.assertEqual(len(conversation_messages), 3)
        
        # Test reverse relationship
        for msg in messages:
            self.assertEqual(msg.conversation, self.conversation)
    
    def test_message_query_performance(self):
        """Test efficient querying of messages"""
        # Create conversation with many messages
        for i in range(20):
            AIMessage.objects.create(
                conversation=self.conversation,
                role='user' if i % 2 == 0 else 'assistant',
                content=f'Performance test message {i}',
                credits_used=1 if i % 2 == 1 else 0
            )
        
        # Test efficient pagination query
        recent_messages = list(
            self.conversation.messages.select_related('conversation')
            .order_by('-created_at')[:10]
        )
        
        self.assertEqual(len(recent_messages), 10)
        
        # Test conversation index query
        conv_messages = AIMessage.objects.filter(
            conversation=self.conversation
        ).count()
        
        self.assertEqual(conv_messages, 20)