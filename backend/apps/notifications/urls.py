"""
Simplified notifications app URLs
"""
from django.urls import path

from .views import (
    NotificationListView,
    NotificationDetailView,
    MarkAsReadView,
    UnreadCountView,
    PendingNotificationsView,
    NotificationDeleteView,
)

app_name = 'notifications'

urlpatterns = [
    # Core notification endpoints
    path('', NotificationListView.as_view(), name='notification-list'),
    path('detail/<str:notification_id>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('<str:notification_id>/', NotificationDeleteView.as_view(), name='notification-delete'),
    
    # Read management
    path('mark-read/', MarkAsReadView.as_view(), name='mark-all-read'),
    path('mark-read/<str:notification_id>/', MarkAsReadView.as_view(), name='mark-read'),
    
    # Status endpoints
    path('unread-count/', UnreadCountView.as_view(), name='unread-count'),
    path('pending/', PendingNotificationsView.as_view(), name='pending-notifications'),
]