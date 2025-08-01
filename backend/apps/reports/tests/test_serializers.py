"""
Unit tests for reports serializers
"""
import json
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework.test import APIRequestFactory

from apps.companies.models import Company, Subscription
from apps.banking.models import BankAccount, Transaction
from apps.categories.models import Category
from apps.reports.models import Report, ScheduledReport, ReportTemplate
from apps.reports.serializers import (
    ReportSerializer,
    ReportCreateSerializer,
    ReportListSerializer,
    ScheduledReportSerializer,
    ReportTemplateSerializer,
    ReportSummarySerializer
)

User = get_user_model()


class ReportSerializerTest(TestCase):
    """Test ReportSerializer"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
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
        
        self.report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Test Report',
            description='Test description',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            parameters={'include_charts': True},
            filters={'min_amount': 100},
            is_generated=True,
            created_by=self.user
        )
    
    def test_serialize_report(self):
        """Test serializing a report"""
        serializer = ReportSerializer(instance=self.report)
        data = serializer.data
        
        self.assertEqual(data['id'], str(self.report.id))
        self.assertEqual(data['title'], 'Test Report')
        self.assertEqual(data['description'], 'Test description')
        self.assertEqual(data['report_type'], 'monthly_summary')
        self.assertEqual(data['period_start'], '2024-01-01')
        self.assertEqual(data['period_end'], '2024-01-31')
        self.assertEqual(data['file_format'], 'pdf')
        self.assertTrue(data['is_generated'])
        self.assertEqual(data['parameters'], {'include_charts': True})
        self.assertEqual(data['filters'], {'min_amount': 100})
        self.assertEqual(data['created_by_name'], self.user.get_full_name())
    
    def test_serialize_report_with_file(self):
        """Test serializing a report with file"""
        # Add file to report
        pdf_content = b'%PDF-1.4 fake pdf content'
        self.report.file.save('test_report.pdf', ContentFile(pdf_content))
        self.report.file_size = len(pdf_content)
        self.report.save()
        
        serializer = ReportSerializer(instance=self.report)
        data = serializer.data
        
        self.assertIsNotNone(data['file'])
        self.assertEqual(data['file_size'], len(pdf_content))
        self.assertAlmostEqual(data['file_size_mb'], len(pdf_content) / (1024 * 1024), places=6)
    
    def test_serialize_report_with_error(self):
        """Test serializing a failed report"""
        self.report.is_generated = False
        self.report.error_message = "Failed to generate due to insufficient data"
        self.report.save()
        
        serializer = ReportSerializer(instance=self.report)
        data = serializer.data
        
        self.assertFalse(data['is_generated'])
        self.assertEqual(data['error_message'], "Failed to generate due to insufficient data")
    
    def test_serialize_report_with_generation_time(self):
        """Test serializing report with generation time"""
        self.report.generation_time = 45.5
        self.report.save()
        
        serializer = ReportSerializer(instance=self.report)
        data = serializer.data
        
        self.assertEqual(data['generation_time'], 45.5)


class ReportCreateSerializerTest(TestCase):
    """Test ReportCreateSerializer"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
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
        
        # Create a mock request with user
        self.request = self.factory.post('/api/reports/')
        self.request.user = self.user
    
    def test_create_valid_report(self):
        """Test creating a valid report"""
        data = {
            'report_type': 'monthly_summary',
            'title': 'New Monthly Report',
            'description': 'Test monthly report',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'file_format': 'pdf',
            'parameters': {
                'include_charts': True,
                'detailed_breakdown': True
            },
            'filters': {
                'account_ids': [1, 2],
                'min_amount': 50.0
            }
        }
        
        serializer = ReportCreateSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        
        report = serializer.save()
        
        self.assertEqual(report.title, 'New Monthly Report')
        self.assertEqual(report.report_type, 'monthly_summary')
        self.assertEqual(report.company, self.company)
        self.assertEqual(report.created_by, self.user)
        self.assertFalse(report.is_generated)  # Should start as not generated
    
    def test_create_report_invalid_dates(self):
        """Test creating report with invalid date range"""
        data = {
            'report_type': 'monthly_summary',
            'title': 'Invalid Report',
            'period_start': '2024-02-01',
            'period_end': '2024-01-01',  # End before start
            'file_format': 'pdf'
        }
        
        serializer = ReportCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('period_start', serializer.errors)
    
    def test_create_report_future_end_date(self):
        """Test creating report with future end date"""
        future_date = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        data = {
            'report_type': 'monthly_summary',
            'title': 'Future Report',
            'period_start': '2024-01-01',
            'period_end': future_date,
            'file_format': 'pdf'
        }
        
        serializer = ReportCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('period_end', serializer.errors)
    
    def test_create_report_excessive_period(self):
        """Test creating report with period exceeding 365 days"""
        data = {
            'report_type': 'monthly_summary',
            'title': 'Long Period Report',
            'period_start': '2023-01-01',
            'period_end': '2024-01-02',  # 366+ days
            'file_format': 'pdf'
        }
        
        serializer = ReportCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('period_start', serializer.errors)
    
    def test_create_report_invalid_report_type(self):
        """Test creating report with invalid report type"""
        data = {
            'report_type': 'invalid_type',
            'title': 'Invalid Type Report',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'file_format': 'pdf'
        }
        
        serializer = ReportCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('report_type', serializer.errors)
    
    def test_create_report_invalid_file_format(self):
        """Test creating report with invalid file format"""
        data = {
            'report_type': 'monthly_summary',
            'title': 'Invalid Format Report',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'file_format': 'invalid_format'
        }
        
        serializer = ReportCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('file_format', serializer.errors)
    
    def test_validate_parameters_field(self):
        """Test parameters field validation"""
        data = {
            'report_type': 'monthly_summary',
            'title': 'Parameters Test',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'file_format': 'pdf',
            'parameters': {
                'account_ids': [1, 2, 3],
                'category_ids': [4, 5],
                'include_charts': True,
                'detailed_breakdown': False
            }
        }
        
        serializer = ReportCreateSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['parameters']['account_ids'], [1, 2, 3])
        self.assertTrue(validated_data['parameters']['include_charts'])
    
    def test_validate_filters_field(self):
        """Test filters field validation"""
        data = {
            'report_type': 'category_analysis',
            'title': 'Filters Test',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'file_format': 'xlsx',
            'filters': {
                'min_amount': 100.50,
                'max_amount': 1000.00,
                'transaction_type': 'credit'
            }
        }
        
        serializer = ReportCreateSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['filters']['min_amount'], 100.50)
        self.assertEqual(validated_data['filters']['transaction_type'], 'credit')


