"""
E2E tests for complete reporting workflows
"""
from decimal import Decimal
from datetime import date, timedelta, datetime
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import json

from apps.authentication.models import User
from apps.companies.models import Company, CompanyUser, SubscriptionPlan
from apps.banking.models import BankProvider, BankAccount, Transaction, TransactionCategory, Budget
from apps.reports.models import Report, ReportSchedule, ReportTemplate
from apps.notifications.models import Notification, NotificationTemplate
from apps.categories.models import CategoryRule


class TestCompleteReportingWorkflow(TransactionTestCase):
    """
    Test complete reporting workflows including:
    - Report generation for different types
    - Scheduled reports
    - Report templates
    - Export functionality
    - Report sharing
    """
    
    def setUp(self):
        self.client = APIClient()
        self._create_test_data()
        self._create_transaction_data()
    
    def _create_test_data(self):
        """Create initial test data"""
        # Create user and company
        self.user = User.objects.create_user(
            username='report_user',
            email='reports@test.com',
            password='TestPass123!',
            first_name='Report',
            last_name='User'
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name='Enterprise',
            slug='enterprise',
            plan_type='enterprise',
            price_monthly=299.00,
            price_yearly=2990.00,
            has_advanced_reports=True
        )
        
        self.company = Company.objects.create(
            name='Report Test Company',
            cnpj='12345678901234',
            owner=self.user,
            subscription_plan=self.plan,
            subscription_status='active',
            business_sector='retail'
        )
        
        CompanyUser.objects.create(
            company=self.company,
            user=self.user,
            role='owner'
        )
        
        # Create additional users for sharing
        self.accountant = User.objects.create_user(
            username='accountant',
            email='accountant@test.com',
            password='TestPass123!',
            first_name='Accountant',
            last_name='User'
        )
        
        CompanyUser.objects.create(
            company=self.company,
            user=self.accountant,
            role='admin'
        )
        
        # Create bank and categories
        self.bank_provider = BankProvider.objects.create(
            name='Test Bank',
            code='001'
        )
        
        self._create_categories()
        
        # Create notification templates
        NotificationTemplate.objects.create(
            name='report_ready',
            subject='Seu relatório está pronto',
            body='O relatório {report_name} foi gerado com sucesso.',
            notification_type='info'
        )
        
        # Authenticate
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    
    def _create_categories(self):
        """Create transaction categories"""
        self.categories = {}
        
        # Income categories
        self.categories['sales'] = TransactionCategory.objects.create(
            slug='sales',
            name='Vendas',
            category_type='income'
        )
        
        self.categories['services'] = TransactionCategory.objects.create(
            slug='services', 
            name='Serviços',
            category_type='income'
        )
        
        # Expense categories
        self.categories['cogs'] = TransactionCategory.objects.create(
            slug='cogs',
            name='Custo das Vendas',
            category_type='expense'
        )
        
        self.categories['operational'] = TransactionCategory.objects.create(
            slug='operational',
            name='Despesas Operacionais',
            category_type='expense'
        )
        
        self.categories['marketing'] = TransactionCategory.objects.create(
            slug='marketing',
            name='Marketing',
            category_type='expense'
        )
        
        self.categories['payroll'] = TransactionCategory.objects.create(
            slug='payroll',
            name='Folha de Pagamento',
            category_type='expense'
        )
    
    def _create_transaction_data(self):
        """Create comprehensive transaction data for reporting"""
        # Create bank account
        self.account = BankAccount.objects.create(
            company=self.company,
            bank_provider=self.bank_provider,
            account_type='checking',
            agency='0001',
            account_number='123456',
            current_balance=Decimal('50000.00')
        )
        
        # Create 3 months of transaction data
        today = date.today()
        
        # Pattern: Regular business with seasonal variation
        for days_ago in range(90):
            tx_date = today - timedelta(days=days_ago)
            
            # Daily sales (higher on weekends)
            if tx_date.weekday() in [5, 6]:  # Weekend
                sales_amount = Decimal('8000.00')
            else:
                sales_amount = Decimal('5000.00')
            
            Transaction.objects.create(
                account=self.account,
                company=self.company,
                transaction_type='credit',
                amount=sales_amount,
                description=f'Vendas do dia {tx_date}',
                transaction_date=tx_date,
                category=self.categories['sales']
            )
            
            # Service revenue (monthly contracts)
            if tx_date.day == 1:
                Transaction.objects.create(
                    account=self.account,
                    company=self.company,
                    transaction_type='credit',
                    amount=Decimal('15000.00'),
                    description='Contratos de Serviço',
                    transaction_date=tx_date,
                    category=self.categories['services']
                )
            
            # Daily operational expenses
            Transaction.objects.create(
                account=self.account,
                company=self.company,
                transaction_type='debit',
                amount=Decimal('1500.00'),
                description='Despesas operacionais',
                transaction_date=tx_date,
                category=self.categories['operational']
            )
            
            # COGS (60% of sales)
            Transaction.objects.create(
                account=self.account,
                company=self.company,
                transaction_type='debit',
                amount=sales_amount * Decimal('0.6'),
                description='Custo das mercadorias',
                transaction_date=tx_date,
                category=self.categories['cogs']
            )
            
            # Weekly marketing expenses
            if tx_date.weekday() == 0:  # Monday
                Transaction.objects.create(
                    account=self.account,
                    company=self.company,
                    transaction_type='debit',
                    amount=Decimal('2000.00'),
                    description='Campanhas de Marketing',
                    transaction_date=tx_date,
                    category=self.categories['marketing']
                )
            
            # Monthly payroll
            if tx_date.day == 5:
                Transaction.objects.create(
                    account=self.account,
                    company=self.company,
                    transaction_type='debit',
                    amount=Decimal('45000.00'),
                    description='Folha de Pagamento',
                    transaction_date=tx_date,
                    category=self.categories['payroll']
                )
        
        # Create budgets for comparison
        self.budgets = []
        for category_key, category in self.categories.items():
            if category.category_type == 'expense':
                if category_key == 'payroll':
                    amount = Decimal('45000.00')
                elif category_key == 'cogs':
                    amount = Decimal('120000.00')
                elif category_key == 'marketing':
                    amount = Decimal('10000.00')
                else:
                    amount = Decimal('50000.00')
                
                budget = Budget.objects.create(
                    company=self.company,
                    name=f'Orçamento {category.name}',
                    category=category,
                    amount=amount,
                    period='monthly',
                    alert_threshold=80,
                    created_by=self.user
                )
                self.budgets.append(budget)
    
    def test_comprehensive_reporting_workflow(self):
        """
        Test complete reporting workflow from generation to sharing
        """
        print("\n=== Comprehensive Reporting Workflow ===")
        
        # Step 1: Generate Cash Flow Report
        print("\n--- Step 1: Cash Flow Report ---")
        response = self.client.post(reverse('reports:report-list'), {
            'report_type': 'cash_flow',
            'period': 'monthly',
            'start_date': (date.today() - timedelta(days=30)).isoformat(),
            'end_date': date.today().isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cash_flow_report = Report.objects.get(pk=response.data['id'])
        
        # Get cash flow data
        response = self.client.get(
            reverse('reports:cash-flow-data', kwargs={'report_id': cash_flow_report.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        cash_flow_data = response.data
        self.assertIn('daily_flow', cash_flow_data)
        self.assertIn('summary', cash_flow_data)
        self.assertIn('projections', cash_flow_data)
        
        print(f"Cash Flow Summary:")
        print(f"  Total Income: R$ {cash_flow_data['summary']['total_income']}")
        print(f"  Total Expenses: R$ {cash_flow_data['summary']['total_expenses']}")
        print(f"  Net Flow: R$ {cash_flow_data['summary']['net_flow']}")
        
        # Step 2: Generate Income vs Expenses Report
        print("\n--- Step 2: Income vs Expenses Report ---")
        response = self.client.post(reverse('reports:report-list'), {
            'report_type': 'income_vs_expenses',
            'period': 'quarterly',
            'include_comparison': True
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        income_report = Report.objects.get(pk=response.data['id'])
        
        # Get income vs expenses data
        response = self.client.get(
            reverse('reports:income-vs-expenses', kwargs={'report_id': income_report.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        income_data = response.data
        self.assertIn('monthly_data', income_data)
        self.assertIn('category_breakdown', income_data)
        self.assertIn('profit_margin', income_data)
        
        # Step 3: Generate Category Analysis Report
        print("\n--- Step 3: Category Analysis Report ---")
        response = self.client.post(reverse('reports:report-list'), {
            'report_type': 'category_spending',
            'period': 'monthly',
            'filters': {
                'categories': [self.categories['marketing'].id, self.categories['payroll'].id]
            }
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        category_report = Report.objects.get(pk=response.data['id'])
        
        # Get category spending data
        response = self.client.get(
            reverse('reports:category-spending', kwargs={'report_id': category_report.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        category_data = response.data
        self.assertIn('category_breakdown', category_data)
        self.assertIn('trends', category_data)
        self.assertIn('budget_comparison', category_data)
        
        # Step 4: Create Custom Report Template
        print("\n--- Step 4: Custom Report Template ---")
        template_data = {
            'name': 'Relatório Executivo Mensal',
            'report_type': 'custom',
            'configuration': {
                'sections': [
                    {
                        'type': 'summary',
                        'title': 'Resumo Executivo',
                        'metrics': ['revenue', 'expenses', 'profit', 'margin']
                    },
                    {
                        'type': 'chart',
                        'title': 'Evolução Mensal',
                        'chart_type': 'line',
                        'data': ['income', 'expenses']
                    },
                    {
                        'type': 'table',
                        'title': 'Top 5 Categorias',
                        'data': 'top_categories'
                    }
                ]
            },
            'is_active': True
        }
        
        response = self.client.post(
            reverse('reports:template-list'),
            template_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        template = ReportTemplate.objects.get(pk=response.data['id'])
        
        # Generate report from template
        response = self.client.post(reverse('reports:report-list'), {
            'template_id': template.id,
            'period': 'monthly'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        custom_report = Report.objects.get(pk=response.data['id'])
        
        # Step 5: Schedule Recurring Reports
        print("\n--- Step 5: Schedule Recurring Reports ---")
        schedule_data = {
            'name': 'Relatório Semanal de Vendas',
            'report_config': {
                'report_type': 'cash_flow',
                'period': 'weekly',
                'filters': {
                    'categories': [self.categories['sales'].id]
                }
            },
            'frequency': 'weekly',
            'day_of_week': 1,  # Monday
            'time_of_day': '08:00',
            'recipients': [self.user.email, self.accountant.email],
            'is_active': True
        }
        
        response = self.client.post(
            reverse('reports:schedule-list'),
            schedule_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        schedule = ReportSchedule.objects.get(pk=response.data['id'])
        
        # Test manual execution of scheduled report
        response = self.client.post(
            reverse('reports:schedule-execute', kwargs={'pk': schedule.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 6: Export Reports
        print("\n--- Step 6: Export Reports ---")
        
        # Export to PDF
        with patch('apps.reports.services.ReportExportService.export_to_pdf') as mock_pdf:
            mock_pdf.return_value = b'PDF content'
            
            response = self.client.get(
                reverse('reports:report-export', kwargs={'pk': cash_flow_report.id}),
                {'format': 'pdf'}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response['Content-Type'], 'application/pdf')
        
        # Export to Excel
        with patch('apps.reports.services.ReportExportService.export_to_excel') as mock_excel:
            mock_excel.return_value = b'Excel content'
            
            response = self.client.get(
                reverse('reports:report-export', kwargs={'pk': income_report.id}),
                {'format': 'excel'}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response['Content-Type'],
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        # Step 7: Share Reports
        print("\n--- Step 7: Share Reports ---")
        
        # Share with accountant
        with patch('apps.notifications.email_service.EmailService.send_report_share_email') as mock_email:
            response = self.client.post(
                reverse('reports:report-share', kwargs={'pk': cash_flow_report.id}),
                {
                    'recipient_email': self.accountant.email,
                    'message': 'Segue o relatório de fluxo de caixa para análise.',
                    'allow_export': True
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_email.assert_called_once()
        
        # Step 8: Analytics Dashboard
        print("\n--- Step 8: Analytics Dashboard ---")
        response = self.client.get(reverse('reports:dashboard-stats'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        dashboard_data = response.data
        self.assertIn('kpis', dashboard_data)
        self.assertIn('trends', dashboard_data)
        self.assertIn('alerts', dashboard_data)
        
        print(f"\nDashboard KPIs:")
        for kpi, value in dashboard_data['kpis'].items():
            print(f"  {kpi}: {value}")
        
        # Step 9: Comparative Analysis
        print("\n--- Step 9: Comparative Analysis ---")
        response = self.client.post(reverse('reports:comparative-analysis'), {
            'period_1': {
                'start_date': (date.today() - timedelta(days=60)).isoformat(),
                'end_date': (date.today() - timedelta(days=30)).isoformat()
            },
            'period_2': {
                'start_date': (date.today() - timedelta(days=30)).isoformat(),
                'end_date': date.today().isoformat()
            },
            'metrics': ['revenue', 'expenses', 'profit_margin', 'category_distribution']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        comparison_data = response.data
        self.assertIn('period_1_data', comparison_data)
        self.assertIn('period_2_data', comparison_data)
        self.assertIn('variance', comparison_data)
        self.assertIn('insights', comparison_data)
        
        # Step 10: Check Report History
        print("\n--- Step 10: Report History ---")
        response = self.client.get(reverse('reports:report-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        reports = response.data['results']
        self.assertGreaterEqual(len(reports), 5)  # All reports we created
        
        print(f"\nGenerated Reports:")
        for report in reports:
            print(f"  - {report['report_type']}: {report['status']} ({report['created_at']})")
        
        print("\n=== Reporting Workflow Complete! ===")
        print(f"Total Reports Generated: {Report.objects.filter(company=self.company).count()}")
        print(f"Active Schedules: {ReportSchedule.objects.filter(company=self.company, is_active=True).count()}")
        print(f"Report Templates: {ReportTemplate.objects.filter(company=self.company).count()}")


class TestReportErrorHandlingAndRecovery(TransactionTestCase):
    """
    Test report generation error handling and recovery
    """
    
    def setUp(self):
        self.client = APIClient()
        self._create_minimal_data()
    
    def _create_minimal_data(self):
        """Create minimal test data"""
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.plan = SubscriptionPlan.objects.create(
            name='Pro',
            slug='pro',
            plan_type='pro',
            price_monthly=99.00,
            price_yearly=990.00
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            owner=self.user,
            subscription_plan=self.plan
        )
        
        CompanyUser.objects.create(
            company=self.company,
            user=self.user,
            role='owner'
        )
        
        # Authenticate
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    
    def test_report_generation_with_no_data(self):
        """
        Test report generation when there's no transaction data
        """
        print("\n=== Report Generation with No Data ===")
        
        # Try to generate report without any transactions
        response = self.client.post(reverse('reports:report-list'), {
            'report_type': 'cash_flow',
            'period': 'monthly'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        report = Report.objects.get(pk=response.data['id'])
        
        # Get report data - should return empty structure
        response = self.client.get(
            reverse('reports:cash-flow-data', kwargs={'report_id': report.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['summary']['total_income'], '0.00')
        self.assertEqual(data['summary']['total_expenses'], '0.00')
        
        print("✓ Report generated successfully with no data")
    
    def test_report_generation_failure_recovery(self):
        """
        Test recovery from report generation failures
        """
        print("\n=== Report Generation Failure Recovery ===")
        
        # Create report that might fail
        with patch('apps.reports.tasks.generate_report_task.delay') as mock_task:
            mock_task.side_effect = Exception("Task queue unavailable")
            
            response = self.client.post(reverse('reports:report-list'), {
                'report_type': 'income_vs_expenses',
                'period': 'monthly'
            })
            
            # Should still create report record
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            report = Report.objects.get(pk=response.data['id'])
            self.assertEqual(report.status, 'pending')
        
        # Retry generation
        response = self.client.post(
            reverse('reports:report-retry', kwargs={'pk': report.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        print("✓ Report generation retry successful")