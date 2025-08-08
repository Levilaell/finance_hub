"""
Smart Rate Limiting with Development Support
"""
import logging
import time
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework.throttling import BaseThrottle

logger = logging.getLogger(__name__)


class SmartRateLimiter:
    """
    Intelligent rate limiter with:
    - Development environment bypass
    - IP whitelist support
    - Adaptive rate limiting based on user behavior
    - Token bucket algorithm for fair usage
    """
    
    # Whitelist for development
    DEVELOPMENT_IPS = [
        '127.0.0.1',
        'localhost',
        '::1',  # IPv6 localhost
        '0.0.0.0',
    ]
    
    # Token bucket configuration
    BUCKET_CONFIGS = {
        'default': {'capacity': 100, 'refill_rate': 10, 'refill_per_second': 1},
        'api': {'capacity': 1000, 'refill_rate': 100, 'refill_per_second': 1},
        'auth': {'capacity': 20, 'refill_rate': 2, 'refill_per_second': 0.1},
        'burst': {'capacity': 60, 'refill_rate': 60, 'refill_per_second': 1},
    }
    
    @classmethod
    def get_client_identifier(cls, request) -> str:
        """Get unique client identifier"""
        if request.user.is_authenticated:
            return f"user_{request.user.id}"
        
        # Get client IP
        ip = cls.get_client_ip(request)
        return f"ip_{ip}"
    
    @classmethod
    def get_client_ip(cls, request) -> str:
        """Extract real client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
    
    @classmethod
    def is_whitelisted(cls, request) -> bool:
        """Check if request is from whitelisted source"""
        # Always whitelist in DEBUG mode
        if settings.DEBUG:
            return True
        
        # Check IP whitelist
        client_ip = cls.get_client_ip(request)
        if client_ip in cls.DEVELOPMENT_IPS:
            return True
        
        # Check custom whitelist from settings
        whitelist = getattr(settings, 'RATE_LIMIT_WHITELIST', [])
        if client_ip in whitelist:
            return True
        
        # Check if superuser
        if request.user.is_authenticated and request.user.is_superuser:
            return True
        
        return False
    
    @classmethod
    def get_bucket_config(cls, endpoint_type: str) -> Dict:
        """Get token bucket configuration for endpoint type"""
        return cls.BUCKET_CONFIGS.get(endpoint_type, cls.BUCKET_CONFIGS['default'])
    
    @classmethod
    def check_rate_limit(cls, request, endpoint_type: str = 'default') -> Tuple[bool, Optional[int]]:
        """
        Check if request should be rate limited using token bucket algorithm
        
        Returns:
            Tuple[bool, Optional[int]]: (is_allowed, retry_after_seconds)
        """
        # Skip rate limiting for whitelisted requests
        if cls.is_whitelisted(request):
            return True, None
        
        client_id = cls.get_client_identifier(request)
        bucket_key = f"rate_bucket:{endpoint_type}:{client_id}"
        timestamp_key = f"rate_timestamp:{endpoint_type}:{client_id}"
        
        config = cls.get_bucket_config(endpoint_type)
        capacity = config['capacity']
        refill_rate = config['refill_rate']
        refill_per_second = config['refill_per_second']
        
        # Get current bucket state
        current_tokens = cache.get(bucket_key, capacity)
        last_refill = cache.get(timestamp_key, time.time())
        
        # Calculate tokens to add based on time passed
        current_time = time.time()
        time_passed = current_time - last_refill
        tokens_to_add = time_passed * refill_per_second
        
        # Update bucket
        current_tokens = min(capacity, current_tokens + tokens_to_add)
        
        if current_tokens >= 1:
            # Allow request and consume token
            current_tokens -= 1
            cache.set(bucket_key, current_tokens, 3600)  # 1 hour TTL
            cache.set(timestamp_key, current_time, 3600)
            return True, None
        else:
            # Calculate retry after
            tokens_needed = 1 - current_tokens
            retry_after = int(tokens_needed / refill_per_second) + 1
            
            logger.warning(
                f"Rate limit exceeded for {client_id} on {endpoint_type}. "
                f"Tokens: {current_tokens:.2f}, Retry after: {retry_after}s"
            )
            
            return False, retry_after
    
    @classmethod
    def create_rate_limit_response(cls, retry_after: int, endpoint_type: str) -> JsonResponse:
        """Create standardized rate limit response"""
        return JsonResponse({
            'error': {
                'message': 'Too many requests. Please slow down.',
                'type': 'rate_limit_exceeded',
                'details': {
                    'endpoint_type': endpoint_type,
                    'retry_after': retry_after,
                    'wait_time': retry_after,
                }
            },
            'retry_after': retry_after,
        }, status=429, headers={'Retry-After': str(retry_after)})


class SmartRateLimitThrottle(BaseThrottle):
    """
    DRF Throttle using SmartRateLimiter
    """
    scope = 'default'
    
    def allow_request(self, request, view):
        """Check if request should be allowed"""
        # Determine endpoint type
        endpoint_type = self.get_endpoint_type(request)
        
        # Check rate limit
        allowed, retry_after = SmartRateLimiter.check_rate_limit(request, endpoint_type)
        
        if not allowed:
            # Store retry_after for wait() method
            self.retry_after = retry_after
        
        return allowed
    
    def wait(self):
        """Return number of seconds to wait before next request"""
        return getattr(self, 'retry_after', 60)
    
    def get_endpoint_type(self, request) -> str:
        """Determine endpoint type from request path"""
        path = request.path
        
        if path.startswith('/api/auth/'):
            return 'auth'
        elif path.startswith('/api/'):
            return 'api'
        else:
            return 'default'


class SmartRateLimitMiddleware:
    """
    Smart rate limiting middleware with development support
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Determine endpoint type
        endpoint_type = self.get_endpoint_type(request)
        
        # Check rate limit
        allowed, retry_after = SmartRateLimiter.check_rate_limit(request, endpoint_type)
        
        if not allowed:
            return SmartRateLimiter.create_rate_limit_response(retry_after, endpoint_type)
        
        # Process request
        response = self.get_response(request)
        
        # Add rate limit headers
        self.add_rate_limit_headers(request, response, endpoint_type)
        
        return response
    
    def get_endpoint_type(self, request) -> str:
        """Determine endpoint type from request path"""
        path = request.path
        
        if path.startswith('/api/auth/'):
            return 'auth'
        elif path.startswith('/api/'):
            return 'api'
        else:
            return 'default'
    
    def add_rate_limit_headers(self, request, response, endpoint_type: str):
        """Add rate limit information headers to response"""
        if SmartRateLimiter.is_whitelisted(request):
            return
        
        client_id = SmartRateLimiter.get_client_identifier(request)
        bucket_key = f"rate_bucket:{endpoint_type}:{client_id}"
        
        config = SmartRateLimiter.get_bucket_config(endpoint_type)
        current_tokens = cache.get(bucket_key, config['capacity'])
        
        response['X-RateLimit-Limit'] = str(config['capacity'])
        response['X-RateLimit-Remaining'] = str(int(current_tokens))
        response['X-RateLimit-Reset'] = str(int(time.time() + 3600))


# Export for easy import
__all__ = ['SmartRateLimiter', 'SmartRateLimitThrottle', 'SmartRateLimitMiddleware']