"""
Health Check Functions for AI Insights
Production monitoring and health validation
"""
import logging
from typing import Dict, Any, Tuple
from django.db import connections
from django.core.cache import cache
from django.conf import settings
from channels.layers import get_channel_layer
from apps.ai_insights.services.openai_wrapper import openai_wrapper
import redis

logger = logging.getLogger(__name__)


def check_database() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check database connectivity and AI Insights tables
    
    Returns:
        Tuple[bool, str, Dict]: (is_healthy, message, details)
    """
    try:
        # Test database connection
        connection = connections['default']
        connection.ensure_connection()
        
        # Test AI Insights models
        from apps.ai_insights.models import AICredit, AIConversation, AIMessage, AIInsight
        
        details = {
            'connection_status': 'connected',
            'credits_count': AICredit.objects.count(),
            'conversations_count': AIConversation.objects.count(),
            'messages_count': AIMessage.objects.count(),
            'insights_count': AIInsight.objects.count(),
        }
        
        return True, "Database is healthy", details
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False, f"Database error: {str(e)}", {'error': str(e)}


def check_redis() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check Redis connectivity for caching and WebSocket
    
    Returns:
        Tuple[bool, str, Dict]: (is_healthy, message, details)
    """
    try:
        # Test default cache
        cache.set('health_check', 'ok', 10)
        test_value = cache.get('health_check')
        
        if test_value != 'ok':
            return False, "Redis cache test failed", {'test_result': test_value}
        
        # Test Redis connection directly
        redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0)
        redis_info = redis_client.info()
        
        details = {
            'cache_test': 'passed',
            'redis_version': redis_info.get('redis_version'),
            'connected_clients': redis_info.get('connected_clients'),
            'used_memory_human': redis_info.get('used_memory_human'),
        }
        
        return True, "Redis is healthy", details
        
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return False, f"Redis error: {str(e)}", {'error': str(e)}


def check_openai_connection() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check OpenAI API connectivity and configuration
    
    Returns:
        Tuple[bool, str, Dict]: (is_healthy, message, details)
    """
    try:
        # Use the wrapper's health check
        health_status = openai_wrapper.health_check()
        
        if health_status['status'] == 'healthy':
            return True, "OpenAI API is healthy", health_status
        else:
            return False, f"OpenAI API is unhealthy: {health_status.get('error', 'Unknown error')}", health_status
        
    except Exception as e:
        logger.error(f"OpenAI health check failed: {str(e)}")
        return False, f"OpenAI error: {str(e)}", {'error': str(e)}


def check_websocket_layer() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check WebSocket channel layer connectivity
    
    Returns:
        Tuple[bool, str, Dict]: (is_healthy, message, details)
    """
    try:
        # Get channel layer
        channel_layer = get_channel_layer()
        
        if not channel_layer:
            return False, "Channel layer not configured", {'layer': 'missing'}
        
        # Test channel layer with a simple message
        import asyncio
        from asgiref.sync import async_to_sync
        
        test_channel = 'health-check-channel'
        test_message = {'type': 'health.check', 'data': 'test'}
        
        # Send message
        async_to_sync(channel_layer.send)(test_channel, test_message)
        
        # Receive message
        received = async_to_sync(channel_layer.receive)([test_channel])
        
        if received != test_message:
            return False, "Channel layer message test failed", {
                'sent': test_message,
                'received': received
            }
        
        details = {
            'layer_type': type(channel_layer).__name__,
            'message_test': 'passed',
        }
        
        return True, "WebSocket layer is healthy", details
        
    except Exception as e:
        logger.error(f"WebSocket health check failed: {str(e)}")
        return False, f"WebSocket error: {str(e)}", {'error': str(e)}


def check_credit_system() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check AI credit system functionality
    
    Returns:
        Tuple[bool, str, Dict]: (is_healthy, message, details)
    """
    try:
        from apps.ai_insights.services.credit_service import CreditService
        from apps.companies.models import Company
        
        # Check credit service configuration
        if not CreditService.CREDIT_PACKAGES:
            return False, "Credit packages not configured", {'packages': 'missing'}
        
        if not CreditService.CREDIT_COSTS:
            return False, "Credit costs not configured", {'costs': 'missing'}
        
        # Check active companies with credits
        total_companies = Company.objects.filter(subscription_status='active').count()
        companies_with_credits = Company.objects.filter(
            subscription_status='active',
            ai_credits__isnull=False
        ).count()
        
        details = {
            'credit_packages': len(CreditService.CREDIT_PACKAGES),
            'credit_costs': len(CreditService.CREDIT_COSTS),
            'total_active_companies': total_companies,
            'companies_with_credits': companies_with_credits,
            'coverage_percentage': (companies_with_credits / total_companies * 100) if total_companies > 0 else 0,
        }
        
        return True, "Credit system is healthy", details
        
    except Exception as e:
        logger.error(f"Credit system health check failed: {str(e)}")
        return False, f"Credit system error: {str(e)}", {'error': str(e)}


def check_conversation_system() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check conversation system health
    
    Returns:
        Tuple[bool, str, Dict]: (is_healthy, message, details)
    """
    try:
        from apps.ai_insights.models import AIConversation, AIMessage
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        # Get conversation statistics
        total_conversations = AIConversation.objects.count()
        active_conversations = AIConversation.objects.filter(status='active').count()
        recent_conversations = AIConversation.objects.filter(created_at__gte=last_24h).count()
        
        # Get message statistics
        total_messages = AIMessage.objects.count()
        recent_messages = AIMessage.objects.filter(created_at__gte=last_24h).count()
        
        # Check for system health indicators
        avg_messages_per_conversation = (
            total_messages / total_conversations if total_conversations > 0 else 0
        )
        
        details = {
            'total_conversations': total_conversations,
            'active_conversations': active_conversations,
            'recent_conversations': recent_conversations,
            'total_messages': total_messages,
            'recent_messages': recent_messages,
            'avg_messages_per_conversation': round(avg_messages_per_conversation, 2),
            'activity_rate': f"{recent_conversations}/24h",
        }
        
        return True, "Conversation system is healthy", details
        
    except Exception as e:
        logger.error(f"Conversation system health check failed: {str(e)}")
        return False, f"Conversation system error: {str(e)}", {'error': str(e)}


def run_comprehensive_health_check() -> Dict[str, Any]:
    """
    Run all health checks and return comprehensive status
    
    Returns:
        Dict: Complete health status
    """
    checks = {
        'database': check_database,
        'redis': check_redis,
        'openai': check_openai_connection,
        'websocket': check_websocket_layer,
        'credit_system': check_credit_system,
        'conversation_system': check_conversation_system,
    }
    
    results = {}
    overall_healthy = True
    
    for check_name, check_func in checks.items():
        try:
            is_healthy, message, details = check_func()
            results[check_name] = {
                'healthy': is_healthy,
                'message': message,
                'details': details,
            }
            
            if not is_healthy:
                overall_healthy = False
                
        except Exception as e:
            logger.error(f"Health check {check_name} failed with exception: {str(e)}")
            results[check_name] = {
                'healthy': False,
                'message': f"Health check failed: {str(e)}",
                'details': {'exception': str(e)},
            }
            overall_healthy = False
    
    return {
        'overall_healthy': overall_healthy,
        'timestamp': timezone.now().isoformat(),
        'checks': results,
        'summary': {
            'total_checks': len(checks),
            'passed': sum(1 for r in results.values() if r['healthy']),
            'failed': sum(1 for r in results.values() if not r['healthy']),
        }
    }