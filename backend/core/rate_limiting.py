"""
Comprehensive rate limiting for Finance Hub API
"""
from typing import Optional
from django.core.cache import cache
from rest_framework.throttling import BaseThrottle, UserRateThrottle, AnonRateThrottle
from rest_framework.exceptions import Throttled
import time


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


class APIEndpointThrottle(BaseFinanceHubThrottle, UserRateThrottle):
    """General API endpoint rate limiting"""
    scope = 'api'
    rate = '1000/hour'


class BurstAPIThrottle(BaseFinanceHubThrottle, UserRateThrottle):
    """Burst rate limiting for short-term spikes"""
    scope = 'burst'
    rate = '60/minute'


class ReportGenerationThrottle(BaseFinanceHubThrottle, UserRateThrottle):
    """Rate limiting for resource-intensive report generation"""
    scope = 'report_generation'
    rate = '10/hour'


class BankSyncThrottle(BaseFinanceHubThrottle, UserRateThrottle):
    """Rate limiting for bank synchronization"""
    scope = 'bank_sync'
    rate = '20/hour'


class AIRequestThrottle(BaseFinanceHubThrottle, UserRateThrottle):
    """Rate limiting for AI requests based on subscription"""
    scope = 'ai_requests'
    
    def get_rate(self):
        """Get rate based on user's subscription plan"""
        if not hasattr(self, 'request') or not self.request:
            return '100/month'
        
        user = self.request.user
        if not user.is_authenticated:
            return '0/hour'  # No AI for anonymous users
        
        try:
            company = user.company
            plan = company.subscription_plan
            
            # Set rate based on plan
            if plan.slug == 'starter':
                return '100/month'
            elif plan.slug == 'professional':
                return '500/month'
            elif plan.slug == 'enterprise':
                return '2000/month'
        except:
            pass
        
        return '100/month'  # Default rate
    
    def allow_request(self, request, view):
        """Check if request is allowed"""
        self.request = request
        self.rate = self.get_rate()
        return super().allow_request(request, view)


class PaymentWebhookThrottle(BaseThrottle):
    """Special throttle for payment webhooks"""
    
    def allow_request(self, request, view):
        """Allow webhooks from trusted sources"""
        # Check for webhook signature headers
        stripe_signature = request.META.get('HTTP_STRIPE_SIGNATURE')
        if stripe_signature:
            # Trust Stripe webhooks
            return True
        
        # For other sources, apply rate limiting
        remote_addr = self.get_ident(request)
        key = f'webhook_throttle:{remote_addr}'
        
        # Allow 100 webhooks per minute per IP
        current = cache.get(key, 0)
        if current >= 100:
            return False
        
        cache.set(key, current + 1, 60)  # 1 minute expiry
        return True


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