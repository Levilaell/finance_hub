"""
Simplified WebSocket consumer for real-time notifications
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

from .services import NotificationService

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Simplified WebSocket consumer with reliability features
    """

    async def connect(self):
        """Accept WebSocket connection if user is authenticated"""
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return

        # Create user-specific notification group
        self.group_name = f"notifications_{self.user.id}"
        
        # Join notification group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        
        # Mark user as online
        await self.mark_user_online()
        
        # Send initial state
        unread_count = await self.get_unread_count()
        pending_notifications = await self.get_pending_notifications()
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'unread_count': unread_count,
            'pending_notifications': pending_notifications
        }))
        
        logger.info(f"User {self.user.id} connected to notifications WebSocket")

    async def disconnect(self, close_code):
        """Leave notification group and mark offline"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            
            # Mark user as offline
            await self.mark_user_offline()
            
            logger.info(f"User {self.user.id} disconnected from notifications WebSocket")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_read':
                # Mark single notification as read
                notification_id = data.get('notification_id')
                if notification_id:
                    success = await self.mark_notification_read(notification_id)
                    if success:
                        await self.send_read_confirmation(notification_id)
                        
            elif message_type == 'mark_all_read':
                # Mark all notifications as read
                count = await self.mark_all_notifications_read()
                await self.send(text_data=json.dumps({
                    'type': 'all_marked_read',
                    'count': count,
                    'unread_count': 0
                }))
                
            elif message_type == 'ack':
                # Acknowledge receipt of critical notification
                notification_id = data.get('notification_id')
                if notification_id:
                    await self.acknowledge_notification(notification_id)
                    
            elif message_type == 'ping':
                # Simple health check
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from user {self.user.id}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    async def notification_message(self, event):
        """
        Send new notification to WebSocket
        """
        notification = event.get('notification', {})
        
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': notification
        }))
        
        # Request acknowledgment for critical notifications
        if notification.get('is_critical'):
            await self.send(text_data=json.dumps({
                'type': 'ack_request',
                'notification_id': notification.get('id')
            }))

    async def unread_count_update(self, event):
        """
        Send updated unread count
        """
        count = event.get('count', 0)
        
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': count
        }))

    @database_sync_to_async
    def get_unread_count(self):
        """Get current unread notification count"""
        from .models import Notification
        
        company = getattr(self.user, 'company', None)
        if not company:
            return 0
            
        return Notification.get_unread_count(company, self.user)

    @database_sync_to_async
    def get_pending_notifications(self):
        """Get pending notifications for initial load"""
        from .models import Notification
        
        company = getattr(self.user, 'company', None)
        if not company:
            return []
        
        # Get recent undelivered notifications
        notifications = Notification.objects.filter(
            company=company,
            user=self.user,
            delivery_status='pending'
        ).order_by('-created_at')[:10]
        
        return [{
            'id': str(n.id),
            'event': n.event,
            'is_critical': n.is_critical,
            'title': n.title,
            'message': n.message,
            'metadata': n.metadata,
            'action_url': n.action_url,
            'created_at': n.created_at.isoformat(),
            'is_read': n.is_read
        } for n in notifications]

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark single notification as read"""
        try:
            from .models import Notification
            
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            
            if not notification.is_read:
                notification.mark_as_read()
                return True
            
            return False
            
        except Notification.DoesNotExist:
            logger.warning(f"Notification {notification_id} not found for user {self.user.id}")
            return False
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False

    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Mark all notifications as read"""
        try:
            from .models import Notification
            
            company = getattr(self.user, 'company', None)
            if not company:
                return 0
            
            # Update all unread notifications
            updated_count = Notification.objects.filter(
                company=company,
                user=self.user,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
            
            # Clear cache
            from django.core.cache import cache
            cache_key = f'notifications:unread_count:{company.id}:{self.user.id}'
            cache.delete(cache_key)
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return 0

    @database_sync_to_async
    def acknowledge_notification(self, notification_id):
        """Acknowledge receipt of critical notification"""
        try:
            from .models import Notification
            
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user,
                is_critical=True
            )
            
            # Mark as delivered if not already
            if notification.delivery_status == 'pending':
                notification.mark_as_delivered()
                
            logger.info(f"Notification {notification_id} acknowledged by user {self.user.id}")
            
        except Exception as e:
            logger.error(f"Error acknowledging notification: {e}")

    @database_sync_to_async
    def mark_user_online(self):
        """Mark user as online"""
        NotificationService.mark_user_online(self.user.id)

    @database_sync_to_async
    def mark_user_offline(self):
        """Mark user as offline"""
        NotificationService.mark_user_offline(self.user.id)
    
    async def send_read_confirmation(self, notification_id):
        """Send confirmation that notification was marked as read"""
        unread_count = await self.get_unread_count()
        
        await self.send(text_data=json.dumps({
            'type': 'notification_read',
            'notification_id': notification_id,
            'unread_count': unread_count
        }))