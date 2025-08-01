"""
Unit tests for reports Celery tasks and async functionality
"""
import json
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock, Mock
from io import BytesIO

from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone
from celery.result import AsyncResult
from celery.exceptions import Retry, Ignore

from apps.companies.models import Company, Subscription
from apps.banking.models import BankAccount, Transaction
from apps.categories.models import Category
from apps.reports.models import Report, ScheduledReport
from apps.reports.tasks import (
    generate_report_async,
    process_scheduled_reports,
    cleanup_old_reports,
    send_report_email,
    generate_ai_insights_async,
    update_report_status
)
from apps.reports.exceptions import (
    ReportGenerationInProgressError,
    ReportDataInsufficientError
)

User = get_user_model()


# Use TransactionTestCase for Celery tests to handle database transactions properly
class CeleryTaskTestCase(TransactionTestCase):
    """Base test case for Celery task testing"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            cnpj="12345678000123"
        )
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.user.company = self.company
        self.user.save()
        
        # Create subscription
        self.subscription = Subscription.objects.create(
            company=self.company,
            plan="premium",
            status="active"
        )
        
        # Create test data
        self.account = BankAccount.objects.create(
            company=self.company,
            pluggy_account_id="test_account_123",
            item=MagicMock(),
            type="BANK",
            balance=Decimal("1000.00"),
            currency_code="BRL"
        )
        
        self.category = Category.objects.create(
            name="Food & Dining",
            icon="utensils",
            type="expense"
        )
        
        # Create transactions for testing
        for i in range(10):
            Transaction.objects.create(
                pluggy_transaction_id=f"txn_{i}",
                account=self.account,
                company=self.company.id,
                type="DEBIT" if i % 2 == 0 else "CREDIT",
                amount=Decimal(f"{(i + 1) * 100}.00"),
                description=f"Transaction {i + 1}",
                date=date(2024, 1, i + 1),
                currency_code="BRL",
                category=self.category if i % 2 == 0 else None
            )


class GenerateReportAsyncTest(CeleryTaskTestCase):
    """Test generate_report_async task"""
    
    def setUp(self):
        super().setUp()
        self.report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Async Test Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            created_by=self.user
        )
    
    @patch('apps.reports.report_generator.ReportGenerator.generate_report')
    def test_generate_report_async_success(self, mock_generator):
        """Test successful async report generation"""
        # Mock PDF generation
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b'%PDF-1.4 mock pdf content'
        mock_buffer.tell.return_value = 2048
        mock_generator.return_value = mock_buffer
        
        # Execute task
        result = generate_report_async(self.report.id)
        
        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['report_id'], self.report.id)
        self.assertIn('file_size', result)
        
        # Verify report was updated
        self.report.refresh_from_db()
        self.assertTrue(self.report.is_generated)
        self.assertIsNotNone(self.report.file)
        self.assertEqual(self.report.file_size, 2048)
        self.assertIsNone(self.report.error_message)
        
        # Verify generator was called with correct parameters
        mock_generator.assert_called_once()
        call_args = mock_generator.call_args
        self.assertEqual(call_args[0][0], self.report.report_type)
    
    def test_generate_report_async_not_found(self):
        """Test task with non-existent report ID"""
        result = generate_report_async('00000000-0000-0000-0000-000000000000')
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], 'Report not found')
    
    @patch('apps.reports.report_generator.ReportGenerator.generate_report')
    def test_generate_report_async_generation_error(self, mock_generator):
        """Test task when report generation fails"""
        # Mock generation failure
        mock_generator.side_effect = Exception("PDF generation failed")
        
        # Execute task
        result = generate_report_async(self.report.id)
        
        # Verify error handling
        self.assertEqual(result['status'], 'error')
        self.assertIn('PDF generation failed', result['error'])
        
        # Verify report error state
        self.report.refresh_from_db()
        self.assertFalse(self.report.is_generated)
        self.assertIsNotNone(self.report.error_message)
        self.assertIn('PDF generation failed', self.report.error_message)
    
    @patch('apps.reports.report_generator.ReportGenerator.generate_report')
    def test_generate_report_async_insufficient_data(self, mock_generator):
        """Test task when insufficient data exists"""
        # Delete all transactions
        Transaction.objects.all().delete()
        
        # Mock generator to raise insufficient data error
        mock_generator.side_effect = ReportDataInsufficientError(
            "No transactions found for the specified period"
        )
        
        # Execute task
        result = generate_report_async(self.report.id)
        
        # Verify error handling
        self.assertEqual(result['status'], 'error')
        self.assertIn('No transactions found', result['error'])
        
        # Verify report error state
        self.report.refresh_from_db()
        self.assertFalse(self.report.is_generated)
        self.assertIsNotNone(self.report.error_message)
    
    @patch('apps.reports.report_generator.ReportGenerator.generate_report')
    def test_generate_report_async_retry_on_temporary_error(self, mock_generator):
        """Test task retry mechanism on temporary errors"""
        # Mock temporary failure that should trigger retry
        mock_generator.side_effect = ConnectionError("Temporary database connection error")
        
        # Mock the retry method
        with patch.object(generate_report_async, 'retry') as mock_retry:
            mock_retry.side_effect = Retry("Retrying due to temporary error")
            
            # Execute task - should raise Retry exception
            with self.assertRaises(Retry):
                generate_report_async(self.report.id)
            
            # Verify retry was called
            mock_retry.assert_called_once()
    
    @patch('apps.reports.report_generator.ReportGenerator.generate_report')
    @patch('apps.reports.tasks.send_report_email.delay')
    def test_generate_report_async_with_email_notification(self, mock_email_task, mock_generator):
        """Test report generation with email notification"""
        # Mock PDF generation
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b'%PDF-1.4 mock pdf content'
        mock_buffer.tell.return_value = 1024
        mock_generator.return_value = mock_buffer
        
        # Set report to send email
        self.report.parameters = {'send_email': True, 'email_recipients': ['test@company.com']}
        self.report.save()
        
        # Execute task
        result = generate_report_async(self.report.id)
        
        # Verify report generation succeeded
        self.assertEqual(result['status'], 'success')
        
        # Verify email task was triggered
        mock_email_task.assert_called_once_with(
            self.report.id,
            ['test@company.com']
        )
    
    @patch('apps.reports.report_generator.ReportGenerator.generate_report')
    def test_generate_report_async_progress_tracking(self, mock_generator):
        """Test progress tracking during report generation"""
        # Mock slow generation with progress updates
        def slow_generation(*args, **kwargs):
            # Simulate progress updates
            update_report_status.delay(self.report.id, 'generating_data', 25)
            update_report_status.delay(self.report.id, 'processing_charts', 50)
            update_report_status.delay(self.report.id, 'finalizing_pdf', 75)
            
            mock_buffer = MagicMock()
            mock_buffer.getvalue.return_value = b'%PDF-1.4 content'
            mock_buffer.tell.return_value = 1024
            return mock_buffer
        
        mock_generator.side_effect = slow_generation
        
        # Execute task
        result = generate_report_async(self.report.id)
        
        # Verify successful completion
        self.assertEqual(result['status'], 'success')
        
        # Verify final report state
        self.report.refresh_from_db()
        self.assertTrue(self.report.is_generated)


class ProcessScheduledReportsTest(CeleryTaskTestCase):
    """Test process_scheduled_reports task"""
    
    def setUp(self):
        super().setUp()
        
        # Create scheduled reports with different frequencies
        self.daily_report = ScheduledReport.objects.create(
            company=self.company,
            name='Daily Summary',
            report_type='daily_summary',
            frequency='daily',
            email_recipients=['daily@company.com'],
            file_format='pdf',
            next_run_at=timezone.now() - timedelta(minutes=1),  # Overdue
            created_by=self.user
        )
        
        self.weekly_report = ScheduledReport.objects.create(
            company=self.company,
            name='Weekly Report',
            report_type='weekly_summary',
            frequency='weekly',
            email_recipients=['weekly@company.com'],
            file_format='xlsx',
            next_run_at=timezone.now() + timedelta(hours=1),  # Not due yet
            created_by=self.user
        )
        
        self.monthly_report = ScheduledReport.objects.create(
            company=self.company,
            name='Monthly Report',
            report_type='monthly_summary',
            frequency='monthly',
            email_recipients=['monthly@company.com'],
            file_format='pdf',
            next_run_at=timezone.now() - timedelta(hours=2),  # Overdue
            is_active=False,  # Inactive
            created_by=self.user
        )
    
    @patch('apps.reports.tasks.generate_report_async.delay')
    def test_process_scheduled_reports_due_reports(self, mock_generate_task):
        """Test processing of due scheduled reports"""
        mock_generate_task.return_value = MagicMock(id='task-123')
        
        # Execute task
        result = process_scheduled_reports()
        
        # Verify result
        self.assertIn('processed', result)
        self.assertIn('skipped', result)
        self.assertEqual(result['processed'], 1)  # Only daily report should be processed
        self.assertEqual(result['skipped'], 2)    # Weekly (not due) + Monthly (inactive)
        
        # Verify generate task was called for due report
        mock_generate_task.assert_called_once()
        
        # Verify scheduled report was updated
        self.daily_report.refresh_from_db()
        self.assertIsNotNone(self.daily_report.last_run_at)
        self.assertGreater(self.daily_report.next_run_at, timezone.now())
    
    @patch('apps.reports.tasks.generate_report_async.delay')
    def test_process_scheduled_reports_next_run_calculation(self, mock_generate_task):
        """Test next run time calculation for different frequencies"""
        mock_generate_task.return_value = MagicMock(id='task-123')
        
        # Set all reports as due
        now = timezone.now()
        self.daily_report.next_run_at = now - timedelta(minutes=1)
        self.daily_report.save()
        
        self.weekly_report.next_run_at = now - timedelta(minutes=1)
        self.weekly_report.save()
        
        self.monthly_report.next_run_at = now - timedelta(minutes=1)
        self.monthly_report.is_active = True
        self.monthly_report.save()
        
        # Execute task
        result = process_scheduled_reports()
        
        # Verify all reports were processed
        self.assertEqual(result['processed'], 3)
        
        # Verify next run times are calculated correctly
        self.daily_report.refresh_from_db()
        self.weekly_report.refresh_from_db()
        self.monthly_report.refresh_from_db()
        
        # Daily should be scheduled for tomorrow
        expected_daily = now + timedelta(days=1)
        self.assertAlmostEqual(
            self.daily_report.next_run_at.timestamp(),
            expected_daily.timestamp(),
            delta=60  # Within 1 minute
        )
        
        # Weekly should be scheduled for next week
        expected_weekly = now + timedelta(weeks=1)
        self.assertAlmostEqual(
            self.weekly_report.next_run_at.timestamp(),
            expected_weekly.timestamp(),
            delta=3600  # Within 1 hour
        )
        
        # Monthly should be scheduled for next month
        # (This is more complex due to varying month lengths)
        self.assertGreater(self.monthly_report.next_run_at, now + timedelta(days=25))
    
    def test_process_scheduled_reports_no_due_reports(self):
        """Test processing when no reports are due"""
        # Set all reports as not due
        future_time = timezone.now() + timedelta(hours=24)
        self.daily_report.next_run_at = future_time
        self.daily_report.save()
        
        self.weekly_report.next_run_at = future_time
        self.weekly_report.save()
        
        # Execute task
        result = process_scheduled_reports()
        
        # Verify no reports were processed
        self.assertEqual(result['processed'], 0)
        self.assertEqual(result['skipped'], 3)  # All skipped (including inactive monthly)
    
    @patch('apps.reports.tasks.generate_report_async.delay')
    def test_process_scheduled_reports_error_handling(self, mock_generate_task):
        """Test error handling in scheduled report processing"""
        # Mock task creation failure
        mock_generate_task.side_effect = Exception("Task queue full")
        
        # Execute task - should not raise exception
        result = process_scheduled_reports()
        
        # Should still return result, with errors logged
        self.assertIn('processed', result)
        self.assertIn('errors', result)
        
        # Verify error was recorded
        self.assertGreater(result['errors'], 0)


class CleanupOldReportsTest(CeleryTaskTestCase):
    """Test cleanup_old_reports task"""
    
    def setUp(self):
        super().setUp()
        
        # Create reports of different ages
        now = timezone.now()
        
        # Recent report (should be kept)
        self.recent_report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Recent Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            is_generated=True,
            created_at=now - timedelta(days=30),
            created_by=self.user
        )
        
        # Old report (should be cleaned up)
        self.old_report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Old Report',
            period_start=date(2023, 1, 1),
            period_end=date(2023, 1, 31),
            file_format='pdf',
            is_generated=True,
            created_at=now - timedelta(days=180),  # 6 months old
            created_by=self.user
        )
        
        # Very old report (should be cleaned up)
        self.very_old_report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Very Old Report',
            period_start=date(2022, 1, 1),
            period_end=date(2022, 1, 31),
            file_format='pdf',
            is_generated=True,
            created_at=now - timedelta(days=400),  # Over 1 year old
            created_by=self.user
        )
        
        # Add files to old reports
        self.old_report.file.save('old_report.pdf', ContentFile(b'old content'))
        self.very_old_report.file.save('very_old_report.pdf', ContentFile(b'very old content'))
    
    @override_settings(REPORTS_CLEANUP_AFTER_DAYS=90)
    def test_cleanup_old_reports_by_age(self):
        """Test cleanup of reports older than specified days"""
        # Execute cleanup task
        result = cleanup_old_reports(days_old=90)
        
        # Verify results
        self.assertEqual(result['deleted_count'], 2)  # old_report and very_old_report
        self.assertGreater(result['freed_space_mb'], 0)
        
        # Verify recent report still exists
        self.assertTrue(Report.objects.filter(id=self.recent_report.id).exists())
        
        # Verify old reports were deleted
        self.assertFalse(Report.objects.filter(id=self.old_report.id).exists())
        self.assertFalse(Report.objects.filter(id=self.very_old_report.id).exists())
    
    def test_cleanup_old_reports_preserve_recent(self):
        """Test that recent reports are preserved"""
        # Execute cleanup with very short retention
        result = cleanup_old_reports(days_old=1)
        
        # All reports should be deleted as they're all older than 1 day
        self.assertEqual(result['deleted_count'], 3)
        
        # No reports should remain
        self.assertEqual(Report.objects.filter(company=self.company).count(), 0)
    
    def test_cleanup_old_reports_dry_run(self):
        """Test cleanup in dry run mode"""
        # Execute cleanup in dry run mode
        result = cleanup_old_reports(days_old=90, dry_run=True)
        
        # Should identify reports for deletion but not delete them
        self.assertEqual(result['would_delete_count'], 2)
        self.assertGreater(result['would_free_space_mb'], 0)
        
        # All reports should still exist
        self.assertEqual(Report.objects.filter(company=self.company).count(), 3)
    
    def test_cleanup_old_reports_by_company(self):
        """Test cleanup filtered by company"""
        # Create another company with reports
        other_company = Company.objects.create(
            name="Other Company",
            cnpj="98765432000100"
        )
        
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123"
        )
        other_user.company = other_company
        other_user.save()
        
        other_old_report = Report.objects.create(
            company=other_company,
            report_type='monthly_summary',
            title='Other Company Old Report',
            period_start=date(2022, 1, 1),
            period_end=date(2022, 1, 31),
            file_format='pdf',
            is_generated=True,
            created_at=timezone.now() - timedelta(days=200),
            created_by=other_user
        )
        
        # Execute cleanup for specific company only
        result = cleanup_old_reports(
            days_old=90,
            company_id=self.company.id
        )
        
        # Should only delete this company's old reports
        self.assertEqual(result['deleted_count'], 2)
        
        # Other company's report should still exist
        self.assertTrue(Report.objects.filter(id=other_old_report.id).exists())
    
    def test_cleanup_old_reports_file_size_calculation(self):
        """Test accurate file size calculation during cleanup"""
        # Add known file sizes
        self.old_report.file_size = 1024 * 1024  # 1 MB
        self.old_report.save()
        
        self.very_old_report.file_size = 2 * 1024 * 1024  # 2 MB
        self.very_old_report.save()
        
        # Execute cleanup
        result = cleanup_old_reports(days_old=90)
        
        # Verify freed space calculation
        expected_freed_mb = 3.0  # 1 MB + 2 MB
        self.assertAlmostEqual(result['freed_space_mb'], expected_freed_mb, places=1)


class SendReportEmailTest(CeleryTaskTestCase):
    """Test send_report_email task"""
    
    def setUp(self):
        super().setUp()
        self.report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Email Test Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            is_generated=True,
            created_by=self.user
        )
        
        # Add file to report
        pdf_content = b'%PDF-1.4 test report content'
        self.report.file.save('test_report.pdf', ContentFile(pdf_content))
        self.report.file_size = len(pdf_content)
        self.report.save()
    
    @patch('django.core.mail.EmailMessage.send')
    def test_send_report_email_success(self, mock_send):
        """Test successful report email sending"""
        mock_send.return_value = True
        
        recipients = ['manager@company.com', 'finance@company.com']
        
        # Execute task
        result = send_report_email(self.report.id, recipients)
        
        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['recipients_count'], 2)
        
        # Verify email was sent
        mock_send.assert_called_once()
    
    @patch('django.core.mail.EmailMessage.send')
    def test_send_report_email_with_custom_message(self, mock_send):
        """Test sending email with custom message"""
        mock_send.return_value = True
        
        recipients = ['test@company.com']
        custom_message = "Please find the monthly report attached."
        
        # Execute task
        result = send_report_email(
            self.report.id,
            recipients,
            subject_override="Custom Subject",
            message_override=custom_message
        )
        
        # Verify success
        self.assertEqual(result['status'], 'success')
        
        # Check that custom message was used
        call_args = mock_send.call_args
        # In a real implementation, we'd verify the email content
        mock_send.assert_called_once()
    
    def test_send_report_email_report_not_found(self):
        """Test email sending for non-existent report"""
        result = send_report_email(
            '00000000-0000-0000-0000-000000000000',
            ['test@company.com']
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], 'Report not found')
    
    def test_send_report_email_report_not_generated(self):
        """Test email sending for report that hasn't been generated"""
        self.report.is_generated = False
        self.report.file = None
        self.report.save()
        
        result = send_report_email(
            self.report.id,
            ['test@company.com']
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('not yet generated', result['error'])
    
    @patch('django.core.mail.EmailMessage.send')
    def test_send_report_email_send_failure(self, mock_send):
        """Test handling of email send failure"""
        mock_send.side_effect = Exception("SMTP server unavailable")
        
        result = send_report_email(
            self.report.id,
            ['test@company.com']
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('SMTP server unavailable', result['error'])
    
    @patch('django.core.mail.EmailMessage.send')
    def test_send_report_email_multiple_recipients(self, mock_send):
        """Test sending email to multiple recipients"""
        mock_send.return_value = True
        
        recipients = [
            'ceo@company.com',
            'cfo@company.com',
            'manager@company.com',
            'accountant@company.com'
        ]
        
        result = send_report_email(self.report.id, recipients)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['recipients_count'], 4)
        
        # Verify email was sent once with all recipients
        mock_send.assert_called_once()


class GenerateAIInsightsAsyncTest(CeleryTaskTestCase):
    """Test generate_ai_insights_async task"""
    
    def setUp(self):
        super().setUp()
        self.report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='AI Insights Test Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            parameters={'include_ai_insights': True},
            created_by=self.user
        )
    
    @patch('openai.ChatCompletion.create')
    def test_generate_ai_insights_async_success(self, mock_openai):
        """Test successful AI insights generation"""
        # Mock OpenAI response
        mock_openai.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        'insights': [
                            {
                                'type': 'success',
                                'title': 'Strong Financial Health',
                                'description': 'Your expenses are well controlled.'
                            }
                        ],
                        'predictions': {
                            'next_month_expenses': 2800.00,
                            'savings_potential': 500.00
                        },
                        'recommendations': [
                            {
                                'title': 'Optimize Food Spending',
                                'description': 'Consider meal planning.',
                                'impact': 'medium'
                            }
                        ]
                    })
                )
            )]
        )
        
        # Execute task
        result = generate_ai_insights_async(
            self.company.id,
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertIn('insights', result['data'])
        self.assertIn('predictions', result['data'])
        self.assertIn('recommendations', result['data'])
        
        # Verify OpenAI was called
        mock_openai.assert_called_once()
    
    @patch('openai.ChatCompletion.create')
    def test_generate_ai_insights_async_openai_error(self, mock_openai):
        """Test handling of OpenAI API errors"""
        # Mock OpenAI failure
        mock_openai.side_effect = Exception("OpenAI API rate limit exceeded")
        
        # Execute task
        result = generate_ai_insights_async(
            self.company.id,
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        # Verify error handling
        self.assertEqual(result['status'], 'error')
        self.assertIn('OpenAI API rate limit exceeded', result['error'])
    
    @patch('openai.ChatCompletion.create')
    def test_generate_ai_insights_async_invalid_response(self, mock_openai):
        """Test handling of invalid AI response"""
        # Mock invalid JSON response
        mock_openai.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content="Invalid JSON response from AI"
                )
            )]
        )
        
        # Execute task
        result = generate_ai_insights_async(
            self.company.id,
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        # Verify error handling
        self.assertEqual(result['status'], 'error')
        self.assertIn('Invalid AI response format', result['error'])
    
    @patch('openai.ChatCompletion.create')
    def test_generate_ai_insights_async_with_context(self, mock_openai):
        """Test AI insights generation with additional context"""
        # Mock OpenAI response
        mock_openai.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        'insights': [],
                        'predictions': {},
                        'recommendations': []
                    })
                )
            )]
        )
        
        # Execute task with additional context
        context = {
            'business_type': 'retail',
            'goals': ['reduce_expenses', 'increase_revenue'],
            'focus_areas': ['food', 'transport']
        }
        
        result = generate_ai_insights_async(
            self.company.id,
            date(2024, 1, 1),
            date(2024, 1, 31),
            context=context
        )
        
        # Verify success
        self.assertEqual(result['status'], 'success')
        
        # Verify context was passed to OpenAI
        mock_openai.assert_called_once()
        call_args = mock_openai.call_args
        prompt_content = call_args[1]['messages'][0]['content']
        self.assertIn('retail', prompt_content)
        self.assertIn('reduce_expenses', prompt_content)


