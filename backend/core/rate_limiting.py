"""
Comprehensive rate limiting for Finance Hub API
"""
from django.core.cache import cache
from rest_framework.throttling import BaseThrottle, UserRateThrottle, AnonRateThrottle


class BaseFinanceHubThrottle(BaseThrottle):
    """Base throttle class with custom cache key generation"""
    
    def get_cache_key(self, request, view):
        """Generate cache key for rate limiting"""
        if request.user.is_authenticated:
            ident = request.user.pk
            try:
                # Include company ID for company-based rate limiting
                company = request.user.company
                ident = f"{ident}:{company.id}"
            except:
                pass
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class RegistrationThrottle(BaseFinanceHubThrottle, AnonRateThrottle):
    """Rate limiting for registration endpoint"""
    scope = 'registration'
    rate = '5/hour'
    
    def get_cache_key(self, request, view):
        """Use IP address for registration throttling"""
        ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class LoginThrottle(BaseFinanceHubThrottle, AnonRateThrottle):
    """Rate limiting for login attempts"""
    scope = 'login'
    rate = '10/hour'
    
    def get_cache_key(self, request, view):
        """Use IP + email combination for login throttling"""
        ident = self.get_ident(request)
        email = request.data.get('email', '')
        if email:
            ident = f"{ident}:{email}"
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class PasswordResetThrottle(BaseFinanceHubThrottle, AnonRateThrottle):
    """Rate limiting for password reset requests"""
    scope = 'password_reset'
    rate = '3/hour'
    
    def get_cache_key(self, request, view):
        """Use email for password reset throttling"""
        email = request.data.get('email', '')
        if email:
            return self.cache_format % {
                'scope': self.scope,
                'ident': email
            }
        return super().get_cache_key(request, view)


def check_rate_limit(key: str, limit: int, window: int = 3600) -> bool:
    """
    Generic rate limit checker
    
    Args:
        key: Cache key for rate limiting
        limit: Maximum number of requests allowed
        window: Time window in seconds (default: 1 hour)
    
    Returns:
        True if request is allowed, False otherwise
    """
    current_count = cache.get(key, 0)
    if current_count >= limit:
        return False
    
    # Increment counter
    try:
        cache.incr(key)
    except ValueError:
        # Key doesn't exist, set it
        cache.set(key, 1, window)
    
    return True


def get_rate_limit_status(key: str, limit: int) -> dict:
    """
    Get current rate limit status
    
    Returns:
        Dict with current count, limit, and remaining requests
    """
    current = cache.get(key, 0)
    return {
        'current': current,
        'limit': limit,
        'remaining': max(0, limit - current)
    }