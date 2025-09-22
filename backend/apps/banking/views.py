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
from django.utils.decorators import method_decorator  # Still needed for csrf_exempt

from rest_framework import status, viewsets, permissions # type: ignore
from rest_framework.decorators import action # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework.views import APIView # type: ignore
from rest_framework.pagination import PageNumberPagination # type: ignore
from rest_framework.exceptions import PermissionDenied # type: ignore

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
    DashboardTransactionSerializer
)
from .integrations.pluggy.client import PluggyClient, PluggyError
from .tasks import sync_bank_account, process_webhook_event

logger = logging.getLogger(__name__)


def _handle_pluggy_error(error: Exception, operation: str, item_id: str = None) -> Response:
    """
    Standardize Pluggy error handling and responses
    
    Args:
        error: The exception that occurred
        operation: Description of the operation that failed
        item_id: Optional item ID for context
        
    Returns:
        Standardized error response
    """
    error_context = f"item {item_id}" if item_id else "request"
    
    if isinstance(error, PluggyError):
        logger.error(f"Pluggy API error during {operation} for {error_context}: {error}")
        return Response({
            'success': False,
            'error': 'banking_api_error',
            'message': f'Banking service error during {operation}',
            'details': str(error)
        }, status=status.HTTP_502_BAD_GATEWAY)
    
    elif isinstance(error, PermissionDenied):
        logger.warning(f"Permission denied during {operation} for {error_context}: {error}")
        return Response({
            'success': False,
            'error': 'permission_denied',
            'message': str(error),
            'details': f'Access denied for {operation}'
        }, status=status.HTTP_403_FORBIDDEN)
    
    else:
        logger.error(f"Unexpected error during {operation} for {error_context}: {error}")
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': f'Internal error during {operation}',
            'details': 'Please try again later or contact support if the issue persists'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        
        # Prioritize Open Finance connectors (safer, OAuth-based)
        return queryset.order_by('-is_open_finance', 'name')
    
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
                
        except Exception as e:
            return _handle_pluggy_error(e, "connectors synchronization")


class PluggyItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Pluggy items (connections)
    """
    serializer_class = PluggyItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Get items for user's company"""
        company, error_response = self.get_user_company(self.request)
        if error_response:
            return PluggyItem.objects.none()
        
        queryset = PluggyItem.objects.filter(
            company=company
        ).select_related('connector').prefetch_related('accounts')
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync specific item - triggers manual update via Pluggy API"""
        item = self.get_object()
        
        try:
            # First, trigger an update via Pluggy API for manual sync
            with PluggyClient() as client:
                try:
                    # According to docs, send empty JSON {} to update without changing credentials
                    logger.info(f"Triggering manual update for item {item.pluggy_item_id}")
                    update_response = client.update_item(item.pluggy_item_id, {})
                    logger.info(f"Update response: {update_response}")
                    
                    # Update item status from response
                    item.status = update_response.get('status', item.status)
                    item.execution_status = update_response.get('executionStatus', '')
                    item.pluggy_updated_at = update_response.get('updatedAt', item.pluggy_updated_at)
                    item.save()
                    
                except PluggyError as e:
                    logger.warning(f"Failed to trigger Pluggy update: {e}")
                    # Continue with sync even if update trigger fails
            
            # Queue sync task
            try:
                task = sync_bank_account.delay(str(item.id), force_update=True)
                task_id = task.id
            except Exception as celery_error:
                logger.warning(f"Could not queue sync task: {celery_error}")
                task_id = None
            
            return Response({
                'success': True,
                'message': 'Manual sync triggered successfully',
                'task_id': task_id,
                'item_status': item.status
            })
            
        except Exception as e:
            logger.error(f"Failed to start sync: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['delete'])
    def disconnect(self, request, pk=None):
        """Disconnect item (delete from Pluggy and locally with all related data)"""
        item = self.get_object()
        company = item.company
        
        try:
            with PluggyClient() as client:
                # Check if it's an Open Finance item that needs consent revocation
                if item.connector.is_open_finance and item.consent_id:
                    logger.info(f"Revoking Open Finance consent for item {item.pluggy_item_id}")
                    try:
                        client.revoke_consent(item.pluggy_item_id)
                    except PluggyError as e:
                        logger.warning(f"Failed to revoke consent: {e}")
                
                # Delete from Pluggy
                logger.info(f"Deleting item {item.pluggy_item_id} from Pluggy")
                try:
                    client.delete_item(item.pluggy_item_id)
                except PluggyError as e:
                    logger.warning(f"Failed to delete from Pluggy (may already be deleted): {e}")
                
                # Use atomic transaction for database operations
                from django.db import transaction as db_transaction
                
                with db_transaction.atomic():
                    # Count transactions to be deleted for usage reset
                    transactions_count = Transaction.objects.filter(
                        account__item=item,
                        company=company
                    ).count()
                    
                    logger.info(f"Will delete {transactions_count} transactions for item {item.pluggy_item_id}")
                    
                    # Delete all transactions (this will cascade delete related data)
                    Transaction.objects.filter(
                        account__item=item,
                        company=company
                    ).delete()
                    
                    # Delete all accounts
                    BankAccount.objects.filter(
                        item=item,
                        company=company
                    ).delete()
                    
                    # Delete webhooks
                    ItemWebhook.objects.filter(item=item).delete()
                    
                    # Delete the item itself
                    item.delete()

                    # Transaction counter reset has been removed in simplified model

                logger.info(f"Successfully disconnected and deleted item {item.pluggy_item_id}")
                
                return Response({
                    'success': True,
                    'message': 'Account disconnected and all data deleted successfully.',
                    'deleted_transactions': transactions_count
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return _handle_pluggy_error(e, "item disconnection and deletion", item.pluggy_item_id)



class BankAccountViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for bank accounts
    """
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        """Get accounts for user's company"""
        company, error_response = self.get_user_company(self.request)
        if error_response:
            return BankAccount.objects.none()
        
        return BankAccount.objects.filter(
            company=company,
            is_active=True
        ).select_related('item__connector').order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync specific account - triggers manual update"""
        account = self.get_object()
        
        try:
            # First, get the latest item status from Pluggy API
            # This is crucial for local development where webhooks don't arrive
            with PluggyClient() as client:
                try:
                    logger.info(f"Fetching latest status for item {account.item.pluggy_item_id}")
                    item_data = client.get_item(account.item.pluggy_item_id)
                    
                    # Update local item with latest status from Pluggy
                    old_status = account.item.status
                    old_execution = account.item.execution_status
                    
                    account.item.status = item_data.get('status', account.item.status)
                    account.item.execution_status = item_data.get('executionStatus', '')
                    # Handle error field safely - it might be None
                    error_data = item_data.get('error') or {}
                    account.item.error_code = error_data.get('code', '')
                    account.item.error_message = error_data.get('message', '')
                    account.item.pluggy_updated_at = item_data.get('updatedAt', account.item.pluggy_updated_at)
                    account.item.save()
                    
                    logger.info(f"Item status updated: {old_status}/{old_execution} -> {account.item.status}/{account.item.execution_status}")
                    
                    # Check for USER_INPUT_TIMEOUT in executionStatus or error code
                    if account.item.execution_status == 'USER_INPUT_TIMEOUT' or account.item.error_code == 'USER_INPUT_TIMEOUT':
                        logger.warning(f"Item {account.item.pluggy_item_id} has USER_INPUT_TIMEOUT - reconnection required")
                        return Response({
                            'success': False,
                            'error_code': 'AUTHENTICATION_TIMEOUT',
                            'message': 'Timeout de autenticação. O banco solicitou verificação adicional mas o tempo expirou.',
                            'reconnection_required': True,
                            'details': 'Por favor, reconecte sua conta e insira o código de verificação em até 60 segundos.',
                            'item_status': account.item.status,
                            'execution_status': account.item.execution_status
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                except PluggyError as e:
                    logger.warning(f"Could not fetch latest item status: {e}")
                    # Continue with cached status if API call fails
            
            # Check item status after update
            if account.item.status in ['LOGIN_ERROR', 'INVALID_CREDENTIALS', 'ERROR']:
                error_msg = account.item.error_message or 'Invalid credentials or connection error.'
                return Response({
                    'success': False,
                    'error_code': 'LOGIN_ERROR',
                    'message': f'{error_msg} Please reconnect the account.',
                    'reconnection_required': True,
                    'item_status': account.item.status,
                    'error_details': account.item.error_code
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if account.item.status == 'WAITING_USER_INPUT':
                return Response({
                    'success': False,
                    'error_code': 'MFA_REQUIRED',
                    'message': 'Autenticação adicional necessária. Reconecte para inserir o código de verificação.',
                    'reconnection_required': True,
                    'item_status': account.item.status
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if account.item.status == 'OUTDATED':
                # OUTDATED usually means there was an error, check executionStatus
                return Response({
                    'success': False,
                    'error_code': 'OUTDATED_CONNECTION',
                    'message': 'Conexão desatualizada. Por favor, reconecte sua conta bancária.',
                    'reconnection_required': True,
                    'item_status': account.item.status,
                    'execution_status': account.item.execution_status
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Now trigger an update via Pluggy API for manual sync
            with PluggyClient() as client:
                try:
                    logger.info(f"Triggering manual update for item {account.item.pluggy_item_id}")
                    update_response = client.update_item(account.item.pluggy_item_id, {})
                    
                    # Update item status again after triggering update
                    account.item.status = update_response.get('status', account.item.status)
                    account.item.execution_status = update_response.get('executionStatus', '')
                    account.item.pluggy_updated_at = update_response.get('updatedAt', account.item.pluggy_updated_at)
                    account.item.save()
                    
                    logger.info(f"Update triggered, new status: {account.item.status}/{account.item.execution_status}")
                    
                except PluggyError as e:
                    logger.warning(f"Failed to trigger Pluggy update: {e}")
                    # Continue with sync even if update trigger fails
            
            # Queue sync
            logger.info(f"Queuing sync for account {account.id} (item {account.item.id})")
            sync_result = None
            task_id = None
            
            try:
                task = sync_bank_account.delay(str(account.item.id), account_id=str(account.id), force_update=True)
                task_id = task.id
                logger.info(f"Successfully queued async sync task {task_id}")
            except Exception as celery_error:
                logger.warning(f"Could not queue sync task: {celery_error}")
                logger.info("Falling back to synchronous sync...")
                
                # Fallback to synchronous sync when Celery is unavailable
                try:
                    from apps.banking.tasks import _sync_account
                    with PluggyClient() as client:
                        sync_result = _sync_account(client, account)
                        logger.info(f"Synchronous sync completed: {sync_result}")
                except Exception as sync_error:
                    logger.error(f"Synchronous sync also failed: {sync_error}")
                    return Response({
                        'success': False,
                        'error': 'Sync service unavailable. Please ensure Redis is running or try again later.',
                        'details': str(sync_error)
                    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Prepare response
            response_data = {
                'success': True,
                'message': 'Manual sync triggered successfully',
                'data': {
                    'account': BankAccountSerializer(account).data,
                    'task_id': task_id,
                    'item_status': account.item.status
                }
            }
            
            # Add sync result if synchronous sync was performed
            if sync_result:
                response_data['sync_result'] = sync_result
                response_data['message'] = 'Sync completed successfully (synchronous mode)'
                if sync_result and isinstance(sync_result, dict) and sync_result.get('transactions_synced'):
                    response_data['message'] += f' - {sync_result["transactions_synced"]} transactions synced'
            
            return Response(response_data)
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to sync account: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
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
                pluggy_updated_at__isnull=False
            ).order_by('-pluggy_updated_at').values_list(
                'pluggy_updated_at', flat=True
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
        # Use active manager to exclude transactions from deleted or inactive accounts
        company, error_response = self.get_user_company(self.request)
        if error_response:
            return Transaction.objects.none()
        
        queryset = Transaction.active.for_company(
            company
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
        
        return queryset.order_by('-date', '-created_at')
    
    def list(self, request, *args, **kwargs):
        """Override list to include totals in response"""
        # Get the paginated response
        response = super().list(request, *args, **kwargs)
        
        # Get the filtered queryset (same filters applied)
        queryset = self.filter_queryset(self.get_queryset())
        
        # Calculate totals from the FULL filtered queryset (not just current page)
        from django.db.models import Sum
        
        # Income total (CREDIT transactions)
        income_total = queryset.filter(type='CREDIT').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Expenses total (DEBIT transactions) 
        expenses_total = queryset.filter(type='DEBIT').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Add totals to response
        response.data['totals'] = {
            'income': float(income_total),
            'expenses': float(abs(expenses_total)),
            'balance': float(income_total - abs(expenses_total)),
            'filtered_count': queryset.count()
        }
        
        return response
    
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
        """Allow partial updates (category, notes, tags) and sync with Pluggy"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Check if category is being updated
        if 'category' in serializer.validated_data:
            new_category = serializer.validated_data['category']
            if new_category and instance.pluggy_transaction_id:
                try:
                    # Find the Pluggy category ID for this category
                    pluggy_category = None
                    if hasattr(new_category, 'pluggy_mappings'):
                        # Get the first Pluggy mapping if available
                        pluggy_mapping = new_category.pluggy_mappings.first()
                        if pluggy_mapping:
                            pluggy_category = pluggy_mapping.id
                    
                    # If we have a Pluggy category ID, sync with Pluggy
                    if pluggy_category:
                        with PluggyClient() as client:
                            client.update_transaction_category(
                                instance.pluggy_transaction_id,
                                pluggy_category
                            )
                            logger.info(f"Synced category update to Pluggy for transaction {instance.pluggy_transaction_id}")
                    else:
                        logger.warning(f"No Pluggy category mapping found for category {new_category.name}")
                        
                except PluggyError as e:
                    logger.error(f"Failed to sync category with Pluggy: {e}")
                    # Continue with local update even if Pluggy sync fails
                except Exception as e:
                    logger.error(f"Unexpected error syncing with Pluggy: {e}")
        
        self.perform_update(serializer)
        
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
            
        return Response(serializer.data)
    
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
        company = self.get_user_company()
        updated = Transaction.objects.filter(
            id__in=data['transaction_ids'],
            account__company=company
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
        company, error_response = self.get_user_company(self.request)
        if error_response:
            return TransactionCategory.objects.none()
        
        return TransactionCategory.objects.filter(
            Q(company=company) | Q(is_system=True)
        ).order_by('type', 'order', 'name')
    
    def perform_create(self, serializer):
        """Set company when creating category"""
        company, error_response = self.get_user_company(self.request)
        if error_response:
            raise PermissionDenied("You must be associated with a company to access this resource.")
        serializer.save(company=company)


class PluggyConnectView(APIView):
    """
    Handle Pluggy Connect integration
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Create connect token"""
        # Check if user has a company
        if not hasattr(request.user, 'company') or not request.user.company:
            return Response({
                'error': 'Usuário não está associado a nenhuma empresa'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PluggyConnectTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with PluggyClient() as client:
                # Create connect token with all supported parameters
                token_data = client.create_connect_token(
                    client_user_id=str(request.user.id),
                    item_id=serializer.validated_data.get('item_id'),
                    webhook_url=serializer.validated_data.get('webhook_url'),
                    oauth_redirect_uri=serializer.validated_data.get('oauth_redirect_uri'),
                    avoid_duplicates=serializer.validated_data.get('avoid_duplicates'),
                    country_codes=serializer.validated_data.get('country_codes'),
                    connector_types=serializer.validated_data.get('connector_types'),
                    connector_ids=serializer.validated_data.get('connector_ids'),
                    products_types=serializer.validated_data.get('products_types')
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
                
        except Exception as e:
            return _handle_pluggy_error(e, "connect token creation")


class PluggyCallbackView(APIView):
    """
    Handle Pluggy Connect callback
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Process Pluggy Connect callback"""
        # Check if user has a company
        if not hasattr(request.user, 'company') or not request.user.company:
            return Response(
                {
                    'success': False,
                    'error': 'You must be associated with a company to access this resource.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        company = request.user.company

        serializer = PluggyCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        item_id = serializer.validated_data['item_id']
        
        try:
            with PluggyClient() as client:
                # Get item details
                item_data = client.get_item(item_id)
                
                # Get or create connector
                connector_id = item_data['connector']['id']
                try:
                    connector = PluggyConnector.objects.get(pluggy_id=connector_id)
                except PluggyConnector.DoesNotExist:
                    # Connector doesn't exist, create it
                    logger.warning(f"Connector {connector_id} not found, creating...")
                    
                    # Get connector details from Pluggy
                    try:
                        connector_data = client.get_connector(connector_id)
                        connector = PluggyConnector.objects.create(
                            pluggy_id=connector_id,
                            name=connector_data.get('name', f'Connector {connector_id}'),
                            institution_url=connector_data.get('institutionUrl', ''),
                            image_url=connector_data.get('imageUrl', ''),
                            country=connector_data.get('country', 'BR'),
                            type=connector_data.get('type', 'UNKNOWN'),
                            has_mfa=connector_data.get('hasMFA', False),
                            oauth_url=connector_data.get('oauthUrl', ''),
                            is_sandbox=connector_data.get('isSandbox', False),
                            is_open_finance=connector_data.get('isOpenFinance', False),
                            supports_payment_initiation=connector_data.get('supportsPaymentInitiation', False),
                            credentials_schema=connector_data.get('credentials', []),
                            connector_data=connector_data
                        )
                        logger.info(f"Created connector: {connector.name}")
                    except Exception as e:
                        logger.error(f"Failed to get connector {connector_id} from Pluggy: {e}")
                        # Create a minimal connector record
                        connector = PluggyConnector.objects.create(
                            pluggy_id=connector_id,
                            name=item_data['connector'].get('name', f'Bank {connector_id}'),
                            country='BR',
                            type='UNKNOWN'
                        )
                        logger.info(f"Created minimal connector record for ID {connector_id}")
                
                # Create or update item
                with transaction.atomic():
                    item, created = PluggyItem.objects.update_or_create(
                        pluggy_item_id=item_id,
                        defaults={
                            'company': request.user.company,
                            'connector': connector,
                            'client_user_id': str(request.user.id),
                            'status': item_data['status'],
                            'execution_status': item_data.get('executionStatus', ''),
                            'pluggy_created_at': item_data['createdAt'],
                            'pluggy_updated_at': item_data['updatedAt'],
                            'status_detail': item_data.get('statusDetail') or {},
                            'error_code': item_data.get('error', {}).get('code', '') if item_data.get('error') else '',
                            'error_message': item_data.get('error', {}).get('message', '') if item_data.get('error') else ''
                        }
                    )
                    
                    # Get accounts - handle PARTIAL_SUCCESS gracefully
                    created_accounts = []
                    accounts_fetch_error = None
                    
                    try:
                        accounts_data = client.get_accounts(item_id)
                        logger.info(f"Fetched {len(accounts_data)} accounts from Pluggy API for item {item_id}")
                        
                        for account_data in accounts_data:
                            account, _ = BankAccount.objects.update_or_create(
                                pluggy_account_id=account_data['id'],
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
                                    'pluggy_created_at': account_data.get('createdAt'),
                                    'pluggy_updated_at': account_data.get('updatedAt')
                                }
                            )
                            created_accounts.append(account)
                            
                    except Exception as accounts_error:
                        logger.warning(f"Failed to fetch accounts for item {item_id}: {accounts_error}")
                        accounts_fetch_error = str(accounts_error)
                        # Don't fail the entire callback - item is still connected
                    
                    # Handle success cases with no accounts (common for Open Finance)
                    connection_message = ""
                    # Check both status and execution_status for success scenarios
                    is_success = item.execution_status in ['SUCCESS', 'PARTIAL_SUCCESS']
                    is_partial_success = item.execution_status == 'PARTIAL_SUCCESS'
                    is_open_finance = item.connector.is_open_finance if item.connector else False
                    is_connection_healthy = item.status == 'UPDATED'
                    
                    if len(created_accounts) == 0:
                        # Handle successful connection but no accounts yet (common scenarios)
                        if is_partial_success and is_open_finance and is_connection_healthy:
                            connection_message = "Bank connected successfully! Account details are being processed and will appear shortly. This is normal for Open Finance connections."
                            logger.info(f"Open Finance connection successful with PARTIAL_SUCCESS execution status for item {item_id} - accounts will be available later")
                            
                            # Schedule a retry task to check for accounts later
                            try:
                                from .tasks import retry_account_fetch
                                retry_task = retry_account_fetch.apply_async(
                                    args=[str(item.id)], 
                                    countdown=300  # Retry in 5 minutes
                                )
                                logger.info(f"Scheduled account retry task: {retry_task.id}")
                            except Exception as retry_error:
                                logger.warning(f"Could not schedule retry task: {retry_error}")
                                
                        else:
                            connection_message = f"Bank connected but no accounts found. Status: {item.status}/{item.execution_status}"
                            if accounts_fetch_error:
                                connection_message += f" Error: {accounts_fetch_error}"
                    else:
                        connection_message = f"Successfully connected {len(created_accounts)} account(s)"
                    
                    # Queue initial sync if item is ready and has accounts
                    sync_queued = False
                    if item.status in ['UPDATED', 'OUTDATED'] and len(created_accounts) > 0:
                        try:
                            logger.info(f"Queuing initial sync for item {item.id} with {len(created_accounts)} accounts")
                            task = sync_bank_account.delay(str(item.id))
                            logger.info(f"Sync task queued with ID: {task.id}")
                            sync_queued = True
                        except Exception as celery_error:
                            logger.warning(f"Could not queue sync task (Celery may not be running): {celery_error}")
                    else:
                        if len(created_accounts) == 0:
                            logger.info(f"Skipping sync for item {item.id} - no accounts available yet")
                        else:
                            logger.warning(f"Item {item.id} not ready for sync, status: {item.status}")
                
                # Build response with detailed status
                response_data = {
                    'success': True,
                    'data': {
                        'item': PluggyItemSerializer(item).data,
                        'accounts': BankAccountSerializer(created_accounts, many=True).data,
                        'message': connection_message,
                        'status': {
                            'is_partial_success': is_partial_success,
                            'is_open_finance': is_open_finance,
                            'accounts_available': len(created_accounts) > 0,
                            'sync_queued': sync_queued,
                            'retry_scheduled': is_partial_success and is_open_finance,
                            'expected_delay': '5-15 minutes' if is_partial_success and is_open_finance else None
                        }
                    }
                }
                
                return Response(response_data)
                
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
    
    def post(self, request, account_id=None):
        """Sync specific account"""
        # Check if user has a company
        if not hasattr(request.user, 'company') or not request.user.company:
            return Response(
                {'error': 'You must be associated with a company to access this resource'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get account_id from URL parameter or request body
        if not account_id:
            account_id = request.data.get('account_id')
            
        if not account_id:
            return Response(
                {'error': 'Account ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
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
            try:
                sync_bank_account.delay(account.item.id, account_id=str(account.id))
            except Exception as celery_error:
                logger.warning(f"Could not queue sync task: {celery_error}")
                # Continue without sync
            
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
        if not hasattr(request.user, 'company') or not request.user.company:
            return Response(
                {"error": {"message": "You must be associated with a company to access this resource."}},
                status=status.HTTP_403_FORBIDDEN
            )
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
        
        # Get transactions - exclude from deleted or inactive accounts
        all_transactions = Transaction.active.for_company(company)
        
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
                'last_update': account.pluggy_updated_at.isoformat() if account.pluggy_updated_at else None
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



class CeleryHealthCheckView(APIView):
    """
    Check Celery worker and Redis health status
    """
    permission_classes = []  # Public endpoint
    
    def get(self, request):
        """Check Celery and Redis status"""
        from celery import current_app # type: ignore
        from django.core.cache import cache
        from django.conf import settings
        import redis # type: ignore
        
        health_status = {
            'celery': {
                'status': 'unknown',
                'active_queues': [],
                'registered_tasks': 0,
                'active_workers': 0
            },
            'redis': {
                'status': 'unknown',
                'info': {}
            },
            'overall': 'unhealthy'
        }
        
        # Check Redis
        try:
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            health_status['redis']['status'] = 'healthy'
            info = r.info()
            health_status['redis']['info'] = {
                'version': info.get('redis_version'),
                'connected_clients': info.get('connected_clients'),
                'used_memory_human': info.get('used_memory_human'),
                'uptime_in_days': info.get('uptime_in_days')
            }
        except Exception as e:
            health_status['redis']['status'] = 'unhealthy'
            health_status['redis']['error'] = str(e)
        
        # Check Celery
        try:
            # Get worker stats
            stats = current_app.control.inspect().stats()
            if stats:
                health_status['celery']['status'] = 'healthy'
                health_status['celery']['active_workers'] = len(stats)
                
                # Get active queues
                active_queues = current_app.control.inspect().active_queues()
                if active_queues:
                    all_queues = set()
                    for worker_queues in active_queues.values():
                        for queue in worker_queues:
                            all_queues.add(queue['name'])
                    health_status['celery']['active_queues'] = list(all_queues)
                
                # Get registered tasks count
                registered = current_app.control.inspect().registered()
                if registered:
                    total_tasks = sum(len(tasks) for tasks in registered.values())
                    health_status['celery']['registered_tasks'] = total_tasks
            else:
                health_status['celery']['status'] = 'unhealthy'
                health_status['celery']['error'] = 'No active workers found'
        except Exception as e:
            health_status['celery']['status'] = 'unhealthy'
            health_status['celery']['error'] = str(e)
        
        # Overall status
        if (health_status['celery']['status'] == 'healthy' and 
            health_status['redis']['status'] == 'healthy'):
            health_status['overall'] = 'healthy'
        
        # Return appropriate status code
        status_code = 200 if health_status['overall'] == 'healthy' else 503
        
        return Response(health_status, status=status_code)