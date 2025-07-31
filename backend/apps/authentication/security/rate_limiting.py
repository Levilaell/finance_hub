"""
Advanced rate limiting and brute force protection
"""
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
import hashlib
import math
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ProgressiveRateLimiter:
    """
    Implements progressive rate limiting with exponential backoff
    """
    
    def __init__(self, key_prefix='auth_attempt', base_delay=1, max_delay=3600):
        self.key_prefix = key_prefix
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.cache_timeout = 86400  # 24 hours
    
    def _get_cache_key(self, identifier: str) -> str:
        """Generate cache key for identifier"""
        return f"{self.key_prefix}:{identifier}"
    
    def _get_attempt_data(self, identifier: str) -> dict:
        """Get attempt data from cache"""
        key = self._get_cache_key(identifier)
        data = cache.get(key, {
            'attempts': 0,
            'first_attempt': None,
            'last_attempt': None,
            'locked_until': None
        })
        return data
    
    def _save_attempt_data(self, identifier: str, data: dict):
        """Save attempt data to cache"""
        key = self._get_cache_key(identifier)
        cache.set(key, data, self.cache_timeout)
    
    def get_delay(self, identifier: str) -> Tuple[int, Optional[str]]:
        """
        Get delay in seconds and lock reason
        Returns: (delay_seconds, reason)
        """
        data = self._get_attempt_data(identifier)
        now = timezone.now()
        
        # Check if currently locked
        if data.get('locked_until'):
            locked_until = data['locked_until']
            if isinstance(locked_until, str):
                locked_until = timezone.datetime.fromisoformat(locked_until)
            
            if locked_until > now:
                remaining = int((locked_until - now).total_seconds())
                return remaining, f"Account locked for {remaining} seconds"
        
        attempts = data.get('attempts', 0)
        
        # Progressive delays: 0, 1, 2, 4, 8, 16, 32, 64, 128...
        if attempts > 0:
            delay = min(self.base_delay * (2 ** (attempts - 1)), self.max_delay)
            
            # After 10 attempts, lock for extended period
            if attempts >= 10:
                lock_duration = min(3600 * (attempts - 9), 86400)  # Max 24 hours
                data['locked_until'] = now + timezone.timedelta(seconds=lock_duration)
                self._save_attempt_data(identifier, data)
                return lock_duration, f"Too many attempts. Account locked for {lock_duration} seconds"
            
            return delay, f"Please wait {delay} seconds before retry"
        
        return 0, None
    
    def record_attempt(self, identifier: str, success: bool = False):
        """Record an authentication attempt"""
        data = self._get_attempt_data(identifier)
        now = timezone.now()
        
        if success:
            # Reset on successful attempt
            cache.delete(self._get_cache_key(identifier))
            logger.info(f"Successful login, cleared rate limit for {identifier}")
        else:
            # Increment failed attempts
            data['attempts'] = data.get('attempts', 0) + 1
            data['last_attempt'] = now.isoformat()
            
            if not data.get('first_attempt'):
                data['first_attempt'] = now.isoformat()
            
            self._save_attempt_data(identifier, data)
            
            # Log suspicious activity
            if data['attempts'] >= 5:
                logger.warning(
                    f"Multiple failed attempts detected",
                    extra={
                        'identifier': identifier,
                        'attempts': data['attempts'],
                        'first_attempt': data['first_attempt'],
                        'last_attempt': data['last_attempt']
                    }
                )
    
    def reset(self, identifier: str):
        """Reset rate limit for identifier"""
        cache.delete(self._get_cache_key(identifier))


