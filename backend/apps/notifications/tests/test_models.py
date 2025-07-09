"""
Test notifications models
Tests for NotificationTemplate, Notification, NotificationPreference, and NotificationLog models
"""
from datetime import time, datetime, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from apps.companies.models import Company, SubscriptionPlan
from apps.notifications.models import (
    NotificationTemplate, 
    Notification, 
    NotificationPreference,
    NotificationLog
)

User = get_user_model()


class TestNotificationTemplateModel(TestCase):
    """Test NotificationTemplate model"""
    
    def setUp(self):
        self.template = NotificationTemplate.objects.create(
            name='Low Balance Alert',
            notification_type='low_balance',
            title_template='Alerta: Saldo baixo em {account_name}',
            message_template='Seu saldo está abaixo de R$ {threshold}. Saldo atual: R$ {balance}',
            send_email=True,
            send_push=True,
            send_sms=False
        )
    
    def test_create_notification_template(self):
        """Test creating a notification template"""
        self.assertEqual(self.template.name, 'Low Balance Alert')
        self.assertEqual(self.template.notification_type, 'low_balance')
        self.assertTrue(self.template.send_email)
        self.assertTrue(self.template.send_push)
        self.assertFalse(self.template.send_sms)
        self.assertTrue(self.template.is_active)
        self.assertTrue(self.template.is_system)
    
    def test_template_string_representation(self):
        """Test notification template string representation"""
        expected = "Low Balance Alert (Saldo Baixo)"
        self.assertEqual(str(self.template), expected)
    
    def test_notification_type_choices(self):
        """Test all notification type choices"""
        valid_types = [
            'low_balance', 'large_transaction', 'recurring_payment',
            'sync_error', 'report_ready', 'subscription_expiring',
            'user_invited', 'budget_exceeded', 'ai_insight', 'custom'
        ]
        
        for notification_type in valid_types:
            template = NotificationTemplate.objects.create(
                name=f'Test {notification_type}',
                notification_type=notification_type,
                title_template='Test Title',
                message_template='Test Message'
            )
            self.assertEqual(template.notification_type, notification_type)
    
    def test_template_with_variables(self):
        """Test template with variable placeholders"""
        template = NotificationTemplate.objects.create(
            name='Transaction Alert',
            notification_type='large_transaction',
            title_template='Transação de R$ {amount} detectada',
            message_template='Uma transação de R$ {amount} foi realizada em {account_name} por {merchant}'
        )
        
        self.assertIn('{amount}', template.title_template)
        self.assertIn('{account_name}', template.message_template)
        self.assertIn('{merchant}', template.message_template)
    
    def test_channel_configuration(self):
        """Test notification channel configuration"""
        template = NotificationTemplate.objects.create(
            name='SMS Only Alert',
            notification_type='custom',
            title_template='SMS Alert',
            message_template='SMS only notification',
            send_email=False,
            send_push=False,
            send_sms=True
        )
        
        self.assertFalse(template.send_email)
        self.assertFalse(template.send_push)
        self.assertTrue(template.send_sms)
    
    def test_template_activation(self):
        """Test template activation/deactivation"""
        self.assertTrue(self.template.is_active)
        
        self.template.is_active = False
        self.template.save()
        
        self.assertFalse(self.template.is_active)
    
    def test_timestamp_fields(self):
        """Test created_at and updated_at timestamps"""
        self.assertIsNotNone(self.template.created_at)
        self.assertIsNotNone(self.template.updated_at)
        
        # Update template
        original_updated = self.template.updated_at
        self.template.name = 'Updated Name'
        self.template.save()
        
        self.assertGreater(self.template.updated_at, original_updated)


