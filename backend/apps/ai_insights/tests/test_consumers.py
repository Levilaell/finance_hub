"""
Tests for AI Insights WebSocket consumers
"""
import json
from unittest.mock import patch, MagicMock, AsyncMock
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company, Plan, Subscription
from apps.ai_insights.models import AICredit, AIConversation, AIMessage
from apps.ai_insights.consumers import ChatConsumer
from apps.ai_insights.routing import websocket_urlpatterns
from core.asgi import application

User = get_user_model()


class ChatConsumerTest(TransactionTestCase):
    """Test ChatConsumer WebSocket functionality"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user
        )
        
        # Set user's company
        self.user.company = self.company
        self.user.save()
        
        # Create plan and subscription
        self.plan = Plan.objects.create(
            name='Professional',
            plan_type='professional',
            price=99.90
        )
        
        Subscription.objects.create(
            company=self.company,
            plan=self.plan,
            status='active'
        )
        
        # Create AI credits
        AICredit.objects.create(
            company=self.company,
            balance=100
        )
        
        # Create conversation
        self.conversation = AIConversation.objects.create(
            company=self.company,
            user=self.user,
            title='Test Chat'
        )
        
        # Generate JWT token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
    
    async def test_websocket_connect_success(self):
        """Test successful WebSocket connection"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/ai-chat/{self.conversation.id}/?token={self.token}"
        )
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive connection established message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'connection_established')
        self.assertIn('Conectado', response['message'])
        
        await communicator.disconnect()
    
    async def test_websocket_connect_no_token(self):
        """Test WebSocket connection without token"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/ai-chat/{self.conversation.id}/"
        )
        
        connected, code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(code, 4001)  # Authentication error
    
    async def test_websocket_connect_invalid_token(self):
        """Test WebSocket connection with invalid token"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/ai-chat/{self.conversation.id}/?token=invalid_token"
        )
        
        connected, code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(code, 4001)  # Authentication error
    
    async def test_websocket_connect_wrong_conversation(self):
        """Test WebSocket connection to wrong conversation"""
        # Create another company and conversation
        other_user = await database_sync_to_async(User.objects.create_user)(
            email='other@example.com',
            password='otherpass'
        )
        other_company = await database_sync_to_async(Company.objects.create)(
            name='Other Company',
            owner=other_user
        )
        other_conversation = await database_sync_to_async(AIConversation.objects.create)(
            company=other_company,
            user=other_user,
            title='Other Chat'
        )
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/ai-chat/{other_conversation.id}/?token={self.token}"
        )
        
        connected, code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(code, 4003)  # Permission denied
    
    @patch('apps.ai_insights.services.ai_service.AIService.process_message')
    async def test_send_message(self, mock_process):
        """Test sending a message through WebSocket"""
        # Mock AI service response
        mock_process.return_value = {
            'message_id': 'msg123',
            'content': 'Your expenses are high in the Salaries category.',
            'credits_used': 3,
            'structured_data': None,
            'insights': []
        }
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/ai-chat/{self.conversation.id}/?token={self.token}"
        )
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip connection message
        await communicator.receive_json_from()
        
        # Send message
        await communicator.send_json_to({
            'type': 'message',
            'message': 'What are my expenses?'
        })
        
        # Should receive typing indicator
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'assistant_typing')
        self.assertTrue(response['typing'])
        
        # Should receive AI response
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'ai_response')
        self.assertEqual(response['message'], 'Your expenses are high in the Salaries category.')
        self.assertEqual(response['credits_used'], 3)
        
        # Should receive typing stop
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'assistant_typing')
        self.assertFalse(response['typing'])
        
        await communicator.disconnect()
    
    async def test_send_empty_message(self):
        """Test sending empty message"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/ai-chat/{self.conversation.id}/?token={self.token}"
        )
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip connection message
        await communicator.receive_json_from()
        
        # Send empty message
        await communicator.send_json_to({
            'type': 'message',
            'message': ''
        })
        
        # Should receive error
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'error')
        self.assertIn('empty', response['message'])
        
        await communicator.disconnect()
    
    @patch('apps.ai_insights.services.ai_service.AIService.process_message')
    async def test_insufficient_credits(self, mock_process):
        """Test sending message with insufficient credits"""
        # Set credits to 0
        credit = await database_sync_to_async(AICredit.objects.get)(company=self.company)
        credit.balance = 0
        await database_sync_to_async(credit.save)()
        
        # Mock AI service to raise InsufficientCreditsError
        from apps.ai_insights.services.credit_service import InsufficientCreditsError
        mock_process.side_effect = InsufficientCreditsError("Insufficient credits")
        
        communicator = WebsocketCommunicator(
            application,
            f"/ws/ai-chat/{self.conversation.id}/?token={self.token}"
        )
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip connection message
        await communicator.receive_json_from()
        
        # Send message
        await communicator.send_json_to({
            'type': 'message',
            'message': 'Analyze my finances'
        })
        
        # Skip typing indicator
        await communicator.receive_json_from()
        
        # Should receive insufficient credits error
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'error')
        self.assertEqual(response['error'], 'insufficient_credits')
        self.assertIn('Créditos insuficientes', response['message'])
        
        # Skip typing stop
        await communicator.receive_json_from()
        
        await communicator.disconnect()
    
    async def test_typing_indicator(self):
        """Test typing indicator functionality"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/ai-chat/{self.conversation.id}/?token={self.token}"
        )
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip connection message
        await communicator.receive_json_from()
        
        # Send typing indicator
        await communicator.send_json_to({
            'type': 'typing',
            'typing': True
        })
        
        # For broadcast testing, we'd need multiple connections
        # This test just ensures no error occurs
        
        await communicator.disconnect()
    
    async def test_invalid_message_type(self):
        """Test sending invalid message type"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/ai-chat/{self.conversation.id}/?token={self.token}"
        )
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip connection message
        await communicator.receive_json_from()
        
        # Send invalid type
        await communicator.send_json_to({
            'type': 'invalid_type',
            'data': 'test'
        })
        
        # Should receive error
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'error')
        self.assertIn('Unknown message type', response['message'])
        
        await communicator.disconnect()
    
    async def test_invalid_json(self):
        """Test sending invalid JSON"""
        communicator = WebsocketCommunicator(
            application,
            f"/ws/ai-chat/{self.conversation.id}/?token={self.token}"
        )
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip connection message
        await communicator.receive_json_from()
        
        # Send invalid JSON
        await communicator.send_to("invalid json {")
        
        # Should receive error
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'error')
        self.assertIn('Invalid JSON', response['message'])
        
        await communicator.disconnect()