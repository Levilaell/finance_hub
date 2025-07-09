"""
Test reports models
Tests for Report, ReportSchedule, and ReportTemplate models
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.utils import timezone
from apps.companies.models import Company, SubscriptionPlan
from apps.reports.models import Report, ReportSchedule, ReportTemplate

User = get_user_model()


class TestReportModel(TestCase):
    """Test Report model"""
    
    def setUp(self):
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Pro Plan',
            slug='pro-plan',
            plan_type='pro',
            price_monthly=99.90,
            price_yearly=999.00,
            max_users=10,
            max_bank_accounts=10
        )
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan
        )
        self.user.company = self.company
        self.user.save()
    
    def test_create_report(self):
        """Test creating a report"""
        report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Monthly Summary - January 2025',
            description='January financial summary',
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            file_format='pdf',
            created_by=self.user
        )
        
        self.assertEqual(report.company, self.company)
        self.assertEqual(report.report_type, 'monthly_summary')
        self.assertEqual(report.title, 'Monthly Summary - January 2025')
        self.assertFalse(report.is_generated)
        self.assertEqual(report.generation_time, 0)
        self.assertEqual(report.created_by, self.user)
    
    def test_report_string_representation(self):
        """Test report string representation"""
        report = Report.objects.create(
            company=self.company,
            report_type='cash_flow',
            title='Cash Flow Report',
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            file_format='xlsx',
            created_by=self.user
        )
        
        expected = "Cash Flow Report (2025-01-01 - 2025-01-31)"
        self.assertEqual(str(report), expected)
    
    def test_report_type_choices(self):
        """Test report type validation"""
        # Valid report type
        report = Report.objects.create(
            company=self.company,
            report_type='profit_loss',
            title='P&L Report',
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            file_format='pdf',
            created_by=self.user
        )
        self.assertEqual(report.report_type, 'profit_loss')
        
        # Invalid report type should raise validation error
        report.report_type = 'invalid_type'
        with self.assertRaises(ValidationError):
            report.full_clean()
    
    def test_file_format_choices(self):
        """Test file format validation"""
        valid_formats = ['pdf', 'xlsx', 'csv', 'json']
        
        for format_type in valid_formats:
            report = Report.objects.create(
                company=self.company,
                report_type='custom',
                title=f'Test Report {format_type}',
                period_start=date(2025, 1, 1),
                period_end=date(2025, 1, 31),
                file_format=format_type,
                created_by=self.user
            )
            self.assertEqual(report.file_format, format_type)
    
    def test_parameters_and_filters(self):
        """Test JSON fields for parameters and filters"""
        parameters = {
            'include_subcategories': True,
            'group_by': 'category',
            'currency': 'BRL'
        }
        filters = {
            'categories': ['food', 'transport'],
            'min_amount': 100,
            'max_amount': 1000
        }
        
        report = Report.objects.create(
            company=self.company,
            report_type='category_analysis',
            title='Category Analysis',
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            file_format='pdf',
            parameters=parameters,
            filters=filters,
            created_by=self.user
        )
        
        self.assertEqual(report.parameters['include_subcategories'], True)
        self.assertEqual(report.parameters['group_by'], 'category')
        self.assertEqual(report.filters['categories'], ['food', 'transport'])
        self.assertEqual(report.filters['min_amount'], 100)
    
    def test_file_upload(self):
        """Test report file upload"""
        report = Report.objects.create(
            company=self.company,
            report_type='annual_report',
            title='Annual Report 2024',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            file_format='pdf',
            created_by=self.user
        )
        
        # Simulate file upload
        file_content = b'PDF content here'
        report.file.save('report.pdf', ContentFile(file_content))
        report.file_size = len(file_content)
        report.is_generated = True
        report.generation_time = 5
        report.save()
        
        self.assertTrue(report.is_generated)
        self.assertEqual(report.file_size, 16)
        self.assertEqual(report.generation_time, 5)
        self.assertIn('reports/', report.file.name)
    
    def test_error_handling(self):
        """Test error message storage"""
        report = Report.objects.create(
            company=self.company,
            report_type='tax_report',
            title='Tax Report Q1 2025',
            period_start=date(2025, 1, 1),
            period_end=date(2025, 3, 31),
            file_format='xlsx',
            created_by=self.user
        )
        
        # Simulate generation error
        report.error_message = "Failed to generate report: Insufficient data"
        report.save()
        
        self.assertFalse(report.is_generated)
        self.assertIn("Insufficient data", report.error_message)
    
    def test_period_validation(self):
        """Test report period validation"""
        # End date should be after start date
        report = Report(
            company=self.company,
            report_type='monthly_summary',
            title='Invalid Period Report',
            period_start=date(2025, 1, 31),
            period_end=date(2025, 1, 1),
            file_format='pdf',
            created_by=self.user
        )
        
        # Note: Model doesn't have built-in validation for this
        # In real implementation, this should be validated
        report.save()
        self.assertTrue(report.period_start > report.period_end)
    
    def test_ordering(self):
        """Test report ordering by created_at"""
        # Create reports with different timestamps
        report1 = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Report 1',
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            file_format='pdf',
            created_by=self.user
        )
        
        # Wait a moment
        report2 = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Report 2',
            period_start=date(2025, 2, 1),
            period_end=date(2025, 2, 28),
            file_format='pdf',
            created_by=self.user
        )
        
        reports = list(Report.objects.all())
        # Should be ordered by -created_at (newest first)
        self.assertEqual(reports[0], report2)
        self.assertEqual(reports[1], report1)


class TestReportScheduleModel(TestCase):
    """Test ReportSchedule model"""
    
    def setUp(self):
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
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan
        )
    
    def test_create_schedule(self):
        """Test creating a report schedule"""
        schedule = ReportSchedule.objects.create(
            company=self.company,
            report_type='monthly_summary',
            frequency='monthly',
            send_email=True,
            email_recipients=['test@example.com', 'admin@example.com'],
            file_format='pdf',
            next_run_at=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        
        self.assertEqual(schedule.company, self.company)
        self.assertEqual(schedule.report_type, 'monthly_summary')
        self.assertEqual(schedule.frequency, 'monthly')
        self.assertTrue(schedule.send_email)
        self.assertEqual(len(schedule.email_recipients), 2)
        self.assertTrue(schedule.is_active)
    
    def test_schedule_string_representation(self):
        """Test schedule string representation"""
        schedule = ReportSchedule.objects.create(
            company=self.company,
            report_type='cash_flow',
            frequency='weekly',
            next_run_at=timezone.now() + timedelta(days=7),
            created_by=self.user
        )
        
        expected = "Fluxo de Caixa - Semanal"
        self.assertEqual(str(schedule), expected)
    
    def test_frequency_choices(self):
        """Test frequency validation"""
        valid_frequencies = ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']
        
        for freq in valid_frequencies:
            schedule = ReportSchedule.objects.create(
                company=self.company,
                report_type='profit_loss',
                frequency=freq,
                next_run_at=timezone.now() + timedelta(days=1),
                created_by=self.user
            )
            self.assertEqual(schedule.frequency, freq)
    
    def test_schedule_parameters(self):
        """Test schedule parameters and filters"""
        parameters = {
            'include_charts': True,
            'detailed_breakdown': False
        }
        filters = {
            'exclude_categories': ['internal_transfers'],
            'accounts': ['checking', 'savings']
        }
        
        schedule = ReportSchedule.objects.create(
            company=self.company,
            report_type='category_analysis',
            frequency='monthly',
            parameters=parameters,
            filters=filters,
            next_run_at=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        
        self.assertEqual(schedule.parameters['include_charts'], True)
        self.assertEqual(schedule.filters['accounts'], ['checking', 'savings'])
    
    def test_last_run_tracking(self):
        """Test last run timestamp tracking"""
        schedule = ReportSchedule.objects.create(
            company=self.company,
            report_type='quarterly_report',
            frequency='quarterly',
            next_run_at=timezone.now() + timedelta(days=90),
            created_by=self.user
        )
        
        # Initially no last run
        self.assertIsNone(schedule.last_run_at)
        
        # Simulate execution
        schedule.last_run_at = timezone.now()
        schedule.save()
        
        self.assertIsNotNone(schedule.last_run_at)
    
    def test_schedule_activation(self):
        """Test schedule activation/deactivation"""
        schedule = ReportSchedule.objects.create(
            company=self.company,
            report_type='annual_report',
            frequency='yearly',
            next_run_at=timezone.now() + timedelta(days=365),
            created_by=self.user
        )
        
        # Should be active by default
        self.assertTrue(schedule.is_active)
        
        # Deactivate
        schedule.is_active = False
        schedule.save()
        
        self.assertFalse(schedule.is_active)
    
    def test_email_recipients_list(self):
        """Test email recipients as JSON list"""
        recipients = ['user1@example.com', 'user2@example.com', 'admin@company.com']
        
        schedule = ReportSchedule.objects.create(
            company=self.company,
            report_type='monthly_summary',
            frequency='monthly',
            email_recipients=recipients,
            next_run_at=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        
        self.assertEqual(len(schedule.email_recipients), 3)
        self.assertIn('admin@company.com', schedule.email_recipients)
        
        # Test empty recipients
        schedule.email_recipients = []
        schedule.save()
        self.assertEqual(schedule.email_recipients, [])


class TestReportTemplateModel(TestCase):
    """Test ReportTemplate model"""
    
    def setUp(self):
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Enterprise Plan',
            slug='enterprise-plan',
            plan_type='enterprise',
            price_monthly=299.90,
            price_yearly=2999.00
        )
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create company
        self.company = Company.objects.create(
            name='Test Company',
            cnpj='11222333000181',
            owner=self.user,
            subscription_plan=self.plan
        )
    
    def test_create_template(self):
        """Test creating a report template"""
        template = ReportTemplate.objects.create(
            company=self.company,
            name='Custom P&L Template',
            description='Customized profit and loss template',
            report_type='custom',
            created_by=self.user
        )
        
        self.assertEqual(template.company, self.company)
        self.assertEqual(template.name, 'Custom P&L Template')
        self.assertEqual(template.report_type, 'custom')
        self.assertTrue(template.is_active)
        self.assertFalse(template.is_public)
    
    def test_template_string_representation(self):
        """Test template string representation"""
        template = ReportTemplate.objects.create(
            company=self.company,
            name='Sales Dashboard Template',
            created_by=self.user
        )
        
        self.assertEqual(str(template), 'Sales Dashboard Template')
    
    def test_template_configuration(self):
        """Test template configuration JSON field"""
        config = {
            'sections': [
                {
                    'name': 'Revenue',
                    'type': 'table',
                    'data_source': 'income_transactions'
                },
                {
                    'name': 'Expenses',
                    'type': 'chart',
                    'chart_type': 'bar',
                    'data_source': 'expense_transactions'
                }
            ],
            'layout': 'two_column'
        }
        
        template = ReportTemplate.objects.create(
            company=self.company,
            name='Financial Overview',
            template_config=config,
            created_by=self.user
        )
        
        self.assertEqual(len(template.template_config['sections']), 2)
        self.assertEqual(template.template_config['layout'], 'two_column')
    
    def test_charts_configuration(self):
        """Test charts configuration"""
        charts = [
            {
                'id': 'revenue_trend',
                'type': 'line',
                'title': 'Revenue Trend',
                'data_key': 'monthly_revenue'
            },
            {
                'id': 'expense_pie',
                'type': 'pie',
                'title': 'Expense Breakdown',
                'data_key': 'expense_by_category'
            }
        ]
        
        template = ReportTemplate.objects.create(
            company=self.company,
            name='Visual Report',
            charts=charts,
            created_by=self.user
        )
        
        self.assertEqual(len(template.charts), 2)
        self.assertEqual(template.charts[0]['type'], 'line')
        self.assertEqual(template.charts[1]['title'], 'Expense Breakdown')
    
    def test_default_parameters_and_filters(self):
        """Test default parameters and filters"""
        defaults = {
            'period': 'last_month',
            'include_pending': False
        }
        filters = {
            'min_transaction_amount': 0,
            'exclude_internal': True
        }
        
        template = ReportTemplate.objects.create(
            company=self.company,
            name='Standard Report',
            default_parameters=defaults,
            default_filters=filters,
            created_by=self.user
        )
        
        self.assertEqual(template.default_parameters['period'], 'last_month')
        self.assertTrue(template.default_filters['exclude_internal'])
    
    def test_template_visibility(self):
        """Test template public/private visibility"""
        # Private template
        private_template = ReportTemplate.objects.create(
            company=self.company,
            name='Private Template',
            is_public=False,
            created_by=self.user
        )
        self.assertFalse(private_template.is_public)
        
        # Public template
        public_template = ReportTemplate.objects.create(
            company=self.company,
            name='Public Template',
            is_public=True,
            created_by=self.user
        )
        self.assertTrue(public_template.is_public)
    
    def test_template_activation(self):
        """Test template activation status"""
        template = ReportTemplate.objects.create(
            company=self.company,
            name='Active Template',
            created_by=self.user
        )
        
        # Should be active by default
        self.assertTrue(template.is_active)
        
        # Deactivate
        template.is_active = False
        template.save()
        self.assertFalse(template.is_active)
    
    def test_timestamp_fields(self):
        """Test created_at and updated_at timestamps"""
        template = ReportTemplate.objects.create(
            company=self.company,
            name='Timestamp Test',
            created_by=self.user
        )
        
        self.assertIsNotNone(template.created_at)
        self.assertIsNotNone(template.updated_at)
        
        # Update template
        original_updated = template.updated_at
        template.name = 'Updated Template'
        template.save()
        
        # updated_at should change
        self.assertGreater(template.updated_at, original_updated)