"""
Unit tests for WebSocket Security
Tests WebSocket authentication and security middleware
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

from apps.ai_insights.websocket_security import (
    SecureWebSocketAuthMiddleware,
    WebSocketSecurityMixin,
    WebSocketRateLimiter
)
from apps.ai_insights.consumers import AIChatConsumer

User = get_user_model()


class TestWebSocketRateLimiter(TestCase):
    """Test WebSocket rate limiting functionality"""
    
    def setUp(self):
        cache.clear()
        self.rate_limiter = WebSocketRateLimiter()
        self.user_id = '12345'
    
    def test_rate_limit_allows_initial_requests(self):
        """Test that initial requests are allowed"""
        result = self.rate_limiter.is_allowed(self.user_id, 'message')
        self.assertTrue(result)
    
    def test_rate_limit_blocks_excessive_requests(self):
        """Test that excessive requests are blocked"""
        # Make requests up to the limit
        for _ in range(60):  # Default limit for message type
            result = self.rate_limiter.is_allowed(self.user_id, 'message')
            self.assertTrue(result)
        
        # Next request should be blocked
        result = self.rate_limiter.is_allowed(self.user_id, 'message')
        self.assertFalse(result)
    
    def test_rate_limit_resets_after_window(self):
        """Test that rate limit resets after time window"""
        # Exhaust the rate limit
        for _ in range(60):
            self.rate_limiter.is_allowed(self.user_id, 'message')
        
        # Should be blocked
        result = self.rate_limiter.is_allowed(self.user_id, 'message')
        self.assertFalse(result)
        
        # Simulate time passing (mock the cache to expire entries)
        cache.clear()
        
        # Should be allowed again
        result = self.rate_limiter.is_allowed(self.user_id, 'message')
        self.assertTrue(result)
    
    def test_different_action_types_have_different_limits(self):
        """Test that different action types have different rate limits"""
        # Message action (default: 60/minute)
        for _ in range(60):
            result = self.rate_limiter.is_allowed(self.user_id, 'message')
            self.assertTrue(result)
        
        result = self.rate_limiter.is_allowed(self.user_id, 'message')
        self.assertFalse(result)
        
        # Connection action should still be allowed (different limit)
        result = self.rate_limiter.is_allowed(self.user_id, 'connect')
        self.assertTrue(result)
    
    def test_different_users_have_separate_limits(self):
        """Test that different users have separate rate limits"""
        user1 = 'user1'
        user2 = 'user2'
        
        # Exhaust limit for user1
        for _ in range(60):
            self.rate_limiter.is_allowed(user1, 'message')
        
        # user1 should be blocked
        result = self.rate_limiter.is_allowed(user1, 'message')
        self.assertFalse(result)
        
        # user2 should still be allowed
        result = self.rate_limiter.is_allowed(user2, 'message')
        self.assertTrue(result)
    
    def test_get_remaining_requests(self):
        """Test getting remaining requests count"""
        # Make some requests
        for _ in range(10):
            self.rate_limiter.is_allowed(self.user_id, 'message')
        
        remaining = self.rate_limiter.get_remaining_requests(self.user_id, 'message')
        self.assertEqual(remaining, 50)  # 60 - 10 = 50
    
    def test_clear_user_limits(self):
        """Test clearing rate limits for a specific user"""
        # Make some requests
        for _ in range(30):
            self.rate_limiter.is_allowed(self.user_id, 'message')
        
        remaining_before = self.rate_limiter.get_remaining_requests(self.user_id, 'message')
        self.assertEqual(remaining_before, 30)
        
        # Clear limits
        self.rate_limiter.clear_user_limits(self.user_id)
        
        # Should have full limit again
        remaining_after = self.rate_limiter.get_remaining_requests(self.user_id, 'message')
        self.assertEqual(remaining_after, 60)


class TestSecureWebSocketAuthMiddleware(TestCase):
    """Test WebSocket authentication middleware"""
    
    def setUp(self):
        self.middleware = SecureWebSocketAuthMiddleware()
        self.mock_inner = Mock()
        self.middleware.inner = self.mock_inner
    
    @database_sync_to_async
    def create_test_user(self):
        """Create a test user"""
        return User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('apps.ai_insights.websocket_security.jwt.decode')
    def test_jwt_token_authentication(self, mock_jwt_decode):
        """Test JWT token authentication"""
        # Mock valid JWT decode
        mock_jwt_decode.return_value = {'user_id': 123}
        
        # Mock scope with JWT token in query string
        scope = {
            'type': 'websocket',
            'query_string': b'token=valid_jwt_token',
            'headers': []
        }
        
        # Mock user lookup
        with patch('apps.ai_insights.websocket_security.User.objects.get') as mock_get:
            mock_user = Mock()
            mock_user.id = 123
            mock_get.return_value = mock_user
            
            # Test authentication
            result = self.middleware.authenticate_websocket(scope)
            
            self.assertEqual(result, mock_user)
            mock_jwt_decode.assert_called_once()
    
    @patch('apps.ai_insights.websocket_security.jwt.decode')
    def test_invalid_jwt_token(self, mock_jwt_decode):
        """Test handling of invalid JWT token"""
        # Mock JWT decode failure
        mock_jwt_decode.side_effect = Exception("Invalid token")
        
        scope = {
            'type': 'websocket',
            'query_string': b'token=invalid_token',
            'headers': []
        }
        
        result = self.middleware.authenticate_websocket(scope)
        self.assertIsNone(result)
    
    def test_missing_token(self):
        """Test handling of missing authentication token"""
        scope = {
            'type': 'websocket',
            'query_string': b'',
            'headers': []
        }
        
        result = self.middleware.authenticate_websocket(scope)
        self.assertIsNone(result)
    
    def test_session_authentication_fallback(self):
        """Test session authentication fallback"""
        scope = {
            'type': 'websocket',
            'query_string': b'',
            'headers': [],
            'session': {'_auth_user_id': '123'}
        }
        
        with patch('apps.ai_insights.websocket_security.User.objects.get') as mock_get:
            mock_user = Mock()
            mock_user.id = 123
            mock_get.return_value = mock_user
            
            result = self.middleware.authenticate_websocket(scope)
            self.assertEqual(result, mock_user)
    
    def test_user_not_found(self):
        """Test handling when user is not found"""
        scope = {
            'type': 'websocket',
            'query_string': b'',
            'headers': [],
            'session': {'_auth_user_id': '999'}
        }
        
        with patch('apps.ai_insights.websocket_security.User.objects.get') as mock_get:
            mock_get.side_effect = User.DoesNotExist()
            
            result = self.middleware.authenticate_websocket(scope)
            self.assertIsNone(result)


class TestWebSocketSecurityMixin(TestCase):
    """Test WebSocket security mixin functionality"""
    
    def setUp(self):
        self.consumer = AIChatConsumer()
        self.consumer.scope = {
            'type': 'websocket',
            'user': Mock(id=123, is_authenticated=True)
        }
        self.consumer.channel_name = 'test-channel'
    
    def test_security_checks_authenticated_user(self):
        """Test security checks for authenticated user"""
        result = self.consumer.security_checks()
        self.assertTrue(result)
    
    def test_security_checks_unauthenticated_user(self):
        """Test security checks for unauthenticated user"""
        self.consumer.scope['user'] = Mock(is_authenticated=False)
        
        result = self.consumer.security_checks()
        self.assertFalse(result)
    
    @patch('apps.ai_insights.websocket_security.cache')
    def test_connection_tracking(self, mock_cache):
        """Test connection tracking functionality"""
        mock_cache.get.return_value = 0
        
        # Test increment connection count
        self.consumer.track_connection(True)
        
        # Should increment total connections
        mock_cache.incr.assert_called_with('ws_total_connections', delta=1)
        
        # Test decrement connection count
        self.consumer.track_connection(False)
        
        # Should decrement total connections
        mock_cache.decr.assert_called_with('ws_total_connections', delta=1)
    
    @patch('apps.ai_insights.websocket_security.WebSocketRateLimiter')
    def test_rate_limiting(self, mock_rate_limiter_class):
        """Test rate limiting functionality"""
        mock_rate_limiter = Mock()
        mock_rate_limiter_class.return_value = mock_rate_limiter
        mock_rate_limiter.is_allowed.return_value = True
        
        result = self.consumer.check_rate_limit('message')
        
        self.assertTrue(result)
        mock_rate_limiter.is_allowed.assert_called_with('123', 'message')
    
    @patch('apps.ai_insights.websocket_security.WebSocketRateLimiter')
    def test_rate_limiting_blocked(self, mock_rate_limiter_class):
        """Test rate limiting when blocked"""
        mock_rate_limiter = Mock()
        mock_rate_limiter_class.return_value = mock_rate_limiter
        mock_rate_limiter.is_allowed.return_value = False
        
        result = self.consumer.check_rate_limit('message')
        
        self.assertFalse(result)
    
    def test_activity_timeout_tracking(self):
        """Test activity timeout tracking"""
        with patch('time.time', return_value=1000):
            self.consumer.update_activity()
            self.assertEqual(self.consumer.last_activity, 1000)
    
    def test_is_activity_timeout(self):
        """Test activity timeout detection"""
        # Set last activity to 2 hours ago
        self.consumer.last_activity = time.time() - (2 * 60 * 60)
        
        # Should detect timeout (default timeout is 1 hour)
        result = self.consumer.is_activity_timeout()
        self.assertTrue(result)
        
        # Set recent activity
        self.consumer.last_activity = time.time() - 30  # 30 seconds ago
        
        # Should not detect timeout
        result = self.consumer.is_activity_timeout()
        self.assertFalse(result)
    
    @patch('apps.ai_insights.websocket_security.logger')
    def test_security_logging(self, mock_logger):
        """Test security event logging"""
        event_data = {
            'event': 'connection_attempt',
            'user_id': 123,
            'ip_address': '192.168.1.1'
        }
        
        self.consumer.log_security_event('connection_attempt', event_data)
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn('Security event: connection_attempt', call_args)
    
    def test_heartbeat_mechanism(self):
        """Test WebSocket heartbeat mechanism"""
        # Mock the send method
        self.consumer.send = AsyncMock()
        
        # Test heartbeat sending
        import asyncio
        
        async def test_heartbeat():
            await self.consumer.send_heartbeat()
            
        asyncio.run(test_heartbeat())
        
        # Verify heartbeat was sent
        self.consumer.send.assert_called_once()
        call_args = self.consumer.send.call_args[1]
        self.assertEqual(call_args['text_data'], '{"type": "heartbeat"}')


@pytest.mark.asyncio
class TestWebSocketConsumerIntegration:
    """Integration tests for WebSocket consumer with security"""
    
    async def test_connection_with_valid_auth(self):
        """Test WebSocket connection with valid authentication"""
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            email='test@example.com',
            password='testpass123'
        )
        
        # Mock the consumer with proper authentication
        application = SecureWebSocketAuthMiddleware(AIChatConsumer.as_asgi())
        
        # Create communicator with authenticated scope
        communicator = WebsocketCommunicator(application, "/ws/ai-chat/")
        communicator.scope['user'] = user
        
        # Test connection
        connected, subprotocol = await communicator.connect()
        
        assert connected
        
        # Clean up
        await communicator.disconnect()
    
    async def test_connection_without_auth(self):
        """Test WebSocket connection without authentication"""
        application = SecureWebSocketAuthMiddleware(AIChatConsumer.as_asgi())
        
        # Create communicator without authentication
        communicator = WebsocketCommunicator(application, "/ws/ai-chat/")
        
        # Test connection - should be rejected
        connected, subprotocol = await communicator.connect()
        
        assert not connected
    
    async def test_rate_limiting_integration(self):
        """Test rate limiting integration with WebSocket consumer"""
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            email='test@example.com',
            password='testpass123'
        )
        
        application = SecureWebSocketAuthMiddleware(AIChatConsumer.as_asgi())
        communicator = WebsocketCommunicator(application, "/ws/ai-chat/")
        communicator.scope['user'] = user
        
        # Connect
        connected, _ = await communicator.connect()
        assert connected
        
        # Send messages up to rate limit
        for i in range(5):  # Send a few messages
            await communicator.send_json_to({
                'type': 'message',
                'content': f'Test message {i}'
            })
            
            # Should receive response or rate limit message
            response = await communicator.receive_json_from()
            assert 'type' in response
        
        # Clean up
        await communicator.disconnect()
    
    @patch('apps.ai_insights.websocket_security.cache')
    async def test_connection_tracking_integration(self, mock_cache):
        """Test connection tracking integration"""
        mock_cache.get.return_value = 0
        
        # Create test user
        user = await database_sync_to_async(User.objects.create_user)(
            email='test@example.com',
            password='testpass123'
        )
        
        application = SecureWebSocketAuthMiddleware(AIChatConsumer.as_asgi())
        communicator = WebsocketCommunicator(application, "/ws/ai-chat/")
        communicator.scope['user'] = user
        
        # Connect
        connected, _ = await communicator.connect()
        assert connected
        
        # Verify connection was tracked
        mock_cache.incr.assert_called()
        
        # Disconnect
        await communicator.disconnect()
        
        # Verify disconnection was tracked
        mock_cache.decr.assert_called()


class TestWebSocketSecurityConfiguration(TestCase):
    """Test WebSocket security configuration"""
    
    def test_rate_limit_configuration(self):
        """Test rate limit configuration"""
        rate_limiter = WebSocketRateLimiter()
        
        # Test default limits
        self.assertIn('message', rate_limiter.limits)
        self.assertIn('connect', rate_limiter.limits)
        self.assertIn('disconnect', rate_limiter.limits)
        
        # Test limit values
        self.assertEqual(rate_limiter.limits['message']['rate'], 60)
        self.assertEqual(rate_limiter.limits['message']['window'], 60)
    
    def test_security_settings_validation(self):
        """Test security settings validation"""
        middleware = SecureWebSocketAuthMiddleware()
        
        # Test that middleware has required attributes
        self.assertTrue(hasattr(middleware, 'activity_timeout'))
        self.assertTrue(hasattr(middleware, 'max_connections_per_user'))
        
        # Test default values
        self.assertEqual(middleware.activity_timeout, 3600)  # 1 hour
        self.assertEqual(middleware.max_connections_per_user, 5)
    
    @patch('apps.ai_insights.websocket_security.settings')
    def test_custom_security_settings(self, mock_settings):
        """Test custom security settings from Django settings"""
        # Mock custom settings
        mock_settings.WS_ACTIVITY_TIMEOUT = 7200  # 2 hours
        mock_settings.WS_MAX_CONNECTIONS_PER_USER = 10
        
        middleware = SecureWebSocketAuthMiddleware()
        
        # Test custom values are applied
        self.assertEqual(middleware.activity_timeout, 7200)
        self.assertEqual(middleware.max_connections_per_user, 10)