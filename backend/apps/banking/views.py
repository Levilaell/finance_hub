"""
API Views for Banking application.
Ref: https://www.django-rest-framework.org/api-guide/viewsets/
"""

from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum, Count, Min, Max

from .models import (
    Connector, BankConnection, BankAccount,
    Transaction, SyncLog, Category, Bill
)
from .serializers import (
    ConnectorSerializer, BankConnectionSerializer,
    BankAccountSerializer, TransactionSerializer,
    CreateConnectionSerializer, TransactionFilterSerializer,
    SyncStatusSerializer, ConnectTokenSerializer,
    SummarySerializer, CategorySerializer, BillSerializer,
    BillFilterSerializer, RegisterPaymentSerializer, BillsSummarySerializer
)
from .services import (
    ConnectorService, BankConnectionService,
    TransactionService
)
from .pluggy_client import PluggyClient
from apps.authentication.models import UserActivityLog
from apps.authentication.signals import get_client_ip


class ConnectorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing available bank connectors.
    Ref: https://docs.pluggy.ai/reference/connectors
    """
    queryset = Connector.objects.filter(is_active=True)
    serializer_class = ConnectorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        country = self.request.query_params.get('country', 'BR')
        connector_type = self.request.query_params.get('type')

        queryset = queryset.filter(country=country)
        if connector_type:
            queryset = queryset.filter(type=connector_type)

        return queryset.order_by('name')

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """
        Sync connectors from Pluggy.
        POST /api/banking/connectors/sync/
        """
        service = ConnectorService()
        try:
            count = service.sync_connectors()
            return Response({
                'message': f'Successfully synced {count} connectors',
                'count': count
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BankConnectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bank connections.
    Ref: https://docs.pluggy.ai/docs/connect-an-account
    """
    serializer_class = BankConnectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BankConnection.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('connector').prefetch_related('accounts')

    def create(self, request):
        """
        Create a new bank connection.
        POST /api/banking/connections/
        """
        import logging
        from core.security_utils import sanitize_for_logging
        logger = logging.getLogger(__name__)

        logger.info(f"Creating connection with data: {sanitize_for_logging(request.data)}")

        # Check if this is a Pluggy widget callback (has pluggy_item_id)
        if 'pluggy_item_id' in request.data:
            service = BankConnectionService()
            try:
                logger.info(f"Creating connection from Pluggy item: {request.data['pluggy_item_id']}")
                connection = service.create_connection_from_item(
                    user=request.user,
                    item_id=request.data['pluggy_item_id']
                )
                logger.info(f"Connection created successfully: {connection.id}")

                # Log activity
                UserActivityLog.log_event(
                    user=request.user,
                    event_type='bank_connection_created',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    connection_id=str(connection.id),
                    connector_name=connection.connector.name,
                    pluggy_item_id=request.data['pluggy_item_id']
                )

                return Response(
                    BankConnectionSerializer(connection).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                logger.error(f"Error creating connection from item: {e}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Old flow for manual connection (if needed) - only if has connector_id
        if 'connector_id' in request.data:
            serializer = CreateConnectionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            service = BankConnectionService()
            try:
                connection = service.create_connection(
                    user=request.user,
                    connector_id=serializer.validated_data['connector_id'],
                    credentials=serializer.validated_data['credentials']
                )

                # Log activity
                UserActivityLog.log_event(
                    user=request.user,
                    event_type='bank_connection_created',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    connection_id=str(connection.id),
                    connector_name=connection.connector.name,
                    connector_id=serializer.validated_data['connector_id']
                )

                return Response(
                    BankConnectionSerializer(connection).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # If neither pluggy_item_id nor connector_id is provided
        logger.error(f"Invalid request data: {request.data}")
        return Response(
            {'error': 'Either pluggy_item_id or connector_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    def destroy(self, request, pk=None):
        """
        Delete (disconnect) a bank connection.
        DELETE /api/banking/connections/{id}/
        """
        connection = self.get_object()
        service = BankConnectionService()

        # Store connection info before deletion
        connection_id = str(connection.id)
        connector_name = connection.connector.name

        if service.delete_connection(connection):
            # Log activity
            UserActivityLog.log_event(
                user=request.user,
                event_type='bank_connection_deleted',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                connection_id=connection_id,
                connector_name=connector_name
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'error': 'Failed to delete connection'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def refresh_status(self, request, pk=None):
        """
        Refresh connection status from Pluggy.
        POST /api/banking/connections/{id}/refresh_status/
        """
        connection = self.get_object()
        service = BankConnectionService()

        try:
            updated_connection = service.update_connection_status(connection)

            # Log activity
            UserActivityLog.log_event(
                user=request.user,
                event_type='bank_connection_updated',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                connection_id=str(connection.id),
                connector_name=connection.connector.name,
                action='refresh_status',
                new_status=updated_connection.status
            )

            return Response(BankConnectionSerializer(updated_connection).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def sync_accounts(self, request, pk=None):
        """
        Sync accounts for this connection.
        POST /api/banking/connections/{id}/sync_accounts/
        """
        connection = self.get_object()
        service = BankConnectionService()

        # Log sync started
        UserActivityLog.log_event(
            user=request.user,
            event_type='sync_started',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            connection_id=str(connection.id),
            connector_name=connection.connector.name,
            sync_type='accounts'
        )

        try:
            count = service.sync_accounts(connection)

            # Log sync completed
            UserActivityLog.log_event(
                user=request.user,
                event_type='sync_completed',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                connection_id=str(connection.id),
                connector_name=connection.connector.name,
                sync_type='accounts',
                records_synced=count
            )

            return Response({
                'message': f'Synced {count} accounts',
                'count': count
            })
        except Exception as e:
            # Log sync failed
            UserActivityLog.log_event(
                user=request.user,
                event_type='sync_failed',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                connection_id=str(connection.id),
                connector_name=connection.connector.name,
                sync_type='accounts',
                error=str(e)
            )

            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def sync_transactions(self, request, pk=None):
        """
        Sync all transactions for this connection.
        This will trigger an item update in Pluggy to fetch fresh data.
        POST /api/banking/connections/{id}/sync_transactions/

        Returns immediately with sync initiation status.
        Use check_status endpoint to monitor progress.
        """
        connection = self.get_object()
        service = BankConnectionService()

        # Log sync started
        UserActivityLog.log_event(
            user=request.user,
            event_type='sync_started',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            connection_id=str(connection.id),
            connector_name=connection.connector.name,
            sync_type='transactions'
        )

        try:
            # Trigger manual sync
            sync_status = service.trigger_manual_sync(connection)

            # Log sync status
            if sync_status['status'] in ['UPDATED', 'UPDATING']:
                UserActivityLog.log_event(
                    user=request.user,
                    event_type='sync_completed',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    connection_id=str(connection.id),
                    connector_name=connection.connector.name,
                    sync_type='transactions',
                    sync_status=sync_status['status']
                )

            # Return sync initiation status immediately
            return Response({
                'message': 'Synchronization initiated',
                'sync_status': sync_status['status'],
                'item_status': sync_status.get('item_status'),
                'requires_action': sync_status['status'] in ['MFA_REQUIRED', 'CREDENTIALS_REQUIRED'],
                'mfa_parameter': sync_status.get('parameter') if sync_status['status'] == 'MFA_REQUIRED' else None
            })

        except ValueError as e:
            # Handle MFA or credential errors
            error_msg = str(e)

            # Log sync failed
            UserActivityLog.log_event(
                user=request.user,
                event_type='sync_failed',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                connection_id=str(connection.id),
                connector_name=connection.connector.name,
                sync_type='transactions',
                error=error_msg
            )

            if 'MFA required' in error_msg:
                return Response({
                    'error': error_msg,
                    'status': 'MFA_REQUIRED',
                    'requires_action': True
                }, status=status.HTTP_400_BAD_REQUEST)
            elif 'Invalid credentials' in error_msg:
                return Response({
                    'error': error_msg,
                    'status': 'CREDENTIALS_REQUIRED',
                    'requires_action': True
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'error': error_msg,
                    'status': 'ERROR'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log sync failed
            UserActivityLog.log_event(
                user=request.user,
                event_type='sync_failed',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                connection_id=str(connection.id),
                connector_name=connection.connector.name,
                sync_type='transactions',
                error=str(e)
            )

            return Response(
                {'error': str(e), 'status': 'ERROR'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def send_mfa(self, request, pk=None):
        """
        Send MFA token for a connection.
        POST /api/banking/connections/{id}/send_mfa/
        {
            "mfa_value": "123456",
            "parameter_name": "token"  // optional, defaults to 'token'
        }
        """
        connection = self.get_object()
        mfa_value = request.data.get('mfa_value')
        parameter_name = request.data.get('parameter_name', 'token')

        if not mfa_value:
            return Response(
                {'error': 'mfa_value is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            client = PluggyClient()
            result = client.send_mfa(
                item_id=connection.pluggy_item_id,
                mfa_value=mfa_value,
                mfa_parameter_name=parameter_name
            )

            # Update connection status
            connection.status = result['status']
            connection.last_updated_at = timezone.now()
            connection.save()

            return Response({
                'message': 'MFA sent successfully',
                'status': result['status']
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def check_status(self, request, pk=None):
        """
        Check the current status of a connection and sync progress.
        GET /api/banking/connections/{id}/check_status/

        Returns:
            status: Item status (UPDATING, UPDATED, etc)
            execution_status: Current execution phase (LOGIN_IN_PROGRESS, TRANSACTIONS_IN_PROGRESS, SUCCESS, etc)
            is_syncing: Boolean indicating if sync is in progress
            sync_complete: Boolean indicating if sync has completed
            requires_action: Boolean indicating if user action needed
        """
        connection = self.get_object()

        try:
            client = PluggyClient()
            item = client.get_item(connection.pluggy_item_id)

            # Update local status
            connection.status = item['status']
            connection.status_detail = item.get('statusDetail')
            connection.execution_status = item.get('executionStatus', '')
            connection.last_updated_at = timezone.now()
            connection.save()

            item_status = item['status']
            execution_status = item.get('executionStatus')

            # Determine sync state
            is_syncing = item_status == 'UPDATING'
            sync_complete = item_status == 'UPDATED' and execution_status == 'SUCCESS'
            requires_action = item_status in ['WAITING_USER_INPUT', 'LOGIN_ERROR']

            response_data = {
                'status': item_status,
                'status_detail': item.get('statusDetail'),
                'execution_status': execution_status,
                'last_updated_at': connection.last_updated_at.isoformat(),
                'is_syncing': is_syncing,
                'sync_complete': sync_complete,
                'requires_action': requires_action
            }

            # Add MFA info if waiting for user input
            if item_status == 'WAITING_USER_INPUT':
                response_data['mfa_required'] = True
                response_data['parameter'] = item.get('parameter', {})

            # Add error info if needed
            if item_status in ['LOGIN_ERROR', 'ERROR', 'OUTDATED']:
                response_data['error_message'] = item.get('statusDetail', {}).get('message', 'Unknown error')

            return Response(response_data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def reconnect_token(self, request, pk=None):
        """
        Get a connect token for reconnecting/updating an existing connection.
        This is used when LOGIN_ERROR or credential issues occur.
        GET /api/banking/connections/{id}/reconnect_token/
        """
        connection = self.get_object()

        try:
            client = PluggyClient()
            token = client._get_connect_token(item_id=connection.pluggy_item_id)

            expires_at = timezone.now() + timedelta(minutes=30)
            return Response({
                'token': token,
                'expires_at': expires_at,
                'item_id': connection.pluggy_item_id,
                'connection_id': str(connection.id)
            })
        except Exception as e:
            logger.error(f"Error getting reconnect token: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def connect_token(self, request):
        """
        Get a connect token for Pluggy widget.
        Can optionally update an existing item.
        GET /api/banking/connections/connect_token/
        Query params:
            - item_id: Optional, for updating an existing connection
        """
        import logging
        logger = logging.getLogger(__name__)

        item_id = request.query_params.get('item_id')

        try:
            client = PluggyClient()
            logger.info("PluggyClient initialized successfully")

            token = client._get_connect_token(item_id=item_id)
            logger.info(f"Connect token obtained for item_id={item_id}: {token[:10]}...")

            expires_at = timezone.now() + timedelta(minutes=30)
            return Response({
                'token': token,
                'expires_at': expires_at,
                'item_id': item_id
            })
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return Response(
                {'error': f'Configuration error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Failed to get connect token: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BankAccountViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing bank accounts.
    Ref: https://docs.pluggy.ai/reference/accounts
    """
    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Otimização: select_related para evitar N+1 queries
        return BankAccount.objects.filter(
            connection__user=self.request.user,
            connection__is_active=True,
            is_active=True
        ).select_related(
            'connection',
            'connection__connector',
            'connection__user'
        )

    @action(detail=True, methods=['post'])
    def sync_transactions(self, request, pk=None):
        """
        Sync transactions for a specific account.
        POST /api/banking/accounts/{id}/sync_transactions/
        """
        account = self.get_object()
        service = TransactionService()
        days_back = int(request.data.get('days_back', 365))

        try:
            count = service.sync_transactions(account, days_back=days_back)
            return Response({
                'message': f'Synced {count} transactions',
                'count': count
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing transactions and updating their categories.
    Ref: https://docs.pluggy.ai/reference/transactions
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['account', 'type', 'category']
    http_method_names = ['get', 'patch', 'head', 'options']  # Only allow GET and PATCH

    def get_queryset(self):
        import logging
        logger = logging.getLogger(__name__)

        # Log para debug
        logger.info(f"Getting transactions for user {self.request.user.id}")

        # Primeiro, vamos ver todas as transações sem filtro
        all_transactions = Transaction.objects.all()
        logger.info(f"Total transactions in DB: {all_transactions.count()}")

        # Agora com filtro de usuário - Otimização: select_related para evitar N+1 queries
        queryset = Transaction.objects.filter(
            account__connection__user=self.request.user,
            account__connection__is_active=True
        ).select_related(
            'account',
            'account__connection',
            'account__connection__connector',
            'user_category'
        )

        logger.info(f"Transactions for user {self.request.user.id}: {queryset.count()}")

        # Log das datas das transações
        if queryset.exists():
            dates = queryset.values_list('date', flat=True)[:5]
            logger.info(f"Sample transaction dates: {list(dates)}")

        # Apply filters
        filter_serializer = TransactionFilterSerializer(data=self.request.query_params)
        if filter_serializer.is_valid():
            filters = filter_serializer.validated_data
            logger.info(f"Applying filters: {filters}")

            if 'account_id' in filters:
                queryset = queryset.filter(account_id=filters['account_id'])
                logger.info(f"After account filter: {queryset.count()}")
            if 'date_from' in filters:
                queryset = queryset.filter(date__gte=filters['date_from'])
                logger.info(f"After date_from filter: {queryset.count()}")
            if 'date_to' in filters:
                queryset = queryset.filter(date__lte=filters['date_to'])
                logger.info(f"After date_to filter: {queryset.count()}")
            if 'type' in filters:
                queryset = queryset.filter(type=filters['type'])
            if 'category' in filters:
                queryset = queryset.filter(pluggy_category__icontains=filters['category'])
        else:
            logger.error(f"Filter validation errors: {filter_serializer.errors}")

        logger.info(f"Final queryset count: {queryset.count()}")
        return queryset.order_by('-date', '-created_at')

    def update(self, request, *args, **kwargs):
        """
        Update transaction category.
        PATCH /api/banking/transactions/{id}/
        Body: { "user_category_id": "uuid" } or { "user_category_id": null }
        """
        partial = kwargs.pop('partial', True)  # Force partial update
        instance = self.get_object()

        # Only allow updating user_category
        allowed_fields = {'user_category_id'}
        request_fields = set(request.data.keys())

        if not request_fields.issubset(allowed_fields):
            return Response(
                {'error': 'Only user_category_id can be updated'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get financial summary.
        GET /api/banking/transactions/summary/
        """
        import logging
        from calendar import monthrange
        logger = logging.getLogger(__name__)

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        # Start with all user transactions
        transactions = self.get_queryset()

        # If no dates provided, always default to current month
        if not date_from and not date_to:
            # Use timezone-aware current time in local timezone (America/Sao_Paulo)
            from django.conf import settings
            import pytz

            utc_now = timezone.now()
            local_tz = pytz.timezone(settings.TIME_ZONE)
            local_now = utc_now.astimezone(local_tz)

            logger.info(f"UTC now: {utc_now}, Local now ({settings.TIME_ZONE}): {local_now}")

            # Always use current month (using local timezone)
            current_month_start = local_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_day = monthrange(local_now.year, local_now.month)[1]
            current_month_end = local_now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

            date_from = current_month_start.date()
            date_to = current_month_end.date()
            logger.info(f"Using current month: {date_from} to {date_to}")

        # Apply date filters
        if date_from:
            if isinstance(date_from, str):
                date_from = datetime.fromisoformat(date_from).date()
            transactions = transactions.filter(date__gte=date_from)
            logger.info(f"Filtering from date: {date_from}")

        if date_to:
            if isinstance(date_to, str):
                date_to = datetime.fromisoformat(date_to).date()
            transactions = transactions.filter(date__lte=date_to)
            logger.info(f"Filtering to date: {date_to}")

        logger.info(f"Summary transactions count: {transactions.count()}")

        income = transactions.filter(type='CREDIT').aggregate(
            total=Sum('amount')
        )['total'] or 0

        expenses = transactions.filter(type='DEBIT').aggregate(
            total=Sum('amount')
        )['total'] or 0

        # Expenses should be negative for proper balance calculation
        # If expenses are positive in DB, negate them
        if expenses > 0:
            expenses = -expenses

        accounts_count = BankAccount.objects.filter(
            connection__user=request.user,
            connection__is_active=True,
            is_active=True
        ).count()

        # Balance = income + expenses (expenses already negative)
        balance = income + expenses

        return Response({
            'income': income,
            'expenses': expenses,
            'balance': balance,
            'period_start': date_from,
            'period_end': date_to,
            'accounts_count': accounts_count,
            'transactions_count': transactions.count()
        })


class SyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing sync logs.
    """
    serializer_class = SyncStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SyncLog.objects.filter(
            connection__user=self.request.user
        ).order_by('-started_at')[:20]  # Last 20 logs


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing transaction categories.
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Category.objects.filter(user=self.request.user)

        # Filter by type if provided
        category_type = self.request.query_params.get('type')
        if category_type:
            queryset = queryset.filter(type=category_type)

        return queryset.order_by('type', 'name')

    def perform_create(self, serializer):
        """Assign current user when creating a category."""
        serializer.save(user=self.request.user)

    def destroy(self, request, pk=None):
        """Prevent deletion of system categories."""
        category = self.get_object()

        if category.is_system:
            return Response(
                {'error': 'Cannot delete system categories'},
                status=status.HTTP_400_BAD_REQUEST
            )

        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BillViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bills (accounts payable/receivable).
    """
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        """Get bills for the current user with filters."""
        # Otimização: select_related para evitar N+1 queries
        queryset = Bill.objects.filter(user=self.request.user).select_related('category', 'user')

        # Apply filters
        filter_serializer = BillFilterSerializer(data=self.request.query_params)
        if filter_serializer.is_valid():
            filters = filter_serializer.validated_data

            if 'type' in filters:
                queryset = queryset.filter(type=filters['type'])
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
            if 'date_from' in filters:
                queryset = queryset.filter(due_date__gte=filters['date_from'])
            if 'date_to' in filters:
                queryset = queryset.filter(due_date__lte=filters['date_to'])
            if 'category' in filters:
                queryset = queryset.filter(category_id=filters['category'])
            if 'is_overdue' in filters and filters['is_overdue']:
                today = timezone.now().date()
                queryset = queryset.filter(
                    due_date__lt=today
                ).exclude(status__in=['paid', 'cancelled'])

        return queryset.select_related('category').order_by('due_date', '-created_at')

    def perform_create(self, serializer):
        """Assign current user when creating a bill."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def register_payment(self, request, pk=None):
        """
        Register a payment for a bill.
        POST /api/banking/bills/{id}/register_payment/
        Body: { "amount": 100.00, "notes": "..." }
        """
        bill = self.get_object()
        serializer = RegisterPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment_amount = serializer.validated_data['amount']
        notes = serializer.validated_data.get('notes', '')

        # Validate payment amount
        if payment_amount > bill.amount_remaining:
            return Response(
                {'error': f'Payment amount ({payment_amount}) exceeds remaining amount ({bill.amount_remaining})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update bill
        bill.amount_paid += payment_amount
        if notes:
            bill.notes = f"{bill.notes}\n{notes}" if bill.notes else notes
        bill.update_status()

        return Response(BillSerializer(bill).data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get bills summary.
        GET /api/banking/bills/summary/
        """
        from calendar import monthrange

        # Get current month range
        utc_now = timezone.now()
        from django.conf import settings
        import pytz
        local_tz = pytz.timezone(settings.TIME_ZONE)
        local_now = utc_now.astimezone(local_tz)

        current_month_start = local_now.replace(day=1)
        last_day = monthrange(local_now.year, local_now.month)[1]
        current_month_end = local_now.replace(day=last_day, hour=23, minute=59, second=59)

        # Get all bills for user
        bills = Bill.objects.filter(user=request.user)

        # Calculate totals
        receivable_bills = bills.filter(type='receivable').exclude(status='cancelled')
        payable_bills = bills.filter(type='payable').exclude(status='cancelled')

        # Total receivable (pending + partially paid)
        total_receivable = receivable_bills.exclude(status='paid').aggregate(
            total=Sum('amount') - Sum('amount_paid')
        )['total'] or 0

        # Total receivable this month
        total_receivable_month = receivable_bills.filter(
            due_date__gte=current_month_start.date(),
            due_date__lte=current_month_end.date()
        ).exclude(status='paid').aggregate(
            total=Sum('amount') - Sum('amount_paid')
        )['total'] or 0

        # Total payable (pending + partially paid)
        total_payable = payable_bills.exclude(status='paid').aggregate(
            total=Sum('amount') - Sum('amount_paid')
        )['total'] or 0

        # Total payable this month
        total_payable_month = payable_bills.filter(
            due_date__gte=current_month_start.date(),
            due_date__lte=current_month_end.date()
        ).exclude(status='paid').aggregate(
            total=Sum('amount') - Sum('amount_paid')
        )['total'] or 0

        # Overdue bills (both types)
        today = local_now.date()
        overdue_bills = bills.filter(
            due_date__lt=today,
        ).exclude(status__in=['paid', 'cancelled'])

        total_overdue = overdue_bills.aggregate(
            total=Sum('amount') - Sum('amount_paid')
        )['total'] or 0

        summary_data = {
            'total_receivable': total_receivable,
            'total_receivable_month': total_receivable_month,
            'total_payable': total_payable,
            'total_payable_month': total_payable_month,
            'total_overdue': total_overdue,
            'overdue_count': overdue_bills.count(),
            'receivable_count': receivable_bills.exclude(status='paid').count(),
            'payable_count': payable_bills.exclude(status='paid').count(),
        }

        serializer = BillsSummarySerializer(summary_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def cash_flow_projection(self, request):
        """
        Get cash flow projection for the next 12 months.
        GET /api/banking/bills/cash_flow_projection/
        Otimizado: busca todas as bills de uma vez e processa em Python
        """
        from dateutil.relativedelta import relativedelta
        from decimal import Decimal

        today = timezone.now().date()

        # Calcular range de 12 meses
        start_date = today
        end_date = (today + relativedelta(months=12))

        # Otimização: Uma única query para todas as bills dos próximos 12 meses
        bills = Bill.objects.filter(
            user=request.user,
            due_date__gte=start_date,
            due_date__lt=end_date
        ).exclude(status='cancelled').values(
            'type',
            'due_date',
            'amount',
            'amount_paid'
        )

        # Criar estrutura de meses
        months_data = {}
        for i in range(12):
            month_start = (today + relativedelta(months=i)).replace(day=1)
            month_key = month_start.strftime('%Y-%m')
            months_data[month_key] = {
                'month': month_key,
                'month_name': month_start.strftime('%B %Y'),
                'receivable': Decimal('0'),
                'payable': Decimal('0'),
            }

        # Processar bills em Python (mais rápido que 48 queries SQL)
        for bill in bills:
            month_key = bill['due_date'].strftime('%Y-%m')
            if month_key in months_data:
                remaining = bill['amount'] - bill['amount_paid']
                if bill['type'] == 'receivable':
                    months_data[month_key]['receivable'] += remaining
                else:
                    months_data[month_key]['payable'] += remaining

        # Converter para lista ordenada
        projections = []
        for month_key in sorted(months_data.keys()):
            data = months_data[month_key]
            projections.append({
                'month': data['month'],
                'month_name': data['month_name'],
                'receivable': float(data['receivable']),
                'payable': float(data['payable']),
                'net': float(data['receivable'] - data['payable'])
            })

        return Response(projections)

    @action(detail=False, methods=['get'])
    def actual_cash_flow(self, request):
        """
        Get actual cash flow based on bill payments for the last 12 months.
        GET /api/banking/bills/actual_cash_flow/

        Returns monthly data showing what was actually paid/received from bills.
        """
        from dateutil.relativedelta import relativedelta

        today = timezone.now().date()
        actual_data = []

        # Get last 12 months
        for i in range(11, -1, -1):
            month_start = (today - relativedelta(months=i)).replace(day=1)
            month_end = (month_start + relativedelta(months=1)) - relativedelta(days=1)

            # Get bills that were paid (fully or partially) in this month
            receivable_bills = Bill.objects.filter(
                user=request.user,
                type='receivable',
                due_date__gte=month_start,
                due_date__lte=month_end
            ).exclude(status='cancelled')

            # Sum the amount_paid (what was actually received)
            receivable_paid = receivable_bills.aggregate(total=Sum('amount_paid'))['total'] or 0

            payable_bills = Bill.objects.filter(
                user=request.user,
                type='payable',
                due_date__gte=month_start,
                due_date__lte=month_end
            ).exclude(status='cancelled')

            # Sum the amount_paid (what was actually paid)
            payable_paid = payable_bills.aggregate(total=Sum('amount_paid'))['total'] or 0

            actual_data.append({
                'month': month_start.strftime('%Y-%m'),
                'month_name': month_start.strftime('%b/%y'),
                'receivable_paid': float(receivable_paid),
                'payable_paid': float(payable_paid),
                'net': float(receivable_paid - payable_paid)
            })

        return Response(actual_data)