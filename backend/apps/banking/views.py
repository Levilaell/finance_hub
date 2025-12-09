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
        Uses paid_at field to determine when bills were paid (for fully paid bills).
        For partial payments, we show them in the due_date month as we don't track
        individual payment dates.
        """
        from dateutil.relativedelta import relativedelta

        today = timezone.now()
        actual_data = []

        # Get last 12 months
        for i in range(11, -1, -1):
            month_start = (today - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + relativedelta(months=1)) - relativedelta(microseconds=1)

            # Get bills that were PAID in this month (using paid_at for fully paid bills)
            # For status=paid, use paid_at; for partially_paid, use due_date as fallback
            receivable_fully_paid = Bill.objects.filter(
                user=request.user,
                type='receivable',
                status='paid',
                paid_at__gte=month_start,
                paid_at__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0

            # For partially paid bills in this month (use due_date as we don't track partial payment dates)
            receivable_partial = Bill.objects.filter(
                user=request.user,
                type='receivable',
                status='partially_paid',
                due_date__gte=month_start.date(),
                due_date__lte=month_end.date()
            ).aggregate(total=Sum('amount_paid'))['total'] or 0

            receivable_paid = float(receivable_fully_paid) + float(receivable_partial)

            # Same for payables
            payable_fully_paid = Bill.objects.filter(
                user=request.user,
                type='payable',
                status='paid',
                paid_at__gte=month_start,
                paid_at__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0

            payable_partial = Bill.objects.filter(
                user=request.user,
                type='payable',
                status='partially_paid',
                due_date__gte=month_start.date(),
                due_date__lte=month_end.date()
            ).aggregate(total=Sum('amount_paid'))['total'] or 0

            payable_paid = float(payable_fully_paid) + float(payable_partial)

            actual_data.append({
                'month': month_start.strftime('%Y-%m'),
                'month_name': month_start.strftime('%b/%y'),
                'receivable_paid': receivable_paid,
                'payable_paid': payable_paid,
                'net': receivable_paid - payable_paid
            })

        return Response(actual_data)


# Temporary view for demo account reset
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
import uuid
from decimal import Decimal
import random


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_demo_account(request):
    """
    Temporary endpoint to reset demo account data.
    POST /api/banking/reset-demo/
    Body: {"secret": "demo_reset_2024"}
    """
    # Simple secret check
    secret = request.data.get('secret')
    if secret != 'demo_reset_2024':
        return Response({'error': 'Invalid secret'}, status=status.HTTP_403_FORBIDDEN)

    user_email = request.data.get('email', 'vitor@teste.com')

    User = get_user_model()
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        return Response({'error': f'User {user_email} not found'}, status=status.HTTP_404_NOT_FOUND)

    # Step 1: Clear existing data
    Bill.objects.filter(user=user).delete()
    BankConnection.objects.filter(user=user).delete()
    Category.objects.filter(user=user).delete()

    # Step 2: Create categories
    categories = _create_demo_categories(user)

    # Step 3: Create accounts
    accounts = _create_demo_accounts(user)

    # Step 4: Create transactions
    total_transactions = 0
    for account in accounts:
        count = _create_demo_transactions(account, user, categories)
        total_transactions += count

    # Step 5: Create bills
    bills_count = _create_demo_bills(user, categories)

    return Response({
        'success': True,
        'user': user_email,
        'accounts_created': len(accounts),
        'transactions_created': total_transactions,
        'bills_created': bills_count,
        'categories_created': len(categories),
    })


def _create_demo_categories(user):
    """Create categories for demo account"""
    categories_data = {
        'income': [
            ('Salario', '#10b981', '💰'),
            ('Atividades de empreendedorismo', '#059669', '💼'),
            ('Renda nao-recorrente', '#34d399', '🎁'),
            ('Juros de rendimentos de dividendos', '#6ee7b7', '📈'),
            ('Transferencia - PIX', '#22c55e', '⚡'),
            ('Transferencia mesma titularidade', '#16a34a', '🔄'),
        ],
        'expense': [
            ('Supermercado', '#f59e0b', '🛒'),
            ('Alimentos e bebidas', '#ea580c', '🍔'),
            ('Compras', '#f97316', '🛍️'),
            ('Compras online', '#fb923c', '📦'),
            ('Aluguel', '#ef4444', '🏠'),
            ('Eletricidade', '#dc2626', '💡'),
            ('Agua', '#3b82f6', '💧'),
            ('Internet', '#6366f1', '🌐'),
            ('Celular', '#8b5cf6', '📱'),
            ('Servicos', '#a855f7', '🛠️'),
            ('Impostos', '#64748b', '📋'),
            ('Taxas bancarias', '#475569', '🏦'),
            ('Transporte', '#0ea5e9', '🚗'),
            ('Postos de gasolina', '#0284c7', '⛽'),
            ('Saude', '#ec4899', '🏥'),
            ('Farmacia', '#db2777', '💊'),
            ('Educacao', '#8b5cf6', '📚'),
            ('Streaming de video', '#7c3aed', '📺'),
            ('Streaming de musica', '#6d28d9', '🎵'),
            ('Restaurantes, bares e lanchonetes', '#f43f5e', '🍽️'),
            ('Delivery de alimentos', '#e11d48', '🛵'),
            ('Transferencia - PIX', '#64748b', '⚡'),
            ('Apostas', '#dc2626', '🎰'),
            ('Outros', '#94a3b8', '📁'),
        ]
    }

    categories = {}
    for cat_type, items in categories_data.items():
        for name, color, icon in items:
            category, _ = Category.objects.get_or_create(
                user=user,
                name=name,
                type=cat_type,
                defaults={'color': color, 'icon': icon, 'is_system': True}
            )
            categories[name] = category

    return categories


def _create_demo_accounts(user):
    """Create fake bank accounts for demo"""
    from .models import Connector, BankConnection, BankAccount

    banks = [
        {'pluggy_id': 999001, 'name': 'Banco Inter', 'logo': 'https://logo.clearbit.com/bancointer.com.br', 'color': '#FF7A00'},
        {'pluggy_id': 999002, 'name': 'Mercado Pago', 'logo': 'https://logo.clearbit.com/mercadopago.com.br', 'color': '#009EE3'},
        {'pluggy_id': 999003, 'name': 'Nubank', 'logo': 'https://logo.clearbit.com/nubank.com.br', 'color': '#8A05BE'},
    ]

    accounts_config = [
        {'bank_idx': 0, 'name': 'BANCO INTER', 'type': 'CHECKING', 'balance': Decimal('12450.83')},
        {'bank_idx': 1, 'name': 'Mercado Pago', 'type': 'CHECKING', 'balance': Decimal('3280.45')},
        {'bank_idx': 2, 'name': 'Nubank Conta', 'type': 'CHECKING', 'balance': Decimal('8920.17')},
    ]

    accounts = []
    for config in accounts_config:
        bank = banks[config['bank_idx']]

        connector, _ = Connector.objects.get_or_create(
            pluggy_id=bank['pluggy_id'],
            defaults={
                'name': bank['name'],
                'institution_name': bank['name'],
                'logo_url': bank['logo'],
                'primary_color': bank['color'],
                'type': 'PERSONAL_BANK',
                'country': 'BR',
                'is_active': True,
                'is_sandbox': True,
            }
        )

        connection, _ = BankConnection.objects.get_or_create(
            user=user,
            connector=connector,
            defaults={
                'pluggy_item_id': f'demo_{uuid.uuid4().hex[:16]}',
                'status': 'UPDATED',
                'is_active': True,
            }
        )

        account = BankAccount.objects.create(
            connection=connection,
            pluggy_account_id=f'demo_acc_{uuid.uuid4().hex[:16]}',
            type=config['type'],
            name=config['name'],
            balance=config['balance'],
            is_active=True,
        )
        accounts.append(account)

    return accounts


def _create_demo_transactions(account, user, categories):
    """Create realistic transactions for demo account"""
    now = timezone.now()
    transactions_created = 0

    is_main_account = 'INTER' in account.name.upper()
    is_mp = 'MERCADO' in account.name.upper()

    # --- RECEITAS ---
    if is_main_account:
        for days_ago in range(90):
            date = now - timedelta(days=days_ago)
            if date.weekday() == 6:
                continue

            num_sales = random.randint(3, 8) if date.weekday() in [4, 5] else random.randint(1, 5)

            for _ in range(num_sales):
                payment_type = random.choices(
                    ['Cartao De Credito - Stripe', 'Cartao De Debito - Stripe', 'PIX'],
                    weights=[40, 30, 30]
                )[0]

                amount = Decimal(str(round(random.uniform(45.00, 350.00), 2)))
                hour = random.randint(8, 21)
                minute = random.randint(0, 59)
                tx_date = date.replace(hour=hour, minute=minute, second=0, microsecond=0)

                if 'PIX' in payment_type:
                    names = ['Maria Santos', 'Joao Silva', 'Ana Costa', 'Carlos Oliveira', 'Pedro Souza']
                    desc = f'Pix recebido - {random.choice(names)}'
                    cat_name = 'Transferencia - PIX'
                else:
                    desc = f'Credito domicilio cartao - {payment_type}'
                    cat_name = 'Atividades de empreendedorismo'

                Transaction.objects.create(
                    account=account,
                    pluggy_transaction_id=f'tx_{uuid.uuid4().hex[:20]}',
                    type='CREDIT',
                    description=desc,
                    amount=amount,
                    currency_code='BRL',
                    date=tx_date,
                    pluggy_category=cat_name,
                    user_category=categories.get(cat_name),
                )
                transactions_created += 1

    # Transferencias entre contas
    if is_mp or 'NUBANK' in account.name.upper():
        for _ in range(random.randint(5, 15)):
            days_ago = random.randint(0, 90)
            date = (now - timedelta(days=days_ago)).replace(
                hour=random.randint(9, 18), minute=random.randint(0, 59)
            )
            amount = Decimal(str(round(random.uniform(100, 2000), 2)))

            Transaction.objects.create(
                account=account,
                pluggy_transaction_id=f'tx_{uuid.uuid4().hex[:20]}',
                type='CREDIT',
                description='Transferencia Pix recebida LEVI LAEL COELHO SILVA',
                amount=amount,
                currency_code='BRL',
                date=date,
                pluggy_category='Transferencia mesma titularidade',
                user_category=categories.get('Transferencia mesma titularidade'),
            )
            transactions_created += 1

    # --- DESPESAS FIXAS ---
    if is_main_account:
        fixed_expenses = [
            (5, 'Aluguel Comercial - Imobiliaria Centro', Decimal('3200.00'), 'Aluguel'),
            (10, 'CPFL Energia - Conta de Luz', (450.00, 780.00), 'Eletricidade'),
            (12, 'Sabesp - Conta de Agua', (180.00, 320.00), 'Agua'),
            (15, 'Vivo Empresarial - Internet', Decimal('249.90'), 'Internet'),
            (8, 'Claro - Celular Empresarial', Decimal('189.90'), 'Celular'),
            (20, 'DAS - Simples Nacional', (850.00, 1450.00), 'Impostos'),
            (22, 'Servicos Contabeis - Contabilidade Silva', Decimal('550.00'), 'Servicos'),
        ]

        for month_offset in range(3):
            for day, desc, amount, cat_name in fixed_expenses:
                try:
                    tx_date = (now.replace(day=1) - timedelta(days=month_offset * 30)).replace(
                        day=day, hour=random.randint(7, 11), minute=random.randint(0, 59)
                    )
                except ValueError:
                    continue

                if tx_date > now:
                    continue

                if isinstance(amount, tuple):
                    final_amount = Decimal(str(round(random.uniform(*amount), 2)))
                else:
                    final_amount = amount

                Transaction.objects.create(
                    account=account,
                    pluggy_transaction_id=f'tx_{uuid.uuid4().hex[:20]}',
                    type='DEBIT',
                    description=desc,
                    amount=final_amount,
                    currency_code='BRL',
                    date=tx_date,
                    pluggy_category=cat_name,
                    user_category=categories.get(cat_name),
                )
                transactions_created += 1

    # Despesas variaveis
    variable_expenses = [
        ('Pix enviado - Pay4fun Instituicao De Pagamento Sa', (20.00, 100.00), 'Servicos'),
        ('Pix enviado - Gowd Instituicao De Pagamento Ltda', (50.00, 150.00), 'Servicos'),
        ('Compra no Debito - Supermercado Dia', (80.00, 350.00), 'Supermercado'),
        ('Compra no Debito - Posto Shell', (100.00, 400.00), 'Postos de gasolina'),
        ('Compra no Debito - Farmacia Drogasil', (25.00, 180.00), 'Farmacia'),
        ('Pix enviado - iFood', (25.00, 95.00), 'Delivery de alimentos'),
        ('Pix enviado - Uber', (15.00, 65.00), 'Transporte'),
        ('Pix enviado - 99', (12.00, 55.00), 'Transporte'),
        ('Netflix.com', Decimal('55.90'), 'Streaming de video'),
        ('Spotify', Decimal('34.90'), 'Streaming de musica'),
        ('Amazon Prime', Decimal('19.90'), 'Streaming de video'),
        ('Compra Online - Mercado Livre', (35.00, 450.00), 'Compras online'),
        ('Compra Online - Amazon', (45.00, 380.00), 'Compras online'),
        ('Compra Online - Shopee', (15.00, 180.00), 'Compras online'),
    ]

    for _ in range(random.randint(25, 45)):
        days_ago = random.randint(0, 90)
        tx_date = (now - timedelta(days=days_ago)).replace(
            hour=random.randint(8, 22), minute=random.randint(0, 59)
        )

        desc, amount, cat_name = random.choice(variable_expenses)

        if isinstance(amount, tuple):
            final_amount = Decimal(str(round(random.uniform(*amount), 2)))
        else:
            final_amount = amount

        Transaction.objects.create(
            account=account,
            pluggy_transaction_id=f'tx_{uuid.uuid4().hex[:20]}',
            type='DEBIT',
            description=desc,
            amount=final_amount,
            currency_code='BRL',
            date=tx_date,
            pluggy_category=cat_name,
            user_category=categories.get(cat_name),
        )
        transactions_created += 1

    # PIX para terceiros
    pix_recipients = ['Maria Santos', 'Joao Silva', 'Ana Costa', 'Carlos Oliveira', 'Pedro Souza', 'Julia Ferreira']

    for _ in range(random.randint(8, 20)):
        days_ago = random.randint(0, 90)
        tx_date = (now - timedelta(days=days_ago)).replace(
            hour=random.randint(8, 21), minute=random.randint(0, 59)
        )

        recipient = random.choice(pix_recipients)
        amount = Decimal(str(round(random.uniform(10, 500), 2)))

        Transaction.objects.create(
            account=account,
            pluggy_transaction_id=f'tx_{uuid.uuid4().hex[:20]}',
            type='DEBIT',
            description=f'Pix enviado - {recipient}',
            amount=amount,
            currency_code='BRL',
            date=tx_date,
            pluggy_category='Transferencia - PIX',
            user_category=categories.get('Transferencia - PIX'),
        )
        transactions_created += 1

    return transactions_created


def _create_demo_bills(user, categories):
    """Create bills for demo account"""
    now = timezone.now()
    bills_created = 0

    # Contas a Pagar
    payables = [
        ('Aluguel Comercial - Janeiro', Decimal('3200.00'), 5, 'Aluguel'),
        ('CPFL Energia', Decimal('685.40'), 10, 'Eletricidade'),
        ('Sabesp - Agua', Decimal('245.80'), 12, 'Agua'),
        ('Internet Vivo', Decimal('249.90'), 15, 'Internet'),
        ('Celular Claro', Decimal('189.90'), 8, 'Celular'),
        ('DAS Simples Nacional', Decimal('1180.00'), 20, 'Impostos'),
        ('Contador - Honorarios', Decimal('550.00'), 22, 'Servicos'),
        ('Fornecedor ABC - Mercadorias', Decimal('4500.00'), 18, 'Supermercado'),
        ('Fornecedor XYZ - Produtos', Decimal('2800.00'), 25, 'Supermercado'),
    ]

    for desc, amount, day, cat_name in payables:
        try:
            due_date = now.replace(day=1) + timedelta(days=day - 1)
            if due_date.month != now.month:
                due_date = (now.replace(day=1) + timedelta(days=32)).replace(day=day)
        except ValueError:
            due_date = now + timedelta(days=day)

        bill_status = 'pending'
        amount_paid = Decimal('0.00')

        if due_date.date() < now.date():
            bill_status = 'paid'
            amount_paid = amount

        Bill.objects.create(
            user=user,
            type='payable',
            description=desc,
            amount=amount,
            amount_paid=amount_paid,
            due_date=due_date.date(),
            status=bill_status,
            category=categories.get(cat_name),
            customer_supplier='Fornecedor',
        )
        bills_created += 1

    # Contas a Receber
    receivables = [
        ('Cliente A - Venda Parcelada 1/3', Decimal('850.00'), 10),
        ('Cliente B - Servico Prestado', Decimal('1200.00'), 15),
        ('Cliente C - Venda Parcelada 2/4', Decimal('450.00'), 20),
        ('Cliente D - Produto Encomendado', Decimal('680.00'), 8),
        ('Cliente E - Consultoria', Decimal('2500.00'), 25),
    ]

    for desc, amount, day in receivables:
        try:
            due_date = now.replace(day=1) + timedelta(days=day - 1)
            if due_date.month != now.month:
                due_date = (now.replace(day=1) + timedelta(days=32)).replace(day=day)
        except ValueError:
            due_date = now + timedelta(days=day)

        bill_status = 'pending'
        amount_paid = Decimal('0.00')

        if due_date.date() < now.date():
            bill_status = 'paid'
            amount_paid = amount

        Bill.objects.create(
            user=user,
            type='receivable',
            description=desc,
            amount=amount,
            amount_paid=amount_paid,
            due_date=due_date.date(),
            status=bill_status,
            category=categories.get('Atividades de empreendedorismo'),
            customer_supplier='Cliente',
        )
        bills_created += 1

    # Bills atrasados
    overdue = [
        ('Fornecedor Atrasado - Nota 1234', Decimal('1850.00'), -5),
        ('Manutencao Equipamentos', Decimal('780.00'), -10),
    ]

    for desc, amount, days_offset in overdue:
        due_date = now.date() + timedelta(days=days_offset)

        Bill.objects.create(
            user=user,
            type='payable',
            description=desc,
            amount=amount,
            amount_paid=Decimal('0.00'),
            due_date=due_date,
            status='pending',
            category=categories.get('Servicos'),
            customer_supplier='Fornecedor',
        )
        bills_created += 1

    return bills_created