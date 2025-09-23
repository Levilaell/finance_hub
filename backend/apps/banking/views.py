"""
Banking API Views
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.db import models
from django.db.models import Q, Sum, Count
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.cache import cache

from .models import (
    PluggyConnector, PluggyItem, BankAccount, Transaction, 
    TransactionCategory, ItemWebhook
)
from .serializers import (
    PluggyConnectorSerializer, PluggyItemSerializer, BankAccountSerializer,
    TransactionSerializer, TransactionUpdateSerializer, TransactionCategorySerializer,
    CreateItemSerializer, CreateCategorySerializer, DashboardDataSerializer,
    SyncResultSerializer, BulkSyncResultSerializer
)
from .integrations.pluggy.sync_service import PluggySyncService
from .integrations.pluggy.client import PluggyError

logger = logging.getLogger('apps.banking.views')


class PluggyConnectorViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for Pluggy connectors (banks)
    """
    serializer_class = PluggyConnectorSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'country', 'is_open_finance', 'is_sandbox']
    search_fields = ['name', 'type']
    ordering_fields = ['name', 'type']
    ordering = ['name']
    
    def get_queryset(self):
        # Only show non-sandbox connectors by default
        queryset = PluggyConnector.objects.filter(is_sandbox=False)
        
        # Allow sandbox if explicitly requested
        if self.request.query_params.get('include_sandbox') == 'true':
            queryset = PluggyConnector.objects.all()
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def sync(self, request):
        """Sync connectors from Pluggy API"""
        include_sandbox = request.data.get('include_sandbox', False)
        
        try:
            sync_service = PluggySyncService()
            result = sync_service.sync_connectors(include_sandbox=include_sandbox)
            
            return Response({
                'message': 'Connectors synced successfully',
                'result': result
            })
        except Exception as e:
            logger.error(f"Failed to sync connectors: {e}")
            return Response(
                {'error': 'Failed to sync connectors'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PluggyItemViewSet(ModelViewSet):
    """
    ViewSet for Pluggy items (bank connections)
    """
    serializer_class = PluggyItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'connector']
    ordering_fields = ['created_at', 'last_successful_update']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return PluggyItem.objects.filter(company=self.request.user.company)
    
    def create(self, request):
        """Create a new bank connection"""
        serializer = CreateItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            sync_service = PluggySyncService()
            item = sync_service.create_item(
                company=request.user.company,
                connector_id=serializer.validated_data['connector_id'],
                credentials=serializer.validated_data['credentials'],
                webhook_url=serializer.validated_data.get('webhook_url'),
                products=serializer.validated_data.get('products')
            )
            
            # Return the created item
            response_serializer = PluggyItemSerializer(item)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except PluggyError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to create item: {e}")
            return Response(
                {'error': 'Failed to create bank connection'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync data for a specific item"""
        item = self.get_object()
        
        try:
            sync_service = PluggySyncService()
            result = sync_service.sync_item_data(item)
            
            serializer = SyncResultSerializer(result)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Failed to sync item {pk}: {e}")
            return Response(
                {'error': 'Failed to sync data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get sync status for an item"""
        item = self.get_object()
        
        try:
            sync_service = PluggySyncService()
            status_data = sync_service.get_sync_status(item)
            
            return Response(status_data)
            
        except Exception as e:
            logger.error(f"Failed to get status for item {pk}: {e}")
            return Response(
                {'error': 'Failed to get sync status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def sync_all(self, request):
        """Sync all items for the company"""
        try:
            sync_service = PluggySyncService()
            result = sync_service.sync_company_data(request.user.company)
            
            serializer = BulkSyncResultSerializer(result)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Failed to sync all items: {e}")
            return Response(
                {'error': 'Failed to sync all connections'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BankAccountViewSet(ReadOnlyModelViewSet):
    """
    ViewSet for bank accounts
    """
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'subtype', 'is_active', 'item']
    search_fields = ['name', 'number', 'marketing_name']
    ordering_fields = ['name', 'balance', 'created_at']
    ordering = ['-balance']
    
    def get_queryset(self):
        return BankAccount.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).select_related('item__connector')
    
    @action(detail=True, methods=['post'])
    def sync_transactions(self, request, pk=None):
        """Sync transactions for a specific account"""
        account = self.get_object()
        
        # Parse date range
        from_date = request.data.get('from_date')
        to_date = request.data.get('to_date')
        
        if from_date:
            from_date = datetime.fromisoformat(from_date)
        if to_date:
            to_date = datetime.fromisoformat(to_date)
        
        try:
            sync_service = PluggySyncService()
            result = sync_service.sync_transactions(
                account=account,
                from_date=from_date,
                to_date=to_date
            )
            
            return Response({
                'message': 'Transactions synced successfully',
                'result': result
            })
            
        except Exception as e:
            logger.error(f"Failed to sync transactions for account {pk}: {e}")
            return Response(
                {'error': 'Failed to sync transactions'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransactionViewSet(ModelViewSet):
    """
    ViewSet for transactions
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'status', 'account', 'category']
    search_fields = ['description', 'pluggy_category_description']
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date', '-created_at']
    
    def get_queryset(self):
        return Transaction.objects.filter(
            company=self.request.user.company,
            is_deleted=False
        ).select_related('account', 'category', 'account__item__connector')
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return TransactionUpdateSerializer
        return TransactionSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete transaction"""
        transaction = self.get_object()
        transaction.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get transaction statistics"""
        # Parse date range
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        
        if not from_date or not to_date:
            # Default to current month
            today = timezone.now().date()
            from_date = today.replace(day=1)
            to_date = today
        else:
            from_date = datetime.fromisoformat(from_date).date()
            to_date = datetime.fromisoformat(to_date).date()
        
        queryset = self.get_queryset().filter(
            date__date__gte=from_date,
            date__date__lte=to_date
        )
        
        # Calculate stats
        stats = {
            'period_start': from_date,
            'period_end': to_date,
            'total_transactions': queryset.count(),
            'total_income': queryset.filter(type='CREDIT').aggregate(
                total=Sum('amount'))['total'] or Decimal('0'),
            'total_expenses': queryset.filter(type='DEBIT').aggregate(
                total=Sum('amount'))['total'] or Decimal('0'),
        }
        
        stats['net_income'] = stats['total_income'] - stats['total_expenses']
        
        # Top categories
        stats['top_expense_categories'] = list(
            queryset.filter(type='DEBIT', category__isnull=False)
            .values('category__name', 'category__icon', 'category__color')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')[:5]
        )
        
        stats['top_income_categories'] = list(
            queryset.filter(type='CREDIT', category__isnull=False)
            .values('category__name', 'category__icon', 'category__color')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')[:5]
        )
        
        return Response(stats)


class TransactionCategoryViewSet(ModelViewSet):
    """
    ViewSet for transaction categories
    """
    serializer_class = TransactionCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'is_active', 'is_system', 'parent']
    search_fields = ['name']
    ordering_fields = ['name', 'order', 'created_at']
    ordering = ['type', 'order', 'name']
    
    def get_queryset(self):
        return TransactionCategory.objects.filter(
            Q(company=self.request.user.company) | Q(is_system=True),
            is_active=True
        )
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCategorySerializer
        return TransactionCategorySerializer
    
    def perform_create(self, serializer):
        # Generate slug
        name = serializer.validated_data['name']
        slug = f"{self.request.user.company.id}-{name.lower().replace(' ', '-')}"
        
        serializer.save(
            company=self.request.user.company,
            slug=slug
        )


class DashboardView(APIView):
    """
    Dashboard data API
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get dashboard data"""
        cache_key = f"dashboard_data_{request.user.company.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        company = request.user.company
        
        # Account stats
        accounts = BankAccount.objects.filter(company=company, is_active=True)
        total_balance = accounts.aggregate(total=Sum('balance'))['total'] or Decimal('0')
        
        account_stats = {
            'total_accounts': accounts.count(),
            'connected_accounts': accounts.filter(item__status='UPDATED').count(),
            'error_accounts': accounts.filter(item__has_error=True).count(),
            'total_balance': total_balance,
            'last_sync': accounts.aggregate(
                last_sync=models.Max('item__last_successful_update')
            )['last_sync']
        }
        
        # Transaction stats (current month)
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        transactions = Transaction.objects.filter(
            company=company,
            is_deleted=False,
            date__date__gte=month_start,
            date__date__lte=today
        )
        
        transaction_stats = {
            'period_start': month_start,
            'period_end': today,
            'total_transactions': transactions.count(),
            'total_income': transactions.filter(type='CREDIT').aggregate(
                total=Sum('amount'))['total'] or Decimal('0'),
            'total_expenses': transactions.filter(type='DEBIT').aggregate(
                total=Sum('amount'))['total'] or Decimal('0'),
        }
        transaction_stats['net_income'] = (
            transaction_stats['total_income'] - transaction_stats['total_expenses']
        )
        
        # Recent transactions
        recent_transactions = transactions.order_by('-date', '-created_at')[:10]
        
        # Top categories this month
        top_categories = (
            transactions.filter(category__isnull=False)
            .values('category__id', 'category__name', 'category__icon', 'category__color')
            .annotate(total_amount=Sum('amount'), transaction_count=Count('id'))
            .order_by('-total_amount')[:5]
        )
        
        dashboard_data = {
            'account_stats': account_stats,
            'transaction_stats': transaction_stats,
            'recent_transactions': TransactionSerializer(recent_transactions, many=True).data,
            'top_categories': list(top_categories),
            'monthly_trends': []  # TODO: Implement monthly trends
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, dashboard_data, 300)
        
        return Response(dashboard_data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def sync_categories(request):
    """Sync Pluggy categories"""
    try:
        sync_service = PluggySyncService()
        result = sync_service.sync_categories()
        
        return Response({
            'message': 'Categories synced successfully',
            'result': result
        })
    except Exception as e:
        logger.error(f"Failed to sync categories: {e}")
        return Response(
            {'error': 'Failed to sync categories'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_default_categories(request):
    """Create default categories for the company"""
    try:
        sync_service = PluggySyncService()
        categories = sync_service.create_default_categories(request.user.company)
        
        return Response({
            'message': f'Created {len(categories)} default categories',
            'categories': TransactionCategorySerializer(categories, many=True).data
        })
    except Exception as e:
        logger.error(f"Failed to create default categories: {e}")
        return Response(
            {'error': 'Failed to create default categories'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def banking_health(request):
    """Check banking system health"""
    try:
        sync_service = PluggySyncService()
        
        # Test Pluggy connection
        pluggy_healthy = sync_service.client.test_connection()
        
        # Get company stats
        company = request.user.company
        items = PluggyItem.objects.filter(company=company)
        accounts = BankAccount.objects.filter(company=company, is_active=True)
        transactions = Transaction.objects.filter(company=company, is_deleted=False)
        
        health_data = {
            'pluggy_api': 'healthy' if pluggy_healthy else 'unhealthy',
            'total_items': items.count(),
            'connected_items': items.filter(status='UPDATED').count(),
            'error_items': items.filter(has_error=True).count(),
            'total_accounts': accounts.count(),
            'total_transactions': transactions.count(),
            'last_sync': items.aggregate(
                last_sync=models.Max('last_successful_update')
            )['last_sync'],
            'system_status': 'healthy' if pluggy_healthy and items.exists() else 'degraded'
        }
        
        return Response(health_data)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response(
            {
                'pluggy_api': 'unhealthy',
                'system_status': 'unhealthy',
                'error': str(e)
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_item(request, item_id):
    """Delete a Pluggy item"""
    try:
        item = PluggyItem.objects.get(
            id=item_id,
            company=request.user.company
        )
        
        sync_service = PluggySyncService()
        success = sync_service.delete_item(item)
        
        if success:
            return Response({'message': 'Bank connection deleted successfully'})
        else:
            return Response(
                {'error': 'Failed to delete connection'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except PluggyItem.DoesNotExist:
        return Response(
            {'error': 'Bank connection not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Failed to delete item {item_id}: {e}")
        return Response(
            {'error': 'Failed to delete bank connection'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )