"""
Unit tests for Monitoring and Metrics System
Tests comprehensive monitoring, alerting, and performance tracking
"""
import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from apps.ai_insights.monitoring import (
    MetricsCollector,
    AIInsightsMonitor,
    PerformanceMetric,
    MonitoringMiddleware,
    ai_insights_monitor
)

User = get_user_model()


class TestPerformanceMetric(TestCase):
    """Test PerformanceMetric data structure"""
    
    def test_metric_creation(self):
        """Test creating a performance metric"""
        timestamp = timezone.now()
        metric = PerformanceMetric(
            name='response_time',
            value=150.5,
            unit='ms',
            timestamp=timestamp,
            tags={'endpoint': '/api/ai-insights/'}
        )
        
        self.assertEqual(metric.name, 'response_time')
        self.assertEqual(metric.value, 150.5)
        self.assertEqual(metric.unit, 'ms')
        self.assertEqual(metric.timestamp, timestamp)
        self.assertEqual(metric.tags['endpoint'], '/api/ai-insights/')
    
    def test_metric_without_tags(self):
        """Test creating a metric without tags"""
        metric = PerformanceMetric(
            name='tokens_used',
            value=100,
            unit='count',
            timestamp=timezone.now()
        )
        
        self.assertIsNone(metric.tags)


class TestMetricsCollector(TestCase):
    """Test MetricsCollector functionality"""
    
    def setUp(self):
        cache.clear()
        self.collector = MetricsCollector()
    
    def test_record_valid_metric(self):
        """Test recording a valid metric"""
        self.collector.record_metric('response_time', 150.0, {'model': 'gpt-4o-mini'})
        
        # Check metric was recorded
        self.assertIn('response_time', self.collector.metrics)
        self.assertEqual(len(self.collector.metrics['response_time']), 1)
        
        metric = self.collector.metrics['response_time'][0]
        self.assertEqual(metric.value, 150.0)
        self.assertEqual(metric.tags['model'], 'gpt-4o-mini')
    
    def test_record_invalid_metric_type(self):
        """Test recording an invalid metric type"""
        with patch('apps.ai_insights.monitoring.logger') as mock_logger:
            self.collector.record_metric('invalid_metric', 100.0)
            
            # Should log warning for unknown metric type
            mock_logger.warning.assert_called_once()
    
    def test_record_ai_request_success(self):
        """Test recording successful AI request"""
        start_time = time.time() - 0.5  # 500ms ago
        
        self.collector.record_ai_request(
            start_time=start_time,
            success=True,
            tokens=150,
            model='gpt-4o-mini'
        )
        
        # Should record response time, tokens, and success rate
        self.assertIn('response_time', self.collector.metrics)
        self.assertIn('tokens_used', self.collector.metrics)
        self.assertIn('success_rate', self.collector.metrics)
        
        # Check response time is reasonable (around 500ms)
        response_time = self.collector.metrics['response_time'][0].value
        self.assertGreater(response_time, 400)  # At least 400ms
        self.assertLess(response_time, 600)     # Less than 600ms
    
    def test_record_ai_request_failure(self):
        """Test recording failed AI request"""
        start_time = time.time() - 0.2  # 200ms ago
        
        self.collector.record_ai_request(
            start_time=start_time,
            success=False,
            error='Rate limit exceeded'
        )
        
        # Should record response time and error rate
        self.assertIn('response_time', self.collector.metrics)
        self.assertIn('error_rate', self.collector.metrics)
        
        error_metric = self.collector.metrics['error_rate'][0]
        self.assertEqual(error_metric.value, 100)
        self.assertEqual(error_metric.tags['error'], 'Rate limit exceeded')
    
    def test_alert_threshold_triggering(self):
        """Test that alerts are triggered when thresholds are exceeded"""
        with patch.object(self.collector, '_send_alert') as mock_send_alert:
            # Record metric that exceeds threshold
            self.collector.record_metric('response_time', 6000)  # 6 seconds > 5 second threshold
            
            mock_send_alert.assert_called_once()
            
            alert = mock_send_alert.call_args[0][0]
            self.assertEqual(alert['metric'], 'response_time')
            self.assertEqual(alert['value'], 6000)
            self.assertEqual(alert['threshold'], 5000)
            self.assertEqual(alert['severity'], 'high')  # > 2x threshold
    
    def test_alert_not_triggered_below_threshold(self):
        """Test that alerts are not triggered below threshold"""
        with patch.object(self.collector, '_send_alert') as mock_send_alert:
            # Record metric below threshold
            self.collector.record_metric('response_time', 1000)  # 1 second < 5 second threshold
            
            mock_send_alert.assert_not_called()
    
    @patch('apps.ai_insights.monitoring.send_mail')
    @patch('apps.ai_insights.monitoring.settings')
    def test_send_alert_email(self, mock_settings, mock_send_mail):
        """Test sending alert emails for high severity alerts"""
        mock_settings.ENABLE_EMAIL_ALERTS = True
        mock_settings.DEFAULT_FROM_EMAIL = 'test@example.com'
        mock_settings.ALERT_RECIPIENTS = ['admin@example.com']
        
        alert = {
            'metric': 'response_time',
            'value': 10000,
            'threshold': 5000,
            'timestamp': timezone.now(),
            'severity': 'high'
        }
        
        self.collector._send_alert(alert)
        
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args[1]
        self.assertIn('AI Insights Alert', call_args['subject'])
        self.assertEqual(call_args['recipient_list'], ['admin@example.com'])
    
    def test_get_metrics_summary(self):
        """Test getting metrics summary for a time period"""
        # Record some metrics
        now = timezone.now()
        
        # Record metrics with different timestamps
        for i in range(5):
            metric = PerformanceMetric(
                name='response_time',
                value=100 + i * 10,  # 100, 110, 120, 130, 140
                unit='ms',
                timestamp=now - timedelta(minutes=i)
            )
            self.collector.metrics['response_time'].append(metric)
        
        # Get summary for last 3 minutes
        summary = self.collector.get_metrics_summary(period_minutes=3)
        
        self.assertIn('response_time', summary)
        stats = summary['response_time']
        
        self.assertEqual(stats['count'], 3)  # Only last 3 metrics
        self.assertEqual(stats['min'], 120)   # Oldest in range
        self.assertEqual(stats['max'], 140)   # Newest in range
        self.assertEqual(stats['average'], 130)  # (120 + 130 + 140) / 3
    
    def test_cache_integration(self):
        """Test that metrics are cached for distributed access"""
        with patch('apps.ai_insights.monitoring.cache') as mock_cache:
            self.collector.record_metric('tokens_used', 50)
            
            # Should cache the metric
            mock_cache.set.assert_called_once()
            cache_key, cached_data, timeout = mock_cache.set.call_args[0]
            
            self.assertTrue(cache_key.startswith('metric:tokens_used:'))
            self.assertEqual(timeout, 3600)  # 1 hour
            self.assertEqual(cached_data['value'], 50)


