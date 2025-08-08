"""
Enhanced WebSocket Security for AI Insights
Provides secure authentication and middleware for WebSocket connections
"""
import logging
import time
import hmac
import hashlib
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qs
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from apps.authentication.models import User

logger = logging.getLogger(__name__)


class WebSocketRateLimiter:
    """Rate limiting for WebSocket connections"""
    
    def __init__(self, max_connections_per_user: int = 5, max_messages_per_minute: int = 60):
        self.max_connections_per_user = max_connections_per_user
        self.max_messages_per_minute = max_messages_per_minute
    
    def check_connection_limit(self, user_id: str) -> bool:
        """Check if user has reached connection limit"""
        cache_key = f"ws_connections:{user_id}"
        current_connections = cache.get(cache_key, 0)
        
        if current_connections >= self.max_connections_per_user:
            logger.warning(f"User {user_id} exceeded connection limit")
            return False
        
        return True
    
    def add_connection(self, user_id: str, connection_id: str):
        """Register a new connection"""
        cache_key = f"ws_connections:{user_id}"
        connections_key = f"ws_connection_ids:{user_id}"
        
        # Increment connection count
        current_count = cache.get(cache_key, 0)
        cache.set(cache_key, current_count + 1, timeout=3600)  # 1 hour
        
        # Store connection ID
        connections = cache.get(connections_key, set())
        connections.add(connection_id)
        cache.set(connections_key, connections, timeout=3600)
    
    def remove_connection(self, user_id: str, connection_id: str):
        """Remove a connection"""
        cache_key = f"ws_connections:{user_id}"
        connections_key = f"ws_connection_ids:{user_id}"
        
        # Decrement connection count
        current_count = cache.get(cache_key, 0)
        if current_count > 0:
            cache.set(cache_key, current_count - 1, timeout=3600)
        
        # Remove connection ID
        connections = cache.get(connections_key, set())
        connections.discard(connection_id)
        cache.set(connections_key, connections, timeout=3600)
    
    def check_message_rate(self, user_id: str) -> bool:
        """Check if user has exceeded message rate limit"""
        cache_key = f"ws_messages:{user_id}"
        current_time = time.time()
        
        # Get message timestamps
        timestamps = cache.get(cache_key, [])
        
        # Remove old timestamps (older than 1 minute)
        timestamps = [ts for ts in timestamps if current_time - ts < 60]
        
        if len(timestamps) >= self.max_messages_per_minute:
            logger.warning(f"User {user_id} exceeded message rate limit")
            return False
        
        # Add current timestamp
        timestamps.append(current_time)
        cache.set(cache_key, timestamps, timeout=120)  # 2 minutes
        
        return True


