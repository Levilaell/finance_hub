"""
Monitoring service for report generation
Tracks metrics, logs events, and provides observability
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager
from functools import wraps

from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('reports')


class ReportMonitoringService:
    """Service for monitoring report generation and performance"""
    
    # Metric keys
    METRIC_GENERATION_COUNT = 'report_generation_count'
    METRIC_GENERATION_TIME = 'report_generation_time'
    METRIC_GENERATION_SUCCESS = 'report_generation_success'
    METRIC_GENERATION_FAILURE = 'report_generation_failure'
    METRIC_DOWNLOAD_COUNT = 'report_download_count'
    METRIC_CACHE_HIT_RATE = 'report_cache_hit_rate'
    
    @classmethod
    def log_report_generation_start(cls, report_id: int, report_type: str,
                                  user_id: int, company_id: int) -> None:
        """
        Log the start of report generation
        
        Args:
            report_id: Report ID
            report_type: Type of report
            user_id: User ID
            company_id: Company ID
        """
        logger.info(
            f"Report generation started",
            extra={
                'report_id': report_id,
                'report_type': report_type,
                'user_id': user_id,
                'company_id': company_id,
                'event': 'report_generation_start',
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Increment generation counter
        cls._increment_metric(cls.METRIC_GENERATION_COUNT, tags={
            'report_type': report_type,
            'company_id': company_id
        })
    
    @classmethod
    def log_report_generation_complete(cls, report_id: int, report_type: str,
                                     generation_time: float, file_size: int,
                                     user_id: int, company_id: int) -> None:
        """
        Log successful report generation
        
        Args:
            report_id: Report ID
            report_type: Type of report
            generation_time: Time taken to generate (seconds)
            file_size: Size of generated file (bytes)
            user_id: User ID
            company_id: Company ID
        """
        logger.info(
            f"Report generation completed successfully",
            extra={
                'report_id': report_id,
                'report_type': report_type,
                'generation_time': generation_time,
                'file_size': file_size,
                'file_size_mb': file_size / (1024 * 1024),
                'user_id': user_id,
                'company_id': company_id,
                'event': 'report_generation_complete',
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Record success metric
        cls._increment_metric(cls.METRIC_GENERATION_SUCCESS, tags={
            'report_type': report_type,
            'company_id': company_id
        })
        
        # Record generation time
        cls._record_timing(cls.METRIC_GENERATION_TIME, generation_time, tags={
            'report_type': report_type,
            'company_id': company_id
        })
        
        # Alert if generation took too long
        if generation_time > 60:  # More than 1 minute
            logger.warning(
                f"Report generation took longer than expected",
                extra={
                    'report_id': report_id,
                    'generation_time': generation_time,
                    'threshold': 60
                }
            )
    
    @classmethod
    def log_report_generation_failure(cls, report_id: int, report_type: str,
                                    error: Exception, user_id: int,
                                    company_id: int) -> None:
        """
        Log failed report generation
        
        Args:
            report_id: Report ID
            report_type: Type of report
            error: Exception that occurred
            user_id: User ID
            company_id: Company ID
        """
        logger.error(
            f"Report generation failed",
            extra={
                'report_id': report_id,
                'report_type': report_type,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'user_id': user_id,
                'company_id': company_id,
                'event': 'report_generation_failure',
                'timestamp': timezone.now().isoformat()
            },
            exc_info=True
        )
        
        # Record failure metric
        cls._increment_metric(cls.METRIC_GENERATION_FAILURE, tags={
            'report_type': report_type,
            'company_id': company_id,
            'error_type': type(error).__name__
        })
    
    @classmethod
    def log_report_download(cls, report_id: int, user_id: int,
                          company_id: int, file_size: int) -> None:
        """
        Log report download
        
        Args:
            report_id: Report ID
            user_id: User ID
            company_id: Company ID
            file_size: Size of downloaded file
        """
        logger.info(
            f"Report downloaded",
            extra={
                'report_id': report_id,
                'user_id': user_id,
                'company_id': company_id,
                'file_size': file_size,
                'event': 'report_download',
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Increment download counter
        cls._increment_metric(cls.METRIC_DOWNLOAD_COUNT, tags={
            'company_id': company_id
        })
    
    @classmethod
    def log_cache_hit(cls, cache_key: str, data_size: int) -> None:
        """
        Log cache hit
        
        Args:
            cache_key: Cache key that was hit
            data_size: Size of cached data
        """
        logger.debug(
            f"Cache hit",
            extra={
                'cache_key': cache_key,
                'data_size': data_size,
                'event': 'cache_hit',
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Update cache hit rate
        cls._update_cache_hit_rate(hit=True)
    
    @classmethod
    def log_cache_miss(cls, cache_key: str) -> None:
        """
        Log cache miss
        
        Args:
            cache_key: Cache key that was missed
        """
        logger.debug(
            f"Cache miss",
            extra={
                'cache_key': cache_key,
                'event': 'cache_miss',
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Update cache hit rate
        cls._update_cache_hit_rate(hit=False)
    
    @classmethod
    @contextmanager
    def monitor_operation(cls, operation_name: str, **kwargs):
        """
        Context manager to monitor operation timing
        
        Args:
            operation_name: Name of operation
            **kwargs: Additional context
            
        Example:
            with ReportMonitoringService.monitor_operation('generate_pdf', report_id=123):
                # Generate PDF
        """
        start_time = time.time()
        
        logger.debug(
            f"Operation started: {operation_name}",
            extra={
                'operation': operation_name,
                'context': kwargs,
                'event': 'operation_start',
                'timestamp': timezone.now().isoformat()
            }
        )
        
        try:
            yield
            
            duration = time.time() - start_time
            
            logger.debug(
                f"Operation completed: {operation_name}",
                extra={
                    'operation': operation_name,
                    'duration': duration,
                    'context': kwargs,
                    'event': 'operation_complete',
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Record timing metric
            cls._record_timing(f'operation_{operation_name}', duration, tags=kwargs)
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"Operation failed: {operation_name}",
                extra={
                    'operation': operation_name,
                    'duration': duration,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'context': kwargs,
                    'event': 'operation_failure',
                    'timestamp': timezone.now().isoformat()
                },
                exc_info=True
            )
            
            raise
    
    @classmethod
    def get_metrics_summary(cls, company_id: Optional[int] = None,
                           period_hours: int = 24) -> Dict[str, Any]:
        """
        Get summary of metrics for monitoring dashboard
        
        Args:
            company_id: Filter by company (optional)
            period_hours: Period to summarize (default 24 hours)
            
        Returns:
            Dictionary with metric summary
        """
        # In a real implementation, this would query a metrics store
        # For now, we'll use cache to store simple counters
        
        summary = {
            'period_hours': period_hours,
            'timestamp': timezone.now().isoformat(),
            'generation_count': cls._get_metric_value(cls.METRIC_GENERATION_COUNT),
            'success_count': cls._get_metric_value(cls.METRIC_GENERATION_SUCCESS),
            'failure_count': cls._get_metric_value(cls.METRIC_GENERATION_FAILURE),
            'download_count': cls._get_metric_value(cls.METRIC_DOWNLOAD_COUNT),
            'average_generation_time': cls._get_metric_value(cls.METRIC_GENERATION_TIME),
            'cache_hit_rate': cls._get_metric_value(cls.METRIC_CACHE_HIT_RATE)
        }
        
        # Calculate success rate
        total = summary['success_count'] + summary['failure_count']
        if total > 0:
            summary['success_rate'] = summary['success_count'] / total
        else:
            summary['success_rate'] = 0
        
        return summary
    
    @staticmethod
    def _increment_metric(metric_name: str, value: int = 1,
                         tags: Optional[Dict[str, Any]] = None) -> None:
        """Increment a counter metric"""
        # In production, this would send to a metrics backend like StatsD/Prometheus
        # For now, we'll use cache
        cache_key = f"metric:{metric_name}"
        if tags:
            tag_str = "_".join([f"{k}:{v}" for k, v in sorted(tags.items())])
            cache_key = f"{cache_key}:{tag_str}"
        
        try:
            current = cache.get(cache_key, 0)
            cache.set(cache_key, current + value, 86400)  # 24 hour TTL
        except Exception as e:
            logger.error(f"Failed to increment metric {metric_name}: {e}")
    
    @staticmethod
    def _record_timing(metric_name: str, value: float,
                      tags: Optional[Dict[str, Any]] = None) -> None:
        """Record a timing metric"""
        # In production, this would send to a metrics backend
        # For now, we'll use cache to store a simple average
        cache_key = f"metric:{metric_name}"
        if tags:
            tag_str = "_".join([f"{k}:{v}" for k, v in sorted(tags.items())])
            cache_key = f"{cache_key}:{tag_str}"
        
        try:
            # Simple running average
            count_key = f"{cache_key}:count"
            sum_key = f"{cache_key}:sum"
            
            current_count = cache.get(count_key, 0)
            current_sum = cache.get(sum_key, 0.0)
            
            cache.set(count_key, current_count + 1, 86400)
            cache.set(sum_key, current_sum + value, 86400)
            
            # Store average
            if current_count > 0:
                avg = (current_sum + value) / (current_count + 1)
                cache.set(cache_key, avg, 86400)
                
        except Exception as e:
            logger.error(f"Failed to record timing {metric_name}: {e}")
    
    @staticmethod
    def _update_cache_hit_rate(hit: bool) -> None:
        """Update cache hit rate metric"""
        hits_key = f"metric:{ReportMonitoringService.METRIC_CACHE_HIT_RATE}:hits"
        total_key = f"metric:{ReportMonitoringService.METRIC_CACHE_HIT_RATE}:total"
        
        try:
            hits = cache.get(hits_key, 0)
            total = cache.get(total_key, 0)
            
            if hit:
                hits += 1
            total += 1
            
            cache.set(hits_key, hits, 86400)
            cache.set(total_key, total, 86400)
            
            # Calculate and store rate
            if total > 0:
                rate = hits / total
                cache.set(f"metric:{ReportMonitoringService.METRIC_CACHE_HIT_RATE}", rate, 86400)
                
        except Exception as e:
            logger.error(f"Failed to update cache hit rate: {e}")
    
    @staticmethod
    def _get_metric_value(metric_name: str) -> Any:
        """Get metric value from cache"""
        try:
            return cache.get(f"metric:{metric_name}", 0)
        except Exception:
            return 0


def monitor_report_operation(operation_name: str):
    """
    Decorator to monitor report operations
    
    Args:
        operation_name: Name of the operation
        
    Example:
        @monitor_report_operation('generate_pdf')
        def generate_pdf_report(report):
            # Generate PDF
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract context from arguments if possible
            context = {}
            
            # Try to extract report_id if first arg is a Report instance
            if args and hasattr(args[0], 'id'):
                context['report_id'] = args[0].id
            
            # Try to extract other useful context
            if 'report_type' in kwargs:
                context['report_type'] = kwargs['report_type']
            
            with ReportMonitoringService.monitor_operation(operation_name, **context):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator