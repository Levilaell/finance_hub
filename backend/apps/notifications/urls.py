"""
Notifications app URLs
"""
from django.urls import path

from .views import (
    NotificationListView,
    MarkAsReadView,
    MarkAllAsReadView,
    NotificationPreferencesView,
    UpdatePreferencesView,
    NotificationCountView,
    WebSocketHealthView,
)

app_name = 'notifications'

urlpatterns = [
    # Notifications management
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:notification_id>/read/', MarkAsReadView.as_view(), name='mark-as-read'),
    path('mark-all-read/', MarkAllAsReadView.as_view(), name='mark-all-read'),
    path('count/', NotificationCountView.as_view(), name='notification-count'),
    
    # Preferences
    path('preferences/', NotificationPreferencesView.as_view(), name='preferences'),
    path('preferences/update/', UpdatePreferencesView.as_view(), name='update-preferences'),
    
    # Health checks
    path('websocket/health/', WebSocketHealthView.as_view(), name='websocket-health'),
]