class TestNotificationModel(TestCase):
    """Test Notification model"""
    
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
        
        # Create template
        self.template = NotificationTemplate.objects.create(
            name='Report Ready',
            notification_type='report_ready',
            title_template='Seu relatório está pronto',
            message_template='O relatório {report_name} foi gerado com sucesso.'
        )
        
        # Create notification
        self.notification = Notification.objects.create(
            user=self.user,
            company=self.company,
            template=self.template,
            notification_type='report_ready',
            title='Seu relatório está pronto',
            message='O relatório Resumo Mensal foi gerado com sucesso.',
            priority='high',
            action_url='/reports/123/'
        )
    
    def test_create_notification(self):
        """Test creating a notification"""
        self.assertEqual(self.notification.user, self.user)
        self.assertEqual(self.notification.company, self.company)
        self.assertEqual(self.notification.template, self.template)
        self.assertEqual(self.notification.notification_type, 'report_ready')
        self.assertEqual(self.notification.priority, 'high')
        self.assertFalse(self.notification.is_read)
        self.assertIsNone(self.notification.read_at)
    
    def test_notification_string_representation(self):
        """Test notification string representation"""
        expected = f"Seu relatório está pronto - {self.user.email}"
        self.assertEqual(str(self.notification), expected)
    
    def test_notification_with_data(self):
        """Test notification with additional data"""
        data = {
            'report_id': 123,
            'report_type': 'monthly_summary',
            'period': '2025-01'
        }
        
        notification = Notification.objects.create(
            user=self.user,
            notification_type='report_ready',
            title='Report Generated',
            message='Your report is ready',
            data=data
        )
        
        self.assertEqual(notification.data['report_id'], 123)
        self.assertEqual(notification.data['report_type'], 'monthly_summary')
        self.assertEqual(notification.data['period'], '2025-01')
    
    def test_mark_as_read(self):
        """Test marking notification as read"""
        self.assertFalse(self.notification.is_read)
        self.assertIsNone(self.notification.read_at)
        
        self.notification.is_read = True
        self.notification.read_at = timezone.now()
        self.notification.save()
        
        self.assertTrue(self.notification.is_read)
        self.assertIsNotNone(self.notification.read_at)
    
    def test_priority_levels(self):
        """Test all priority levels"""
        priorities = ['low', 'medium', 'high', 'urgent']
        
        for priority in priorities:
            notification = Notification.objects.create(
                user=self.user,
                notification_type='custom',
                title=f'{priority} priority notification',
                message='Test message',
                priority=priority
            )
            self.assertEqual(notification.priority, priority)
    
    def test_delivery_status_tracking(self):
        """Test delivery status tracking"""
        self.assertFalse(self.notification.email_sent)
        self.assertIsNone(self.notification.email_sent_at)
        
        # Mark email as sent
        self.notification.email_sent = True
        self.notification.email_sent_at = timezone.now()
        self.notification.save()
        
        self.assertTrue(self.notification.email_sent)
        self.assertIsNotNone(self.notification.email_sent_at)
        
        # Check push and SMS status
        self.assertFalse(self.notification.push_sent)
        self.assertFalse(self.notification.sms_sent)
    
    def test_notification_without_company(self):
        """Test notification without company (system notification)"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='subscription_expiring',
            title='Subscription Expiring',
            message='Your subscription expires in 7 days',
            priority='urgent'
        )
        
        self.assertIsNone(notification.company)
        self.assertEqual(notification.user, self.user)
    
    def test_notification_expiration(self):
        """Test notification with expiration date"""
        expires_at = timezone.now() + timedelta(days=7)
        
        notification = Notification.objects.create(
            user=self.user,
            notification_type='custom',
            title='Limited Time Offer',
            message='This offer expires soon',
            expires_at=expires_at
        )
        
        self.assertEqual(notification.expires_at, expires_at)
    
    def test_notification_ordering(self):
        """Test notifications are ordered by created_at descending"""
        # Create older notification
        older = Notification.objects.create(
            user=self.user,
            notification_type='custom',
            title='Older notification',
            message='Created first'
        )
        
        # Create newer notification
        newer = Notification.objects.create(
            user=self.user,
            notification_type='custom',
            title='Newer notification',
            message='Created second'
        )
        
        notifications = list(Notification.objects.all())
        # Newer should come first due to -created_at ordering
        self.assertEqual(notifications[0], newer)
        self.assertEqual(notifications[1], older)


class TestNotificationPreferenceModel(TestCase):
    """Test NotificationPreference model"""
    
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create preferences
        self.preferences = NotificationPreference.objects.create(
            user=self.user,
            email_enabled=True,
            push_enabled=True,
            sms_enabled=False,
            low_balance_threshold=Decimal('500.00'),
            large_transaction_threshold=Decimal('10000.00')
        )
    
    def test_create_notification_preferences(self):
        """Test creating notification preferences"""
        self.assertEqual(self.preferences.user, self.user)
        self.assertTrue(self.preferences.email_enabled)
        self.assertTrue(self.preferences.push_enabled)
        self.assertFalse(self.preferences.sms_enabled)
        self.assertEqual(self.preferences.low_balance_threshold, Decimal('500.00'))
        self.assertEqual(self.preferences.large_transaction_threshold, Decimal('10000.00'))
    
    def test_preferences_string_representation(self):
        """Test preferences string representation"""
        expected = f"Preferences for {self.user.email}"
        self.assertEqual(str(self.preferences), expected)
    
    def test_one_to_one_relationship(self):
        """Test one-to-one relationship with user"""
        # Try to create another preference for same user
        with self.assertRaises(Exception):
            NotificationPreference.objects.create(
                user=self.user,
                email_enabled=False
            )
    
    def test_quiet_hours_configuration(self):
        """Test quiet hours configuration"""
        self.preferences.quiet_hours_start = time(22, 0)  # 10 PM
        self.preferences.quiet_hours_end = time(8, 0)     # 8 AM
        self.preferences.save()
        
        self.assertEqual(self.preferences.quiet_hours_start, time(22, 0))
        self.assertEqual(self.preferences.quiet_hours_end, time(8, 0))
    
    def test_digest_settings(self):
        """Test email digest settings"""
        self.assertFalse(self.preferences.send_daily_digest)
        self.assertTrue(self.preferences.send_weekly_digest)
        self.assertEqual(self.preferences.digest_time, '09:00')
        
        # Update digest settings
        self.preferences.send_daily_digest = True
        self.preferences.send_weekly_digest = False
        self.preferences.digest_time = time(18, 30)
        self.preferences.save()
        
        self.assertTrue(self.preferences.send_daily_digest)
        self.assertFalse(self.preferences.send_weekly_digest)
        self.assertEqual(self.preferences.digest_time, time(18, 30))
    
    def test_type_preferences(self):
        """Test notification type preferences"""
        type_prefs = {
            'low_balance': {'email': True, 'push': True, 'sms': False},
            'large_transaction': {'email': True, 'push': False, 'sms': True},
            'report_ready': {'email': False, 'push': True, 'sms': False}
        }
        
        self.preferences.type_preferences = type_prefs
        self.preferences.save()
        
        self.assertEqual(
            self.preferences.type_preferences['low_balance']['email'], 
            True
        )
        self.assertEqual(
            self.preferences.type_preferences['large_transaction']['sms'], 
            True
        )
        self.assertEqual(
            self.preferences.type_preferences['report_ready']['email'], 
            False
        )
    
    def test_threshold_values(self):
        """Test threshold value updates"""
        # Update thresholds
        self.preferences.low_balance_threshold = Decimal('2000.00')
        self.preferences.large_transaction_threshold = Decimal('50000.00')
        self.preferences.save()
        
        self.assertEqual(self.preferences.low_balance_threshold, Decimal('2000.00'))
        self.assertEqual(self.preferences.large_transaction_threshold, Decimal('50000.00'))
    
    def test_updated_at_timestamp(self):
        """Test updated_at timestamp"""
        original_updated = self.preferences.updated_at
        
        # Update preferences
        self.preferences.email_enabled = False
        self.preferences.save()
        
        self.assertGreater(self.preferences.updated_at, original_updated)


class TestNotificationLogModel(TestCase):
    """Test NotificationLog model"""
    
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create notification
        self.notification = Notification.objects.create(
            user=self.user,
            notification_type='low_balance',
            title='Low Balance Alert',
            message='Your balance is low',
            priority='high'
        )
    
    def test_create_successful_log(self):
        """Test creating a successful notification log"""
        log = NotificationLog.objects.create(
            notification=self.notification,
            channel='email',
            success=True,
            recipient='test@example.com',
            provider='sendgrid',
            provider_message_id='msg_123456'
        )
        
        self.assertEqual(log.notification, self.notification)
        self.assertEqual(log.channel, 'email')
        self.assertTrue(log.success)
        self.assertEqual(log.recipient, 'test@example.com')
        self.assertEqual(log.provider, 'sendgrid')
        self.assertEqual(log.provider_message_id, 'msg_123456')
        self.assertEqual(log.error_message, '')
    
    def test_create_failed_log(self):
        """Test creating a failed notification log"""
        log = NotificationLog.objects.create(
            notification=self.notification,
            channel='sms',
            success=False,
            recipient='+5511999999999',
            provider='twilio',
            error_message='Invalid phone number format'
        )
        
        self.assertEqual(log.channel, 'sms')
        self.assertFalse(log.success)
        self.assertEqual(log.error_message, 'Invalid phone number format')
        self.assertEqual(log.provider_message_id, '')
    
    def test_log_string_representation(self):
        """Test notification log string representation"""
        log = NotificationLog.objects.create(
            notification=self.notification,
            channel='push',
            success=True,
            recipient='device_token_123'
        )
        
        expected = "push - Low Balance Alert - Success"
        self.assertEqual(str(log), expected)
        
        # Test failed log
        failed_log = NotificationLog.objects.create(
            notification=self.notification,
            channel='email',
            success=False,
            recipient='test@example.com'
        )
        
        expected_failed = "email - Low Balance Alert - Failed"
        self.assertEqual(str(failed_log), expected_failed)
    
    def test_channel_choices(self):
        """Test all channel choices"""
        channels = ['email', 'push', 'sms', 'in_app']
        
        for channel in channels:
            log = NotificationLog.objects.create(
                notification=self.notification,
                channel=channel,
                success=True,
                recipient=f'recipient_{channel}'
            )
            self.assertEqual(log.channel, channel)
    
    def test_multiple_logs_per_notification(self):
        """Test multiple logs for same notification"""
        # Email attempt - success
        email_log = NotificationLog.objects.create(
            notification=self.notification,
            channel='email',
            success=True,
            recipient='test@example.com'
        )
        
        # Push attempt - failed
        push_log = NotificationLog.objects.create(
            notification=self.notification,
            channel='push',
            success=False,
            recipient='invalid_token',
            error_message='Invalid device token'
        )
        
        # SMS attempt - success
        sms_log = NotificationLog.objects.create(
            notification=self.notification,
            channel='sms',
            success=True,
            recipient='+5511999999999'
        )
        
        # Check all logs are associated with notification
        logs = self.notification.logs.all()
        self.assertEqual(logs.count(), 3)
        self.assertIn(email_log, logs)
        self.assertIn(push_log, logs)
        self.assertIn(sms_log, logs)
    
    def test_log_ordering(self):
        """Test logs are ordered by attempted_at descending"""
        # Create older log
        older_log = NotificationLog.objects.create(
            notification=self.notification,
            channel='email',
            success=True,
            recipient='test@example.com'
        )
        
        # Create newer log
        newer_log = NotificationLog.objects.create(
            notification=self.notification,
            channel='push',
            success=True,
            recipient='device_123'
        )
        
        logs = list(NotificationLog.objects.all())
        # Newer should come first due to -attempted_at ordering
        self.assertEqual(logs[0], newer_log)
        self.assertEqual(logs[1], older_log)
    
    def test_attempted_at_timestamp(self):
        """Test attempted_at is automatically set"""
        log = NotificationLog.objects.create(
            notification=self.notification,
            channel='in_app',
            success=True,
            recipient=self.user.username
        )
        
        self.assertIsNotNone(log.attempted_at)
        self.assertAlmostEqual(
            log.attempted_at, 
            timezone.now(), 
            delta=timedelta(seconds=1)
        )