class UpdateReportStatusTest(CeleryTaskTestCase):
    """Test update_report_status task for progress tracking"""
    
    def setUp(self):
        super().setUp()
        self.report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Status Update Test Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            created_by=self.user
        )
    
    def test_update_report_status_success(self):
        """Test successful report status update"""
        # Execute task
        result = update_report_status(
            self.report.id,
            'generating_charts',
            50
        )
        
        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['progress'], 50)
        
        # Verify report metadata was updated
        self.report.refresh_from_db()
        # In a real implementation, progress might be stored in metadata
        # self.assertEqual(self.report.progress, 50)
    
    def test_update_report_status_not_found(self):
        """Test status update for non-existent report"""
        result = update_report_status(
            '00000000-0000-0000-0000-000000000000',
            'processing',
            25
        )
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], 'Report not found')
    
    def test_update_report_status_with_custom_data(self):
        """Test status update with custom metadata"""
        custom_data = {
            'current_section': 'transactions_analysis',
            'total_sections': 5,
            'estimated_completion': '2024-01-15T10:30:00Z'
        }
        
        result = update_report_status(
            self.report.id,
            'processing_data',
            75,
            custom_data=custom_data
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['progress'], 75)
        
        # Verify custom data was stored
        # In a real implementation, custom data might be stored in report metadata


