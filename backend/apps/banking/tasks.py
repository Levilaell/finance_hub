"""
Celery tasks for banking app - Webhook processing
"""
import logging
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache

from .models import BankConnection, SyncLog, Transaction
from .services import BankConnectionService, TransactionService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
)
def process_item_updated(self, item_id: str, payload: dict):
    """
    Process item update webhook asynchronously.
    This is triggered when an item's data has been successfully updated.

    Args:
        item_id: Pluggy item ID
        payload: Full webhook payload
    """
    try:
        logger.info(f"[TASK] Processing item_updated for item {item_id}")

        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        service = BankConnectionService()

        # Update connection status
        service.update_connection_status(connection)

        # Sync accounts if status is good
        if connection.status == 'UPDATED':
            service.sync_accounts(connection)

            # Check if transactions are actually ready before syncing
            status_detail = connection.status_detail or {}
            transactions_status = status_detail.get('transactions', {})
            transactions_updated = transactions_status.get('isUpdated', False)

            if transactions_updated:
                # Sync transactions for all accounts
                tx_service = TransactionService()
                # Don't trigger update from webhook since it's already updated
                tx_service.sync_all_accounts_transactions(connection, trigger_update=False)
                logger.info(f"[TASK] Transactions synced for connection {connection.id}")
            else:
                # Transactions not ready yet - will be synced when transactions/created webhook arrives
                execution_status = connection.execution_status
                logger.warning(
                    f"[TASK] Transactions not ready for connection {connection.id}. "
                    f"executionStatus={execution_status}, "
                    f"transactions.isUpdated={transactions_updated}, "
                    f"transactions.lastUpdatedAt={transactions_status.get('lastUpdatedAt')}. "
                    f"Waiting for transactions/created or transactions/updated webhook."
                )

        logger.info(f"[TASK] Successfully processed update for connection {connection.id}")

    except BankConnection.DoesNotExist:
        logger.warning(f"[TASK] Connection not found for item {item_id}")
    except Exception as e:
        logger.error(f"[TASK] Error handling item update: {e}")
        raise  # Celery will retry


@shared_task(bind=True)
def process_item_created(self, item_id: str, payload: dict):
    """
    Process item creation webhook asynchronously.
    """
    try:
        logger.info(f"[TASK] Processing item_created for item {item_id}")

        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        connection.status = 'UPDATING'
        connection.save()

        # Initial sync will happen when status becomes 'UPDATED'
        logger.info(f"[TASK] Item created for connection {connection.id}")

    except BankConnection.DoesNotExist:
        logger.warning(f"[TASK] Connection not found for new item {item_id}")
    except Exception as e:
        logger.error(f"[TASK] Error handling item creation: {e}")


@shared_task(bind=True)
def process_item_error(self, item_id: str, payload: dict):
    """
    Process item error webhook asynchronously.
    """
    try:
        logger.info(f"[TASK] Processing item_error for item {item_id}")

        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        error = payload.get('error', {})

        connection.status = 'ERROR'
        connection.status_detail = {
            'code': error.get('code'),
            'message': error.get('message'),
            'details': error.get('details')
        }
        connection.save()

        # Log sync failure
        SyncLog.objects.create(
            connection=connection,
            sync_type='FULL',
            status='FAILED',
            error_message=error.get('message', 'Unknown error'),
            completed_at=timezone.now()
        )

        logger.error(f"[TASK] Item error for connection {connection.id}: {error}")

    except BankConnection.DoesNotExist:
        logger.warning(f"[TASK] Connection not found for errored item {item_id}")
    except Exception as e:
        logger.error(f"[TASK] Error handling item error: {e}")


@shared_task(bind=True)
def process_item_deleted(self, item_id: str, payload: dict):
    """
    Process item deletion webhook asynchronously.
    """
    try:
        logger.info(f"[TASK] Processing item_deleted for item {item_id}")

        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        connection.is_active = False
        connection.save()

        logger.info(f"[TASK] Item deleted for connection {connection.id}")

    except BankConnection.DoesNotExist:
        logger.warning(f"[TASK] Connection not found for deleted item {item_id}")
    except Exception as e:
        logger.error(f"[TASK] Error handling item deletion: {e}")


@shared_task(bind=True)
def process_item_mfa(self, item_id: str, payload: dict):
    """
    Process MFA required webhook asynchronously.
    """
    try:
        logger.info(f"[TASK] Processing MFA requirement for item {item_id}")

        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        connection.status = 'WAITING_USER_INPUT'
        connection.status_detail = {
            'mfa_required': True,
            'parameter': payload.get('parameter'),
            'message': payload.get('message', 'MFA required')
        }
        connection.save()

        logger.info(f"[TASK] MFA required for connection {connection.id}")

        # TODO: Implement notification to user about MFA requirement
        # This could be done via email, push notification, or in-app notification

    except BankConnection.DoesNotExist:
        logger.warning(f"[TASK] Connection not found for MFA item {item_id}")
    except Exception as e:
        logger.error(f"[TASK] Error handling MFA requirement: {e}")