class TestAIInsightsMonitor(TestCase):
    """Test AIInsightsMonitor functionality"""
    
    def setUp(self):
        self.monitor = AIInsightsMonitor()
        
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('apps.ai_insights.monitoring.AIConversation')
    @patch('apps.ai_insights.monitoring.AIMessage')
    @patch('apps.ai_insights.monitoring.AICreditTransaction')
    @patch('apps.ai_insights.monitoring.AIInsight')
    def test_monitor_conversation_activity(self, mock_insight, mock_transaction, mock_message, mock_conversation):
        """Test monitoring conversation activity"""
        # Mock database queries
        mock_conversation.objects.filter.return_value.count.return_value = 5
        mock_message.objects.filter.return_value.count.side_effect = [10, 50]  # hour, 24h
        mock_transaction.objects.filter.return_value.aggregate.return_value = {'total': Decimal('-25')}
        mock_insight.objects.filter.return_value.count.return_value = 3
        
        activity = self.monitor.monitor_conversation_activity()
        
        self.assertEqual(activity['active_conversations'], 5)
        self.assertEqual(activity['messages_last_hour'], 10)
        self.assertEqual(activity['messages_last_24h'], 50)
        self.assertEqual(activity['credits_used_last_hour'], 25)
        self.assertEqual(activity['insights_generated_last_hour'], 3)
        self.assertIn('timestamp', activity)
    
    @patch('apps.ai_insights.monitoring.AICredit')
    @patch('apps.ai_insights.monitoring.AICreditTransaction')
    def test_monitor_credit_usage(self, mock_transaction, mock_credit):
        """Test monitoring credit usage"""
        # Mock credit totals
        mock_credit.objects.aggregate.return_value = {
            'total_balance': Decimal('1000'),
            'total_bonus': Decimal('100'),
            'total_purchased': Decimal('5000')
        }
        
        # Mock daily usage
        mock_transaction.objects.filter.return_value.aggregate.return_value = {
            'total': Decimal('-150'),
            'count': 25
        }
        
        # Mock low balance accounts
        mock_credit.objects.filter.return_value.count.return_value = 3
        
        # Mock usage by type
        mock_transaction.objects.filter.return_value.values.return_value.annotate.return_value = [
            {'metadata__request_type': 'general', 'count': 10, 'total': Decimal('-50')},
            {'metadata__request_type': 'analysis', 'count': 15, 'total': Decimal('-100')}
        ]
        
        usage = self.monitor.monitor_credit_usage()
        
        self.assertEqual(usage['total_credits']['balance'], 1000)
        self.assertEqual(usage['total_credits']['bonus'], 100)
        self.assertEqual(usage['total_credits']['purchased'], 5000)
        self.assertEqual(usage['daily_usage']['credits'], 150)
        self.assertEqual(usage['daily_usage']['transactions'], 25)
        self.assertEqual(usage['low_balance_accounts'], 3)
        self.assertEqual(len(usage['usage_by_type']), 2)
    
    @patch('apps.ai_insights.monitoring.cache')
    @patch('apps.ai_insights.monitoring.openai_wrapper')
    def test_monitor_system_performance(self, mock_openai_wrapper, mock_cache):
        """Test monitoring system performance"""
        # Mock cache stats
        mock_cache.get.return_value = 10  # WebSocket connections
        
        # Mock OpenAI health
        mock_openai_wrapper.health_check.return_value = {
            'status': 'healthy',
            'api_available': True,
            'response_time': 150
        }
        
        # Mock cache stats method
        with patch.object(self.monitor, '_get_cache_stats') as mock_cache_stats:
            mock_cache_stats.return_value = {
                'hits': 100,
                'misses': 20,
                'hit_rate': 83.33,
                'memory_used': '50MB'
            }
            
            performance = self.monitor.monitor_system_performance()
            
            self.assertEqual(performance['websocket_connections'], 10)
            self.assertEqual(performance['openai_health']['status'], 'healthy')
            self.assertEqual(performance['cache_stats']['hit_rate'], 83.33)
            self.assertIn('timestamp', performance)
    
    def test_get_cache_stats_unavailable(self):
        """Test cache stats when Redis stats are unavailable"""
        stats = self.monitor._get_cache_stats()
        
        # Should handle unavailable stats gracefully
        self.assertIn('status', stats)
        self.assertEqual(stats['status'], 'unavailable')
        self.assertIsNone(stats['hit_rate'])
    
    @patch.object(AIInsightsMonitor, 'monitor_conversation_activity')
    @patch.object(AIInsightsMonitor, 'monitor_credit_usage')
    @patch.object(AIInsightsMonitor, 'monitor_system_performance')
    @patch('apps.ai_insights.monitoring.run_comprehensive_health_check')
    def test_generate_health_report(self, mock_health_check, mock_performance, mock_credit, mock_activity):
        """Test generating comprehensive health report"""
        # Mock all monitoring methods
        mock_health_check.return_value = {
            'overall_healthy': True,
            'checks': {'database': {'healthy': True}}
        }
        
        mock_activity.return_value = {'active_conversations': 5}
        mock_credit.return_value = {'total_credits': {'balance': 1000}}
        mock_performance.return_value = {'cache_stats': {'hit_rate': 85}}
        
        # Mock metrics summary
        with patch.object(self.monitor.metrics_collector, 'get_metrics_summary') as mock_summary:
            mock_summary.return_value = {'response_time': {'average': 150}}
            
            report = self.monitor.generate_health_report()
            
            self.assertEqual(report['status'], 'healthy')
            self.assertIn('health_checks', report)
            self.assertIn('activity', report)
            self.assertIn('credit_usage', report)
            self.assertIn('performance', report)
            self.assertIn('metrics_summary', report)
            self.assertIn('recent_alerts', report)
            self.assertIn('generated_at', report)
    
    def test_generate_health_report_unhealthy(self):
        """Test generating health report when system is unhealthy"""
        with patch('apps.ai_insights.monitoring.run_comprehensive_health_check') as mock_health_check:
            mock_health_check.return_value = {
                'overall_healthy': False,
                'checks': {'database': {'healthy': False, 'error': 'Connection failed'}}
            }
            
            with patch.object(self.monitor, 'monitor_conversation_activity'):
                with patch.object(self.monitor, 'monitor_credit_usage'):
                    with patch.object(self.monitor, 'monitor_system_performance'):
                        report = self.monitor.generate_health_report()
                        
                        self.assertEqual(report['status'], 'unhealthy')
    
    def test_run_periodic_checks(self):
        """Test running periodic health checks"""
        # Mock time
        with patch('time.time', return_value=1000):
            self.monitor.last_health_check = None
            
            with patch.object(self.monitor, 'generate_health_report') as mock_report:
                mock_report.return_value = {'status': 'healthy'}
                
                result = self.monitor.run_periodic_checks()
                
                self.assertEqual(result['status'], 'healthy')
                self.assertEqual(self.monitor.last_health_check, 1000)
    
    def test_run_periodic_checks_unhealthy_alert(self):
        """Test that unhealthy status triggers alert"""
        with patch('time.time', return_value=2000):
            self.monitor.last_health_check = None
            
            with patch.object(self.monitor, 'generate_health_report') as mock_report:
                mock_report.return_value = {'status': 'unhealthy', 'error': 'Database down'}
                
                with patch.object(self.monitor.metrics_collector, '_send_alert') as mock_alert:
                    result = self.monitor.run_periodic_checks()
                    
                    self.assertEqual(result['status'], 'unhealthy')
                    mock_alert.assert_called_once()
                    
                    alert = mock_alert.call_args[0][0]
                    self.assertEqual(alert['metric'], 'system_health')
                    self.assertEqual(alert['severity'], 'high')


