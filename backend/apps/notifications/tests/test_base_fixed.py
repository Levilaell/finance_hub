"""
Fixed test base that works with existing database schema
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import connection
from datetime import timedelta

from apps.notifications.models import Notification
from apps.notifications.services import NotificationService

User = get_user_model()


class FixedNotificationTestCase(TestCase):
    """Test case that handles the database schema mismatch gracefully"""
    
    def setUp(self):
        """Set up test data with all required fields"""
        # Create user
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        
        # Create company with ALL required fields from database schema
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO companies (
                    name, trade_name, company_type, business_sector,
                    email, phone, website,
                    address_street, address_number, address_complement,
                    address_neighborhood, address_city, address_state, address_zipcode,
                    monthly_revenue, employee_count, subscription_status, billing_cycle,
                    current_month_transactions, current_month_ai_requests,
                    last_usage_reset, notified_80_percent, notified_90_percent,
                    primary_color, currency, fiscal_year_start,
                    enable_ai_categorization, auto_categorize_threshold,
                    enable_notifications, enable_email_reports,
                    created_at, updated_at, is_active, owner_id, trial_ends_at
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s, %s, %s
                ) RETURNING id
            """, [
                'Test Company',          # name
                'Test Trade',           # trade_name  
                'other',                # company_type
                'other',                # business_sector
                'test@company.com',     # email
                '123-456-7890',         # phone
                'https://test.com',     # website
                'Test Street',          # address_street
                '123',                  # address_number
                'Apt 1',               # address_complement
                'Test Neighborhood',    # address_neighborhood
                'Test City',           # address_city
                'TS',                  # address_state
                '12345-678',           # address_zipcode
                1000.00,               # monthly_revenue
                1,                     # employee_count
                'trial',               # subscription_status
                'monthly',             # billing_cycle
                0,                     # current_month_transactions
                0,                     # current_month_ai_requests
                timezone.now(),        # last_usage_reset
                False,                 # notified_80_percent
                False,                 # notified_90_percent
                '#000000',             # primary_color
                'USD',                 # currency
                '01',                  # fiscal_year_start
                True,                  # enable_ai_categorization
                0.8,                   # auto_categorize_threshold
                True,                  # enable_notifications
                True,                  # enable_email_reports
                timezone.now(),        # created_at
                timezone.now(),        # updated_at
                True,                  # is_active
                self.user.id,          # owner_id
                timezone.now() + timedelta(days=14)  # trial_ends_at
            ])
            self.company_id = cursor.fetchone()[0]
    
    def tearDown(self):
        """Clean up test data"""
        # Delete notifications first (foreign key constraint)
        Notification.objects.filter(company_id=self.company_id).delete()
        
        # Delete company
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM companies WHERE id = %s", [self.company_id])
            
        super().tearDown()


class TestNotificationWithFixedSchema(FixedNotificationTestCase):
    """Test notifications with proper schema handling"""
    
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
        
        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.event, 'report_ready')
        self.assertEqual(notification.user, self.user)
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.delivery_status, 'pending')
    
    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            company_id=self.company_id,
            user=self.user,
            event='account_connected',
            event_key=f'account_connected:{self.company_id}:{self.user.id}:read_test',
            title='Account Connected'
        )
        
        self.assertFalse(notification.is_read)
        notification.mark_as_read()
        
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
    
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
            self.assertTrue(notification.is_critical)
        
        # Test non-critical event
        notification = Notification.objects.create(
            company_id=self.company_id,
            user=self.user,
            event='report_ready',
            event_key=f'report_ready:{self.company_id}:{self.user.id}:normal_test',
            title='Report Ready',
            is_critical=False
        )
        self.assertFalse(notification.is_critical)
    
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
        self.assertEqual(notification.delivery_status, 'pending')
        
        # Mark as delivered
        notification.mark_as_delivered()
        self.assertEqual(notification.delivery_status, 'delivered')
        self.assertIsNotNone(notification.delivered_at)
        
        # Create another and mark as failed
        notification2 = Notification.objects.create(
            company_id=self.company_id,
            user=self.user,
            event='sync_completed',
            event_key=f'sync_completed:{self.company_id}:{self.user.id}:failed_test',
            title='Sync Completed'
        )
        
        notification2.mark_as_failed()
        self.assertEqual(notification2.delivery_status, 'failed')
    
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
        
        self.assertEqual(unread_count, 2)