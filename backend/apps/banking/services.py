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

    def sync_connectors(self, country: str = 'BR', sandbox: Optional[bool] = None) -> int:
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

    def create_connection_from_item(self, user: User, item_id: str) -> BankConnection:
        """
        Create a connection from an existing Pluggy item (after widget auth).
        Ref: https://docs.pluggy.ai/docs/connect-widget-overview
        """
        logger.info(f"Creating connection from item {item_id} for user {user.id}")

        try:
            # Check if connection already exists
            existing = BankConnection.objects.filter(
                pluggy_item_id=item_id,
                user=user
            ).first()

            if existing:
                logger.info(f"Connection already exists for item {item_id}")
                return existing

            logger.info(f"Fetching item details from Pluggy for item {item_id}")
            # Get item details from Pluggy
            pluggy_item = self.client.get_item(item_id)
            logger.info(f"Pluggy item retrieved: {pluggy_item}")

            # Get connector
            connector = Connector.objects.filter(
                pluggy_id=pluggy_item['connector']['id']
            ).first()

            if not connector:
                # Try to sync connectors and get again
                connector_service = ConnectorService()
                connector_service.sync_connectors()
                connector = Connector.objects.filter(
                    pluggy_id=pluggy_item['connector']['id']
                ).first()

            if not connector:
                raise ValueError(f"Connector {pluggy_item['connector']['id']} not found")

            # Create local connection record
            connection = BankConnection.objects.create(
                user=user,
                connector=connector,
                pluggy_item_id=item_id,
                status=pluggy_item['status'],
                status_detail=pluggy_item.get('statusDetail'),
                execution_status=pluggy_item.get('executionStatus', ''),
                last_updated_at=timezone.now()
            )

            # If connection is ready, sync accounts
            if connection.status == 'UPDATED':
                self.sync_accounts(connection)

            logger.info(f"Created bank connection {connection.id} from item {item_id}")
            return connection

        except Exception as e:
            logger.error(f"Failed to create connection from item: {e}")
            raise

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

    def trigger_manual_sync(self, connection: BankConnection) -> Dict:
        """
        Trigger a manual synchronization for a connection.
        This updates the item in Pluggy to fetch new data from the financial institution.

        Returns:
            Dict with sync status and any required actions
        """
        try:
            logger.info(f"Triggering manual sync for connection {connection.id}")

            # First, check current item status
            current_item = self.client.get_item(connection.pluggy_item_id)
            current_status = current_item['status']

            logger.info(f"Current item status: {current_status}")

            # Handle different status scenarios
            if current_status == 'WAITING_USER_INPUT':
                # MFA is required
                parameter = current_item.get('parameter', {})
                logger.warning(f"Item requires MFA. Parameter: {parameter}")
                return {
                    'status': 'MFA_REQUIRED',
                    'message': 'Multi-factor authentication required',
                    'parameter': parameter,
                    'item_status': current_status
                }

            elif current_status == 'LOGIN_ERROR':
                # Credentials are invalid
                logger.warning(f"Item has login error. Need to update credentials.")
                return {
                    'status': 'CREDENTIALS_REQUIRED',
                    'message': 'Invalid credentials, please reconnect',
                    'item_status': current_status
                }

            elif current_status in ['UPDATED', 'OUTDATED']:
                # Item can be updated - trigger sync
                logger.info(f"Triggering item update for sync")
                updated_item = self.client.trigger_item_update(connection.pluggy_item_id)

                # Update local status
                connection.status = updated_item['status']
                connection.status_detail = updated_item.get('statusDetail')
                connection.execution_status = updated_item.get('executionStatus', '')
                connection.last_updated_at = timezone.now()
                connection.save()

                return {
                    'status': 'SYNC_TRIGGERED',
                    'message': 'Synchronization started successfully',
                    'item_status': updated_item['status']
                }

            elif current_status == 'UPDATING':
                # Already updating
                logger.info(f"Item is already updating")
                return {
                    'status': 'ALREADY_SYNCING',
                    'message': 'Synchronization already in progress',
                    'item_status': current_status
                }

            else:
                # Unknown status
                logger.warning(f"Unknown item status: {current_status}")
                return {
                    'status': 'UNKNOWN',
                    'message': f'Unknown item status: {current_status}',
                    'item_status': current_status
                }

        except Exception as e:
            logger.error(f"Failed to trigger manual sync: {e}")
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
                        'bank_data': pluggy_account.get('bankData') or {},  # Ensure never None
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
        Delete a bank connection and all associated data.
        Ref: https://docs.pluggy.ai/reference/items-delete
        """
        try:
            # Delete from Pluggy first
            try:
                self.client.delete_item(connection.pluggy_item_id)
            except Exception as pluggy_error:
                logger.warning(f"Failed to delete from Pluggy: {pluggy_error}")
                # Continue with local deletion even if Pluggy deletion fails

            # Store connection ID for logging
            connection_id = connection.id

            # Delete from database (will cascade delete accounts and transactions)
            connection.delete()

            logger.info(f"Deleted connection {connection_id} and all associated data")
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
                         days_back: int = 365,
                         trigger_update: bool = True) -> int:
        """
        Sync transactions for an account.
        By default, triggers an item update first to get fresh data.
        Ref: https://docs.pluggy.ai/reference/transactions-list

        Args:
            account: The bank account to sync
            days_back: How many days of transactions to sync
            trigger_update: Whether to trigger item update before syncing (default: True)
        """
        sync_log = SyncLog.objects.create(
            connection=account.connection,
            sync_type='TRANSACTIONS',
            status='IN_PROGRESS',
            details={'account_id': str(account.id)}
        )

        try:
            # Trigger item update for manual syncs to get fresh data
            if trigger_update:
                logger.info(f"Triggering item update before syncing transactions for account {account.id}")
                connection_service = BankConnectionService()
                sync_status = connection_service.trigger_manual_sync(account.connection)

                if sync_status['status'] == 'MFA_REQUIRED':
                    sync_log.status = 'FAILED'
                    sync_log.error_message = 'MFA required for sync'
                    sync_log.completed_at = timezone.now()
                    sync_log.save()
                    raise ValueError('MFA required. Please complete authentication through the app.')

                elif sync_status['status'] == 'CREDENTIALS_REQUIRED':
                    sync_log.status = 'FAILED'
                    sync_log.error_message = 'Invalid credentials'
                    sync_log.completed_at = timezone.now()
                    sync_log.save()
                    raise ValueError('Invalid credentials. Please reconnect your account.')

                elif sync_status['status'] not in ['SYNC_TRIGGERED', 'ALREADY_SYNCING']:
                    logger.warning(f"Unexpected sync status: {sync_status}")

                # Wait a moment for the update to start processing
                import time
                time.sleep(2)

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

                    # Get merchant info safely - ensure we never pass None
                    merchant = pluggy_tx.get('merchant') or {}
                    merchant_name = merchant.get('name', '') if merchant else ''
                    merchant_category = merchant.get('category', '') if merchant else ''

                    # Ensure merchant fields are never None
                    merchant_name = merchant_name if merchant_name is not None else ''
                    merchant_category = merchant_category if merchant_category is not None else ''

                    # Ensure all string fields are never None
                    description = pluggy_tx.get('description', '')
                    description = description if description is not None else ''

                    category = pluggy_tx.get('category', '')
                    category = category if category is not None else ''

                    category_id = pluggy_tx.get('categoryId', '')
                    category_id = category_id if category_id is not None else ''

                    TransactionModel.objects.update_or_create(
                        pluggy_transaction_id=pluggy_tx['id'],
                        defaults={
                            'account': account,
                            'type': tx_type,
                            'description': description,
                            'amount': abs(Decimal(str(pluggy_tx.get('amount', 0)))),
                            'currency_code': pluggy_tx.get('currencyCode', 'BRL'),
                            'date': datetime.fromisoformat(pluggy_tx['date'].replace('Z', '+00:00')),
                            'category': category,
                            'category_id': category_id,
                            'merchant_name': merchant_name,
                            'merchant_category': merchant_category,
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

    def sync_all_accounts_transactions(self, connection: BankConnection,
                                      trigger_update: bool = True) -> Dict[str, int]:
        """
        Sync transactions for all accounts in a connection.

        Args:
            connection: The bank connection
            trigger_update: Whether to trigger item update before syncing (default: True)
        """
        results = {}

        # Only trigger update once for the connection, not for each account
        if trigger_update:
            logger.info(f"Triggering item update for connection {connection.id}")
            connection_service = BankConnectionService()
            sync_status = connection_service.trigger_manual_sync(connection)

            if sync_status['status'] == 'MFA_REQUIRED':
                raise ValueError('MFA required. Please complete authentication through the app.')
            elif sync_status['status'] == 'CREDENTIALS_REQUIRED':
                raise ValueError('Invalid credentials. Please reconnect your account.')

            # Wait for update to process
            import time
            time.sleep(3)

        for account in connection.accounts.filter(is_active=True):
            try:
                # Don't trigger update again since we did it for the connection
                count = self.sync_transactions(account, trigger_update=False)
                results[str(account.id)] = count
            except Exception as e:
                logger.error(f"Failed to sync transactions for account {account.id}: {e}")
                results[str(account.id)] = 0

        return results