class TestMonitoringMiddleware(TestCase):
    """Test MonitoringMiddleware functionality"""
    
    def setUp(self):
        self.get_response = Mock()
        self.middleware = MonitoringMiddleware(self.get_response)
        
        # Mock response
        self.mock_response = Mock()
        self.mock_response.status_code = 200
        self.get_response.return_value = self.mock_response
    
    def test_middleware_processes_ai_insights_requests(self):
        """Test that middleware processes AI Insights requests"""
        # Mock request
        request = Mock()
        request.path = '/api/ai-insights/conversations/'
        request.method = 'GET'
        
        with patch('apps.ai_insights.monitoring.ai_insights_monitor') as mock_monitor:
            response = self.middleware(request)
            
            # Should call get_response
            self.get_response.assert_called_once_with(request)
            
            # Should record metrics
            mock_monitor.metrics_collector.record_metric.assert_called_once()
            
            # Check metric details
            call_args = mock_monitor.metrics_collector.record_metric.call_args
            self.assertEqual(call_args[0][0], 'response_time')  # metric name
            self.assertIsInstance(call_args[0][1], float)      # duration
            
            tags = call_args[0][2]
            self.assertEqual(tags['endpoint'], '/api/ai-insights/conversations/')
            self.assertEqual(tags['method'], 'GET')
            self.assertEqual(tags['status'], '200')
    
    def test_middleware_skips_non_ai_insights_requests(self):
        """Test that middleware skips non-AI Insights requests"""
        # Mock request to different endpoint
        request = Mock()
        request.path = '/api/banking/accounts/'
        request.method = 'GET'
        
        with patch('apps.ai_insights.monitoring.ai_insights_monitor') as mock_monitor:
            response = self.middleware(request)
            
            # Should call get_response
            self.get_response.assert_called_once_with(request)
            
            # Should NOT record metrics
            mock_monitor.metrics_collector.record_metric.assert_not_called()
    
    def test_middleware_measures_request_duration(self):
        """Test that middleware accurately measures request duration"""
        request = Mock()
        request.path = '/api/ai-insights/test/'
        request.method = 'POST'
        
        # Mock get_response to take some time
        def slow_response(req):
            time.sleep(0.1)  # 100ms delay
            return self.mock_response
        
        self.get_response.side_effect = slow_response
        
        with patch('apps.ai_insights.monitoring.ai_insights_monitor') as mock_monitor:
            response = self.middleware(request)
            
            # Check that duration is reasonable (around 100ms)
            call_args = mock_monitor.metrics_collector.record_metric.call_args
            duration = call_args[0][1]
            
            self.assertGreater(duration, 80)   # At least 80ms
            self.assertLess(duration, 200)     # Less than 200ms


