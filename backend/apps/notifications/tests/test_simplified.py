"""
Simplified notification tests that work with current model schema
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.notifications.models import Notification
from apps.companies.models import Company

User = get_user_model()


class TestNotificationSimplified(TestCase):
    """Test notifications with simplified company model"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        
        # Create company with only the fields that exist in current model
        self.company = Company.objects.create(
            owner=self.user,
            name='Test Company',
            trade_name='Test Trade Name',
            subscription_status='trial',
            billing_cycle='monthly',
            trial_ends_at=timezone.now() + timedelta(days=14),
            current_month_transactions=0,
            current_month_ai_requests=0,
            is_active=True
        )
    
    def test_notification_creation(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='report_ready',
            event_key=f'report_ready:{self.company.id}:{self.user.id}:test1',
            title='Report Ready',
            message='Your report is ready',
            is_critical=False
        )
        
        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.event, 'report_ready')
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.company, self.company)
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.delivery_status, 'pending')
    
    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='account_connected',
            event_key=f'account_connected:{self.company.id}:{self.user.id}:read_test',
            title='Account Connected',
            message='Your account has been connected'
        )
        
        self.assertFalse(notification.is_read)
        notification.mark_as_read()
        
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
    
    def test_critical_notification(self):
        """Test critical notification"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='payment_failed',
            event_key=f'payment_failed:{self.company.id}:{self.user.id}:critical_test',
            title='Payment Failed',
            message='Payment could not be processed',
            is_critical=True
        )
        self.assertTrue(notification.is_critical)
    
    def test_delivery_status(self):
        """Test delivery status changes"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='sync_completed',
            event_key=f'sync_completed:{self.company.id}:{self.user.id}:delivery_test',
            title='Sync Completed'
        )
        
        # Initial status
        self.assertEqual(notification.delivery_status, 'pending')
        
        # Mark as delivered
        notification.mark_as_delivered()
        self.assertEqual(notification.delivery_status, 'delivered')
        self.assertIsNotNone(notification.delivered_at)
    
    def test_retry_mechanism(self):
        """Test retry logic"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='account_sync_failed',
            event_key=f'account_sync_failed:{self.company.id}:{self.user.id}:retry_test',
            title='Sync Failed',
            is_critical=True,
            delivery_status='failed'
        )
        
        # Should retry initially
        self.assertTrue(notification.should_retry())
        
        # Increment retries
        for i in range(3):
            notification.increment_retry()
        
        # Should not retry after max retries
        self.assertEqual(notification.retry_count, 3)
        self.assertFalse(notification.should_retry())
    
    def test_unread_count(self):
        """Test unread notification count"""
        # Create some notifications
        for i in range(3):
            Notification.objects.create(
                company=self.company,
                user=self.user,
                event='report_ready',
                event_key=f'report_ready:{self.company.id}:{self.user.id}:count_{i}',
                title=f'Report {i}',
                is_read=False
            )
        
        # Mark one as read
        notification = Notification.objects.filter(user=self.user).first()
        notification.mark_as_read()
        
        # Check unread count
        unread_count = Notification.objects.filter(
            company=self.company,
            user=self.user,
            is_read=False
        ).count()
        
        self.assertEqual(unread_count, 2)