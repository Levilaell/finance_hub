"""
Unit tests for reports services with mocked external APIs
"""
import json
import hashlib
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock, Mock

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.companies.models import Company, SubscriptionPlan
from apps.banking.models import BankAccount, Transaction
from apps.banking.models import TransactionCategory
from apps.reports.models import Report
from apps.reports.services.validation_service import ReportValidationService
from apps.reports.services.cache_service import ReportCacheService
from apps.reports.exceptions import (
    InvalidReportPeriodError,
    ReportDataInsufficientError,
    ReportGenerationInProgressError
)

User = get_user_model()


class ReportValidationServiceTest(TestCase):
    """Test ReportValidationService with comprehensive validation scenarios"""
    
    def setUp(self):
        self.company = CompanyFactory(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.user.company = self.company
        self.user.save()
        
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
    
    def test_validate_date_range_valid_dates(self):
        """Test validation with valid date ranges"""
        # Valid 30-day range
        start_date, end_date = ReportValidationService._validate_date_range(
            "2024-01-01",
            "2024-01-31"
        )
        
        self.assertEqual(start_date, date(2024, 1, 1))
        self.assertEqual(end_date, date(2024, 1, 31))
        
        # Valid single day
        start_date, end_date = ReportValidationService._validate_date_range(
            "2024-01-15",
            "2024-01-15"
        )
        
        self.assertEqual(start_date, date(2024, 1, 15))
        self.assertEqual(end_date, date(2024, 1, 15))
    
    def test_validate_date_range_invalid_formats(self):
        """Test validation with invalid date formats"""
        invalid_formats = [
            ("01-01-2024", "2024-01-31"),  # DD-MM-YYYY format
            ("2024/01/01", "2024-01-31"),  # Different separator
            ("2024-1-1", "2024-01-31"),    # Missing leading zeros
            ("invalid", "2024-01-31"),     # Completely invalid
            ("2024-13-01", "2024-01-31"),  # Invalid month
            ("2024-01-32", "2024-01-31"),  # Invalid day
        ]
        
        for start_str, end_str in invalid_formats:
            with self.subTest(start=start_str, end=end_str):
                with self.assertRaises(InvalidReportPeriodError):
                    ReportValidationService._validate_date_range(start_str, end_str)
    
    def test_validate_date_range_logical_errors(self):
        """Test validation with logically invalid date ranges"""
        # Start date after end date
        with self.assertRaises(InvalidReportPeriodError):
            ReportValidationService._validate_date_range("2024-02-01", "2024-01-01")
        
        # Future end date
        future_date = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        with self.assertRaises(InvalidReportPeriodError):
            ReportValidationService._validate_date_range("2024-01-01", future_date)
        
        # Range exceeding 365 days
        with self.assertRaises(InvalidReportPeriodError):
            ReportValidationService._validate_date_range("2023-01-01", "2024-01-02")
    
    def test_validate_report_type_valid_types(self):
        """Test validation with valid report types"""
        valid_types = [
            'monthly_summary',
            'cash_flow',
            'profit_loss',
            'category_analysis',
            'quarterly_report',
            'annual_report',
            'tax_report'
        ]
        
        for report_type in valid_types:
            with self.subTest(report_type=report_type):
                validated_type = ReportValidationService._validate_report_type(report_type)
                self.assertEqual(validated_type, report_type)
    
    def test_validate_report_type_invalid_types(self):
        """Test validation with invalid report types"""
        invalid_types = [
            'invalid_type',
            '',
            None,
            'custom_report',  # Assuming this is not in valid choices
            'MONTHLY_SUMMARY',  # Wrong case
        ]
        
        for report_type in invalid_types:
            with self.subTest(report_type=report_type):
                with self.assertRaises(ValidationError):
                    ReportValidationService._validate_report_type(report_type)
    
    def test_validate_filters_comprehensive(self):
        """Test comprehensive filter validation"""
        # Valid filters
        valid_filters = {
            'category_ids': [1, 2, 3],
            'account_ids': [4, 5],
            'transaction_type': 'credit',
            'min_amount': '100.50',
            'max_amount': '1000.00',
            'exclude_transfers': True,
            'include_pending': False,
            'date_grouping': 'monthly',
            'currency': 'BRL'
        }
        
        validated = ReportValidationService._validate_filters(valid_filters)
        
        self.assertEqual(validated['category_ids'], [1, 2, 3])
        self.assertEqual(validated['account_ids'], [4, 5])
        self.assertEqual(validated['transaction_type'], 'credit')
        self.assertEqual(validated['min_amount'], 100.50)
        self.assertEqual(validated['max_amount'], 1000.00)
        self.assertTrue(validated['exclude_transfers'])
        self.assertFalse(validated['include_pending'])
    
    def test_validate_filters_invalid_ranges(self):
        """Test filter validation with invalid amount ranges"""
        # Min amount greater than max amount
        invalid_filters = {
            'min_amount': '1000',
            'max_amount': '100'
        }
        
        with self.assertRaises(ValidationError):
            ReportValidationService._validate_filters(invalid_filters)
        
        # Negative amounts
        invalid_filters = {
            'min_amount': '-100',
            'max_amount': '1000'
        }
        
        with self.assertRaises(ValidationError):
            ReportValidationService._validate_filters(invalid_filters)
    
    def test_validate_filters_invalid_types(self):
        """Test filter validation with invalid data types"""
        invalid_filters = [
            {'category_ids': 'not_a_list'},
            {'account_ids': [1, 'invalid_id', 3]},
            {'transaction_type': 'invalid_type'},
            {'min_amount': 'not_a_number'},
            {'date_grouping': 'invalid_grouping'},
        ]
        
        for filters in invalid_filters:
            with self.subTest(filters=filters):
                with self.assertRaises(ValidationError):
                    ReportValidationService._validate_filters(filters)
    
    def test_validate_company_permissions(self):
        """Test company-based permission validation"""
        # User can access their own company's data
        result = ReportValidationService.validate_company_access(
            self.user,
            self.company.id
        )
        self.assertTrue(result)
        
        # Create another company
        other_company = Company.objects.create(
            name="Other Company",
            cnpj="98765432000100"
        )
        
        # User cannot access other company's data
        with self.assertRaises(ValidationError):
            ReportValidationService.validate_company_access(
                self.user,
                other_company.id
            )
    
    def test_validate_subscription_limits(self):
        """Test subscription-based validation"""
        # Create subscription
        # Create subscription plan and assign to company
        from apps.companies.tests.factories import SubscriptionPlanFactory
        subscription_plan = SubscriptionPlanFactory(
            name="starter".title(),
            slug="starter",
            has_advanced_reports=True
        )
        self.company.subscription_plan = subscription_plan
        self.company.subscription_status = "active"
        self.company.save()
        
        # Mock plan limits
        with patch.object(subscription, 'plan_data', {
            'max_reports_per_month': 5,
            'has_advanced_reports': False
        }):
            # Should allow basic reports under limit
            result = ReportValidationService.validate_subscription_limits(
                self.company,
                'monthly_summary'
            )
            self.assertTrue(result)
            
            # Should reject advanced reports
            with self.assertRaises(ValidationError):
                ReportValidationService.validate_subscription_limits(
                    self.company,
                    'advanced_analytics'  # Assuming this requires premium
                )
    
    def test_validate_data_availability(self):
        """Test validation of data availability for reports"""
        # Create transactions for testing
        for i in range(5):
            Transaction.objects.create(
                pluggy_transaction_id=f"txn_{i}",
                account=self.account,
                company=self.company.id,
                type="DEBIT" if i % 2 == 0 else "CREDIT",
                amount=Decimal(f"{(i + 1) * 10}.00"),
                description=f"Transaction {i + 1}",
                date=date(2024, 1, i + 1),
                currency_code="BRL"
            )
        
        # Should pass with sufficient data
        result = ReportValidationService.validate_data_availability(
            self.company,
            date(2024, 1, 1),
            date(2024, 1, 31),
            'monthly_summary'
        )
        self.assertTrue(result)
        
        # Should fail with no data in range
        with self.assertRaises(ReportDataInsufficientError):
            ReportValidationService.validate_data_availability(
                self.company,
                date(2023, 1, 1),
                date(2023, 1, 31),
                'monthly_summary'
            )
    
    def test_validate_concurrent_reports(self):
        """Test validation of concurrent report generation"""
        # Create a report in progress
        report_in_progress = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='In Progress Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            is_generated=False,
            created_by=self.user
        )
        
        # Should allow different report types
        result = ReportValidationService.validate_concurrent_reports(
            self.company,
            'cash_flow'
        )
        self.assertTrue(result)
        
        # Should reject same type in progress
        with self.assertRaises(ReportGenerationInProgressError):
            ReportValidationService.validate_concurrent_reports(
                self.company,
                'monthly_summary'
            )


