"""
Unit tests for AI Insights WebSocket Consumers
Tests WebSocket consumer functionality with security integration
"""
import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache

from apps.ai_insights.consumers import AIChatConsumer
from apps.ai_insights.websocket_security import SecureWebSocketAuthMiddleware

User = get_user_model()


class TestAIChatConsumer(TestCase):
    """Test AIChatConsumer functionality"""
    
    def setUp(self):
        self.consumer = AIChatConsumer()
        self.consumer.scope = {
            'type': 'websocket',
            'user': Mock(id=123, is_authenticated=True),
            'url_route': {'kwargs': {}}
        }
        self.consumer.channel_name = 'test-channel'
        self.consumer.channel_layer = Mock()
    
    def test_consumer_initialization(self):
        """Test consumer initialization"""
        self.assertIsInstance(self.consumer, AIChatConsumer)
        self.assertTrue(hasattr(self.consumer, 'security_checks'))
        self.assertTrue(hasattr(self.consumer, 'track_connection'))
    
    async def test_connect_authenticated_user(self):
        """Test WebSocket connection for authenticated user"""
        self.consumer.accept = AsyncMock()
        self.consumer.send = AsyncMock()
        
        # Mock security checks to pass
        with patch.object(self.consumer, 'security_checks', return_value=True):
            with patch.object(self.consumer, 'track_connection'):
                with patch.object(self.consumer, 'log_security_event'):
                    await self.consumer.connect()
                    
                    # Should accept connection
                    self.consumer.accept.assert_called_once()
    
    async def test_connect_unauthenticated_user(self):
        """Test WebSocket connection for unauthenticated user"""
        self.consumer.scope['user'] = Mock(is_authenticated=False)
        self.consumer.close = AsyncMock()
        
        # Mock security checks to fail
        with patch.object(self.consumer, 'security_checks', return_value=False):
            with patch.object(self.consumer, 'log_security_event'):
                await self.consumer.connect()
                
                # Should close connection
                self.consumer.close.assert_called_once_with(code=4003)
    
    async def test_disconnect_cleanup(self):
        """Test WebSocket disconnection cleanup"""
        with patch.object(self.consumer, 'track_connection') as mock_track:
            with patch.object(self.consumer, 'log_security_event') as mock_log:
                await self.consumer.disconnect(1000)
                
                # Should track disconnection
                mock_track.assert_called_once_with(False)
                
                # Should log security event
                mock_log.assert_called_once()
    
    async def test_receive_valid_message(self):
        """Test receiving valid chat message"""
        self.consumer.send = AsyncMock()
        
        message_data = {
            'type': 'message',
            'content': 'Hello AI',
            'request_type': 'general'
        }
        
        with patch.object(self.consumer, 'check_rate_limit', return_value=True):
            with patch.object(self.consumer, 'update_activity'):
                with patch.object(self.consumer, 'handle_chat_message') as mock_handle:
                    mock_handle.return_value = None
                    
                    await self.consumer.receive(text_data=json.dumps(message_data))
                    
                    # Should handle the message
                    mock_handle.assert_called_once_with(message_data)
    
    async def test_receive_rate_limited(self):
        """Test receiving message when rate limited"""
        self.consumer.send = AsyncMock()
        
        message_data = {
            'type': 'message',
            'content': 'Hello AI'
        }
        
        with patch.object(self.consumer, 'check_rate_limit', return_value=False):
            await self.consumer.receive(text_data=json.dumps(message_data))
            
            # Should send rate limit error
            self.consumer.send.assert_called_once()
            call_args = self.consumer.send.call_args[1]
            sent_data = json.loads(call_args['text_data'])
            
            self.assertEqual(sent_data['type'], 'error')
            self.assertIn('rate limit', sent_data['message'].lower())
    
    async def test_receive_invalid_json(self):
        """Test receiving invalid JSON"""
        self.consumer.send = AsyncMock()
        
        with patch.object(self.consumer, 'log_security_event') as mock_log:
            await self.consumer.receive(text_data='invalid json{')
            
            # Should send error response
            self.consumer.send.assert_called_once()
            call_args = self.consumer.send.call_args[1]
            sent_data = json.loads(call_args['text_data'])
            
            self.assertEqual(sent_data['type'], 'error')
            self.assertIn('Invalid JSON', sent_data['message'])
            
            # Should log security event
            mock_log.assert_called_once()
    
    async def test_receive_activity_timeout(self):
        """Test receiving message after activity timeout"""
        self.consumer.close = AsyncMock()
        
        with patch.object(self.consumer, 'is_activity_timeout', return_value=True):
            await self.consumer.receive(text_data='{"type": "message"}')
            
            # Should close connection
            self.consumer.close.assert_called_once_with(code=4008)
    
    async def test_handle_chat_message_success(self):
        """Test handling successful chat message"""
        self.consumer.send = AsyncMock()
        
        message_data = {
            'content': 'Analyze my expenses',
            'request_type': 'analysis'
        }
        
        # Mock AI service response
        mock_response = {
            'message': 'Here is your expense analysis...',
            'message_id': 'msg_123',
            'credits_used': 5,
            'credits_remaining': 45,
            'structured_data': {'chart_data': []},
            'insights': [],
            'created_at': '2023-01-01T00:00:00Z'
        }
        
        with patch('apps.ai_insights.consumers.ai_service') as mock_ai_service:
            mock_ai_service.process_user_message.return_value = mock_response
            
            await self.consumer.handle_chat_message(message_data)
            
            # Should send AI response
            self.consumer.send.assert_called_once()
            call_args = self.consumer.send.call_args[1]
            sent_data = json.loads(call_args['text_data'])
            
            self.assertEqual(sent_data['type'], 'ai_response')
            self.assertTrue(sent_data['success'])
            self.assertEqual(sent_data['data']['message'], mock_response['message'])
    
    async def test_handle_chat_message_error(self):
        """Test handling chat message with AI service error"""
        self.consumer.send = AsyncMock()
        
        message_data = {
            'content': 'Test message',
            'request_type': 'general'
        }
        
        with patch('apps.ai_insights.consumers.ai_service') as mock_ai_service:
            mock_ai_service.process_user_message.side_effect = Exception("AI service error")
            
            await self.consumer.handle_chat_message(message_data)
            
            # Should send error response
            self.consumer.send.assert_called_once()
            call_args = self.consumer.send.call_args[1]
            sent_data = json.loads(call_args['text_data'])
            
            self.assertEqual(sent_data['type'], 'error')
            self.assertIn('processing your message', sent_data['message'])
    
    async def test_send_typing_indicator(self):
        """Test sending typing indicator"""
        self.consumer.send = AsyncMock()
        
        await self.consumer.send_typing_indicator(True)
        
        # Should send typing indicator
        self.consumer.send.assert_called_once()
        call_args = self.consumer.send.call_args[1]
        sent_data = json.loads(call_args['text_data'])
        
        self.assertEqual(sent_data['type'], 'assistant_typing')
        self.assertTrue(sent_data['typing'])
    
    async def test_send_heartbeat(self):
        """Test sending heartbeat"""
        self.consumer.send = AsyncMock()
        
        await self.consumer.send_heartbeat()
        
        # Should send heartbeat
        self.consumer.send.assert_called_once()
        call_args = self.consumer.send.call_args[1]
        sent_data = json.loads(call_args['text_data'])
        
        self.assertEqual(sent_data['type'], 'heartbeat')
    
    def test_get_conversation_id(self):
        """Test getting conversation ID from scope"""
        # Test with conversation_id in URL kwargs
        self.consumer.scope['url_route']['kwargs'] = {'conversation_id': 'conv_123'}
        
        conversation_id = self.consumer.get_conversation_id()
        self.assertEqual(conversation_id, 'conv_123')
        
        # Test without conversation_id
        self.consumer.scope['url_route']['kwargs'] = {}
        
        conversation_id = self.consumer.get_conversation_id()
        self.assertIsNone(conversation_id)


