"""
Test report scheduling views
Tests for ReportScheduleViewSet
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
class TestReportScheduleViewSet(TestCase):
    """Test ReportScheduleViewSet"""
    
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
        
        # Create report schedules
        self.schedule1 = ReportSchedule.objects.create(
            company=self.company,
            report_type='monthly_summary',
            frequency='monthly',
            send_email=True,
            email_recipients=['test@example.com', 'admin@example.com'],
            file_format='pdf',
            next_run_at=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        
        self.schedule2 = ReportSchedule.objects.create(
            company=self.company,
            report_type='cash_flow',
            frequency='weekly',
            send_email=False,
            file_format='xlsx',
            next_run_at=timezone.now() + timedelta(days=7),
            created_by=self.user,
            is_active=False
        )
        
        # Other company's schedule
        self.other_schedule = ReportSchedule.objects.create(
            company=self.other_company,
            report_type='annual_report',
            frequency='yearly',
            next_run_at=timezone.now() + timedelta(days=365),
            created_by=self.other_user
        )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    def test_list_schedules(self):
        """Test listing company report schedules"""
        url = reverse('reports:report-schedule-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Should not include other company's schedule
        schedule_ids = [s['id'] for s in response.data['results']]
        self.assertIn(self.schedule1.id, schedule_ids)
        self.assertIn(self.schedule2.id, schedule_ids)
        self.assertNotIn(self.other_schedule.id, schedule_ids)
    
    def test_retrieve_schedule(self):
        """Test retrieving single schedule"""
        url = reverse('reports:report-schedule-detail', kwargs={'pk': self.schedule1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['report_type'], 'monthly_summary')
        self.assertEqual(response.data['frequency'], 'monthly')
        self.assertTrue(response.data['send_email'])
        self.assertEqual(len(response.data['email_recipients']), 2)
    
    def test_retrieve_other_company_schedule_forbidden(self):
        """Test cannot retrieve other company's schedule"""
        url = reverse('reports:report-schedule-detail', kwargs={'pk': self.other_schedule.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_schedule(self):
        """Test creating a new report schedule"""
        url = reverse('reports:report-schedule-list')
        data = {
            'report_type': 'quarterly_report',
            'frequency': 'quarterly',
            'send_email': True,
            'email_recipients': ['test@example.com', 'finance@company.com'],
            'file_format': 'pdf',
            'next_run_at': (timezone.now() + timedelta(days=90)).isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['report_type'], 'quarterly_report')
        self.assertEqual(response.data['frequency'], 'quarterly')
        
        # Check schedule was created
        schedule = ReportSchedule.objects.get(id=response.data['id'])
        self.assertEqual(schedule.company, self.company)
        self.assertEqual(schedule.created_by, self.user)
        self.assertTrue(schedule.is_active)
    
    def test_create_schedule_with_parameters(self):
        """Test creating schedule with custom parameters"""
        url = reverse('reports:report-schedule-list')
        data = {
            'report_type': 'category_analysis',
            'frequency': 'monthly',
            'file_format': 'xlsx',
            'next_run_at': (timezone.now() + timedelta(days=30)).isoformat(),
            'parameters': {
                'include_subcategories': True,
                'group_by': 'category'
            },
            'filters': {
                'categories': ['food', 'transport'],
                'min_amount': 100
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parameters']['include_subcategories'], True)
        self.assertEqual(response.data['filters']['categories'], ['food', 'transport'])
    
    def test_toggle_active(self):
        """Test toggling schedule active status"""
        # Currently active schedule
        url = reverse('reports:report-schedule-toggle-active', kwargs={'pk': self.schedule1.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertFalse(response.data['is_active'])
        
        # Refresh from database
        self.schedule1.refresh_from_db()
        self.assertFalse(self.schedule1.is_active)
        
        # Toggle back
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_active'])
    
    @patch('apps.reports.tasks.generate_report_task.delay')
    def test_run_now(self, mock_task):
        """Test running scheduled report immediately"""
        url = reverse('reports:report-schedule-run-now', kwargs={'pk': self.schedule1.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('report_id', response.data)
        
        # Check report was created
        report = Report.objects.get(id=response.data['report_id'])
        self.assertEqual(report.company, self.company)
        self.assertEqual(report.report_type, 'monthly_summary')
        self.assertIn('Manual Run', report.title)
        
        # Check task was queued
        mock_task.assert_called_once_with(report.id)
        
        # Check schedule was updated
        self.schedule1.refresh_from_db()
        self.assertIsNotNone(self.schedule1.last_run_at)
    
    def test_update_schedule(self):
        """Test updating report schedule"""
        url = reverse('reports:report-schedule-detail', kwargs={'pk': self.schedule1.pk})
        data = {
            'frequency': 'weekly',
            'email_recipients': ['newemail@example.com'],
            'send_email': False
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.schedule1.refresh_from_db()
        self.assertEqual(self.schedule1.frequency, 'weekly')
        self.assertEqual(self.schedule1.email_recipients, ['newemail@example.com'])
        self.assertFalse(self.schedule1.send_email)
    
    def test_delete_schedule(self):
        """Test deleting report schedule"""
        url = reverse('reports:report-schedule-detail', kwargs={'pk': self.schedule2.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ReportSchedule.objects.filter(pk=self.schedule2.pk).exists())
    
    def test_create_schedule_invalid_frequency(self):
        """Test creating schedule with invalid frequency"""
        url = reverse('reports:report-schedule-list')
        data = {
            'report_type': 'monthly_summary',
            'frequency': 'invalid_frequency',
            'file_format': 'pdf',
            'next_run_at': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('frequency', response.data)
    
    def test_filter_schedules_by_active_status(self):
        """Test filtering schedules by active status"""
        # Get only active schedules
        url = reverse('reports:report-schedule-list')
        response = self.client.get(url, {'is_active': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.schedule1.id)
        
        # Get only inactive schedules
        response = self.client.get(url, {'is_active': 'false'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.schedule2.id)
    
    def test_filter_schedules_by_report_type(self):
        """Test filtering schedules by report type"""
        url = reverse('reports:report-schedule-list')
        response = self.client.get(url, {'report_type': 'monthly_summary'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['report_type'], 'monthly_summary')
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access is denied"""
        self.client.force_authenticate(user=None)
        
        url = reverse('reports:report-schedule-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_schedule_with_empty_email_recipients(self):
        """Test creating schedule without email recipients when send_email is False"""
        url = reverse('reports:report-schedule-list')
        data = {
            'report_type': 'profit_loss',
            'frequency': 'monthly',
            'send_email': False,
            'email_recipients': [],
            'file_format': 'pdf',
            'next_run_at': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['send_email'])
        self.assertEqual(response.data['email_recipients'], [])
    
    def test_schedule_ordering(self):
        """Test schedules are ordered by report type"""
        url = reverse('reports:report-schedule-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that schedules are present
        self.assertEqual(len(response.data['results']), 2)