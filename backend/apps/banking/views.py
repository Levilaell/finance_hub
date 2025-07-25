"""
Banking app views - Pluggy Integration
Following Pluggy's official API patterns
"""
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from django.db import transaction
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from .models import (
    PluggyConnector, PluggyItem, BankAccount,
    Transaction, TransactionCategory, ItemWebhook
)
from .serializers import (
    PluggyConnectorSerializer, PluggyItemSerializer, BankAccountSerializer,
    TransactionSerializer, TransactionCategorySerializer,
    PluggyConnectTokenSerializer, PluggyCallbackSerializer,
    AccountSyncSerializer, BulkCategorizeSerializer,
    TransactionFilterSerializer, DashboardDataSerializer,
    WebhookEventSerializer, DashboardTransactionSerializer
)
from .integrations.pluggy.client import PluggyClient, PluggyError
from .tasks import sync_bank_account, process_webhook_event

logger = logging.getLogger(__name__)


class StandardPagination(PageNumberPagination):
    """Standard pagination for the API"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


class PluggyConnectorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Pluggy connectors (banks)
    """
    queryset = PluggyConnector.objects.filter(is_sandbox=False)
    serializer_class = PluggyConnectorSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        """Filter connectors based on query params"""
        queryset = super().get_queryset()
        
        # Filter by type
        connector_type = self.request.query_params.get('type')
        if connector_type:
            queryset = queryset.filter(type=connector_type)
        
        # Filter by Open Finance
        is_open_finance = self.request.query_params.get('is_open_finance')
        if is_open_finance is not None:
            queryset = queryset.filter(
                is_open_finance=is_open_finance.lower() == 'true'
            )
        
        # Filter by country
        country = self.request.query_params.get('country', 'BR')
        queryset = queryset.filter(country=country)
        
        return queryset.order_by('name')
    
    @action(detail=False, methods=['post'])
    def sync(self, request):
        """Sync connectors from Pluggy API"""
        try:
            with PluggyClient() as client:
                # Get connectors from Pluggy
                connectors = client.get_connectors()
                
                # Update or create connectors
                created = 0
                updated = 0
                
                for connector_data in connectors:
                    obj, was_created = PluggyConnector.objects.update_or_create(
                        pluggy_id=connector_data['id'],
                        defaults={
                            'name': connector_data['name'],
                            'institution_url': connector_data.get('institutionUrl', ''),
                            'image_url': connector_data.get('imageUrl', ''),
                            'primary_color': connector_data.get('primaryColor', '#000000'),
                            'type': connector_data['type'],
                            'country': connector_data.get('country', 'BR'),
                            'has_mfa': connector_data.get('hasMFA', False),
                            'has_oauth': connector_data.get('oauth', False),
                            'is_open_finance': connector_data.get('isOpenFinance', False),
                            'is_sandbox': connector_data.get('sandbox', False),
                            'products': connector_data.get('products', []),
                            'credentials': connector_data.get('credentials', [])
                        }
                    )
                    
                    if was_created:
                        created += 1
                    else:
                        updated += 1
                
                return Response({
                    'success': True,
                    'message': f'Synced {len(connectors)} connectors',
                    'created': created,
                    'updated': updated
                })
                
        except PluggyError as e:
            logger.error(f"Failed to sync connectors: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PluggyItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Pluggy items (connections)
    """
    serializer_class = PluggyItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Get items for user's company"""
        return PluggyItem.objects.filter(
            company=self.request.user.company
        ).select_related('connector').prefetch_related('accounts')
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync specific item"""
        item = self.get_object()
        
        try:
            # Queue sync task
            task = sync_bank_account.delay(item.id)
            
            return Response({
                'success': True,
                'message': 'Sync started',
                'task_id': task.id
            })
            
        except Exception as e:
            logger.error(f"Failed to start sync: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'])
    def disconnect(self, request, pk=None):
        """Disconnect item (delete from Pluggy and locally)"""
        item = self.get_object()
        
        try:
            with PluggyClient() as client:
                # Delete from Pluggy
                client.delete_item(item.pluggy_id)
                
                # Delete locally
                item.delete()
                
                return Response(status=status.HTTP_204_NO_CONTENT)
                
        except PluggyError as e:
            logger.error(f"Failed to disconnect item: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class BankAccountViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for bank accounts
    """
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        """Get accounts for user's company"""
        return BankAccount.objects.filter(
            company=self.request.user.company,
            is_active=True
        ).select_related('item__connector').order_by('-created')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get accounts summary"""
        accounts = self.get_queryset()
        
        # Calculate totals by type
        summary = accounts.values('type').annotate(
            count=Count('id'),
            total_balance=Sum('balance')
        )
        
        # Overall totals
        total_balance = accounts.aggregate(
            total=Sum('balance')
        )['total'] or Decimal('0.00')
        
        return Response({
            'total_balance': total_balance,
            'total_accounts': accounts.count(),
            'by_type': list(summary),
            'last_update': accounts.filter(
                updated_at__isnull=False
            ).order_by('-updated_at').values_list(
                'updated_at', flat=True
            ).first()
        })


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for transactions
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Get transactions with filters"""
        # Base queryset
        queryset = Transaction.objects.filter(
            account__company=self.request.user.company
        ).select_related(
            'account__item__connector',
            'category'
        )
        
        # Apply filters
        filter_serializer = TransactionFilterSerializer(
            data=self.request.query_params
        )
        
        if filter_serializer.is_valid():
            filters = filter_serializer.validated_data
            
            # Account filter
            if filters.get('account_id'):
                queryset = queryset.filter(account_id=filters['account_id'])
            
            # Category filter
            if filters.get('category_id'):
                queryset = queryset.filter(category_id=filters['category_id'])
            
            # Date range
            if filters.get('start_date'):
                queryset = queryset.filter(date__gte=filters['start_date'])
            if filters.get('end_date'):
                queryset = queryset.filter(date__lte=filters['end_date'])
            
            # Amount range
            if filters.get('min_amount'):
                queryset = queryset.filter(
                    Q(amount__gte=filters['min_amount']) |
                    Q(amount__lte=-filters['min_amount'])
                )
            if filters.get('max_amount'):
                queryset = queryset.filter(
                    amount__lte=filters['max_amount'],
                    amount__gte=-filters['max_amount']
                )
            
            # Transaction type
            if filters.get('type'):
                queryset = queryset.filter(type=filters['type'])
            
            # Search
            if filters.get('search'):
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(description__icontains=search_term) |
                    Q(merchant__name__icontains=search_term) |
                    Q(notes__icontains=search_term)
                )
        
        return queryset.order_by('-date', '-created')
    
    def create(self, request, *args, **kwargs):
        """Prevent manual transaction creation"""
        return Response(
            {"error": "Manual transaction creation is not allowed. Transactions are synced from Pluggy."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def destroy(self, request, *args, **kwargs):
        """Prevent transaction deletion"""
        return Response(
            {"error": "Transaction deletion is not allowed. Transactions are managed by Pluggy."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def update(self, request, *args, **kwargs):
        """Allow partial updates (category, notes, tags)"""
        partial = kwargs.pop('partial', True)
        return super().update(request, *args, partial=partial, **kwargs)
    
    @action(detail=False, methods=['post'])
    def bulk_categorize(self, request):
        """Bulk categorize transactions"""
        serializer = BulkCategorizeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Update transactions
        updated = Transaction.objects.filter(
            id__in=data['transaction_ids'],
            account__company=request.user.company
        ).update(
            category_id=data['category_id'],
            modified=timezone.now()
        )
        
        return Response({
            'success': True,
            'updated': updated
        })
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export transactions as CSV"""
        import csv
        from django.http import HttpResponse
        
        # Get filtered queryset
        queryset = self.get_queryset()
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Description', 'Amount', 'Type', 'Category',
            'Account', 'Bank', 'Notes'
        ])
        
        for transaction in queryset:
            writer.writerow([
                transaction.date.strftime('%Y-%m-%d'),
                transaction.description,
                float(transaction.amount),
                transaction.type,
                transaction.category.name if transaction.category else '',
                transaction.account.display_name,
                transaction.account.item.connector.name,
                transaction.notes
            ])
        
        return response


class TransactionCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for transaction categories
    """
    serializer_class = TransactionCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        """Get categories for user's company and system categories"""
        return TransactionCategory.objects.filter(
            Q(company=self.request.user.company) | Q(is_system=True)
        ).order_by('type', 'order', 'name')
    
    def perform_create(self, serializer):
        """Set company when creating category"""
        serializer.save(company=self.request.user.company)


class PluggyConnectView(APIView):
    """
    Handle Pluggy Connect integration
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Create connect token"""
        serializer = PluggyConnectTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with PluggyClient() as client:
                # Create connect token
                token_data = client.create_connect_token(
                    item_id=serializer.validated_data.get('item_id'),
                    client_user_id=str(request.user.id),
                    webhook_url=serializer.validated_data.get('webhook_url')
                )
                
                # Build connect URL if not provided
                connect_url = token_data.get('connectUrl')
                if not connect_url:
                    connect_base = os.getenv('PLUGGY_CONNECT_URL', 'https://connect.pluggy.ai')
                    connect_url = f"{connect_base}?token={token_data['accessToken']}"
                
                return Response({
                    'success': True,
                    'data': {
                        'connect_token': token_data['accessToken'],
                        'connect_url': connect_url
                    }
                })
                
        except PluggyError as e:
            logger.error(f"Failed to create connect token: {e}")
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class PluggyCallbackView(APIView):
    """
    Handle Pluggy Connect callback
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Process Pluggy Connect callback"""
        serializer = PluggyCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        item_id = serializer.validated_data['item_id']
        
        try:
            with PluggyClient() as client:
                # Get item details
                item_data = client.get_item(item_id)
                
                # Get connector
                connector = PluggyConnector.objects.get(
                    pluggy_id=item_data['connector']['id']
                )
                
                # Create or update item
                with transaction.atomic():
                    item, created = PluggyItem.objects.update_or_create(
                        pluggy_id=item_id,
                        defaults={
                            'company': request.user.company,
                            'connector': connector,
                            'client_user_id': str(request.user.id),
                            'status': item_data['status'],
                            'execution_status': item_data.get('executionStatus', ''),
                            'created_at': item_data['createdAt'],
                            'updated_at': item_data['updatedAt'],
                            'status_detail': item_data.get('statusDetail', {}),
                            'error_code': item_data.get('error', {}).get('code', '') if item_data.get('error') else '',
                            'error_message': item_data.get('error', {}).get('message', '') if item_data.get('error') else ''
                        }
                    )
                    
                    # Get accounts
                    accounts_data = client.get_accounts(item_id)
                    created_accounts = []
                    
                    for account_data in accounts_data:
                        account, _ = BankAccount.objects.update_or_create(
                            pluggy_id=account_data['id'],
                            defaults={
                                'item': item,
                                'company': request.user.company,
                                'type': account_data['type'],
                                'subtype': account_data.get('subtype', ''),
                                'number': account_data.get('number', ''),
                                'name': account_data.get('name', ''),
                                'marketing_name': account_data.get('marketingName', ''),
                                'owner': account_data.get('owner', ''),
                                'tax_number': account_data.get('taxNumber', ''),
                                'balance': Decimal(str(account_data.get('balance', 0))),
                                'currency_code': account_data.get('currencyCode', 'BRL'),
                                'bank_data': account_data.get('bankData', {}),
                                'credit_data': account_data.get('creditData', {}),
                                'created_at': account_data.get('createdAt'),
                                'updated_at': account_data.get('updatedAt')
                            }
                        )
                        created_accounts.append(account)
                    
                    # Queue initial sync if item is ready
                    if item.status == 'UPDATED':
                        sync_bank_account.delay(item.id)
                
                return Response({
                    'success': True,
                    'data': {
                        'item': PluggyItemSerializer(item).data,
                        'accounts': BankAccountSerializer(created_accounts, many=True).data,
                        'message': f'Successfully connected {len(created_accounts)} account(s)'
                    }
                })
                
        except Exception as e:
            logger.error(f"Failed to process callback: {e}", exc_info=True)
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AccountSyncView(APIView):
    """
    Sync account data
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, account_id):
        """Sync specific account"""
        try:
            account = BankAccount.objects.get(
                id=account_id,
                company=request.user.company
            )
            
            # Check item status
            if account.item.status in ['LOGIN_ERROR', 'INVALID_CREDENTIALS']:
                return Response({
                    'success': False,
                    'error_code': 'LOGIN_ERROR',
                    'message': 'Invalid credentials. Please reconnect the account.',
                    'reconnection_required': True
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if account.item.status == 'WAITING_USER_INPUT':
                return Response({
                    'success': False,
                    'error_code': 'MFA_REQUIRED',
                    'message': 'Additional authentication required.',
                    'reconnection_required': True
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Queue sync
            sync_bank_account.delay(account.item.id, account_id=str(account.id))
            
            return Response({
                'success': True,
                'message': 'Sync started',
                'data': {
                    'account': BankAccountSerializer(account).data
                }
            })
            
        except BankAccount.DoesNotExist:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class DashboardView(APIView):
    """
    Dashboard data endpoint
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get dashboard data"""
        company = request.user.company
        
        # Get date ranges
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month_end = current_month_start - timedelta(days=1)
        previous_month_start = previous_month_end.replace(day=1)
        
        # Get accounts
        accounts = BankAccount.objects.filter(
            company=company,
            is_active=True
        ).select_related('item__connector')
        
        # Calculate balances
        total_balance = accounts.aggregate(
            total=Sum('balance')
        )['total'] or Decimal('0.00')
        
        # Get transactions
        all_transactions = Transaction.objects.filter(
            account__company=company
        )
        
        # Current month stats
        current_month_transactions = all_transactions.filter(
            date__gte=current_month_start
        )
        
        current_income = current_month_transactions.filter(
            type='CREDIT'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        current_expenses = current_month_transactions.filter(
            type='DEBIT'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Previous month stats
        previous_month_transactions = all_transactions.filter(
            date__gte=previous_month_start,
            date__lt=current_month_start
        )
        
        previous_income = previous_month_transactions.filter(
            type='CREDIT'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        previous_expenses = previous_month_transactions.filter(
            type='DEBIT'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Recent transactions
        recent_transactions = all_transactions.select_related(
            'account__item__connector',
            'category'
        ).order_by('-date')[:10]
        
        # Category breakdown (current month)
        category_breakdown = current_month_transactions.filter(
            category__isnull=False
        ).values(
            'category__name',
            'category__icon',
            'category__color'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:10]
        
        # Accounts summary
        accounts_summary = []
        for account in accounts:
            transactions_count = account.transactions.filter(
                date__gte=current_month_start
            ).count()
            
            accounts_summary.append({
                'id': account.id,
                'name': account.display_name,
                'type': account.type,
                'balance': account.balance,
                'connector': {
                    'name': account.item.connector.name,
                    'image_url': account.item.connector.image_url
                },
                'transactions_count': transactions_count,
                'last_update': account.updated_at
            })
        
        # Build response
        data = {
            'current_balance': total_balance,
            'monthly_income': current_income,
            'monthly_expenses': abs(current_expenses),
            'monthly_net': current_income - abs(current_expenses),
            'recent_transactions': DashboardTransactionSerializer(
                recent_transactions, 
                many=True
            ).data,
            'top_categories': list(category_breakdown),
            'accounts_count': accounts.count(),
            'transactions_count': current_month_transactions.count(),
            'total_balance': total_balance,
            'total_accounts': accounts.count(),
            'active_accounts': accounts.filter(item__status='UPDATED').count(),
            'current_month': {
                'income': current_income,
                'expenses': abs(current_expenses),
                'net': current_income - abs(current_expenses)
            },
            'previous_month': {
                'income': previous_income,
                'expenses': abs(previous_expenses),
                'net': previous_income - abs(previous_expenses)
            },
            'category_breakdown': list(category_breakdown),
            'accounts_summary': accounts_summary
        }
        
        return Response(data)


@method_decorator(csrf_exempt, name='dispatch')
class PluggyWebhookView(APIView):
    """
    Handle Pluggy webhooks
    """
    permission_classes = []  # Webhooks come from Pluggy, not authenticated users
    authentication_classes = []
    
    def post(self, request):
        """Process webhook event"""
        # Verify signature
        signature = request.headers.get('X-Pluggy-Signature', '')
        
        try:
            # Validate webhook
            with PluggyClient() as client:
                if not client.validate_webhook(signature, request.body.decode()):
                    logger.warning("Invalid webhook signature")
                    return Response(
                        {'error': 'Invalid signature'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            
            # Parse event
            serializer = WebhookEventSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            event_type = serializer.validated_data['event']
            event_data = serializer.validated_data['data']
            
            # Queue processing
            process_webhook_event.delay(event_type, event_data)
            
            return Response({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )