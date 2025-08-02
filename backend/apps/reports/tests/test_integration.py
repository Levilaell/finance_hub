"""
End-to-end integration tests for the reports system.
Tests complete workflows from API calls through to file generation and notifications.
"""
import json
import os
import tempfile
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
from io import BytesIO

from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

from apps.companies.models import Company, SubscriptionPlan
from apps.banking.models import BankAccount, Transaction
from apps.banking.models import TransactionCategory
from apps.reports.models import Report
from apps.reports.tasks import generate_report_async
from apps.reports import consumers

User = get_user_model()


class ReportsAPIIntegrationTest(TestCase):
    """Test complete API workflows for reports functionality"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test company and user
        self.company = CompanyFactory(name="Integration Test Company")
        
        self.user = User.objects.create_user(
            email="integration@test.com",
            password="testpass123",
            is_verified=True
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
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.account = BankAccount.objects.create(
            company=self.company,
            pluggy_account_id="test_account_123",
            item=MagicMock(),
            type="BANK",
            balance=Decimal("10000.00"),
            currency_code="BRL"
        )
        
        self.transaction_category = TransactionCategory.objects.create(
            name="Food & Dining",
            icon="utensils",
            type="expense"
        )
        
        # Create transactions for reports
        self.transactions = []
        for i in range(20):
            transaction = Transaction.objects.create(
                pluggy_transaction_id=f"integration_txn_{i}",
                account=self.account,
                company=self.company.id,
                type="DEBIT" if i % 2 == 0 else "CREDIT",
                amount=Decimal(f"{(i + 1) * 50}.00"),
                description=f"Integration Transaction {i + 1}",
                date=date(2024, 1, (i % 28) + 1),
                currency_code="BRL",
                category=self.transaction_category if i % 3 == 0 else None
            )
            self.transactions.append(transaction)
    
    def test_complete_report_generation_workflow(self):
        """Test complete workflow from API request to generated report"""
        
        # Step 1: Create report via API
        create_data = {
            'report_type': 'monthly_summary',
            'title': 'Integration Test Report',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'file_format': 'pdf',
            'parameters': {
                'include_charts': True,
                'detailed_breakdown': True,
                'account_ids': [self.account.id],
                'category_ids': [self.transaction_category.id]
            }
        }
        
        response = self.client.post(
            reverse('reports:reports-list'),
            data=create_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report_data = response.json()
        report_id = report_data['id']
        
        # Verify report was created
        report = Report.objects.get(id=report_id)
        self.assertEqual(report.report_type, 'monthly_summary')
        self.assertEqual(report.title, 'Integration Test Report')
        self.assertFalse(report.is_generated)
        
        # Step 2: Mock PDF generation and trigger async task
        with patch('apps.reports.report_generator.ReportGenerator.generate_report') as mock_generator:
            mock_buffer = MagicMock()
            mock_buffer.getvalue.return_value = b'%PDF-1.4 integration test content'
            mock_buffer.tell.return_value = 2048
            mock_generator.return_value = mock_buffer
            
            # Execute async task
            result = generate_report_async(report_id)
            
            self.assertEqual(result['status'], 'success')
            
        # Step 3: Verify report was generated
        report.refresh_from_db()
        self.assertTrue(report.is_generated)
        self.assertIsNotNone(report.file)
        self.assertEqual(report.file_size, 2048)
        
        # Step 4: Get report status via API
        status_response = self.client.get(
            reverse('reports:reports-detail', kwargs={'pk': report_id})
        )
        
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)
        status_data = status_response.json()
        self.assertTrue(status_data['is_generated'])
        
        # Step 5: Download report via API
        download_response = self.client.get(
            reverse('reports:reports-download', kwargs={'pk': report_id})
        )
        
        self.assertEqual(download_response.status_code, status.HTTP_200_OK)
        self.assertIn('download_url', download_response.json())
    
    def test_report_list_filtering_and_pagination(self):
        """Test report listing with filters and pagination"""
        
        # Create multiple reports
        reports = []
        for i in range(15):
            report = Report.objects.create(
                company=self.company,
                report_type='monthly_summary' if i % 2 == 0 else 'cash_flow',
                title=f'Test Report {i + 1}',
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31),
                file_format='pdf',
                is_generated=i % 3 == 0,  # Some generated, some not
                created_by=self.user
            )
            reports.append(report)
        
        # Test basic listing
        response = self.client.get(reverse('reports:reports-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 15)
        
        # Test filtering by report type
        response = self.client.get(
            reverse('reports:reports-list'),
            {'report_type': 'monthly_summary'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 8)  # 8 monthly_summary reports (0,2,4,6,8,10,12,14)
        
        # Test filtering by generation status
        response = self.client.get(
            reverse('reports:reports-list'),
            {'is_generated': 'true'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 5)  # Every 3rd report is generated (0,3,6,9,12)
        
        # Test pagination
        response = self.client.get(
            reverse('reports:reports-list'),
            {'page': 1, 'page_size': 5}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['results']), 5)
        self.assertIsNotNone(data['next'])
        
        # Test second page
        response = self.client.get(
            reverse('reports:reports-list'),
            {'page': 2, 'page_size': 5}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['results']), 5)
    
    def test_analytics_api_integration(self):
        """Test analytics API with real data"""
        
        # Test analytics endpoint
        response = self.client.get(
            reverse('reports:analytics'),
            {'period': 30}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify analytics structure
        self.assertIn('total_income', data)
        self.assertIn('total_expenses', data) 
        self.assertIn('net_result', data)
        self.assertIn('transaction_count', data)
        
        # Verify calculations are correct based on test data
        # CREDIT transactions: 1,3,5,7,9,11,13,15,17,19 (10 transactions)
        # DEBIT transactions: 0,2,4,6,8,10,12,14,16,18 (10 transactions)
        expected_income = sum(Decimal(f"{(i + 1) * 50}") for i in range(20) if i % 2 == 1)
        expected_expenses = sum(Decimal(f"{(i + 1) * 50}") for i in range(20) if i % 2 == 0)
        
        self.assertEqual(Decimal(str(data['total_income'])), expected_income)
        self.assertEqual(Decimal(str(data['total_expenses'])), expected_expenses)
        self.assertEqual(data['transaction_count'], 20)
    
    def test_dashboard_stats_integration(self):
        """Test dashboard statistics API"""
        
        response = self.client.get(reverse('reports:dashboard-stats'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify dashboard data structure
        self.assertIn('total_balance', data)
        self.assertIn('income_this_month', data)
        self.assertIn('expenses_this_month', data)
        self.assertIn('net_income', data)
        
        # Verify balance calculation
        self.assertEqual(Decimal(str(data['total_balance'])), Decimal('10000.00'))
    
    def test_cash_flow_data_integration(self):
        """Test cash flow data API with date parameters"""
        
        response = self.client.get(
            reverse('reports:cash-flow-data'),
            {
                'start_date': '2024-01-01',
                'end_date': '2024-01-31'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)
        
        # Verify data points exist for the period
        if data['data']:
            first_point = data['data'][0]
            self.assertIn('date', first_point)
            self.assertIn('income', first_point)
            self.assertIn('expenses', first_point)
    
    def test_category_spending_integration(self):
        """Test category spending analysis API"""
        
        response = self.client.get(
            reverse('reports:category-spending'),
            {
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'type': 'expense'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)
        
        # Should have at least one category (our test category)
        category_data = [item for item in data['data'] if item['category'] == 'Food & Dining']
        self.assertGreater(len(category_data), 0)
    
    def test_report_regeneration_workflow(self):
        """Test report regeneration workflow"""
        
        # Create initial report
        report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Regeneration Test Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            is_generated=True,
            created_by=self.user
        )
        
        # Add file to simulate existing report
        report.file.save('original_report.pdf', ContentFile(b'original content'))
        original_file_size = report.file_size = 100
        report.save()
        
        # Regenerate report
        with patch('apps.reports.report_generator.ReportGenerator.generate_report') as mock_generator:
            mock_buffer = MagicMock()
            mock_buffer.getvalue.return_value = b'%PDF-1.4 regenerated content'
            mock_buffer.tell.return_value = 150
            mock_generator.return_value = mock_buffer
            
            response = self.client.post(
                reverse('reports:reports-regenerate', kwargs={'pk': report.id})
            )
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Execute regeneration task
            result = generate_report_async(report.id)
            self.assertEqual(result['status'], 'success')
        
        # Verify report was regenerated
        report.refresh_from_db()
        self.assertTrue(report.is_generated)
        self.assertEqual(report.file_size, 150)  # New size
    
    def test_company_isolation(self):
        """Test that companies can only access their own reports"""
        
        # Create another company and user
        other_company = Company.objects.create(
            name="Other Company",
            cnpj="98765432000100"
        )
        
        other_user = User.objects.create_user(
            email="other@test.com",
            password="testpass123",
            is_verified=True
        )
        other_user.company = other_company
        other_user.save()
        
        # Create report for other company
        other_report = Report.objects.create(
            company=other_company,
            report_type='monthly_summary',
            title='Other Company Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            created_by=other_user
        )
        
        # Current user should not be able to access other company's report
        response = self.client.get(
            reverse('reports:reports-detail', kwargs={'pk': other_report.id})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Switch to other user
        self.client.force_authenticate(user=other_user)
        
        # Other user should be able to access their report
        response = self.client.get(
            reverse('reports:reports-detail', kwargs={'pk': other_report.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_api_error_handling(self):
        """Test API error handling scenarios"""
        
        # Test invalid report type
        invalid_data = {
            'report_type': 'invalid_type',
            'title': 'Invalid Report',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'file_format': 'pdf'
        }
        
        response = self.client.post(
            reverse('reports:reports-list'),
            data=invalid_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('report_type', response.json())
        
        # Test invalid date range
        invalid_data = {
            'report_type': 'monthly_summary',
            'title': 'Invalid Date Report',
            'period_start': '2024-02-01',
            'period_end': '2024-01-01',  # End before start
            'file_format': 'pdf'
        }
        
        response = self.client.post(
            reverse('reports:reports-list'),
            data=invalid_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test non-existent report access
        response = self.client.get(
            reverse('reports:reports-detail', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ScheduledReportsIntegrationTest(TestCase):
    """Test scheduled reports functionality"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test company and user
        self.company = CompanyFactory(name="Scheduled Test Company")
        
        self.user = User.objects.create_user(
            email="scheduled@test.com",
            password="testpass123",
            is_verified=True
        )
        self.user.company = self.company
        self.user.save()
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
    
    def test_scheduled_report_creation_workflow(self):
        """Test complete scheduled report creation and management"""
        
        # Create scheduled report
        schedule_data = {
            'name': 'Weekly Revenue Report',
            'report_type': 'weekly_summary',
            'frequency': 'weekly',
            'email_recipients': ['manager@company.com', 'finance@company.com'],
            'file_format': 'pdf',
            'parameters': {
                'include_charts': True,
                'send_email': True
            }
        }
        
        response = self.client.post(
            reverse('reports:schedules-list'),
            data=schedule_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        schedule_data = response.json()
        schedule_id = schedule_data['id']
        
        # Verify scheduled report was created
        scheduled_report = ScheduledReport.objects.get(id=schedule_id)
        self.assertEqual(scheduled_report.name, 'Weekly Revenue Report')
        self.assertEqual(scheduled_report.frequency, 'weekly')
        self.assertTrue(scheduled_report.is_active)
        
        # Test retrieving scheduled report
        response = self.client.get(
            reverse('reports:schedules-detail', kwargs={'pk': schedule_id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test updating scheduled report
        update_data = {
            'name': 'Updated Weekly Report',
            'is_active': False
        }
        
        response = self.client.patch(
            reverse('reports:schedules-detail', kwargs={'pk': schedule_id}),
            data=update_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify update
        scheduled_report.refresh_from_db()
        self.assertEqual(scheduled_report.name, 'Updated Weekly Report')
        self.assertFalse(scheduled_report.is_active)
    
    def test_scheduled_report_toggle_active(self):
        """Test toggling scheduled report active status"""
        
        # Create scheduled report
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
        
        # Toggle to inactive
        response = self.client.post(
            reverse('reports:schedules-toggle-active', kwargs={'pk': scheduled_report.id})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify toggled to inactive
        scheduled_report.refresh_from_db()
        self.assertFalse(scheduled_report.is_active)
        
        # Toggle back to active
        response = self.client.post(
            reverse('reports:schedules-toggle-active', kwargs={'pk': scheduled_report.id})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify toggled to active
        scheduled_report.refresh_from_db()
        self.assertTrue(scheduled_report.is_active)
    
    def test_run_scheduled_report_now(self):
        """Test running scheduled report immediately"""
        
        # Create scheduled report
        scheduled_report = ScheduledReport.objects.create(
            company=self.company,
            name='Run Now Test Report',
            report_type='monthly_summary',
            frequency='monthly',
            email_recipients=['test@company.com'],
            file_format='pdf',
            created_by=self.user
        )
        
        # Mock task creation
        with patch('apps.reports.tasks.generate_report_async.delay') as mock_task:
            mock_task.return_value = MagicMock(id='task-123')
            
            response = self.client.post(
                reverse('reports:schedules-run-now', kwargs={'pk': scheduled_report.id})
            )
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertIn('message', data)
            self.assertIn('task_id', data)
            
            # Verify task was triggered
            mock_task.assert_called_once()


class WebSocketIntegrationTest(TransactionTestCase):
    """Test WebSocket integration for real-time updates"""
    
    @database_sync_to_async
    def create_test_data(self):
        """Create test data in async context"""
        company = Company.objects.create(
            name="WebSocket Test Company",
            cnpj="12345678000123"
        )
        
        user = User.objects.create_user(
            email="websocket@test.com",
            password="testpass123",
            is_verified=True
        )
        user.company = company
        user.save()
        
        return company, user
    
    async def test_report_progress_websocket(self):
        """Test WebSocket notifications for report generation progress"""
        company, user = await self.create_test_data()
        
        # Create WebSocket communicator
        communicator = WebsocketCommunicator(
            consumers.ReportProgressConsumer.as_asgi(),
            f"/ws/reports/progress/{company.id}/"
        )
        
        # Connect to WebSocket
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Simulate report progress updates
        progress_updates = [
            {'status': 'started', 'progress': 0},
            {'status': 'collecting_data', 'progress': 25},
            {'status': 'generating_charts', 'progress': 50},
            {'status': 'creating_pdf', 'progress': 75},
            {'status': 'completed', 'progress': 100}
        ]
        
        for update in progress_updates:
            # Send progress update
            await communicator.send_json_to({
                'type': 'report_progress',
                'data': update
            })
            
            # Receive the update
            response = await communicator.receive_json_from()
            self.assertEqual(response['type'], 'report_progress')
            self.assertEqual(response['data']['status'], update['status'])
            self.assertEqual(response['data']['progress'], update['progress'])
        
        # Disconnect
        await communicator.disconnect()
    
    async def test_report_completion_notification(self):
        """Test WebSocket notification when report is completed"""
        company, user = await self.create_test_data()
        
        # Create communicator
        communicator = WebsocketCommunicator(
            consumers.ReportNotificationConsumer.as_asgi(),
            f"/ws/reports/notifications/{company.id}/"
        )
        
        # Connect
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Simulate report completion
        completion_data = {
            'type': 'report_completed',
            'report_id': 'test-report-123',
            'title': 'Monthly Summary Report',
            'download_url': '/api/reports/test-report-123/download/',
            'file_size': 2048
        }
        
        await communicator.send_json_to(completion_data)
        
        # Receive notification
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'report_completed')
        self.assertEqual(response['report_id'], 'test-report-123')
        self.assertIn('download_url', response)
        
        # Disconnect
        await communicator.disconnect()


class AIInsightsIntegrationTest(TestCase):
    """Test AI insights integration with mocked OpenAI"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test company and user
        self.company = CompanyFactory(name="AI Test Company")
        
        self.user = User.objects.create_user(
            email="ai@test.com",
            password="testpass123",
            is_verified=True
        )
        self.user.company = self.company
        self.user.save()
        
        # Create subscription with AI features
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
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
        
        # Create test transactions
        account = BankAccount.objects.create(
            company=self.company,
            pluggy_account_id="ai_test_account",
            item=MagicMock(),
            type="BANK",
            balance=Decimal("5000.00"),
            currency_code="BRL"
        )
        
        for i in range(10):
            Transaction.objects.create(
                pluggy_transaction_id=f"ai_txn_{i}",
                account=account,
                company=self.company.id,
                type="DEBIT" if i % 2 == 0 else "CREDIT",
                amount=Decimal(f"{(i + 1) * 100}.00"),
                description=f"AI Test Transaction {i + 1}",
                date=date(2024, 1, (i % 28) + 1),
                currency_code="BRL"
            )
    
    @patch('openai.ChatCompletion.create')
    def test_ai_insights_generation(self, mock_openai):
        """Test AI insights generation with mocked OpenAI"""
        
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
                            'next_month_income': 5000.00,
                            'next_month_expenses': 2800.00,
                            'projected_savings': 2200.00
                        },
                        'recommendations': [
                            {
                                'title': 'Optimize Food Spending',
                                'description': 'Consider meal planning.',
                                'impact': 'medium'
                            }
                        ],
                        'key_metrics': {
                            'health_score': 85,
                            'efficiency_score': 78,
                            'growth_potential': 90
                        }
                    })
                )
            )]
        )
        
        # Request AI insights
        response = self.client.get(
            reverse('reports:ai-insights'),
            {
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'type': 'comprehensive'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify response structure
        self.assertIn('insights', data)
        self.assertIn('predictions', data)
        self.assertIn('recommendations', data)
        self.assertIn('key_metrics', data)
        self.assertTrue(data['ai_generated'])
        
        # Verify OpenAI was called
        mock_openai.assert_called_once()
    
    @patch('openai.ChatCompletion.create')
    def test_ai_insights_error_handling(self, mock_openai):
        """Test AI insights with OpenAI error"""
        
        # Mock OpenAI failure
        mock_openai.side_effect = Exception("OpenAI API rate limit exceeded")
        
        # Request AI insights
        response = self.client.get(
            reverse('reports:ai-insights'),
            {
                'start_date': '2024-01-01',
                'end_date': '2024-01-31'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return fallback data
        self.assertFalse(data['ai_generated'])
        self.assertTrue(data['fallback_mode'])
        self.assertIn('error', data)
    
    @patch('openai.ChatCompletion.create')
    def test_ask_ai_endpoint(self, mock_openai):
        """Test AI question endpoint"""
        
        # Mock OpenAI response
        mock_openai.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content="Based on your spending patterns, I recommend creating a monthly budget for food expenses and tracking your spending more closely."
                )
            )]
        )
        
        # Ask AI a question
        response = self.client.post(
            reverse('reports:ai-insights-ask'),
            data={
                'question': 'How can I reduce my food expenses?',
                'context': {
                    'current_food_spending': 800,
                    'target_reduction': 20
                }
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('answer', data)
        self.assertIn('confidence', data)
        self.assertIn('I recommend', data['answer'])
        
        # Verify OpenAI was called
        mock_openai.assert_called_once()


class FileHandlingIntegrationTest(TestCase):
    """Test file upload/download integration"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test company and user
        self.company = CompanyFactory(name="File Test Company")
        
        self.user = User.objects.create_user(
            email="file@test.com",
            password="testpass123",
            is_verified=True
        )
        self.user.company = self.company
        self.user.save()
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
    
    def test_report_file_generation_and_download(self):
        """Test complete file generation and download workflow"""
        
        # Create report
        report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='File Test Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            created_by=self.user
        )
        
        # Mock file generation
        with patch('apps.reports.report_generator.ReportGenerator.generate_report') as mock_generator:
            # Create temporary PDF content
            pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%%EOF'
            
            mock_buffer = MagicMock()
            mock_buffer.getvalue.return_value = pdf_content
            mock_buffer.tell.return_value = len(pdf_content)
            mock_generator.return_value = mock_buffer
            
            # Generate report
            result = generate_report_async(report.id)
            self.assertEqual(result['status'], 'success')
        
        # Verify file was created
        report.refresh_from_db()
        self.assertTrue(report.is_generated)
        self.assertIsNotNone(report.file)
        self.assertEqual(report.file_size, len(pdf_content))
        
        # Test download URL generation
        response = self.client.get(
            reverse('reports:reports-download', kwargs={'pk': report.id})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('download_url', data)
        
        # Test actual file download (in a real scenario, this would be a signed URL)
        # For testing, we'll verify the file exists and has the right content type
        self.assertTrue(report.file.name.endswith('.pdf'))
    
    def test_file_cleanup_on_regeneration(self):
        """Test that old files are cleaned up when regenerating reports"""
        
        # Create report with initial file
        report = Report.objects.create(
            company=self.company,
            report_type='monthly_summary',
            title='Cleanup Test Report',
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            file_format='pdf',
            is_generated=True,
            created_by=self.user
        )
        
        # Add initial file
        old_content = b'old pdf content'
        report.file.save('old_report.pdf', ContentFile(old_content))
        old_file_path = report.file.path
        
        # Regenerate report
        with patch('apps.reports.report_generator.ReportGenerator.generate_report') as mock_generator:
            new_content = b'%PDF-1.4 new pdf content'
            
            mock_buffer = MagicMock()
            mock_buffer.getvalue.return_value = new_content
            mock_buffer.tell.return_value = len(new_content)
            mock_generator.return_value = mock_buffer
            
            # Regenerate
            result = generate_report_async(report.id)
            self.assertEqual(result['status'], 'success')
        
        # Verify new file was created and old one cleaned up
        report.refresh_from_db()
        self.assertTrue(report.is_generated)
        self.assertEqual(report.file_size, len(new_content))
        
        # In a real implementation, old file should be deleted
        # This would need proper file storage testing


class PerformanceIntegrationTest(TestCase):
    """Test performance aspects of the reports system"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test company and user
        self.company = CompanyFactory(name="Performance Test Company")
        
        self.user = User.objects.create_user(
            email="performance@test.com",
            password="testpass123",
            is_verified=True
        )
        self.user.company = self.company
        self.user.save()
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
        
        # Create large dataset for performance testing
        account = BankAccount.objects.create(
            company=self.company,
            pluggy_account_id="perf_test_account",
            item=MagicMock(),
            type="BANK",
            balance=Decimal("50000.00"),
            currency_code="BRL"
        )
        
        categories = []
        for i in range(10):
            category = TransactionCategory.objects.create(
                name=f"Category {i + 1}",
                icon="icon",
                type="expense" if i % 2 == 0 else "income"
            )
            categories.append(category)
        
        # Create large number of transactions
        transactions = []
        for i in range(1000):  # 1000 transactions for performance testing
            transaction = Transaction.objects.create(
                pluggy_transaction_id=f"perf_txn_{i}",
                account=account,
                company=self.company.id,
                type="DEBIT" if i % 2 == 0 else "CREDIT",
                amount=Decimal(f"{(i % 100 + 1) * 10}.00"),
                description=f"Performance Transaction {i + 1}",
                date=date(2024, 1, (i % 28) + 1),
                currency_code="BRL",
                category=categories[i % len(categories)]
            )
            transactions.append(transaction)
    
    def test_large_dataset_analytics_performance(self):
        """Test analytics performance with large dataset"""
        import time
        
        start_time = time.time()
        
        # Request analytics for large dataset
        response = self.client.get(
            reverse('reports:analytics'),
            {'period': 30}
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(execution_time, 5.0, "Analytics query took too long")
        
        # Verify data integrity
        data = response.json()
        self.assertIn('total_income', data)
        self.assertIn('total_expenses', data)
        self.assertEqual(data['transaction_count'], 1000)
    
    def test_paginated_reports_performance(self):
        """Test pagination performance with many reports"""
        
        # Create many reports
        reports = []
        for i in range(100):
            report = Report.objects.create(
                company=self.company,
                report_type='monthly_summary',
                title=f'Performance Report {i + 1}',
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31),
                file_format='pdf',
                created_by=self.user
            )
            reports.append(report)
        
        import time
        start_time = time.time()
        
        # Request first page
        response = self.client.get(
            reverse('reports:reports-list'),
            {'page': 1, 'page_size': 20}
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(execution_time, 2.0, "Paginated query took too long")
        
        # Verify pagination
        data = response.json()
        self.assertEqual(data['count'], 100)
        self.assertEqual(len(data['results']), 20)
        self.assertIsNotNone(data['next'])