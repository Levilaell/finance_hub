"""
Test cases for Notification models
"""
import pytest
from .test_base import NotificationTestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from unittest.mock import patch, MagicMock
from datetime import timedelta
from django.db import IntegrityError

from apps.notifications.models import Notification
from apps.notifications.constants import CRITICAL_EVENTS
from apps.companies.models import Company
from .factories import create_test_company, create_test_notification

User = get_user_model()


class NotificationModelTest(NotificationTestCase):
    """Test Notification model functionality"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        # Clear cache before each test
        cache.clear()
    
    def test_create_notification(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='account_connected',
            event_key=f'account_connected:{self.company.id}:{self.user.id}:test1',
            title='Account Connected',
            message='Your bank account has been connected',
            metadata={'account_name': 'Test Bank'}
        )
        
        assert notification.id is not None
        assert notification.company == self.company
        assert notification.user == self.user
        assert notification.event == 'account_connected'
        assert notification.delivery_status == 'pending'
        assert notification.is_read is False
        assert notification.retry_count == 0
    
    def test_notification_str_representation(self):
        """Test string representation of notification"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='low_balance',
            event_key=f'low_balance:{self.company.id}:{self.user.id}:str_test',
            title='Low Balance Alert',
            is_critical=True
        )
        
        expected_str = f"Low Balance Alert - {self.user.email}"
        assert str(notification) == expected_str
    
    def test_event_deduplication(self):
        """Test notification deduplication with event_key"""
        event_key = "payment_failed:unique_event_123"
        
        # Create first notification
        notification1 = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='payment_failed',
            event_key=event_key,
            title='Payment Failed',
            is_critical=True
        )
        
        # Try to create duplicate (should raise IntegrityError)
        with self.assertRaises(IntegrityError):
            Notification.objects.create(
                company=self.company,
                user=self.user,
                event='payment_failed',
                event_key=event_key,
                title='Payment Failed',
                is_critical=True
            )
    
    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='report_ready',
            event_key=f'report_ready:{self.company.id}:{self.user.id}:read_test',
            title='Report Ready'
        )
        
        assert notification.is_read is False
        assert notification.read_at is None
        
        notification.mark_as_read()
        
        assert notification.is_read is True
        assert notification.read_at is not None
    
    def test_mark_as_delivered(self):
        """Test marking notification as delivered"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='account_connected',
            event_key=f'account_connected:{self.company.id}:{self.user.id}:delivered_test',
            title='Account Connected'
        )
        
        assert notification.delivery_status == 'pending'
        assert notification.delivered_at is None
        
        notification.mark_as_delivered()
        
        assert notification.delivery_status == 'delivered'
        assert notification.delivered_at is not None
    
    def test_mark_as_failed(self):
        """Test marking notification as failed"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='large_transaction',
            event_key=f'large_transaction:{self.company.id}:{self.user.id}:failed_test',
            title='Large Transaction'
        )
        
        notification.mark_as_failed()
        
        assert notification.delivery_status == 'failed'
    
    def test_increment_retry(self):
        """Test incrementing retry count"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='low_balance',
            event_key=f'low_balance:{self.company.id}:{self.user.id}:retry_test',
            title='Low Balance',
            is_critical=True
        )
        
        assert notification.retry_count == 0
        
        notification.increment_retry()
        assert notification.retry_count == 1
        
        notification.increment_retry()
        assert notification.retry_count == 2
    
    def test_should_retry(self):
        """Test retry logic"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='account_sync_failed',
            event_key=f'account_sync_failed:{self.company.id}:{self.user.id}:should_retry_test',
            title='Sync Failed',
            is_critical=True
        )
        
        # Should retry when retry count is low
        assert notification.should_retry() is True
        
        # Should not retry after max retries
        notification.retry_count = 3
        notification.save()
        assert notification.should_retry() is False
        
        # Should not retry if already delivered
        notification.retry_count = 0
        notification.delivery_status = 'delivered'
        notification.save()
        assert notification.should_retry() is False
    
    def test_get_unread_count(self):
        """Test getting unread count"""
        # Create some notifications
        for i in range(5):
            Notification.objects.create(
                company=self.company,
                user=self.user,
                event='account_connected',
                event_key=f'account_connected:{self.company.id}:{self.user.id}:count_{i}',
                title=f'Notification {i}'
            )
        
        # Mark some as read
        notifications = Notification.objects.filter(user=self.user)[:2]
        for n in notifications:
            n.mark_as_read()
        
        # Check unread count
        count = Notification.objects.filter(
            company=self.company,
            user=self.user,
            is_read=False
        ).count()
        assert count == 3
    
    def test_notification_ordering(self):
        """Test notification ordering"""
        # Create notifications with different timestamps
        old_notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='account_connected',
            event_key=f'account_connected:{self.company.id}:{self.user.id}:old',
            title='Old Notification'
        )
        old_notification.created_at = timezone.now() - timedelta(hours=2)
        old_notification.save()
        
        new_notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='payment_success',
            event_key=f'payment_success:{self.company.id}:{self.user.id}:new',
            title='New Notification'
        )
        
        # Get notifications (should be ordered by -created_at)
        notifications = list(Notification.objects.filter(user=self.user))
        
        assert notifications[0] == new_notification
        assert notifications[1] == old_notification
    
    def test_metadata_json_field(self):
        """Test metadata JSON field"""
        metadata = {
            'account_name': 'Test Bank',
            'balance': 1500.50,
            'currency': 'USD',
            'nested': {
                'key': 'value'
            }
        }
        
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='low_balance',
            event_key=f'low_balance:{self.company.id}:{self.user.id}:metadata_test',
            title='Low Balance',
            metadata=metadata,
            is_critical=True
        )
        
        # Reload from database
        notification.refresh_from_db()
        
        assert notification.metadata['account_name'] == 'Test Bank'
        assert notification.metadata['balance'] == 1500.50
        assert notification.metadata['nested']['key'] == 'value'
    
    def test_critical_notifications(self):
        """Test critical notification flags"""
        # Create critical notification
        critical_notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='payment_failed',
            event_key=f'payment_failed:{self.company.id}:{self.user.id}:critical_test',
            title='Payment Failed',
            is_critical=True
        )
        
        # Create non-critical notification
        normal_notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='report_ready',
            event_key=f'report_ready:{self.company.id}:{self.user.id}:normal_test',
            title='Report Ready',
            is_critical=False
        )
        
        assert critical_notification.is_critical is True
        assert normal_notification.is_critical is False
    
    def test_action_url(self):
        """Test action URL field"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='large_transaction',
            event_key=f'large_transaction:{self.company.id}:{self.user.id}:action_url_test',
            title='Large Transaction',
            action_url='/transactions/123'
        )
        
        assert notification.action_url == '/transactions/123'