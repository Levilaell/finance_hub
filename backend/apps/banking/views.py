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
    Transaction, SyncLog, Category, Bill, CategoryRule
)
from .serializers import (
    ConnectorSerializer, BankConnectionSerializer,
    BankAccountSerializer, TransactionSerializer,
    CreateConnectionSerializer, TransactionFilterSerializer,
    SyncStatusSerializer, ConnectTokenSerializer,
    SummarySerializer, CategorySerializer, BillSerializer,
    BillFilterSerializer, RegisterPaymentSerializer, BillsSummarySerializer,
    LinkTransactionSerializer, LinkBillSerializer,
    TransactionSuggestionSerializer, BillSuggestionSerializer,
    UserSettingsSerializer,
    BillUploadSerializer, BillOCRResultSerializer, BillFromOCRSerializer,
    CategoryRuleSerializer,
    # BillPayment serializers (pagamentos parciais)
    BillPaymentSerializer, BillPaymentCreateSerializer, PartialPaymentTransactionSerializer
)
from .services import (
    ConnectorService, BankConnectionService,
    TransactionService, TransactionMatchService, CategoryRuleService
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
        Update transaction category with optional batch operations.
        PATCH /api/banking/transactions/{id}/

        Body options:
        - Simple: { "user_category_id": "uuid" }
        - With batch: {
            "user_category_id": "uuid",
            "apply_to_similar": true,
            "create_rule": true,
            "similar_transaction_ids": ["uuid1", "uuid2"]
          }
        """
        import logging
        logger = logging.getLogger(__name__)

        partial = kwargs.pop('partial', True)
        instance = self.get_object()

        # Extract batch operation flags
        apply_to_similar = request.data.get('apply_to_similar', False)
        create_rule = request.data.get('create_rule', False)
        similar_ids = request.data.get('similar_transaction_ids', [])

        # Only allow specific fields
        allowed_fields = {'user_category_id', 'apply_to_similar', 'create_rule', 'similar_transaction_ids'}
        request_fields = set(request.data.keys())

        if not request_fields.issubset(allowed_fields):
            return Response(
                {'error': 'Only user_category_id and batch operation fields are allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the main transaction
        update_data = {'user_category_id': request.data.get('user_category_id')}
        serializer = self.get_serializer(instance, data=update_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Refresh to get updated category
        instance.refresh_from_db()

        # Track batch operation results
        applied_count = 0
        rule_created = False

        # Apply to similar transactions if requested
        if apply_to_similar and similar_ids and instance.user_category:
            applied_count = Transaction.objects.filter(
                id__in=similar_ids,
                account__connection__user=request.user
            ).update(user_category=instance.user_category)
            logger.info(f"Applied category to {applied_count} similar transactions")

        # Create rule if requested
        if create_rule and instance.user_category:
            try:
                CategoryRuleService.create_rule_from_transaction(
                    request.user,
                    instance,
                    instance.user_category
                )
                rule_created = True
                logger.info(f"Created category rule from transaction {instance.id}")
            except ValueError as e:
                logger.warning(f"Could not create rule: {e}")

        response_data = serializer.data
        response_data['applied_to_similar'] = applied_count
        response_data['rule_created'] = rule_created

        return Response(response_data)

    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """
        Get similar transactions for batch categorization.
        GET /api/banking/transactions/{id}/similar/

        Returns transactions that match by:
        1. Same merchant_name (highest score)
        2. Similar description prefix
        3. Fuzzy description match (>70%)
        """
        transaction = self.get_object()

        similar = CategoryRuleService.find_similar_transactions(
            request.user,
            transaction,
            limit=50
        )

        # Determine suggested pattern
        if transaction.merchant_name:
            suggested_pattern = CategoryRuleService.normalize_text(transaction.merchant_name)
            suggested_match_type = 'contains'
        else:
            suggested_pattern = CategoryRuleService.normalize_text(transaction.description)[:12]
            suggested_match_type = 'prefix'

        return Response({
            'count': len(similar),
            'transactions': [
                {
                    'id': str(s['transaction'].id),
                    'description': s['transaction'].description,
                    'merchant_name': s['transaction'].merchant_name or '',
                    'amount': str(s['transaction'].amount),
                    'date': s['transaction'].date.isoformat(),
                    'match_type': s['match_type'],
                    'score': round(s['score'], 2)
                }
                for s in similar
            ],
            'suggested_pattern': suggested_pattern,
            'suggested_match_type': suggested_match_type
        })

    @action(detail=True, methods=['get'])
    def suggested_bills(self, request, pk=None):
        """
        Get bills suggested for linking to this transaction.
        GET /api/banking/transactions/{id}/suggested_bills/
        """
        transaction = self.get_object()

        # Check if already linked
        if hasattr(transaction, 'linked_bill') and transaction.linked_bill:
            return Response(
                {'error': 'Transaction is already linked to a bill'},
                status=status.HTTP_400_BAD_REQUEST
            )

        match_service = TransactionMatchService()
        suggestions = match_service.get_suggested_bills_for_transaction(transaction)

        # Serialize with relevance score
        result = []
        for suggestion in suggestions:
            bill = suggestion['bill']
            bill.relevance_score = suggestion['relevance_score']
            result.append(BillSuggestionSerializer(bill).data)

        return Response(result)

    @action(detail=True, methods=['post'])
    def link_bill(self, request, pk=None):
        """
        Link a bill to this transaction.
        POST /api/banking/transactions/{id}/link_bill/
        Body: { "bill_id": "uuid" }
        """
        transaction = self.get_object()

        serializer = LinkBillSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        bill_id = serializer.validated_data['bill_id']
        bill = Bill.objects.get(id=bill_id)

        match_service = TransactionMatchService()

        try:
            updated_bill = match_service.link_transaction_to_bill(transaction, bill)
            # Return updated transaction with linked bill info
            transaction.refresh_from_db()
            return Response(TransactionSerializer(transaction, context={'request': request}).data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

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
        # Only return parent categories (subcategories come nested)
        queryset = Category.objects.filter(
            user=self.request.user,
            parent=None
        ).prefetch_related('subcategories')

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
        bill = serializer.save(user=self.request.user)

        # Log bill creation
        UserActivityLog.log_event(
            user=self.request.user,
            event_type='bill_created',
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            bill_id=str(bill.id),
            bill_type=bill.type,
            amount=float(bill.amount),
            description=bill.description[:100] if bill.description else ''
        )

    def perform_update(self, serializer):
        """Log bill update."""
        bill = serializer.save()

        # Log bill update
        UserActivityLog.log_event(
            user=self.request.user,
            event_type='bill_updated',
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            bill_id=str(bill.id),
            bill_type=bill.type,
            status=bill.status
        )

    def perform_destroy(self, instance):
        """Log bill deletion."""
        bill_id = str(instance.id)
        bill_type = instance.type
        description = instance.description[:100] if instance.description else ''

        instance.delete()

        # Log bill deletion
        UserActivityLog.log_event(
            user=self.request.user,
            event_type='bill_deleted',
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            bill_id=bill_id,
            bill_type=bill_type,
            description=description
        )

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

        # Log payment registration
        UserActivityLog.log_event(
            user=request.user,
            event_type='bill_payment_registered',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            bill_id=str(bill.id),
            bill_type=bill.type,
            payment_amount=float(payment_amount),
            total_paid=float(bill.amount_paid),
            new_status=bill.status
        )

        return Response(BillSerializer(bill).data)

    @action(detail=True, methods=['post'])
    def link_transaction(self, request, pk=None):
        """
        Link a transaction to this bill.
        POST /api/banking/bills/{id}/link_transaction/
        Body: { "transaction_id": "uuid" }
        """
        bill = self.get_object()

        serializer = LinkTransactionSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        transaction_id = serializer.validated_data['transaction_id']
        transaction = Transaction.objects.get(id=transaction_id)

        match_service = TransactionMatchService()

        try:
            updated_bill = match_service.link_transaction_to_bill(transaction, bill)

            # Log transaction link
            UserActivityLog.log_event(
                user=request.user,
                event_type='bill_transaction_linked',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                bill_id=str(bill.id),
                transaction_id=str(transaction_id),
                bill_type=bill.type
            )

            return Response(BillSerializer(updated_bill).data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def unlink_transaction(self, request, pk=None):
        """
        Remove link between transaction and bill.
        POST /api/banking/bills/{id}/unlink_transaction/
        """
        bill = self.get_object()
        transaction_id = str(bill.linked_transaction_id) if bill.linked_transaction else None

        match_service = TransactionMatchService()

        try:
            updated_bill = match_service.unlink_transaction_from_bill(bill)

            # Log transaction unlink
            UserActivityLog.log_event(
                user=request.user,
                event_type='bill_transaction_unlinked',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                bill_id=str(bill.id),
                transaction_id=transaction_id,
                bill_type=bill.type
            )

            return Response(BillSerializer(updated_bill).data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def suggested_transactions(self, request, pk=None):
        """
        Get transactions suggested for linking to this bill.
        GET /api/banking/bills/{id}/suggested_transactions/
        """
        bill = self.get_object()

        # Check if bill is eligible
        if bill.status != 'pending':
            return Response(
                {'error': 'Bill must be pending to link transactions'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if bill.amount_paid > 0:
            return Response(
                {'error': 'Bill already has prior payments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if bill.linked_transaction:
            return Response(
                {'error': 'Bill is already linked to a transaction'},
                status=status.HTTP_400_BAD_REQUEST
            )

        match_service = TransactionMatchService()
        suggestions = match_service.get_suggested_transactions_for_bill(bill)

        # Serialize with relevance score
        result = []
        for suggestion in suggestions:
            tx = suggestion['transaction']
            tx.relevance_score = suggestion['relevance_score']
            result.append(TransactionSuggestionSerializer(tx).data)

        return Response(result)

    # ============================================================
    # ENDPOINTS PARA PAGAMENTOS PARCIAIS (BillPayment)
    # ============================================================

    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        """
        Lista todos os pagamentos de uma bill.
        GET /api/banking/bills/{id}/payments/
        """
        bill = self.get_object()
        payments = bill.payments.select_related('transaction', 'transaction__account').all()
        serializer = BillPaymentSerializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_payment(self, request, pk=None):
        """
        Adiciona um pagamento a uma bill (manual ou com transação).
        POST /api/banking/bills/{id}/add_payment/
        Body: { "amount": 1000.00, "transaction_id": "uuid" (opcional), "notes": "..." }
        """
        from .models import BillPayment

        bill = self.get_object()

        if not bill.can_add_payment:
            return Response(
                {'error': f'Conta não pode receber pagamentos. Status: {bill.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BillPaymentCreateSerializer(
            data=request.data,
            context={'request': request, 'bill': bill}
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        transaction_id = data.get('transaction_id')

        if transaction_id:
            # Vincular transação como pagamento
            transaction = Transaction.objects.get(id=transaction_id)
            match_service = TransactionMatchService()

            try:
                payment = match_service.link_transaction_as_partial_payment(
                    transaction=transaction,
                    bill=bill,
                    notes=data.get('notes', '')
                )
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Pagamento manual (sem transação)
            payment = BillPayment.objects.create(
                bill=bill,
                amount=data['amount'],
                payment_date=timezone.now(),
                notes=data.get('notes', '')
            )
            # recalculate_payments é chamado automaticamente no save()

        # Log activity
        UserActivityLog.log_event(
            user=request.user,
            event_type='bill_payment_added',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            bill_id=str(bill.id),
            payment_id=str(payment.id),
            amount=float(data['amount']),
            has_transaction=bool(transaction_id)
        )

        bill.refresh_from_db()
        return Response(BillSerializer(bill).data)

    @action(detail=True, methods=['delete'], url_path='payments/(?P<payment_id>[^/.]+)')
    def remove_payment(self, request, pk=None, payment_id=None):
        """
        Remove um pagamento de uma bill.
        DELETE /api/banking/bills/{id}/payments/{payment_id}/
        """
        from .models import BillPayment

        bill = self.get_object()

        try:
            payment = bill.payments.get(id=payment_id)
        except BillPayment.DoesNotExist:
            return Response(
                {'error': 'Pagamento não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        match_service = TransactionMatchService()
        updated_bill = match_service.unlink_payment(payment)

        # Log activity
        UserActivityLog.log_event(
            user=request.user,
            event_type='bill_payment_removed',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            bill_id=str(bill.id),
            payment_id=str(payment_id)
        )

        return Response(BillSerializer(updated_bill).data)

    @action(detail=True, methods=['get'])
    def suggested_transactions_partial(self, request, pk=None):
        """
        Retorna transações sugeridas para pagamento parcial.
        GET /api/banking/bills/{id}/suggested_transactions_partial/

        Retorna transações com valor <= valor restante.
        """
        bill = self.get_object()

        if not bill.can_add_payment:
            return Response(
                {'error': 'Conta não pode receber mais pagamentos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        match_service = TransactionMatchService()
        suggestions = match_service.get_suggested_transactions_for_partial(bill)

        result = []
        for suggestion in suggestions:
            tx = suggestion['transaction']
            tx.relevance_score = suggestion['relevance_score']
            tx.would_complete_bill = suggestion['would_complete_bill']
            serializer = PartialPaymentTransactionSerializer(
                tx,
                context={'request': request, 'bill': bill}
            )
            result.append(serializer.data)

        return Response({
            'remaining_amount': str(bill.amount_remaining),
            'transactions': result
        })

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

    @action(detail=False, methods=['post'])
    def upload_boleto(self, request):
        """
        Upload a boleto file (PDF or image) and extract data using OCR.
        POST /api/banking/bills/upload_boleto/

        Returns extracted data for user review before creating a bill.
        """
        from .ocr_service import get_ocr_service, OCRResult
        import logging

        logger = logging.getLogger(__name__)

        # Validate file upload
        serializer = BillUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data['file']
        logger.info(f"Processing boleto upload: {uploaded_file.name} ({uploaded_file.size} bytes)")

        try:
            # Process file with OCR
            ocr_service = get_ocr_service()
            result = ocr_service.process_file(uploaded_file)

            if not result.success:
                logger.warning(f"OCR processing failed: {result.error}")
                return Response({
                    'success': False,
                    'error': result.error or 'Falha ao processar arquivo',
                    'needs_review': True,
                    'barcode': '',
                    'amount': None,
                    'due_date': None,
                    'beneficiary': '',
                    'confidence': 0,
                }, status=status.HTTP_200_OK)  # Return 200 so frontend can handle gracefully

            # Build response with extracted data
            response_data = {
                'success': True,
                'barcode': result.barcode,
                'amount': str(result.amount) if result.amount else None,
                'due_date': result.due_date.strftime('%Y-%m-%d') if result.due_date else None,
                'beneficiary': result.beneficiary,
                'confidence': result.confidence,
                'needs_review': result.needs_review,
                'extracted_fields': result.extracted_fields,
                'error': '',
            }

            logger.info(f"OCR success: confidence={result.confidence}, barcode_found={bool(result.barcode)}")

            return Response(response_data, status=status.HTTP_200_OK)

        except ImportError as e:
            logger.error(f"OCR dependency missing: {e}")
            return Response({
                'success': False,
                'error': 'Serviço de OCR não disponível. Verifique as dependências.',
                'needs_review': True,
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except Exception as e:
            logger.exception(f"Unexpected error during OCR processing: {e}")
            return Response({
                'success': False,
                'error': f'Erro ao processar arquivo: {str(e)}',
                'needs_review': True,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def create_from_ocr(self, request):
        """
        Create a bill from OCR results after user review.
        POST /api/banking/bills/create_from_ocr/

        Body: {
            "type": "payable",
            "description": "...",
            "amount": 100.00,
            "due_date": "2025-01-15",
            "customer_supplier": "...",
            "barcode": "...",
            "ocr_confidence": 85.5,
            "ocr_raw_data": {...}
        }
        """
        serializer = BillFromOCRSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        bill = serializer.save()

        return Response(
            BillSerializer(bill).data,
            status=status.HTTP_201_CREATED
        )


class CategoryRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing category rules.

    GET    /api/banking/category-rules/          List all rules
    POST   /api/banking/category-rules/          Create a new rule
    GET    /api/banking/category-rules/{id}/     Get rule details
    PATCH  /api/banking/category-rules/{id}/     Update rule (toggle active, etc)
    DELETE /api/banking/category-rules/{id}/     Delete rule
    """
    serializer_class = CategoryRuleSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return CategoryRule.objects.filter(
            user=self.request.user
        ).select_related('category').order_by('-created_at')

    def perform_create(self, serializer):
        """Create rule with current user."""
        # Normalize pattern before saving
        pattern = serializer.validated_data.get('pattern', '')
        normalized = CategoryRuleService.normalize_text(pattern)
        serializer.save(user=self.request.user, pattern=normalized)

    def create(self, request, *args, **kwargs):
        """
        Create a new category rule.
        POST /api/banking/category-rules/

        Body: {
            "pattern": "UBER",
            "match_type": "contains",
            "category": "uuid"
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check if rule already exists
        pattern = CategoryRuleService.normalize_text(request.data.get('pattern', ''))
        match_type = request.data.get('match_type', 'prefix')

        existing = CategoryRule.objects.filter(
            user=request.user,
            pattern=pattern,
            match_type=match_type
        ).first()

        if existing:
            # Update existing rule instead of creating duplicate
            existing.category_id = request.data.get('category')
            existing.is_active = True
            existing.save(update_fields=['category', 'is_active', 'updated_at'])
            return Response(
                CategoryRuleSerializer(existing).data,
                status=status.HTTP_200_OK
            )

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """
        Update a category rule (typically toggle is_active).
        PATCH /api/banking/category-rules/{id}/

        Body: { "is_active": false } or { "category": "uuid" }
        """
        instance = self.get_object()

        # Only allow updating specific fields
        allowed_fields = {'is_active', 'category', 'pattern', 'match_type'}
        request_fields = set(request.data.keys())

        if not request_fields.issubset(allowed_fields):
            return Response(
                {'error': 'Only is_active, category, pattern, and match_type can be updated'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Normalize pattern if updating
        if 'pattern' in request.data:
            request.data['pattern'] = CategoryRuleService.normalize_text(request.data['pattern'])

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get statistics about category rules.
        GET /api/banking/category-rules/stats/
        """
        rules = self.get_queryset()

        total = rules.count()
        active = rules.filter(is_active=True).count()
        total_applied = sum(r.applied_count for r in rules)

        return Response({
            'total_rules': total,
            'active_rules': active,
            'inactive_rules': total - active,
            'total_times_applied': total_applied
        })