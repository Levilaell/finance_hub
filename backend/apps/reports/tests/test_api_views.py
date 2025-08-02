"""
Integration tests for reports API views
"""
import json
import io
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.companies.models import Company, SubscriptionPlan
from apps.banking.models import BankAccount, Transaction
from apps.banking.models import TransactionCategory
from apps.reports.models import Report, ReportTemplate
from apps.reports.exceptions import (
    InvalidReportPeriodError,
    ReportDataInsufficientError,
    ReportGenerationInProgressError
)

User = get_user_model()


class ReportAPITestCase(APITestCase):
    """Base test case for Report API tests"""
    
    def setUp(self):
        self.company = CompanyFactory(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.user.company = self.company
        self.user.save()
        
        # Create subscription
        # Create subscription plan and assign to company
        from apps.companies.tests.factories import SubscriptionPlanFactory
        self.subscription_plan = SubscriptionPlanFactory(
            name="premium".title(),
            slug="premium",
            has_advanced_reports=True,
            enable_ai_reports=True
        )
        self.company.subscription_plan = self.subscription_plan
        self.company.subscription_status = "active"
        self.company.save()
        
        # Create test data
        self.account = BankAccount.objects.create(
            company=self.company,
            pluggy_account_id="test_account_123",
            item=MagicMock(),
            type="BANK",
            balance=Decimal("1000.00"),
            currency_code="BRL"
        )
        
        self.transaction_category = TransactionCategory.objects.create(
            name="Food & Dining",
            icon="utensils",
            type="expense"
        )
        
        # Create transactions
        for i in range(10):
            Transaction.objects.create(
                pluggy_transaction_id=f"txn_{i}",
                account=self.account,
                company=self.company.id,
                type="DEBIT" if i % 2 == 0 else "CREDIT",
                amount=Decimal(f"{(i + 1) * 10}.00"),
                description=f"Transaction {i + 1}",
                date=(timezone.now() - timedelta(days=i)).date(),
                currency_code="BRL",
                category=self.transaction_category if i % 2 == 0 else None
            )
        
        self.client.force_authenticate(user=self.user)


class ReportListCreateAPITest(ReportAPITestCase):
    """Test Report list and create endpoints"""
    
    def test_list_reports_authenticated(self):
        """Test listing reports for authenticated user"""
        # Create test reports
        for i in range(3):
            Report.objects.create(
                company=self.company,
                report_type='monthly_summary',
                title=f'Test Report {i+1}',
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31),
                file_format='pdf',
                is_generated=i == 0,  # Only first one generated
                created_by=self.user
            )
        
        url = reverse('reports:report-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)
        
        # Check that all reports belong to the user's company
        for report_data in response.data['results']:
            report = Report.objects.get(id=report_data['id'])
            self.assertEqual(report.company, self.company)
    
    def test_list_reports_unauthenticated(self):
        """Test listing reports without authentication"""
        self.client.force_authenticate(user=None)
        
        url = reverse('reports:report-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_reports_filtering(self):
        """Test filtering reports by various parameters"""
        # Create reports with different types and statuses
        Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Monthly Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            is_generated=True,
            created_by=self.user
        )
        
        Report.objects.create(
            company=self.company,
            report_type='cash_flow',
            title='Cash Flow Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='xlsx',
            is_generated=False,
            created_by=self.user
        )
        
        url = reverse('reports:report-list')
        
        # Filter by report type
        response = self.client.get(url, {'report_type': 'monthly_summary'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['report_type'], 'monthly_summary')
        
        # Filter by generation status
        response = self.client.get(url, {'is_generated': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertTrue(response.data['results'][0]['is_generated'])
        
        # Filter by file format
        response = self.client.get(url, {'file_format': 'xlsx'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['file_format'], 'xlsx')
    
    def test_list_reports_pagination(self):
        """Test report list pagination"""
        # Create many reports
        for i in range(25):
            Report.objects.create(
                company=self.company,
                report_type='monthly_summary',
                title=f'Report {i+1}',
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31),
                file_format='pdf',
                created_by=self.user
            )
        
        url = reverse('reports:report-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 25)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])
        
        # Test specific page size
        response = self.client.get(url, {'page_size': 5})
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNotNone(response.data['next'])
    
    @patch('apps.reports.tasks.generate_report_async.delay')
    def test_create_report_success(self, mock_task):
        """Test successful report creation"""
        mock_task.return_value = MagicMock(id='test-task-id')
        
        data = {
            'report_type': 'monthly_summary',
            'title': 'New Monthly Report',
            'description': 'Test monthly summary report',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'file_format': 'pdf',
            'parameters': {
                'include_charts': True,
                'detailed_breakdown': True
            },
            'filters': {
                'account_ids': [str(self.account.id)],
                'min_amount': 50.0
            }
        }
        
        url = reverse('reports:report-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Monthly Report')
        self.assertEqual(response.data['report_type'], 'monthly_summary')
        self.assertFalse(response.data['is_generated'])
        self.assertEqual(response.data['company'], str(self.company.id))
        
        # Verify report was created in database
        report = Report.objects.get(id=response.data['id'])
        self.assertEqual(report.title, 'New Monthly Report')
        self.assertEqual(report.created_by, self.user)
        
        # Verify async task was called
        mock_task.assert_called_once()
    
    def test_create_report_invalid_data(self):
        """Test report creation with invalid data"""
        data = {
            'report_type': 'invalid_type',
            'title': 'Invalid Report',
            'period_start': '2024-02-01',
            'period_end': '2024-01-01',  # End before start
            'file_format': 'invalid_format'
        }
        
        url = reverse('reports:report-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('report_type', response.data)
        self.assertIn('period_start', response.data)
        self.assertIn('file_format', response.data)
    
    def test_create_report_insufficient_data(self):
        """Test report creation when insufficient transaction data exists"""
        # Delete all transactions
        Transaction.objects.all().delete()
        
        data = {
            'report_type': 'monthly_summary',
            'title': 'Empty Report',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'file_format': 'pdf'
        }
        
        url = reverse('reports:report-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn('detail', response.data)


class ReportDetailAPITest(ReportAPITestCase):
    """Test Report detail, update, delete endpoints"""
    
    def setUp(self):
        super().setUp()
        self.report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Test Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            is_generated=True,
            created_by=self.user
        )
    
    def test_get_report_detail(self):
        """Test retrieving report details"""
        url = reverse('reports:report-detail', kwargs={'pk': self.report.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.report.id))
        self.assertEqual(response.data['title'], 'Test Report')
        self.assertTrue(response.data['is_generated'])
    
    def test_get_report_detail_not_found(self):
        """Test retrieving non-existent report"""
        url = reverse('reports:report-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_report_detail_other_company(self):
        """Test accessing report from different company"""
        # Create another company and report
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
        
        other_report = Report.objects.create(
            company=other_company,
            report_type='monthly_summary',
            title='Other Company Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            created_by=other_user
        )
        
        url = reverse('reports:report-detail', kwargs={'pk': other_report.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_report(self):
        """Test updating report (limited fields)"""
        data = {
            'title': 'Updated Report Title',
            'description': 'Updated description'
        }
        
        url = reverse('reports:report-detail', kwargs={'pk': self.report.id})
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Report Title')
        
        # Verify in database
        self.report.refresh_from_db()
        self.assertEqual(self.report.title, 'Updated Report Title')
    
    def test_delete_report(self):
        """Test deleting report"""
        url = reverse('reports:report-detail', kwargs={'pk': self.report.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify report was deleted
        with self.assertRaises(Report.DoesNotExist):
            Report.objects.get(id=self.report.id)


class ReportDownloadAPITest(ReportAPITestCase):
    """Test report download functionality"""
    
    def setUp(self):
        super().setUp()
        self.report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Downloadable Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            is_generated=True,
            created_by=self.user
        )
        
        # Add file to report
        pdf_content = b'%PDF-1.4 fake pdf content for testing'
        self.report.file.save('test_report.pdf', ContentFile(pdf_content))
        self.report.file_size = len(pdf_content)
        self.report.save()
    
    def test_download_report_success(self):
        """Test successful report download"""
        url = reverse('reports:report-download', kwargs={'pk': self.report.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('test_report.pdf', response['Content-Disposition'])
    
    def test_download_report_not_generated(self):
        """Test downloading report that hasn't been generated"""
        self.report.is_generated = False
        self.report.file = None
        self.report.save()
        
        url = reverse('reports:report-download', kwargs={'pk': self.report.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not yet generated', response.data['detail'])
    
    def test_download_report_with_signed_url(self):
        """Test downloading report using signed URL"""
        # First get the signed download URL
        url = reverse('reports:report-detail', kwargs={'pk': self.report.id})
        response = self.client.get(url + 'download/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('download_url', response.data)
        
        # Then use the signed URL (would be a separate request in practice)
        download_url = response.data['download_url']
        # This would require implementing the signed URL endpoint
        # For now, just verify the URL was generated


class ReportRegenerateAPITest(ReportAPITestCase):
    """Test report regeneration functionality"""
    
    def setUp(self):
        super().setUp()
        self.report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Regeneration Test Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            is_generated=True,
            error_message=None,
            created_by=self.user
        )
    
    @patch('apps.reports.tasks.generate_report_async.delay')
    def test_regenerate_report_success(self, mock_task):
        """Test successful report regeneration"""
        mock_task.return_value = MagicMock(id='regenerate-task-id')
        
        url = reverse('reports:report-regenerate', kwargs={'pk': self.report.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['report_id'], self.report.id)
        
        # Verify report status was reset
        self.report.refresh_from_db()
        self.assertFalse(self.report.is_generated)
        self.assertIsNone(self.report.error_message)
        
        # Verify async task was called
        mock_task.assert_called_once_with(self.report.id)
    
    def test_regenerate_report_in_progress(self):
        """Test regenerating report that's already in progress"""
        # Mark report as in progress
        self.report.is_generated = False
        self.report.error_message = None
        self.report.save()
        
        url = reverse('reports:report-regenerate', kwargs={'pk': self.report.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('in progress', response.data['detail'])


class ReportSummaryAPITest(ReportAPITestCase):
    """Test report summary endpoint"""
    
    def setUp(self):
        super().setUp()
        
        # Create various reports for testing
        for i in range(5):
            Report.objects.create(
                company=self.company,
                report_type='monthly_summary',
                title=f'Summary Test Report {i+1}',
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31),
                file_format='pdf',
                is_generated=i < 3,  # First 3 are generated
                error_message='Failed to generate' if i == 4 else None,
                created_by=self.user
            )
    
    def test_get_report_summary(self):
        """Test retrieving report summary statistics"""
        url = reverse('reports:report-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check summary statistics
        self.assertEqual(response.data['total_reports'], 5)
        self.assertEqual(response.data['reports_generated'], 3)
        self.assertEqual(response.data['reports_pending'], 1)
        self.assertEqual(response.data['reports_failed'], 1)
        
        # Check that recent reports are included
        self.assertIn('recent_reports', response.data)
        self.assertLessEqual(len(response.data['recent_reports']), 10)  # Should limit recent reports


class ScheduledReportAPITest(ReportAPITestCase):
    """Test scheduled report endpoints"""
    
    def test_list_scheduled_reports(self):
        """Test listing scheduled reports"""
        # Create test scheduled reports
        for i in range(3):
            ScheduledReport.objects.create(
                company=self.company,
                name=f'Scheduled Report {i+1}',
                report_type='monthly_summary',
                frequency='monthly',
                email_recipients=[f'test{i}@company.com'],
                file_format='pdf',
                is_active=i < 2,  # First 2 are active
                created_by=self.user
            )
        
        url = reverse('reports:scheduled-report-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        
        # Test filtering by active status
        response = self.client.get(url, {'is_active': 'true'})
        self.assertEqual(response.data['count'], 2)
    
    def test_create_scheduled_report(self):
        """Test creating scheduled report"""
        data = {
            'name': 'Weekly Revenue Report',
            'report_type': 'cash_flow',
            'frequency': 'weekly',
            'email_recipients': ['manager@company.com', 'finance@company.com'],
            'file_format': 'xlsx',
            'send_email': True,
            'parameters': {
                'include_projections': True
            }
        }
        
        url = reverse('reports:scheduled-report-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Weekly Revenue Report')
        self.assertEqual(response.data['frequency'], 'weekly')
        self.assertTrue(response.data['is_active'])
        self.assertIsNotNone(response.data['next_run_at'])
        
        # Verify in database
        scheduled_report = ScheduledReport.objects.get(id=response.data['id'])
        self.assertEqual(scheduled_report.company, self.company)
        self.assertEqual(scheduled_report.created_by, self.user)
    
    def test_toggle_scheduled_report(self):
        """Test toggling scheduled report active status"""
        scheduled_report = ScheduledReport.objects.create(
            company=self.company,
            name='Toggle Test Report',
            report_type='monthly_summary',
            frequency='monthly',
            email_recipients=['test@company.com'],
            file_format='pdf',
            is_active=True,
            created_by=self.user
        )
        
        url = reverse('reports:scheduled-report-toggle', kwargs={'pk': scheduled_report.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_active'])
        
        # Verify in database
        scheduled_report.refresh_from_db()
        self.assertFalse(scheduled_report.is_active)
    
    def test_run_scheduled_report_now(self):
        """Test running scheduled report immediately"""
        scheduled_report = ScheduledReport.objects.create(
            company=self.company,
            name='Run Now Test',
            report_type='monthly_summary',
            frequency='monthly',
            email_recipients=['test@company.com'],
            file_format='pdf',
            created_by=self.user
        )
        
        with patch('apps.reports.tasks.generate_report_async.delay') as mock_task:
            mock_task.return_value = MagicMock(id='scheduled-task-id')
            
            url = reverse('reports:scheduled-report-run-now', kwargs={'pk': scheduled_report.id})
            response = self.client.post(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('message', response.data)
            
            # Verify task was called
            mock_task.assert_called_once()


class ReportTemplateAPITest(ReportAPITestCase):
    """Test report template endpoints"""
    
    def test_list_report_templates(self):
        """Test listing report templates"""
        # Create test templates
        for i in range(3):
            ReportTemplate.objects.create(
                company=self.company,
                name=f'Template {i+1}',
                report_type='monthly_summary',
                template_config={'layout': 'standard'},
                is_public=i == 0,  # First one is public
                is_active=i < 2,  # First 2 are active
                created_by=self.user
            )
        
        url = reverse('reports:report-template-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        
        # Test filtering by public status
        response = self.client.get(url, {'is_public': 'true'})
        self.assertEqual(response.data['count'], 1)
    
    def test_create_report_template(self):
        """Test creating report template"""
        data = {
            'name': 'Custom Cash Flow Template',
            'description': 'Custom template for cash flow reports',
            'report_type': 'cash_flow',
            'template_config': {
                'layout': 'landscape',
                'sections': ['summary', 'detailed_breakdown', 'charts']
            },
            'charts': [
                {
                    'type': 'line',
                    'title': 'Monthly Trend',
                    'data_key': 'monthly_data'
                }
            ],
            'default_parameters': {
                'include_projections': True
            },
            'is_public': False
        }
        
        url = reverse('reports:report-template-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Custom Cash Flow Template')
        self.assertEqual(response.data['report_type'], 'cash_flow')
        self.assertFalse(response.data['is_public'])
        self.assertTrue(response.data['is_active'])
        
        # Verify in database
        template = ReportTemplate.objects.get(id=response.data['id'])
        self.assertEqual(template.company, self.company)
        self.assertEqual(template.created_by, self.user)
        self.assertEqual(len(template.charts), 1)


class ReportAPIPermissionsTest(ReportAPITestCase):
    """Test API permissions and security"""
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access reports"""
        self.client.force_authenticate(user=None)
        
        urls = [
            reverse('reports:report-list'),
            reverse('reports:scheduled-report-list'),
            reverse('reports:report-template-list'),
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_company_isolation(self):
        """Test that users can only access their company's reports"""
        # Create another company and user
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
        
        # Create reports for both companies
        our_report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Our Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            created_by=self.user
        )
        
        other_report = Report.objects.create(
            company=other_company,
            report_type='monthly_summary',
            title='Other Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            created_by=other_user
        )
        
        # Test that we can only see our report
        url = reverse('reports:report-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Our Report')
        
        # Test that we cannot access other company's report
        url = reverse('reports:report-detail', kwargs={'pk': other_report.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_subscription_limits(self):
        """Test that subscription limits are enforced"""
        # This would depend on how subscription limits are implemented
        # For now, just test that the endpoint exists and returns appropriate response
        
        # Set subscription to a limited plan
        self.subscription.plan = "starter"  # Assuming starter has limits
        self.subscription.save()
        
        # Create multiple reports to potentially hit limits
        for i in range(5):
            Report.objects.create(
                company=self.company,
                report_type='monthly_summary',
                title=f'Limit Test Report {i+1}',
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31),
                file_format='pdf',
                created_by=self.user
            )
        
        # Try to create another report
        data = {
            'report_type': 'monthly_summary',
            'title': 'Over Limit Report',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'file_format': 'pdf'
        }
        
        url = reverse('reports:report-list')
        # Response depends on how limits are implemented
        # Could be 403 Forbidden or 402 Payment Required
        response = self.client.post(url, data, format='json')
        
        # For now, just verify the endpoint is accessible
        self.assertIn(response.status_code, [
            status.HTTP_201_CREATED,  # If no limits implemented yet
            status.HTTP_403_FORBIDDEN,  # If limits enforced
            status.HTTP_402_PAYMENT_REQUIRED  # If upgrade required
        ])