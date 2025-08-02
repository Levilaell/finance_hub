"""
Test cases for Notification WebSocket consumers
"""
import pytest
from django.test import TestCase
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from django.urls import re_path
from django.contrib.auth import get_user_model
import json
from unittest.mock import patch, AsyncMock

from apps.notifications.consumers import NotificationConsumer
from apps.notifications.models import Notification
from apps.companies.models import Company

User = get_user_model()


# Test application for WebSocket
test_application = URLRouter([
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
])


class NotificationConsumerTest(TestCase):
    """Test NotificationConsumer WebSocket functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test company
        self.company = Company.objects.create(
            name="Test Company",
            document_number="12345678901234",
            plan_name="premium",
            is_active=True
        )
        
        # Create test user
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        
        # Set company owner
        self.company.owner = self.user
        self.company.save()
    
    @pytest.mark.asyncio
    async def test_connect_authenticated_user(self):
        """Test WebSocket connection for authenticated user"""
        communicator = WebsocketCommunicator(
            test_application,
            "/ws/notifications/",
            headers=[(b'origin', b'localhost')]
        )
        communicator.scope['user'] = self.user
        
        connected, subprotocol = await communicator.connect()
        assert connected
        
        # Should receive connection_established message
        message = await communicator.receive_json_from()
        assert message['type'] == 'connection_established'
        assert 'unread_count' in message
        assert 'pending_notifications' in message
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_connect_anonymous_user(self):
        """Test WebSocket connection rejection for anonymous user"""
        from django.contrib.auth.models import AnonymousUser
        
        communicator = WebsocketCommunicator(
            test_application,
            "/ws/notifications/"
        )
        communicator.scope['user'] = AnonymousUser()
        
        connected, subprotocol = await communicator.connect()
        assert not connected
    
    @pytest.mark.asyncio
    async def test_mark_notification_read(self):
        """Test marking notification as read via WebSocket"""
        # Create notification
        notification = await database_sync_to_async(Notification.objects.create)(
            company=self.company,
            user=self.user,
            event='report_ready',
            title='Report Ready',
            is_read=False
        )
        
        communicator = WebsocketCommunicator(
            test_application,
            "/ws/notifications/"
        )
        communicator.scope['user'] = self.user
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Clear connection message
        await communicator.receive_json_from()
        
        # Send mark_read message
        await communicator.send_json_to({
            'type': 'mark_read',
            'notification_id': str(notification.id)
        })
        
        # Should receive confirmation
        message = await communicator.receive_json_from()
        assert message['type'] == 'notification_read'
        assert message['notification_id'] == str(notification.id)
        assert message['unread_count'] == 0
        
        # Check notification was marked as read
        await database_sync_to_async(notification.refresh_from_db)()
        assert notification.is_read is True
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_mark_all_notifications_read(self):
        """Test marking all notifications as read"""
        # Create multiple notifications
        for i in range(3):
            await database_sync_to_async(Notification.objects.create)(
                company=self.company,
                user=self.user,
                event='low_balance',
                title=f'Alert {i}',
                is_read=False
            )
        
        communicator = WebsocketCommunicator(
            test_application,
            "/ws/notifications/"
        )
        communicator.scope['user'] = self.user
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Clear connection message
        await communicator.receive_json_from()
        
        # Send mark_all_read message
        await communicator.send_json_to({
            'type': 'mark_all_read'
        })
        
        # Should receive confirmation
        message = await communicator.receive_json_from()
        assert message['type'] == 'all_marked_read'
        assert message['count'] == 3
        assert message['unread_count'] == 0
        
        # Check all notifications were marked as read
        notifications = await database_sync_to_async(
            lambda: list(Notification.objects.filter(user=self.user))
        )()
        
        for notification in notifications:
            assert notification.is_read is True
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_acknowledge_critical_notification(self):
        """Test acknowledging critical notification"""
        # Create critical notification
        notification = await database_sync_to_async(Notification.objects.create)(
            company=self.company,
            user=self.user,
            event='payment_failed',
            title='Payment Failed',
            is_critical=True,
            delivery_status='pending'
        )
        
        communicator = WebsocketCommunicator(
            test_application,
            "/ws/notifications/"
        )
        communicator.scope['user'] = self.user
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Clear connection message
        await communicator.receive_json_from()
        
        # Send acknowledgment
        await communicator.send_json_to({
            'type': 'ack',
            'notification_id': str(notification.id)
        })
        
        # Allow time for processing
        await communicator.receive_nothing(timeout=0.1)
        
        # Check notification was marked as delivered
        await database_sync_to_async(notification.refresh_from_db)()
        assert notification.delivery_status == 'delivered'
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_ping_pong(self):
        """Test ping/pong health check"""
        communicator = WebsocketCommunicator(
            test_application,
            "/ws/notifications/"
        )
        communicator.scope['user'] = self.user
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Clear connection message
        await communicator.receive_json_from()
        
        # Send ping
        await communicator.send_json_to({
            'type': 'ping'
        })
        
        # Should receive pong
        message = await communicator.receive_json_from()
        assert message['type'] == 'pong'
        assert 'timestamp' in message
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_receive_new_notification(self):
        """Test receiving new notification via WebSocket"""
        communicator = WebsocketCommunicator(
            test_application,
            "/ws/notifications/"
        )
        communicator.scope['user'] = self.user
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Clear connection message
        await communicator.receive_json_from()
        
        # Create consumer instance and send notification
        consumer = NotificationConsumer()
        consumer.channel_name = "test_channel"
        consumer.send = AsyncMock()
        
        notification_data = {
            'id': '123',
            'event': 'account_connected',
            'title': 'Account Connected',
            'message': 'Your account has been connected',
            'is_critical': False,
            'is_read': False,
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        await consumer.notification_message({
            'notification': notification_data
        })
        
        # Check send was called with correct data
        consumer.send.assert_called_once()
        sent_data = json.loads(consumer.send.call_args[1]['text_data'])
        assert sent_data['type'] == 'new_notification'
        assert sent_data['notification']['id'] == '123'
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_invalid_json_handling(self):
        """Test handling of invalid JSON messages"""
        communicator = WebsocketCommunicator(
            test_application,
            "/ws/notifications/"
        )
        communicator.scope['user'] = self.user
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Clear connection message
        await communicator.receive_json_from()
        
        # Send invalid JSON
        await communicator.send_to(bytes("invalid json", 'utf-8'))
        
        # Should not crash - just receive nothing
        await communicator.receive_nothing(timeout=0.1)
        
        # Connection should still be active
        await communicator.send_json_to({'type': 'ping'})
        message = await communicator.receive_json_from()
        assert message['type'] == 'pong'
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    @patch('apps.notifications.services.NotificationService.mark_user_online')
    @patch('apps.notifications.services.NotificationService.mark_user_offline')
    async def test_user_online_offline_tracking(self, mock_offline, mock_online):
        """Test user online/offline status tracking"""
        communicator = WebsocketCommunicator(
            test_application,
            "/ws/notifications/"
        )
        communicator.scope['user'] = self.user
        
        # Connect
        connected, _ = await communicator.connect()
        assert connected
        
        # Check mark_user_online was called
        mock_online.assert_called_with(self.user.id)
        
        # Disconnect
        await communicator.disconnect()
        
        # Check mark_user_offline was called
        mock_offline.assert_called_with(self.user.id)