@pytest.mark.asyncio
class TestAIChatConsumerIntegration:
    """Integration tests for AIChatConsumer"""
    
    async def test_full_chat_flow(self):
        """Test complete chat flow from connection to message"""
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create communicator
        application = SecureWebSocketAuthMiddleware(AIChatConsumer.as_asgi())
        communicator = WebsocketCommunicator(application, "/ws/ai-chat/")
        communicator.scope['user'] = user
        
        # Connect
        connected, _ = await communicator.connect()
        assert connected
        
        # Send chat message
        with patch('apps.ai_insights.consumers.ai_service') as mock_ai_service:
            mock_ai_service.process_user_message.return_value = {
                'message': 'Test AI response',
                'message_id': 'msg_123',
                'credits_used': 2,
                'credits_remaining': 48,
                'structured_data': None,
                'insights': [],
                'created_at': '2023-01-01T00:00:00Z'
            }
            
            await communicator.send_json_to({
                'type': 'message',
                'content': 'Hello AI',
                'request_type': 'general'
            })
            
            # Receive response
            response = await communicator.receive_json_from()
            
            assert response['type'] == 'ai_response'
            assert response['success'] is True
            assert response['data']['message'] == 'Test AI response'
        
        # Disconnect
        await communicator.disconnect()
    
    async def test_multiple_concurrent_connections(self):
        """Test multiple concurrent WebSocket connections"""
        # Create test users
        users = []
        for i in range(3):
            user = await database_sync_to_async(User.objects.create_user)(
                email=f'test{i}@example.com',
                password='testpass123'
            )
            users.append(user)
        
        # Create communicators
        communicators = []
        application = SecureWebSocketAuthMiddleware(AIChatConsumer.as_asgi())
        
        for user in users:
            communicator = WebsocketCommunicator(application, "/ws/ai-chat/")
            communicator.scope['user'] = user
            communicators.append(communicator)
        
        # Connect all
        for communicator in communicators:
            connected, _ = await communicator.connect()
            assert connected
        
        # Send messages from all connections
        with patch('apps.ai_insights.consumers.ai_service') as mock_ai_service:
            mock_ai_service.process_user_message.return_value = {
                'message': 'Concurrent response',
                'message_id': 'msg_concurrent',
                'credits_used': 1,
                'credits_remaining': 49,
                'structured_data': None,
                'insights': [],
                'created_at': '2023-01-01T00:00:00Z'
            }
            
            # Send from all connections simultaneously
            send_tasks = []
            for communicator in communicators:
                task = communicator.send_json_to({
                    'type': 'message',
                    'content': 'Concurrent test'
                })
                send_tasks.append(task)
            
            await asyncio.gather(*send_tasks)
            
            # Receive responses
            for communicator in communicators:
                response = await communicator.receive_json_from()
                assert response['type'] == 'ai_response'
                assert response['data']['message'] == 'Concurrent response'
        
        # Disconnect all
        for communicator in communicators:
            await communicator.disconnect()
    
    async def test_conversation_specific_connection(self):
        """Test connecting to specific conversation"""
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create conversation
        from apps.ai_insights.models import AIConversation
        conversation = await database_sync_to_async(AIConversation.objects.create)(
            user=user,
            title='Test Conversation',
            status='active'
        )
        
        # Connect to specific conversation
        application = SecureWebSocketAuthMiddleware(AIChatConsumer.as_asgi())
        communicator = WebsocketCommunicator(
            application, 
            f"/ws/ai-chat/{conversation.id}/"
        )
        communicator.scope['user'] = user
        communicator.scope['url_route'] = {
            'kwargs': {'conversation_id': str(conversation.id)}
        }
        
        # Connect
        connected, _ = await communicator.connect()
        assert connected
        
        # Send message
        with patch('apps.ai_insights.consumers.ai_service') as mock_ai_service:
            mock_ai_service.process_user_message.return_value = {
                'message': 'Conversation specific response',
                'message_id': 'msg_conv',
                'credits_used': 3,
                'credits_remaining': 47,
                'structured_data': None,
                'insights': [],
                'created_at': '2023-01-01T00:00:00Z'
            }
            
            await communicator.send_json_to({
                'type': 'message',
                'content': 'Message in specific conversation'
            })
            
            # Should receive response
            response = await communicator.receive_json_from()
            assert response['type'] == 'ai_response'
            
            # Verify AI service was called with conversation context
            mock_ai_service.process_user_message.assert_called_once()
            call_args = mock_ai_service.process_user_message.call_args[1]
            assert 'conversation_id' in call_args
        
        await communicator.disconnect()
    
    async def test_connection_tracking_integration(self):
        """Test connection tracking with real cache"""
        from django.core.cache import cache
        cache.clear()
        
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create communicator
        application = SecureWebSocketAuthMiddleware(AIChatConsumer.as_asgi())
        communicator = WebsocketCommunicator(application, "/ws/ai-chat/")
        communicator.scope['user'] = user
        
        # Check initial connection count
        initial_count = cache.get('ws_total_connections', 0)
        
        # Connect
        connected, _ = await communicator.connect()
        assert connected
        
        # Check connection count increased
        after_connect = cache.get('ws_total_connections', 0)
        assert after_connect == initial_count + 1
        
        # Disconnect
        await communicator.disconnect()
        
        # Check connection count decreased
        after_disconnect = cache.get('ws_total_connections', 0)
        assert after_disconnect == initial_count
    
    async def test_heartbeat_mechanism(self):
        """Test WebSocket heartbeat mechanism"""
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create communicator
        application = SecureWebSocketAuthMiddleware(AIChatConsumer.as_asgi())
        communicator = WebsocketCommunicator(application, "/ws/ai-chat/")
        communicator.scope['user'] = user
        
        # Connect
        connected, _ = await communicator.connect()
        assert connected
        
        # Send heartbeat request
        await communicator.send_json_to({
            'type': 'heartbeat'
        })
        
        # Should receive heartbeat response
        response = await communicator.receive_json_from()
        assert response['type'] == 'heartbeat'
        
        await communicator.disconnect()


