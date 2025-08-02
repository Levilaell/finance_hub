"""
Unit tests for report generation functionality
"""
import json
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.base import ContentFile
from rest_framework.test import APITestCase
from rest_framework import status

from apps.companies.models import Company, SubscriptionPlan
from apps.banking.models import BankAccount, Transaction
from apps.banking.models import TransactionCategory
from apps.reports.models import Report, ReportTemplate
from apps.reports.services.validation_service import ReportValidationService
from apps.reports.services.cache_service import ReportCacheService
from apps.reports.exceptions import (
    InvalidReportPeriodError,
    ReportDataInsufficientError,
    ReportGenerationInProgressError
)

User = get_user_model()


class ReportValidationServiceTest(TestCase):
    """Test report validation service"""
    
    def setUp(self):
        self.company = CompanyFactory(name="Test Company")
    
    def test_validate_date_range_valid(self):
        """Test valid date range validation"""
        start_date, end_date = ReportValidationService._validate_date_range(
            "2024-01-01",
            "2024-01-31"
        )
        
        self.assertEqual(start_date, date(2024, 1, 1))
        self.assertEqual(end_date, date(2024, 1, 31))
    
    def test_validate_date_range_invalid_format(self):
        """Test invalid date format"""
        with self.assertRaises(InvalidReportPeriodError):
            ReportValidationService._validate_date_range(
                "01-01-2024",  # Wrong format
                "2024-01-31"
            )
    
    def test_validate_date_range_start_after_end(self):
        """Test start date after end date"""
        with self.assertRaises(InvalidReportPeriodError):
            ReportValidationService._validate_date_range(
                "2024-02-01",
                "2024-01-01"
            )
    
    def test_validate_date_range_future_date(self):
        """Test future end date"""
        future_date = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        with self.assertRaises(InvalidReportPeriodError):
            ReportValidationService._validate_date_range(
                "2024-01-01",
                future_date
            )
    
    def test_validate_date_range_exceeds_limit(self):
        """Test date range exceeding 365 days"""
        with self.assertRaises(InvalidReportPeriodError):
            ReportValidationService._validate_date_range(
                "2023-01-01",
                "2024-01-02"  # 366 days
            )
    
    def test_validate_report_type(self):
        """Test report type validation"""
        valid_type = ReportValidationService._validate_report_type("monthly_summary")
        self.assertEqual(valid_type, "monthly_summary")
        
        # Test invalid type
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            ReportValidationService._validate_report_type("invalid_type")
    
    def test_validate_filters(self):
        """Test filter validation"""
        filters = {
            'category_ids': [1, 2, 3],
            'account_ids': [4, 5],
            'transaction_type': 'credit',
            'min_amount': '100.50',
            'max_amount': '1000.00'
        }
        
        validated = ReportValidationService._validate_filters(filters)
        
        self.assertEqual(validated['category_ids'], [1, 2, 3])
        self.assertEqual(validated['account_ids'], [4, 5])
        self.assertEqual(validated['transaction_type'], 'credit')
        self.assertEqual(validated['min_amount'], 100.50)
        self.assertEqual(validated['max_amount'], 1000.00)
    
    def test_validate_filters_invalid_amount_range(self):
        """Test invalid amount range in filters"""
        from django.core.exceptions import ValidationError
        
        filters = {
            'min_amount': '1000',
            'max_amount': '100'  # Less than min
        }
        
        with self.assertRaises(ValidationError):
            ReportValidationService._validate_filters(filters)


