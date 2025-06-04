"""
Notification signals for real-time WebSocket updates
"""
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification


@receiver(post_save, sender=Notification)
def send_realtime_notification(sender, instance, created, **kwargs):
    """
    Send real-time notification via WebSocket when a new notification is created
    """
    if created:
        send_notification_websocket(instance)


def send_notification_websocket(notification):
    """
    Send notification via WebSocket to the user
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    # Prepare notification data
    notification_data = {
        'type': 'notification_message',
        'message': {
            'id': str(notification.id),
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'priority': notification.priority,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
            'action_url': notification.action_url,
            'data': notification.data,
        }
    }
    
    # Send to user's notification group
    group_name = f"notifications_{notification.user.id}"
    async_to_sync(channel_layer.group_send)(
        group_name,
        notification_data
    )