class TestWebSocketErrorHandling(TestCase):
    """Test WebSocket error handling scenarios"""
    
    def setUp(self):
        self.consumer = AIChatConsumer()
        self.consumer.scope = {
            'type': 'websocket',
            'user': Mock(id=123, is_authenticated=True)
        }
        self.consumer.send = AsyncMock()
    
    async def test_handle_invalid_message_type(self):
        """Test handling invalid message type"""
        message_data = {
            'type': 'invalid_type',
            'content': 'test'
        }
        
        await self.consumer.receive(text_data=json.dumps(message_data))
        
        # Should send error response
        self.consumer.send.assert_called_once()
        call_args = self.consumer.send.call_args[1]
        sent_data = json.loads(call_args['text_data'])
        
        self.assertEqual(sent_data['type'], 'error')
        self.assertIn('Unknown message type', sent_data['message'])
    
    async def test_handle_missing_content(self):
        """Test handling message with missing content"""
        message_data = {
            'type': 'message'
            # Missing 'content' field
        }
        
        await self.consumer.receive(text_data=json.dumps(message_data))
        
        # Should send error response
        self.consumer.send.assert_called_once()
        call_args = self.consumer.send.call_args[1]
        sent_data = json.loads(call_args['text_data'])
        
        self.assertEqual(sent_data['type'], 'error')
        self.assertIn('Content is required', sent_data['message'])
    
    async def test_handle_ai_service_timeout(self):
        """Test handling AI service timeout"""
        message_data = {
            'type': 'message',
            'content': 'Test message'
        }
        
        with patch('apps.ai_insights.consumers.ai_service') as mock_ai_service:
            mock_ai_service.process_user_message.side_effect = asyncio.TimeoutError()
            
            with patch.object(self.consumer, 'check_rate_limit', return_value=True):
                with patch.object(self.consumer, 'update_activity'):
                    await self.consumer.receive(text_data=json.dumps(message_data))
                    
                    # Should send timeout error
                    self.consumer.send.assert_called()
                    call_args = self.consumer.send.call_args[1]
                    sent_data = json.loads(call_args['text_data'])
                    
                    self.assertEqual(sent_data['type'], 'error')
                    self.assertIn('timeout', sent_data['message'].lower())
    
    async def test_handle_insufficient_credits(self):
        """Test handling insufficient credits error"""
        message_data = {
            'type': 'message',
            'content': 'Test message'
        }
        
        with patch('apps.ai_insights.consumers.ai_service') as mock_ai_service:
            from apps.ai_insights.exceptions import InsufficientCreditsError
            mock_ai_service.process_user_message.side_effect = InsufficientCreditsError(
                "Not enough credits"
            )
            
            with patch.object(self.consumer, 'check_rate_limit', return_value=True):
                with patch.object(self.consumer, 'update_activity'):
                    await self.consumer.receive(text_data=json.dumps(message_data))
                    
                    # Should send credits error
                    self.consumer.send.assert_called()
                    call_args = self.consumer.send.call_args[1]
                    sent_data = json.loads(call_args['text_data'])
                    
                    self.assertEqual(sent_data['type'], 'error')
                    self.assertEqual(sent_data['error_code'], 'INSUFFICIENT_CREDITS')
    
    async def test_handle_connection_limit_exceeded(self):
        """Test handling connection limit exceeded"""
        self.consumer.close = AsyncMock()
        
        with patch.object(self.consumer, 'security_checks', return_value=True):
            with patch('apps.ai_insights.consumers.cache') as mock_cache:
                # Mock that user has too many connections
                mock_cache.get.return_value = 10  # Exceeds limit of 5
                
                await self.consumer.connect()
                
                # Should close connection
                self.consumer.close.assert_called_once_with(code=4007)


