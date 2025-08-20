"""
Rate limiter utility for API clients
Implements token bucket algorithm with exponential backoff
"""
import time
import threading
import logging
from typing import Optional
from dataclasses import dataclass
from django.core.cache import cache

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiter"""
    max_requests: int = 10  # Maximum requests per period
    period_seconds: int = 1  # Period in seconds
    max_retries: int = 3  # Maximum retry attempts
    initial_backoff: float = 1.0  # Initial backoff delay in seconds
    max_backoff: float = 60.0  # Maximum backoff delay
    backoff_multiplier: float = 2.0  # Exponential backoff multiplier


class RateLimiter:
    """
    Token bucket rate limiter with exponential backoff
    Thread-safe implementation using Redis/cache for distributed rate limiting
    """
    
    def __init__(self, identifier: str, config: RateLimitConfig):
        self.identifier = identifier
        self.config = config
        self.lock = threading.RLock()
        
        # Cache keys for distributed rate limiting
        self.bucket_key = f"rate_limit:bucket:{identifier}"
        self.last_refill_key = f"rate_limit:last_refill:{identifier}"
        
    def _get_current_time(self) -> float:
        """Get current time in seconds"""
        return time.time()
    
    def _refill_bucket(self) -> int:
        """
        Refill the token bucket based on elapsed time
        Returns current token count
        """
        now = self._get_current_time()
        
        # Get last refill time and current tokens
        last_refill = cache.get(self.last_refill_key, now)
        current_tokens = cache.get(self.bucket_key, self.config.max_requests)
        
        # Calculate tokens to add based on elapsed time
        elapsed = now - last_refill
        tokens_to_add = int(elapsed * (self.config.max_requests / self.config.period_seconds))
        
        if tokens_to_add > 0:
            # Add tokens up to maximum
            new_token_count = min(
                current_tokens + tokens_to_add,
                self.config.max_requests
            )
            
            # Update cache atomically
            cache.set(self.bucket_key, new_token_count, 300)  # 5 minute expiry
            cache.set(self.last_refill_key, now, 300)
            
            logger.debug(f"Rate limiter {self.identifier}: refilled {tokens_to_add} tokens, now {new_token_count}")
            return new_token_count
        
        return current_tokens
    
    def _consume_token(self) -> bool:
        """
        Try to consume a token from the bucket
        Returns True if token was consumed, False if bucket is empty
        """
        with self.lock:
            current_tokens = self._refill_bucket()
            
            if current_tokens > 0:
                # Consume token
                new_count = current_tokens - 1
                cache.set(self.bucket_key, new_count, 300)
                logger.debug(f"Rate limiter {self.identifier}: consumed token, {new_count} remaining")
                return True
            
            logger.debug(f"Rate limiter {self.identifier}: no tokens available")
            return False
    
    def wait_for_token(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for a token to become available
        
        Args:
            timeout: Maximum time to wait in seconds (None for no timeout)
            
        Returns:
            True if token acquired, False if timeout reached
        """
        start_time = self._get_current_time()
        retry_count = 0
        backoff_delay = self.config.initial_backoff
        
        while retry_count < self.config.max_retries:
            # Check timeout
            if timeout and (self._get_current_time() - start_time) >= timeout:
                logger.warning(f"Rate limiter {self.identifier}: timeout reached after {timeout}s")
                return False
            
            # Try to get token
            if self._consume_token():
                if retry_count > 0:
                    logger.info(f"Rate limiter {self.identifier}: acquired token after {retry_count} retries")
                return True
            
            # Calculate next wait time
            wait_time = min(backoff_delay, self.config.max_backoff)
            
            # Check if wait would exceed timeout
            if timeout and (self._get_current_time() - start_time + wait_time) >= timeout:
                logger.warning(f"Rate limiter {self.identifier}: would exceed timeout, aborting")
                return False
            
            logger.debug(f"Rate limiter {self.identifier}: waiting {wait_time:.2f}s (retry {retry_count + 1})")
            time.sleep(wait_time)
            
            retry_count += 1
            backoff_delay *= self.config.backoff_multiplier
        
        logger.error(f"Rate limiter {self.identifier}: max retries ({self.config.max_retries}) exceeded")
        return False
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire a token (blocking)
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if token acquired, False if failed
        """
        return self.wait_for_token(timeout)
    
    def try_acquire(self) -> bool:
        """
        Try to acquire a token immediately (non-blocking)
        
        Returns:
            True if token acquired, False if none available
        """
        return self._consume_token()
    
    def get_status(self) -> dict:
        """
        Get current rate limiter status
        
        Returns:
            Dict with current status information
        """
        current_tokens = self._refill_bucket()
        return {
            'identifier': self.identifier,
            'current_tokens': current_tokens,
            'max_requests': self.config.max_requests,
            'period_seconds': self.config.period_seconds,
            'tokens_percentage': (current_tokens / self.config.max_requests) * 100
        }


class PluggyRateLimiter(RateLimiter):
    """
    Specialized rate limiter for Pluggy API
    Follows Pluggy's rate limiting requirements: 10 requests per second
    """
    
    def __init__(self, client_id: str):
        config = RateLimitConfig(
            max_requests=10,  # Pluggy limit: 10 requests per second
            period_seconds=1,
            max_retries=3,
            initial_backoff=0.1,  # Start with small delay
            max_backoff=5.0,  # Don't wait too long for financial API
            backoff_multiplier=2.0
        )
        super().__init__(f"pluggy:{client_id}", config)


# Global registry for rate limiters
_rate_limiters = {}
_limiter_lock = threading.RLock()


def get_pluggy_rate_limiter(client_id: str) -> PluggyRateLimiter:
    """
    Get or create a Pluggy rate limiter for the given client ID
    Thread-safe singleton pattern
    """
    with _limiter_lock:
        if client_id not in _rate_limiters:
            _rate_limiters[client_id] = PluggyRateLimiter(client_id)
        return _rate_limiters[client_id]