class IPBasedRateLimiter:
    """
    Rate limiter based on IP address with subnet support
    """
    
    def __init__(self, key_prefix='ip_rate', window_seconds=60, max_requests=10):
        self.key_prefix = key_prefix
        self.window_seconds = window_seconds
        self.max_requests = max_requests
    
    def _get_cache_key(self, ip_address: str, action: str) -> str:
        """Generate cache key for IP and action"""
        return f"{self.key_prefix}:{action}:{ip_address}"
    
    def _get_subnet_key(self, ip_address: str, action: str) -> str:
        """Generate cache key for IP subnet (for IPv4 /24, IPv6 /48)"""
        if ':' in ip_address:  # IPv6
            # Get /48 subnet
            parts = ip_address.split(':')[:3]
            subnet = ':'.join(parts)
        else:  # IPv4
            # Get /24 subnet
            parts = ip_address.split('.')[:3]
            subnet = '.'.join(parts)
        
        return f"{self.key_prefix}:subnet:{action}:{subnet}"
    
    def check_rate_limit(self, ip_address: str, action: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request is allowed
        Returns: (allowed, retry_after_seconds)
        """
        now = timezone.now()
        current_window = int(now.timestamp() / self.window_seconds)
        
        # Check IP-specific limit
        ip_key = self._get_cache_key(ip_address, action)
        ip_data = cache.get(ip_key, {'window': current_window, 'count': 0})
        
        if ip_data['window'] == current_window:
            if ip_data['count'] >= self.max_requests:
                retry_after = self.window_seconds - (int(now.timestamp()) % self.window_seconds)
                return False, retry_after
        else:
            # New window
            ip_data = {'window': current_window, 'count': 0}
        
        # Check subnet limit (more restrictive)
        subnet_key = self._get_subnet_key(ip_address, action)
        subnet_data = cache.get(subnet_key, {'window': current_window, 'count': 0})
        
        subnet_limit = self.max_requests * 5  # Allow 5x requests per subnet
        if subnet_data['window'] == current_window:
            if subnet_data['count'] >= subnet_limit:
                retry_after = self.window_seconds - (int(now.timestamp()) % self.window_seconds)
                logger.warning(f"Subnet rate limit exceeded for {ip_address}")
                return False, retry_after
        
        return True, None
    
    def record_request(self, ip_address: str, action: str):
        """Record a request for rate limiting"""
        now = timezone.now()
        current_window = int(now.timestamp() / self.window_seconds)
        
        # Update IP counter
        ip_key = self._get_cache_key(ip_address, action)
        ip_data = cache.get(ip_key, {'window': current_window, 'count': 0})
        
        if ip_data['window'] == current_window:
            ip_data['count'] += 1
        else:
            ip_data = {'window': current_window, 'count': 1}
        
        cache.set(ip_key, ip_data, self.window_seconds * 2)
        
        # Update subnet counter
        subnet_key = self._get_subnet_key(ip_address, action)
        subnet_data = cache.get(subnet_key, {'window': current_window, 'count': 0})
        
        if subnet_data['window'] == current_window:
            subnet_data['count'] += 1
        else:
            subnet_data = {'window': current_window, 'count': 1}
        
        cache.set(subnet_key, subnet_data, self.window_seconds * 2)


class AccountLockoutManager:
    """
    Manages account lockout policies
    """
    
    def __init__(self):
        self.max_attempts = getattr(settings, 'AUTH_MAX_LOGIN_ATTEMPTS', 5)
        self.lockout_duration = getattr(settings, 'AUTH_LOCKOUT_DURATION', 3600)  # 1 hour
        self.reset_period = getattr(settings, 'AUTH_ATTEMPT_RESET_PERIOD', 86400)  # 24 hours
    
    def should_lock_account(self, user) -> bool:
        """Check if account should be locked"""
        if user.failed_login_attempts >= self.max_attempts:
            return True
        
        # Check if attempts are within reset period
        if user.last_failed_login:
            time_since_last_failure = (timezone.now() - user.last_failed_login).total_seconds()
            if time_since_last_failure > self.reset_period:
                # Reset attempts if outside reset period
                user.failed_login_attempts = 0
                user.last_failed_login = None
                user.save()
                return False
        
        return False
    
    def lock_account(self, user, duration_seconds=None):
        """Lock user account"""
        if duration_seconds is None:
            duration_seconds = self.lockout_duration
        
        user.is_locked = True
        user.locked_until = timezone.now() + timezone.timedelta(seconds=duration_seconds)
        user.save()
        
        logger.warning(
            f"Account locked due to failed login attempts",
            extra={
                'user_id': user.id,
                'email': user.email,
                'attempts': user.failed_login_attempts,
                'locked_until': user.locked_until.isoformat()
            }
        )
    
    def check_and_unlock(self, user) -> bool:
        """Check if account can be unlocked"""
        if user.is_locked and user.locked_until:
            if timezone.now() >= user.locked_until:
                user.unlock_account()
                logger.info(f"Account automatically unlocked for {user.email}")
                return True
        return False


class DistributedRateLimiter:
    """
    Distributed rate limiter for multi-server deployments
    Uses Redis or similar distributed cache
    """
    
    def __init__(self, key_prefix='dist_rate', window_seconds=60):
        self.key_prefix = key_prefix
        self.window_seconds = window_seconds
        
    def _get_cache_key(self, identifier: str, action: str) -> str:
        """Generate distributed cache key"""
        window = int(timezone.now().timestamp() / self.window_seconds)
        return f"{self.key_prefix}:{action}:{identifier}:{window}"
    
    def increment_and_check(self, identifier: str, action: str, limit: int) -> Tuple[bool, int, Optional[int]]:
        """
        Increment counter and check if within limit
        Returns: (allowed, current_count, retry_after)
        """
        key = self._get_cache_key(identifier, action)
        
        try:
            # Use Redis pipeline for atomic increment and expire
            current = cache.incr(key)
            
            if current == 1:
                # First request in this window, set expiry
                cache.expire(key, self.window_seconds + 10)
            
            if current > limit:
                retry_after = self.window_seconds - (int(timezone.now().timestamp()) % self.window_seconds)
                return False, current, retry_after
            
            return True, current, None
            
        except Exception as e:
            logger.error(f"Distributed rate limiter error: {e}")
            # Fail open on errors
            return True, 0, None


# Convenience functions
def get_client_identifier(request) -> str:
    """Generate unique identifier for rate limiting from request"""
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Create composite identifier
    raw = f"{ip}:{user_agent}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get_client_ip(request) -> str:
    """Get client IP address from request"""
    # Check for IP behind proxy
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    
    return ip