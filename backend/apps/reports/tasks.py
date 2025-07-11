"""
Reports app Celery tasks
Asynchronous report generation
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def generate_report_task(report_id):
    """
    Generate report asynchronously
    """
    try:
        from .models import Report
        report = Report.objects.get(id=report_id)
        
        # Mark report as being processed
        report.is_generated = False
        report.save()
        
        # Generate actual report
        logger.info(f"Generating report {report_id} of type {report.report_type}")
        
        from .report_generator import ReportGenerator
        from django.core.files.base import ContentFile
        
        generator = ReportGenerator(report.company)
        
        # Generate report based on type
        # For now, all report types will use the transaction report generator
        # In the future, we can add specific generators for each report type
        buffer = generator.generate_transaction_report(
            start_date=report.period_start,
            end_date=report.period_end,
            format=report.file_format or 'pdf',
            filters=report.parameters
        )
        filename = f"{report.report_type}_{report.period_start}_{report.period_end}.{report.file_format or 'pdf'}"
        
        # Save file
        report.file.save(filename, ContentFile(buffer.getvalue()))
        
        # Update report as completed
        report.is_generated = True
        report.generation_time = int((timezone.now() - report.created_at).total_seconds())
        report.file_size = buffer.tell()
        report.save()
        
        logger.info(f"Report {report_id} generated successfully")
        
        # Send notification to user
        from apps.notifications.email_service import EmailService
        EmailService.send_report_ready_email(report.created_by, report)
        
    except Exception as e:
        logger.error(f"Error generating report {report_id}: {str(e)}")
        
        # Update report as failed
        try:
            report = Report.objects.get(id=report_id)
            report.is_generated = False
            report.error_message = str(e)
            report.save()
        except:
            pass


@shared_task
def process_scheduled_reports():
    """
    Process all scheduled reports that are due
    """
    from .models import ReportSchedule, Report
    from datetime import timedelta
    
    now = timezone.now()
    
    # Get all active schedules
    schedules = ReportSchedule.objects.filter(is_active=True)
    
    for schedule in schedules:
        # Check if schedule is due
        if schedule.next_run_at and schedule.next_run_at <= now:
            logger.info(f"Processing scheduled report: {schedule.name}")
            
            # Calculate date range based on frequency
            if schedule.frequency == 'daily':
                period_start = now.date() - timedelta(days=1)
                period_end = now.date()
            elif schedule.frequency == 'weekly':
                period_start = now.date() - timedelta(days=7)
                period_end = now.date()
            elif schedule.frequency == 'monthly':
                period_start = (now.date().replace(day=1) - timedelta(days=1)).replace(day=1)
                period_end = now.date().replace(day=1) - timedelta(days=1)
            else:
                continue
            
            # Create report
            report = Report.objects.create(
                company=schedule.company,
                report_type=schedule.report_type,
                title=f"{schedule.name} - {now.strftime('%Y-%m-%d')}",
                period_start=period_start,
                period_end=period_end,
                created_by=schedule.created_by
            )
            
            # Queue report generation
            generate_report_task.delay(report.id)
            
            # Update schedule
            schedule.last_run_at = now
            # Calculate next run time based on frequency
            if schedule.frequency == 'daily':
                schedule.next_run_at = now + timedelta(days=1)
            elif schedule.frequency == 'weekly':
                schedule.next_run_at = now + timedelta(days=7)
            elif schedule.frequency == 'monthly':
                schedule.next_run_at = now + timedelta(days=30)
            elif schedule.frequency == 'quarterly':
                schedule.next_run_at = now + timedelta(days=90)
            elif schedule.frequency == 'yearly':
                schedule.next_run_at = now + timedelta(days=365)
            schedule.save()
            
            logger.info(f"Scheduled report queued: {report.id}")


@shared_task
def cleanup_old_reports():
    """
    Clean up old reports to save storage
    """
    from .models import Report
    from datetime import timedelta
    
    # Delete reports older than 90 days
    cutoff_date = timezone.now() - timedelta(days=90)
    
    old_reports = Report.objects.filter(
        created_at__lt=cutoff_date,
        is_generated=True
    )
    
    count = old_reports.count()
    old_reports.delete()
    
    logger.info(f"Cleaned up {count} old reports")
    
    return count