"""
Cache utilities and decorators
"""
from functools import wraps

from django.core.cache import cache
# make_template_fragment_key was removed in Django 5.0
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie


def cache_key_user(prefix, user):
    """Generate cache key including user ID"""
    return f"{prefix}:user:{user.id}"


def cache_key_company(prefix, company):
    """Generate cache key including company ID"""
    return f"{prefix}:company:{company.id}"


def cache_for_user(timeout=300, prefix=''):
    """
    Cache decorator that includes user ID in cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if not request.user.is_authenticated:
                return func(self, request, *args, **kwargs)
                
            cache_key = cache_key_user(f"{prefix}:{func.__name__}", request.user)
            result = cache.get(cache_key)
            
            if result is None:
                result = func(self, request, *args, **kwargs)
                cache.set(cache_key, result, timeout)
                
            return result
        return wrapper
    return decorator


def invalidate_user_cache(user, prefix=''):
    """Invalidate all cache entries for a user"""
    pattern = f"{prefix}:*:user:{user.id}"
    cache.delete_pattern(pattern)


def invalidate_company_cache(company, prefix=''):
    """Invalidate all cache entries for a company"""
    pattern = f"{prefix}:*:company:{company.id}"
    cache.delete_pattern(pattern)


# Pre-configured decorators
cache_1min = cache_page(60)
cache_5min = cache_page(60 * 5)
cache_15min = cache_page(60 * 15)
cache_1hour = cache_page(60 * 60)
cache_1day = cache_page(60 * 60 * 24)

# Cache with user variation
cache_per_user_1min = vary_on_cookie(cache_1min)
cache_per_user_5min = vary_on_cookie(cache_5min)
cache_per_user_15min = vary_on_cookie(cache_15min)