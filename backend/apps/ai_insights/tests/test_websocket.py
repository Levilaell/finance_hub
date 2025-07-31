"""
WebSocket Tests for AI Insights
"""
import json
from unittest.mock import patch, MagicMock, AsyncMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

from apps.companies.models import Company, SubscriptionPlan, CompanyUser
from apps.ai_insights.models import AICredit, AIConversation, AIMessage
from apps.ai_insights.consumers import ChatConsumer

User = get_user_model()


class WebSocketTestCase(TestCase):
    """Base test case for WebSocket tests"""
    
    async def setup_test_data(self):
        """Setup test data asynchronously"""
        # Create user
        self.user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create plan
        self.plan = await database_sync_to_async(SubscriptionPlan.objects.create)(
            name='Professional',
            slug='professional',
            plan_type='professional',
            price_monthly=99.90,
            price_yearly=999.00,
            max_bank_accounts=10,
            max_transactions=5000
        )
        
        # Create company
        self.company = await database_sync_to_async(Company.objects.create)(
            name='Test Company',
            owner=self.user,
            cnpj='12345678901234',
            company_type='ltda',
            business_sector='technology',
            subscription_plan=self.plan,
            subscription_status='active'
        )
        
        # Create company user
        await database_sync_to_async(CompanyUser.objects.create)(
            user=self.user,
            company=self.company,
            role='admin',
            is_active=True
        )
        
        # Create AI credits
        self.ai_credit = await database_sync_to_async(AICredit.objects.create)(
            company=self.company,
            balance=100,
            monthly_allowance=100,
            bonus_credits=10
        )
        
        # Create conversation
        self.conversation = await database_sync_to_async(AIConversation.objects.create)(
            company=self.company,
            user=self.user,
            title='Test Chat',
            status='active'
        )


class ChatConsumerTest(WebSocketTestCase):
    """Test ChatConsumer WebSocket functionality"""
    
    @patch('apps.ai_insights.consumers.ChatConsumer.authenticate_user')
    @patch('apps.ai_insights.consumers.ChatConsumer.has_permission')
    async def test_websocket_connect_success(self, mock_permission, mock_auth):
        """Test successful WebSocket connection"""
        await self.setup_test_data()
        
        # Mock authentication and permission
        mock_auth.return_value = True
        mock_permission.return_value = True
        
        # Create communicator
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/ai-insights/chat/{self.conversation.id}/?token=test_token"
        )
        
        # Mock user and company on consumer
        communicator.scope['user'] = self.user
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive connection established message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'connection_established')
        self.assertEqual(response['conversation_id'], str(self.conversation.id))
        
        await communicator.disconnect()
    
    @patch('apps.ai_insights.consumers.ChatConsumer.authenticate_user')
    async def test_websocket_connect_auth_failure(self, mock_auth):
        """Test WebSocket connection with authentication failure"""
        await self.setup_test_data()
        
        # Mock authentication failure
        mock_auth.return_value = False
        
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/ai-insights/chat/{self.conversation.id}/?token=invalid_token"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)
    
    @patch('apps.ai_insights.consumers.ChatConsumer.authenticate_user')
    @patch('apps.ai_insights.consumers.ChatConsumer.has_permission')
    @patch('apps.ai_insights.consumers.ChatConsumer.process_ai_message')
    async def test_send_message_success(self, mock_process, mock_permission, mock_auth):
        """Test sending message successfully"""
        await self.setup_test_data()
        
        # Setup mocks
        mock_auth.return_value = True
        mock_permission.return_value = True
        mock_process.return_value = {
            'message_id': 'test_msg_123',
            'content': 'AI response content',
            'credits_used': 1,
            'credits_remaining': 99,
            'structured_data': None,
            'insights': [],
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/ai-insights/chat/{self.conversation.id}/?token=test_token"
        )
        
        # Mock consumer attributes
        consumer = communicator.application.application
        consumer.user = self.user
        consumer.company = self.company
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip connection message
        await communicator.receive_json_from()
        
        # Send message
        await communicator.send_json_to({
            'type': 'message',
            'message': 'Test message'
        })
        
        # Should receive typing indicator
        typing_response = await communicator.receive_json_from()
        self.assertEqual(typing_response['type'], 'assistant_typing')
        self.assertTrue(typing_response['typing'])
        
        # Should receive AI response
        ai_response = await communicator.receive_json_from()
        self.assertEqual(ai_response['type'], 'ai_response')
        self.assertTrue(ai_response['success'])
        self.assertEqual(ai_response['data']['message'], 'AI response content')
        
        # Should receive typing stop
        typing_stop = await communicator.receive_json_from()
        self.assertEqual(typing_stop['type'], 'assistant_typing')
        self.assertFalse(typing_stop['typing'])
        
        await communicator.disconnect()
    
    @patch('apps.ai_insights.consumers.ChatConsumer.authenticate_user')
    @patch('apps.ai_insights.consumers.ChatConsumer.has_permission')
    @patch('apps.ai_insights.consumers.ChatConsumer.get_credits_balance')
    async def test_send_message_no_credits(self, mock_credits, mock_permission, mock_auth):
        """Test sending message with no credits"""
        await self.setup_test_data()
        
        # Setup mocks
        mock_auth.return_value = True
        mock_permission.return_value = True
        mock_credits.return_value = 0  # No credits
        
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/ai-insights/chat/{self.conversation.id}/?token=test_token"
        )
        
        # Mock consumer attributes
        consumer = communicator.application.application
        consumer.user = self.user
        consumer.company = self.company
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip connection message
        await communicator.receive_json_from()
        
        # Send message
        await communicator.send_json_to({
            'type': 'message',
            'message': 'Test message'
        })
        
        # Should receive error about insufficient credits
        error_response = await communicator.receive_json_from()
        self.assertEqual(error_response['type'], 'error')
        self.assertEqual(error_response['error_code'], 'INSUFFICIENT_CREDITS')
        
        await communicator.disconnect()
    
    @patch('apps.ai_insights.consumers.ChatConsumer.authenticate_user')
    @patch('apps.ai_insights.consumers.ChatConsumer.has_permission')
    async def test_send_empty_message(self, mock_permission, mock_auth):
        """Test sending empty message"""
        await self.setup_test_data()
        
        # Setup mocks
        mock_auth.return_value = True
        mock_permission.return_value = True
        
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/ai-insights/chat/{self.conversation.id}/?token=test_token"
        )
        
        # Mock consumer attributes
        consumer = communicator.application.application
        consumer.user = self.user
        consumer.company = self.company
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip connection message
        await communicator.receive_json_from()
        
        # Send empty message
        await communicator.send_json_to({
            'type': 'message',
            'message': ''
        })
        
        # Should receive error about empty message
        error_response = await communicator.receive_json_from()
        self.assertEqual(error_response['type'], 'error')
        self.assertEqual(error_response['error_code'], 'EMPTY_MESSAGE')
        
        await communicator.disconnect()
    
    @patch('apps.ai_insights.consumers.ChatConsumer.authenticate_user')
    @patch('apps.ai_insights.consumers.ChatConsumer.has_permission')
    async def test_typing_indicator(self, mock_permission, mock_auth):
        """Test typing indicator functionality"""
        await self.setup_test_data()
        
        # Setup mocks
        mock_auth.return_value = True
        mock_permission.return_value = True
        
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/ai-insights/chat/{self.conversation.id}/?token=test_token"
        )
        
        # Mock consumer attributes
        consumer = communicator.application.application
        consumer.user = self.user
        consumer.company = self.company
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip connection message
        await communicator.receive_json_from()
        
        # Send typing indicator
        await communicator.send_json_to({
            'type': 'typing',
            'typing': True
        })
        
        # No immediate response expected for typing
        # This tests that the message is processed without error
        
        await communicator.disconnect()
    
    async def test_invalid_conversation_id(self):
        """Test connection with invalid conversation ID"""
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            "/ws/ai-insights/chat/invalid/?token=test_token"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)


