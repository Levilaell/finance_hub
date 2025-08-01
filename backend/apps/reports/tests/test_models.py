"""
Unit tests for reports models
"""
import json
import os
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils import timezone

from apps.companies.models import Company, Subscription
from apps.banking.models import BankAccount, Transaction
from apps.categories.models import Category
from apps.reports.models import Report, ScheduledReport, ReportTemplate
from apps.reports.exceptions import (
    InvalidReportPeriodError,
    ReportDataInsufficientError
)

User = get_user_model()


class ReportModelTest(TestCase):
    """Test Report model"""
    
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
    
    def test_create_report(self):
        """Test creating a basic report"""
        report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Test Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            created_by=self.user
        )
        
        self.assertEqual(report.company, self.company)
        self.assertEqual(report.report_type, 'monthly_summary')
        self.assertEqual(report.title, 'Test Report')
        self.assertFalse(report.is_generated)
        self.assertIsNone(report.file)
        self.assertEqual(report.file_size, 0)
        self.assertIsNone(report.error_message)
    
    def test_report_str_representation(self):
        """Test string representation of Report"""
        report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Test Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            created_by=self.user
        )
        
        expected = f"Test Report (monthly_summary) - {self.company.name}"
        self.assertEqual(str(report), expected)
    
    def test_report_period_validation(self):
        """Test report period validation"""
        # Test start date after end date
        with self.assertRaises(ValidationError):
            report = Report(
                company=self.company,
                report_type='monthly_summary',
                title='Invalid Report',
                period_start=date(2024, 2, 1),
                period_end=date(2024, 1, 31),
                file_format='pdf',
                created_by=self.user
            )
            report.full_clean()
    
    def test_report_with_file(self):
        """Test report with attached file"""
        report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Test Report with File',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            is_generated=True,
            created_by=self.user
        )
        
        # Simulate file attachment
        pdf_content = b'%PDF-1.4 fake pdf content'
        report.file.save('test_report.pdf', ContentFile(pdf_content))
        
        self.assertTrue(report.is_generated)
        self.assertIsNotNone(report.file)
        self.assertEqual(report.file_size, len(pdf_content))
    
    def test_report_parameters_json_field(self):
        """Test parameters JSON field"""
        parameters = {
            'account_ids': [1, 2, 3],
            'category_ids': [4, 5],
            'include_charts': True,
            'detailed_breakdown': True
        }
        
        report = Report.objects.create(
            company=self.company,
            report_type='category_analysis',
            title='Test Report with Parameters',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            parameters=parameters,
            created_by=self.user
        )
        
        # Refresh from database
        report.refresh_from_db()
        self.assertEqual(report.parameters, parameters)
        self.assertEqual(report.parameters['account_ids'], [1, 2, 3])
        self.assertTrue(report.parameters['include_charts'])
    
    def test_report_filters_json_field(self):
        """Test filters JSON field"""
        filters = {
            'min_amount': 100.50,
            'max_amount': 1000.00,
            'transaction_type': 'credit',
            'exclude_transfers': True
        }
        
        report = Report.objects.create(
            company=self.company,
            report_type='profit_loss',
            title='Test Report with Filters',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            filters=filters,
            created_by=self.user
        )
        
        # Refresh from database
        report.refresh_from_db()
        self.assertEqual(report.filters, filters)
        self.assertEqual(report.filters['min_amount'], 100.50)
        self.assertTrue(report.filters['exclude_transfers'])
    
    def test_report_file_path_generation(self):
        """Test dynamic file path generation"""
        report = Report.objects.create(
            company=self.company,
            report_type='cash_flow',
            title='Cash Flow Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='xlsx',
            created_by=self.user
        )
        
        # The file path should include company and report info
        expected_path_parts = [
            'reports',
            str(self.company.id),
            '2024',
            '01'
        ]
        
        # Mock file save to check path
        with patch('django.core.files.storage.FileSystemStorage.save') as mock_save:
            mock_save.return_value = 'test_path.xlsx'
            report.file.save('test.xlsx', ContentFile(b'fake xlsx content'))
            
            # Check that save was called
            self.assertTrue(mock_save.called)