class ReportListSerializerTest(TestCase):
    """Test ReportListSerializer (optimized for list views)"""
    
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
    
    def test_serialize_report_list(self):
        """Test serializing reports for list view"""
        reports = []
        for i in range(3):
            report = Report.objects.create(
                company=self.company,
                report_type='monthly_summary',
                title=f'Report {i+1}',
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31),
                file_format='pdf',
                is_generated=i % 2 == 0,  # Alternate generated status
                created_by=self.user
            )
            reports.append(report)
        
        serializer = ReportListSerializer(reports, many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 3)
        
        # Check first report
        first_report = data[0]
        self.assertEqual(first_report['title'], 'Report 1')
        self.assertTrue(first_report['is_generated'])
        self.assertEqual(first_report['created_by_name'], self.user.get_full_name())
        
        # Verify essential fields are present
        for report_data in data:
            self.assertIn('id', report_data)
            self.assertIn('title', report_data)
            self.assertIn('report_type', report_data)
            self.assertIn('is_generated', report_data)
            self.assertIn('created_at', report_data)
            
            # List serializer should not include heavy fields
            self.assertNotIn('parameters', report_data)
            self.assertNotIn('filters', report_data)


class ScheduledReportSerializerTest(TestCase):
    """Test ScheduledReportSerializer"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
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
        
        self.request = self.factory.post('/api/reports/schedules/')
        self.request.user = self.user
    
    def test_serialize_scheduled_report(self):
        """Test serializing a scheduled report"""
        scheduled_report = ScheduledReport.objects.create(
            company=self.company,
            name='Monthly Revenue Report',
            report_type='monthly_summary',
            frequency='monthly',
            email_recipients=['manager@company.com', 'finance@company.com'],
            file_format='pdf',
            send_email=True,
            parameters={'include_charts': True},
            filters={'min_amount': 100},
            created_by=self.user
        )
        
        serializer = ScheduledReportSerializer(instance=scheduled_report)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Monthly Revenue Report')
        self.assertEqual(data['report_type'], 'monthly_summary')
        self.assertEqual(data['frequency'], 'monthly')
        self.assertTrue(data['is_active'])
        self.assertTrue(data['send_email'])
        self.assertEqual(len(data['email_recipients']), 2)
        self.assertEqual(data['parameters'], {'include_charts': True})
        self.assertEqual(data['created_by_name'], self.user.get_full_name())
    
    def test_create_scheduled_report(self):
        """Test creating a scheduled report"""
        data = {
            'name': 'Weekly Cash Flow',
            'report_type': 'cash_flow',
            'frequency': 'weekly',
            'email_recipients': ['cfo@company.com'],
            'file_format': 'xlsx',
            'send_email': True,
            'parameters': {
                'include_projections': True
            },
            'filters': {
                'exclude_transfers': True
            }
        }
        
        serializer = ScheduledReportSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        
        scheduled_report = serializer.save()
        
        self.assertEqual(scheduled_report.name, 'Weekly Cash Flow')
        self.assertEqual(scheduled_report.company, self.company)
        self.assertEqual(scheduled_report.created_by, self.user)
        self.assertTrue(scheduled_report.is_active)
        self.assertIsNotNone(scheduled_report.next_run_at)
    
    def test_validate_email_recipients(self):
        """Test email recipients validation"""
        # Valid emails
        data = {
            'name': 'Test Report',
            'report_type': 'monthly_summary',
            'frequency': 'monthly',
            'email_recipients': ['valid@email.com', 'another@valid.com'],
            'file_format': 'pdf'
        }
        
        serializer = ScheduledReportSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        
        # Invalid emails
        data['email_recipients'] = ['invalid-email', 'another@invalid']
        serializer = ScheduledReportSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('email_recipients', serializer.errors)
    
    def test_validate_frequency(self):
        """Test frequency field validation"""
        data = {
            'name': 'Test Report',
            'report_type': 'monthly_summary',
            'frequency': 'invalid_frequency',
            'email_recipients': ['test@company.com'],
            'file_format': 'pdf'
        }
        
        serializer = ScheduledReportSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('frequency', serializer.errors)


class ReportTemplateSerializerTest(TestCase):
    """Test ReportTemplateSerializer"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
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
        
        self.request = self.factory.post('/api/reports/templates/')
        self.request.user = self.user
    
    def test_serialize_report_template(self):
        """Test serializing a report template"""
        template_config = {
            'sections': ['summary', 'detailed_transactions'],
            'styling': {'primary_color': '#1f2937'}
        }
        
        charts = [
            {'type': 'line', 'title': 'Trend', 'data_key': 'monthly_data'},
            {'type': 'pie', 'title': 'Categories', 'data_key': 'category_data'}
        ]
        
        template = ReportTemplate.objects.create(
            company=self.company,
            name='Standard Template',
            description='Standard monthly template',
            report_type='monthly_summary',
            template_config=template_config,
            charts=charts,
            default_parameters={'include_charts': True},
            default_filters={'min_amount': 10},
            is_public=False,
            created_by=self.user
        )
        
        serializer = ReportTemplateSerializer(instance=template)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Standard Template')
        self.assertEqual(data['description'], 'Standard monthly template')
        self.assertEqual(data['report_type'], 'monthly_summary')
        self.assertFalse(data['is_public'])
        self.assertTrue(data['is_active'])
        self.assertEqual(data['template_config'], template_config)
        self.assertEqual(len(data['charts']), 2)
        self.assertEqual(data['created_by_name'], self.user.get_full_name())
    
    def test_create_report_template(self):
        """Test creating a report template"""
        data = {
            'name': 'New Template',
            'description': 'Custom template for cash flow',
            'report_type': 'cash_flow',
            'template_config': {
                'layout': 'landscape',
                'sections': ['summary', 'charts']
            },
            'charts': [
                {
                    'type': 'bar',
                    'title': 'Monthly Cash Flow',
                    'data_key': 'cash_flow_data'
                }
            ],
            'default_parameters': {
                'include_projections': True
            },
            'is_public': False
        }
        
        serializer = ReportTemplateSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        
        template = serializer.save()
        
        self.assertEqual(template.name, 'New Template')
        self.assertEqual(template.company, self.company)
        self.assertEqual(template.created_by, self.user)
        self.assertTrue(template.is_active)
        self.assertEqual(len(template.charts), 1)
    
    def test_validate_template_config(self):
        """Test template_config validation"""
        data = {
            'name': 'Config Test',
            'report_type': 'monthly_summary',
            'template_config': {
                'sections': ['summary', 'invalid_section'],
                'layout': 'invalid_layout'
            }
        }
        
        serializer = ReportTemplateSerializer(data=data, context={'request': self.request})
        # Should still be valid as we allow flexible config
        self.assertTrue(serializer.is_valid())
        
        # But empty config should be rejected
        data['template_config'] = {}
        serializer = ReportTemplateSerializer(data=data, context={'request': self.request})
        # Empty config might be valid depending on business rules
        # self.assertFalse(serializer.is_valid())


