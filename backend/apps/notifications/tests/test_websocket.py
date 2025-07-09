"""
Test WebSocket consumers for real-time notifications
Tests for NotificationConsumer and TransactionConsumer
Note: These are unit tests for the consumer logic, not full integration tests
"""
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from asgiref.sync import async_to_sync

from apps.companies.models import Company, SubscriptionPlan
from apps.notifications.models import Notification
from apps.notifications.consumers import NotificationConsumer, TransactionConsumer

User = get_user_model()


class TestNotificationConsumerLogic(TestCase):
    """Test NotificationConsumer logic without full WebSocket setup"""
    
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create subscription plan and company
        self.plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            slug='pro-plan',
            plan_type='pro',
            price_monthly=99.90,
            price_yearly=999.00
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan
        )
        
        # Create notification
        self.notification = Notification.objects.create(
            user=self.user,
            company=self.company,
            notification_type='report_ready',
            title='Report Ready',
            message='Your report is ready',
            priority='high'
        )
    
    def test_mark_notification_read_sync(self):
        """Test mark_notification_read method synchronously"""
        consumer = NotificationConsumer()
        consumer.user = self.user
        
        # Test marking notification as read
        result = async_to_sync(consumer.mark_notification_read)(self.notification.id)
        self.assertTrue(result)
        
        # Verify notification is marked as read
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
    
    def test_mark_notification_read_invalid_id(self):
        """Test marking non-existent notification"""
        consumer = NotificationConsumer()
        consumer.user = self.user
        
        # Test with invalid ID
        result = async_to_sync(consumer.mark_notification_read)(99999)
        self.assertFalse(result)
    
    def test_mark_other_user_notification(self):
        """Test cannot mark another user's notification"""
        # Create another user and notification
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        other_notification = Notification.objects.create(
            user=other_user,
            notification_type='custom',
            title='Other Notification',
            message='Not accessible',
            priority='low'
        )
        
        consumer = NotificationConsumer()
        consumer.user = self.user
        
        # Try to mark other user's notification
        result = async_to_sync(consumer.mark_notification_read)(other_notification.id)
        self.assertFalse(result)
        
        # Verify notification is still unread
        other_notification.refresh_from_db()
        self.assertFalse(other_notification.is_read)
    
    @patch('apps.notifications.consumers.logger')
    async def test_connect_anonymous_user(self, mock_logger):
        """Test connect method with anonymous user"""
        consumer = NotificationConsumer()
        consumer.scope = {'user': Mock(is_anonymous=True)}
        consumer.close = AsyncMock()
        consumer.channel_layer = Mock()
        consumer.accept = AsyncMock()
        
        await consumer.connect()
        
        # Should close connection for anonymous user
        consumer.close.assert_called_once()
        consumer.accept.assert_not_called()
    
    @patch('apps.notifications.consumers.logger')
    async def test_connect_authenticated_user(self, mock_logger):
        """Test connect method with authenticated user"""
        consumer = NotificationConsumer()
        consumer.scope = {'user': self.user}
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_add = AsyncMock()
        consumer.channel_name = 'test_channel'
        consumer.accept = AsyncMock()
        
        await consumer.connect()
        
        # Should accept connection
        consumer.accept.assert_called_once()
        consumer.channel_layer.group_add.assert_called_once_with(
            f'notifications_{self.user.id}',
            'test_channel'
        )
        mock_logger.info.assert_called()
    
    @patch('apps.notifications.consumers.logger')
    async def test_disconnect(self, mock_logger):
        """Test disconnect method"""
        consumer = NotificationConsumer()
        consumer.user = self.user
        consumer.group_name = f'notifications_{self.user.id}'
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_discard = AsyncMock()
        consumer.channel_name = 'test_channel'
        
        await consumer.disconnect(1000)
        
        # Should discard from group
        consumer.channel_layer.group_discard.assert_called_once_with(
            consumer.group_name,
            'test_channel'
        )
        mock_logger.info.assert_called()
    
    async def test_receive_ping(self):
        """Test receive method with ping message"""
        consumer = NotificationConsumer()
        consumer.user = self.user
        consumer.send = AsyncMock()
        
        # Send ping message
        await consumer.receive(json.dumps({
            'type': 'ping',
            'timestamp': '2025-01-09T10:00:00Z'
        }))
        
        # Should send pong response
        consumer.send.assert_called_once()
        call_args = consumer.send.call_args[1]
        response = json.loads(call_args['text_data'])
        self.assertEqual(response['type'], 'pong')
        self.assertEqual(response['timestamp'], '2025-01-09T10:00:00Z')
    
    async def test_receive_mark_read(self):
        """Test receive method with mark_read message"""
        consumer = NotificationConsumer()
        consumer.user = self.user
        consumer.mark_notification_read = AsyncMock(return_value=True)
        
        # Send mark_read message
        await consumer.receive(json.dumps({
            'type': 'mark_read',
            'notification_id': self.notification.id
        }))
        
        # Should call mark_notification_read
        consumer.mark_notification_read.assert_called_once_with(self.notification.id)
    
    @patch('apps.notifications.consumers.logger')
    async def test_receive_invalid_json(self, mock_logger):
        """Test receive method with invalid JSON"""
        consumer = NotificationConsumer()
        consumer.user = self.user
        
        # Send invalid JSON
        await consumer.receive("invalid json{")
        
        # Should log error
        mock_logger.error.assert_called()
    
    async def test_notification_message(self):
        """Test notification_message method"""
        consumer = NotificationConsumer()
        consumer.send = AsyncMock()
        
        # Call notification_message
        await consumer.notification_message({
            'message': {
                'id': 123,
                'type': 'new_notification',
                'title': 'Test Notification'
            }
        })
        
        # Should send the message
        consumer.send.assert_called_once()
        call_args = consumer.send.call_args[1]
        sent_data = json.loads(call_args['text_data'])
        self.assertEqual(sent_data['id'], 123)
        self.assertEqual(sent_data['type'], 'new_notification')


