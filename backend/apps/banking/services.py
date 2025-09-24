"""
Banking services for Pluggy integration and data synchronization.
Ref: https://docs.pluggy.ai/docs/creating-an-use-case-from-scratch
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal

from django.db import transaction
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

from .models import (
    Connector, BankConnection, BankAccount,
    Transaction as TransactionModel, SyncLog
)
from .pluggy_client import PluggyClient

User = get_user_model()
logger = logging.getLogger(__name__)


class ConnectorService:
    """
    Service for managing bank connectors.
    Ref: https://docs.pluggy.ai/reference/connectors
    """

    def __init__(self):
        self.client = PluggyClient()

    def sync_connectors(self, country: str = 'BR', sandbox: bool = False) -> int:
        """
        Sync available connectors from Pluggy.
        Returns the number of connectors synced.
        """
        sync_log = SyncLog.objects.create(
            sync_type='CONNECTORS',
            status='IN_PROGRESS'
        )

        try:
            pluggy_connectors = self.client.get_connectors(country=country, sandbox=sandbox)
            synced_count = 0

            for pluggy_connector in pluggy_connectors:
                connector, created = Connector.objects.update_or_create(
                    pluggy_id=pluggy_connector['id'],
                    defaults={
                        'name': pluggy_connector['name'],
                        'institution_name': pluggy_connector.get('institutionName', ''),
                        'institution_url': pluggy_connector.get('institutionUrl', ''),
                        'country': pluggy_connector.get('countries', ['BR'])[0],
                        'primary_color': pluggy_connector.get('primaryColor', ''),
                        'logo_url': pluggy_connector.get('logoUrl', ''),
                        'type': pluggy_connector.get('type', 'PERSONAL_BANK'),
                        'credentials_schema': pluggy_connector.get('credentials', {}),
                        'supports_mfa': pluggy_connector.get('hasMfa', False),
                        'is_sandbox': pluggy_connector.get('isSandbox', False),
                        'is_active': pluggy_connector.get('isEnabled', True),
                    }
                )
                synced_count += 1

            sync_log.status = 'SUCCESS'
            sync_log.completed_at = timezone.now()
            sync_log.records_synced = synced_count
            sync_log.save()

            logger.info(f"Synced {synced_count} connectors")
            return synced_count

        except Exception as e:
            sync_log.status = 'FAILED'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            logger.error(f"Failed to sync connectors: {e}")
            raise

    def get_active_connectors(self, country: str = 'BR') -> List[Connector]:
        """Get all active connectors for a country."""
        return Connector.objects.filter(
            country=country,
            is_active=True
        ).order_by('name')


class BankConnectionService:
    """
    Service for managing bank connections (Items in Pluggy).
    Ref: https://docs.pluggy.ai/docs/connect-an-account
    """

    def __init__(self):
        self.client = PluggyClient()

    def create_connection(self, user: User, connector_id: int,
                         credentials: Dict[str, str]) -> BankConnection:
        """
        Create a new bank connection for a user.
        Ref: https://docs.pluggy.ai/reference/items-create
        """
        try:
            connector = Connector.objects.get(pluggy_id=connector_id)

            # Build webhook URL
            webhook_url = None
            if hasattr(settings, 'WEBHOOK_BASE_URL'):
                webhook_url = f"{settings.WEBHOOK_BASE_URL}/api/banking/webhooks/pluggy/"

            # Create item in Pluggy
            pluggy_item = self.client.create_item(
                connector_id=connector_id,
                credentials=credentials,
                webhook_url=webhook_url,
                user_data={'id': str(user.id), 'email': user.email}
            )

            # Create local connection record
            connection = BankConnection.objects.create(
                user=user,
                connector=connector,
                pluggy_item_id=pluggy_item['id'],
                status='UPDATING',
                webhook_url=webhook_url or ''
            )

            logger.info(f"Created bank connection {connection.id} for user {user.id}")
            return connection

        except Connector.DoesNotExist:
            logger.error(f"Connector {connector_id} not found")
            raise ValueError(f"Connector {connector_id} not found")
        except Exception as e:
            logger.error(f"Failed to create bank connection: {e}")
            raise

    def update_connection_status(self, connection: BankConnection) -> BankConnection:
        """
        Update connection status from Pluggy.
        Ref: https://docs.pluggy.ai/reference/items-retrieve
        """
        try:
            pluggy_item = self.client.get_item(connection.pluggy_item_id)

            connection.status = pluggy_item['status']
            connection.status_detail = pluggy_item.get('statusDetail')
            connection.execution_status = pluggy_item.get('executionStatus', '')
            connection.last_updated_at = timezone.now()
            connection.save()

            # If connection is ready, sync accounts
            if connection.status == 'UPDATED':
                self.sync_accounts(connection)

            return connection

        except Exception as e:
            logger.error(f"Failed to update connection status: {e}")
            raise

    def sync_accounts(self, connection: BankConnection) -> int:
        """
        Sync accounts for a connection.
        Ref: https://docs.pluggy.ai/reference/accounts-list
        """
        try:
            pluggy_accounts = self.client.get_accounts(connection.pluggy_item_id)
            synced_count = 0

            for pluggy_account in pluggy_accounts:
                account_type = self._map_account_type(pluggy_account.get('type', 'BANK'))

                BankAccount.objects.update_or_create(
                    pluggy_account_id=pluggy_account['id'],
                    defaults={
                        'connection': connection,
                        'type': account_type,
                        'subtype': pluggy_account.get('subtype', ''),
                        'name': pluggy_account.get('name', ''),
                        'number': pluggy_account.get('number', ''),
                        'balance': Decimal(str(pluggy_account.get('balance', 0))),
                        'currency_code': pluggy_account.get('currencyCode', 'BRL'),
                        'bank_data': pluggy_account.get('bankData', {}),
                        'last_synced_at': timezone.now(),
                    }
                )
                synced_count += 1

            logger.info(f"Synced {synced_count} accounts for connection {connection.id}")
            return synced_count

        except Exception as e:
            logger.error(f"Failed to sync accounts: {e}")
            raise

    def delete_connection(self, connection: BankConnection) -> bool:
        """
        Delete a bank connection.
        Ref: https://docs.pluggy.ai/reference/items-delete
        """
        try:
            # Delete from Pluggy
            self.client.delete_item(connection.pluggy_item_id)

            # Mark as inactive (soft delete)
            connection.is_active = False
            connection.save()

            logger.info(f"Deleted connection {connection.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete connection: {e}")
            return False

    def _map_account_type(self, pluggy_type: str) -> str:
        """Map Pluggy account type to our model choices."""
        mapping = {
            'BANK': 'CHECKING',
            'CHECKING': 'CHECKING',
            'SAVINGS': 'SAVINGS',
            'CREDIT_CARD': 'CREDIT_CARD',
            'LOAN': 'LOAN',
            'INVESTMENT': 'INVESTMENT',
        }
        return mapping.get(pluggy_type, 'CHECKING')


class TransactionService:
    """
    Service for managing transactions.
    Ref: https://docs.pluggy.ai/reference/transactions
    """

    def __init__(self):
        self.client = PluggyClient()

    def sync_transactions(self, account: BankAccount,
                         days_back: int = 90) -> int:
        """
        Sync transactions for an account.
        Ref: https://docs.pluggy.ai/reference/transactions-list
        """
        sync_log = SyncLog.objects.create(
            connection=account.connection,
            sync_type='TRANSACTIONS',
            status='IN_PROGRESS',
            details={'account_id': str(account.id)}
        )

        try:
            date_from = timezone.now() - timedelta(days=days_back)
            date_to = timezone.now()

            pluggy_transactions = self.client.get_transactions(
                account_id=account.pluggy_account_id,
                date_from=date_from,
                date_to=date_to
            )

            synced_count = 0
            with transaction.atomic():
                for pluggy_tx in pluggy_transactions:
                    tx_type = 'CREDIT' if pluggy_tx['type'] == 'CREDIT' else 'DEBIT'

                    TransactionModel.objects.update_or_create(
                        pluggy_transaction_id=pluggy_tx['id'],
                        defaults={
                            'account': account,
                            'type': tx_type,
                            'description': pluggy_tx.get('description', ''),
                            'amount': abs(Decimal(str(pluggy_tx.get('amount', 0)))),
                            'currency_code': pluggy_tx.get('currencyCode', 'BRL'),
                            'date': datetime.fromisoformat(pluggy_tx['date']).date(),
                            'category': pluggy_tx.get('category', ''),
                            'category_id': pluggy_tx.get('categoryId', ''),
                            'merchant_name': pluggy_tx.get('merchant', {}).get('name', ''),
                            'merchant_category': pluggy_tx.get('merchant', {}).get('category', ''),
                            'payment_data': pluggy_tx.get('paymentData'),
                        }
                    )
                    synced_count += 1

            account.last_synced_at = timezone.now()
            account.save()

            sync_log.status = 'SUCCESS'
            sync_log.completed_at = timezone.now()
            sync_log.records_synced = synced_count
            sync_log.save()

            logger.info(f"Synced {synced_count} transactions for account {account.id}")
            return synced_count

        except Exception as e:
            sync_log.status = 'FAILED'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            logger.error(f"Failed to sync transactions: {e}")
            raise

    def sync_all_accounts_transactions(self, connection: BankConnection) -> Dict[str, int]:
        """
        Sync transactions for all accounts in a connection.
        """
        results = {}
        for account in connection.accounts.filter(is_active=True):
            try:
                count = self.sync_transactions(account)
                results[str(account.id)] = count
            except Exception as e:
                logger.error(f"Failed to sync transactions for account {account.id}: {e}")
                results[str(account.id)] = 0

        return results

    def get_income_expense_summary(self, user: User,
                                  date_from: datetime,
                                  date_to: datetime) -> Dict[str, Decimal]:
        """
        Calculate income and expense summary for a user.
        """
        transactions = TransactionModel.objects.filter(
            account__connection__user=user,
            account__connection__is_active=True,
            date__gte=date_from,
            date__lte=date_to
        )

        income = transactions.filter(type='CREDIT').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        expenses = transactions.filter(type='DEBIT').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        return {
            'income': income,
            'expenses': expenses,
            'balance': income - expenses
        }

    def get_transactions_by_category(self, user: User,
                                    date_from: datetime,
                                    date_to: datetime) -> Dict[str, Decimal]:
        """
        Get transaction totals grouped by category.
        """
        from django.db.models import Sum

        transactions = TransactionModel.objects.filter(
            account__connection__user=user,
            account__connection__is_active=True,
            date__gte=date_from,
            date__lte=date_to
        ).values('category', 'type').annotate(
            total=Sum('amount')
        )

        result = {}
        for tx in transactions:
            key = f"{tx['category'] or 'Uncategorized'}_{tx['type']}"
            result[key] = tx['total']

        return result