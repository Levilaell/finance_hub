"""
Reports app views
Financial reporting and analytics
"""
import logging
from decimal import Decimal
import math
from typing import Dict, Any, List
from datetime import datetime, timedelta

from apps.companies.decorators import requires_plan_feature
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
from .models import Report, ReportTemplate, AIAnalysis, AIAnalysisTemplate
from .serializers import (
    ReportSerializer,
    ReportTemplateSerializer,
    AIAnalysisSerializer,
    AIAnalysisListSerializer,
    AIAnalysisTemplateSerializer,
)
# from .ai_service import enhanced_ai_service  # To be implemented
from django.utils import timezone as django_timezone
logger = logging.getLogger(__name__)


# Adicionar estas correções ao backend/apps/reports/views.py

# backend/apps/reports/views.py

import logging
from decimal import Decimal
import math
from typing import Dict, Any, List
from datetime import datetime, timedelta

from django.http import HttpResponse
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.banking.models import BankAccount, Transaction
from .models import Report, ReportTemplate
from .serializers import (
    ReportSerializer,
    ReportTemplateSerializer,
)
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class ReportViewSet(viewsets.ModelViewSet):
    """
    Report management viewset - SEM CELERY
    """
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Report.objects.filter(
            company=self.request.user.company
        ).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Generate a new report SINCRONAMENTE"""
        logger.info(f"Report creation request data: {request.data}")
        
        report_type = request.data.get('report_type')
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        file_format = request.data.get('file_format', 'pdf')
        
        # Validação
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
                
        except ValueError as e:
            return Response({
                'error': f'Invalid date format. Use YYYY-MM-DD. Error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar tipo de relatório
        valid_types = [choice[0] for choice in Report.REPORT_TYPES]
        if report_type not in valid_types:
            return Response({
                'error': f'Invalid report type. Valid types: {", ".join(valid_types)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Criar relatório
        try:
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
            
            # Gerar relatório SINCRONAMENTE
            try:
                from django.core.files.base import ContentFile
                generator = ReportGenerator(report.company)
                
                # Gerar relatório baseado no tipo
                buffer = generator.generate_report(
                    report_type=report.report_type,
                    start_date=report.period_start,
                    end_date=report.period_end,
                    format=report.file_format or 'pdf',
                    filters=report.parameters
                )
                
                filename = f"{report.report_type}_{report.period_start}_{report.period_end}.{report.file_format or 'pdf'}"
                
                # Salvar arquivo
                report.file.save(filename, ContentFile(buffer.getvalue()))
                report.is_generated = True
                report.generation_time = 1  # Geração síncrona é rápida
                report.file_size = buffer.tell()
                report.save()
                
            except Exception as e:
                logger.error(f"Error generating report: {str(e)}")
                report.error_message = str(e)
                report.save()
            
            serializer = self.get_serializer(report)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating report: {str(e)}")
            return Response({
                'error': f'Failed to create report: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download report file"""
        try:
            report = self.get_object()
            
            if not report.is_generated:
                return Response({
                    'error': 'Report is not ready for download'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not report.file:
                return Response({
                    'error': 'Report file not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Abrir e retornar o arquivo
            try:
                file_handle = report.file.open('rb')
                response = HttpResponse(
                    file_handle.read(),
                    content_type=self._get_content_type(report.file_format)
                )
                response['Content-Disposition'] = f'attachment; filename="{report.title}_{report.id}.{report.file_format}"'
                file_handle.close()
                return response
            except Exception as e:
                logger.error(f"Error downloading report {pk}: {str(e)}")
                return Response({
                    'error': 'Failed to download report'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Report.DoesNotExist:
            return Response({
                'error': 'Report not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def _get_content_type(self, file_format):
        """Get content type for file format"""
        content_types = {
            'pdf': 'application/pdf',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'csv': 'text/csv',
            'json': 'application/json'
        }
        return content_types.get(file_format, 'application/octet-stream')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get reports summary statistics"""
        company = request.user.company
        reports = self.get_queryset()
        
        from django.db.models import Count
        from django.utils import timezone
        
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        
        summary_data = {
            'total_reports': reports.count(),
            'reports_generated': reports.filter(is_generated=True).count(),
            'reports_pending': reports.filter(is_generated=False, error_message='').count(),
            'reports_failed': reports.filter(is_generated=False).exclude(error_message='').count(),
            'reports_by_type': list(reports.values('report_type').annotate(
                count=Count('id'),
                label=Count('id')
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


class QuickReportsView(APIView):
    """Quick report generation for common reports - SEM CELERY"""
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
        """Generate quick report SINCRONAMENTE"""
        from django.utils import timezone
        from django.core.files.base import ContentFile
        
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
        
        # Create report
        report = Report.objects.create(
            company=company,
            report_type=report_type,
            title=title,
            period_start=period_start,
            period_end=period_end,
            created_by=request.user,
            file_format='pdf'
        )
        
        # Generate report immediately
        try:
            generator = ReportGenerator(report.company)
            buffer = generator.generate_report(
                report_type=report.report_type,
                start_date=report.period_start,
                end_date=report.period_end,
                format=report.file_format or 'pdf',
                filters={}
            )
            
            filename = f"{report.report_type}_{report.period_start}_{report.period_end}.pdf"
            report.file.save(filename, ContentFile(buffer.getvalue()))
            report.is_generated = True
            report.file_size = buffer.tell()
            report.save()
            
        except Exception as e:
            logger.error(f"Error generating quick report: {str(e)}")
            report.error_message = str(e)
            report.save()
        
        return Response({
            'status': 'success',
            'report': ReportSerializer(report).data,
            'message': 'Relatório gerado com sucesso!'
        })




# Manter outras views (AnalyticsView, DashboardStatsView, etc.) como estão

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
            account__in=accounts,
            date__gte=start_datetime,
            date__lte=end_datetime
        )
        
        # Income vs Expenses
        income = transactions.filter(
            type='CREDIT'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        expenses = transactions.filter(
            type='DEBIT'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Top income sources
        top_income_sources = transactions.filter(
            type='CREDIT',
            counterpart_name__isnull=False
        ).values('counterpart_name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:10]
        
        # Top expense categories
        top_expense_categories = transactions.filter(
            type='DEBIT',
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
                date__gte=week_start_datetime,
                date__lte=week_end_datetime
            )
            
            week_income = week_transactions.filter(
                type='CREDIT'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            week_expenses = week_transactions.filter(
                type='DEBIT'
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
            account__in=accounts,
            date__gte=month_start
        )
        
        total_balance = accounts.aggregate(total=Sum('current_balance'))['total'] or Decimal('0')
        
        income = transactions.filter(
            type='CREDIT'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        expenses = transactions.filter(
            type='DEBIT'
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
                account__in=accounts,
                date__date=current_date
            )
            
            daily_income = transactions.filter(
                type='CREDIT'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            daily_expenses = transactions.filter(
                type='DEBIT'
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
            transaction_type = 'DEBIT'
        else:
            transaction_type = 'CREDIT'
        
        category_data = Transaction.objects.filter(
            account__in=accounts,
            date__gte=start_datetime,
            date__lte=end_datetime,
            type=transaction_type,
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
                account__in=accounts,
                date__gte=current_datetime,
                date__lte=month_end_datetime
            )
            
            income = transactions.filter(
                type='CREDIT'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            expenses = transactions.filter(
                type='DEBIT'
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

 