class ReportGenerationAPITest(APITestCase):
    """Test report generation API endpoints"""
    
    def setUp(self):
        # Create user and company
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.company = CompanyFactory(name="Test Company")
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
        
        # Create bank account
        self.account = BankAccount.objects.create(
            company=self.company,
            bank_provider=MagicMock(name="Test Bank"),
            account_type="checking",
            balance=Decimal("1000.00")
        )
        
        # Create category
        self.transaction_category = TransactionCategory.objects.create(
            name="Food",
            icon="utensils"
        )
        
        # Create transactions
        for i in range(10):
            Transaction.objects.create(
                bank_account=self.account,
                transaction_type="debit" if i % 2 == 0 else "credit",
                amount=Decimal(f"{(i + 1) * 10}.00"),
                description=f"Transaction {i + 1}",
                transaction_date=timezone.now().date() - timedelta(days=i),
                category=self.transaction_category if i % 2 == 0 else None
            )
        
        self.client.force_authenticate(user=self.user)
    
    @patch('apps.reports.views.generate_report_async.delay')
    def test_create_report_success(self, mock_task):
        """Test successful report creation"""
        data = {
            'report_type': 'monthly_summary',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'title': 'January Report',
            'file_format': 'pdf'
        }
        
        response = self.client.post('/api/reports/reports/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['report_type'], 'monthly_summary')
        self.assertEqual(response.data['status'], 'processing')
        
        # Check that async task was called
        mock_task.assert_called_once()
    
    def test_create_report_invalid_dates(self):
        """Test report creation with invalid dates"""
        data = {
            'report_type': 'monthly_summary',
            'period_start': '2024-02-01',
            'period_end': '2024-01-01',  # Before start
            'title': 'Invalid Report'
        }
        
        response = self.client.post('/api/reports/reports/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Start date must be before', str(response.data))
    
    def test_create_report_no_data(self):
        """Test report creation with no transaction data"""
        # Delete all transactions
        Transaction.objects.all().delete()
        
        data = {
            'report_type': 'monthly_summary',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'title': 'Empty Report'
        }
        
        response = self.client.post('/api/reports/reports/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn('No transactions found', str(response.data))
    
    def test_download_report_with_signed_url(self):
        """Test secure report download"""
        from django.core.signing import TimestampSigner
        
        # Create a generated report
        report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Test Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            is_generated=True,
            created_by=self.user
        )
        
        # Add a dummy file
        report.file.save('test.pdf', ContentFile(b'PDF content'))
        
        # Generate signed URL
        signer = TimestampSigner()
        signed_id = signer.sign(str(report.id))
        
        response = self.client.get(f'/api/reports/secure-download/{signed_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_download_report_invalid_signature(self):
        """Test download with invalid signature"""
        response = self.client.get('/api/reports/secure-download/invalid_signature/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_report_summary_endpoint(self):
        """Test report summary endpoint"""
        # Create some reports
        for i in range(5):
            Report.objects.create(
                company=self.company,
                report_type='monthly_summary',
                title=f'Report {i}',
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31),
                is_generated=i % 2 == 0,  # Some generated, some not
                created_by=self.user
            )
        
        response = self.client.get('/api/reports/reports/summary/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_reports'], 5)
        self.assertEqual(response.data['reports_generated'], 3)
        self.assertEqual(response.data['reports_pending'], 2)


class ReportCacheServiceTest(TestCase):
    """Test report cache service"""
    
    def setUp(self):
        self.company_id = 1
        self.start_date = "2024-01-01"
        self.end_date = "2024-01-31"
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        key = ReportCacheService._generate_cache_key(
            'analytics',
            company_id=1,
            period_days=30
        )
        
        self.assertIsInstance(key, str)
        self.assertEqual(len(key), 32)  # MD5 hash length
    
    def test_analytics_cache_operations(self):
        """Test analytics data caching"""
        test_data = {
            'total_income': 1000.00,
            'total_expenses': 500.00,
            'net_result': 500.00
        }
        
        # Set cache
        ReportCacheService.set_analytics_data(
            self.company_id,
            30,
            self.start_date,
            self.end_date,
            test_data
        )
        
        # Get from cache
        cached_data = ReportCacheService.get_analytics_data(
            self.company_id,
            30,
            self.start_date,
            self.end_date
        )
        
        self.assertEqual(cached_data, test_data)
    
    def test_decimal_serialization(self):
        """Test Decimal serialization for cache"""
        data = {
            'amount': Decimal('123.45'),
            'nested': {
                'value': Decimal('67.89')
            },
            'list': [Decimal('10.00'), Decimal('20.00')]
        }
        
        serialized = ReportCacheService._serialize_for_cache(data)
        
        self.assertEqual(serialized['amount'], 123.45)
        self.assertEqual(serialized['nested']['value'], 67.89)
        self.assertEqual(serialized['list'], [10.00, 20.00])


class AsyncTaskTest(TransactionTestCase):
    """Test async task functionality"""
    
    def setUp(self):
        # Create test data
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.company = CompanyFactory(name="Test Company")
        self.report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Test Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            created_by=self.user
        )
    
    @patch('apps.reports.report_generator.ReportGenerator.generate_report')
    def test_generate_report_async_task(self, mock_generate):
        """Test async report generation task"""
        from apps.reports.tasks import generate_report_async
        
        # Mock report generation
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b'PDF content'
        mock_buffer.tell.return_value = 1024
        mock_generate.return_value = mock_buffer
        
        # Run task
        result = generate_report_async(self.report.id)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['report_id'], self.report.id)
        
        # Refresh report
        self.report.refresh_from_db()
        self.assertTrue(self.report.is_generated)
        self.assertIsNotNone(self.report.file)
        self.assertEqual(self.report.file_size, 1024)
    
    def test_generate_report_async_task_failure(self):
        """Test async task failure handling"""
        from apps.reports.tasks import generate_report_async
        
        # Use non-existent report ID
        result = generate_report_async(99999)
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], 'Report not found')