"""
Webhook Monitoring Service
Monitors webhook delivery success/failure rates and provides retry mechanisms
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q
from django.conf import settings
from .audit_service import PaymentAuditService
from .notification_service import notification_service
from ..models import FailedWebhook

logger = logging.getLogger(__name__)


class WebhookMonitoringService:
    """Service for monitoring webhook delivery and health metrics"""
    
    def __init__(self):
        self.max_retries = getattr(settings, 'WEBHOOK_MAX_RETRIES', 5)
        self.initial_backoff_minutes = getattr(settings, 'WEBHOOK_INITIAL_BACKOFF_MINUTES', 5)
        self.max_backoff_hours = getattr(settings, 'WEBHOOK_MAX_BACKOFF_HOURS', 6)
        
    def record_webhook_success(self, event_id: str, event_type: str, processing_time_ms: float):
        """
        Record a successful webhook processing
        
        Args:
            event_id: Unique event identifier
            event_type: Type of webhook event
            processing_time_ms: Time taken to process in milliseconds
        """
        try:
            # Log successful processing
            PaymentAuditService.log_payment_action(
                action='webhook_processed_successfully',
                company=None,
                metadata={
                    'event_id': event_id,
                    'event_type': event_type,
                    'processing_time_ms': processing_time_ms,
                    'source': 'webhook_monitoring'
                }
            )
            
            # If this was a previously failed webhook that succeeded on retry, clean it up
            FailedWebhook.objects.filter(event_id=event_id).delete()
            
            logger.debug(f"Webhook {event_id} processed successfully in {processing_time_ms}ms")
            
        except Exception as e:
            logger.error(f"Error recording webhook success: {e}")
    
    def record_webhook_failure(
        self, 
        event_id: str, 
        event_type: str, 
        event_data: Dict[str, Any],
        error_message: str,
        is_retryable: bool = True
    ) -> Dict[str, Any]:
        """
        Record a failed webhook processing
        
        Args:
            event_id: Unique event identifier
            event_type: Type of webhook event
            event_data: Full webhook event data
            error_message: Error that occurred
            is_retryable: Whether this failure should be retried
            
        Returns:
            Dict with retry decision and next action
        """
        try:
            with transaction.atomic():
                # Get or create failed webhook record
                failed_webhook, created = FailedWebhook.objects.get_or_create(
                    event_id=event_id,
                    defaults={
                        'event_type': event_type,
                        'event_data': event_data,
                        'error_message': error_message,
                        'retry_count': 0,
                        'max_retries': self.max_retries if is_retryable else 0,
                        'next_retry_at': self._calculate_next_retry_time(0) if is_retryable else None
                    }
                )
                
                if not created:
                    # Update existing record
                    failed_webhook.error_message = error_message
                    failed_webhook.updated_at = timezone.now()
                    
                    if is_retryable and failed_webhook.should_retry():
                        failed_webhook.increment_retry()
                    
                    failed_webhook.save()
                
                # Log the failure
                PaymentAuditService.log_security_event(
                    event_type='webhook_processing_failed',
                    company=None,
                    details={
                        'event_id': event_id,
                        'event_type': event_type,
                        'error_message': error_message,
                        'retry_count': failed_webhook.retry_count,
                        'is_retryable': is_retryable,
                        'next_retry_at': failed_webhook.next_retry_at.isoformat() if failed_webhook.next_retry_at else None
                    },
                    severity='warning' if is_retryable and failed_webhook.should_retry() else 'critical'
                )
                
                # Check if we should alert about repeated failures
                self._check_failure_patterns(event_type, failed_webhook)
                
                logger.warning(f"Webhook {event_id} failed: {error_message}")
                
                return {
                    'action': 'retry_scheduled' if (is_retryable and failed_webhook.should_retry()) else 'failed_permanently',
                    'retry_count': failed_webhook.retry_count,
                    'max_retries': failed_webhook.max_retries,
                    'next_retry_at': failed_webhook.next_retry_at.isoformat() if failed_webhook.next_retry_at else None
                }
                
        except Exception as e:
            logger.error(f"Error recording webhook failure: {e}")
            return {'action': 'error', 'error': str(e)}
    
    def process_failed_webhooks(self) -> Dict[str, Any]:
        """
        Process all failed webhooks that are due for retry
        
        Returns:
            Dict with processing results
        """
        try:
            # Get all failed webhooks due for retry
            due_webhooks = FailedWebhook.objects.filter(
                next_retry_at__lte=timezone.now(),
                retry_count__lt=models.F('max_retries')
            ).order_by('next_retry_at')
            
            processed = 0
            successful = 0
            failed = 0
            
            for webhook in due_webhooks:
                try:
                    result = self._retry_webhook(webhook)
                    
                    if result['success']:
                        successful += 1
                        # Delete successful retry
                        webhook.delete()
                        logger.info(f"Webhook {webhook.event_id} retry succeeded")
                    else:
                        failed += 1
                        # Update failure record
                        webhook.error_message = result.get('error', 'Retry failed')
                        webhook.increment_retry()
                        logger.warning(f"Webhook {webhook.event_id} retry failed: {result.get('error')}")
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error retrying webhook {webhook.event_id}: {e}")
                    failed += 1
                    processed += 1
            
            # Log summary
            if processed > 0:
                logger.info(f"Processed {processed} failed webhooks: {successful} successful, {failed} failed")
            
            return {
                'processed': processed,
                'successful': successful,
                'failed': failed
            }
            
        except Exception as e:
            logger.error(f"Error processing failed webhooks: {e}")
            return {'error': str(e), 'processed': 0}
    
    def get_webhook_health_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get webhook health metrics for the specified period
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dict with health metrics
        """
        try:
            since = timezone.now() - timedelta(hours=hours)
            
            # Get failure counts by event type
            failure_counts = FailedWebhook.objects.filter(
                created_at__gte=since
            ).values('event_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Get retry statistics
            retry_stats = FailedWebhook.objects.filter(
                created_at__gte=since
            ).aggregate(
                total_failures=Count('id'),
                total_retries=Count('id', filter=Q(retry_count__gt=0)),
                exhausted_retries=Count('id', filter=Q(retry_count__gte=models.F('max_retries')))
            )
            
            # Calculate success rate (approximate)
            # Note: This is approximate since we don't track all successful webhooks
            total_failures = retry_stats['total_failures'] or 0
            exhausted_failures = retry_stats['exhausted_retries'] or 0
            
            # Get current pending retries
            pending_retries = FailedWebhook.objects.filter(
                retry_count__lt=models.F('max_retries'),
                next_retry_at__gt=timezone.now()
            ).count()
            
            # Get overdue retries (should have been processed but weren't)
            overdue_retries = FailedWebhook.objects.filter(
                retry_count__lt=models.F('max_retries'),
                next_retry_at__lte=timezone.now()
            ).count()
            
            return {
                'period_hours': hours,
                'failure_summary': {
                    'total_failures': total_failures,
                    'total_retries': retry_stats['total_retries'],
                    'exhausted_retries': exhausted_failures,
                    'pending_retries': pending_retries,
                    'overdue_retries': overdue_retries
                },
                'failure_by_type': list(failure_counts),
                'health_status': self._calculate_health_status(total_failures, exhausted_failures, overdue_retries),
                'recommendations': self._generate_recommendations(total_failures, exhausted_failures, overdue_retries)
            }
            
        except Exception as e:
            logger.error(f"Error getting webhook health metrics: {e}")
            return {'error': str(e)}
    
    def cleanup_old_failures(self, days: int = 30) -> int:
        """
        Clean up old failed webhook records
        
        Args:
            days: Number of days to keep records
            
        Returns:
            Number of records deleted
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # Delete old exhausted retries
            deleted_count, _ = FailedWebhook.objects.filter(
                Q(retry_count__gte=models.F('max_retries')) |
                Q(created_at__lt=cutoff_date)
            ).delete()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old webhook failure records")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old webhook failures: {e}")
            return 0
    
    def _retry_webhook(self, webhook: FailedWebhook) -> Dict[str, Any]:
        """
        Retry a specific failed webhook
        
        Args:
            webhook: FailedWebhook instance to retry
            
        Returns:
            Dict with retry result
        """
        try:
            from .webhook_handler import WebhookHandler
            
            # Create webhook handler
            handler = WebhookHandler(gateway='stripe')  # Assuming Stripe for now
            
            # Attempt to reprocess the webhook
            result = handler._process_webhook_event({
                'id': webhook.event_id,
                'type': webhook.event_type,
                'data': webhook.event_data
            })
            
            if result.get('status') == 'success':
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Webhook processing failed')
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _calculate_next_retry_time(self, retry_count: int) -> datetime:
        """Calculate next retry time using exponential backoff"""
        backoff_minutes = self.initial_backoff_minutes * (2 ** retry_count)
        max_backoff_minutes = self.max_backoff_hours * 60
        
        # Cap at maximum backoff
        backoff_minutes = min(backoff_minutes, max_backoff_minutes)
        
        return timezone.now() + timedelta(minutes=backoff_minutes)
    
    def _check_failure_patterns(self, event_type: str, webhook: FailedWebhook):
        """Check for concerning failure patterns and alert if necessary"""
        # Check for repeated failures of the same event type
        recent_failures = FailedWebhook.objects.filter(
            event_type=event_type,
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        # Alert if we have many failures of the same type
        if recent_failures >= 5:
            logger.critical(f"High failure rate for webhook type {event_type}: {recent_failures} failures in the last hour")
            
            # Send alert notification (implement based on your notification system)
            try:
                notification_service.notify_payment_failed(
                    company_id=None,  # System-level notification
                    data={
                        'alert_type': 'webhook_failure_pattern',
                        'event_type': event_type,
                        'failure_count': recent_failures,
                        'time_window': '1 hour'
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send webhook failure alert: {e}")
    
    def _calculate_health_status(self, total_failures: int, exhausted_failures: int, overdue_retries: int) -> str:
        """Calculate overall webhook health status"""
        if overdue_retries > 10:
            return 'critical'
        elif exhausted_failures > 5 or total_failures > 20:
            return 'warning'
        elif total_failures > 0:
            return 'degraded'
        else:
            return 'healthy'
    
    def _generate_recommendations(self, total_failures: int, exhausted_failures: int, overdue_retries: int) -> List[str]:
        """Generate recommendations based on webhook health"""
        recommendations = []
        
        if overdue_retries > 0:
            recommendations.append(f"Process {overdue_retries} overdue webhook retries immediately")
        
        if exhausted_failures > 0:
            recommendations.append(f"Investigate {exhausted_failures} webhooks that exhausted all retries")
        
        if total_failures > 10:
            recommendations.append("High failure rate detected - check system health and external dependencies")
        
        if not recommendations:
            recommendations.append("Webhook system is healthy")
        
        return recommendations


# Singleton instance
webhook_monitoring_service = WebhookMonitoringService()