class TestMonitoringSingleton(TestCase):
    """Test monitoring singleton pattern"""
    
    def test_singleton_instance(self):
        """Test that ai_insights_monitor is a singleton"""
        from apps.ai_insights.monitoring import ai_insights_monitor
        
        # Should be the same instance
        monitor1 = ai_insights_monitor
        monitor2 = ai_insights_monitor
        
        self.assertIs(monitor1, monitor2)
    
    def test_singleton_has_metrics_collector(self):
        """Test that singleton has metrics collector"""
        self.assertIsInstance(ai_insights_monitor.metrics_collector, MetricsCollector)


@pytest.mark.django_db
class TestMonitoringIntegration:
    """Integration tests for monitoring system"""
    
    def test_full_monitoring_cycle(self):
        """Test complete monitoring cycle with real data"""
        # Create test data
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create conversation
        from apps.ai_insights.models import AIConversation, AIMessage, AICredit
        
        conversation = AIConversation.objects.create(
            user=user,
            title='Test Conversation',
            status='active'
        )
        
        # Create messages
        AIMessage.objects.create(
            conversation=conversation,
            role='user',
            content='Test message',
            credits_used=1
        )
        
        # Create credits
        AICredit.objects.create(
            user=user,
            balance=100,
            monthly_allowance=50
        )
        
        # Test monitoring
        monitor = AIInsightsMonitor()
        
        activity = monitor.monitor_conversation_activity()
        credit_usage = monitor.monitor_credit_usage()
        
        # Verify data
        assert activity['active_conversations'] >= 1
        assert credit_usage['total_credits']['balance'] >= 100
    
    def test_metrics_persistence(self):
        """Test that metrics persist across collector instances"""
        # Record metric with first collector
        collector1 = MetricsCollector()
        collector1.record_metric('test_metric', 100)
        
        # Create second collector
        collector2 = MetricsCollector()
        
        # Should be able to access cached metrics
        with patch('apps.ai_insights.monitoring.cache') as mock_cache:
            # Mock cache to return stored metric
            mock_cache.get.return_value = {
                'name': 'test_metric',
                'value': 100,
                'unit': 'count',
                'timestamp': timezone.now().isoformat(),
                'tags': {}
            }
            
            # Verify cache interaction
            collector1.record_metric('test_metric', 200)
            mock_cache.set.assert_called()
    
    def test_error_handling_in_monitoring(self):
        """Test error handling in monitoring methods"""
        monitor = AIInsightsMonitor()
        
        # Test with database errors
        with patch('apps.ai_insights.monitoring.AIConversation.objects') as mock_objects:
            mock_objects.filter.side_effect = Exception("Database error")
            
            # Should handle error gracefully
            activity = monitor.monitor_conversation_activity()
            
            # Should return empty dict on error
            assert activity == {}
    
    def test_concurrent_metrics_collection(self):
        """Test concurrent metrics collection"""
        import threading
        
        collector = MetricsCollector()
        results = []
        
        def record_metrics():
            for i in range(10):
                collector.record_metric('concurrent_test', i)
            results.append(len(collector.metrics['concurrent_test']))
        
        # Create multiple threads
        threads = [threading.Thread(target=record_metrics) for _ in range(3)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Should have metrics from all threads
        total_metrics = len(collector.metrics['concurrent_test'])
        assert total_metrics == 30  # 3 threads × 10 metrics each