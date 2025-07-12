"""
Reports app views
Financial reporting and analytics
"""
import logging
from decimal import Decimal
import math
from typing import Dict, Any, List
from datetime import datetime, timedelta

from collections import defaultdict
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Q, Sum, Avg, Max, Min
from django.http import FileResponse, Http404
from django.utils import timezone

from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone as django_timezone

from apps.banking.models import BankAccount, Transaction, TransactionCategory
from .models import Report, ReportSchedule, ReportTemplate
from .serializers import (
    ReportScheduleSerializer,
    ReportSerializer,
    ReportTemplateSerializer,
)
from .tasks import generate_report_task
from .ai_service import enhanced_ai_service
from .ai_tasks import generate_company_ai_insights
from django.utils import timezone as django_timezone
logger = logging.getLogger(__name__)


# Adicionar estas correções ao backend/apps/reports/views.py

class ReportViewSet(viewsets.ModelViewSet):
    """
    Report management viewset - CORRIGIDO
    """
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Report.objects.filter(
            company=self.request.user.company
        ).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Generate a new report with proper validation"""
        report_type = request.data.get('report_type')
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        file_format = request.data.get('file_format', 'pdf')  # Default to PDF
        
        # Validação melhorada
        if not all([report_type, period_start, period_end]):
            return Response({
                'error': 'report_type, period_start, and period_end are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar datas
        try:
            start_date = datetime.strptime(period_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(period_end, '%Y-%m-%d').date()
            
            if start_date > end_date:
                return Response({
                    'error': 'Start date must be before end date'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if end_date > timezone.now().date():
                return Response({
                    'error': 'End date cannot be in the future'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ValueError:
            return Response({
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar tipo de relatório
        valid_types = [choice[0] for choice in Report.REPORT_TYPES]
        if report_type not in valid_types:
            return Response({
                'error': f'Invalid report type. Valid types: {", ".join(valid_types)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Criar relatório com todos os campos necessários
        report = Report.objects.create(
            company=request.user.company,
            report_type=report_type,
            title=request.data.get('title', f'{report_type} Report - {period_start} to {period_end}'),
            description=request.data.get('description', ''),
            period_start=start_date,
            period_end=end_date,
            file_format=file_format,
            parameters=request.data.get('parameters', {}),
            filters=request.data.get('filters', {}),
            created_by=request.user
        )
        
        # Queue report generation
        generate_report_task.delay(report.id)
        
        serializer = self.get_serializer(report)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get reports summary statistics with proper data structure"""
        company = request.user.company
        reports = self.get_queryset()
        
        # Adicionar dados agregados úteis
        from django.db.models import Count, Q
        from datetime import timedelta
        
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        
        summary_data = {
            'total_reports': reports.count(),
            'reports_generated': reports.filter(is_generated=True).count(),
            'reports_pending': reports.filter(is_generated=False, error_message='').count(),
            'reports_failed': reports.filter(is_generated=False).exclude(error_message='').count(),
            'reports_by_type': list(reports.values('report_type').annotate(
                count=Count('id'),
                label=Count('id')  # Para o frontend
            )),
            'recent_reports': ReportSerializer(
                reports.select_related('created_by')[:10], 
                many=True
            ).data,
            'reports_last_30_days': reports.filter(created_at__gte=last_30_days).count(),
            'most_used_type': reports.values('report_type').annotate(
                count=Count('id')
            ).order_by('-count').first()
        }
        
        return Response(summary_data)


