"""
Reports app views
Financial reporting and analytics
"""
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum, Avg
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from apps.banking.models import BankAccount, Transaction, TransactionCategory
from .models import Report, ReportSchedule, ReportTemplate
from .serializers import (
    ReportScheduleSerializer,
    ReportSerializer,
    ReportTemplateSerializer,
)
from .tasks import generate_report_task


class ReportViewSet(viewsets.ModelViewSet):
    """
    Report management viewset
    """
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Report.objects.filter(
            company=self.request.user.company
        ).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Generate a new report"""
        report_type = request.data.get('report_type')
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        
        if not all([report_type, period_start, period_end]):
            return Response({
                'error': 'report_type, period_start, and period_end are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create report instance
        report = Report.objects.create(
            company=request.user.company,
            report_type=report_type,
            title=request.data.get('title', f'{report_type} Report'),
            period_start=period_start,
            period_end=period_end,
            created_by=request.user
        )
        
        # Queue report generation
        generate_report_task.delay(report.id)
        
        return Response(
            ReportSerializer(report).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download report file"""
        report = self.get_object()
        
        if not report.is_generated or not report.file:
            return Response({
                'error': 'Report is not ready for download'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            return FileResponse(
                report.file.open('rb'),
                as_attachment=True,
                filename=f'{report.title}_{report.created_at.strftime("%Y%m%d")}.{report.file_format}'
            )
        except FileNotFoundError:
            raise Http404("Report file not found")
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get reports summary statistics"""
        company = request.user.company
        reports = self.get_queryset()
        
        return Response({
            'total_reports': reports.count(),
            'reports_by_type': reports.values('report_type').annotate(count=Count('id')),
            'recent_reports': ReportSerializer(reports[:5], many=True).data
        })


class ReportScheduleViewSet(viewsets.ModelViewSet):
    """
    Report schedule management
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
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new scheduled report"""
        from datetime import datetime, timedelta
        
        # Calculate next_run_at based on frequency
        frequency = request.data.get('frequency', 'monthly')
        now = timezone.now()
        
        if frequency == 'daily':
            next_run = now + timedelta(days=1)
        elif frequency == 'weekly':
            next_run = now + timedelta(weeks=1)
        elif frequency == 'monthly':
            next_run = now + timedelta(days=30)
        elif frequency == 'quarterly':
            next_run = now + timedelta(days=90)
        elif frequency == 'yearly':
            next_run = now + timedelta(days=365)
        else:
            next_run = now + timedelta(days=30)
        
        # Add next_run_at to the request data
        request.data['next_run_at'] = next_run.isoformat()
        
        return super().create(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle schedule active status"""
        schedule = self.get_object()
        schedule.is_active = not schedule.is_active
        schedule.save()
        
        return Response({
            'status': 'success',
            'is_active': schedule.is_active
        })
    
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """Run scheduled report immediately"""
        schedule = self.get_object()
        
        # Create report based on schedule
        report = Report.objects.create(
            company=schedule.company,
            report_type=schedule.report_type,
            title=f'{schedule.get_report_type_display()} - Manual Run',
            period_start=timezone.now().date() - timedelta(days=30),
            period_end=timezone.now().date(),
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
            'message': 'Report generation started'
        })


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """
    Report template management
    """
    serializer_class = ReportTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ReportTemplate.objects.filter(
            Q(company=self.request.user.company) | Q(is_system=True),
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
        
        # Get all company accounts
        accounts = BankAccount.objects.filter(company=company, is_active=True)
        
        # Get transactions for period
        transactions = Transaction.objects.filter(
            bank_account__in=accounts,
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
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
            
            week_transactions = transactions.filter(
                transaction_date__gte=week_start,
                transaction_date__lte=week_end
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
        
        if category_type == 'expense':
            transaction_types = ['debit', 'transfer_out', 'pix_out', 'fee']
        else:
            transaction_types = ['credit', 'transfer_in', 'pix_in']
        
        category_data = Transaction.objects.filter(
            bank_account__in=accounts,
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
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
            
            transactions = Transaction.objects.filter(
                bank_account__in=accounts,
                transaction_date__gte=current_date,
                transaction_date__lte=month_end
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
    """AI-powered financial insights"""
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
        
        # Get transactions for the period
        # Convert dates to datetime for proper comparison
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        transactions = Transaction.objects.filter(
            bank_account__in=accounts,
            transaction_date__gte=start_datetime,
            transaction_date__lte=end_datetime
        )
        
        # Calculate insights
        insights = []
        
        # 1. Cash Flow Analysis
        income = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        expenses = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        net_flow = income - abs(expenses)
        
        if net_flow > 0:
            insights.append({
                'type': 'success',
                'title': 'Fluxo de Caixa Positivo',
                'description': f'Você manteve um fluxo de caixa positivo de {net_flow:,.2f}',
                'value': f'R$ {net_flow:,.2f}',
                'trend': 'up'
            })
        else:
            insights.append({
                'type': 'warning',
                'title': 'Fluxo de Caixa Negativo',
                'description': f'Suas despesas superaram a receita em {abs(net_flow):,.2f}',
                'value': f'R$ {abs(net_flow):,.2f}',
                'trend': 'down'
            })
        
        # 2. Top Spending Category
        top_expense_category = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee'],
            category__isnull=False
        ).values('category__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('total').first()
        
        if top_expense_category:
            total_expenses = abs(expenses)
            percentage = (abs(top_expense_category['total']) / total_expenses * 100) if total_expenses > 0 else 0
            insights.append({
                'type': 'info',
                'title': 'Maior Categoria de Gastos',
                'description': f'{top_expense_category["category__name"]} representa {percentage:.1f}% dos gastos',
                'value': f'R$ {abs(top_expense_category["total"]):,.2f}',
            })
        
        # 3. Savings Rate
        if income > 0:
            savings_rate = (net_flow / income) * 100
            insights.append({
                'type': 'success' if savings_rate > 20 else 'warning' if savings_rate > 10 else 'danger',
                'title': 'Taxa de Poupança',
                'description': f'Você está poupando {savings_rate:.1f}% da sua renda',
                'value': f'{savings_rate:.1f}%',
                'trend': 'up' if savings_rate > 0 else 'down'
            })
        
        # 4. Transaction Volume Insight
        days_in_period = (end_date - start_date).days + 1
        daily_transactions = transactions.count() / days_in_period if days_in_period > 0 else 0
        
        if daily_transactions > 15:
            insights.append({
                'type': 'info',
                'title': 'Alto Volume de Transações',
                'description': f'Você tem {daily_transactions:.1f} transações por dia em média',
                'value': f'{daily_transactions:.1f}/dia'
            })
        
        # 5. Predictions (simplified)
        if days_in_period >= 30:
            monthly_income = income / (days_in_period / 30)
            monthly_expenses = abs(expenses) / (days_in_period / 30)
            
            predictions = {
                'next_month_income': float(monthly_income),
                'next_month_expenses': float(monthly_expenses),
                'projected_savings': float(monthly_income - monthly_expenses)
            }
        else:
            predictions = {
                'next_month_income': float(income * 30 / days_in_period),
                'next_month_expenses': float(abs(expenses) * 30 / days_in_period),
                'projected_savings': float(net_flow * 30 / days_in_period)
            }
        
        # 6. Recommendations
        recommendations = []
        
        if income > 0:
            savings_rate = (net_flow / income) * 100
            if savings_rate < 10:
                recommendations.append({
                    'type': 'warning',
                    'title': 'Aumente sua Taxa de Poupança',
                    'description': 'Tente economizar pelo menos 10% da sua renda mensal'
                })
        
        if daily_transactions > 20:
            recommendations.append({
                'type': 'info',
                'title': 'Automatize a Categorização',
                'description': 'Com muitas transações, considere usar regras automáticas'
            })
        
        if top_expense_category:
            total_expenses = abs(expenses)
            percentage = (abs(top_expense_category['total']) / total_expenses * 100) if total_expenses > 0 else 0
            if percentage > 40:
                recommendations.append({
                    'type': 'warning',
                    'title': 'Diversifique seus Gastos',
                    'description': f'Mais de 40% dos gastos estão em {top_expense_category["category__name"]}'
                })
        
        return Response({
            'insights': insights,
            'predictions': predictions,
            'recommendations': recommendations,
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': days_in_period
            }
        })