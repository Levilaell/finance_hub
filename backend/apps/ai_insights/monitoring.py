"""
Comprehensive Monitoring and Metrics for AI Insights
Provides real-time monitoring, alerting, and performance tracking
"""
import logging
import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, asdict
from collections import defaultdict

from django.conf import settings
from django.core.cache import cache
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from django.core.mail import send_mail

from .models import AIMessage, AIConversation, AICredit, AICreditTransaction, AIInsight

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = None
    

class MetricsCollector:
    """Collects and aggregates metrics for AI Insights"""
    
    METRIC_TYPES = {
        'response_time': 'ms',
        'tokens_used': 'count',
        'credits_consumed': 'count',
        'error_rate': 'percentage',
        'success_rate': 'percentage',
        'active_conversations': 'count',
        'insights_generated': 'count',
        'websocket_connections': 'count',
        'cache_hit_rate': 'percentage',
        'openai_availability': 'percentage',
    }
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.alerts = []
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric value"""
        if name not in self.METRIC_TYPES:
            logger.warning(f"Unknown metric type: {name}")
            return
        
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=self.METRIC_TYPES[name],
            timestamp=timezone.now(),
            tags=tags or {}
        )
        
        # Store in memory for aggregation
        self.metrics[name].append(metric)
        
        # Also store in cache for distributed access
        cache_key = f"metric:{name}:{int(time.time())}"
        cache.set(cache_key, asdict(metric), timeout=3600)  # 1 hour
        
        # Check for alerts
        self._check_alerts(metric)
    
    def record_ai_request(self, start_time: float, success: bool, tokens: int = 0, 
                         model: str = None, error: str = None):
        """Record metrics for an AI request"""
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        self.record_metric('response_time', duration, {'model': model or 'unknown'})
        
        if tokens > 0:
            self.record_metric('tokens_used', tokens, {'model': model or 'unknown'})
        
        if success:
            self.record_metric('success_rate', 100, {'model': model or 'unknown'})
        else:
            self.record_metric('error_rate', 100, {'error': error or 'unknown'})
    
    def _check_alerts(self, metric: PerformanceMetric):
        """Check if metric triggers any alerts"""
        alert_thresholds = {
            'response_time': 5000,  # 5 seconds
            'error_rate': 10,  # 10%
            'credits_consumed': 1000,  # High usage alert
            'openai_availability': 50,  # Below 50% availability
        }
        
        threshold = alert_thresholds.get(metric.name)
        if threshold and metric.value > threshold:
            alert = {
                'metric': metric.name,
                'value': metric.value,
                'threshold': threshold,
                'timestamp': metric.timestamp,
                'severity': 'high' if metric.value > threshold * 2 else 'medium'
            }
            self.alerts.append(alert)
            self._send_alert(alert)
    
    def _send_alert(self, alert: Dict[str, Any]):
        """Send alert notification"""
        try:
            # Log alert
            logger.warning(f"Alert triggered: {json.dumps(alert)}")
            
            # Send email alert for high severity
            if alert['severity'] == 'high' and getattr(settings, 'ENABLE_EMAIL_ALERTS', False):
                send_mail(
                    subject=f"[AI Insights Alert] {alert['metric']} exceeded threshold",
                    message=f"Metric: {alert['metric']}\nValue: {alert['value']}\nThreshold: {alert['threshold']}\nTime: {alert['timestamp']}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=getattr(settings, 'ALERT_RECIPIENTS', []),
                    fail_silently=True
                )
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
    
    def get_metrics_summary(self, period_minutes: int = 60) -> Dict[str, Any]:
        """Get summary of metrics for the specified period"""
        cutoff_time = timezone.now() - timedelta(minutes=period_minutes)
        summary = {}
        
        for metric_name, metrics in self.metrics.items():
            recent_metrics = [m for m in metrics if m.timestamp > cutoff_time]
            
            if recent_metrics:
                values = [m.value for m in recent_metrics]
                summary[metric_name] = {
                    'count': len(recent_metrics),
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'unit': self.METRIC_TYPES[metric_name]
                }
        
        return summary


class AIInsightsMonitor:
    """Main monitoring class for AI Insights"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.health_check_interval = 60  # seconds
        self.last_health_check = None
    
    def monitor_conversation_activity(self) -> Dict[str, Any]:
        """Monitor conversation activity and metrics"""
        try:
            now = timezone.now()
            last_hour = now - timedelta(hours=1)
            last_24h = now - timedelta(hours=24)
            
            # Active conversations
            active_conversations = AIConversation.objects.filter(
                status='active',
                last_message_at__gte=last_hour
            ).count()
            
            # Messages sent
            messages_last_hour = AIMessage.objects.filter(
                created_at__gte=last_hour
            ).count()
            
            messages_last_24h = AIMessage.objects.filter(
                created_at__gte=last_24h
            ).count()
            
            # Credits used
            credits_used_hour = AICreditTransaction.objects.filter(
                type='usage',
                created_at__gte=last_hour
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Insights generated
            insights_generated = AIInsight.objects.filter(
                created_at__gte=last_hour
            ).count()
            
            # Record metrics
            self.metrics_collector.record_metric('active_conversations', active_conversations)
            self.metrics_collector.record_metric('insights_generated', insights_generated)
            
            return {
                'active_conversations': active_conversations,
                'messages_last_hour': messages_last_hour,
                'messages_last_24h': messages_last_24h,
                'credits_used_last_hour': abs(credits_used_hour),
                'insights_generated_last_hour': insights_generated,
                'timestamp': now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error monitoring conversation activity: {str(e)}")
            return {}
    
    def monitor_credit_usage(self) -> Dict[str, Any]:
        """Monitor credit usage patterns"""
        try:
            now = timezone.now()
            
            # Total credits in system
            total_credits = AICredit.objects.aggregate(
                total_balance=Sum('balance'),
                total_bonus=Sum('bonus_credits'),
                total_purchased=Sum('total_purchased')
            )
            
            # Usage patterns
            today = now.date()
            daily_usage = AICreditTransaction.objects.filter(
                type='usage',
                created_at__date=today
            ).aggregate(
                total=Sum('amount'),
                count=Count('id')
            )
            
            # Low balance accounts
            low_balance_threshold = 10
            low_balance_accounts = AICredit.objects.filter(
                balance__lt=low_balance_threshold
            ).count()
            
            # Usage by type
            usage_by_type = AICreditTransaction.objects.filter(
                type='usage',
                created_at__gte=now - timedelta(hours=24)
            ).values('metadata__request_type').annotate(
                count=Count('id'),
                total=Sum('amount')
            )
            
            return {
                'total_credits': {
                    'balance': total_credits['total_balance'] or 0,
                    'bonus': total_credits['total_bonus'] or 0,
                    'purchased': total_credits['total_purchased'] or 0
                },
                'daily_usage': {
                    'credits': abs(daily_usage['total'] or 0),
                    'transactions': daily_usage['count'] or 0
                },
                'low_balance_accounts': low_balance_accounts,
                'usage_by_type': list(usage_by_type),
                'timestamp': now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error monitoring credit usage: {str(e)}")
            return {}
    
    def monitor_system_performance(self) -> Dict[str, Any]:
        """Monitor system performance metrics"""
        try:
            # Cache hit rate
            cache_stats = self._get_cache_stats()
            
            # WebSocket connections (from cache)
            ws_connections = cache.get('ws_total_connections', 0)
            
            # OpenAI health
            from .services.openai_wrapper import openai_wrapper
            openai_health = openai_wrapper.health_check()
            
            # Database connection pool
            from django.db import connection
            db_queries = len(connection.queries)
            
            # Record metrics
            if cache_stats['hit_rate'] is not None:
                self.metrics_collector.record_metric('cache_hit_rate', cache_stats['hit_rate'])
            
            self.metrics_collector.record_metric('websocket_connections', ws_connections)
            
            if openai_health['api_available']:
                self.metrics_collector.record_metric('openai_availability', 100)
            else:
                self.metrics_collector.record_metric('openai_availability', 0)
            
            return {
                'cache_stats': cache_stats,
                'websocket_connections': ws_connections,
                'openai_health': openai_health,
                'database_queries': db_queries,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error monitoring system performance: {str(e)}")
            return {}
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            # Try to get Redis stats if available
            from django.core.cache import cache
            if hasattr(cache._cache, 'get_stats'):
                stats = cache._cache.get_stats()
                hits = stats.get('keyspace_hits', 0)
                misses = stats.get('keyspace_misses', 0)
                total = hits + misses
                hit_rate = (hits / total * 100) if total > 0 else None
                
                return {
                    'hits': hits,
                    'misses': misses,
                    'hit_rate': hit_rate,
                    'memory_used': stats.get('used_memory_human', 'N/A')
                }
        except Exception:
            pass
        
        return {'hit_rate': None, 'status': 'unavailable'}
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        try:
            # Run all health checks
            from .health import run_comprehensive_health_check
            health_status = run_comprehensive_health_check()
            
            # Get monitoring data
            conversation_activity = self.monitor_conversation_activity()
            credit_usage = self.monitor_credit_usage()
            system_performance = self.monitor_system_performance()
            
            # Get metrics summary
            metrics_summary = self.metrics_collector.get_metrics_summary()
            
            # Check for recent alerts
            recent_alerts = [
                alert for alert in self.metrics_collector.alerts
                if alert['timestamp'] > timezone.now() - timedelta(hours=1)
            ]
            
            report = {
                'status': 'healthy' if health_status['overall_healthy'] else 'unhealthy',
                'health_checks': health_status,
                'activity': conversation_activity,
                'credit_usage': credit_usage,
                'performance': system_performance,
                'metrics_summary': metrics_summary,
                'recent_alerts': recent_alerts,
                'generated_at': timezone.now().isoformat()
            }
            
            # Cache the report
            cache.set('ai_insights:health_report', report, timeout=300)  # 5 minutes
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating health report: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'generated_at': timezone.now().isoformat()
            }
    
    def run_periodic_checks(self):
        """Run periodic health and monitoring checks"""
        try:
            current_time = time.time()
            
            # Run health check every interval
            if (self.last_health_check is None or 
                current_time - self.last_health_check > self.health_check_interval):
                
                report = self.generate_health_report()
                self.last_health_check = current_time
                
                # Check if system is unhealthy
                if report['status'] == 'unhealthy':
                    logger.error(f"System unhealthy: {json.dumps(report)}")
                    
                    # Send alert
                    self.metrics_collector._send_alert({
                        'metric': 'system_health',
                        'value': 'unhealthy',
                        'threshold': 'healthy',
                        'timestamp': timezone.now(),
                        'severity': 'high',
                        'details': report
                    })
                
                return report
                
        except Exception as e:
            logger.error(f"Error in periodic checks: {str(e)}")
            return None


# Singleton instance
ai_insights_monitor = AIInsightsMonitor()


# Monitoring middleware
class MonitoringMiddleware:
    """Middleware to track request metrics"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip non-AI insights endpoints
        if not request.path.startswith('/api/ai-insights/'):
            return self.get_response(request)
        
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Record request metrics
        duration = (time.time() - start_time) * 1000
        
        ai_insights_monitor.metrics_collector.record_metric(
            'response_time',
            duration,
            {
                'endpoint': request.path,
                'method': request.method,
                'status': str(response.status_code)
            }
        )
        
        return response