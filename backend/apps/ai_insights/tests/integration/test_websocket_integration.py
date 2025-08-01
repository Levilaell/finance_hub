"""
WebSocket Integration Tests
Tests real-time communication between frontend and backend via WebSocket
"""
import asyncio
import json
from unittest.mock import patch, Mock
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model

from apps.companies.models import Company
from apps.ai_insights.models import (
    AICredit,
    AIConversation,
    AIMessage,
    AIInsight
)
from apps.ai_insights.consumers import ChatConsumer
from apps.ai_insights.websocket_security import SecureWebSocketAuthMiddleware

User = get_user_model()


class WebSocketIntegrationTest(TransactionTestCase):
    """Test WebSocket integration with real database transactions"""
    
    async def setUp(self):
        """Set up test data asynchronously"""
        # Create test company and user
        self.company = await database_sync_to_async(Company.objects.create)(
            name='WebSocket Test Company',
            business_sector='Technology'
        )
        
        self.user = await database_sync_to_async(User.objects.create_user)(
            email='websocket-test@example.com',
            password='testpass123'
        )
        
        # Associate user with company
        self.user.company = self.company
        await database_sync_to_async(self.user.save)()
        
        # Create AI credits
        self.credit = await database_sync_to_async(AICredit.objects.create)(
            company=self.company,
            balance=100,
            monthly_allowance=50
        )
        
        # Create test conversation
        self.conversation = await database_sync_to_async(AIConversation.objects.create)(
            company=self.company,
            user=self.user,
            title='WebSocket Test Conversation'
        )
    
    async def create_authenticated_communicator(self, conversation_id=None):
        """Create authenticated WebSocket communicator"""
        application = SecureWebSocketAuthMiddleware(ChatConsumer.as_asgi())
        
        url = "/ws/ai-chat/"
        if conversation_id:
            url = f"/ws/ai-chat/{conversation_id}/"
        
        communicator = WebsocketCommunicator(application, url)
        
        # Add authentication to scope
        communicator.scope['user'] = self.user
        communicator.scope['url_route'] = {
            'kwargs': {'conversation_id': str(conversation_id)} if conversation_id else {}
        }
        
        return communicator
    
    async def test_websocket_connection_lifecycle(self):
        """Test complete WebSocket connection lifecycle"""
        communicator = await self.create_authenticated_communicator(self.conversation.id)
        
        # Connect
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive connection established message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'connection_established')
        self.assertIn('credits_available', response)
        self.assertEqual(response['conversation_id'], str(self.conversation.id))
        
        # Disconnect
        await communicator.disconnect()
    
    @patch('apps.ai_insights.services.ai_service.AIService.process_message')
    async def test_message_sending_workflow(self, mock_ai_service):
        """Test complete message sending workflow"""
        # Mock AI service response
        ai_message = await database_sync_to_async(AIMessage.objects.create)(
            conversation=self.conversation,
            role='assistant',
            content='AI response to your question about expenses',
            credits_used=3,
            tokens_used=150,
            model_used='gpt-4o-mini'
        )
        
        mock_ai_service.return_value = {
            'ai_message': ai_message,
            'credits_used': 3,
            'credits_remaining': 97,
            'insights': []
        }
        
        communicator = await self.create_authenticated_communicator(self.conversation.id)
        
        # Connect
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Receive connection message
        await communicator.receive_json_from()
        
        # Send chat message
        await communicator.send_json_to({
            'type': 'message',
            'message': 'What are my biggest expenses this month?'
        })
        
        # Should receive typing indicator
        typing_response = await communicator.receive_json_from()
        self.assertEqual(typing_response['type'], 'assistant_typing')
        self.assertTrue(typing_response['typing'])
        
        # Should receive AI response
        ai_response = await communicator.receive_json_from()
        self.assertEqual(ai_response['type'], 'ai_response')
        self.assertTrue(ai_response['success'])
        self.assertEqual(ai_response['data']['message'], 'AI response to your question about expenses')
        self.assertEqual(ai_response['data']['credits_used'], 3)
        self.assertEqual(ai_response['data']['credits_remaining'], 97)
        
        # Should receive typing stop
        typing_stop = await communicator.receive_json_from()
        self.assertEqual(typing_stop['type'], 'assistant_typing')
        self.assertFalse(typing_stop['typing'])
        
        # Verify AI service was called
        mock_ai_service.assert_called_once()
        call_args = mock_ai_service.call_args
        self.assertEqual(call_args[1]['conversation'], self.conversation)
        self.assertEqual(call_args[1]['user_message'], 'What are my biggest expenses this month?')
        
        # Verify conversation metrics updated
        conversation = await database_sync_to_async(
            AIConversation.objects.get
        )(id=self.conversation.id)
        self.assertEqual(conversation.message_count, 2)  # User + AI message
        self.assertEqual(conversation.total_credits_used, 3)
        
        await communicator.disconnect()
    
    async def test_insufficient_credits_handling(self):
        """Test handling of insufficient credits scenario"""
        # Set zero balance
        self.credit.balance = 0
        self.credit.bonus_credits = 0
        await database_sync_to_async(self.credit.save)()
        
        communicator = await self.create_authenticated_communicator(self.conversation.id)
        
        # Connect
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Receive connection message
        await communicator.receive_json_from()
        
        # Send message
        await communicator.send_json_to({
            'type': 'message',
            'message': 'Test message with no credits'
        })
        
        # Should receive error response
        error_response = await communicator.receive_json_from()
        self.assertEqual(error_response['type'], 'error')
        self.assertEqual(error_response['error_code'], 'INSUFFICIENT_CREDITS')
        self.assertIn('insuficientes', error_response['message'])
        self.assertEqual(error_response['credits_remaining'], 0)
        
        await communicator.disconnect()
    
    async def test_rate_limiting_enforcement(self):
        """Test rate limiting enforcement"""
        communicator = await self.create_authenticated_communicator(self.conversation.id)
        
        # Connect
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Receive connection message
        await communicator.receive_json_from()
        
        # Send many messages rapidly
        responses = []
        for i in range(65):  # Exceed rate limit of 60/minute
            await communicator.send_json_to({
                'type': 'message',
                'message': f'Rapid message {i}'
            })
            
            try:
                response = await asyncio.wait_for(
                    communicator.receive_json_from(),
                    timeout=0.1
                )
                responses.append(response)
            except asyncio.TimeoutError:
                break
        
        # Should eventually get rate limited
        rate_limit_errors = [
            r for r in responses 
            if r.get('type') == 'error' and r.get('error_code') == 'RATE_LIMITED'
        ]
        
        # At least some messages should be rate limited
        self.assertTrue(len(rate_limit_errors) > 0)
        
        await communicator.disconnect()
    
    async def test_typing_indicators(self):
        """Test typing indicator functionality"""
        communicator = await self.create_authenticated_communicator(self.conversation.id)
        
        # Connect
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Receive connection message
        await communicator.receive_json_from()
        
        # Send typing indicator
        await communicator.send_json_to({
            'type': 'typing',
            'typing': True
        })
        
        # Should not receive any response for typing (unless multiple users)
        # In single-user scenario, typing indicators are not echoed back
        
        # Send stop typing
        await communicator.send_json_to({
            'type': 'typing',
            'typing': False
        })
        
        await communicator.disconnect()
    
    async def test_read_receipts(self):
        """Test read receipt functionality"""
        # Create a message
        message = await database_sync_to_async(AIMessage.objects.create)(
            conversation=self.conversation,
            role='assistant',
            content='Test message for read receipt'
        )
        
        communicator = await self.create_authenticated_communicator(self.conversation.id)
        
        # Connect
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Receive connection message
        await communicator.receive_json_from()
        
        # Send read receipt
        await communicator.send_json_to({
            'type': 'read_receipt',
            'message_id': str(message.id)
        })
        
        # Verify message was marked as read in database
        message_updated = await database_sync_to_async(
            AIMessage.objects.get
        )(id=message.id)
        self.assertIsNotNone(message_updated.viewed_at)
        
        await communicator.disconnect()
    
    async def test_ping_pong_heartbeat(self):
        """Test WebSocket heartbeat mechanism"""
        communicator = await self.create_authenticated_communicator(self.conversation.id)
        
        # Connect
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Receive connection message
        await communicator.receive_json_from()
        
        # Send ping
        await communicator.send_json_to({
            'type': 'ping'
        })
        
        # Should receive pong
        pong_response = await communicator.receive_json_from()
        self.assertEqual(pong_response['type'], 'pong')
        
        await communicator.disconnect()
    
    async def test_invalid_message_handling(self):
        """Test handling of invalid messages"""
        communicator = await self.create_authenticated_communicator(self.conversation.id)
        
        # Connect
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Receive connection message
        await communicator.receive_json_from()
        
        # Send invalid message type
        await communicator.send_json_to({
            'type': 'invalid_message_type',
            'data': 'test'
        })
        
        # Should receive error response
        error_response = await communicator.receive_json_from()
        self.assertEqual(error_response['type'], 'error')
        self.assertIn('Unknown message type', error_response['message'])
        
        # Send message without content
        await communicator.send_json_to({
            'type': 'message'
            # Missing 'message' field
        })
        
        # Should receive error response
        error_response = await communicator.receive_json_from()
        self.assertEqual(error_response['type'], 'error')
        self.assertIn('empty', error_response['message'].lower())
        
        await communicator.disconnect()
    
    async def test_connection_without_conversation(self):
        """Test WebSocket connection without specific conversation"""
        communicator = await self.create_authenticated_communicator()
        
        # Connect
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive connection message without conversation_id
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'connection_established')
        self.assertNotIn('conversation_id', response)
        
        await communicator.disconnect()
    
    async def test_concurrent_connections(self):
        """Test multiple concurrent WebSocket connections"""
        # Create multiple communicators
        communicators = []
        for i in range(3):
            communicator = await self.create_authenticated_communicator(self.conversation.id)
            communicators.append(communicator)
        
        # Connect all
        for communicator in communicators:
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            # Receive connection message
            await communicator.receive_json_from()
        
        # Send message from first connection
        with patch('apps.ai_insights.services.ai_service.AIService.process_message') as mock_ai_service:
            ai_message = await database_sync_to_async(AIMessage.objects.create)(
                conversation=self.conversation,
                role='assistant',
                content='Concurrent test response'
            )
            
            mock_ai_service.return_value = {
                'ai_message': ai_message,
                'credits_used': 2,
                'credits_remaining': 98,
                'insights': []
            }
            
            await communicators[0].send_json_to({
                'type': 'message',
                'message': 'Concurrent test message'
            })
            
            # First connection should receive typing and response
            typing_msg = await communicators[0].receive_json_from()
            self.assertEqual(typing_msg['type'], 'assistant_typing')
            
            ai_response = await communicators[0].receive_json_from()
            self.assertEqual(ai_response['type'], 'ai_response')
            
            typing_stop = await communicators[0].receive_json_from()
            self.assertEqual(typing_stop['type'], 'assistant_typing')
            self.assertFalse(typing_stop['typing'])
        
        # Disconnect all
        for communicator in communicators:
            await communicator.disconnect()
    
    @patch('apps.ai_insights.services.ai_service.openai_wrapper')
    async def test_ai_service_error_handling(self, mock_openai):
        """Test WebSocket handling of AI service errors"""
        # Mock OpenAI error
        from apps.ai_insights.services.openai_wrapper import OpenAIError
        mock_openai.create_completion.side_effect = OpenAIError("API rate limit exceeded")
        
        communicator = await self.create_authenticated_communicator(self.conversation.id)
        
        # Connect
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Receive connection message
        await communicator.receive_json_from()
        
        # Send message
        await communicator.send_json_to({
            'type': 'message',
            'message': 'Test message that will cause AI error'
        })
        
        # Should receive typing indicator first
        typing_response = await communicator.receive_json_from()
        self.assertEqual(typing_response['type'], 'assistant_typing')
        
        # Should receive error response
        error_response = await communicator.receive_json_from()
        self.assertEqual(error_response['type'], 'error')
        self.assertEqual(error_response['error_code'], 'MESSAGE_PROCESSING_ERROR')
        
        # Should receive typing stop
        typing_stop = await communicator.receive_json_from()
        self.assertEqual(typing_stop['type'], 'assistant_typing')
        self.assertFalse(typing_stop['typing'])
        
        await communicator.disconnect()
    
    async def test_websocket_security_validation(self):
        """Test WebSocket security and validation"""
        communicator = await self.create_authenticated_communicator(self.conversation.id)
        
        # Connect
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Receive connection message
        await communicator.receive_json_from()
        
        # Test message size limit
        large_message = 'x' * 5000  # Exceed message limit
        await communicator.send_json_to({
            'type': 'message',
            'message': large_message
        })
        
        # Should receive error for message too long
        error_response = await communicator.receive_json_from()
        self.assertEqual(error_response['type'], 'error')
        self.assertEqual(error_response['error_code'], 'MESSAGE_TOO_LONG')
        
        await communicator.disconnect()
    
    async def test_conversation_context_isolation(self):
        """Test that conversations are properly isolated"""
        # Create another conversation for different user
        other_company = await database_sync_to_async(Company.objects.create)(
            name='Other Company',
            business_sector='Finance'
        )
        
        other_user = await database_sync_to_async(User.objects.create_user)(
            email='other-websocket@example.com',
            password='testpass123'
        )
        other_user.company = other_company
        await database_sync_to_async(other_user.save)()
        
        other_conversation = await database_sync_to_async(AIConversation.objects.create)(
            company=other_company,
            user=other_user,
            title='Other Conversation'
        )
        
        # Try to connect to other user's conversation
        communicator = await self.create_authenticated_communicator(other_conversation.id)
        
        # Connection should fail due to permission check
        connected, _ = await communicator.connect()
        
        # Connection might succeed but should be closed due to permission check
        if connected:
            try:
                response = await asyncio.wait_for(
                    communicator.receive_json_from(),
                    timeout=1.0
                )
                # If we get a response, it should be an error or connection should close
                if response:
                    self.assertEqual(response.get('type'), 'error')
            except asyncio.TimeoutError:
                # Connection was likely closed due to permission failure
                pass
        
        await communicator.disconnect()