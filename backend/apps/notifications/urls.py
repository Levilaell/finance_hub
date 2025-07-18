"""
Notifications app URLs
"""
from django.urls import path

from .views import (
    NotificationListView,
    NotificationDetailView,
    NotificationUpdateView,
    NotificationDeleteView,
    MarkAllAsReadView,
    UnreadCountView,
    DeleteAllReadView,
)

app_name = 'notifications'

urlpatterns = [
    # Notifications management
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<str:notification_id>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('<str:notification_id>/', NotificationUpdateView.as_view(), name='notification-update'),
    path('<str:notification_id>/', NotificationDeleteView.as_view(), name='notification-delete'),
    path('mark-all-read/', MarkAllAsReadView.as_view(), name='mark-all-read'),
    path('unread-count/', UnreadCountView.as_view(), name='unread-count'),
    path('delete-all-read/', DeleteAllReadView.as_view(), name='delete-all-read'),
]