@pytest.mark.django_db
class TestConsumerPerformance:
    """Test WebSocket consumer performance"""
    
    async def test_message_processing_speed(self):
        """Test message processing performance"""
        import time
        
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create communicator
        application = SecureWebSocketAuthMiddleware(AIChatConsumer.as_asgi())
        communicator = WebsocketCommunicator(application, "/ws/ai-chat/")
        communicator.scope['user'] = user
        
        # Connect
        connected, _ = await communicator.connect()
        assert connected
        
        # Mock fast AI service
        with patch('apps.ai_insights.consumers.ai_service') as mock_ai_service:
            mock_ai_service.process_user_message.return_value = {
                'message': 'Fast response',
                'message_id': 'msg_fast',
                'credits_used': 1,
                'credits_remaining': 49,
                'structured_data': None,
                'insights': [],
                'created_at': '2023-01-01T00:00:00Z'
            }
            
            # Measure processing time
            start_time = time.time()
            
            await communicator.send_json_to({
                'type': 'message',
                'content': 'Performance test'
            })
            
            response = await communicator.receive_json_from()
            
            processing_time = time.time() - start_time
            
            # Should process quickly (under 1 second for mocked service)
            assert processing_time < 1.0
            assert response['type'] == 'ai_response'
        
        await communicator.disconnect()
    
    async def test_concurrent_message_handling(self):
        """Test handling multiple concurrent messages"""
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create communicator
        application = SecureWebSocketAuthMiddleware(AIChatConsumer.as_asgi())
        communicator = WebsocketCommunicator(application, "/ws/ai-chat/")
        communicator.scope['user'] = user
        
        # Connect
        connected, _ = await communicator.connect()
        assert connected
        
        # Mock AI service with slight delay
        with patch('apps.ai_insights.consumers.ai_service') as mock_ai_service:
            async def mock_process(content, **kwargs):
                await asyncio.sleep(0.1)  # 100ms processing time
                return {
                    'message': f'Response to: {content}',
                    'message_id': f'msg_{content[:5]}',
                    'credits_used': 1,
                    'credits_remaining': 49,
                    'structured_data': None,
                    'insights': [],
                    'created_at': '2023-01-01T00:00:00Z'
                }
            
            mock_ai_service.process_user_message.side_effect = mock_process
            
            # Send multiple messages quickly
            messages = ['Message 1', 'Message 2', 'Message 3']
            
            send_tasks = []
            for i, msg in enumerate(messages):
                task = communicator.send_json_to({
                    'type': 'message',
                    'content': msg
                })
                send_tasks.append(task)
                # Small delay between sends to avoid rate limiting
                await asyncio.sleep(0.01)
            
            # Wait for all sends to complete
            await asyncio.gather(*send_tasks)
            
            # Receive all responses
            responses = []
            for _ in messages:
                response = await communicator.receive_json_from()
                responses.append(response)
            
            # All should be successful
            assert len(responses) == 3
            for response in responses:
                assert response['type'] == 'ai_response'
                assert response['success'] is True
        
        await communicator.disconnect()