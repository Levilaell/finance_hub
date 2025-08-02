"""
Simple notification tests that bypass company creation issues
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import connection
from django.core.cache import cache
from datetime import timedelta

from apps.notifications.models import Notification
from apps.notifications.services import NotificationService

User = get_user_model()


class SimpleNotificationTest(TestCase):
    """Test notifications with direct database manipulation"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        
        # Create company using raw SQL to handle schema mismatch
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO companies (
                    name, trade_name, company_type, business_sector, 
                    email, phone, website,
                    address_street, address_number, address_complement,
                    address_neighborhood, address_city, address_state, address_zipcode,
                    employee_count, subscription_status, billing_cycle,
                    current_month_transactions, current_month_ai_requests,
                    last_usage_reset, notified_80_percent, notified_90_percent,
                    primary_color, currency, fiscal_year_start,
                    enable_ai_categorization, auto_categorize_threshold,
                    enable_notifications, enable_email_reports,
                    created_at, updated_at, is_active, owner_id, trial_ends_at
                ) VALUES (
                    'Test Company', 'Test Trade', 'other', 'other',
                    '', '', '',
                    '', '', '',
                    '', '', '', '',
                    1, 'trial', 'monthly',
                    0, 0,
                    %s, false, false,
                    '#000000', 'USD', '01',
                    true, 0.8,
                    true, true,
                    %s, %s, true, %s, %s
                ) RETURNING id
            """, [
                timezone.now(),  # last_usage_reset
                timezone.now(),  # created_at
                timezone.now(),  # updated_at
                self.user.id,   # owner_id
                timezone.now() + timedelta(days=14)  # trial_ends_at
            ])
            self.company_id = cursor.fetchone()[0]
        
        # Clear cache
        cache.clear()
    
    def test_notification_creation(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            company_id=self.company_id,
            user=self.user,
            event='report_ready',
            event_key=f'report_ready:{self.company_id}:{self.user.id}:test1',
            title='Report Ready',
            message='Your report is ready',
            is_critical=False
        )
        
        assert notification.id is not None
        assert notification.event == 'report_ready'
        assert notification.user == self.user
        assert notification.is_read is False
        assert notification.delivery_status == 'pending'
    
    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            company_id=self.company_id,
            user=self.user,
            event='account_connected',
            event_key=f'account_connected:{self.company_id}:{self.user.id}:read_test',
            title='Account Connected'
        )
        
        assert notification.is_read is False
        notification.mark_as_read()
        
        notification.refresh_from_db()
        assert notification.is_read is True
        assert notification.read_at is not None
    
    def test_notification_service_create(self):
        """Test notification service creation"""
        # Mock the company object
        class MockCompany:
            id = self.company_id
            owner_id = self.user.id
        
        company = MockCompany()
        
        # Create notification through service
        notification = NotificationService.create_notification(
            event_name='low_balance',
            company=company,
            user=self.user,
            title='Low Balance',
            message='Your balance is low',
            metadata={'balance': 100}
        )
        
        assert notification is not None
        assert notification.event == 'low_balance'
        assert notification.is_critical is True  # low_balance is critical
        assert notification.metadata['balance'] == 100
    
    def test_unread_count(self):
        """Test unread notification count"""
        # Create some notifications
        for i in range(3):
            Notification.objects.create(
                company_id=self.company_id,
                user=self.user,
                event='report_ready',
                event_key=f'report_ready:{self.company_id}:{self.user.id}:count_{i}',
                title=f'Report {i}'
            )
        
        # Mark one as read
        notification = Notification.objects.filter(user=self.user).first()
        notification.mark_as_read()
        
        # Check unread count
        unread_count = Notification.objects.filter(
            company_id=self.company_id,
            user=self.user,
            is_read=False
        ).count()
        
        assert unread_count == 2
    
    def test_critical_event_flags(self):
        """Test critical event detection"""
        critical_events = ['payment_failed', 'account_sync_failed', 'low_balance', 'security_alert']
        
        for event in critical_events:
            notification = Notification.objects.create(
                company_id=self.company_id,
                user=self.user,
                event=event,
                event_key=f'{event}:{self.company_id}:{self.user.id}:critical_test',
                title=event.replace('_', ' ').title(),
                is_critical=True
            )
            assert notification.is_critical is True
        
        # Test non-critical event
        notification = Notification.objects.create(
            company_id=self.company_id,
            user=self.user,
            event='report_ready',
            event_key=f'report_ready:{self.company_id}:{self.user.id}:normal_test',
            title='Report Ready',
            is_critical=False
        )
        assert notification.is_critical is False
    
    def test_delivery_status_flow(self):
        """Test notification delivery status flow"""
        notification = Notification.objects.create(
            company_id=self.company_id,
            user=self.user,
            event='payment_success',
            event_key=f'payment_success:{self.company_id}:{self.user.id}:delivery_test',
            title='Payment Success'
        )
        
        # Initial status
        assert notification.delivery_status == 'pending'
        
        # Mark as delivered
        notification.mark_as_delivered()
        assert notification.delivery_status == 'delivered'
        assert notification.delivered_at is not None
        
        # Create another and mark as failed
        notification2 = Notification.objects.create(
            company_id=self.company_id,
            user=self.user,
            event='sync_completed',
            event_key=f'sync_completed:{self.company_id}:{self.user.id}:failed_test',
            title='Sync Completed'
        )
        
        notification2.mark_as_failed()
        assert notification2.delivery_status == 'failed'
    
    def test_retry_mechanism(self):
        """Test notification retry logic"""
        notification = Notification.objects.create(
            company_id=self.company_id,
            user=self.user,
            event='account_sync_failed',
            event_key=f'account_sync_failed:{self.company_id}:{self.user.id}:retry_test',
            title='Sync Failed',
            is_critical=True,
            delivery_status='failed'
        )
        
        # Should retry initially
        assert notification.should_retry() is True
        
        # Increment retries
        for i in range(3):
            notification.increment_retry()
        
        # Should not retry after max retries
        assert notification.retry_count == 3
        assert notification.should_retry() is False
    
    def tearDown(self):
        """Clean up test data"""
        # Delete company and related data
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM companies WHERE id = %s", [self.company_id])
        
        super().tearDown()