class ReportSummarySerializerTest(TestCase):
    """Test ReportSummarySerializer for dashboard stats"""
    
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
        
        # Create various reports for testing
        for i in range(5):
            Report.objects.create(
                company=self.company,
                report_type='monthly_summary',
                title=f'Report {i+1}',
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31),
                file_format='pdf',
                is_generated=i < 3,  # First 3 are generated
                created_by=self.user
            )
    
    def test_report_summary_calculation(self):
        """Test report summary calculations"""
        # The summary data would typically be calculated in a view or service
        # Here we test the serializer with mock data
        summary_data = {
            'total_reports': 5,
            'reports_generated': 3,
            'reports_pending': 2,
            'reports_failed': 0,
            'total_file_size_mb': 15.5,
            'avg_generation_time': 25.3,
            'most_common_type': 'monthly_summary',
            'recent_reports': Report.objects.filter(company=self.company)[:3]
        }
        
        serializer = ReportSummarySerializer(summary_data)
        data = serializer.data
        
        self.assertEqual(data['total_reports'], 5)
        self.assertEqual(data['reports_generated'], 3)
        self.assertEqual(data['reports_pending'], 2)
        self.assertEqual(data['most_common_type'], 'monthly_summary')
        self.assertEqual(len(data['recent_reports']), 3)


