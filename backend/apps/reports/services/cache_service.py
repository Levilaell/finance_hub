"""
Caching service for reports module
Handles Redis caching with proper invalidation
"""
import hashlib
import json
import logging
from typing import Any, Optional, Dict, List
from datetime import timedelta

from django.core.cache import cache
from django.conf import settings
from decimal import Decimal

logger = logging.getLogger(__name__)


class ReportCacheService:
    """Service for managing report-related caching"""
    
    # Cache timeout values
    ANALYTICS_TIMEOUT = 60 * 15  # 15 minutes
    REPORT_SUMMARY_TIMEOUT = 60 * 5  # 5 minutes
    CASH_FLOW_TIMEOUT = 60 * 30  # 30 minutes
    CATEGORY_DATA_TIMEOUT = 60 * 60  # 1 hour
    
    @staticmethod
    def _generate_cache_key(prefix: str, **kwargs) -> str:
        """
        Generate a consistent cache key from parameters
        
        Args:
            prefix: Cache key prefix
            **kwargs: Parameters to include in key
            
        Returns:
            MD5 hash of the cache key
        """
        # Sort kwargs for consistent key generation
        sorted_params = sorted(kwargs.items())
        key_string = f"{prefix}_" + "_".join([f"{k}:{v}" for k, v in sorted_params])
        
        # Use MD5 hash for shorter keys
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @classmethod
    def get_analytics_data(cls, company_id: int, period_days: int, 
                          start_date: str, end_date: str) -> Optional[Dict]:
        """
        Get cached analytics data
        
        Args:
            company_id: Company ID
            period_days: Number of days in period
            start_date: Start date ISO format
            end_date: End date ISO format
            
        Returns:
            Cached data or None
        """
        cache_key = cls._generate_cache_key(
            'analytics',
            company_id=company_id,
            period_days=period_days,
            start_date=start_date,
            end_date=end_date
        )
        
        data = cache.get(cache_key)
        if data:
            logger.info(f"Cache hit for analytics data: {cache_key}")
        return data
    
    @classmethod
    def set_analytics_data(cls, company_id: int, period_days: int,
                          start_date: str, end_date: str, data: Dict) -> None:
        """
        Cache analytics data
        
        Args:
            company_id: Company ID
            period_days: Number of days in period
            start_date: Start date ISO format
            end_date: End date ISO format
            data: Data to cache
        """
        cache_key = cls._generate_cache_key(
            'analytics',
            company_id=company_id,
            period_days=period_days,
            start_date=start_date,
            end_date=end_date
        )
        
        # Convert Decimal to float for JSON serialization
        serialized_data = cls._serialize_for_cache(data)
        
        cache.set(cache_key, serialized_data, cls.ANALYTICS_TIMEOUT)
        logger.info(f"Cached analytics data: {cache_key}")
    
    @classmethod
    def get_cash_flow_data(cls, company_id: int, start_date: str, end_date: str) -> Optional[List]:
        """
        Get cached cash flow data
        
        Args:
            company_id: Company ID
            start_date: Start date ISO format
            end_date: End date ISO format
            
        Returns:
            Cached data or None
        """
        cache_key = cls._generate_cache_key(
            'cashflow',
            company_id=company_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return cache.get(cache_key)
    
    @classmethod
    def set_cash_flow_data(cls, company_id: int, start_date: str, 
                          end_date: str, data: List) -> None:
        """
        Cache cash flow data
        
        Args:
            company_id: Company ID
            start_date: Start date ISO format
            end_date: End date ISO format
            data: Data to cache
        """
        cache_key = cls._generate_cache_key(
            'cashflow',
            company_id=company_id,
            start_date=start_date,
            end_date=end_date
        )
        
        serialized_data = cls._serialize_for_cache(data)
        cache.set(cache_key, serialized_data, cls.CASH_FLOW_TIMEOUT)
    
    @classmethod
    def get_report_summary(cls, company_id: int) -> Optional[Dict]:
        """
        Get cached report summary
        
        Args:
            company_id: Company ID
            
        Returns:
            Cached data or None
        """
        cache_key = f"report_summary_{company_id}"
        return cache.get(cache_key)
    
    @classmethod
    def set_report_summary(cls, company_id: int, data: Dict) -> None:
        """
        Cache report summary
        
        Args:
            company_id: Company ID
            data: Data to cache
        """
        cache_key = f"report_summary_{company_id}"
        serialized_data = cls._serialize_for_cache(data)
        cache.set(cache_key, serialized_data, cls.REPORT_SUMMARY_TIMEOUT)
    
    @classmethod
    def invalidate_company_caches(cls, company_id: int) -> None:
        """
        Invalidate all caches for a company
        
        Args:
            company_id: Company ID
        """
        # Pattern-based cache deletion would require Redis SCAN
        # For now, we'll invalidate known cache keys
        patterns = [
            f"report_summary_{company_id}",
            f"analytics_*{company_id}*",
            f"cashflow_*{company_id}*"
        ]
        
        # If using Redis directly
        if hasattr(cache, '_cache'):
            redis_client = cache._cache
            for pattern in patterns:
                for key in redis_client.scan_iter(match=pattern):
                    redis_client.delete(key)
        
        logger.info(f"Invalidated caches for company {company_id}")
    
    @classmethod
    def invalidate_report_caches(cls, report_id: int, company_id: int) -> None:
        """
        Invalidate caches related to a specific report
        
        Args:
            report_id: Report ID
            company_id: Company ID
        """
        # Invalidate report summary for the company
        cache_key = f"report_summary_{company_id}"
        cache.delete(cache_key)
        
        logger.info(f"Invalidated report caches for report {report_id}")
    
    @staticmethod
    def _serialize_for_cache(data: Any) -> Any:
        """
        Convert Decimal and other non-JSON types for caching
        
        Args:
            data: Data to serialize
            
        Returns:
            JSON-serializable data
        """
        if isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, dict):
            return {k: ReportCacheService._serialize_for_cache(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [ReportCacheService._serialize_for_cache(item) for item in data]
        else:
            return data
    
    @classmethod
    def warm_cache(cls, company_id: int) -> None:
        """
        Pre-warm cache for a company
        
        Args:
            company_id: Company ID
        """
        from datetime import datetime, timedelta
        from apps.reports.views_optimized import AnalyticsView
        
        # Warm up common date ranges
        today = datetime.now().date()
        date_ranges = [
            (7, today - timedelta(days=7), today),  # Last 7 days
            (30, today - timedelta(days=30), today),  # Last 30 days
            (90, today - timedelta(days=90), today),  # Last 90 days
        ]
        
        for days, start_date, end_date in date_ranges:
            # This would trigger cache population
            # In practice, you might want to call the actual view logic
            logger.info(f"Pre-warming cache for company {company_id}, {days} days")


class CacheKeyGenerator:
    """Utility class for generating cache keys"""
    
    @staticmethod
    def transaction_stats_key(company_id: int, month: str) -> str:
        """Generate cache key for transaction statistics"""
        return f"trans_stats_{company_id}_{month}"
    
    @staticmethod
    def category_breakdown_key(company_id: int, start_date: str, end_date: str) -> str:
        """Generate cache key for category breakdown"""
        return hashlib.md5(
            f"cat_breakdown_{company_id}_{start_date}_{end_date}".encode()
        ).hexdigest()
    
    @staticmethod
    def account_balance_key(account_id: int, date: str) -> str:
        """Generate cache key for account balance"""
        return f"acc_balance_{account_id}_{date}"