class WebSocketSecurityTest(WebSocketTestCase):
    """Test WebSocket security features"""
    
    @patch('apps.ai_insights.consumers.ChatConsumer.authenticate_user')
    @patch('apps.ai_insights.consumers.ChatConsumer.has_permission')
    @patch('apps.ai_insights.consumers.ChatConsumer.check_rate_limit')
    async def test_rate_limiting(self, mock_rate_limit, mock_permission, mock_auth):
        """Test rate limiting functionality"""
        await self.setup_test_data()
        
        # Setup mocks
        mock_auth.return_value = True
        mock_permission.return_value = True
        mock_rate_limit.return_value = False  # Rate limited
        
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/ai-insights/chat/{self.conversation.id}/?token=test_token"
        )
        
        # Mock consumer attributes
        consumer = communicator.application.application
        consumer.user = self.user
        consumer.company = self.company
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip connection message
        await communicator.receive_json_from()
        
        # Send message
        await communicator.send_json_to({
            'type': 'message',
            'message': 'Test message'
        })
        
        # Should receive rate limit error
        error_response = await communicator.receive_json_from()
        self.assertEqual(error_response['type'], 'error')
        self.assertEqual(error_response['error_code'], 'RATE_LIMITED')
        
        await communicator.disconnect()
    
    @patch('apps.ai_insights.consumers.ChatConsumer.authenticate_user')
    @patch('apps.ai_insights.consumers.ChatConsumer.has_permission')
    async def test_message_too_long(self, mock_permission, mock_auth):
        """Test message length validation"""
        await self.setup_test_data()
        
        # Setup mocks
        mock_auth.return_value = True
        mock_permission.return_value = True
        
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/ai-insights/chat/{self.conversation.id}/?token=test_token"
        )
        
        # Mock consumer attributes
        consumer = communicator.application.application
        consumer.user = self.user
        consumer.company = self.company
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip connection message
        await communicator.receive_json_from()
        
        # Send very long message (>4000 chars)
        long_message = 'x' * 4001
        await communicator.send_json_to({
            'type': 'message',
            'message': long_message
        })
        
        # Should receive error about message length
        error_response = await communicator.receive_json_from()
        self.assertEqual(error_response['type'], 'error')
        self.assertEqual(error_response['error_code'], 'MESSAGE_TOO_LONG')
        
        await communicator.disconnect()