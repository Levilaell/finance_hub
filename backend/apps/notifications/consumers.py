"""
WebSocket consumers for real-time notifications and updates
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications
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
        logger.info(f"User {self.user.id} connected to notifications WebSocket")

    async def disconnect(self, close_code):
        """Leave notification group"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"User {self.user.id} disconnected from notifications WebSocket")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
                
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from user {self.user.id}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    async def notification_message(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        try:
            from .models import Notification
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.is_read = True
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False


class TransactionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time transaction updates
    """

    async def connect(self):
        """Accept WebSocket connection if user is authenticated"""
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return

        # Create user-specific transaction group
        self.group_name = f"transactions_{self.user.id}"
        
        # Join transaction group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"User {self.user.id} connected to transactions WebSocket")

    async def disconnect(self, close_code):
        """Leave transaction group"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"User {self.user.id} disconnected from transactions WebSocket")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from user {self.user.id}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    async def transaction_update(self, event):
        """Send transaction update to WebSocket"""
        await self.send(text_data=json.dumps(event['message']))

    async def balance_update(self, event):
        """Send balance update to WebSocket"""
        await self.send(text_data=json.dumps(event['message']))