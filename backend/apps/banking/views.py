"""
Banking app views
Financial dashboard and transaction management
"""
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import requests
from django.conf import settings
from django.db.models import Count, Max, Q, Sum
from django.db import models
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .cache_service import cache_service

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

from .models import (BankAccount, BankProvider, Budget, FinancialGoal, 
                     Transaction, TransactionCategory)
# from core.cache import cache_for_user
from .serializers import (BankAccountSerializer, BankProviderSerializer, BudgetSerializer,
                          DashboardSerializer, EnhancedDashboardSerializer, ExpenseTrendSerializer,
                          FinancialGoalSerializer, TimeSeriesDataSerializer, TransactionCategorySerializer,
                          TransactionSerializer)
from .services import BankingSyncService


class BankAccountViewSet(viewsets.ModelViewSet):
    """
    Bank account management
    """
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        try:
            company = self.request.user.company
        except AttributeError:
            # If user has no company, return empty queryset
            return BankAccount.objects.none()
        
        return BankAccount.objects.filter(
            company=company
        ).select_related('bank_provider').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set company when creating bank account"""
        try:
            company = self.request.user.company
            serializer.save(company=company)
        except AttributeError:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Usuário não possui empresa associada")
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync transactions for specific account"""
        account = self.get_object()
        sync_service = BankingSyncService()
        
        try:
            result = sync_service.sync_account(account)
            return Response({
                'status': 'success',
                'message': 'Sincronização iniciada',
                'sync_id': result.id
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get accounts summary"""
        accounts = self.get_queryset()
        
        total_balance = accounts.aggregate(
            total=Sum('current_balance')
        )['total'] or Decimal('0')
        
        active_count = accounts.filter(is_active=True).count()
        sync_errors = accounts.filter(status='error').count()
        
        return Response({
            'total_accounts': accounts.count(),
            'active_accounts': active_count,
            'total_balance': total_balance,
            'sync_errors': sync_errors,
            'last_sync': accounts.filter(
                last_sync_at__isnull=False
            ).aggregate(latest=Max('last_sync_at'))['latest']
        })


class TransactionViewSet(viewsets.ModelViewSet):
    """
    Transaction management and filtering
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_fields = ['category', 'transaction_type', 'bank_account']
    search_fields = ['description', 'counterpart_name']
    ordering_fields = ['transaction_date', 'amount']
    ordering = ['-transaction_date']
    
    def get_queryset(self):
        queryset = Transaction.objects.filter(
            bank_account__company=self.request.user.company
        ).select_related(
            'bank_account', 
            'category', 
            'subcategory'
        )
        
        # Apply filters from query params
        filters = {}
        
        # Date range filters
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            filters['transaction_date__gte'] = start_date
        if end_date:
            filters['transaction_date__lte'] = end_date
            
        # Category filter
        category_id = self.request.query_params.get('category')
        if category_id:
            filters['category_id'] = category_id
            
        # Account filter
        account_id = self.request.query_params.get('account')
        if account_id:
            filters['bank_account_id'] = account_id
            
        # Transaction type filter
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            filters['transaction_type'] = transaction_type
            
        # Search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(counterpart_name__icontains=search) |
                Q(notes__icontains=search)
            )
        
        return queryset.filter(**filters)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get transaction summary for dashboard"""
        queryset = self.get_queryset()
        
        # Date filtering
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(transaction_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(transaction_date__lte=end_date)
        
        # Calculate summary
        income = queryset.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        expenses = queryset.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        return Response({
            'income': income,
            'expenses': abs(expenses),
            'net': income - abs(expenses),
            'transaction_count': queryset.count()
        })
    
    @action(detail=False, methods=['post'])
    def bulk_categorize(self, request):
        """Bulk categorize transactions"""
        transaction_ids = request.data.get('transaction_ids', [])
        category_id = request.data.get('category_id')
        
        if not transaction_ids or not category_id:
            return Response({
                'error': 'transaction_ids e category_id são obrigatórios'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            category = TransactionCategory.objects.get(id=category_id)
            updated_count = Transaction.objects.filter(
                id__in=transaction_ids,
                bank_account__company=request.user.company
            ).update(
                category=category,
                is_manually_reviewed=True
            )
            
            return Response({
                'status': 'success',
                'updated_count': updated_count
            })
        except TransactionCategory.DoesNotExist:
            return Response({
                'error': 'category_id inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export transactions to CSV"""
        import csv
        from django.http import HttpResponse
        
        queryset = self.get_queryset()
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Data', 'Descrição', 'Valor', 'Tipo', 'Categoria',
            'Conta', 'Contraparte', 'Referência', 'Status'
        ])
        
        for transaction in queryset:
            writer.writerow([
                transaction.transaction_date.strftime('%d/%m/%Y'),
                transaction.description,
                str(transaction.amount).replace('.', ','),
                transaction.get_transaction_type_display(),
                transaction.category.name if transaction.category else '',
                transaction.bank_account.display_name,
                transaction.counterpart_name,
                transaction.reference_number,
                transaction.get_status_display()
            ])
        
        return response