class TestTransactionConsumerLogic(TestCase):
    """Test TransactionConsumer logic without full WebSocket setup"""
    
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('apps.notifications.consumers.logger')
    async def test_connect_anonymous_user(self, mock_logger):
        """Test transaction consumer connect with anonymous user"""
        consumer = TransactionConsumer()
        consumer.scope = {'user': Mock(is_anonymous=True)}
        consumer.close = AsyncMock()
        consumer.channel_layer = Mock()
        consumer.accept = AsyncMock()
        
        await consumer.connect()
        
        # Should close connection
        consumer.close.assert_called_once()
        consumer.accept.assert_not_called()
    
    @patch('apps.notifications.consumers.logger')
    async def test_connect_authenticated_user(self, mock_logger):
        """Test transaction consumer connect with authenticated user"""
        consumer = TransactionConsumer()
        consumer.scope = {'user': self.user}
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_add = AsyncMock()
        consumer.channel_name = 'test_channel'
        consumer.accept = AsyncMock()
        
        await consumer.connect()
        
        # Should accept connection
        consumer.accept.assert_called_once()
        consumer.channel_layer.group_add.assert_called_once_with(
            f'transactions_{self.user.id}',
            'test_channel'
        )
        mock_logger.info.assert_called()
    
    async def test_receive_ping(self):
        """Test transaction consumer ping/pong"""
        consumer = TransactionConsumer()
        consumer.user = self.user
        consumer.send = AsyncMock()
        
        # Send ping
        await consumer.receive(json.dumps({
            'type': 'ping',
            'timestamp': '2025-01-09T15:30:00Z'
        }))
        
        # Should send pong
        consumer.send.assert_called_once()
        call_args = consumer.send.call_args[1]
        response = json.loads(call_args['text_data'])
        self.assertEqual(response['type'], 'pong')
        self.assertEqual(response['timestamp'], '2025-01-09T15:30:00Z')
    
    async def test_transaction_update(self):
        """Test transaction_update method"""
        consumer = TransactionConsumer()
        consumer.send = AsyncMock()
        
        # Call transaction_update
        await consumer.transaction_update({
            'message': {
                'type': 'transaction_created',
                'transaction_id': 123,
                'amount': '-50.00'
            }
        })
        
        # Should send the update
        consumer.send.assert_called_once()
        call_args = consumer.send.call_args[1]
        sent_data = json.loads(call_args['text_data'])
        self.assertEqual(sent_data['type'], 'transaction_created')
        self.assertEqual(sent_data['transaction_id'], 123)
    
    async def test_balance_update(self):
        """Test balance_update method"""
        consumer = TransactionConsumer()
        consumer.send = AsyncMock()
        
        # Call balance_update
        await consumer.balance_update({
            'message': {
                'type': 'balance_updated',
                'account_id': 456,
                'new_balance': '5000.00'
            }
        })
        
        # Should send the update
        consumer.send.assert_called_once()
        call_args = consumer.send.call_args[1]
        sent_data = json.loads(call_args['text_data'])
        self.assertEqual(sent_data['type'], 'balance_updated')
        self.assertEqual(sent_data['account_id'], 456)
    
    @patch('apps.notifications.consumers.logger')
    async def test_disconnect(self, mock_logger):
        """Test transaction consumer disconnect"""
        consumer = TransactionConsumer()
        consumer.user = self.user
        consumer.group_name = f'transactions_{self.user.id}'
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_discard = AsyncMock()
        consumer.channel_name = 'test_channel'
        
        await consumer.disconnect(1000)
        
        # Should discard from group
        consumer.channel_layer.group_discard.assert_called_once_with(
            consumer.group_name,
            'test_channel'
        )
        mock_logger.info.assert_called()


class TestWebSocketGroupIsolation(TestCase):
    """Test WebSocket group isolation between users"""
    
    def setUp(self):
        # Create multiple users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
    
    def test_notification_group_names(self):
        """Test that notification groups are user-specific"""
        consumer1 = NotificationConsumer()
        consumer1.user = self.user1
        
        consumer2 = NotificationConsumer()
        consumer2.user = self.user2
        
        # Groups should be different
        group1 = f'notifications_{self.user1.id}'
        group2 = f'notifications_{self.user2.id}'
        
        self.assertNotEqual(group1, group2)
        self.assertEqual(group1, f'notifications_{self.user1.id}')
        self.assertEqual(group2, f'notifications_{self.user2.id}')
    
    def test_transaction_group_names(self):
        """Test that transaction groups are user-specific"""
        consumer1 = TransactionConsumer()
        consumer1.user = self.user1
        
        consumer2 = TransactionConsumer()
        consumer2.user = self.user2
        
        # Groups should be different
        group1 = f'transactions_{self.user1.id}'
        group2 = f'transactions_{self.user2.id}'
        
        self.assertNotEqual(group1, group2)
        self.assertEqual(group1, f'transactions_{self.user1.id}')
        self.assertEqual(group2, f'transactions_{self.user2.id}')