"""
Test cases for Notification service
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from unittest.mock import patch, MagicMock, call
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
import asyncio
import json

from apps.notifications.services import NotificationService, handle_account_connected, handle_payment_failed
from apps.notifications.models import Notification
from apps.companies.models import Company

User = get_user_model()


class NotificationServiceTest(TestCase):
    """Test NotificationService functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test company
        self.company = Company.objects.create(
            name="Test Company",
            document_number="12345678901234",
            plan_name="premium",
            is_active=True
        )
        
        # Create test users
        self.user1 = User.objects.create_user(
            email="user1@example.com",
            username="user1",
            password="testpass123"
        )
        
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            username="user2",
            password="testpass123"
        )
        
        # Set company owner
        self.company.owner = self.user1
        self.company.save()
        
        # Clear cache before each test
        cache.clear()
    
    def test_create_single_notification(self):
        """Test creating a single notification"""
        notification = NotificationService.create_notification(
            event_name='account_connected',
            company=self.company,
            user=self.user1,
            title='Account Connected',
            message='Your bank account has been connected',
            metadata={'account_name': 'Test Bank'}
        )
        
        assert notification is not None
        assert notification.user == self.user1
        assert notification.event == 'account_connected'
        assert notification.title == 'Account Connected'
        assert notification.metadata['account_name'] == 'Test Bank'
    
    def test_create_broadcast_notification(self):
        """Test creating broadcast notifications"""
        with patch.object(NotificationService, '_deliver_via_websocket') as mock_deliver:
            mock_deliver.return_value = True
            
            notification = NotificationService.create_notification(
                event_name='system_maintenance',
                company=self.company,
                broadcast=True,
                title='System Maintenance',
                message='System will be down for maintenance'
            )
            
            # Check notifications were created for all users
            notifications = Notification.objects.filter(
                company=self.company,
                event='custom'
            )
            assert notifications.count() == 2
            
            # Check delivery was attempted for each
            assert mock_deliver.call_count == 2
    
    def test_notification_deduplication(self):
        """Test notification deduplication with event_id"""
        event_id = "payment_123"
        
        # Create first notification
        notification1 = NotificationService.create_notification(
            event_name='payment_failed',
            company=self.company,
            user=self.user1,
            event_id=event_id
        )
        
        # Try to create duplicate
        notification2 = NotificationService.create_notification(
            event_name='payment_failed',
            company=self.company,
            user=self.user1,
            event_id=event_id
        )
        
        assert notification1 is not None
        assert notification2 is None
        assert Notification.objects.filter(event_id=event_id).count() == 1
    
    @patch('apps.notifications.services.async_to_sync')
    @patch.object(NotificationService, '_is_user_online')
    def test_deliver_via_websocket_online_user(self, mock_is_online, mock_async_to_sync):
        """Test WebSocket delivery for online user"""
        mock_is_online.return_value = True
        mock_channel_send = MagicMock()
        mock_async_to_sync.return_value = mock_channel_send
        
        notification = Notification.objects.create(
            company=self.company,
            user=self.user1,
            event='account_connected',
            title='Account Connected'
        )
        
        result = NotificationService._deliver_via_websocket(notification)
        
        assert result is True
        assert notification.delivery_status == 'delivered'
        assert notification.delivered_at is not None
        
        # Check WebSocket message was sent
        mock_channel_send.assert_called_once()
        call_args = mock_channel_send.call_args[0]
        assert call_args[0] == f"notifications_{self.user1.id}"
        assert call_args[1]['type'] == 'notification_message'
    
    @patch('apps.notifications.services.async_to_sync')
    @patch.object(NotificationService, '_is_user_online')
    def test_deliver_via_websocket_offline_user(self, mock_is_online, mock_async_to_sync):
        """Test WebSocket delivery for offline user (non-critical)"""
        mock_is_online.return_value = False
        
        notification = Notification.objects.create(
            company=self.company,
            user=self.user1,
            event='report_ready',
            title='Report Ready',
            is_critical=False
        )
        
        result = NotificationService._deliver_via_websocket(notification)
        
        assert result is False
        assert notification.delivery_status == 'pending'
        mock_async_to_sync.assert_not_called()
    
    @patch('apps.notifications.services.async_to_sync')
    @patch.object(NotificationService, '_is_user_online')
    def test_deliver_critical_notification_offline_user(self, mock_is_online, mock_async_to_sync):
        """Test critical notification delivery for offline user"""
        mock_is_online.return_value = False
        mock_channel_send = MagicMock()
        mock_async_to_sync.return_value = mock_channel_send
        
        notification = Notification.objects.create(
            company=self.company,
            user=self.user1,
            event='payment_failed',
            title='Payment Failed',
            is_critical=True
        )
        
        result = NotificationService._deliver_via_websocket(notification)
        
        # Critical notifications are attempted even for offline users
        assert result is True
        assert notification.delivery_status == 'delivered'
        mock_channel_send.assert_called_once()
    
    @patch('apps.notifications.services.cache')
    def test_is_user_online(self, mock_cache):
        """Test checking user online status"""
        mock_cache.get.return_value = True
        
        result = NotificationService._is_user_online(self.user1.id)
        
        assert result is True
        mock_cache.get.assert_called_with(f"ws:online:{self.user1.id}", False)
    
    @patch('apps.notifications.services.cache')
    @patch('apps.notifications.services.async_to_sync')
    def test_update_unread_count_cache(self, mock_async_to_sync, mock_cache):
        """Test updating unread count cache"""
        mock_channel_send = MagicMock()
        mock_async_to_sync.return_value = mock_channel_send
        
        # Create some unread notifications
        for i in range(3):
            Notification.objects.create(
                company=self.company,
                user=self.user1,
                event='low_balance',
                title=f'Alert {i}'
            )
        
        NotificationService._update_unread_count_cache(self.company.id, self.user1.id)
        
        # Check cache operations
        cache_key = f'notifications:unread_count:{self.company.id}:{self.user1.id}'
        mock_cache.delete.assert_called_with(cache_key)
        mock_cache.set.assert_called_with(cache_key, 3, timeout=300)
        
        # Check WebSocket update
        mock_channel_send.assert_called_once()
        call_args = mock_channel_send.call_args[0]
        assert call_args[1]['type'] == 'unread_count_update'
        assert call_args[1]['count'] == 3
    
    def test_get_pending_notifications(self):
        """Test getting pending notifications"""
        # Create mix of notifications
        for i in range(5):
            Notification.objects.create(
                company=self.company,
                user=self.user1,
                event='account_connected',
                title=f'Notification {i}',
                delivery_status='pending' if i < 3 else 'delivered'
            )
        
        pending = NotificationService.get_pending_notifications(self.user1, self.company)
        
        assert len(pending) == 3
        for notification in pending:
            assert notification.delivery_status == 'pending'
    
    @patch('apps.notifications.services.cache')
    def test_mark_user_online(self, mock_cache):
        """Test marking user as online"""
        with patch.object(NotificationService, '_deliver_via_websocket') as mock_deliver:
            # Create pending notification
            notification = Notification.objects.create(
                company=self.company,
                user=self.user1,
                event='report_ready',
                title='Report Ready',
                delivery_status='pending'
            )
            
            NotificationService.mark_user_online(self.user1.id)
            
            # Check cache was set
            mock_cache.set.assert_called_with(
                f"ws:online:{self.user1.id}",
                True,
                timeout=600
            )
            
            # Check pending notifications were delivered
            mock_deliver.assert_called_once()
    
    @patch('apps.notifications.services.cache')
    def test_mark_user_offline(self, mock_cache):
        """Test marking user as offline"""
        NotificationService.mark_user_offline(self.user1.id)
        
        mock_cache.delete.assert_called_with(f"ws:online:{self.user1.id}")
    
    @patch('apps.notifications.services.time.sleep')
    @patch.object(NotificationService, '_deliver_via_websocket')
    def test_retry_worker(self, mock_deliver, mock_sleep):
        """Test retry worker for failed notifications"""
        # Create failed notification
        notification = Notification.objects.create(
            company=self.company,
            user=self.user1,
            event='payment_failed',
            title='Payment Failed',
            delivery_status='failed',
            retry_count=0
        )
        
        # Mock delivery success on retry
        mock_deliver.return_value = True
        
        # Set up mock to exit after one iteration
        mock_sleep.side_effect = Exception("Exit test")
        
        # Run retry worker
        try:
            NotificationService._retry_worker()
        except Exception:
            pass
        
        # Check notification was retried
        notification.refresh_from_db()
        assert notification.retry_count == 1
        assert notification.delivery_status == 'delivered'
        mock_deliver.assert_called_once()
    
    def test_cleanup_old_notifications(self):
        """Test cleaning up old read notifications"""
        from datetime import timedelta
        from django.utils import timezone
        
        # Create old read notification
        old_notification = Notification.objects.create(
            company=self.company,
            user=self.user1,
            event='report_ready',
            title='Old Report',
            is_read=True,
            read_at=timezone.now() - timedelta(days=40)
        )
        
        # Create recent read notification
        recent_notification = Notification.objects.create(
            company=self.company,
            user=self.user1,
            event='report_ready',
            title='Recent Report',
            is_read=True,
            read_at=timezone.now() - timedelta(days=5)
        )
        
        # Create unread notification
        unread_notification = Notification.objects.create(
            company=self.company,
            user=self.user1,
            event='report_ready',
            title='Unread Report'
        )
        
        deleted_count = NotificationService.cleanup_old_notifications(days=30)
        
        assert deleted_count == 1
        assert not Notification.objects.filter(id=old_notification.id).exists()
        assert Notification.objects.filter(id=recent_notification.id).exists()
        assert Notification.objects.filter(id=unread_notification.id).exists()


class NotificationEventHandlersTest(TestCase):
    """Test notification event handlers"""
    
    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(
            name="Test Company",
            document_number="12345678901234"
        )
        
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        
        CompanyMembership.objects.create(
            company=self.company,
            user=self.user,
            role='admin'
        )
    
    @patch.object(NotificationService, 'create_notification')
    def test_handle_account_connected(self, mock_create):
        """Test account connected event handler"""
        handle_account_connected(
            self.company,
            self.user,
            account_name="Chase Bank"
        )
        
        mock_create.assert_called_once_with(
            event_name='account_connected',
            company=self.company,
            user=self.user,
            broadcast=False,
            title="Account Connected",
            message="Chase Bank has been successfully connected",
            metadata={'account_name': 'Chase Bank'}
        )
    
    @patch.object(NotificationService, 'create_notification')
    def test_handle_payment_failed(self, mock_create):
        """Test payment failed event handler"""
        handle_payment_failed(
            self.company,
            self.user,
            error_message="Card declined"
        )
        
        mock_create.assert_called_once_with(
            event_name='payment_failed',
            company=self.company,
            user=self.user,
            title="Payment Failed",
            message="Card declined",
            metadata={'error': 'Card declined'},
            action_url="/subscription"
        )