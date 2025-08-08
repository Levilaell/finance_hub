"""
Monitoring and Health Check Views for AI Insights
Provides API endpoints for monitoring, metrics, and health checks
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import cache_page
from django.conf import settings

from .monitoring import ai_insights_monitor
from .health import run_comprehensive_health_check
from .permissions import IsCompanyOwnerOrStaff


class HealthCheckThrottle(AnonRateThrottle):
    """Rate limit for health check endpoints"""
    rate = '60/minute'


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([HealthCheckThrottle])
def health_check(request):
    """
    Basic health check endpoint
    
    Returns 200 if service is operational, 503 if unhealthy
    """
    try:
        # Quick health check
        health_status = run_comprehensive_health_check()
        
        if health_status['overall_healthy']:
            return Response({
                'status': 'healthy',
                'timestamp': health_status['timestamp']
            })
        else:
            return Response({
                'status': 'unhealthy',
                'timestamp': health_status['timestamp'],
                'failed_checks': [
                    name for name, check in health_status['checks'].items()
                    if not check['healthy']
                ]
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompanyOwnerOrStaff])
@cache_page(60)  # Cache for 1 minute
def health_detailed(request):
    """
    Detailed health check endpoint for authenticated users
    
    Provides comprehensive health information
    """
    try:
        health_status = run_comprehensive_health_check()
        return Response(health_status)
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompanyOwnerOrStaff])
def metrics_summary(request):
    """
    Get metrics summary for monitoring
    
    Query parameters:
    - period: Time period in minutes (default: 60)
    """
    try:
        period = int(request.query_params.get('period', 60))
        
        # Get metrics from monitor
        metrics = ai_insights_monitor.metrics_collector.get_metrics_summary(period)
        
        return Response({
            'period_minutes': period,
            'metrics': metrics,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompanyOwnerOrStaff])
def activity_monitor(request):
    """
    Monitor AI Insights activity in real-time
    
    Returns conversation activity, credit usage, and performance metrics
    """
    try:
        # Get monitoring data
        activity = ai_insights_monitor.monitor_conversation_activity()
        credit_usage = ai_insights_monitor.monitor_credit_usage()
        performance = ai_insights_monitor.monitor_system_performance()
        
        return Response({
            'activity': activity,
            'credit_usage': credit_usage,
            'performance': performance
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompanyOwnerOrStaff])
@cache_page(300)  # Cache for 5 minutes
def comprehensive_report(request):
    """
    Generate comprehensive health and monitoring report
    
    Includes health checks, metrics, activity, and alerts
    """
    try:
        report = ai_insights_monitor.generate_health_report()
        return Response(report)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCompanyOwnerOrStaff])
def alerts(request):
    """
    Get recent alerts and warnings
    
    Query parameters:
    - hours: Number of hours to look back (default: 24)
    """
    try:
        from datetime import timedelta
        from django.utils import timezone
        
        hours = int(request.query_params.get('hours', 24))
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Get alerts from monitor
        all_alerts = ai_insights_monitor.metrics_collector.alerts
        recent_alerts = [
            alert for alert in all_alerts
            if alert['timestamp'] > cutoff_time
        ]
        
        # Sort by timestamp descending
        recent_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return Response({
            'alerts': recent_alerts,
            'count': len(recent_alerts),
            'period_hours': hours
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCompanyOwnerOrStaff])
def test_alert(request):
    """
    Test alert system by triggering a test alert
    
    For testing monitoring and alerting functionality
    """
    if not settings.DEBUG:
        return Response({
            'error': 'Test alerts only available in DEBUG mode'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Trigger a test alert
        ai_insights_monitor.metrics_collector._send_alert({
            'metric': 'test_alert',
            'value': 'test',
            'threshold': 'none',
            'timestamp': timezone.now(),
            'severity': request.data.get('severity', 'medium'),
            'message': request.data.get('message', 'This is a test alert')
        })
        
        return Response({
            'status': 'success',
            'message': 'Test alert sent'
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Prometheus-compatible metrics endpoint
@api_view(['GET'])
@permission_classes([AllowAny])  # Use IP whitelist or other auth method
def metrics_prometheus(request):
    """
    Export metrics in Prometheus format
    
    For integration with Prometheus monitoring
    """
    try:
        # Check if request is from allowed IPs
        allowed_ips = getattr(settings, 'PROMETHEUS_ALLOWED_IPS', ['127.0.0.1'])
        client_ip = request.META.get('REMOTE_ADDR')
        
        if client_ip not in allowed_ips and not settings.DEBUG:
            return Response({
                'error': 'Unauthorized'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate Prometheus format metrics
        metrics_data = ai_insights_monitor.metrics_collector.get_metrics_summary(60)
        
        prometheus_output = []
        
        for metric_name, data in metrics_data.items():
            # Type declaration
            prometheus_output.append(f"# TYPE ai_insights_{metric_name} gauge")
            
            # Metric value
            if isinstance(data, dict) and 'average' in data:
                prometheus_output.append(
                    f"ai_insights_{metric_name} {data['average']}"
                )
        
        # Add custom metrics
        activity = ai_insights_monitor.monitor_conversation_activity()
        prometheus_output.extend([
            "# TYPE ai_insights_active_conversations gauge",
            f"ai_insights_active_conversations {activity.get('active_conversations', 0)}",
            "# TYPE ai_insights_messages_per_hour gauge",
            f"ai_insights_messages_per_hour {activity.get('messages_last_hour', 0)}",
        ])
        
        return Response(
            '\n'.join(prometheus_output),
            content_type='text/plain; version=0.0.4'
        )
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# URL configuration for monitoring endpoints
from django.urls import path

urlpatterns = [
    path('health/', health_check, name='ai_insights_health'),
    path('health/detailed/', health_detailed, name='ai_insights_health_detailed'),
    path('metrics/', metrics_summary, name='ai_insights_metrics'),
    path('metrics/prometheus/', metrics_prometheus, name='ai_insights_metrics_prometheus'),
    path('monitor/activity/', activity_monitor, name='ai_insights_activity'),
    path('monitor/report/', comprehensive_report, name='ai_insights_report'),
    path('monitor/alerts/', alerts, name='ai_insights_alerts'),
    path('monitor/test-alert/', test_alert, name='ai_insights_test_alert'),
]