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

from apps.authentication.models import User
from apps.companies.models import Company
from .models import AIConversation, AIMessage, AICredit
from .services.ai_service import AIService
from .services.credit_service import CreditService, InsufficientCreditsError

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for AI chat conversations"""
    
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
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        
        # Authenticate user from query string token
        if not await self.authenticate_user():
            await self.close(code=4001)
            return
        
        # Verify user has permission to access this conversation
        if not await self.has_permission():
            await self.close(code=4003)
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection established message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Conectado ao Assistente Financeiro AI',
            'conversation_id': self.conversation_id
        }))
        
        logger.info(f"WebSocket connected: User {self.user.id} to conversation {self.conversation_id}")
    
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
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)
            else:
                await self.send_error(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}", exc_info=True)
            await self.send_error(f"Error processing message: {str(e)}")
    
    async def handle_message(self, data: Dict[str, Any]):
        """Process incoming chat message"""
        message_content = data.get('message', '').strip()
        
        if not message_content:
            await self.send_error("Message content cannot be empty")
            return
        
        # Send typing indicator
        await self.send(text_data=json.dumps({
            'type': 'assistant_typing',
            'typing': True
        }))
        
        try:
            # Process message with AI service
            response = await self.process_ai_message(message_content)
            
            # Send AI response
            await self.send(text_data=json.dumps({
                'type': 'ai_response',
                'message': response['content'],
                'message_id': response['message_id'],
                'credits_used': response['credits_used'],
                'credits_remaining': response['credits_remaining'],
                'structured_data': response.get('structured_data'),
                'insights': response.get('insights', []),
                'created_at': response['created_at']
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
            
        except InsufficientCreditsError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'insufficient_credits',
                'message': 'Créditos insuficientes. Compre mais créditos para continuar.',
                'credits_remaining': await self.get_credits_balance()
            }))
        except Exception as e:
            logger.error(f"Error processing AI message: {str(e)}", exc_info=True)
            await self.send_error(f"Erro ao processar mensagem: {str(e)}")
        finally:
            # Stop typing indicator
            await self.send(text_data=json.dumps({
                'type': 'assistant_typing',
                'typing': False
            }))
    
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
        """Authenticate user from token in query string"""
        query_string = self.scope.get('query_string', b'').decode()
        params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
        token = params.get('token')
        
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
            # Get conversation
            conversation = AIConversation.objects.get(id=self.conversation_id)
            
            # Create user message
            user_message = AIMessage.objects.create(
                conversation=conversation,
                role='user',
                content=content,
                type='text'
            )
            
            # Process with AI service
            result = self.ai_service.process_message(
                company=self.company,
                user=self.user,
                conversation=conversation,
                message=content
            )
            
            # Get remaining credits
            credit_balance = AICredit.objects.get(company=self.company)
            
            return {
                'message_id': str(result['message_id']),
                'content': result['content'],
                'credits_used': result['credits_used'],
                'credits_remaining': credit_balance.balance,
                'structured_data': result.get('structured_data'),
                'insights': result.get('insights', []),
                'created_at': timezone.now().isoformat()
            }
            
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
    
    async def send_error(self, error_message: str):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message
        }))