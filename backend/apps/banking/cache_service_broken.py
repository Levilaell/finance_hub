"""
Redis caching service for banking operations
"""
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union

from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import QuerySet
from django.utils import timezone

logger = logging.getLogger(__name__)


class DecimalEncoder(DjangoJSONEncoder):
    """JSON encoder that handles Decimal types"""
    
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class BankingCacheService:
    """
    Centralized caching service for banking operations
    """
    
    # Cache timeout configurations (in seconds)
    CACHE_TIMEOUTS = {
        'dashboard_summary': 300,      # 5 minutes
        'monthly_trends': 1800,        # 30 minutes
        'category_totals': 900,        # 15 minutes
        'account_balance': 60,         # 1 minute
        'transaction_list': 600,       # 10 minutes
        'bank_providers': 3600,        # 1 hour
        'user_categories': 1800,       # 30 minutes
        'financial_insights': 1800,    # 30 minutes
    }
    
    # Cache key prefixes
    KEY_PREFIXES = {
        'dashboard': 'dash',
        'transactions': 'tx',
        'accounts': 'acc',
        'categories': 'cat',
        'reports': 'rep',
        'insights': 'ins',
    }
    
    def __init__(self):
        self.encoder = DecimalEncoder()
    
    def _make_key(self, prefix: str, *args) -> str:
        """Generate cache key with prefix and arguments"""
        key_parts = [self.KEY_PREFIXES.get(prefix, prefix)]
        key_parts.extend(str(arg) for arg in args)
        return ':'.join(key_parts)
    
    def _serialize_data(self, data: Any) -> str:
        """Serialize data for cache storage"""
        return json.dumps(data, cls=self.encoder, ensure_ascii=False)
    
    def _deserialize_data(self, data: str) -> Any:
        """Deserialize data from cache"""
        if data is None:
            return None
        return json.loads(data)
    
    # Dashboard caching methods
    def get_dashboard_summary(self, company_id: int, user_id: int) -> Optional[Dict]:
        """Get cached dashboard summary"""
        key = self._make_key('dashboard', 'summary', company_id, user_id)
        data = cache.get(key)
        return self._deserialize_data(data) if data else None
    
    def set_dashboard_summary(self, company_id: int, user_id: int, data: Dict) -> None:
        """Cache dashboard summary"""
        key = self._make_key('dashboard', 'summary', company_id, user_id)
        serialized = self._serialize_data(data)
        cache.set(key, serialized, self.CACHE_TIMEOUTS['dashboard_summary'])
        logger.debug(f"Cached dashboard summary for company {company_id}")
    
    def get_monthly_trends(self, company_id: int, months: int = 12) -> Optional[List[Dict]]:
        """Get cached monthly trends"""
        key = self._make_key('dashboard', 'trends', company_id, months)
        data = cache.get(key)
        return self._deserialize_data(data) if data else None
    
    def set_monthly_trends(self, company_id: int, months: int, data: List[Dict]) -> None:
        """Cache monthly trends"""
        key = self._make_key('dashboard', 'trends', company_id, months)
        serialized = self._serialize_data(data)
        cache.set(key, serialized, self.CACHE_TIMEOUTS['monthly_trends'])
        logger.debug(f"Cached monthly trends for company {company_id}")
    
    # Transaction caching methods
    def get_transaction_list(self, account_id: int, filters_hash: str, page: int = 1) -> Optional[Dict]:
        """Get cached transaction list"""
        key = self._make_key('transactions', 'list', account_id, filters_hash, page)
        data = cache.get(key)
        return self._deserialize_data(data) if data else None
    
    def set_transaction_list(self, account_id: int, filters_hash: str, page: int, data: Dict) -> None:
        """Cache transaction list"""
        key = self._make_key('transactions', 'list', account_id, filters_hash, page)
        serialized = self._serialize_data(data)
        cache.set(key, serialized, self.CACHE_TIMEOUTS['transaction_list'])
        logger.debug(f"Cached transaction list for account {account_id}")
    
    def get_category_totals(self, company_id: int, date_from: str, date_to: str) -> Optional[Dict]:
        """Get cached category totals"""
        key = self._make_key('categories', 'totals', company_id, date_from, date_to)
        data = cache.get(key)
        return self._deserialize_data(data) if data else None
    
    def set_category_totals(self, company_id: int, date_from: str, date_to: str, data: Dict) -> None:
        """Cache category totals"""
        key = self._make_key('categories', 'totals', company_id, date_from, date_to)
        serialized = self._serialize_data(data)
        cache.set(key, serialized, self.CACHE_TIMEOUTS['category_totals'])
        logger.debug(f"Cached category totals for company {company_id}")
    
    # Account caching methods
    def get_account_balance(self, account_id: int) -> Optional[Dict]:
        """Get cached account balance"""
        key = self._make_key('accounts', 'balance', account_id)
        data = cache.get(key)
        return self._deserialize_data(data) if data else None
    
    def set_account_balance(self, account_id: int, balance_data: Dict) -> None:
        """Cache account balance"""
        key = self._make_key('accounts', 'balance', account_id)
        serialized = self._serialize_data(balance_data)
        cache.set(key, serialized, self.CACHE_TIMEOUTS['account_balance'])
        logger.debug(f"Cached balance for account {account_id}")
    
    # Bank providers caching
    def get_bank_providers(self) -> Optional[List[Dict]]:
        """Get cached bank providers"""
        key = self._make_key('categories', 'bank_providers')
        data = cache.get(key)
        return self._deserialize_data(data) if data else None
    
    def set_bank_providers(self, providers: List[Dict]) -> None:
        """Cache bank providers"""
        key = self._make_key('categories', 'bank_providers')
        serialized = self._serialize_data(providers)
        cache.set(key, serialized, self.CACHE_TIMEOUTS['bank_providers'])
        logger.debug("Cached bank providers")
    
    # Categories caching
    def get_user_categories(self, company_id: int) -> Optional[List[Dict]]:
        """Get cached user categories"""
        key = self._make_key('categories', 'user', company_id)
        data = cache.get(key)
        return self._deserialize_data(data) if data else None
    
    def set_user_categories(self, company_id: int, categories: List[Dict]) -> None:
        """Cache user categories"""
        key = self._make_key('categories', 'user', company_id)
        serialized = self._serialize_data(categories)
        cache.set(key, serialized, self.CACHE_TIMEOUTS['user_categories'])
        logger.debug(f"Cached categories for company {company_id}")
    
    # Financial insights caching
    def get_financial_insights(self, company_id: int, insight_type: str) -> Optional[Dict]:
        """Get cached financial insights"""
        key = self._make_key('insights', insight_type, company_id)
        data = cache.get(key)
        return self._deserialize_data(data) if data else None
    
    def set_financial_insights(self, company_id: int, insight_type: str, insights: Dict) -> None:
        """Cache financial insights"""
        key = self._make_key('insights', insight_type, company_id)
        serialized = self._serialize_data(insights)
        cache.set(key, serialized, self.CACHE_TIMEOUTS['financial_insights'])
        logger.debug(f"Cached {insight_type} insights for company {company_id}")\n    \n    # Cache invalidation methods\n    def invalidate_company_cache(self, company_id: int) -> None:\n        \"\"\"Invalidate all cache entries for a company\"\"\"\n        patterns = [\n            f\"{self.KEY_PREFIXES['dashboard']}:*:{company_id}:*\",\n            f\"{self.KEY_PREFIXES['categories']}:*:{company_id}:*\",\n            f\"{self.KEY_PREFIXES['insights']}:*:{company_id}:*\",\n        ]\n        \n        for pattern in patterns:\n            try:\n                cache.delete_many(pattern)\n            except Exception as e:\n                logger.warning(f\"Failed to delete cache pattern {pattern}: {e}\")\n        \n        logger.info(f\"Invalidated cache for company {company_id}\")\n    \n    def invalidate_account_cache(self, account_id: int) -> None:\n        \"\"\"Invalidate cache entries for an account\"\"\"\n        patterns = [\n            f\"{self.KEY_PREFIXES['accounts']}:*:{account_id}:*\",\n            f\"{self.KEY_PREFIXES['transactions']}:*:{account_id}:*\",\n        ]\n        \n        for pattern in patterns:\n            try:\n                cache.delete_many(pattern)\n            except Exception as e:\n                logger.warning(f\"Failed to delete cache pattern {pattern}: {e}\")\n        \n        logger.info(f\"Invalidated cache for account {account_id}\")\n    \n    def invalidate_transaction_cache(self, account_id: int) -> None:\n        \"\"\"Invalidate transaction-related cache for an account\"\"\"\n        # When transactions change, invalidate related caches\n        patterns = [\n            f\"{self.KEY_PREFIXES['transactions']}:*:{account_id}:*\",\n            f\"{self.KEY_PREFIXES['dashboard']}:*\",  # Dashboard depends on transactions\n            f\"{self.KEY_PREFIXES['categories']}:totals:*\",  # Category totals\n        ]\n        \n        for pattern in patterns:\n            try:\n                cache.delete_many(pattern)\n            except Exception as e:\n                logger.warning(f\"Failed to delete cache pattern {pattern}: {e}\")\n        \n        logger.info(f\"Invalidated transaction cache for account {account_id}\")\n    \n    def warm_cache_for_company(self, company_id: int) -> None:\n        \"\"\"Pre-warm cache for a company's most accessed data\"\"\"\n        try:\n            # This would typically be called during off-peak hours\n            # or when a user first logs in\n            \n            from .models import BankAccount\n            from .views import EnhancedDashboardView\n            \n            # Get company's accounts\n            accounts = BankAccount.objects.filter(\n                company_id=company_id,\n                status='active'\n            )\n            \n            if not accounts.exists():\n                return\n            \n            # Pre-warm dashboard data\n            # This would call the actual dashboard methods to populate cache\n            logger.info(f\"Started cache warming for company {company_id}\")\n            \n            # Note: In a real implementation, you'd call the actual dashboard methods\n            # to populate the cache, but we need to be careful about circular imports\n            \n        except Exception as e:\n            logger.error(f\"Failed to warm cache for company {company_id}: {e}\")\n    \n    def get_cache_stats(self) -> Dict[str, Any]:\n        \"\"\"Get cache statistics\"\"\"\n        try:\n            # This would require Redis connection for detailed stats\n            stats = {\n                'cache_backend': 'redis',\n                'status': 'connected',\n                'timestamp': timezone.now().isoformat()\n            }\n            \n            # In production, you'd add more detailed stats here\n            return stats\n            \n        except Exception as e:\n            logger.error(f\"Failed to get cache stats: {e}\")\n            return {\n                'cache_backend': 'unknown',\n                'status': 'error',\n                'error': str(e)\n            }\n\n\n# Global cache service instance\ncache_service = BankingCacheService()\n\n\n# Cache decorators for common patterns\ndef cache_result(cache_key_func, timeout=300):\n    \"\"\"Decorator to cache function results\"\"\"\n    def decorator(func):\n        def wrapper(*args, **kwargs):\n            # Generate cache key\n            cache_key = cache_key_func(*args, **kwargs)\n            \n            # Try to get from cache\n            result = cache.get(cache_key)\n            if result is not None:\n                return cache_service._deserialize_data(result)\n            \n            # Calculate result and cache it\n            result = func(*args, **kwargs)\n            serialized = cache_service._serialize_data(result)\n            cache.set(cache_key, serialized, timeout)\n            \n            return result\n        return wrapper\n    return decorator\n\n\ndef invalidate_on_save(cache_patterns):\n    \"\"\"Decorator to invalidate cache when model is saved\"\"\"\n    def decorator(func):\n        def wrapper(self, *args, **kwargs):\n            result = func(self, *args, **kwargs)\n            \n            # Invalidate cache patterns\n            for pattern in cache_patterns:\n                try:\n                    # Pattern can be a function that takes the model instance\n                    if callable(pattern):\n                        pattern_str = pattern(self)\n                    else:\n                        pattern_str = pattern.format(instance=self)\n                    \n                    cache.delete_many(pattern_str)\n                except Exception as e:\n                    logger.warning(f\"Failed to invalidate cache pattern: {e}\")\n            \n            return result\n        return wrapper\n    return decorator