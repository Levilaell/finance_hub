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
        pass
    
    def _make_key(self, prefix: str, *args) -> str:
        """Generate cache key with prefix and arguments"""
        key_parts = [self.KEY_PREFIXES.get(prefix, prefix)]
        key_parts.extend(str(arg) for arg in args)
        return ':'.join(key_parts)
    
    def _serialize_data(self, data: Any) -> str:
        """Serialize data for cache storage"""
        return json.dumps(data, cls=DecimalEncoder, ensure_ascii=False)
    
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


# Global cache service instance
cache_service = BankingCacheService()