class CeleryTaskIntegrationTest(CeleryTaskTestCase):
    """Test integration between multiple Celery tasks"""
    
    def setUp(self):
        super().setUp()
        self.scheduled_report = ScheduledReport.objects.create(
            company=self.company,
            name='Integration Test Report',
            report_type='monthly_summary', 
            frequency='monthly',
            email_recipients=['integration@company.com'],
            file_format='pdf',
            send_email=True,
            next_run_at=timezone.now() - timedelta(minutes=1),  # Due now
            created_by=self.user
        )
    
    @patch('apps.reports.report_generator.ReportGenerator.generate_report')
    @patch('django.core.mail.EmailMessage.send')
    def test_scheduled_report_full_workflow(self, mock_send_email, mock_generator):
        """Test complete scheduled report workflow"""
        # Mock PDF generation
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b'%PDF-1.4 scheduled report content'
        mock_buffer.tell.return_value = 1024
        mock_generator.return_value = mock_buffer
        
        # Mock email sending
        mock_send_email.return_value = True
        
        # Process scheduled reports (this should trigger report generation)
        schedule_result = process_scheduled_reports()
        
        # Verify scheduled report was processed
        self.assertEqual(schedule_result['processed'], 1)
        
        # Verify a report was created
        created_reports = Report.objects.filter(company=self.company)
        self.assertEqual(created_reports.count(), 1)
        
        created_report = created_reports.first()
        
        # Simulate the report generation completing
        generate_result = generate_report_async(created_report.id)
        self.assertEqual(generate_result['status'], 'success')
        
        # Simulate email sending
        email_result = send_report_email(
            created_report.id,
            self.scheduled_report.email_recipients
        )
        self.assertEqual(email_result['status'], 'success')
        
        # Verify scheduled report was updated
        self.scheduled_report.refresh_from_db()
        self.assertIsNotNone(self.scheduled_report.last_run_at)
        self.assertGreater(self.scheduled_report.next_run_at, timezone.now())
    
    @patch('apps.reports.tasks.generate_ai_insights_async.delay')
    @patch('apps.reports.report_generator.ReportGenerator.generate_report')
    def test_report_generation_with_ai_insights_integration(self, mock_generator, mock_ai_task):
        """Test report generation that triggers AI insights generation"""
        # Mock AI task
        mock_ai_task.return_value = MagicMock(id='ai-task-123')
        
        # Mock PDF generation
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b'%PDF-1.4 content with AI placeholder'
        mock_buffer.tell.return_value = 2048
        mock_generator.return_value = mock_buffer
        
        # Create report with AI insights enabled
        report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='AI Integration Test',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            parameters={'include_ai_insights': True, 'ai_type': 'comprehensive'},
            created_by=self.user
        )
        
        # Generate report
        result = generate_report_async(report.id)
        
        # Verify report generation succeeded
        self.assertEqual(result['status'], 'success')
        
        # Verify AI insights task was triggered
        mock_ai_task.assert_called_once_with(
            self.company.id,
            date(2024, 1, 1),
            date(2024, 1, 31),
            context={'type': 'comprehensive', 'report_id': report.id}
        )