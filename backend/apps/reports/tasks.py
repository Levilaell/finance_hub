"""
Async tasks for report generation using Celery
"""
import io
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from celery import shared_task
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.template.loader import render_to_string

from apps.reports.models import Report
from apps.reports.report_generator import ReportGenerator
from apps.reports.exceptions import ReportGenerationError

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    soft_time_limit=300,  # 5 minutes
    time_limit=600,  # 10 minutes
)
def generate_report_async(self, report_id: int, regenerate: bool = False) -> Dict[str, Any]:
    """
    Generate report asynchronously with proper error handling and retries
    
    Args:
        report_id: ID of the Report instance
        regenerate: Whether this is a regeneration attempt
        
    Returns:
        Dict with generation results
    """
    try:
        report = Report.objects.select_related('company', 'created_by').get(id=report_id)
        
        # Check if already generated and not regenerating
        if report.is_generated and not regenerate:
            logger.info(f"Report {report_id} already generated, skipping")
            return {
                'status': 'skipped',
                'report_id': report_id,
                'message': 'Report already generated'
            }
        
        # Update status to processing
        report.is_generated = False
        report.error_message = ''
        report.save(update_fields=['is_generated', 'error_message'])
        
        logger.info(f"Starting report generation for {report_id}: {report.title}")
        start_time = timezone.now()
        
        # Generate report
        generator = ReportGenerator(report.company)
        file_buffer = generator.generate_report(
            report_type=report.report_type,
            start_date=report.period_start,
            end_date=report.period_end,
            format=report.file_format,
            filters=report.filters
        )
        
        # Save generated file
        filename = f"{report.title}_{report.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{report.file_format}"
        report.file.save(
            filename,
            ContentFile(file_buffer.getvalue()),
            save=False
        )
        
        # Update report metadata
        generation_time = (timezone.now() - start_time).total_seconds()
        report.is_generated = True
        report.generation_time = generation_time
        report.file_size = file_buffer.tell()  # Get buffer size
        report.save(update_fields=['is_generated', 'generation_time', 'file_size', 'file'])
        
        # Send notification email
        send_report_notification(report, success=True)
        
        logger.info(f"Report {report_id} generated successfully in {generation_time:.2f}s")
        
        return {
            'status': 'success',
            'report_id': report_id,
            'filename': filename,
            'generation_time': generation_time,
            'file_size': report.file_size
        }
        
    except Report.DoesNotExist:
        logger.error(f"Report {report_id} not found")
        return {
            'status': 'error',
            'report_id': report_id,
            'error': 'Report not found'
        }
        
    except Exception as exc:
        logger.error(f"Error generating report {report_id}: {str(exc)}", exc_info=True)
        
        # Update report with error
        try:
            report = Report.objects.get(id=report_id)
            report.error_message = str(exc)
            report.is_generated = False
            report.save(update_fields=['error_message', 'is_generated'])
            
            # Send error notification
            send_report_notification(report, success=False, error=str(exc))
        except:
            pass
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task
def cleanup_old_reports(days: int = 30) -> Dict[str, int]:
    """
    Clean up old generated reports to save storage
    
    Args:
        days: Delete reports older than this many days
        
    Returns:
        Dict with cleanup statistics
    """
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Find old reports with files
    old_reports = Report.objects.filter(
        created_at__lt=cutoff_date,
        is_generated=True
    ).exclude(file='')
    
    deleted_count = 0
    freed_space = 0
    
    for report in old_reports:
        try:
            # Get file size before deletion
            if report.file:
                freed_space += report.file.size
                report.file.delete()
                
            # Mark as not generated
            report.is_generated = False
            report.save(update_fields=['is_generated', 'file'])
            
            deleted_count += 1
            
        except Exception as e:
            logger.error(f"Error cleaning up report {report.id}: {str(e)}")
    
    logger.info(f"Cleaned up {deleted_count} reports, freed {freed_space / 1024 / 1024:.2f} MB")
    
    return {
        'deleted_count': deleted_count,
        'freed_space_mb': freed_space / 1024 / 1024
    }


@shared_task
def generate_scheduled_reports() -> Dict[str, Any]:
    """
    Generate all scheduled reports that are due
    
    Returns:
        Dict with generation statistics
    """
    from apps.reports.models import ScheduledReport
    from datetime import timedelta
    
    now = timezone.now()
    generated_count = 0
    error_count = 0
    
    # Find due scheduled reports
    scheduled_reports = ScheduledReport.objects.filter(
        is_active=True,
        next_run__lte=now
    ).select_related('company', 'created_by')
    
    for scheduled in scheduled_reports:
        try:
            # Create report instance
            report = Report.objects.create(
                company=scheduled.company,
                title=f"{scheduled.name} - {now.strftime('%Y-%m-%d')}",
                description=f"Scheduled report: {scheduled.name}",
                report_type=scheduled.report_type,
                period_start=calculate_period_start(scheduled.frequency),
                period_end=now.date(),
                file_format=scheduled.file_format,
                parameters=scheduled.parameters,
                filters=scheduled.filters,
                created_by=scheduled.created_by
            )
            
            # Generate report asynchronously
            generate_report_async.delay(report.id)
            
            # Update next run time
            scheduled.last_run = now
            scheduled.next_run = calculate_next_run(scheduled.frequency, now)
            scheduled.save(update_fields=['last_run', 'next_run'])
            
            generated_count += 1
            
        except Exception as e:
            logger.error(f"Error generating scheduled report {scheduled.id}: {str(e)}")
            error_count += 1
    
    logger.info(f"Generated {generated_count} scheduled reports, {error_count} errors")
    
    return {
        'generated_count': generated_count,
        'error_count': error_count
    }


def send_report_notification(report: Report, success: bool = True, error: Optional[str] = None):
    """Send email notification about report generation"""
    try:
        if success:
            subject = f"Relatório '{report.title}' está pronto"
            template = 'reports/email/report_ready.html'
            context = {
                'report': report,
                'download_url': f"{settings.FRONTEND_URL}/reports/{report.id}/download"
            }
        else:
            subject = f"Erro ao gerar relatório '{report.title}'"
            template = 'reports/email/report_error.html'
            context = {
                'report': report,
                'error': error
            }
        
        html_message = render_to_string(template, context)
        
        send_mail(
            subject=subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[report.created_by.email],
            html_message=html_message,
            fail_silently=False
        )
        
    except Exception as e:
        logger.error(f"Failed to send report notification: {str(e)}")


def calculate_period_start(frequency: str) -> datetime.date:
    """Calculate period start based on frequency"""
    from datetime import timedelta
    today = timezone.now().date()
    
    if frequency == 'daily':
        return today - timedelta(days=1)
    elif frequency == 'weekly':
        return today - timedelta(days=7)
    elif frequency == 'monthly':
        return today.replace(day=1)
    elif frequency == 'quarterly':
        quarter = (today.month - 1) // 3
        return today.replace(month=quarter * 3 + 1, day=1)
    else:
        return today - timedelta(days=30)


def calculate_next_run(frequency: str, current_time: datetime) -> datetime:
    """Calculate next run time based on frequency"""
    from datetime import timedelta
    
    if frequency == 'daily':
        return current_time + timedelta(days=1)
    elif frequency == 'weekly':
        return current_time + timedelta(weeks=1)
    elif frequency == 'monthly':
        # Next month, same day
        if current_time.month == 12:
            return current_time.replace(year=current_time.year + 1, month=1)
        else:
            return current_time.replace(month=current_time.month + 1)
    elif frequency == 'quarterly':
        # Next quarter
        return current_time + timedelta(days=90)
    else:
        return current_time + timedelta(days=30)