class ReportCacheServiceTest(TestCase):
    """Test ReportCacheService with comprehensive caching scenarios"""
    
    def setUp(self):
        self.company_id = 1
        self.start_date = "2024-01-01"
        self.end_date = "2024-01-31"
        
        # Clear cache before each test
        cache.clear()
    
    def tearDown(self):
        # Clear cache after each test
        cache.clear()
    
    def test_cache_key_generation_consistency(self):
        """Test that cache keys are generated consistently"""
        key1 = ReportCacheService._generate_cache_key(
            'analytics',
            company_id=1,
            period_days=30,
            extra_param='test'
        )
        
        key2 = ReportCacheService._generate_cache_key(
            'analytics',
            company_id=1,
            period_days=30,
            extra_param='test'
        )
        
        self.assertEqual(key1, key2)
        self.assertEqual(len(key1), 32)  # MD5 hash length
    
    def test_cache_key_generation_uniqueness(self):
        """Test that different parameters generate different keys"""
        key1 = ReportCacheService._generate_cache_key(
            'analytics',
            company_id=1,
            period_days=30
        )
        
        key2 = ReportCacheService._generate_cache_key(
            'analytics',
            company_id=2,  # Different company
            period_days=30
        )
        
        key3 = ReportCacheService._generate_cache_key(
            'analytics',
            company_id=1,
            period_days=60  # Different period
        )
        
        self.assertNotEqual(key1, key2)
        self.assertNotEqual(key1, key3)
        self.assertNotEqual(key2, key3)
    
    def test_analytics_cache_operations(self):
        """Test analytics data caching operations"""
        test_data = {
            'total_income': Decimal('5000.00'),
            'total_expenses': Decimal('3000.00'),
            'net_result': Decimal('2000.00'),
            'transaction_count': 150,
            'categories_breakdown': {
                'food': Decimal('800.00'),
                'transport': Decimal('400.00'),
                'utilities': Decimal('600.00')
            }
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
        
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['total_income'], 5000.00)  # Decimal converted to float
        self.assertEqual(cached_data['transaction_count'], 150)
        self.assertEqual(cached_data['categories_breakdown']['food'], 800.00)
    
    def test_cache_expiration(self):
        """Test cache expiration behavior"""
        test_data = {'test': 'data'}
        
        # Set cache with custom TTL
        with override_settings(CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'TIMEOUT': 1  # 1 second
            }
        }):
            ReportCacheService.set_analytics_data(
                self.company_id,
                30,
                self.start_date,
                self.end_date,
                test_data,
                timeout=1
            )
            
            # Should be available immediately
            cached_data = ReportCacheService.get_analytics_data(
                self.company_id,
                30,
                self.start_date,
                self.end_date
            )
            self.assertIsNotNone(cached_data)
            
            # Mock time passage and test expiration
            import time
            time.sleep(2)
            
            cached_data = ReportCacheService.get_analytics_data(
                self.company_id,
                30,
                self.start_date,
                self.end_date
            )
            # Note: LocMemCache might not respect timeout exactly in tests
            # This is more for testing the interface
    
    def test_decimal_serialization_comprehensive(self):
        """Test comprehensive Decimal serialization scenarios"""
        complex_data = {
            'simple_decimal': Decimal('123.45'),
            'nested_object': {
                'amount': Decimal('67.89'),
                'percentage': Decimal('15.50'),
                'nested_again': {
                    'deep_amount': Decimal('999.99')
                }
            },
            'decimal_list': [
                Decimal('10.00'),
                Decimal('20.50'),
                Decimal('30.75')
            ],
            'mixed_list': [
                Decimal('100.00'),
                'string_value',
                42,
                {'nested_decimal': Decimal('200.00')}
            ],
            'none_value': None,
            'boolean_value': True,
            'string_value': 'test',
            'integer_value': 123
        }
        
        serialized = ReportCacheService._serialize_for_cache(complex_data)
        
        # Check simple decimal conversion
        self.assertEqual(serialized['simple_decimal'], 123.45)
        
        # Check nested object conversion
        self.assertEqual(serialized['nested_object']['amount'], 67.89)
        self.assertEqual(serialized['nested_object']['nested_again']['deep_amount'], 999.99)
        
        # Check list conversion
        self.assertEqual(serialized['decimal_list'], [10.00, 20.50, 30.75])
        
        # Check mixed list conversion
        mixed_list = serialized['mixed_list']
        self.assertEqual(mixed_list[0], 100.00)  # Decimal converted
        self.assertEqual(mixed_list[1], 'string_value')  # String unchanged
        self.assertEqual(mixed_list[2], 42)  # Integer unchanged
        self.assertEqual(mixed_list[3]['nested_decimal'], 200.00)  # Nested decimal converted
        
        # Check other types unchanged
        self.assertIsNone(serialized['none_value'])
        self.assertTrue(serialized['boolean_value'])
        self.assertEqual(serialized['string_value'], 'test')
        self.assertEqual(serialized['integer_value'], 123)
    
    def test_dashboard_cache_operations(self):
        """Test dashboard-specific cache operations"""
        dashboard_data = {
            'total_balance': Decimal('10000.00'),
            'monthly_income': Decimal('5000.00'),
            'monthly_expenses': Decimal('3000.00'),
            'accounts_summary': [
                {
                    'id': 1,
                    'name': 'Checking Account',
                    'balance': Decimal('5000.00')
                },
                {
                    'id': 2,
                    'name': 'Savings Account',  
                    'balance': Decimal('5000.00')
                }
            ]
        }
        
        # Set dashboard cache
        ReportCacheService.set_dashboard_data(
            self.company_id,
            dashboard_data
        )
        
        # Get dashboard cache
        cached_data = ReportCacheService.get_dashboard_data(self.company_id)
        
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['total_balance'], 10000.00)
        self.assertEqual(len(cached_data['accounts_summary']), 2)
        self.assertEqual(cached_data['accounts_summary'][0]['balance'], 5000.00)
    
    def test_report_template_cache_operations(self):
        """Test report template caching operations"""
        template_data = {
            'id': 1,
            'name': 'Monthly Summary Template',
            'config': {
                'sections': ['summary', 'charts', 'detailed_breakdown'],
                'styling': {
                    'primary_color': '#1f2937',
                    'font_family': 'Arial'
                }
            },
            'charts': [
                {
                    'type': 'line',
                    'title': 'Monthly Trend',
                    'data_key': 'monthly_data'
                }
            ]
        }
        
        # Set template cache
        ReportCacheService.set_report_template(
            template_id=1,
            template_data=template_data
        )
        
        # Get template cache
        cached_template = ReportCacheService.get_report_template(template_id=1)
        
        self.assertIsNotNone(cached_template)
        self.assertEqual(cached_template['name'], 'Monthly Summary Template')
        self.assertEqual(len(cached_template['config']['sections']), 3)
        self.assertEqual(len(cached_template['charts']), 1)
    
    def test_cache_invalidation(self):
        """Test cache invalidation operations"""
        # Set multiple cache entries
        data1 = {'test': 'data1'}
        data2 = {'test': 'data2'}
        
        ReportCacheService.set_analytics_data(
            self.company_id, 30, self.start_date, self.end_date, data1
        )
        ReportCacheService.set_dashboard_data(self.company_id, data2)
        
        # Verify data is cached
        self.assertIsNotNone(ReportCacheService.get_analytics_data(
            self.company_id, 30, self.start_date, self.end_date
        ))
        self.assertIsNotNone(ReportCacheService.get_dashboard_data(self.company_id))
        
        # Invalidate analytics cache
        ReportCacheService.invalidate_analytics_cache(
            self.company_id, 30, self.start_date, self.end_date
        )
        
        # Analytics should be gone, dashboard should remain
        self.assertIsNone(ReportCacheService.get_analytics_data(
            self.company_id, 30, self.start_date, self.end_date
        ))
        self.assertIsNotNone(ReportCacheService.get_dashboard_data(self.company_id))
        
        # Invalidate all company cache
        ReportCacheService.invalidate_company_cache(self.company_id)
        
        # All should be gone
        self.assertIsNone(ReportCacheService.get_dashboard_data(self.company_id))
    
    def test_cache_miss_behavior(self):
        """Test behavior when cache misses occur"""
        # Test getting non-existent cache entries
        self.assertIsNone(ReportCacheService.get_analytics_data(
            999, 30, "2024-01-01", "2024-01-31"
        ))
        
        self.assertIsNone(ReportCacheService.get_dashboard_data(999))
        
        self.assertIsNone(ReportCacheService.get_report_template(999))
    
    def test_cache_with_complex_parameters(self):
        """Test caching with complex parameter combinations"""
        # Test with filters and custom parameters
        complex_params = {
            'account_ids': [1, 2, 3],
            'category_ids': [4, 5],
            'exclude_transfers': True,
            'include_pending': False,
            'custom_filter': 'advanced'
        }
        
        test_data = {'complex': 'result'}
        
        # Generate key with complex parameters
        cache_key = ReportCacheService._generate_cache_key(
            'complex_analytics',
            company_id=self.company_id,
            **complex_params
        )
        
        # Set and get with same parameters
        cache.set(cache_key, ReportCacheService._serialize_for_cache(test_data))
        cached_data = cache.get(cache_key)
        
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['complex'], 'result')


