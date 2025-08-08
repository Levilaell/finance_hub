"""WebSocket consumers for real-time payment updates"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class PaymentStatusConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time payment status updates"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company_id = None
        self.payment_group_name = None
        self.user = None
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        
        # Require authentication
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        
        # Get company ID from user
        company = await self.get_user_company()
        if not company:
            await self.close()
            return
        
        self.company_id = str(company.id)
        self.payment_group_name = f'payment_updates_{self.company_id}'
        
        # Join company payment group
        await self.channel_layer.group_add(
            self.payment_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'status': 'connected',
            'company_id': self.company_id
        }))
        
        logger.info(f"Payment WebSocket connected for company {self.company_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.payment_group_name:
            # Leave payment group
            await self.channel_layer.group_discard(
                self.payment_group_name,
                self.channel_name
            )
        
        logger.info(f"Payment WebSocket disconnected for company {self.company_id}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Respond to ping with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            
            elif message_type == 'subscribe':
                # Subscribe to specific payment events
                event_types = data.get('events', [])
                await self.send(text_data=json.dumps({
                    'type': 'subscribed',
                    'events': event_types
                }))
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal error'
            }))
    
    # Event handlers for group messages
    
    async def payment_success(self, event):
        """Handle payment success notification"""
        await self.send(text_data=json.dumps({
            'type': 'payment_success',
            'payment_id': event.get('payment_id'),
            'subscription_id': event.get('subscription_id'),
            'amount': event.get('amount'),
            'currency': event.get('currency'),
            'timestamp': event.get('timestamp')
        }))
    
    async def payment_failed(self, event):
        """Handle payment failure notification"""
        await self.send(text_data=json.dumps({
            'type': 'payment_failed',
            'payment_id': event.get('payment_id'),
            'reason': event.get('reason'),
            'retry_available': event.get('retry_available', False),
            'timestamp': event.get('timestamp')
        }))
    
    async def subscription_updated(self, event):
        """Handle subscription update notification"""
        await self.send(text_data=json.dumps({
            'type': 'subscription_updated',
            'subscription_id': event.get('subscription_id'),
            'status': event.get('status'),
            'plan': event.get('plan'),
            'changes': event.get('changes', {}),
            'timestamp': event.get('timestamp')
        }))
    
    async def payment_method_updated(self, event):
        """Handle payment method update notification"""
        await self.send(text_data=json.dumps({
            'type': 'payment_method_updated',
            'payment_method_id': event.get('payment_method_id'),
            'action': event.get('action'),  # added, removed, updated
            'details': event.get('details', {}),
            'timestamp': event.get('timestamp')
        }))
    
    async def trial_ending(self, event):
        """Handle trial ending notification"""
        await self.send(text_data=json.dumps({
            'type': 'trial_ending',
            'days_remaining': event.get('days_remaining'),
            'trial_end_date': event.get('trial_end_date'),
            'timestamp': event.get('timestamp')
        }))
    
    async def usage_limit_warning(self, event):
        """Handle usage limit warning"""
        await self.send(text_data=json.dumps({
            'type': 'usage_limit_warning',
            'usage_type': event.get('usage_type'),
            'current': event.get('current'),
            'limit': event.get('limit'),
            'percentage': event.get('percentage'),
            'timestamp': event.get('timestamp')
        }))
    
    @database_sync_to_async
    def get_user_company(self):
        """Get user's current company"""
        return getattr(self.user, 'current_company', None)


class PaymentCheckoutConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for checkout session status"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.checkout_group_name = None
    
    async def connect(self):
        """Handle WebSocket connection for checkout status"""
        # Get session ID from URL route
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        
        if not self.session_id:
            await self.close()
            return
        
        self.checkout_group_name = f'checkout_{self.session_id}'
        
        # Join checkout session group
        await self.channel_layer.group_add(
            self.checkout_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial status
        await self.send(text_data=json.dumps({
            'type': 'checkout_status',
            'status': 'monitoring',
            'session_id': self.session_id
        }))
    
    async def disconnect(self, close_code):
        """Handle disconnection"""
        if self.checkout_group_name:
            await self.channel_layer.group_discard(
                self.checkout_group_name,
                self.channel_name
            )
    
    async def checkout_completed(self, event):
        """Handle checkout completion"""
        await self.send(text_data=json.dumps({
            'type': 'checkout_completed',
            'session_id': event.get('session_id'),
            'subscription_id': event.get('subscription_id'),
            'status': 'success',
            'timestamp': event.get('timestamp')
        }))
    
    async def checkout_failed(self, event):
        """Handle checkout failure"""
        await self.send(text_data=json.dumps({
            'type': 'checkout_failed',
            'session_id': event.get('session_id'),
            'reason': event.get('reason'),
            'status': 'failed',
            'timestamp': event.get('timestamp')
        }))