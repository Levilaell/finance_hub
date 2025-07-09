"""
Test report generation views
Tests for ReportViewSet and QuickReportsView
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.banking.models import BankAccount, BankProvider, Transaction, TransactionCategory
from apps.companies.models import Company, SubscriptionPlan
from apps.reports.models import Report, ReportSchedule, ReportTemplate

User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class TestReportViewSet(TestCase):
    """Test ReportViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            slug='pro-plan',
            plan_type='pro',
            price_monthly=99.90,
            price_yearly=999.00
        )
        
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        
        # Create companies
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan
        )
        self.user.company = self.company
        self.user.save()
        
        self.other_company = Company.objects.create(
            name='Other Company',
            cnpj='99888777000166',
            owner=self.other_user,
            subscription_plan=self.plan
        )
        self.other_user.company = self.other_company
        self.other_user.save()
        
        # Create some test reports
        self.report1 = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='January 2025 Report',
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            file_format='pdf',
            created_by=self.user,
            is_generated=True
        )
        
        self.report2 = Report.objects.create(
            company=self.company,
            report_type='cash_flow',
            title='Cash Flow Report',
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            file_format='xlsx',
            created_by=self.user
        )
        
        # Other company's report
        self.other_report = Report.objects.create(
            company=self.other_company,
            report_type='annual_report',
            title='Annual Report 2024',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            file_format='pdf',
            created_by=self.other_user
        )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    def test_list_reports(self):
        """Test listing company reports"""
        url = reverse('reports:report-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Should not include other company's report
        report_ids = [r['id'] for r in response.data['results']]
        self.assertIn(self.report1.id, report_ids)
        self.assertIn(self.report2.id, report_ids)
        self.assertNotIn(self.other_report.id, report_ids)
    
    def test_retrieve_report(self):
        """Test retrieving single report"""
        url = reverse('reports:report-detail', kwargs={'pk': self.report1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'January 2025 Report')
        self.assertEqual(response.data['report_type'], 'monthly_summary')
    
    def test_retrieve_other_company_report_forbidden(self):
        """Test cannot retrieve other company's report"""
        url = reverse('reports:report-detail', kwargs={'pk': self.other_report.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('apps.reports.tasks.generate_report_task.delay')
    def test_create_report(self, mock_task):
        """Test creating a new report"""
        url = reverse('reports:report-list')
        data = {
            'report_type': 'quarterly_report',
            'title': 'Q1 2025 Report',
            'period_start': '2025-01-01',
            'period_end': '2025-03-31',
            'file_format': 'pdf'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['report_type'], 'quarterly_report')
        self.assertEqual(response.data['title'], 'Q1 2025 Report')
        
        # Check report was created
        report = Report.objects.get(id=response.data['id'])
        self.assertEqual(report.company, self.company)
        self.assertEqual(report.created_by, self.user)
        
        # Check task was queued
        mock_task.assert_called_once()
    
    @patch('apps.reports.tasks.generate_report_task.delay')
    def test_create_report_missing_fields(self, mock_task):
        """Test creating report with missing required fields"""
        url = reverse('reports:report-list')
        data = {
            'report_type': 'monthly_summary'
            # Missing period_start and period_end
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        mock_task.assert_not_called()
    
    def test_download_report_not_ready(self):
        """Test download report that's not ready"""
        url = reverse('reports:report-download', kwargs={'pk': self.report2.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Report is not ready for download')
    
    def test_download_report_file_not_found(self):
        """Test download report with missing file"""
        # Set report as completed but without file
        self.report1.is_generated = True
        self.report1.file = None
        self.report1.save()
        
        url = reverse('reports:report-download', kwargs={'pk': self.report1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_report_summary(self):
        """Test report summary endpoint"""
        # Create more reports with different statuses
        Report.objects.create(
            company=self.company,
            report_type='tax_report',
            title='Tax Report',
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            created_by=self.user,
            is_generated=False,
            error_message='Failed to generate'
        )
        
        url = reverse('reports:report-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_reports'], 3)
        self.assertIn('reports_by_type', response.data)
        self.assertIn('recent_reports', response.data)
        self.assertEqual(len(response.data['recent_reports']), 3)
    
    def test_update_report(self):
        """Test updating report"""
        url = reverse('reports:report-detail', kwargs={'pk': self.report1.pk})
        data = {
            'title': 'Updated Report Title',
            'description': 'New description'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.report1.refresh_from_db()
        self.assertEqual(self.report1.title, 'Updated Report Title')
        self.assertEqual(self.report1.description, 'New description')
    
    def test_delete_report(self):
        """Test deleting report"""
        url = reverse('reports:report-detail', kwargs={'pk': self.report2.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Report.objects.filter(pk=self.report2.pk).exists())
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access is denied"""
        self.client.force_authenticate(user=None)
        
        url = reverse('reports:report-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class TestQuickReportsView(TestCase):
    """Test QuickReportsView"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            slug='pro-plan',
            plan_type='pro',
            price_monthly=99.90,
            price_yearly=999.00
        )
        
        # Create user and company
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan
        )
        self.user.company = self.company
        self.user.save()
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    def test_get_quick_report_options(self):
        """Test getting quick report options"""
        url = reverse('reports:quick-reports')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('quick_reports', response.data)
        
        # Check we have the expected quick reports
        quick_reports = response.data['quick_reports']
        report_ids = [r['id'] for r in quick_reports]
        
        self.assertIn('current_month', report_ids)
        self.assertIn('last_month', report_ids)
        self.assertIn('quarterly', report_ids)
        self.assertIn('year_to_date', report_ids)
        self.assertIn('cash_flow_30', report_ids)
    
    @patch('apps.reports.tasks.generate_report_task.delay')
    def test_generate_current_month_report(self, mock_task):
        """Test generating current month report"""
        url = reverse('reports:quick-reports')
        data = {'report_id': 'current_month'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('report', response.data)
        
        # Check report was created correctly
        report = Report.objects.get(id=response.data['report']['id'])
        self.assertEqual(report.report_type, 'monthly_summary')
        self.assertEqual(report.period_start.month, timezone.now().month)
        self.assertEqual(report.period_start.day, 1)
        
        # Check task was queued
        mock_task.assert_called_once_with(report.id)
    
    @patch('apps.reports.tasks.generate_report_task.delay')
    def test_generate_last_month_report(self, mock_task):
        """Test generating last month report"""
        url = reverse('reports:quick-reports')
        data = {'report_id': 'last_month'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Check report was created correctly
        report = Report.objects.get(id=response.data['report']['id'])
        self.assertEqual(report.report_type, 'monthly_summary')
        
        # Verify it's for last month
        today = timezone.now().date()
        last_month = (today.replace(day=1) - timedelta(days=1))
        self.assertEqual(report.period_start.month, last_month.month)
        self.assertEqual(report.period_end.month, last_month.month)
    
    @patch('apps.reports.tasks.generate_report_task.delay')
    def test_generate_quarterly_report(self, mock_task):
        """Test generating quarterly report"""
        url = reverse('reports:quick-reports')
        data = {'report_id': 'quarterly'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check report was created correctly
        report = Report.objects.get(id=response.data['report']['id'])
        self.assertEqual(report.report_type, 'quarterly')
        
        # Should cover last 90 days
        days_diff = (report.period_end - report.period_start).days
        self.assertAlmostEqual(days_diff, 90, delta=1)
    
    @patch('apps.reports.tasks.generate_report_task.delay')
    def test_generate_year_to_date_report(self, mock_task):
        """Test generating year-to-date report"""
        url = reverse('reports:quick-reports')
        data = {'report_id': 'year_to_date'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check report was created correctly
        report = Report.objects.get(id=response.data['report']['id'])
        self.assertEqual(report.report_type, 'annual')
        self.assertEqual(report.period_start.month, 1)
        self.assertEqual(report.period_start.day, 1)
        self.assertEqual(report.period_start.year, timezone.now().year)
    
    @patch('apps.reports.tasks.generate_report_task.delay')
    def test_generate_cash_flow_report(self, mock_task):
        """Test generating cash flow projection report"""
        url = reverse('reports:quick-reports')
        data = {'report_id': 'cash_flow_30'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check report was created correctly
        report = Report.objects.get(id=response.data['report']['id'])
        self.assertEqual(report.report_type, 'cash_flow')
        
        # Should project 30 days into future
        days_diff = (report.period_end - report.period_start).days
        self.assertEqual(days_diff, 30)
        self.assertEqual(report.period_start, timezone.now().date())
    
    def test_invalid_report_id(self):
        """Test generating report with invalid ID"""
        url = reverse('reports:quick-reports')
        data = {'report_id': 'invalid_report'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid report_id')
    
    def test_missing_report_id(self):
        """Test generating report without report_id"""
        url = reverse('reports:quick-reports')
        data = {}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access is denied"""
        self.client.force_authenticate(user=None)
        
        url = reverse('reports:quick-reports')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)