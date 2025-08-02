"""
Test cases for Notification API views
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
import json
from datetime import timedelta

from apps.notifications.models import Notification
from apps.companies.models import Company

User = get_user_model()


class NotificationViewTest(TestCase):
    """Test Notification API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test company
        self.company = Company.objects.create(
            name="Test Company",
            document_number="12345678901234",
            plan_name="premium",
            is_active=True
        )
        
        # Create test users
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        
        self.other_user = User.objects.create_user(
            email="other@example.com",
            username="otheruser",
            password="testpass123"
        )
        
        # Set company owner
        self.company.owner = self.user
        self.company.save()
        
        # Create another company and user for isolation testing
        self.other_company = Company.objects.create(
            name="Other Company",
            document_number="98765432109876"
        )
        
        self.other_company.owner = self.other_user
        self.other_company.save()
        
        # Authenticate user
        self.client.force_authenticate(user=self.user)
    
    def test_list_notifications(self):
        """Test listing notifications"""
        # Create test notifications
        for i in range(5):
            Notification.objects.create(
                company=self.company,
                user=self.user,
                event='report_ready',
                title=f'Report {i}',
                message=f'Your report {i} is ready'
            )
        
        # Create notification for other user (shouldn't be visible)
        Notification.objects.create(
            company=self.other_company,
            user=self.other_user,
            event='account_connected',
            title='Other User Notification'
        )
        
        response = self.client.get(reverse('notifications:notification-list'))
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
        assert len(response.data['results']) == 5
    
    def test_list_notifications_pagination(self):
        """Test notification list pagination"""
        # Create 25 notifications
        for i in range(25):
            Notification.objects.create(
                company=self.company,
                user=self.user,
                event='low_balance',
                title=f'Alert {i}'
            )
        
        # First page
        response = self.client.get(reverse('notifications:notification-list'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 25
        assert len(response.data['results']) == 20  # Default page size
        
        # Second page
        response = self.client.get(
            reverse('notifications:notification-list'),
            {'page': 2}
        )
        assert len(response.data['results']) == 5
    
    def test_filter_notifications_by_read_status(self):
        """Test filtering notifications by read status"""
        # Create mix of read and unread notifications
        for i in range(3):
            notification = Notification.objects.create(
                company=self.company,
                user=self.user,
                event='account_connected',
                title=f'Notification {i}'
            )
            if i < 2:
                notification.mark_as_read()
        
        # Filter unread
        response = self.client.get(
            reverse('notifications:notification-list'),
            {'is_read': 'false'}
        )
        assert response.data['count'] == 1
        
        # Filter read
        response = self.client.get(
            reverse('notifications:notification-list'),
            {'is_read': 'true'}
        )
        assert response.data['count'] == 2
    
    def test_filter_notifications_by_event(self):
        """Test filtering notifications by event type"""
        # Create notifications with different events
        events = ['account_connected', 'payment_failed', 'report_ready']
        for event in events:
            for i in range(2):
                Notification.objects.create(
                    company=self.company,
                    user=self.user,
                    event=event,
                    title=f'{event} {i}'
                )
        
        # Filter by event
        response = self.client.get(
            reverse('notifications:notification-list'),
            {'event': 'payment_failed'}
        )
        assert response.data['count'] == 2
        for notification in response.data['results']:
            assert notification['event'] == 'payment_failed'
    
    def test_filter_critical_notifications(self):
        """Test filtering critical notifications"""
        # Create mix of critical and normal notifications
        Notification.objects.create(
            company=self.company,
            user=self.user,
            event='payment_failed',
            title='Critical',
            is_critical=True
        )
        
        Notification.objects.create(
            company=self.company,
            user=self.user,
            event='report_ready',
            title='Normal',
            is_critical=False
        )
        
        response = self.client.get(
            reverse('notifications:notification-list'),
            {'is_critical': 'true'}
        )
        assert response.data['count'] == 1
        assert response.data['results'][0]['is_critical'] is True
    
    def test_get_notification_detail(self):
        """Test retrieving single notification"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='large_transaction',
            title='Large Transaction',
            message='$5,000 transaction detected',
            metadata={'amount': 5000, 'currency': 'USD'}
        )
        
        response = self.client.get(
            reverse('notifications:notification-detail', args=[notification.id])
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(notification.id)
        assert response.data['title'] == 'Large Transaction'
        assert response.data['metadata']['amount'] == 5000
    
    def test_cannot_access_other_user_notification(self):
        """Test user cannot access other user's notifications"""
        # Create notification for other user
        other_notification = Notification.objects.create(
            company=self.other_company,
            user=self.other_user,
            event='account_connected',
            title='Private Notification'
        )
        
        response = self.client.get(
            reverse('notifications:notification-detail', args=[other_notification.id])
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_mark_notification_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='report_ready',
            title='Report Ready',
            is_read=False
        )
        
        response = self.client.post(
            reverse('notifications:notification-mark-read', args=[notification.id])
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        notification.refresh_from_db()
        assert notification.is_read is True
        assert notification.read_at is not None
    
    def test_mark_all_notifications_as_read(self):
        """Test marking all notifications as read"""
        # Create unread notifications
        for i in range(3):
            Notification.objects.create(
                company=self.company,
                user=self.user,
                event='low_balance',
                title=f'Alert {i}',
                is_read=False
            )
        
        response = self.client.post(reverse('notifications:notification-mark-all-read'))
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'All notifications marked as read'
        assert response.data['count'] == 3
        
        # Check all are marked as read
        unread_count = Notification.objects.filter(
            user=self.user,
            is_read=False
        ).count()
        assert unread_count == 0
    
    def test_get_unread_count(self):
        """Test getting unread notification count"""
        # Create mix of read and unread
        for i in range(5):
            notification = Notification.objects.create(
                company=self.company,
                user=self.user,
                event='account_connected',
                title=f'Notification {i}'
            )
            if i >= 3:
                notification.mark_as_read()
        
        response = self.client.get(reverse('notifications:notification-unread-count'))
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
    
    @patch('apps.notifications.services.NotificationService.get_pending_notifications')
    def test_get_pending_notifications(self, mock_get_pending):
        """Test getting pending notifications for polling"""
        # Mock pending notifications
        mock_notifications = [
            Notification(
                id='123',
                company=self.company,
                user=self.user,
                event='payment_failed',
                title='Payment Failed',
                delivery_status='pending'
            )
        ]
        mock_get_pending.return_value = mock_notifications
        
        response = self.client.get(reverse('notifications:notification-pending'))
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['notifications']) == 1
        mock_get_pending.assert_called_once_with(self.user, self.company)
    
    def test_delete_notification(self):
        """Test deleting a notification"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='report_ready',
            title='Report Ready'
        )
        
        response = self.client.delete(
            reverse('notifications:notification-detail', args=[notification.id])
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Notification.objects.filter(id=notification.id).exists()
    
    def test_notification_ordering(self):
        """Test notifications are ordered by created_at descending"""
        # Create notifications with different timestamps
        old_notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='report_ready',
            title='Old'
        )
        old_notification.created_at = timezone.now() - timedelta(hours=2)
        old_notification.save()
        
        new_notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='report_ready',
            title='New'
        )
        
        response = self.client.get(reverse('notifications:notification-list'))
        
        results = response.data['results']
        assert results[0]['title'] == 'New'
        assert results[1]['title'] == 'Old'
    
    def test_unauthenticated_access(self):
        """Test unauthenticated users cannot access notifications"""
        self.client.force_authenticate(user=None)
        
        response = self.client.get(reverse('notifications:notification-list'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_notification_serialization(self):
        """Test notification serialization includes all fields"""
        notification = Notification.objects.create(
            company=self.company,
            user=self.user,
            event='large_transaction',
            title='Large Transaction',
            message='Transaction detected',
            metadata={'amount': 1000},
            action_url='/transactions',
            is_critical=True
        )
        
        response = self.client.get(
            reverse('notifications:notification-detail', args=[notification.id])
        )
        
        data = response.data
        assert 'id' in data
        assert 'event' in data
        assert 'title' in data
        assert 'message' in data
        assert 'metadata' in data
        assert 'action_url' in data
        assert 'is_critical' in data
        assert 'is_read' in data
        assert 'created_at' in data
        assert 'read_at' in data