class ReportScheduleViewSet(viewsets.ModelViewSet):
    """
    Report schedule management - CORRIGIDO
    """
    serializer_class = ReportScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_active', 'report_type', 'frequency']
    ordering_fields = ['report_type', 'frequency', 'next_run_at']
    ordering = ['report_type']
    
    def get_queryset(self):
        return ReportSchedule.objects.filter(
            company=self.request.user.company
        ).select_related('created_by')
    
    def create(self, request, *args, **kwargs):
        """Create a new scheduled report with validation"""
        
        # Validar campos obrigatórios
        required_fields = ['name', 'report_type', 'frequency', 'email_recipients']
        missing_fields = [field for field in required_fields if not request.data.get(field)]
        
        if missing_fields:
            return Response({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar email_recipients
        email_recipients = request.data.get('email_recipients', [])
        if isinstance(email_recipients, str):
            email_recipients = [email.strip() for email in email_recipients.split(',')]
        
        if not email_recipients:
            return Response({
                'error': 'At least one email recipient is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar emails
        import re
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        invalid_emails = [email for email in email_recipients if not re.match(email_pattern, email)]
        
        if invalid_emails:
            return Response({
                'error': f'Invalid email addresses: {", ".join(invalid_emails)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calcular next_run_at baseado na frequência
        frequency = request.data.get('frequency', 'monthly')
        now = timezone.now()
        
        frequency_deltas = {
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
            'monthly': timedelta(days=30),
            'quarterly': timedelta(days=90),
            'yearly': timedelta(days=365)
        }
        
        next_run = now + frequency_deltas.get(frequency, timedelta(days=30))
        
        # Preparar dados para criação
        schedule_data = {
            'company': request.user.company,
            'name': request.data.get('name'),
            'report_type': request.data.get('report_type'),
            'frequency': frequency,
            'send_email': request.data.get('send_email', True),
            'email_recipients': email_recipients,
            'file_format': request.data.get('file_format', 'pdf'),
            'is_active': request.data.get('is_active', True),
            'next_run_at': next_run,
            'parameters': request.data.get('parameters', {}),
            'filters': request.data.get('filters', {}),
            'created_by': request.user
        }
        
        # Criar agendamento
        schedule = ReportSchedule.objects.create(**schedule_data)
        
        serializer = self.get_serializer(schedule)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """Run scheduled report immediately with better error handling"""
        try:
            schedule = self.get_object()
            
            # Determinar período baseado no tipo de relatório
            today = timezone.now().date()
            
            if schedule.frequency == 'daily':
                period_start = today - timedelta(days=1)
                period_end = today
            elif schedule.frequency == 'weekly':
                period_start = today - timedelta(days=7)
                period_end = today
            elif schedule.frequency == 'monthly':
                # Mês anterior completo
                first_day_current = today.replace(day=1)
                period_end = first_day_current - timedelta(days=1)
                period_start = period_end.replace(day=1)
            elif schedule.frequency == 'quarterly':
                period_start = today - timedelta(days=90)
                period_end = today
            else:  # yearly
                period_start = today.replace(year=today.year-1)
                period_end = today
            
            # Criar relatório
            report = Report.objects.create(
                company=schedule.company,
                report_type=schedule.report_type,
                title=f'{schedule.name} - Execução Manual - {timezone.now().strftime("%d/%m/%Y %H:%M")}',
                description=f'Relatório gerado manualmente a partir do agendamento: {schedule.name}',
                period_start=period_start,
                period_end=period_end,
                file_format=schedule.file_format,
                parameters=schedule.parameters,
                filters=schedule.filters,
                created_by=request.user
            )
            
            # Queue report generation
            generate_report_task.delay(report.id)
            
            # Update schedule
            schedule.last_run_at = timezone.now()
            schedule.save()
            
            return Response({
                'status': 'success',
                'report_id': report.id,
                'message': 'Relatório sendo gerado. Você será notificado quando estiver pronto.'
            })
            
        except Exception as e:
            logger.error(f"Error running scheduled report: {e}")
            return Response({
                'error': 'Falha ao executar relatório',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """
    Report template management - CORRIGIDO
    """
    serializer_class = ReportTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Remover referência ao campo is_system inexistente
        return ReportTemplate.objects.filter(
            Q(company=self.request.user.company) | Q(is_public=True),
            is_active=True
        ).order_by('name')


class QuickReportsView(APIView):
    """
    Quick report generation for common reports
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get quick report options"""
        return Response({
            'quick_reports': [
                {
                    'id': 'current_month',
                    'name': 'Resumo do Mês Atual',
                    'description': 'Relatório completo do mês em andamento',
                    'icon': 'calendar'
                },
                {
                    'id': 'last_month',
                    'name': 'Resumo do Mês Anterior',
                    'description': 'Relatório completo do mês passado',
                    'icon': 'calendar-check'
                },
                {
                    'id': 'quarterly',
                    'name': 'Relatório Trimestral',
                    'description': 'Análise dos últimos 3 meses',
                    'icon': 'chart-line'
                },
                {
                    'id': 'year_to_date',
                    'name': 'Acumulado do Ano',
                    'description': 'Resultados desde o início do ano',
                    'icon': 'chart-bar'
                },
                {
                    'id': 'cash_flow_30',
                    'name': 'Fluxo de Caixa 30 dias',
                    'description': 'Projeção de fluxo de caixa para os próximos 30 dias',
                    'icon': 'money-bill-wave'
                }
            ]
        })
    
    def post(self, request):
        """Generate quick report"""
        report_id = request.data.get('report_id')
        company = request.user.company
        
        # Define date ranges for quick reports
        now = timezone.now()
        today = now.date()
        
        if report_id == 'current_month':
            period_start = today.replace(day=1)
            period_end = today
            report_type = 'monthly_summary'
            title = f'Resumo de {now.strftime("%B %Y")}'
            
        elif report_id == 'last_month':
            last_month = (today.replace(day=1) - timedelta(days=1))
            period_start = last_month.replace(day=1)
            period_end = last_month
            report_type = 'monthly_summary'
            title = f'Resumo de {last_month.strftime("%B %Y")}'
            
        elif report_id == 'quarterly':
            period_end = today
            period_start = today - timedelta(days=90)
            report_type = 'quarterly_report'
            title = f'Relatório Trimestral - {period_start.strftime("%b")} a {period_end.strftime("%b %Y")}'
            
        elif report_id == 'year_to_date':
            period_start = today.replace(month=1, day=1)
            period_end = today
            report_type = 'annual_report'
            title = f'Acumulado {today.year}'
            
        elif report_id == 'cash_flow_30':
            period_start = today
            period_end = today + timedelta(days=30)
            report_type = 'cash_flow'
            title = 'Projeção de Fluxo de Caixa - 30 dias'
            
        else:
            return Response({
                'error': 'Invalid report_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create and queue report
        report = Report.objects.create(
            company=company,
            report_type=report_type,
            title=title,
            period_start=period_start,
            period_end=period_end,
            created_by=request.user
        )
        
        generate_report_task.delay(report.id)
        
        return Response({
            'status': 'success',
            'report': ReportSerializer(report).data,
            'message': 'Relatório sendo gerado. Você será notificado quando estiver pronto.'
        })


class AnalyticsView(APIView):
    """
    Advanced analytics and insights
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        company = request.user.company
        period = request.query_params.get('period', '30')  # days
        
        try:
            period_days = int(period)
        except ValueError:
            period_days = 30
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=period_days)
        
        # Convert dates to datetime for proper comparison
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Get all company accounts
        accounts = BankAccount.objects.filter(company=company, is_active=True)
        
        # Get transactions for period
        transactions = Transaction.objects.filter(
            bank_account__in=accounts,
            transaction_date__gte=start_datetime,
            transaction_date__lte=end_datetime
        )
        
        # Income vs Expenses
        income = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        expenses = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Top income sources
        top_income_sources = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in'],
            counterpart_name__isnull=False
        ).values('counterpart_name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:10]
        
        # Top expense categories
        top_expense_categories = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee'],
            category__isnull=False
        ).values('category__name', 'category__icon').annotate(
            total=Sum('amount'),
            count=Count('id'),
            avg=Avg('amount')
        ).order_by('-total')[:10]
        
        # Daily average
        daily_avg_income = income / period_days if period_days > 0 else Decimal('0')
        daily_avg_expense = abs(expenses) / period_days if period_days > 0 else Decimal('0')
        
        # Cash flow trend (weekly)
        weekly_trend = []
        for i in range(0, period_days, 7):
            week_start = end_date - timedelta(days=period_days-i)
            week_end = min(week_start + timedelta(days=6), end_date)
            
            # Convert dates to datetime for proper comparison
            week_start_datetime = datetime.combine(week_start, datetime.min.time())
            week_end_datetime = datetime.combine(week_end, datetime.max.time())
            
            week_transactions = transactions.filter(
                transaction_date__gte=week_start_datetime,
                transaction_date__lte=week_end_datetime
            )
            
            week_income = week_transactions.filter(
                transaction_type__in=['credit', 'transfer_in', 'pix_in']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            week_expenses = week_transactions.filter(
                transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            weekly_trend.append({
                'week_start': week_start,
                'week_end': week_end,
                'income': week_income,
                'expenses': abs(week_expenses),
                'net': week_income - abs(week_expenses)
            })
        
        return Response({
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': period_days
            },
            'summary': {
                'total_income': income,
                'total_expenses': abs(expenses),
                'net_result': income - abs(expenses),
                'transaction_count': transactions.count(),
                'daily_avg_income': daily_avg_income,
                'daily_avg_expense': daily_avg_expense
            },
            'top_income_sources': list(top_income_sources),
            'top_expense_categories': list(top_expense_categories),
            'weekly_trend': weekly_trend,
            'insights': self._generate_insights(income, expenses, transactions, period_days)
        })
    
    def _generate_insights(self, income, expenses, transactions, period_days):
        """Generate financial insights"""
        insights = []
        
        net_result = income - abs(expenses)
        
        # Profitability insight
        if net_result > 0:
            profit_margin = (net_result / income * 100) if income > 0 else 0
            insights.append({
                'type': 'positive',
                'title': 'Resultado Positivo',
                'message': f'Você teve um lucro de R$ {net_result:,.2f} ({profit_margin:.1f}% de margem) no período.'
            })
        else:
            insights.append({
                'type': 'warning',
                'title': 'Resultado Negativo',
                'message': f'Você teve um prejuízo de R$ {abs(net_result):,.2f} no período. Considere revisar seus gastos.'
            })
        
        # Expense trend
        if period_days >= 30:
            daily_expense = abs(expenses) / period_days
            monthly_projection = daily_expense * 30
            insights.append({
                'type': 'info',
                'title': 'Projeção de Gastos',
                'message': f'Com base na média diária, seus gastos mensais projetados são de R$ {monthly_projection:,.2f}.'
            })
        
        # Transaction frequency
        daily_transactions = transactions.count() / period_days if period_days > 0 else 0
        if daily_transactions > 10:
            insights.append({
                'type': 'info',
                'title': 'Alto Volume de Transações',
                'message': f'Você tem em média {daily_transactions:.1f} transações por dia. Considere usar a categorização automática.'
            })
        
        return insights


class DashboardStatsView(APIView):
    """Dashboard statistics endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        company = request.user.company
        accounts = BankAccount.objects.filter(company=company, is_active=True)
        
        # Current month stats
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        transactions = Transaction.objects.filter(
            bank_account__in=accounts,
            transaction_date__gte=month_start
        )
        
        total_balance = accounts.aggregate(total=Sum('current_balance'))['total'] or Decimal('0')
        
        income = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        expenses = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        return Response({
            'total_balance': total_balance,
            'income_this_month': income,
            'expenses_this_month': abs(expenses),
            'net_income': income - abs(expenses),
            'pending_transactions': 0,  # Placeholder
            'accounts_count': accounts.count(),
        })


class CashFlowDataView(APIView):
    """Cash flow data for charts"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        company = request.user.company
        accounts = BankAccount.objects.filter(company=company, is_active=True)
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            return Response({'error': 'start_date and end_date are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Generate daily cash flow data
        cash_flow_data = []
        current_date = start_date
        running_balance = Decimal('0')
        
        while current_date <= end_date:
            transactions = Transaction.objects.filter(
                bank_account__in=accounts,
                transaction_date__date=current_date
            )
            
            daily_income = transactions.filter(
                transaction_type__in=['credit', 'transfer_in', 'pix_in']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            daily_expenses = transactions.filter(
                transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            running_balance += daily_income - abs(daily_expenses)
            
            cash_flow_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'income': float(daily_income),
                'expenses': float(abs(daily_expenses)),
                'balance': float(running_balance)
            })
            
            current_date += timedelta(days=1)
        
        return Response(cash_flow_data)


class CategorySpendingView(APIView):
    """Category spending data for charts"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        company = request.user.company
        accounts = BankAccount.objects.filter(company=company, is_active=True)
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        category_type = request.GET.get('type', 'expense')
        
        if not start_date or not end_date:
            return Response({'error': 'start_date and end_date are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Convert dates to datetime for proper comparison
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        if category_type == 'expense':
            transaction_types = ['debit', 'transfer_out', 'pix_out', 'fee']
        else:
            transaction_types = ['credit', 'transfer_in', 'pix_in']
        
        category_data = Transaction.objects.filter(
            bank_account__in=accounts,
            transaction_date__gte=start_datetime,
            transaction_date__lte=end_datetime,
            transaction_type__in=transaction_types,
            category__isnull=False
        ).values('category__name', 'category__icon').annotate(
            amount=Sum('amount'),
            count=Count('id')
        ).order_by('-amount' if category_type == 'income' else 'amount')
        
        # Calculate percentages
        total_amount = sum(item['amount'] for item in category_data)
        
        result = []
        for item in category_data:
            amount = abs(item['amount'])
            percentage = (amount / abs(total_amount) * 100) if total_amount else 0
            
            result.append({
                'category': {
                    'name': item['category__name'],
                    'icon': item['category__icon']
                },
                'amount': float(amount),
                'percentage': round(percentage, 1),
                'transaction_count': item['count']
            })
        
        return Response(result)


class IncomeVsExpensesView(APIView):
    """Income vs expenses comparison data"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        company = request.user.company
        accounts = BankAccount.objects.filter(company=company, is_active=True)
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            return Response({'error': 'start_date and end_date are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Generate monthly data
        current_date = start_date.replace(day=1)  # Start from first day of month
        monthly_data = []
        
        while current_date <= end_date:
            # Calculate last day of current month
            if current_date.month == 12:
                next_month = current_date.replace(year=current_date.year + 1, month=1)
            else:
                next_month = current_date.replace(month=current_date.month + 1)
            
            month_end = next_month - timedelta(days=1)
            
            # Convert dates to datetime for proper comparison
            current_datetime = datetime.combine(current_date, datetime.min.time())
            month_end_datetime = datetime.combine(month_end, datetime.max.time())
            
            transactions = Transaction.objects.filter(
                bank_account__in=accounts,
                transaction_date__gte=current_datetime,
                transaction_date__lte=month_end_datetime
            )
            
            income = transactions.filter(
                transaction_type__in=['credit', 'transfer_in', 'pix_in']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            expenses = transactions.filter(
                transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            monthly_data.append({
                'month': current_date.strftime('%Y-%m'),
                'income': float(income),
                'expenses': float(abs(expenses)),
                'profit': float(income - abs(expenses))
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return Response(monthly_data)







class AIInsightsView(APIView):
    
    """Enhanced AI-powered financial insights with caching and real-time updates"""
    permission_classes = [permissions.IsAuthenticated]
    
    def _to_float(self, value):
        """Safely convert any value to float"""
        if value is None:
            return 0.0
        if isinstance(value, Decimal):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def get(self, request):
        """Get AI insights with optional real-time generation"""
        try:
            company = request.user.company
            
            # Check subscription
            if not self._check_ai_access(company):
                return Response({
                    'error': 'AI insights not available in your plan',
                    'upgrade_required': True
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get parameters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            force_refresh = request.GET.get('force_refresh', 'false').lower() == 'true'
            insight_type = request.GET.get('type', 'comprehensive')  # comprehensive, quick, custom
            
            # Validate dates
            if not start_date or not end_date:
                # Try to get cached latest insights
                cached_insights = self._get_cached_insights(company.id)
                if cached_insights:
                    return Response(cached_insights)
                
                return Response({'error': 'start_date and end_date are required'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Check for future dates
            if start_date > timezone.now().date():
                return self._future_period_response(start_date, end_date)
            
            # Get accounts
            accounts = BankAccount.objects.filter(company=company, is_active=True)
            if not accounts.exists():
                return self._no_accounts_response()
            
            # Get transactions
            transactions = self._get_transactions(accounts, start_date, end_date)
            
            if not transactions.exists():
                return self._no_transactions_response(start_date, end_date)
            
            # Generate or get cached insights
            cache_key = f"ai_insights_{company.id}_{start_date}_{end_date}_{insight_type}"
            
            if not force_refresh:
                cached = cache.get(cache_key)
                if cached:
                    logger.info(f"Returning cached insights for company {company.id}")
                    cached['from_cache'] = True
                    return Response(cached)
            
            # Calculate comprehensive financial metrics
            financial_data = self._calculate_comprehensive_metrics(
                transactions, start_date, end_date, company
            )
            
            # Generate AI insights based on type
            if insight_type == 'quick':
                insights = self._generate_quick_insights(financial_data)
            elif insight_type == 'custom':
                custom_params = request.GET.get('custom_params', {})
                insights = self._generate_custom_insights(financial_data, custom_params)
            else:
                insights = enhanced_ai_service.generate_insights(
                    financial_data,
                    company_name=company.name,
                    force_refresh=force_refresh
                )
            
            # Add interactive elements
            insights = self._add_interactive_elements(insights, company)
            
            # Cache the result
            cache.set(cache_key, insights, 86400)  # 24 hours
            
            # Queue background analysis for patterns (commented out for now)
            # if force_refresh:
            #     from .ai_tasks import analyze_deeper_patterns
            #     analyze_deeper_patterns.delay(company.id, financial_data)
            
            return Response(insights)
            
        except Exception as e:
            logger.error(f"Error in AIInsightsView: {e}", exc_info=True)
            return Response({
                'error': 'An error occurred while generating insights',
                'details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def ask_ai(self, request):
        """Allow users to ask specific questions to AI"""
        try:
            company = request.user.company
            question = request.data.get('question')
            context = request.data.get('context', {})
            
            if not question:
                return Response({'error': 'Question is required'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Get recent financial data for context
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            
            accounts = BankAccount.objects.filter(company=company, is_active=True)
            transactions = self._get_transactions(accounts, start_date, end_date)
            
            financial_data = self._calculate_comprehensive_metrics(
                transactions, start_date, end_date, company
            )
            
            # Ask AI
            response = enhanced_ai_service.ask_financial_question(
                question=question,
                financial_data=financial_data,
                context=context,
                company_name=company.name
            )
            
            return Response(response)
            
        except Exception as e:
            logger.error(f"Error in ask_ai: {e}")
            return Response({
                'error': 'Failed to process your question'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def insights_history(self, request):
        """Get historical insights and trends"""
        try:
            company = request.user.company
            period = request.GET.get('period', '30')  # days
            
            # Get historical insights from cache
            insights_history = []
            
            for i in range(0, int(period), 7):  # Weekly intervals
                date = timezone.now().date() - timedelta(days=i)
                cache_key = f"ai_insights_summary_{company.id}_{date}"
                summary = cache.get(cache_key)
                
                if summary:
                    insights_history.append({
                        'date': date,
                        'health_score': summary.get('health_score', 0),
                        'key_metrics': summary.get('key_metrics', {}),
                        'top_insight': summary.get('top_insight', '')
                    })
            
            return Response({
                'history': insights_history,
                'trends': self._analyze_historical_trends(insights_history)
            })
            
        except Exception as e:
            logger.error(f"Error getting insights history: {e}")
            return Response({
                'error': 'Failed to retrieve insights history'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _check_ai_access(self, company) -> bool:
        """Check if company has access to AI features"""
        # Check subscription plan
        if hasattr(company, 'subscription_plan'):
            return company.subscription_plan.enable_ai_insights
        return True  # Default to true for now
    
    def _get_cached_insights(self, company_id: int) -> Dict[str, Any]:
        """Get latest cached insights for company"""
        cache_key = f"ai_insights_latest_{company_id}"
        return cache.get(cache_key)
    
    def make_aware_datetime(date_obj):
        """Convert date to timezone-aware datetime"""
        if isinstance(date_obj, datetime):
            if django_timezone.is_naive(date_obj):
                return django_timezone.make_aware(date_obj)
            return date_obj
        elif isinstance(date_obj, date):
            # Convert date to datetime at start/end of day
            dt = datetime.combine(date_obj, datetime.min.time())
            return django_timezone.make_aware(dt)
        return date_obj

    def _get_transactions(self, accounts, start_date, end_date):
        """Get transactions with proper timezone handling"""
        from django.utils import timezone as django_timezone
        
        try:
            # Convert dates to timezone-aware datetimes
            if isinstance(start_date, date) and not isinstance(start_date, datetime):
                start_datetime = django_timezone.make_aware(
                    datetime.combine(start_date, datetime.min.time())
                )
            elif isinstance(start_date, datetime):
                start_datetime = start_date if django_timezone.is_aware(start_date) else django_timezone.make_aware(start_date)
            else:
                start_datetime = django_timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
                
            if isinstance(end_date, date) and not isinstance(end_date, datetime):
                end_datetime = django_timezone.make_aware(
                    datetime.combine(end_date, datetime.max.time().replace(microsecond=999999))
                )
            elif isinstance(end_date, datetime):
                end_datetime = end_date if django_timezone.is_aware(end_date) else django_timezone.make_aware(end_date)
            else:
                end_datetime = django_timezone.make_aware(datetime.combine(end_date, datetime.max.time().replace(microsecond=999999)))
            
            return Transaction.objects.filter(
                bank_account__in=accounts,
                transaction_date__gte=start_datetime,
                transaction_date__lte=end_datetime
            ).select_related('category', 'bank_account')
            
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            # Fallback to date-based query
            return Transaction.objects.filter(
                bank_account__in=accounts,
                transaction_date__date__gte=start_date,
                transaction_date__date__lte=end_date
            ).select_related('category', 'bank_account')

    def _calculate_comprehensive_metrics(self, transactions, start_date, end_date, company):
        """Calculate comprehensive financial metrics with additional insights"""
        
        # Basic metrics
        basic_metrics = self._calculate_basic_metrics(transactions, start_date, end_date)
        
        # Advanced metrics
        advanced_metrics = {
            'customer_metrics': self._calculate_customer_metrics(transactions),
            'cash_flow_patterns': self._analyze_cash_flow_patterns(transactions),
            'expense_trends': self._analyze_expense_trends(transactions),
            'revenue_quality': self._assess_revenue_quality(transactions),
            'operational_efficiency': self._calculate_operational_efficiency(transactions),
            'financial_ratios': self._calculate_financial_ratios(basic_metrics),
            'benchmark_comparison': self._get_benchmark_comparison(company, basic_metrics)
        }
        
        # Combine all metrics
        return {
            **basic_metrics,
            **advanced_metrics,
            'company_context': {
                'name': company.name,
                'industry': getattr(company, 'industry', 'general'),
                'size': getattr(company, 'size', 'small'),
                'age_months': self._calculate_company_age(company)
            }
        }
    
    def _calculate_basic_metrics(self, transactions, start_date, end_date):
        """Calculate basic financial metrics"""
        # Income and expenses
        income_types = ['credit', 'transfer_in', 'pix_in']
        expense_types = ['debit', 'transfer_out', 'pix_out', 'fee']
        
        income = transactions.filter(
            transaction_type__in=income_types
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        expenses = transactions.filter(
            transaction_type__in=expense_types
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Category breakdown
        category_data = self._get_category_breakdown(transactions, expense_types)
        
        # Transaction volume metrics
        daily_transactions = transactions.values('transaction_date__date').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        # Weekly patterns
        weekly_patterns = self._calculate_weekly_patterns(
            transactions, start_date, end_date
        )
        
        # Largest transactions
        largest_income = transactions.filter(
            transaction_type__in=income_types
        ).order_by('-amount').first()
        
        largest_expense = transactions.filter(
            transaction_type__in=expense_types
        ).order_by('amount').first()
        
        return {
            'income': float(income),
            'expenses': float(abs(expenses)),
            'net_flow': float(income - abs(expenses)),
            'transaction_count': transactions.count(),
            'period_days': (end_date - start_date).days + 1,
            'top_expense_categories': category_data,
            'weekly_patterns': weekly_patterns,
            'daily_transaction_data': list(daily_transactions),
            'largest_income': {
                'amount': float(largest_income.amount) if largest_income else 0,
                'description': largest_income.description if largest_income else '',
                'date': largest_income.transaction_date if largest_income else None
            },
            'largest_expense': {
                'amount': float(abs(largest_expense.amount)) if largest_expense else 0,
                'description': largest_expense.description if largest_expense else '',
                'date': largest_expense.transaction_date if largest_expense else None
            }
        }
    
    def _get_category_breakdown(self, transactions, expense_types):
        """Get detailed category breakdown"""
        category_data = transactions.filter(
            transaction_type__in=expense_types,
            category__isnull=False
        ).values(
            'category__name', 
            'category__icon',
            'category__slug'
        ).annotate(
            total=Sum('amount'),
            count=Count('id'),
            avg_amount=Avg('amount'),
            max_amount=Max('amount'),
            min_amount=Min('amount')
        ).order_by('total')
        
        # Calculate percentages and format
        total_expenses = sum(abs(item['total']) for item in category_data)
        
        formatted_categories = []
        for item in category_data:
            amount = abs(item['total'])
            formatted_categories.append({
                'name': item['category__name'],
                'icon': item['category__icon'],
                'slug': item['category__slug'],
                'amount': float(amount),
                'percentage': round((amount / total_expenses * 100), 1) if total_expenses > 0 else 0,
                'count': item['count'],
                'avg_amount': float(abs(item['avg_amount'])),
                'max_amount': float(abs(item['max_amount'])),
                'min_amount': float(abs(item['min_amount']))
            })
        
        return formatted_categories
    
    def _calculate_weekly_patterns(self, transactions, start_date, end_date):
        """Calculate detailed weekly patterns"""
        weekly_data = []
        current_date = start_date
        
        while current_date <= end_date:
            week_end = min(current_date + timedelta(days=6), end_date)
            
            week_transactions = transactions.filter(
                transaction_date__date__gte=current_date,
                transaction_date__date__lte=week_end
            )
            
            week_income = week_transactions.filter(
                transaction_type__in=['credit', 'transfer_in', 'pix_in']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            week_expenses = week_transactions.filter(
                transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Daily breakdown
            daily_data = []
            for i in range((week_end - current_date).days + 1):
                day = current_date + timedelta(days=i)
                day_trans = week_transactions.filter(transaction_date__date=day)
                
                day_income = day_trans.filter(
                    transaction_type__in=['credit', 'transfer_in', 'pix_in']
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                day_expenses = day_trans.filter(
                    transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                daily_data.append({
                    'date': day,
                    'income': float(day_income),
                    'expenses': float(abs(day_expenses)),
                    'net': float(day_income - abs(day_expenses)),
                    'transaction_count': day_trans.count()
                })
            
            weekly_data.append({
                'week_start': current_date,
                'week_end': week_end,
                'income': float(week_income),
                'expenses': float(abs(week_expenses)),
                'net': float(week_income - abs(week_expenses)),
                'transaction_count': week_transactions.count(),
                'daily_breakdown': daily_data
            })
            
            current_date = week_end + timedelta(days=1)
        
        return weekly_data
    
    def _calculate_customer_metrics(self, transactions):
        """Calculate customer-related metrics"""
        income_transactions = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in'],
            counterpart_name__isnull=False
        )
        
        customer_data = income_transactions.values('counterpart_name').annotate(
            total_revenue=Sum('amount'),
            transaction_count=Count('id'),
            avg_transaction=Avg('amount'),
            first_transaction=Min('transaction_date'),
            last_transaction=Max('transaction_date')
        ).order_by('-total_revenue')
        
        total_revenue = sum(c['total_revenue'] for c in customer_data)
        
        # Top customers analysis
        top_customers = []
        for customer in customer_data[:10]:
            top_customers.append({
                'name': customer['counterpart_name'],
                'revenue': float(customer['total_revenue']),
                'percentage': float(customer['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0,
                'transactions': customer['transaction_count'],
                'avg_transaction': float(customer['avg_transaction']),
                'days_active': (customer['last_transaction'] - customer['first_transaction']).days
            })
        
        # Customer concentration risk
        top_3_revenue = sum(c['revenue'] for c in top_customers[:3])
        concentration_risk = (top_3_revenue / float(total_revenue) * 100) if total_revenue > 0 else 0
        
        return {
            'total_customers': customer_data.count(),
            'top_customers': top_customers,
            'customer_concentration_risk': concentration_risk,
            'average_customer_value': float(total_revenue / customer_data.count()) if customer_data.count() > 0 else 0,
            'customer_retention_rate': self._calculate_retention_rate(customer_data)
        }
    
    def _calculate_retention_rate(self, customer_data):
        """Calculate customer retention rate"""
        # Simplified: customers who transacted in both first and last 30% of period
        if not customer_data:
            return 0
        
        total_customers = customer_data.count()
        retained_customers = sum(
            1 for c in customer_data 
            if (c['last_transaction'] - c['first_transaction']).days > 30
        )
        
        return (retained_customers / total_customers * 100) if total_customers > 0 else 0
    

    def _analyze_cash_flow_patterns(self, transactions):
        """Analyze cash flow patterns"""
        # Group by day of week - usando Django ORM compatível
        day_of_week_data = []
        for day in range(7):  # 0 = Monday, 6 = Sunday
            day_transactions = transactions.filter(
                transaction_date__week_day=day + 2  # Django week_day: 1=Sunday, 2=Monday, etc.
            )
            
            income = day_transactions.filter(
                transaction_type__in=['credit', 'transfer_in', 'pix_in']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            expenses = day_transactions.filter(
                transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            day_of_week_data.append({
                'transaction_date__week_day': day,
                'income': income,
                'expenses': expenses
            })
        
        # Group by day of month - usando Python ao invés de SQL
        from collections import defaultdict
        day_of_month_dict = defaultdict(lambda: {'income': Decimal('0'), 'expenses': Decimal('0')})
        
        for trans in transactions:
            day = trans.transaction_date.day
            if trans.transaction_type in ['credit', 'transfer_in', 'pix_in']:
                day_of_month_dict[day]['income'] += trans.amount
            elif trans.transaction_type in ['debit', 'transfer_out', 'pix_out', 'fee']:
                day_of_month_dict[day]['expenses'] += trans.amount
        
        day_of_month_data = [
            {'day': day, 'income': data['income'], 'expenses': data['expenses']}
            for day, data in sorted(day_of_month_dict.items())
        ]
        
        # Find best and worst days
        if day_of_week_data:
            best_day = max(day_of_week_data, 
                        key=lambda x: float(x.get('income', 0) or 0) - float(abs(x.get('expenses', 0) or 0)))
            worst_day = min(day_of_week_data, 
                        key=lambda x: float(x.get('income', 0) or 0) - float(abs(x.get('expenses', 0) or 0)))
        else:
            best_day = worst_day = None
        
        return {
            'by_day_of_week': day_of_week_data,
            'by_day_of_month': day_of_month_data,
            'best_day_of_week': best_day['transaction_date__week_day'] if best_day else None,
            'worst_day_of_week': worst_day['transaction_date__week_day'] if worst_day else None,
            'income_concentration': self._calculate_income_concentration(day_of_month_data),
            'expense_concentration': self._calculate_expense_concentration(day_of_month_data)
        }
    

    def _calculate_income_concentration(self, day_data):
        """Calculate how concentrated income is on specific days"""
        total_income = sum(float(d['income'] or 0) for d in day_data)
        if total_income == 0:
            return 0
        
        # Calculate Gini coefficient for income distribution
        sorted_income = sorted([float(d['income'] or 0) for d in day_data])
        n = len(sorted_income)
        if n == 0:
            return 0
        
        index = range(1, n + 1)
        
        return (2 * sum(index[i] * sorted_income[i] for i in range(n))) / (n * sum(sorted_income)) - (n + 1) / n

    def _calculate_expense_concentration(self, day_data):
        """Calculate how concentrated expenses are on specific days"""
        total_expenses = sum(abs(float(d['expenses'] or 0)) for d in day_data)
        if total_expenses == 0:
            return 0
        
        # Similar to income concentration
        sorted_expenses = sorted([abs(float(d['expenses'] or 0)) for d in day_data])
        n = len(sorted_expenses)
        if n == 0:
            return 0
        
        index = range(1, n + 1)
        
        return (2 * sum(index[i] * sorted_expenses[i] for i in range(n))) / (n * sum(sorted_expenses)) - (n + 1) / n


    def _analyze_expense_trends(self, transactions):
        """Analyze expense trends over time"""
        expense_transactions = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        )
        
        # Monthly trend - usando Python ao invés de SQL raw
        from collections import defaultdict
        monthly_dict = defaultdict(lambda: {'total': Decimal('0'), 'count': 0, 'amounts': []})
        
        for trans in expense_transactions:
            month_key = trans.transaction_date.strftime('%Y-%m')
            monthly_dict[month_key]['total'] += abs(trans.amount)
            monthly_dict[month_key]['count'] += 1
            monthly_dict[month_key]['amounts'].append(abs(trans.amount))
        
        # Calcular média e converter para lista ordenada
        monthly_expenses = []
        for month, data in sorted(monthly_dict.items()):
            avg_amount = data['total'] / data['count'] if data['count'] > 0 else Decimal('0')
            monthly_expenses.append({
                'month': month,
                'total': data['total'],
                'count': data['count'],
                'avg': avg_amount
            })
        
        # Category trends
        category_trends = {}
        for category in expense_transactions.values('category__name').distinct():
            if category['category__name']:
                cat_name = category['category__name']
                cat_monthly = defaultdict(lambda: Decimal('0'))
                
                cat_transactions = expense_transactions.filter(category__name=cat_name)
                for trans in cat_transactions:
                    month_key = trans.transaction_date.strftime('%Y-%m')
                    cat_monthly[month_key] += abs(trans.amount)
                
                category_trends[cat_name] = [
                    {'month': month, 'total': total}
                    for month, total in sorted(cat_monthly.items())
                ]
        
        return {
            'monthly_trend': monthly_expenses,
            'category_trends': category_trends,
            'growth_rate': self._calculate_expense_growth_rate(monthly_expenses),
            'volatility': self._calculate_expense_volatility(monthly_expenses)
        }



    def _calculate_expense_growth_rate(self, monthly_data):
        """Calculate average monthly expense growth rate"""
        if len(monthly_data) < 2:
            return 0
        
        growth_rates = []
        for i in range(1, len(monthly_data)):
            prev_total = float(monthly_data[i-1].get('total', 0))
            curr_total = float(monthly_data[i].get('total', 0))
            
            if prev_total != 0:
                growth = ((curr_total - prev_total) / abs(prev_total)) * 100
                growth_rates.append(growth)
        
        return float(sum(growth_rates) / len(growth_rates)) if growth_rates else 0

    def _calculate_expense_volatility(self, monthly_data):
        """Calculate expense volatility (standard deviation / mean)"""
        if not monthly_data:
            return 0
        
        expenses = [abs(float(m['total'])) for m in monthly_data]
        mean = sum(expenses) / len(expenses) if expenses else 0
        
        if mean == 0:
            return 0
        
        # Use float operations
        variance = sum((x - mean) ** 2 for x in expenses) / len(expenses)
        std_dev = math.sqrt(variance)  # Use math.sqrt instead of ** 0.5
        
        return (std_dev / mean) * 100
    
    def _assess_revenue_quality(self, transactions):
        """Assess the quality and sustainability of revenue"""
        income_transactions = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in']
        )
        
        # Recurring vs one-time
        recurring_keywords = ['mensalidade', 'assinatura', 'recorrente', 'mensal']
        recurring_revenue = income_transactions.filter(
            description__iregex='|'.join(recurring_keywords)
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_revenue = income_transactions.aggregate(total=Sum('amount'))['total'] or 0
        
        # Revenue predictability score
        daily_revenue = income_transactions.values('transaction_date__date').annotate(
            total=Sum('amount')
        )
        
        revenue_volatility = self._calculate_revenue_volatility(daily_revenue)
        predictability_score = 100 - min(revenue_volatility, 100)
        
        return {
            'total_revenue': float(total_revenue),
            'recurring_revenue': float(recurring_revenue),
            'recurring_percentage': float(recurring_revenue / total_revenue * 100) if total_revenue > 0 else 0,
            'predictability_score': predictability_score,
            'revenue_sources': self._identify_revenue_sources(income_transactions),
            'seasonality_index': self._calculate_seasonality_index(income_transactions)
        }
    
    def _calculate_revenue_volatility(self, daily_revenue):
        """Calculate revenue volatility"""
        if not daily_revenue:
            return 0
        
        # Convert all values to float
        revenues = [float(d['total']) for d in daily_revenue]
        mean = sum(revenues) / len(revenues)
        
        if mean == 0:
            return 100
        
        # Calculate variance using float operations
        variance = sum((r - mean) ** 2 for r in revenues) / len(revenues)
        std_dev = math.sqrt(variance)  # Use math.sqrt instead of ** 0.5
        
        return (std_dev / mean) * 100
    

    def _identify_revenue_sources(self, income_transactions):
        """Identify and categorize revenue sources"""
        # Usar apenas os primeiros 20 registros para análise
        sources = income_transactions.values('description')[:20]
        
        categorized_sources = {
            'sales': Decimal('0'),
            'services': Decimal('0'),
            'subscriptions': Decimal('0'),
            'other': Decimal('0')
        }
        
        # Analisar cada transação
        for trans in income_transactions:
            desc_lower = trans.description.lower() if trans.description else ''
            amount = trans.amount
            
            if any(word in desc_lower for word in ['venda', 'produto', 'pedido']):
                categorized_sources['sales'] += amount
            elif any(word in desc_lower for word in ['serviço', 'consultoria', 'projeto']):
                categorized_sources['services'] += amount
            elif any(word in desc_lower for word in ['assinatura', 'mensalidade', 'recorrente']):
                categorized_sources['subscriptions'] += amount
            else:
                categorized_sources['other'] += amount
        
        return {k: float(v) for k, v in categorized_sources.items()}


    def _calculate_seasonality_index(self, income_transactions):
        """Calculate seasonality index (0-100, higher = more seasonal)"""
        # Agrupar por mês usando Python
        from collections import defaultdict
        monthly_data = defaultdict(lambda: Decimal('0'))
        
        for trans in income_transactions:
            month = trans.transaction_date.month
            monthly_data[month] += trans.amount
        
        if len(monthly_data) < 3:
            return 0
        
        # Converter para lista de floats
        revenues = [float(amount) for amount in monthly_data.values()]
        mean = sum(revenues) / len(revenues)
        
        if mean == 0:
            return 0
        
        # Calcular coefficient of variation
        variance = sum((r - mean) ** 2 for r in revenues) / len(revenues)
        std_dev = variance ** 0.5
        cv = (std_dev / mean) * 100
        
        # Converter para escala 0-100
        return min(float(cv), 100.0)
    
    def _calculate_operational_efficiency(self, transactions):
        """Calculate operational efficiency metrics"""
        # Operating expense ratio
        operating_expenses = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee'],
            category__slug__in=['salaries', 'rent', 'utilities', 'supplies', 'admin']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_revenue = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Cost per transaction
        total_costs = abs(transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        ).aggregate(total=Sum('amount'))['total'] or 0)
        
        revenue_transactions = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in']
        ).count()
        
        return {
            'operating_expense_ratio': float(abs(operating_expenses) / total_revenue * 100) if total_revenue > 0 else 0,
            'cost_per_transaction': float(total_costs / revenue_transactions) if revenue_transactions > 0 else 0,
            'efficiency_score': self._calculate_efficiency_score(operating_expenses, total_revenue),
            'automation_potential': self._assess_automation_potential(transactions)
        }
    
    def _calculate_efficiency_score(self, operating_expenses, total_revenue):
        """Calculate efficiency score (0-100)"""
        if total_revenue == 0:
            return 0
        
        ratio = abs(operating_expenses) / total_revenue
        
        # Lower ratio = higher efficiency
        if ratio < 0.3:
            return 90
        elif ratio < 0.5:
            return 70
        elif ratio < 0.7:
            return 50
        else:
            return 30
    
    def _assess_automation_potential(self, transactions):
        """Assess potential for automation based on transaction patterns"""
        # Recurring transactions
        recurring_expenses = transactions.filter(
            transaction_type__in=['debit', 'transfer_out'],
            description__iregex='mensalidade|assinatura|aluguel|salário'
        ).count()
        
        total_expenses = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        ).count()
        
        automation_score = (recurring_expenses / total_expenses * 100) if total_expenses > 0 else 0
        
        return {
            'score': automation_score,
            'recurring_transactions': recurring_expenses,
            'potential_savings': automation_score * 0.1  # 10% time savings per automated transaction
        }
    
    def _calculate_financial_ratios(self, basic_metrics):
        """Calculate key financial ratios"""
        income = basic_metrics['income']
        expenses = basic_metrics['expenses']
        net_flow = basic_metrics['net_flow']
        
        return {
            'profit_margin': (net_flow / income * 100) if income > 0 else 0,
            'expense_ratio': (expenses / income * 100) if income > 0 else 0,
            'liquidity_ratio': income / expenses if expenses > 0 else 0,
            'burn_rate': expenses / basic_metrics['period_days'] if basic_metrics['period_days'] > 0 else 0,
            'runway_months': (income / (expenses / basic_metrics['period_days'] * 30)) if expenses > 0 else 0
        }
    
    def _get_benchmark_comparison(self, company, basic_metrics):
        """Compare metrics against industry benchmarks"""
        # This would ideally pull from a benchmark database
        # For now, using hardcoded values
        industry_benchmarks = {
            'general': {
                'profit_margin': 15,
                'expense_ratio': 85,
                'growth_rate': 10
            },
            'retail': {
                'profit_margin': 10,
                'expense_ratio': 90,
                'growth_rate': 8
            },
            'services': {
                'profit_margin': 20,
                'expense_ratio': 80,
                'growth_rate': 15
            }
        }
        
        industry = getattr(company, 'industry', 'general')
        benchmarks = industry_benchmarks.get(industry, industry_benchmarks['general'])
        
        profit_margin = (basic_metrics['net_flow'] / basic_metrics['income'] * 100) if basic_metrics['income'] > 0 else 0
        
        return {
            'industry': industry,
            'profit_margin_vs_industry': profit_margin - benchmarks['profit_margin'],
            'performance_percentile': self._calculate_performance_percentile(profit_margin, benchmarks['profit_margin'])
        }
    
    def _calculate_performance_percentile(self, actual, benchmark):
        """Calculate performance percentile compared to benchmark"""
        if benchmark == 0:
            return 50
        
        ratio = actual / benchmark
        
        if ratio >= 1.5:
            return 90
        elif ratio >= 1.2:
            return 75
        elif ratio >= 1.0:
            return 60
        elif ratio >= 0.8:
            return 40
        else:
            return 25
    
    def _calculate_company_age(self, company):
        """Calculate company age in months"""
        if hasattr(company, 'created_at'):
            return (timezone.now() - company.created_at).days // 30
        return 12  # Default
    
    def _generate_quick_insights(self, financial_data):
        """Generate quick insights without full AI processing"""
        insights = []
        
        # Quick cash flow insight
        if financial_data['net_flow'] > 0:
            insights.append({
                'type': 'success',
                'title': 'Fluxo de Caixa Positivo',
                'description': f"Lucro de R$ {financial_data['net_flow']:,.2f}",
                'value': f"R$ {financial_data['net_flow']:,.2f}",
                'trend': 'up'
            })
        else:
            insights.append({
                'type': 'danger',
                'title': 'Atenção ao Fluxo de Caixa',
                'description': f"Déficit de R$ {abs(financial_data['net_flow']):,.2f}",
                'value': f"-R$ {abs(financial_data['net_flow']):,.2f}",
                'trend': 'down'
            })
        
        # Top expense category
        if financial_data['top_expense_categories']:
            top_cat = financial_data['top_expense_categories'][0]
            insights.append({
                'type': 'info',
                'title': f"Maior Gasto: {top_cat['name']}",
                'description': f"{top_cat['percentage']:.1f}% das despesas",
                'value': f"R$ {top_cat['amount']:,.2f}"
            })
        
        return {
            'insights': insights,
            'predictions': {
                'next_month_income': financial_data['income'],
                'next_month_expenses': financial_data['expenses'],
                'projected_savings': financial_data['net_flow']
            },
            'recommendations': [],
            'quick_mode': True
        }
    
    def _generate_custom_insights(self, financial_data, custom_params):
        """Generate custom insights based on specific parameters"""
        # This would be expanded based on custom requirements
        return enhanced_ai_service.generate_insights(
            financial_data,
            company_name=financial_data.get('company_context', {}).get('name', 'Empresa'),
            force_refresh=True
        )
    
    def _add_interactive_elements(self, insights, company):
        """Add interactive elements to insights"""
        # Add action buttons for recommendations
        for rec in insights.get('recommendations', []):
            if rec.get('type') == 'cost_reduction':
                rec['action_button'] = {
                    'label': 'Ver Detalhes',
                    'url': f'/categories?focus={rec.get("category_slug", "")}'
                }
            elif rec.get('type') == 'revenue_growth':
                rec['action_button'] = {
                    'label': 'Criar Campanha',
                    'url': '/marketing/campaigns/new'
                }
        
        # Add drill-down links for insights
        for insight in insights.get('insights', []):
            if 'category' in insight.get('title', '').lower():
                insight['drill_down'] = {
                    'label': 'Analisar Categoria',
                    'url': '/reports?type=category_analysis'
                }
        
        return insights
    
    def _future_period_response(self, start_date, end_date):
        """Response for future period requests"""
        return Response({
            'insights': [
                {
                    'type': 'info',
                    'title': 'Período Futuro',
                    'description': 'Não é possível gerar insights para períodos futuros',
                    'value': 'N/A'
                }
            ],
            'predictions': {
                'message': 'Use períodos passados para ver previsões futuras'
            },
            'recommendations': [],
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        })
    
    def _no_accounts_response(self):
        """Response when no accounts are connected"""
        return Response({
            'insights': [
                {
                    'type': 'warning',
                    'title': 'Nenhuma Conta Conectada',
                    'description': 'Conecte suas contas bancárias para começar a receber insights',
                    'value': 'Configurar',
                    'action_button': {
                        'label': 'Conectar Conta',
                        'url': '/banking/accounts/connect'
                    }
                }
            ],
            'recommendations': [
                {
                    'type': 'setup',
                    'title': 'Conecte sua Primeira Conta',
                    'description': 'Em menos de 5 minutos, conecte sua conta e comece a receber insights automáticos',
                    'priority': 'high'
                }
            ]
        })
    
    def _no_transactions_response(self, start_date, end_date):
        """Response when no transactions found"""
        return Response({
            'insights': [
                {
                    'type': 'info',
                    'title': 'Sem Transações no Período',
                    'description': 'Não foram encontradas transações para análise',
                    'value': '0 transações'
                }
            ],
            'predictions': {},
            'recommendations': [
                {
                    'type': 'action',
                    'title': 'Verifique suas Contas',
                    'description': 'Certifique-se de que suas contas estão sincronizadas corretamente'
                }
            ],
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        })
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (coefficient of variation) safely"""
        if not values or len(values) < 2:
            return 0
        
        # Filter out non-finite values and convert to float
        clean_values = [float(v) for v in values if np.isfinite(float(v))]
        if len(clean_values) < 2:
            return 0
        
        mean = np.mean(clean_values)
        if mean == 0:
            return 0
        
        std_dev = np.std(clean_values)
        cv = (std_dev / abs(mean)) * 100
        
        return min(cv, 200)
    
    def _analyze_historical_trends(self, insights_history):
        """Analyze trends from historical insights"""
        if not insights_history:
            return {}
        
        health_scores = [h['health_score'] for h in insights_history]
        
        return {
            'health_trend': 'improving' if health_scores[-1] > health_scores[0] else 'declining',
            'average_health': sum(health_scores) / len(health_scores),
            'volatility': self._calculate_score_volatility(health_scores)
        }
    
    def _calculate_score_volatility(self, scores):
        """Calculate volatility of scores"""
        if len(scores) < 2:
            return 0
        
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        
        return variance ** 0.5
    
    