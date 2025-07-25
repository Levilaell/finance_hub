"""
Banking app views
Financial dashboard and transaction management
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from apps.companies.decorators import requires_plan_feature
from django.db.models import Count, Max, Q, Sum
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

from .models import (BankAccount, BankProvider, 
                     Transaction, TransactionCategory)
from .serializers import (BankAccountSerializer, BankProviderSerializer,
                          DashboardSerializer, ExpenseTrendSerializer, TimeSeriesDataSerializer, TransactionCategorySerializer,
                          TransactionSerializer)


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
    
    @requires_plan_feature('add_bank_account')
    def perform_create(self, serializer):
        """Set company when creating bank account"""
        try:
            company = self.request.user.company
            
            # Check if can add more bank accounts
            if not company.can_add_bank_account():
                limit = company.subscription_plan.max_bank_accounts if company.subscription_plan else 0
                raise ValidationError({
                    'error': 'limit_reached',
                    'message': f'Você atingiu o limite de {limit} contas bancárias do seu plano.',
                    'limit_type': 'bank_accounts',
                    'current': company.active_bank_accounts_count,
                    'limit': limit,
                    'redirect': '/dashboard/subscription/upgrade'
                })
            
            serializer.save(company=company)
        except AttributeError:
            raise ValidationError("Usuário não possui empresa associada")
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync transactions for specific account"""
        from ..tasks import sync_pluggy_account
        
        account = self.get_object()
        
        # Check if account is a Pluggy account
        if not account.external_id:
            return Response({
                'status': 'error',
                'message': 'Esta conta não está conectada via Pluggy'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Queue async sync task
            task = sync_pluggy_account.delay(account.id)
            return Response({
                'status': 'success',
                'message': 'Sincronização iniciada',
                'task_id': task.id
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
    
    @requires_plan_feature('create_transaction')
    def create(self, request, *args, **kwargs):
        """Create a new transaction with automatic usage tracking"""
        company = request.user.company
        
        # Verificar se a conta bancária pertence à empresa do usuário
        bank_account_id = request.data.get('bank_account')
        if bank_account_id:
            try:
                bank_account = BankAccount.objects.get(id=bank_account_id)
                if bank_account.company != company:
                    return Response({
                        'error': 'Conta bancária não pertence à sua empresa'
                    }, status=status.HTTP_403_FORBIDDEN)
            except BankAccount.DoesNotExist:
                return Response({
                    'error': 'Conta bancária não encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Criar a transação usando o método pai
        response = super().create(request, *args, **kwargs)
        
        # Se criou com sucesso, incrementar contador e adicionar avisos
        if response.status_code == 201:
            # Incrementar contador
            company.increment_transaction_count()
            
            # Calcular uso atual
            usage_percentage = company.get_usage_percentage('transactions')
            
            # Adicionar informações de uso se estiver próximo do limite
            if usage_percentage >= 80:
                response.data['usage_warning'] = {
                    'percentage': round(usage_percentage, 1),
                    'used': company.current_month_transactions,
                    'limit': company.subscription_plan.max_transactions,
                    'remaining': company.subscription_plan.max_transactions - company.current_month_transactions,
                    'message': f'Atenção: Você já utilizou {round(usage_percentage, 1)}% do seu limite mensal de transações.'
                }
                
                # Se atingiu 90%, adicionar sugestão de upgrade
                if usage_percentage >= 90:
                    response.data['usage_warning']['upgrade_suggestion'] = True
                    response.data['usage_warning']['message'] = 'Você está próximo do limite! Considere fazer upgrade do seu plano.'
            
            # Log para monitoramento
            logger.info(
                f"Transaction created for company {company.id} - "
                f"Usage: {company.current_month_transactions}/{company.subscription_plan.max_transactions if company.subscription_plan else 'unlimited'}"
            )
        
        return response

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
        category_id = self.request.query_params.get('category_id')
        if category_id:
            if category_id == 'uncategorized':
                filters['category__isnull'] = True
            else:
                filters['category_id'] = category_id
            
        # Account filter
        account_id = self.request.query_params.get('account_id')
        if account_id:
            filters['bank_account_id'] = account_id
            
        # Transaction type filter
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            filters['transaction_type'] = transaction_type
            
        # Amount filters - aplicar no valor absoluto
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        
        if min_amount or max_amount:
            # Precisamos filtrar pelo valor absoluto, então vamos usar Q objects
            amount_q = Q()
            
            if min_amount:
                min_val = float(min_amount)
                print(f"🔍 Backend - min_amount: {min_amount} -> {min_val}")
                # Para valores mínimos, queremos transações onde |amount| >= min_val
                amount_q &= (Q(amount__gte=min_val) | Q(amount__lte=-min_val))
            
            if max_amount:
                max_val = float(max_amount)
                print(f"🔍 Backend - max_amount: {max_amount} -> {max_val}")
                # Para valores máximos, queremos transações onde |amount| <= max_val
                amount_q &= Q(amount__lte=max_val) & Q(amount__gte=-max_val)
            
            # Aplicar o filtro de amount usando Q objects
            queryset = queryset.filter(amount_q)
            
            # Debug para verificar se está funcionando
            if max_amount:
                test_exceeding = queryset.filter(
                    Q(amount__gt=max_val) | Q(amount__lt=-max_val)
                )
                if test_exceeding.exists():
                    print(f"⚠️ Transações que excedem {max_val}:")
                    for t in test_exceeding[:3]:
                        print(f"  - Amount: {t.amount}, |Amount|: {abs(t.amount)}, Description: {t.description[:30]}")
                else:
                    print(f"✅ Nenhuma transação excede o valor máximo de {max_val}")
        
        print(f"🔍 Backend - All query params: {dict(self.request.query_params)}")
        print(f"🔍 Backend - Final filters: {filters}")
            
        # Search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(counterpart_name__icontains=search) |
                Q(notes__icontains=search)
            )
        
        # Apply remaining filters
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
                # Campo is_manually_reviewed removido - categorização automática via Pluggy
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
        
        # Get usage limits data
        from apps.companies.models import ResourceUsage
        
        usage_record = ResourceUsage.get_or_create_current_month(company)
        plan = company.subscription_plan
        
        # Build usage limits info
        if plan:
            usage_limits = {
                'transactions': {
                    'limit': plan.max_transactions,
                    'used': usage_record.transactions_count,
                    'percentage': round((usage_record.transactions_count / plan.max_transactions * 100), 1)
                                if plan.max_transactions and plan.max_transactions not in [0, 999999] else 0
                },
                'bank_accounts': {
                    'limit': plan.max_bank_accounts,
                    'used': accounts.count(),
                    'percentage': round((accounts.count() / plan.max_bank_accounts * 100), 1)
                                if plan.max_bank_accounts and plan.max_bank_accounts not in [0, 999] else 0
                },
                'ai_requests': {
                    'limit': plan.max_ai_requests_per_month,
                    'used': usage_record.total_ai_usage,
                    'percentage': round((usage_record.total_ai_usage / plan.max_ai_requests_per_month * 100), 1)
                                if plan.max_ai_requests_per_month and plan.max_ai_requests_per_month not in [0, 999999] else 0
                }
            }

            
        else:
            # Default limits for free/trial
            usage_limits = {
                'transactions': {'limit': 100, 'used': usage_record.transactions_count, 'percentage': round((usage_record.transactions_count / 100 * 100), 1)},
                'bank_accounts': {'limit': 2, 'used': accounts.count(), 'percentage': round((accounts.count() / 2 * 100), 1)},
                'ai_requests': {'limit': 10, 'used': usage_record.total_ai_usage, 'percentage': round((usage_record.total_ai_usage / 10 * 100), 1)}
            }
        
        data = {
            'current_balance': total_balance,
            'monthly_income': income,
            'monthly_expenses': abs(expenses),
            'monthly_net': income - abs(expenses),
            'recent_transactions': TransactionSerializer(recent_transactions, many=True).data,
            'top_categories': top_categories,
            'accounts_count': accounts.count(),
            'transactions_count': transactions.count(),
            'usage_limits': usage_limits,  # Added usage limits data
        }
        
        return Response(data)




class TimeSeriesAnalyticsView(APIView):
    """
    Time series data for charts and analytics
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from django.db.models import Sum, Q
        from datetime import datetime, timedelta
        
        company = request.user.company
        accounts = BankAccount.objects.filter(company=company, is_active=True)
        
        data = []
        
        return Response(TimeSeriesDataSerializer(data, many=True).data)


class ExpenseTrendsView(APIView):
    """
    Expense trends analysis by category
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response([])


