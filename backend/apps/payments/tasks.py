"""
Celery tasks for payment processing and retries
"""
import logging
from celery import shared_task
from django.utils import timezone
from .services.payment_retry_service import payment_retry_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def execute_payment_retry(self, payment_id: int):
    """
    Execute a scheduled payment retry
    
    Args:
        payment_id: ID of the payment to retry
    """
    try:
        logger.info(f"Executing payment retry for payment {payment_id}")
        
        result = payment_retry_service.execute_retry(payment_id)
        
        if result['success']:
            logger.info(f"Payment retry succeeded for payment {payment_id}")
            return result
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.warning(f"Payment retry failed for payment {payment_id}: {error_msg}")
            return result
            
    except Exception as e:
        logger.error(f"Error in payment retry task for payment {payment_id}: {e}")
        
        # Retry the task with exponential backoff
        try:
            self.retry(countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for payment retry task {payment_id}")
            return {'success': False, 'error': 'Task failed after max retries'}


@shared_task
def process_pending_retries():
    """
    Process all pending payment retries that are due
    This task should be run periodically (e.g., every 5 minutes)
    """
    from .models import PaymentRetry
    
    try:
        # Get all active retries that are due
        due_retries = PaymentRetry.objects.filter(
            status='active',
            next_retry_at__lte=timezone.now()
        ).select_related('payment')
        
        if not due_retries.exists():
            logger.debug("No pending payment retries to process")
            return {'processed': 0}
        
        processed_count = 0
        
        for retry_record in due_retries:
            try:
                logger.info(f"Processing due retry for payment {retry_record.payment.id}")
                
                # Execute the retry
                result = payment_retry_service.execute_retry(retry_record.payment.id)
                
                if result['success']:
                    logger.info(f"Scheduled retry succeeded for payment {retry_record.payment.id}")
                else:
                    logger.warning(f"Scheduled retry failed for payment {retry_record.payment.id}: {result.get('error')}")
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing retry for payment {retry_record.payment.id}: {e}")
                continue
        
        logger.info(f"Processed {processed_count} pending payment retries")
        return {'processed': processed_count}
        
    except Exception as e:
        logger.error(f"Error in process_pending_retries task: {e}")
        return {'error': str(e), 'processed': 0}


@shared_task
def cleanup_old_retry_records():
    """
    Clean up old completed/exhausted retry records
    This task should be run daily
    """
    from .models import PaymentRetry
    from datetime import timedelta
    
    try:
        # Delete completed retries older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        
        deleted_count, _ = PaymentRetry.objects.filter(
            status__in=['completed', 'exhausted', 'cancelled'],
            updated_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old payment retry records")
        return {'deleted': deleted_count}
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_retry_records task: {e}")
        return {'error': str(e), 'deleted': 0}


@shared_task
def generate_retry_report():
    """
    Generate a report of payment retry statistics
    This task should be run weekly
    """
    from .models import PaymentRetry, Payment
    from django.db.models import Count, Q
    from datetime import timedelta
    
    try:
        # Get stats for the last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        
        stats = {
            'period': '7 days',
            'total_retries': PaymentRetry.objects.filter(created_at__gte=week_ago).count(),
            'successful_retries': PaymentRetry.objects.filter(
                created_at__gte=week_ago,
                status='completed'
            ).count(),
            'exhausted_retries': PaymentRetry.objects.filter(
                created_at__gte=week_ago,
                status='exhausted'
            ).count(),
            'active_retries': PaymentRetry.objects.filter(status='active').count(),
        }
        
        # Calculate success rate
        if stats['total_retries'] > 0:
            stats['success_rate'] = (stats['successful_retries'] / stats['total_retries']) * 100
        else:
            stats['success_rate'] = 0
        
        # Get most common error codes
        error_codes = PaymentRetry.objects.filter(
            created_at__gte=week_ago
        ).exclude(
            last_error_code=''
        ).values('last_error_code').annotate(
            count=Count('last_error_code')
        ).order_by('-count')[:5]
        
        stats['top_error_codes'] = list(error_codes)
        
        logger.info(f"Payment retry report: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error generating retry report: {e}")
        return {'error': str(e)}


@shared_task
def process_failed_webhooks():
    """
    Process all failed webhooks that are due for retry
    This task should be run every 5-10 minutes
    """
    from .services.webhook_monitoring_service import webhook_monitoring_service
    
    try:
        logger.info("Processing failed webhooks")
        result = webhook_monitoring_service.process_failed_webhooks()
        
        if result.get('processed', 0) > 0:
            logger.info(f"Webhook retry summary: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in process_failed_webhooks task: {e}")
        return {'error': str(e), 'processed': 0}


@shared_task
def cleanup_old_webhook_failures():
    """
    Clean up old webhook failure records
    This task should be run daily
    """
    from .services.webhook_monitoring_service import webhook_monitoring_service
    
    try:
        deleted_count = webhook_monitoring_service.cleanup_old_failures(days=30)
        logger.info(f"Cleaned up {deleted_count} old webhook failure records")
        return {'deleted': deleted_count}
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_webhook_failures task: {e}")
        return {'error': str(e), 'deleted': 0}


@shared_task
def generate_webhook_health_report():
    """
    Generate webhook health metrics report
    This task should be run hourly or daily
    """
    from .services.webhook_monitoring_service import webhook_monitoring_service
    
    try:
        # Get 24-hour metrics
        metrics = webhook_monitoring_service.get_webhook_health_metrics(hours=24)
        
        if metrics.get('error'):
            logger.error(f"Error generating webhook health report: {metrics['error']}")
            return metrics
        
        # Log the report
        health_status = metrics.get('health_status', 'unknown')
        failure_summary = metrics.get('failure_summary', {})
        
        logger.info(f"Webhook Health Report: Status={health_status}, "
                   f"Failures={failure_summary.get('total_failures', 0)}, "
                   f"Pending={failure_summary.get('pending_retries', 0)}")
        
        # Alert if health is not good
        if health_status in ['warning', 'critical']:
            logger.warning(f"Webhook health status is {health_status}: {metrics.get('recommendations', [])}")
            
            # Send notification for critical status
            if health_status == 'critical':
                from .services.notification_service import notification_service
                try:
                    notification_service.notify_payment_failed(
                        company_id=None,  # System notification
                        data={
                            'alert_type': 'webhook_health_critical',
                            'health_status': health_status,
                            'metrics': failure_summary,
                            'recommendations': metrics.get('recommendations', [])
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to send webhook health alert: {e}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error in generate_webhook_health_report task: {e}")
        return {'error': str(e)}