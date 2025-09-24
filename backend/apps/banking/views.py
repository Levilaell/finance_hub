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
from django.db.models import Sum, Count

from .models import (
    Connector, BankConnection, BankAccount,
    Transaction, SyncLog
)
from .serializers import (
    ConnectorSerializer, BankConnectionSerializer,
    BankAccountSerializer, TransactionSerializer,
    CreateConnectionSerializer, TransactionFilterSerializer,
    SyncStatusSerializer, ConnectTokenSerializer,
    SummarySerializer
)
from .services import (
    ConnectorService, BankConnectionService,
    TransactionService
)
from .pluggy_client import PluggyClient


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
        serializer = CreateConnectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = BankConnectionService()
        try:
            connection = service.create_connection(
                user=request.user,
                connector_id=serializer.validated_data['connector_id'],
                credentials=serializer.validated_data['credentials']
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

    def destroy(self, request, pk=None):
        """
        Delete (disconnect) a bank connection.
        DELETE /api/banking/connections/{id}/
        """
        connection = self.get_object()
        service = BankConnectionService()

        if service.delete_connection(connection):
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

        try:
            count = service.sync_accounts(connection)
            return Response({
                'message': f'Synced {count} accounts',
                'count': count
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def sync_transactions(self, request, pk=None):
        """
        Sync all transactions for this connection.
        POST /api/banking/connections/{id}/sync_transactions/
        """
        connection = self.get_object()
        service = TransactionService()

        try:
            results = service.sync_all_accounts_transactions(connection)
            total = sum(results.values())
            return Response({
                'message': f'Synced {total} transactions',
                'results': results,
                'total': total
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def connect_token(self, request):
        """
        Get a connect token for Pluggy widget.
        GET /api/banking/connections/connect_token/
        """
        client = PluggyClient()
        try:
            token = client._get_connect_token()
            expires_at = timezone.now() + timedelta(minutes=30)
            return Response({
                'token': token,
                'expires_at': expires_at
            })
        except Exception as e:
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
        return BankAccount.objects.filter(
            connection__user=self.request.user,
            connection__is_active=True,
            is_active=True
        ).select_related('connection__connector')

    @action(detail=True, methods=['post'])
    def sync_transactions(self, request, pk=None):
        """
        Sync transactions for a specific account.
        POST /api/banking/accounts/{id}/sync_transactions/
        """
        account = self.get_object()
        service = TransactionService()
        days_back = int(request.data.get('days_back', 90))

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


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing transactions.
    Ref: https://docs.pluggy.ai/reference/transactions
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['account', 'type', 'category']

    def get_queryset(self):
        queryset = Transaction.objects.filter(
            account__connection__user=self.request.user,
            account__connection__is_active=True
        ).select_related('account')

        # Apply filters
        filter_serializer = TransactionFilterSerializer(data=self.request.query_params)
        if filter_serializer.is_valid():
            filters = filter_serializer.validated_data

            if 'account_id' in filters:
                queryset = queryset.filter(account_id=filters['account_id'])
            if 'date_from' in filters:
                queryset = queryset.filter(date__gte=filters['date_from'])
            if 'date_to' in filters:
                queryset = queryset.filter(date__lte=filters['date_to'])
            if 'type' in filters:
                queryset = queryset.filter(type=filters['type'])
            if 'category' in filters:
                queryset = queryset.filter(category__icontains=filters['category'])

        return queryset.order_by('-date', '-created_at')

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get financial summary.
        GET /api/banking/transactions/summary/
        """
        # Default to current month
        now = timezone.now()
        date_from = request.query_params.get(
            'date_from',
            now.replace(day=1).date()
        )
        date_to = request.query_params.get(
            'date_to',
            now.date()
        )

        if isinstance(date_from, str):
            date_from = datetime.fromisoformat(date_from).date()
        if isinstance(date_to, str):
            date_to = datetime.fromisoformat(date_to).date()

        transactions = self.get_queryset().filter(
            date__gte=date_from,
            date__lte=date_to
        )

        income = transactions.filter(type='CREDIT').aggregate(
            total=Sum('amount')
        )['total'] or 0

        expenses = transactions.filter(type='DEBIT').aggregate(
            total=Sum('amount')
        )['total'] or 0

        accounts_count = BankAccount.objects.filter(
            connection__user=request.user,
            connection__is_active=True,
            is_active=True
        ).count()

        return Response({
            'income': income,
            'expenses': expenses,
            'balance': income - expenses,
            'period_start': date_from,
            'period_end': date_to,
            'accounts_count': accounts_count,
            'transactions_count': transactions.count()
        })

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Get transactions grouped by category.
        GET /api/banking/transactions/by_category/
        """
        service = TransactionService()
        now = timezone.now()
        date_from = request.query_params.get(
            'date_from',
            now.replace(day=1)
        )
        date_to = request.query_params.get(
            'date_to',
            now
        )

        if isinstance(date_from, str):
            date_from = datetime.fromisoformat(date_from)
        if isinstance(date_to, str):
            date_to = datetime.fromisoformat(date_to)

        result = service.get_transactions_by_category(
            request.user,
            date_from,
            date_to
        )
        return Response(result)


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