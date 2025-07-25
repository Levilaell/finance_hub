"""
Webhook handler for Pluggy events with proper sync/async handling
"""
import logging
from typing import Dict, Any
from django.db import transaction
from asgiref.sync import sync_to_async

from .models import BankAccount
from .integrations.pluggy.sync_service import PluggyTransactionSyncService

logger = logging.getLogger(__name__)


class PluggyWebhookHandler:
    """Handle Pluggy webhook events with proper async context"""
    
    def __init__(self):
        self.sync_service = PluggyTransactionSyncService()
    
    async def process_event(self, event_type: str, event_data: dict) -> dict:
        """
        Process webhook events with proper async handling
        
        Args:
            event_type: Type of webhook event
            event_data: Event payload data
            
        Returns:
            dict: Processing result
        """
        result = {'success': True, 'message': ''}
        
        try:
            if event_type == 'item/created':
                result = await self._handle_item_created(event_data)
                
            elif event_type == 'item/updated':
                result = await self._handle_item_updated(event_data)
                
            elif event_type == 'item/error':
                result = await self._handle_item_error(event_data)
                
            elif event_type == 'transactions/created':
                result = await self._handle_transactions_created(event_data)
                
            elif event_type == 'item/waiting_user_action':
                result = await self._handle_item_waiting_user_action(event_data)
                
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                result['message'] = f'Event {event_type} received but not processed'
                
        except Exception as e:
            logger.error(f"Error processing webhook event {event_type}: {e}", exc_info=True)
            result['success'] = False
            result['message'] = str(e)
            
        return result
    
    async def _handle_item_created(self, event_data: dict) -> dict:
        """Handle item created event"""
        item_id = event_data.get('id')
        logger.info(f"Pluggy item created: {item_id}")
        return {'success': True, 'message': f'Item {item_id} created successfully'}
    
    async def _handle_item_updated(self, event_data: dict) -> dict:
        """Handle item updated event"""
        item_id = event_data.get('id')
        status_val = event_data.get('status')
        logger.info(f"Pluggy item {item_id} updated: {status_val}")
        
        # Handle different status updates
        if status_val == 'ACTIVE':
            # Use sync_to_async for database queries
            accounts = await sync_to_async(
                lambda: list(BankAccount.objects.filter(
                    pluggy_item_id=item_id,
                    is_active=True
                ))
            )()
            
            if accounts:
                for account in accounts:
                    try:
                        await self.sync_service.sync_account_transactions(account)
                        logger.info(f"Synced account {account.id} after item update")
                    except Exception as e:
                        logger.error(f"Failed to sync account {account.id}: {e}")
                        
        elif status_val == 'WAITING_USER_ACTION':
            # Update account status to reflect authentication needed
            await sync_to_async(
                BankAccount.objects.filter(
                    pluggy_item_id=item_id
                ).update
            )(
                sync_status='waiting_user_action',
                sync_error_message='Reautenticação necessária'
            )
            logger.warning(f"Item {item_id} requires user action for reauthentication")
            
        elif status_val == 'LOGIN_ERROR':
            # Update account status for login errors
            await sync_to_async(
                BankAccount.objects.filter(
                    pluggy_item_id=item_id
                ).update
            )(
                sync_status='login_error',
                sync_error_message='Credenciais inválidas'
            )
            logger.error(f"Item {item_id} has login error")
                        
        return {'success': True, 'message': f'Item {item_id} updated to {status_val}'}
    
    async def _handle_item_error(self, event_data: dict) -> dict:
        """Handle item error event"""
        item_id = event_data.get('id')
        error = event_data.get('error', {})
        logger.warning(f"Pluggy item {item_id} error: {error}")
        
        # Mark accounts as having errors
        await sync_to_async(
            BankAccount.objects.filter(
                pluggy_item_id=item_id
            ).update
        )(
            sync_status='error',
            sync_error_message=error.get('message', 'Unknown error')
        )
        
        return {'success': True, 'message': f'Item {item_id} error recorded'}
    
    async def _handle_transactions_created(self, event_data: dict) -> dict:
        """Handle transactions created event"""
        # Try different possible locations for accountId
        account_id = event_data.get('accountId') or event_data.get('account_id')
        
        # If not in event_data, it might be an item_id
        item_id = event_data.get('itemId') or event_data.get('item_id') or event_data.get('id')
        
        if not account_id and not item_id:
            logger.error(f"No accountId or itemId in webhook data: {event_data}")
            return {'success': False, 'message': 'No accountId or itemId provided'}
        
        # Find accounts to sync
        accounts_to_sync = []
        
        try:
            if account_id:
                logger.info(f"New transactions for Pluggy account {account_id}")
                # Find by external_id (account ID)
                account = await sync_to_async(
                    BankAccount.objects.get
                )(
                    external_id=account_id,
                    is_active=True
                )
                accounts_to_sync = [account]
            elif item_id:
                logger.info(f"New transactions for Pluggy item {item_id}")
                # Find all accounts for this item
                accounts = await sync_to_async(
                    lambda: list(BankAccount.objects.filter(
                        pluggy_item_id=item_id,
                        is_active=True
                    ))
                )()
                accounts_to_sync = accounts
            
            if not accounts_to_sync:
                logger.warning(f"No active accounts found for webhook data: {event_data}")
                return {'success': False, 'message': 'No active accounts found'}
            
            # Sync all related accounts
            sync_results = []
            for account in accounts_to_sync:
                try:
                    await self.sync_service.sync_account_transactions(account)
                    sync_results.append(f"Account {account.id}: success")
                    logger.info(f"✅ Synced transactions for account {account.id}")
                except Exception as e:
                    sync_results.append(f"Account {account.id}: failed - {str(e)}")
                    logger.error(f"❌ Failed to sync account {account.id}: {e}")
            
            return {
                'success': True, 
                'message': f'Processed {len(accounts_to_sync)} accounts',
                'details': sync_results
            }
            
        except BankAccount.DoesNotExist:
            logger.warning(f"Account not found for webhook data: {event_data}")
            return {'success': False, 'message': 'Account not found'}
        except Exception as e:
            logger.error(f"Error processing transactions webhook: {e}", exc_info=True)
            return {'success': False, 'message': str(e)}
    
    async def _handle_item_waiting_user_action(self, event_data: dict) -> dict:
        """Handle item waiting for user action event"""
        item_id = event_data.get('id')
        logger.warning(f"Pluggy item {item_id} requires user action")
        
        # Update all accounts with this item to reflect authentication needed
        await sync_to_async(
            BankAccount.objects.filter(
                pluggy_item_id=item_id
            ).update
        )(
            sync_status='waiting_user_action',
            sync_error_message='Reautenticação necessária - faça login novamente no banco'
        )
        
        # TODO: Send notification to user about reauth needed
        logger.info(f"Updated accounts for item {item_id} to waiting_user_action status")
        
        return {'success': True, 'message': f'Item {item_id} requires user reauthentication'}