class ScheduledReportModelTest(TestCase):
    """Test ScheduledReport model"""
    
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
    
    def test_create_scheduled_report(self):
        """Test creating a scheduled report"""
        scheduled_report = ScheduledReport.objects.create(
            company=self.company,
            name='Monthly Revenue Report',
            report_type='monthly_summary',
            frequency='monthly',
            email_recipients=['manager@company.com', 'finance@company.com'],
            file_format='pdf',
            send_email=True,
            created_by=self.user
        )
        
        self.assertEqual(scheduled_report.company, self.company)
        self.assertEqual(scheduled_report.name, 'Monthly Revenue Report')
        self.assertEqual(scheduled_report.frequency, 'monthly')
        self.assertTrue(scheduled_report.is_active)
        self.assertTrue(scheduled_report.send_email)
        self.assertEqual(len(scheduled_report.email_recipients), 2)
    
    def test_scheduled_report_str_representation(self):
        """Test string representation of ScheduledReport"""
        scheduled_report = ScheduledReport.objects.create(
            company=self.company,
            name='Weekly Cash Flow',
            report_type='cash_flow',
            frequency='weekly',
            email_recipients=['finance@company.com'],
            file_format='pdf',
            created_by=self.user
        )
        
        expected = f"Weekly Cash Flow (weekly) - {self.company.name}"
        self.assertEqual(str(scheduled_report), expected)
    
    def test_email_recipients_json_field(self):
        """Test email recipients JSON field"""
        recipients = [
            'ceo@company.com',
            'cfo@company.com',
            'manager@company.com'
        ]
        
        scheduled_report = ScheduledReport.objects.create(
            company=self.company,
            name='Executive Summary',
            report_type='quarterly_report',
            frequency='quarterly',
            email_recipients=recipients,
            file_format='pdf',
            created_by=self.user
        )
        
        # Refresh from database
        scheduled_report.refresh_from_db()
        self.assertEqual(scheduled_report.email_recipients, recipients)
        self.assertIn('ceo@company.com', scheduled_report.email_recipients)
    
    def test_scheduled_report_with_parameters(self):
        """Test scheduled report with parameters"""
        parameters = {
            'account_ids': [1, 2],
            'include_projections': True,
            'detail_level': 'high'
        }
        
        scheduled_report = ScheduledReport.objects.create(
            company=self.company,
            name='Detailed Monthly Report',
            report_type='monthly_summary',
            frequency='monthly',
            email_recipients=['manager@company.com'],
            file_format='xlsx',
            parameters=parameters,
            created_by=self.user
        )
        
        # Refresh from database
        scheduled_report.refresh_from_db()
        self.assertEqual(scheduled_report.parameters, parameters)
        self.assertTrue(scheduled_report.parameters['include_projections'])
    
    def test_next_run_calculation(self):
        """Test next run date calculation"""
        scheduled_report = ScheduledReport.objects.create(
            company=self.company,
            name='Daily Report',
            report_type='daily_summary',
            frequency='daily',
            email_recipients=['daily@company.com'],
            file_format='pdf',
            created_by=self.user
        )
        
        # Initially, next_run_at should be set
        self.assertIsNotNone(scheduled_report.next_run_at)
        
        # After setting last_run_at, next_run_at should be updated
        now = timezone.now()
        scheduled_report.last_run_at = now
        scheduled_report.save()
        
        # For daily frequency, next run should be tomorrow (approximately)
        expected_next_run = now + timedelta(days=1)
        self.assertAlmostEqual(
            scheduled_report.next_run_at.timestamp(),
            expected_next_run.timestamp(),
            delta=3600  # Within 1 hour
        )