class SecureWebSocketAuthMiddleware(BaseMiddleware):
    """Enhanced WebSocket authentication middleware"""
    
    def __init__(self, inner):
        super().__init__(inner)
        self.rate_limiter = WebSocketRateLimiter()
    
    async def __call__(self, scope, receive, send):
        """Process WebSocket connection"""
        try:
            # Extract token from headers (preferred) or query string
            token = await self.extract_token(scope)
            
            if not token:
                await self.close_connection(send, 4001, "Authentication required")
                return
            
            # Validate token and get user
            user = await self.validate_token(token)
            
            if not user:
                await self.close_connection(send, 4001, "Invalid authentication token")
                return
            
            # Check rate limiting
            if not self.rate_limiter.check_connection_limit(str(user.id)):
                await self.close_connection(send, 4008, "Connection limit exceeded")
                return
            
            # Generate connection ID
            connection_id = self.generate_connection_id(user.id)
            
            # Add user and connection info to scope
            scope['user'] = user
            scope['connection_id'] = connection_id
            scope['rate_limiter'] = self.rate_limiter
            
            # Register connection
            self.rate_limiter.add_connection(str(user.id), connection_id)
            
            try:
                # Call the inner application
                await self.inner(scope, receive, send)
            finally:
                # Always remove connection on disconnect
                self.rate_limiter.remove_connection(str(user.id), connection_id)
                
        except Exception as e:
            logger.error(f"WebSocket middleware error: {str(e)}", exc_info=True)
            await self.close_connection(send, 4000, "Internal server error")
    
    async def extract_token(self, scope: Dict) -> Optional[str]:
        """Extract authentication token from WebSocket scope"""
        # Try to get from headers first (more secure)
        headers = dict(scope.get('headers', []))
        auth_header = headers.get(b'authorization', b'').decode('utf-8')
        
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        
        # Fallback to query string (less secure, for browser compatibility)
        query_string = scope.get('query_string', b'').decode('utf-8')
        params = parse_qs(query_string)
        tokens = params.get('token', [])
        
        return tokens[0] if tokens else None
    
    @database_sync_to_async
    def validate_token(self, token: str) -> Optional[User]:
        """Validate JWT token and return user"""
        try:
            # Validate token
            UntypedToken(token)
            
            # Get user from token
            from rest_framework_simplejwt.authentication import JWTAuthentication
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            
            # Check if user is active
            if not user.is_active:
                return None
            
            return user
            
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Invalid token in WebSocket connection: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error validating WebSocket token: {str(e)}", exc_info=True)
            return None
    
    def generate_connection_id(self, user_id: int) -> str:
        """Generate unique connection ID"""
        timestamp = timezone.now().timestamp()
        data = f"{user_id}:{timestamp}".encode()
        return hmac.new(
            settings.SECRET_KEY.encode(),
            data,
            hashlib.sha256
        ).hexdigest()[:16]
    
    async def close_connection(self, send, code: int, reason: str):
        """Close WebSocket connection with code and reason"""
        await send({
            'type': 'websocket.close',
            'code': code,
            'reason': reason
        })


class WebSocketSecurityMixin:
    """Mixin for WebSocket consumers to add security features"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_activity = time.time()
        self.activity_timeout = 300  # 5 minutes
    
    async def check_activity_timeout(self) -> bool:
        """Check if connection has been idle too long"""
        current_time = time.time()
        if current_time - self.last_activity > self.activity_timeout:
            await self.close(code=4002, reason="Connection timeout due to inactivity")
            return False
        return True
    
    async def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()
    
    async def validate_message_size(self, message: str) -> bool:
        """Validate message size to prevent DoS"""
        max_size = getattr(settings, 'WEBSOCKET_MAX_MESSAGE_SIZE', 65536)  # 64KB
        if len(message) > max_size:
            await self.send_json({
                'type': 'error',
                'code': 'MESSAGE_TOO_LARGE',
                'message': f'Message exceeds maximum size of {max_size} bytes'
            })
            return False
        return True
    
    async def sanitize_message(self, message: Dict) -> Dict:
        """Sanitize incoming message data"""
        # Remove any potentially harmful fields
        dangerous_fields = ['__proto__', 'constructor', 'prototype']
        for field in dangerous_fields:
            message.pop(field, None)
        
        # Limit string lengths
        max_string_length = 4000
        for key, value in message.items():
            if isinstance(value, str) and len(value) > max_string_length:
                message[key] = value[:max_string_length]
        
        return message


def create_secure_websocket_token(user_id: int, expires_in: int = 3600) -> str:
    """
    Create a secure WebSocket-specific token
    
    Args:
        user_id: User ID
        expires_in: Token expiration in seconds
        
    Returns:
        Secure token string
    """
    import jwt
    
    payload = {
        'user_id': user_id,
        'type': 'websocket',
        'exp': timezone.now() + timedelta(seconds=expires_in),
        'iat': timezone.now(),
    }
    
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm='HS256'
    )
    
    return token


def verify_websocket_token(token: str) -> Optional[Dict]:
    """
    Verify WebSocket-specific token
    
    Args:
        token: Token to verify
        
    Returns:
        Decoded payload or None if invalid
    """
    import jwt
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        
        # Verify it's a WebSocket token
        if payload.get('type') != 'websocket':
            return None
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("WebSocket token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid WebSocket token: {str(e)}")
        return None