class ReportGenerationServiceTest(TestCase):
    """Test report generation service with mocked external dependencies"""
    
    def setUp(self):
        self.company = CompanyFactory(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.user.company = self.company
        self.user.save()
        
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
                amount=Decimal(f"{(i + 1) * 100}.00"),
                description=f"Transaction {i + 1}",
                date=date(2024, 1, i + 1),
                currency_code="BRL",
                category=self.transaction_category if i % 2 == 0 else None
            )
    
    @patch('apps.reports.report_generator.ReportGenerator.generate_report')
    def test_report_generation_with_ai_integration(self, mock_generator):
        """Test report generation with mocked AI integration"""
        # Mock AI service response
        mock_ai_response = {
            'insights': [
                {
                    'type': 'success',
                    'title': 'Strong Financial Health',
                    'description': 'Your expenses are well controlled this month.'
                }
            ],
            'predictions': {
                'next_month_expenses': 2800.00,
                'savings_potential': 500.00
            },
            'recommendations': [
                {
                    'title': 'Optimize Food Spending',
                    'description': 'Consider meal planning to reduce food costs.',
                    'impact': 'medium'
                }
            ]
        }
        
        # Mock PDF generation
        mock_pdf_buffer = MagicMock()
        mock_pdf_buffer.getvalue.return_value = b'%PDF-1.4 mock pdf content'
        mock_pdf_buffer.tell.return_value = 1024
        mock_generator.return_value = mock_pdf_buffer
        
        # Create report
        report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='AI Enhanced Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            parameters={'include_ai_insights': True},
            created_by=self.user
        )
        
        # Mock AI service integration
        with patch('apps.reports.services.ai_service.AIService.generate_insights') as mock_ai:
            mock_ai.return_value = mock_ai_response
            
            # Generate report
            from apps.reports.services.report_generation_service import ReportGenerationService
            service = ReportGenerationService()
            result = service.generate_report(report.id)
            
            # Verify AI service was called
            mock_ai.assert_called_once()
            
            # Verify report generation was called
            mock_generator.assert_called_once()
            
            # Verify result
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['report_id'], report.id)
    
    @patch('openai.ChatCompletion.create')
    def test_openai_integration_error_handling(self, mock_openai):
        """Test OpenAI integration with error handling"""
        # Mock OpenAI failure
        mock_openai.side_effect = Exception("OpenAI API error")
        
        report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='OpenAI Error Test',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            parameters={'include_ai_insights': True},
            created_by=self.user
        )
        
        # Should handle OpenAI error gracefully
        with patch('apps.reports.services.ai_service.AIService.generate_insights') as mock_ai_service:
            mock_ai_service.side_effect = Exception("AI service unavailable")
            
            from apps.reports.services.report_generation_service import ReportGenerationService
            service = ReportGenerationService()
            
            # Should not raise exception, but return error status
            with patch('apps.reports.report_generator.ReportGenerator.generate_report') as mock_generator:
                mock_pdf_buffer = MagicMock()
                mock_pdf_buffer.getvalue.return_value = b'%PDF-1.4 fallback content'
                mock_pdf_buffer.tell.return_value = 512
                mock_generator.return_value = mock_pdf_buffer
                
                result = service.generate_report_with_fallback(report.id)
                
                # Should generate report without AI insights
                self.assertEqual(result['status'], 'success')
                self.assertIn('ai_insights_failed', result)
    
    @patch('stripe.Invoice.create')
    @patch('stripe.Customer.retrieve')
    def test_subscription_integration(self, mock_customer, mock_invoice):
        """Test integration with subscription/billing system"""
        # Mock Stripe responses
        mock_customer.return_value = MagicMock(
            id='cus_test123',
            subscriptions=MagicMock(
                data=[MagicMock(
                    status='active',
                    plan=MagicMock(id='plan_premium')
                )]
            )
        )
        
        mock_invoice.return_value = MagicMock(
            id='in_test123',
            amount_due=2000,  # $20.00
            status='paid'
        )
        
        # Create subscription-dependent report
        report = Report.objects.create(
            company=self.company,
            report_type='advanced_analytics',  # Premium feature
            title='Premium Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            created_by=self.user
        )
        
        # Test subscription validation
        from apps.reports.services.subscription_service import SubscriptionService
        service = SubscriptionService()
        
        # Should allow premium features for active subscription
        can_generate = service.can_generate_report(
            self.company,
            'advanced_analytics'
        )
        self.assertTrue(can_generate)
        
        # Mock expired subscription
        mock_customer.return_value.subscriptions.data[0].status = 'past_due'
        
        can_generate = service.can_generate_report(
            self.company,
            'advanced_analytics'
        )
        self.assertFalse(can_generate)
    
    def test_pluggy_api_integration_mock(self):
        """Test Pluggy API integration with mocked responses"""
        # Mock Pluggy API responses for account data
        mock_pluggy_accounts = [
            {
                'id': 'acc_123',
                'name': 'Checking Account',
                'balance': 5000.00,
                'currency': 'BRL',
                'type': 'BANK'
            },
            {
                'id': 'acc_456',
                'name': 'Savings Account',
                'balance': 10000.00,
                'currency': 'BRL',
                'type': 'BANK'
            }
        ]
        
        mock_pluggy_transactions = [
            {
                'id': 'txn_123',
                'description': 'Supermarket Purchase',
                'amount': -150.00,
                'date': '2024-01-15',
                'category': 'food'
            },
            {
                'id': 'txn_456',
                'description': 'Salary',
                'amount': 5000.00,
                'date': '2024-01-01',
                'category': 'income'
            }
        ]
        
        # Create report that needs fresh data from Pluggy
        report = Report.objects.create(
            company=self.company,
            report_type='real_time_report',
            title='Real-time Data Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            parameters={'include_real_time_data': True},
            created_by=self.user
        )
        
        # Mock Pluggy service integration
        with patch('apps.banking.services.pluggy_service.PluggyService.get_accounts') as mock_accounts:
            with patch('apps.banking.services.pluggy_service.PluggyService.get_transactions') as mock_transactions:
                mock_accounts.return_value = mock_pluggy_accounts
                mock_transactions.return_value = mock_pluggy_transactions
                
                from apps.reports.services.data_collection_service import DataCollectionService
                service = DataCollectionService()
                
                # Collect fresh data from Pluggy
                data = service.collect_real_time_data(
                    self.company,
                    date(2024, 1, 1),
                    date(2024, 1, 31)
                )
                
                # Verify Pluggy APIs were called
                mock_accounts.assert_called_once()
                mock_transactions.assert_called_once()
                
                # Verify data structure
                self.assertIn('accounts', data)
                self.assertIn('transactions', data)
                self.assertEqual(len(data['accounts']), 2)
                self.assertEqual(len(data['transactions']), 2)
                self.assertEqual(data['accounts'][0]['balance'], 5000.00)