class TransactionCategoryViewSet(viewsets.ModelViewSet):
    """
    Transaction category management
    """
    serializer_class = TransactionCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for categories
    
    def get_queryset(self):
        return TransactionCategory.objects.filter(is_active=True)


class BankProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Available bank providers
    """
    serializer_class = BankProviderSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = BankProvider.objects.filter(is_active=True)


class DashboardView(APIView):
    """
    Main financial dashboard data
    """
    permission_classes = [permissions.IsAuthenticated]
    
    # @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def get(self, request):
        try:
            company = request.user.company
        except AttributeError:
            return Response({
                'error': 'Usuário não possui empresa associada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get current month data
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get all company accounts
        accounts = BankAccount.objects.filter(company=company, is_active=True)
        
        # Current balances
        total_balance = accounts.aggregate(
            total=Sum('current_balance')
        )['total'] or Decimal('0')
        
        # This month transactions (current month only)
        transactions = Transaction.objects.filter(
            bank_account__in=accounts,
            transaction_date__gte=start_of_month
        )
        
        # Income and expenses this month
        income = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        expenses = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Recent transactions
        recent_transactions = Transaction.objects.filter(
            bank_account__in=accounts
        ).select_related('category', 'bank_account')[:10]
        
        # Top categories this month
        top_categories = transactions.filter(
            category__isnull=False
        ).values(
            'category__name', 
            'category__icon'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:5]
        
        data = {
            'current_balance': total_balance,
            'monthly_income': income,
            'monthly_expenses': abs(expenses),
            'monthly_net': income - abs(expenses),
            'recent_transactions': TransactionSerializer(recent_transactions, many=True).data,
            'top_categories': top_categories,
            'accounts_count': accounts.count(),
            'transactions_count': transactions.count(),
        }
        
        return Response(data)


class EnhancedDashboardView(APIView):
    """
    Enhanced dashboard with all financial features
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from django.db.models import Sum, Count, Q, Avg
        from datetime import datetime, timedelta
        import calendar
        
        try:
            company = request.user.company
        except AttributeError:
            return Response({
                'error': 'Usuário não possui empresa associada'
            }, status=status.HTTP_400_BAD_REQUEST)
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Basic dashboard data (existing)
        accounts = BankAccount.objects.filter(company=company, is_active=True)
        total_balance = accounts.aggregate(total=Sum('current_balance'))['total'] or Decimal('0')
        
        # This month transactions (current month only)
        transactions = Transaction.objects.filter(
            bank_account__in=accounts,
            transaction_date__gte=start_of_month
        )
        
        income = transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        expenses = transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        recent_transactions = Transaction.objects.filter(
            bank_account__in=accounts
        ).select_related('category', 'bank_account')[:10]
        
        top_categories = transactions.filter(
            category__isnull=False
        ).values('category__name', 'category__icon').annotate(
            total=Sum('amount'), count=Count('id')
        ).order_by('-total')[:5]
        
        # Budget data
        active_budgets = Budget.objects.filter(
            company=company,
            status='active',
            start_date__lte=now.date(),
            end_date__gte=now.date()
        )
        
        for budget in active_budgets:
            budget.update_spent_amount()
        
        budgets_summary = {
            'total_budgets': active_budgets.count(),
            'total_budget_amount': active_budgets.aggregate(total=Sum('amount'))['total'] or Decimal('0'),
            'total_spent': active_budgets.aggregate(total=Sum('spent_amount'))['total'] or Decimal('0'),
            'exceeded_count': active_budgets.filter(status='exceeded').count(),
        }
        
        # Goals data
        active_goals = FinancialGoal.objects.filter(
            company=company,
            status='active'
        )
        
        for goal in active_goals:
            goal.update_progress()
        
        goals_summary = {
            'total_goals': active_goals.count(),
            'completed_goals': FinancialGoal.objects.filter(company=company, status='completed').count(),
            'total_target_amount': active_goals.aggregate(total=Sum('target_amount'))['total'] or Decimal('0'),
            'total_current_amount': active_goals.aggregate(total=Sum('current_amount'))['total'] or Decimal('0'),
        }
        
        # Time series data for charts (last 6 months)
        monthly_trends = []
        for i in range(6):
            month_start = (now - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = month_start.replace(day=28) + timedelta(days=4)
            month_end = next_month - timedelta(days=next_month.day)
            
            month_transactions = Transaction.objects.filter(
                bank_account__in=accounts,
                transaction_date__gte=month_start,
                transaction_date__lte=month_end
            )
            
            month_income = month_transactions.filter(
                transaction_type__in=['credit', 'transfer_in', 'pix_in']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            month_expenses = month_transactions.filter(
                transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Calculate balance at end of month
            balance_transactions = Transaction.objects.filter(
                bank_account__in=accounts,
                transaction_date__lte=month_end
            ).aggregate(
                total_in=Sum('amount', filter=Q(transaction_type__in=['credit', 'transfer_in', 'pix_in'])),
                total_out=Sum('amount', filter=Q(transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']))
            )
            
            # For balance calculation, total_out should already be negative from the query filter
            total_in = balance_transactions['total_in'] or Decimal('0')
            total_out = balance_transactions['total_out'] or Decimal('0')
            balance = total_in + total_out  # total_out is already negative
            
            monthly_trends.append({
                'date': month_start.date(),
                'income': month_income,
                'expenses': abs(month_expenses),
                'balance': balance,
                'net_flow': month_income - abs(month_expenses)
            })
        
        # Expense trends by category
        expense_trends = []
        for category_data in top_categories[:5]:
            category_name = category_data['category__name']
            
            # Current month
            current_amount = category_data['total']
            
            # Previous month
            prev_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
            prev_month_end = start_of_month - timedelta(days=1)
            
            prev_amount = Transaction.objects.filter(
                bank_account__in=accounts,
                category__name=category_name,
                transaction_date__gte=prev_month_start,
                transaction_date__lte=prev_month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            change = current_amount - abs(prev_amount)
            change_percentage = 0
            if prev_amount != 0:
                change_percentage = (change / abs(prev_amount)) * 100
            
            expense_trends.append({
                'period': now.strftime('%Y-%m'),
                'category': category_name,
                'amount': abs(current_amount),
                'transaction_count': category_data['count'],
                'change_from_previous': change,
                'change_percentage': change_percentage
            })
        
        # Comparative analysis
        prev_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
        prev_month_end = start_of_month - timedelta(days=1)
        
        prev_transactions = Transaction.objects.filter(
            bank_account__in=accounts,
            transaction_date__gte=prev_month_start,
            transaction_date__lte=prev_month_end
        )
        
        prev_income = prev_transactions.filter(
            transaction_type__in=['credit', 'transfer_in', 'pix_in']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        prev_expenses = prev_transactions.filter(
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        income_variance = income - prev_income
        expense_variance = abs(expenses) - abs(prev_expenses)
        
        income_comparison = {
            'current_period': income,
            'previous_period': prev_income,
            'variance': income_variance,
            'variance_percentage': (income_variance / prev_income * 100) if prev_income else 0,
            'trend': 'up' if income_variance > 0 else 'down' if income_variance < 0 else 'stable'
        }
        
        expense_comparison = {
            'current_period': abs(expenses),
            'previous_period': abs(prev_expenses),
            'variance': expense_variance,
            'variance_percentage': (expense_variance / abs(prev_expenses) * 100) if prev_expenses else 0,
            'trend': 'up' if expense_variance > 0 else 'down' if expense_variance < 0 else 'stable'
        }
        
        # Financial insights
        insights = []
        
        # Budget insights
        for budget in active_budgets:
            if budget.is_exceeded:
                insights.append(f"Orçamento '{budget.name}' foi excedido em {budget.spent_percentage:.1f}%")
            elif budget.is_alert_threshold_reached:
                insights.append(f"Orçamento '{budget.name}' atingiu {budget.spent_percentage:.1f}% do limite")
        
        # Spending insights
        if expense_variance > 0:
            insights.append(f"Gastos aumentaram {expense_comparison['variance_percentage']:.1f}% comparado ao mês anterior")
        
        # Goal insights
        for goal in active_goals:
            if goal.days_remaining and goal.days_remaining < 30:
                insights.append(f"Meta '{goal.name}' tem prazo em {goal.days_remaining} dias")
        
        # Alerts
        alerts = []
        
        # Budget alerts
        for budget in active_budgets.filter(is_alert_enabled=True):
            if budget.is_exceeded:
                alerts.append({
                    'type': 'budget_exceeded',
                    'message': f"Orçamento '{budget.name}' excedido",
                    'severity': 'high'
                })
            elif budget.is_alert_threshold_reached:
                alerts.append({
                    'type': 'budget_warning',
                    'message': f"Orçamento '{budget.name}' próximo do limite",
                    'severity': 'medium'
                })
        
        data = {
            # Basic data
            'current_balance': total_balance,
            'monthly_income': income,
            'monthly_expenses': abs(expenses),
            'monthly_net': income - abs(expenses),
            'recent_transactions': TransactionSerializer(recent_transactions, many=True).data,
            'transactions_count': transactions.count(),
            'top_categories': list(top_categories),
            'accounts_count': accounts.count(),
            
            # Enhanced data
            'active_budgets': BudgetSerializer(active_budgets, many=True).data,
            'budgets_summary': budgets_summary,
            'active_goals': FinancialGoalSerializer(active_goals, many=True).data,
            'goals_summary': goals_summary,
            'monthly_trends': monthly_trends,
            'expense_trends': expense_trends,
            'income_comparison': income_comparison,
            'expense_comparison': expense_comparison,
            'financial_insights': insights,
            'alerts': alerts,
        }
        
        # Cache the dashboard data
        cache_service.set_dashboard_summary(company.id, request.user.id, data)
        
        return Response(data)


class BudgetViewSet(viewsets.ModelViewSet):
    """
    Budget management viewset
    """
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Budget.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def update_spent(self, request, pk=None):
        """Update spent amount for budget"""
        budget = self.get_object()
        budget.update_spent_amount()
        return Response(self.get_serializer(budget).data)
    
    @action(detail=False)
    def summary(self, request):
        """Get budget summary statistics"""
        company = request.user.company
        budgets = self.get_queryset().filter(status='active')
        
        total_amount = budgets.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        total_spent = budgets.aggregate(total=Sum('spent_amount'))['total'] or Decimal('0')
        exceeded_count = budgets.filter(status='exceeded').count()
        
        return Response({
            'total_budgets': budgets.count(),
            'total_amount': total_amount,
            'total_spent': total_spent,
            'remaining': total_amount - total_spent,
            'exceeded_count': exceeded_count,
            'on_track_count': budgets.count() - exceeded_count,
        })


class FinancialGoalViewSet(viewsets.ModelViewSet):
    """
    Financial goal management viewset
    """
    serializer_class = FinancialGoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return FinancialGoal.objects.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update goal progress"""
        goal = self.get_object()
        goal.update_progress()
        return Response(self.get_serializer(goal).data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark goal as completed"""
        goal = self.get_object()
        goal.status = 'completed'
        goal.completed_at = timezone.now()
        goal.save()
        return Response(self.get_serializer(goal).data)
    
    @action(detail=False)
    def summary(self, request):
        """Get goals summary statistics"""
        goals = self.get_queryset()
        active_goals = goals.filter(status='active')
        
        total_target = active_goals.aggregate(total=Sum('target_amount'))['total'] or Decimal('0')
        total_current = active_goals.aggregate(total=Sum('current_amount'))['total'] or Decimal('0')
        
        return Response({
            'total_goals': goals.count(),
            'active_goals': active_goals.count(),
            'completed_goals': goals.filter(status='completed').count(),
            'total_target_amount': total_target,
            'total_current_amount': total_current,
            'overall_progress': (total_current / total_target * 100) if total_target else 0,
        })


class TimeSeriesAnalyticsView(APIView):
    """
    Time series data for charts and analytics
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from django.db.models import Sum, Q
        from datetime import datetime, timedelta
        
        company = request.user.company
        period = request.query_params.get('period', '6months')  # 6months, 1year, 2years
        
        # Calculate period range
        now = timezone.now()
        if period == '1year':
            months = 12
        elif period == '2years':
            months = 24
        else:
            months = 6
        
        accounts = BankAccount.objects.filter(company=company, is_active=True)
        data = []
        
        for i in range(months):
            month_start = (now - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = month_start.replace(day=28) + timedelta(days=4)
            month_end = next_month - timedelta(days=next_month.day)
            
            transactions = Transaction.objects.filter(
                bank_account__in=accounts,
                transaction_date__gte=month_start,
                transaction_date__lte=month_end
            )
            
            income = transactions.filter(
                transaction_type__in=['credit', 'transfer_in', 'pix_in']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            expenses = transactions.filter(
                transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Calculate balance at end of month
            balance_transactions = Transaction.objects.filter(
                bank_account__in=accounts,
                transaction_date__lte=month_end
            ).aggregate(
                total_in=Sum('amount', filter=Q(transaction_type__in=['credit', 'transfer_in', 'pix_in'])),
                total_out=Sum('amount', filter=Q(transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']))
            )
            
            # For balance calculation, total_out should already be negative from the query filter
            total_in = balance_transactions['total_in'] or Decimal('0')
            total_out = balance_transactions['total_out'] or Decimal('0')
            balance = total_in + total_out  # total_out is already negative
            
            data.append({
                'date': month_start.date(),
                'income': income,
                'expenses': abs(expenses),
                'balance': balance,
                'net_flow': income - abs(expenses)
            })
        
        return Response(TimeSeriesDataSerializer(reversed(data), many=True).data)


class ExpenseTrendsView(APIView):
    """
    Expense trends analysis by category
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from django.db.models import Sum, Count
        from datetime import timedelta
        
        company = request.user.company
        period = request.query_params.get('period', 'monthly')  # monthly, quarterly
        
        accounts = BankAccount.objects.filter(company=company, is_active=True)
        now = timezone.now()
        
        if period == 'quarterly':
            months = 3
        else:
            months = 1
        
        # Current period
        current_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if period == 'quarterly':
            current_start = current_start.replace(month=((now.month-1)//3)*3+1)
        
        # Previous period
        prev_start = current_start - timedelta(days=30*months)
        prev_end = current_start - timedelta(days=1)
        
        # Get top categories from current period
        current_transactions = Transaction.objects.filter(
            bank_account__in=accounts,
            transaction_date__gte=current_start,
            transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
        )
        
        top_categories = current_transactions.filter(
            category__isnull=False
        ).values('category__name').annotate(
            amount=Sum('amount'),
            count=Count('id')
        ).order_by('-amount')[:10]
        
        trends = []
        for cat_data in top_categories:
            category_name = cat_data['category__name']
            current_amount = abs(cat_data['amount'])
            
            # Previous period amount
            prev_amount = Transaction.objects.filter(
                bank_account__in=accounts,
                category__name=category_name,
                transaction_date__gte=prev_start,
                transaction_date__lte=prev_end,
                transaction_type__in=['debit', 'transfer_out', 'pix_out', 'fee']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            prev_amount = abs(prev_amount)
            change = current_amount - prev_amount
            change_percentage = (change / prev_amount * 100) if prev_amount else 0
            
            trends.append({
                'period': current_start.strftime('%Y-%m'),
                'category': category_name,
                'amount': current_amount,
                'transaction_count': cat_data['count'],
                'change_from_previous': change,
                'change_percentage': change_percentage
            })
        
        return Response(ExpenseTrendSerializer(trends, many=True).data)


class ConnectBankAccountView(APIView):
    """
    Initiate real Open Banking connection via OAuth2 flow
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        bank_code = request.data.get('bank_code')
        authorization_code = request.data.get('authorization_code')
        consent_id = request.data.get('consent_id')
        
        if not bank_code:
            return Response({
                'error': 'bank_code é obrigatório'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            bank_provider = BankProvider.objects.get(code=bank_code, is_active=True)
        except BankProvider.DoesNotExist:
            return Response({
                'error': 'Banco não encontrado ou não suportado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Check if we should use Pluggy instead of sandbox
            use_pluggy = request.data.get('use_pluggy', False)
            
            if use_pluggy and hasattr(settings, 'PLUGGY_CLIENT_ID'):
                # Use Pluggy for real bank connection
                from .pluggy_views import PluggyConnectTokenView
                pluggy_view = PluggyConnectTokenView()
                
                # Return the Pluggy connect token response
                return pluggy_view.post(request)
            
            from .services import OpenBankingService
            open_banking = OpenBankingService()
            
            # Get or create company for user
            from apps.companies.models import Company
            company, created = Company.objects.get_or_create(
                owner=request.user,
                defaults={'name': f'Empresa {request.user.first_name}'}
            )
            
            if authorization_code:
                # Complete OAuth flow - exchange code for tokens and create account
                credentials = {'authorization_code': authorization_code}
                connection_result = open_banking.connect_account(bank_code, credentials)
                
                if connection_result.get('status') == 'connected':
                    # Create bank account with real data
                    account_info = connection_result['account_info']
                    
                    bank_account = BankAccount.objects.create(
                        company=company,
                        bank_provider=bank_provider,
                        account_type=account_info.get('accountType', 'checking'),
                        account_number=account_info.get('accountNumber', ''),
                        account_digit='',
                        agency=account_info.get('agency', ''),
                        external_id=connection_result['account_id'],
                        access_token=connection_result['access_token'],
                        refresh_token=connection_result.get('refresh_token', ''),
                        token_expires_at=timezone.now() + timedelta(seconds=connection_result.get('expires_in', 3600)),
                        current_balance=Decimal(str(account_info.get('balance', 0))),
                        available_balance=Decimal(str(account_info.get('availableBalance', 0))),
                        status='active',
                        is_active=True,
                        nickname=f'Conta {bank_provider.name}'
                    )
                    
                    # Trigger initial sync of transactions
                    sync_service = BankingSyncService()
                    try:
                        sync_service.sync_account(bank_account, days_back=30)
                    except Exception as sync_error:
                        logger.warning(f"Initial sync failed: {sync_error}")
                    
                    return Response({
                        'status': 'success',
                        'message': f'Conta {bank_provider.name} conectada com sucesso via Open Banking',
                        'account_id': bank_account.id,
                        'account_name': bank_account.nickname,
                        'balance': float(bank_account.current_balance),
                        'connection_type': 'real_open_banking'
                    })
                else:
                    return Response({
                        'error': 'Falha na conexão com Open Banking'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            else:
                # Initiate consent flow
                connection_result = open_banking.connect_account(bank_code, {})
                
                if connection_result.get('status') == 'consent_required':
                    return Response({
                        'status': 'consent_required',
                        'consent_id': connection_result['consent_id'],
                        'authorization_url': connection_result['authorization_url'],
                        'message': 'Autorização necessária. Redirecione o usuário para a URL de autorização.',
                        'instructions': 'Após autorizar, retorne com o código de autorização obtido.'
                    })
                else:
                    return Response({
                        'error': 'Falha ao iniciar fluxo de consentimento'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
        except Exception as e:
            logger.error(f"Error connecting bank account: {e}")
            return Response({
                'error': f'Erro na conexão Open Banking: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OpenBankingCallbackView(APIView):
    """
    Handle OAuth callback from Open Banking authorization
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        authorization_code = request.data.get('code')
        state = request.data.get('state')
        bank_code = request.data.get('bank_code')
        
        if not authorization_code or not bank_code:
            return Response({
                'error': 'Código de autorização e bank_code são obrigatórios'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get or create company for user
            from apps.companies.models import Company
            from .services import OpenBankingService
            from .models import BankProvider, BankAccount
            from decimal import Decimal
            from django.utils import timezone
            from datetime import timedelta
            
            company, created = Company.objects.get_or_create(
                owner=request.user,
                defaults={'name': f'Empresa {request.user.first_name}'}
            )
            
            try:
                bank_provider = BankProvider.objects.get(code=bank_code, is_active=True)
            except BankProvider.DoesNotExist:
                return Response({
                    'error': 'Banco não encontrado ou não suportado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            open_banking = OpenBankingService()
            
            # Complete OAuth flow - exchange code for tokens and create account
            credentials = {'authorization_code': authorization_code}
            connection_result = open_banking.connect_account(bank_code, credentials)
            
            if connection_result.get('status') == 'connected':
                # Create bank account with real data
                account_info = connection_result['account_info']
                
                bank_account = BankAccount.objects.create(
                    company=company,
                    bank_provider=bank_provider,
                    account_type=account_info.get('accountType', 'checking'),
                    account_number=account_info.get('accountNumber', ''),
                    account_digit='',
                    agency=account_info.get('agency', ''),
                    external_id=connection_result.get('account_id', f'mock-{bank_code}-{timezone.now().timestamp()}'),
                    access_token=connection_result.get('access_token', ''),
                    refresh_token=connection_result.get('refresh_token', ''),
                    token_expires_at=timezone.now() + timedelta(seconds=connection_result.get('expires_in', 3600)),
                    current_balance=Decimal(str(account_info.get('balance', 0))),
                    available_balance=Decimal(str(account_info.get('availableBalance', 0))),
                    status='active',
                    is_active=True,
                    nickname=f'Conta {bank_provider.name}'
                )
                
                return Response({
                    'status': 'success',
                    'message': f'Conta {bank_provider.name} conectada com sucesso via Open Banking',
                    'account_id': bank_account.id,
                    'account_name': bank_account.nickname,
                    'balance': float(bank_account.current_balance),
                    'connection_type': 'real_open_banking'
                })
            else:
                return Response({
                    'error': 'Falha na conexão com Open Banking'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return Response({
                'error': f'Erro no callback OAuth: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefreshTokenView(APIView):
    """
    Refresh expired Open Banking access tokens
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, account_id):
        try:
            account = BankAccount.objects.get(
                id=account_id,
                company=request.user.company
            )
        except BankAccount.DoesNotExist:
            return Response({
                'error': 'Conta não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not account.refresh_token:
            return Response({
                'error': 'Token de refresh não disponível'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .services import OpenBankingService
            open_banking = OpenBankingService()
            
            # Get bank endpoints
            endpoints = open_banking._get_bank_endpoints(account.bank_provider.code)
            
            # Create client assertion for token refresh
            jwt_assertion = open_banking._create_jwt_assertion(endpoints['token_endpoint'])
            
            token_data = {
                'grant_type': 'refresh_token',
                'refresh_token': account.refresh_token,
                'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
                'client_assertion': jwt_assertion
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'x-fapi-interaction-id': str(uuid.uuid4())
            }
            
            response = requests.post(
                endpoints['token_endpoint'],
                data=token_data,
                headers=headers,
                cert=(open_banking.cert_path, open_banking.key_path) if open_banking.cert_path else None,
                verify=open_banking.ca_cert_path if open_banking.ca_cert_path else True,
                timeout=open_banking.timeout
            )
            
            if response.status_code == 200:
                tokens = response.json()
                
                # Update account with new tokens
                account.access_token = tokens['access_token']
                if 'refresh_token' in tokens:
                    account.refresh_token = tokens['refresh_token']
                account.token_expires_at = timezone.now() + timedelta(seconds=tokens.get('expires_in', 3600))
                account.status = 'active'
                account.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Token atualizado com sucesso',
                    'expires_in': tokens.get('expires_in', 3600)
                })
            else:
                account.status = 'expired'
                account.save()
                return Response({
                    'error': f'Falha ao atualizar token: {response.status_code}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            account.status = 'error'
            account.save()
            return Response({
                'error': f'Erro ao atualizar token: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SyncBankAccountView(APIView):
    """
    Manually trigger bank account sync
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, account_id):
        try:
            account = BankAccount.objects.get(
                id=account_id,
                company=request.user.company
            )
        except BankAccount.DoesNotExist:
            return Response({
                'error': 'Conta não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        sync_service = BankingSyncService()
        
        try:
            sync_log = sync_service.sync_account(account)
            return Response({
                'status': 'success',
                'message': 'Sincronização iniciada',
                'sync_id': sync_log.id
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)