"""
Cache utilities for the finance hub application
"""
import hashlib
import json
from functools import wraps
from typing import Any, Callable, Optional, Union

from django.conf import settings
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpRequest


def make_cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from arguments
    """
    key_parts = []
    
    # Add args
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        else:
            # For complex types, use JSON representation
            key_parts.append(json.dumps(arg, cls=DjangoJSONEncoder, sort_keys=True))
    
    # Add kwargs
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}:{v}")
        else:
            key_parts.append(f"{k}:{json.dumps(v, cls=DjangoJSONEncoder, sort_keys=True)}")
    
    # Create hash for long keys
    key_str = ":".join(key_parts)
    if len(key_str) > 200:
        key_str = hashlib.md5(key_str.encode()).hexdigest()
    
    return key_str


def cache_result(
    ttl: Union[int, str] = 'medium',
    key_prefix: Optional[str] = None,
    vary_on_user: bool = False,
    vary_on_company: bool = True
) -> Callable:
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds or a key from CACHE_TTL
        key_prefix: Optional prefix for cache key
        vary_on_user: Include user ID in cache key
        vary_on_company: Include company ID in cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get TTL value
            if isinstance(ttl, str):
                ttl_seconds = settings.CACHE_TTL.get(ttl, 300)
            else:
                ttl_seconds = ttl
            
            # Build cache key parts
            cache_key_parts = [key_prefix or func.__name__]
            
            # Add user/company if needed
            request = None
            for arg in args:
                if isinstance(arg, HttpRequest):
                    request = arg
                    break
                elif hasattr(arg, 'request'):
                    request = arg.request
                    break
            
            if request and hasattr(request, 'user'):
                if vary_on_user and request.user.is_authenticated:
                    cache_key_parts.append(f"user:{request.user.id}")
                if vary_on_company and request.user.is_authenticated:
                    try:
                        company = request.user.company
                        cache_key_parts.append(f"company:{company.id}")
                    except:
                        pass
            
            # Add function arguments
            cache_key_parts.append(make_cache_key(*args, **kwargs))
            cache_key = ":".join(cache_key_parts)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate all cache keys matching a pattern
    
    Returns:
        Number of keys deleted
    """
    if hasattr(cache, '_cache'):
        # For Redis backend
        keys = cache._cache.get_client().keys(f"{cache.key_prefix}:{pattern}")
        if keys:
            return cache._cache.get_client().delete(*keys)
    return 0


def cache_api_response(
    ttl: Union[int, str] = 'medium',
    vary_on_params: bool = True
) -> Callable:
    """
    Decorator specifically for caching API view responses
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Build cache key
            cache_key_parts = [
                'api',
                request.method,
                request.path,
            ]
            
            # Add company
            if hasattr(request.user, 'company'):
                try:
                    cache_key_parts.append(f"company:{request.user.company.id}")
                except:
                    pass
            
            # Add query params if needed
            if vary_on_params and request.GET:
                params = dict(request.GET)
                cache_key_parts.append(make_cache_key(**params))
            
            cache_key = ":".join(cache_key_parts)
            
            # Try cache for GET requests only
            if request.method == 'GET':
                cached_response = cache.get(cache_key)
                if cached_response is not None:
                    return cached_response
            
            # Call view
            response = view_func(self, request, *args, **kwargs)
            
            # Cache successful GET responses
            if request.method == 'GET' and response.status_code == 200:
                if isinstance(ttl, str):
                    ttl_seconds = settings.CACHE_TTL.get(ttl, 300)
                else:
                    ttl_seconds = ttl
                cache.set(cache_key, response, ttl_seconds)
            
            return response
        
        return wrapper
    return decorator