@shared_task(bind=True)
def process_item_login_succeeded(self, item_id: str, payload: dict):
    """
    Process login succeeded webhook asynchronously.
    """
    try:
        logger.info(f"[TASK] Processing login_succeeded for item {item_id}")

        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        connection.status = 'UPDATING'
        connection.last_updated_at = timezone.now()
        connection.save()

        logger.info(f"[TASK] Login succeeded for connection {connection.id}")

    except BankConnection.DoesNotExist:
        logger.warning(f"[TASK] Connection not found for item {item_id}")
    except Exception as e:
        logger.error(f"[TASK] Error handling login success: {e}")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
)
def process_transactions_created(self, item_id: str, payload: dict):
    """
    Process transactions created webhook asynchronously.
    """
    try:
        logger.info(f"[TASK] Processing transactions_created for item {item_id}")

        connection = BankConnection.objects.get(pluggy_item_id=item_id)

        # First ensure accounts are synced
        service = BankConnectionService()

        # Update connection status first
        service.update_connection_status(connection)

        # Sync accounts if needed
        if connection.accounts.count() == 0:
            logger.info(f"[TASK] No accounts found, syncing accounts for connection {connection.id}")
            service.sync_accounts(connection)

        # Now sync transactions for all accounts
        tx_service = TransactionService()
        # Don't trigger update since transactions are already available
        tx_service.sync_all_accounts_transactions(connection, trigger_update=False)

        logger.info(f"[TASK] Transactions created processed for connection {connection.id}")

    except BankConnection.DoesNotExist:
        logger.warning(f"[TASK] Connection not found for item {item_id}")
    except Exception as e:
        logger.error(f"[TASK] Error handling transactions created: {e}")
        raise  # Celery will retry


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
)
def process_transactions_updated(self, item_id: str, payload: dict):
    """
    Process transactions updated webhook asynchronously.
    """
    try:
        logger.info(f"[TASK] Processing transactions_updated for item {item_id}")

        connection = BankConnection.objects.get(pluggy_item_id=item_id)

        # Update connection status
        service = BankConnectionService()
        service.update_connection_status(connection)

        # Sync accounts first to ensure they exist
        if connection.accounts.count() == 0:
            logger.info(f"[TASK] No accounts found, syncing accounts for connection {connection.id}")
            service.sync_accounts(connection)
        else:
            # Update existing accounts with latest data
            service.sync_accounts(connection)

        # Sync transactions for all accounts
        tx_service = TransactionService()
        # Don't trigger update since transactions are already updated
        tx_service.sync_all_accounts_transactions(connection, trigger_update=False)

        logger.info(f"[TASK] Transactions updated for connection {connection.id}")

    except BankConnection.DoesNotExist:
        logger.warning(f"[TASK] Connection not found for item {item_id}")
    except Exception as e:
        logger.error(f"[TASK] Error handling transactions update: {e}")
        raise  # Celery will retry


@shared_task(bind=True)
def process_transactions_deleted(self, item_id: str, payload: dict):
    """
    Process transactions deleted webhook asynchronously.
    """
    try:
        logger.info(f"[TASK] Processing transactions_deleted for item {item_id}")

        connection = BankConnection.objects.get(pluggy_item_id=item_id)
        transaction_ids = payload.get('transactionIds', [])

        if not transaction_ids:
            logger.warning(f"[TASK] No transaction IDs provided in delete event for item {item_id}")
            return

        # Delete transactions by their Pluggy IDs
        deleted_count = Transaction.objects.filter(
            pluggy_transaction_id__in=transaction_ids,
            account__connection=connection
        ).delete()[0]

        logger.info(
            f"[TASK] Deleted {deleted_count} transactions for connection {connection.id}. "
            f"Transaction IDs: {transaction_ids}"
        )

    except BankConnection.DoesNotExist:
        logger.warning(f"[TASK] Connection not found for item {item_id}")
    except Exception as e:
        logger.error(f"[TASK] Error handling transactions deletion: {e}")


@shared_task(bind=True)
def process_connector_status(self, payload: dict):
    """
    Process connector status update webhook asynchronously.
    """
    connector_id = payload.get('connectorId')
    data = payload.get('data', {})
    status = data.get('status')

    logger.info(f"[TASK] Connector {connector_id} status changed to: {status}")

    # Log connector status for monitoring
    # This can be used to track bank maintenance, outages, etc.
    # Status values: ONLINE, UNSTABLE, OFFLINE

    if status == 'OFFLINE':
        logger.warning(f"[TASK] Connector {connector_id} is OFFLINE - bank may be unavailable")
    elif status == 'UNSTABLE':
        logger.warning(f"[TASK] Connector {connector_id} is UNSTABLE - connection issues may occur")
    else:
        logger.info(f"[TASK] Connector {connector_id} is back {status}")

    # TODO: Optionally notify users about their affected connections
    # For example, if a user has connections using this connector, we could:
    # 1. Update connection status to reflect connector issues
    # 2. Send notification to user about potential sync delays
    # 3. Disable auto-sync until connector is back online
