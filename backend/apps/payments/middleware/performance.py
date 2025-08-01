"""
Performance monitoring middleware for payment operations
"""
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class PaymentPerformanceMiddleware(MiddlewareMixin):
    """Middleware to monitor payment operation performance"""
    
    PAYMENT_PATHS = [
        '/api/payments/',
        '/api/checkout/',
        '/api/subscription/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Start performance monitoring for payment endpoints"""
        if not any(request.path.startswith(path) for path in self.PAYMENT_PATHS):
            return None
        
        # Record start time and initial query count
        request._performance_start_time = time.time()
        request._performance_start_queries = len(connection.queries)
        
        return None
    
    def process_response(self, request, response):
        """Log performance metrics for payment endpoints"""
        if not hasattr(request, '_performance_start_time'):
            return response
        
        # Calculate metrics
        end_time = time.time()
        duration_ms = (end_time - request._performance_start_time) * 1000
        query_count = len(connection.queries) - request._performance_start_queries
        
        # Log performance data
        log_data = {
            'path': request.path,
            'method': request.method,
            'duration_ms': round(duration_ms, 2),
            'query_count': query_count,
            'status_code': response.status_code,
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
        }
        
        # Add response size if available
        if hasattr(response, 'content'):
            log_data['response_size_bytes'] = len(response.content)
        
        # Log warnings for slow requests
        if duration_ms > 1000:  # > 1 second
            logger.warning(f"Slow payment request: {log_data}")
        elif duration_ms > 500:  # > 500ms
            logger.info(f"Payment request performance: {log_data}")
        
        # Log warnings for high query count
        if query_count > 10:
            logger.warning(f"High query count for payment request: {log_data}")
            
            # Log actual queries in debug mode
            if settings.DEBUG:
                recent_queries = connection.queries[-query_count:]
                for i, query in enumerate(recent_queries, 1):
                    logger.debug(f"Query {i}: {query['sql']} (Time: {query['time']}s)")
        
        # Store metrics in cache for monitoring dashboard
        self.store_performance_metrics(request.path, request.method, duration_ms, query_count)
        
        # Add performance headers
        response['X-Response-Time'] = f"{duration_ms:.2f}ms"
        response['X-Query-Count'] = str(query_count)
        
        return response
    
    def store_performance_metrics(self, path, method, duration_ms, query_count):
        """Store performance metrics in cache for monitoring"""
        try:
            # Create cache key
            cache_key = f"perf_metrics:{path}:{method}"
            
            # Get existing metrics or create new
            metrics = cache.get(cache_key, {
                'count': 0,
                'total_duration': 0,
                'total_queries': 0,
                'max_duration': 0,
                'min_duration': float('inf'),
                'last_updated': time.time()
            })
            
            # Update metrics
            metrics['count'] += 1
            metrics['total_duration'] += duration_ms
            metrics['total_queries'] += query_count
            metrics['max_duration'] = max(metrics['max_duration'], duration_ms)
            metrics['min_duration'] = min(metrics['min_duration'], duration_ms)
            metrics['last_updated'] = time.time()
            
            # Calculate averages
            metrics['avg_duration'] = metrics['total_duration'] / metrics['count']
            metrics['avg_queries'] = metrics['total_queries'] / metrics['count']
            
            # Store in cache (expire after 1 hour)
            cache.set(cache_key, metrics, 3600)
            
        except Exception as e:
            logger.error(f"Failed to store performance metrics: {e}")


class DatabaseQueryOptimizationMiddleware(MiddlewareMixin):
    """Middleware to detect and log N+1 query problems"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Reset query tracking for new request"""
        if settings.DEBUG:
            connection.queries_log.clear()
        return None
    
    def process_response(self, request, response):
        """Analyze query patterns for optimization opportunities"""
        if not settings.DEBUG or not hasattr(connection, 'queries'):
            return response
        
        queries = connection.queries
        if len(queries) < 5:  # Don't analyze requests with few queries
            return response
        
        # Detect potential N+1 queries
        query_patterns = {}
        for query in queries:
            sql = query['sql']
            # Remove specific IDs and values to identify patterns
            pattern = self.normalize_query(sql)
            
            if pattern not in query_patterns:
                query_patterns[pattern] = []
            query_patterns[pattern].append(query)
        
        # Find patterns that occur multiple times (potential N+1)
        n_plus_one_patterns = {
            pattern: queries_list 
            for pattern, queries_list in query_patterns.items() 
            if len(queries_list) > 3 and 'SELECT' in pattern.upper()
        }
        
        if n_plus_one_patterns:
            logger.warning(
                f"Potential N+1 queries detected on {request.path}: "
                f"{len(n_plus_one_patterns)} patterns with multiple executions"
            )
            
            for pattern, queries_list in n_plus_one_patterns.items():
                logger.warning(
                    f"Pattern executed {len(queries_list)} times: {pattern[:100]}..."
                )
        
        return response
    
    def normalize_query(self, sql):
        """Normalize SQL query to identify patterns"""
        import re
        
        # Replace numbers with placeholder
        sql = re.sub(r'\b\d+\b', '?', sql)
        
        # Replace quoted strings with placeholder
        sql = re.sub(r"'[^']*'", "'?'", sql)
        sql = re.sub(r'"[^"]*"', '"?"', sql)
        
        # Replace IN clauses with placeholder
        sql = re.sub(r'IN \([^)]+\)', 'IN (?)', sql)
        
        # Normalize whitespace
        sql = ' '.join(sql.split())
        
        return sql


def get_performance_metrics():
    """Get current performance metrics from cache"""
    try:
        cache_pattern = "perf_metrics:*"
        # This would require redis or another cache backend that supports pattern matching
        # For now, we'll return a simple structure
        
        # In a real implementation, you'd iterate through all cached metrics
        return {
            'endpoints': {},
            'summary': {
                'total_requests': 0,
                'avg_response_time': 0,
                'slow_requests': 0,
                'high_query_requests': 0
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        return None