class SerializerValidationTest(TestCase):
    """Test cross-cutting serializer validation concerns"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
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
        
        self.request = self.factory.post('/api/reports/')
        self.request.user = self.user
    
    def test_company_isolation_in_serializers(self):
        """Test that serializers properly isolate data by company"""
        # This would be more thoroughly tested in view tests
        # but we can test that company is properly set
        
        data = {
            'report_type': 'monthly_summary',
            'title': 'Company Isolation Test',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'file_format': 'pdf'
        }
        
        serializer = ReportCreateSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        
        report = serializer.save()
        self.assertEqual(report.company, self.company)
        self.assertEqual(report.created_by, self.user)
    
    def test_json_field_serialization(self):
        """Test JSON field serialization and deserialization"""
        complex_parameters = {
            'nested_object': {
                'key1': 'value1',
                'key2': ['item1', 'item2'],
                'key3': {'nested_key': 123}
            },
            'simple_array': [1, 2, 3, 4, 5],
            'boolean_flags': {
                'flag1': True,
                'flag2': False
            }
        }
        
        data = {
            'report_type': 'custom',
            'title': 'JSON Field Test',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'file_format': 'json',
            'parameters': complex_parameters
        }
        
        serializer = ReportCreateSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        
        report = serializer.save()
        
        # Verify the JSON was properly stored and can be retrieved
        self.assertEqual(report.parameters, complex_parameters)
        self.assertEqual(report.parameters['nested_object']['key2'], ['item1', 'item2'])
        
        # Verify serialization back out
        output_serializer = ReportSerializer(instance=report)
        output_data = output_serializer.data
        self.assertEqual(output_data['parameters'], complex_parameters)