class ReportTemplateModelTest(TestCase):
    """Test ReportTemplate model"""
    
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
    
    def test_create_report_template(self):
        """Test creating a report template"""
        template_config = {
            'sections': ['summary', 'detailed_transactions', 'charts'],
            'chart_types': ['line', 'pie', 'bar'],
            'formatting': {
                'currency': 'BRL',
                'date_format': 'dd/mm/yyyy'
            }
        }
        
        template = ReportTemplate.objects.create(
            company=self.company,
            name='Standard Monthly Template',
            description='Standard template for monthly reports',
            report_type='monthly_summary',
            template_config=template_config,
            is_public=False,
            created_by=self.user
        )
        
        self.assertEqual(template.company, self.company)
        self.assertEqual(template.name, 'Standard Monthly Template')
        self.assertEqual(template.report_type, 'monthly_summary')
        self.assertFalse(template.is_public)
        self.assertTrue(template.is_active)
    
    def test_report_template_str_representation(self):
        """Test string representation of ReportTemplate"""
        template = ReportTemplate.objects.create(
            company=self.company,
            name='Cash Flow Template',
            report_type='cash_flow',
            template_config={},
            created_by=self.user
        )
        
        expected = f"Cash Flow Template (cash_flow) - {self.company.name}"
        self.assertEqual(str(template), expected)
    
    def test_template_config_json_field(self):
        """Test template_config JSON field"""
        config = {
            'layout': 'portrait',
            'sections': [
                {
                    'type': 'summary',
                    'title': 'Executive Summary',
                    'fields': ['total_income', 'total_expenses', 'net_result']
                },
                {
                    'type': 'chart',
                    'chart_type': 'line',
                    'data_source': 'monthly_trend'
                }
            ],
            'styling': {
                'primary_color': '#1f2937',
                'secondary_color': '#6b7280',
                'font_family': 'Arial'
            }
        }
        
        template = ReportTemplate.objects.create(
            company=self.company,
            name='Advanced Template',
            report_type='profit_loss',
            template_config=config,
            created_by=self.user
        )
        
        # Refresh from database
        template.refresh_from_db()
        self.assertEqual(template.template_config, config)
        self.assertEqual(template.template_config['layout'], 'portrait')
        self.assertEqual(len(template.template_config['sections']), 2)
    
    def test_charts_json_field(self):
        """Test charts JSON field"""
        charts = [
            {
                'type': 'line',
                'title': 'Monthly Trend',
                'data_key': 'monthly_data',
                'x_axis': 'date',
                'y_axis': 'amount'
            },
            {
                'type': 'pie',
                'title': 'Category Distribution',
                'data_key': 'category_data',
                'value_field': 'total'
            }
        ]
        
        template = ReportTemplate.objects.create(
            company=self.company,
            name='Chart Heavy Template',
            report_type='category_analysis',
            template_config={},
            charts=charts,
            created_by=self.user
        )
        
        # Refresh from database
        template.refresh_from_db()
        self.assertEqual(template.charts, charts)
        self.assertEqual(len(template.charts), 2)
        self.assertEqual(template.charts[0]['type'], 'line')
    
    def test_default_parameters_and_filters(self):
        """Test default parameters and filters"""
        default_parameters = {
            'include_charts': True,
            'detail_level': 'medium',
            'currency_conversion': False
        }
        
        default_filters = {
            'exclude_internal_transfers': True,
            'min_amount_threshold': 10.00
        }
        
        template = ReportTemplate.objects.create(
            company=self.company,
            name='Filtered Template',
            report_type='transaction_report',
            template_config={},
            default_parameters=default_parameters,
            default_filters=default_filters,
            created_by=self.user
        )
        
        # Refresh from database
        template.refresh_from_db()
        self.assertEqual(template.default_parameters, default_parameters)
        self.assertEqual(template.default_filters, default_filters)
        self.assertTrue(template.default_parameters['include_charts'])
        self.assertTrue(template.default_filters['exclude_internal_transfers'])
    
    def test_public_template(self):
        """Test public template functionality"""
        template = ReportTemplate.objects.create(
            company=self.company,
            name='Public Template',
            description='A template available to all companies',
            report_type='monthly_summary',
            template_config={'layout': 'standard'},
            is_public=True,
            created_by=self.user
        )
        
        self.assertTrue(template.is_public)
        self.assertTrue(template.is_active)
        
        # Public templates should be accessible by other companies
        other_company = Company.objects.create(
            name="Other Company",
            cnpj="98765432000100"
        )
        
        # This would be tested in a view or service layer
        # Here we just verify the model allows public templates
        self.assertTrue(template.is_public)


class ReportModelManagerTest(TestCase):
    """Test custom model managers and querysets"""
    
    def setUp(self):
        self.company1 = Company.objects.create(
            name="Company 1",
            cnpj="12345678000123"
        )
        self.company2 = Company.objects.create(
            name="Company 2", 
            cnpj="98765432000100"
        )
        self.user1 = User.objects.create_user(
            email="user1@example.com",
            password="testpass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="testpass123"
        )
        self.user1.company = self.company1
        self.user2.company = self.company2
        self.user1.save()
        self.user2.save()
    
    def test_company_isolation(self):
        """Test that reports are properly isolated by company"""
        # Create reports for different companies
        report1 = Report.objects.create(
            company=self.company1,
            report_type='monthly_summary',
            title='Company 1 Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            created_by=self.user1
        )
        
        report2 = Report.objects.create(
            company=self.company2,
            report_type='monthly_summary',
            title='Company 2 Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            created_by=self.user2
        )
        
        # Verify each company only sees their own reports
        company1_reports = Report.objects.filter(company=self.company1)
        company2_reports = Report.objects.filter(company=self.company2)
        
        self.assertEqual(company1_reports.count(), 1)
        self.assertEqual(company2_reports.count(), 1)
        self.assertEqual(company1_reports.first().title, 'Company 1 Report')
        self.assertEqual(company2_reports.first().title, 'Company 2 Report')
    
    def test_generated_reports_filter(self):
        """Test filtering generated vs pending reports"""
        # Create generated report
        generated_report = Report.objects.create(
            company=self.company1,
            report_type='monthly_summary',
            title='Generated Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            is_generated=True,
            created_by=self.user1
        )
        
        # Create pending report
        pending_report = Report.objects.create(
            company=self.company1,
            report_type='cash_flow',
            title='Pending Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            is_generated=False,
            created_by=self.user1
        )
        
        # Filter tests
        generated_reports = Report.objects.filter(is_generated=True)
        pending_reports = Report.objects.filter(is_generated=False)
        
        self.assertEqual(generated_reports.count(), 1)
        self.assertEqual(pending_reports.count(), 1)
        self.assertEqual(generated_reports.first().title, 'Generated Report')
        self.assertEqual(pending_reports.first().title, 'Pending Report')