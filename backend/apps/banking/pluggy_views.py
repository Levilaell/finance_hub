"""
Pluggy views para integração com bancos brasileiros
"""
import logging
from typing import Dict, Any
from decimal import Decimal
import asyncio
import hmac
import hashlib
import json

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from .models import BankAccount, BankProvider
from .pluggy_client import PluggyClient, PluggyAuthenticationError
from .serializers import BankAccountSerializer
from .pluggy_sync_service import PluggyTransactionSyncService

logger = logging.getLogger(__name__)


@method_decorator(ratelimit(key='ip', rate='20/m', method='GET'), name='dispatch')
class PluggyBankProvidersView(APIView):
    """Get available banks from Pluggy"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get list of banks supported by Pluggy"""
        
        try:
            async def get_banks():
                async with PluggyClient() as client:
                    connectors = await client.get_connectors()
                    
                    # Filter and format banks
                    banks = []
                    for connector in connectors:
                        if connector.get('type') == 'PERSONAL_BANK':
                            banks.append({
                                'id': connector['id'],
                                'name': connector['name'],
                                'code': str(connector['id']),
                                'health_status': connector.get('health', {}).get('status', 'ONLINE'),
                                'logo': connector.get('imageUrl'),
                                'primary_color': connector.get('primaryColor', '#000000'),
                                'supports_accounts': connector.get('hasAccounts', True),
                                'supports_transactions': connector.get('hasTransactions', True),
                                'is_sandbox': False  # Em produção/trial, não é sandbox
                            })
                    
                    return banks
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                banks = loop.run_until_complete(get_banks())
            finally:
                loop.close()
            
            # Detecta se está em modo sandbox ou produção
            sandbox_mode = getattr(settings, 'PLUGGY_USE_SANDBOX', False)
            
            return Response({
                'success': True,
                'data': banks,
                'total': len(banks),
                'sandbox_mode': sandbox_mode,
                'message': 'Bancos do sandbox Pluggy' if sandbox_mode else 'Bancos reais Pluggy'
            })
            
        except Exception as e:
            logger.error(f"Error getting Pluggy banks: {e}")
            
            # Em caso de erro, retorna resposta vazia ao invés de fallback
            return Response({
                'success': False,
                'data': [],
                'total': 0,
                'error': str(e),
                'message': 'Erro ao buscar bancos disponíveis'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(ratelimit(key='user', rate='5/m', method='POST'), name='dispatch')
class PluggyConnectTokenView(APIView):
    """Create Pluggy Connect token for bank connection"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Create a connect token for Pluggy Connect widget"""
        
        try:
            item_id = request.data.get('item_id')
            
            async def create_token():
                async with PluggyClient() as client:
                    return await client.create_connect_token(item_id)
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                token_data = loop.run_until_complete(create_token())
            finally:
                loop.close()
            
            connect_token = token_data.get('accessToken')
            sandbox_mode = getattr(settings, 'PLUGGY_USE_SANDBOX', False)
            
            response_data = {
                'success': True,
                'data': {
                    'connect_token': connect_token,
                    'connect_url': getattr(settings, 'PLUGGY_CONNECT_URL', 'https://connect.pluggy.ai'),
                    'sandbox_mode': sandbox_mode,
                    'expires_at': token_data.get('expiresAt'),
                    'message': 'Token para sandbox Pluggy' if sandbox_mode else 'Token para produção Pluggy'
                }
            }
            
            # Só adiciona credenciais de sandbox se estiver em modo sandbox
            if sandbox_mode:
                response_data['data']['sandbox_credentials'] = {
                    'user': 'user-ok',
                    'password': 'password-ok', 
                    'token': '123456'
                }
            
            return Response(response_data)
            
        except PluggyAuthenticationError as e:
            logger.error(f"Pluggy authentication error: {e}")
            return Response({
                'success': False,
                'error': 'Authentication failed with Pluggy API',
                'details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(f"Error creating Pluggy connect token: {e}")
            return Response({
                'success': False,
                'error': 'Failed to create connect token',
                'details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _parse_account_number(account_data):
    """
    Parse account number from Pluggy data to Brazilian format
    """
    # Get the number field from Pluggy
    full_number = account_data.get('number', '')
    
    logger.info(f"🔍 Parsing account number: '{full_number}'")
    
    # Pluggy may return formats like:
    # - "0001/12345-0"  (with agency)
    # - "12345-0"       (just account)
    # - "123456"        (without digit)
    
    if '/' in full_number:
        # Format: "0001/12345-0" -> extract "12345-0"
        parts = full_number.split('/')
        if len(parts) >= 2:
            agency = parts[0].strip()
            account_number = parts[1].strip()
        else:
            agency = '0001'
            account_number = full_number.strip()
    else:
        # Format: "12345-0" or "123456"
        agency = '0001'  # Default agency
        account_number = full_number.strip()
    
    # Ensure account number has check digit
    if account_number and '-' not in account_number:
        # Add check digit if missing
        if len(account_number) >= 2:
            account_number = f"{account_number[:-1]}-{account_number[-1]}"
        else:
            account_number = "12345-6"  # Fallback
    
    # Validate final format
    if not account_number or len(account_number) < 3:
        account_number = "12345-6"  # Safe fallback
        
    # Ensure agency is not empty
    if not agency:
        agency = "0001"
    
    logger.info(f"✅ Parsed result: agency='{agency}', account='{account_number}'")
    
    return agency, account_number


@method_decorator(ratelimit(key='user', rate='10/h', method='POST'), name='dispatch')
class PluggyItemCallbackView(APIView):
    """Handle Pluggy item creation callback"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Process successful bank connection from Pluggy Connect"""
        import asyncio
        
        try:
            item_id = request.data.get('item_id')
            connector_name = request.data.get('connector_name', 'Unknown Bank')

            if not item_id:
                return Response({
                    'success': False,
                    'error': 'item_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            company = request.user.company
            
            async def process_item():
                async with PluggyClient() as client:
                    # Get item details
                    item = await client.get_item(item_id)
                    
                    # Get accounts for this item
                    accounts = await client.get_accounts(item_id)
                    
                    return item, accounts
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                item_data, accounts_data = loop.run_until_complete(process_item())
            finally:
                loop.close()
            
            # Create bank provider
            connector_id = item_data.get('connectorId', item_data.get('connector', {}).get('id', ''))
            bank_provider, _ = BankProvider.objects.get_or_create(
                code=f"pluggy_{connector_id}",
                defaults={
                    'name': item_data.get('connector', {}).get('name', connector_name),
                    'is_active': True,
                    'is_open_banking': True,
                    'supports_pix': True,
                    'supports_ted': True
                }
            )
            
            created_accounts = []
            
            for account_data in accounts_data:
                logger.info(f"Processing Pluggy account: {account_data}")
                
                # Parse account number correctly
                agency, account_number = _parse_account_number(account_data)
                
                # Map account types
                account_type_map = {
                    'BANK': 'checking',
                    'CHECKING': 'checking', 
                    'CHECKING_ACCOUNT': 'checking',
                    'SAVINGS': 'savings',
                    'SAVINGS_ACCOUNT': 'savings',
                    'CREDIT': 'credit_card',
                    'CREDIT_CARD': 'credit_card'
                }
                
                account_type = account_type_map.get(
                    account_data.get('type', 'BANK'), 
                    'checking'
                )
                
                # Better nickname using bank name + account type
                account_name = account_data.get('name', 'Conta Corrente')
                nickname = f"{bank_provider.name} - {account_name}"
                
                logger.info(f"✅ Creating account: {agency} / {account_number} - {nickname}")
                
                try:
                    # Create or update bank account
                    bank_account, created = BankAccount.objects.update_or_create(
                        company=company,
                        bank_provider=bank_provider,
                        agency=agency,
                        account_number=account_number,
                        account_type=account_type,
                        defaults={
                            'external_id': account_data.get('id'),
                            'pluggy_item_id': item_id,
                            'current_balance': Decimal(str(account_data.get('balance', 0))),
                            'available_balance': Decimal(str(account_data.get('balance', 0))),
                            'status': 'active',
                            'is_active': True,
                            'nickname': nickname,
                        }
                    )
                    
                    created_accounts.append({
                        'id': bank_account.id,
                        'name': bank_account.nickname,
                        'balance': float(bank_account.current_balance),
                        'account_type': bank_account.account_type,
                        'created': created,
                        'agency': agency,
                        'account_number': account_number
                    })
                    
                    logger.info(f"✅ Account {'created' if created else 'updated'}: {bank_account.id}")
                    
                except Exception as account_error:
                    logger.error(f"❌ Error creating account: {account_error}")
                    logger.error(f"❌ Account data that failed: agency={agency}, number={account_number}")
                    
                    # Continue with other accounts even if one fails
                    continue
            
            if not created_accounts:
                return Response({
                    'success': False,
                    'error': 'Nenhuma conta pôde ser criada. Verifique os logs para detalhes.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            sandbox_mode = getattr(settings, 'PLUGGY_USE_SANDBOX', False)
            
            return Response({
                'success': True,
                'data': {
                    'accounts': created_accounts,
                    'message': f'Conectado com sucesso ao {bank_provider.name}',
                    'sandbox_mode': sandbox_mode,
                    'item_id': item_id
                }
            })

        except PluggyAuthenticationError as e:
            logger.error(f"Pluggy authentication error: {e}")
            return Response({
                'success': False,
                'error': 'Authentication failed with Pluggy',
                'details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(f"Error in Pluggy callback: {e}", exc_info=True)
            return Response({
                'success': False,
                'error': 'An error occurred processing the connection',
                'details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(ratelimit(key='user', rate='20/h', method='POST'), name='dispatch')
class PluggySyncAccountView(APIView):
    """Manually trigger account sync"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, account_id):
        """Manually sync a specific account"""
        try:
            company = request.user.company

            # Get the account
            try:
                account = BankAccount.objects.get(
                    id=account_id,
                    company=company
                )
            except BankAccount.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Account not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check if account has external_id (is Pluggy account)
            if not account.external_id:
                return Response({
                    'success': False,
                    'error': 'This account is not connected via Pluggy'
                }, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"🔄 Starting manual sync for account {account_id}")
            
            # Use the corrected sync service
            from .pluggy_sync_service import pluggy_sync_service
            import asyncio
            
            async def sync_account():
                return await pluggy_sync_service.sync_account_transactions(account)
            
            # Run async sync
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(sync_account())
            finally:
                loop.close()
            
            sandbox_mode = getattr(settings, 'PLUGGY_USE_SANDBOX', False)
            
            logger.info(f"✅ Sync completed for account {account_id}: {result}")
            
            if result.get('status') == 'success':
                # Force update counters after sync
                from apps.companies.models import ResourceUsage
                from apps.banking.models import Transaction
                from django.utils import timezone
                
                try:
                    # Recalculate and update counters
                    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    current_month_count = Transaction.objects.filter(
                        bank_account__company=company,
                        transaction_date__gte=month_start
                    ).count()
                    
                    # Update company counter
                    company.current_month_transactions = current_month_count
                    company.save(update_fields=['current_month_transactions'])
                    
                    # Update ResourceUsage
                    usage = ResourceUsage.get_or_create_current_month(company)
                    usage.transactions_count = current_month_count
                    usage.save(update_fields=['transactions_count'])
                    
                    logger.info(f"✅ Forced counter update: {current_month_count} transactions for {company.name}")
                except Exception as e:
                    logger.error(f"❌ Error updating counters: {e}")
                
                return Response({
                    'success': True,
                    'data': {
                        'message': f'Sincronização concluída com sucesso',
                        'transactions_synced': result.get('transactions', 0),
                        'status': result.get('status'),
                        'sandbox_mode': sandbox_mode,
                        'usage_updated': True
                    }
                })
            else:
                return Response({
                    'success': False,
                    'error': f"Sync failed: {result.get('error', 'Unknown error')}",
                    'details': result
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"❌ Error syncing Pluggy account {account_id}: {e}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Sync failed',
                'details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def verify_pluggy_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify the webhook signature from Pluggy
    
    Args:
        payload: The raw request body
        signature: The signature from the X-Pluggy-Signature header
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    webhook_secret = getattr(settings, 'PLUGGY_WEBHOOK_SECRET', '')
    
    if not webhook_secret:
        logger.warning("PLUGGY_WEBHOOK_SECRET not configured")
        return False
    
    try:
        # Calculate expected signature
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


async def process_webhook_event(event_type: str, event_data: dict) -> dict:
    """
    Process webhook events asynchronously
    
    Args:
        event_type: Type of webhook event
        event_data: Event payload data
        
    Returns:
        dict: Processing result
    """
    result = {'success': True, 'message': ''}
    
    try:
        if event_type == 'item/created':
            item_id = event_data.get('id')
            logger.info(f"Pluggy item created: {item_id}")
            result['message'] = f'Item {item_id} created successfully'
            
        elif event_type == 'item/updated':
            item_id = event_data.get('id')
            status_val = event_data.get('status')
            logger.info(f"Pluggy item {item_id} updated: {status_val}")
            
            # If item is now active, sync all accounts
            if status_val == 'ACTIVE':
                accounts = BankAccount.objects.filter(
                    pluggy_item_id=item_id,
                    is_active=True
                )
                
                if accounts.exists():
                    sync_service = PluggyTransactionSyncService()
                    for account in accounts:
                        try:
                            await sync_service.sync_account(account.id)
                            logger.info(f"Synced account {account.id} after item update")
                        except Exception as e:
                            logger.error(f"Failed to sync account {account.id}: {e}")
                            
            result['message'] = f'Item {item_id} updated to {status_val}'
            
        elif event_type == 'item/error':
            item_id = event_data.get('id')
            error = event_data.get('error')
            logger.warning(f"Pluggy item {item_id} error: {error}")
            
            # Mark accounts as having errors
            BankAccount.objects.filter(
                pluggy_item_id=item_id
            ).update(
                sync_status='error',
                sync_error_message=error.get('message', 'Unknown error')
            )
            
            result['message'] = f'Item {item_id} error recorded'
            
        elif event_type == 'transactions/created':
            account_id = event_data.get('accountId')
            if account_id:
                logger.info(f"New transactions for Pluggy account {account_id}")
                
                # Find and sync the account
                try:
                    account = BankAccount.objects.get(
                        external_id=account_id,
                        is_active=True
                    )
                    
                    sync_service = PluggyTransactionSyncService()
                    await sync_service.sync_account(account.id)
                    
                    result['message'] = f'Synced new transactions for account {account_id}'
                except BankAccount.DoesNotExist:
                    logger.warning(f"Account {account_id} not found for transaction sync")
                    result['success'] = False
                    result['message'] = f'Account {account_id} not found'
                    
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            result['message'] = f'Event {event_type} received but not processed'
            
    except Exception as e:
        logger.error(f"Error processing webhook event {event_type}: {e}")
        result['success'] = False
        result['message'] = str(e)
        
    return result


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def pluggy_webhook(request):
    """Handle Pluggy webhooks for real-time updates"""
    try:
        # Verify webhook signature
        signature = request.META.get('HTTP_X_PLUGGY_SIGNATURE', '')
        
        # Get raw body for signature verification
        raw_body = request.body
        
        # Verify signature if webhook secret is configured
        if getattr(settings, 'PLUGGY_WEBHOOK_SECRET', ''):
            if not signature:
                logger.warning("Missing X-Pluggy-Signature header")
                return Response(
                    {'error': 'Missing signature'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
            if not verify_pluggy_webhook_signature(raw_body, signature):
                logger.warning("Invalid webhook signature")
                return Response(
                    {'error': 'Invalid signature'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        # Parse event data
        event_type = request.data.get('event') or request.data.get('type')
        event_data = request.data.get('data', {})
        
        logger.info(f"Received authenticated Pluggy webhook: {event_type}")
        
        # Process webhook asynchronously
        result = asyncio.run(process_webhook_event(event_type, event_data))
        
        if result['success']:
            return Response({
                'status': 'received',
                'message': result['message']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': result['message']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error(f"Error processing Pluggy webhook: {e}")
        return Response(
            {'error': 'Webhook processing failed'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@method_decorator(ratelimit(key='user', rate='5/h', method='DELETE'), name='dispatch')
class PluggyDisconnectAccountView(APIView):
    """Disconnect a Pluggy account"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, account_id):
        """Disconnect account from Pluggy"""
        try:
            company = request.user.company

            account = BankAccount.objects.get(
                id=account_id,
                company=company
            )

            # TODO: Delete from Pluggy using item_id
            # if account.pluggy_item_id:
            #     await pluggy_client.delete_item(account.pluggy_item_id)

            # Deactivate account locally
            account.status = 'inactive'
            account.is_active = False
            account.save()

            return Response({
                'success': True,
                'message': 'Account disconnected successfully'
            })

        except BankAccount.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Account not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error disconnecting Pluggy account {account_id}: {e}")
            return Response({
                'success': False,
                'error': 'Failed to disconnect account'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(ratelimit(key='user', rate='10/h', method='GET'), name='dispatch')
class PluggyAccountStatusView(APIView):
    """Get Pluggy account connection status"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, account_id):
        """Get real-time status of Pluggy account"""
        try:
            company = request.user.company

            account = BankAccount.objects.get(
                id=account_id,
                company=company
            )

            sandbox_mode = getattr(settings, 'PLUGGY_USE_SANDBOX', False)

            return Response({
                'success': True,
                'data': {
                    'account_id': account.id,
                    'external_id': account.external_id,
                    'status': account.status,
                    'last_sync': account.last_sync_at,
                    'balance': float(account.current_balance or 0),
                    'pluggy_status': 'active' if account.is_active else 'inactive',
                    'last_update': account.updated_at,
                    'sandbox_mode': sandbox_mode
                }
            })

        except BankAccount.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Account not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting account status {account_id}: {e}")
            return Response({
                'success': False,
                'error': 'Failed to get account status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)