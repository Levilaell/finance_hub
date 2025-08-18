"""
Distributed locks using Redis to prevent race conditions in critical operations
Following Stripe best practices for idempotent operations
"""
import redis
import time
import logging
from contextlib import contextmanager
from django.conf import settings
from typing import Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)


class RedisLock:
    """Redis-based distributed lock with automatic expiration"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize Redis lock manager"""
        self.redis_client = redis_client or self._get_redis_client()
        self.default_timeout = 30  # 30 seconds default timeout
        self.default_retry_interval = 0.1  # 100ms retry interval
    
    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client instance"""
        try:
            # Try to get Redis from Django cache if using Redis cache
            from django.core.cache import cache
            if hasattr(cache, '_cache') and hasattr(cache._cache, '_lib'):
                return cache._cache._lib.get_client()
        except:
            pass
        
        # Fallback to default Redis connection
        try:
            return redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Redis not available for locks: {e}")
            return None
    
    @contextmanager
    def acquire_lock(self, 
                    lock_key: str, 
                    timeout: int = None,
                    retry_timeout: int = 5,
                    retry_interval: float = None):
        """
        Acquire a distributed lock with automatic release
        
        Args:
            lock_key: Unique key for the lock
            timeout: Lock expiration time in seconds (default: 30)
            retry_timeout: How long to try acquiring the lock
            retry_interval: Interval between retry attempts
            
        Raises:
            LockTimeoutError: If lock cannot be acquired within retry_timeout
        """
        if not self.redis_client:
            # Fallback: no-op context manager if Redis not available
            logger.warning(f"Redis not available, skipping lock for {lock_key}")
            yield
            return
        
        timeout = timeout or self.default_timeout
        retry_interval = retry_interval or self.default_retry_interval
        
        # Generate unique lock value to prevent accidental unlock by other processes
        lock_value = f"{time.time()}:{id(self)}"
        lock_acquired = False
        start_time = time.time()
        
        try:
            # Try to acquire lock with retries
            while time.time() - start_time < retry_timeout:
                if self.redis_client.set(lock_key, lock_value, nx=True, ex=timeout):
                    lock_acquired = True
                    logger.debug(f"Acquired lock: {lock_key}")
                    break
                
                time.sleep(retry_interval)
            
            if not lock_acquired:
                raise LockTimeoutError(f"Could not acquire lock {lock_key} within {retry_timeout}s")
            
            yield
            
        finally:
            # Release lock only if we own it
            if lock_acquired and self.redis_client:
                try:
                    # Use Lua script to ensure atomic compare-and-delete
                    release_script = """
                    if redis.call("get", KEYS[1]) == ARGV[1] then
                        return redis.call("del", KEYS[1])
                    else
                        return 0
                    end
                    """
                    self.redis_client.eval(release_script, 1, lock_key, lock_value)
                    logger.debug(f"Released lock: {lock_key}")
                except Exception as e:
                    logger.error(f"Error releasing lock {lock_key}: {e}")


class LockTimeoutError(Exception):
    """Raised when lock cannot be acquired within timeout"""
    pass


# Global lock manager instance
lock_manager = RedisLock()


def with_lock(lock_key_template: str, 
              timeout: int = 30, 
              retry_timeout: int = 5,
              retry_interval: float = 0.1):
    """
    Decorator to add distributed locking to functions
    
    Args:
        lock_key_template: Lock key template (can use function args)
        timeout: Lock timeout in seconds
        retry_timeout: How long to try acquiring lock
        retry_interval: Retry interval in seconds
    
    Example:
        @with_lock("subscription:create:{company_id}")
        def create_subscription(company_id, plan_id):
            # This function will be protected by distributed lock
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build lock key from template and function arguments
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            try:
                lock_key = lock_key_template.format(**bound_args.arguments)
            except KeyError as e:
                logger.error(f"Lock key template error: {e}")
                # Execute without lock if template is invalid
                return func(*args, **kwargs)
            
            # Execute function with lock
            with lock_manager.acquire_lock(
                lock_key=lock_key,
                timeout=timeout, 
                retry_timeout=retry_timeout,
                retry_interval=retry_interval
            ):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Predefined lock decorators for common operations
def subscription_lock(company_id_field='company_id'):
    """Lock for subscription operations on a specific company"""
    return with_lock(
        f"subscription:operation:{{{company_id_field}}}",
        timeout=45,
        retry_timeout=10
    )


def payment_lock(company_id_field='company_id'):
    """Lock for payment operations on a specific company"""
    return with_lock(
        f"payment:operation:{{{company_id_field}}}",
        timeout=60,
        retry_timeout=15
    )


def webhook_lock(event_id_field='event_id'):
    """Lock for webhook processing to ensure idempotency"""
    return with_lock(
        f"webhook:process:{{{event_id_field}}}",
        timeout=30,
        retry_timeout=5
    )


# Usage tracking locks to prevent double counting
def usage_lock(company_id_field='company_id', usage_type_field='usage_type'):
    """Lock for usage tracking operations"""
    return with_lock(
        f"usage:increment:{{{company_id_field}}}:{{{usage_type_field}}}",
        timeout=10,
        retry_timeout=3
    )