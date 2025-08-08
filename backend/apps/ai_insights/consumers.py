"""
WebSocket consumers for AI Insights real-time chat
"""
import json
import logging
from typing import Dict, Any
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.db import transaction
import asyncio

from apps.authentication.models import User
from apps.companies.models import Company
from .models import AIConversation, AIMessage, AICredit
from .services.ai_service import AIService
from .services.credit_service import CreditService, InsufficientCreditsError
from .websocket_security import WebSocketSecurityMixin

logger = logging.getLogger(__name__)


class ChatConsumer(WebSocketSecurityMixin, AsyncWebsocketConsumer):
    """WebSocket consumer for AI chat conversations with enhanced security"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai_service = AIService()
        self.credit_service = CreditService()
        self.conversation_id = None
        self.room_group_name = None
        self.user = None
        self.company = None
        
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
            self.room_group_name = f'chat_{self.conversation_id}'
            
            # Validate conversation_id format
            if not self.conversation_id or not str(self.conversation_id).isdigit():
                await self.close(code=4000)  # Bad request
                return
            
            # Authenticate user from query string token
            auth_result = await self.authenticate_user()
            if not auth_result:
                logger.warning(f"Authentication failed for conversation {self.conversation_id}")
                await self.close(code=4001)  # Unauthorized
                return
            
            # Verify user has permission to access this conversation
            permission_result = await self.has_permission()
            if not permission_result:
                logger.warning(f"Permission denied for user {self.user.id} to conversation {self.conversation_id}")
                await self.close(code=4003)  # Forbidden
                return
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Get initial credits balance
            credits_balance = await self.get_credits_balance()
            
            # Send connection established message with enhanced info
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Conectado ao Assistente Financeiro AI',
                'conversation_id': str(self.conversation_id),
                'user_id': str(self.user.id),
                'company_id': str(self.company.id),
                'credits_available': credits_balance,
                'timestamp': timezone.now().isoformat()
            }))
            
            logger.info(f"WebSocket connected: User {self.user.id} to conversation {self.conversation_id}")
            
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {str(e)}", exc_info=True)
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        logger.info(f"WebSocket disconnected: User {self.user.id if self.user else 'Unknown'} from conversation {self.conversation_id}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages with security checks"""
        try:
            # Update activity timestamp
            await self.update_activity()
            
            # Check activity timeout
            if not await self.check_activity_timeout():
                return
            
            # Validate message size
            if not await self.validate_message_size(text_data):
                return
            
            # Parse and sanitize message
            data = json.loads(text_data)
            data = await self.sanitize_message(data)
            
            message_type = data.get('type', 'message')
            
            # Check rate limiting for messages
            if hasattr(self.scope, 'rate_limiter'):
                if not self.scope['rate_limiter'].check_message_rate(str(self.user.id)):
                    await self.send_error("Rate limit exceeded. Please slow down.", error_code="RATE_LIMITED")
                    return
            
            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)
            elif message_type == 'ping':
                # Handle ping for connection keep-alive
                await self.send(text_data=json.dumps({'type': 'pong'}))
            else:
                await self.send_error(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format", error_code="INVALID_JSON")
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}", exc_info=True)
            await self.send_error("Error processing message", error_code="PROCESSING_ERROR")
    
    async def handle_message(self, data: Dict[str, Any]):
        """Process incoming chat message"""
        try:
            message_content = data.get('message', '').strip()
            
            # Validate message content
            if not message_content:
                await self.send_error("Message content cannot be empty", error_code="EMPTY_MESSAGE")
                return
            
            if len(message_content) > 4000:  # Max message length
                await self.send_error("Message too long. Maximum 4000 characters.", error_code="MESSAGE_TOO_LONG")
                return
            
            # Check rate limiting (basic implementation)
            if not await self.check_rate_limit():
                await self.send_error("Rate limit exceeded. Please wait before sending another message.", error_code="RATE_LIMITED")
                return
            
            # Check credits before processing
            credits_available = await self.get_credits_balance()
            if credits_available <= 0:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'error': 'insufficient_credits',
                    'error_code': 'INSUFFICIENT_CREDITS',
                    'message': 'Créditos insuficientes. Compre mais créditos para continuar.',
                    'credits_remaining': 0
                }))
                return
            
            # Send typing indicator
            await self.send(text_data=json.dumps({
                'type': 'assistant_typing',
                'typing': True,
                'timestamp': timezone.now().isoformat()
            }))
            
            # Process message with AI service
            response = await self.process_ai_message(message_content)
            
            # Send AI response with enhanced structure
            await self.send(text_data=json.dumps({
                'type': 'ai_response',
                'success': True,
                'data': {
                    'message': response['content'],
                    'message_id': response['message_id'],
                    'credits_used': response['credits_used'],
                    'credits_remaining': response['credits_remaining'],
                    'structured_data': response.get('structured_data'),
                    'insights': response.get('insights', []),
                    'created_at': response['created_at']
                },
                'timestamp': timezone.now().isoformat()
            }))
            
            # Broadcast to other clients in the same conversation
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': response,
                    'sender_id': str(self.user.id)
                }
            )
            
        except InsufficientCreditsError as e:
            logger.warning(f"Insufficient credits for user {self.user.id}: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'insufficient_credits',
                'error_code': 'INSUFFICIENT_CREDITS',
                'message': 'Créditos insuficientes. Compre mais créditos para continuar.',
                'credits_remaining': await self.get_credits_balance()
            }))
        except Exception as e:
            logger.error(f"Error processing AI message: {str(e)}", exc_info=True)
            await self.send_error(
                f"Erro ao processar mensagem: {str(e)}",
                error_code="MESSAGE_PROCESSING_ERROR"
            )
        finally:
            # Always stop typing indicator
            try:
                await self.send(text_data=json.dumps({
                    'type': 'assistant_typing',
                    'typing': False,
                    'timestamp': timezone.now().isoformat()
                }))
            except Exception as e:
                logger.error(f"Error stopping typing indicator: {str(e)}")
    
    async def handle_typing(self, data: Dict[str, Any]):
        """Handle typing indicator"""
        is_typing = data.get('typing', False)
        
        # Broadcast typing status to other users
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_typing',
                'user_id': str(self.user.id),
                'typing': is_typing
            }
        )
    
    async def handle_read_receipt(self, data: Dict[str, Any]):
        """Handle read receipt for messages"""
        message_id = data.get('message_id')
        if message_id:
            # Update message read status in database
            await self.mark_message_read(message_id)
    
    # Channel layer message handlers
    async def chat_message(self, event):
        """Handle chat message from channel layer"""
        # Don't send the message back to the sender
        if event.get('sender_id') != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'new_message',
                'message': event['message']
            }))
    
    async def user_typing(self, event):
        """Handle typing indicator from channel layer"""
        # Don't send typing indicator back to the sender
        if event.get('user_id') != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'user_typing',
                'user_id': event['user_id'],
                'typing': event['typing']
            }))
    
    # Helper methods
    @database_sync_to_async
    def authenticate_user(self):
        """Authenticate user with enhanced security"""
        # Check if already authenticated by middleware
        if hasattr(self.scope, 'user') and self.scope['user']:
            self.user = self.scope['user']
            
            # Get user's active company
            if hasattr(self.user, 'company'):
                self.company = self.user.company
            else:
                # Get first company user belongs to
                company_user = self.user.company_users.filter(is_active=True).first()
                if company_user:
                    self.company = company_user.company
                else:
                    logger.warning(f"User {self.user.id} has no active company")
                    return False
            
            return True
        
        # Fallback to query string auth (less secure, for backward compatibility)
        query_string = self.scope.get('query_string', b'').decode()
        params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
        token = params.get('token')
        
        if not token:
            # Try to get from headers
            headers = dict(self.scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode('utf-8')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
        
        if not token:
            logger.warning("No token provided in WebSocket connection")
            return False
        
        try:
            # Validate token
            UntypedToken(token)
            
            # Get user from token
            from rest_framework_simplejwt.authentication import JWTAuthentication
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            self.user = jwt_auth.get_user(validated_token)
            
            # Get user's active company
            if hasattr(self.user, 'company'):
                self.company = self.user.company
            else:
                # Get first company user belongs to
                company_user = self.user.company_users.filter(is_active=True).first()
                if company_user:
                    self.company = company_user.company
                else:
                    logger.warning(f"User {self.user.id} has no active company")
                    return False
            
            return True
            
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Invalid token in WebSocket connection: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error authenticating WebSocket user: {str(e)}", exc_info=True)
            return False
    
    @database_sync_to_async
    def has_permission(self):
        """Check if user has permission to access conversation"""
        try:
            conversation = AIConversation.objects.get(
                id=self.conversation_id,
                company=self.company
            )
            # User must belong to the same company as the conversation
            return True
        except AIConversation.DoesNotExist:
            logger.warning(f"Conversation {self.conversation_id} not found or user lacks permission")
            return False
    
    @database_sync_to_async
    def process_ai_message(self, content: str) -> Dict[str, Any]:
        """Process message with AI service"""
        try:
            with transaction.atomic():
                # Get conversation with select_for_update to prevent race conditions
                conversation = AIConversation.objects.select_for_update().get(
                    id=self.conversation_id,
                    company=self.company
                )
                
                # Validate conversation is active
                if conversation.status != 'active':
                    raise ValidationError("Conversation is not active")
                
                # Process with AI service using the updated method signature
                result = AIService.process_message(
                    conversation=conversation,
                    user_message=content,
                    context_data={},
                    request_type='general'
                )
                
                # Get remaining credits
                credit_balance = AICredit.objects.get(company=self.company)
                
                return {
                    'message_id': str(result['ai_message'].id),
                    'content': result['ai_message'].content,
                    'credits_used': result['credits_used'],
                    'credits_remaining': credit_balance.balance + credit_balance.bonus_credits,
                    'structured_data': result['ai_message'].structured_data,
                    'insights': [{
                        'id': str(insight.id),
                        'title': insight.title,
                        'priority': insight.priority
                    } for insight in result.get('insights', [])],
                    'created_at': result['ai_message'].created_at.isoformat()
                }
                
        except AIConversation.DoesNotExist:
            logger.error(f"Conversation {self.conversation_id} not found")
            raise ValidationError("Conversation not found")
        except Exception as e:
            logger.error(f"Error in process_ai_message: {str(e)}", exc_info=True)
            raise
    
    @database_sync_to_async
    def get_credits_balance(self) -> int:
        """Get current credits balance"""
        try:
            credit = AICredit.objects.get(company=self.company)
            return credit.balance
        except AICredit.DoesNotExist:
            return 0
    
    @database_sync_to_async
    def mark_message_read(self, message_id: str):
        """Mark message as read"""
        try:
            AIMessage.objects.filter(
                id=message_id,
                conversation__company=self.company
            ).update(viewed_at=timezone.now())
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
    
    async def send_error(self, error_message: str, error_code: str = None):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'success': False,
            'error': error_message,
            'error_code': error_code,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def check_rate_limit(self) -> bool:
        """Basic rate limiting check"""
        # Simple implementation - could be enhanced with Redis
        from django.core.cache import cache
        
        cache_key = f"ws_rate_limit_{self.user.id}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= 60:  # Max 60 messages per minute
            return False
        
        cache.set(cache_key, current_count + 1, 60)  # 1 minute timeout
        return True