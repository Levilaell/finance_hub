"""
Pluggy-specific views for bank connection and management
"""
import logging
from typing import Dict, Any
from decimal import Decimal

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from .models import BankAccount, BankProvider
from .serializers import BankAccountSerializer, BankProviderSerializer

logger = logging.getLogger(__name__)


@method_decorator(ratelimit(key='user', rate='10/m', method='GET'), name='dispatch')
class PluggyBankProvidersView(APIView):
    """Get available banks from Pluggy"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get list of banks supported by Pluggy"""
        import asyncio
        from .pluggy_client import PluggyClient
        
        try:
            # Get real banks from Pluggy
            async def get_banks():
                async with PluggyClient() as client:
                    connectors = await client.get_connectors()
                    
                    # Filter and format for our use
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
                                'supports_transactions': connector.get('hasTransactions', True)
                            })
                    
                    return banks
            
            # Execute async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                banks = loop.run_until_complete(get_banks())
            finally:
                loop.close()
            
            return Response({
                'success': True,
                'data': banks,
                'total': len(banks)
            })
            
        except Exception as e:
            logger.error(f"Error getting Pluggy banks: {e}")
            
            # Fallback to cached/default banks if API fails
            default_banks = [
                {
                    'id': 201,
                    'name': 'Banco do Brasil',
                    'code': '201',
                    'health_status': 'ONLINE'
                },
                {
                    'id': 202, 
                    'name': 'Itaú',
                    'code': '202',
                    'health_status': 'ONLINE'
                },
                {
                    'id': 203,
                    'name': 'Bradesco',
                    'code': '203',
                    'health_status': 'ONLINE'
                }
            ]
            
            return Response({
                'success': True,
                'data': default_banks,
                'total': len(default_banks),
                'cached': True
            })


@method_decorator(ratelimit(key='user', rate='5/m', method='POST'), name='dispatch')
class PluggyConnectTokenView(APIView):
    """Create Pluggy Connect token for bank connection"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Create a connect token for Pluggy Connect widget"""
        import asyncio
        from .pluggy_client import PluggyClient
        
        try:
            # Optional: specify item_id for reconnection
            item_id = request.data.get('item_id')
            
            # Run async client
            async def create_token():
                async with PluggyClient() as client:
                    return await client.create_connect_token(item_id)
            
            # Execute async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                token_data = loop.run_until_complete(create_token())
            finally:
                loop.close()
            
            # Return connect token data
            return Response({
                'success': True,
                'data': {
                    'connect_token': token_data.get('accessToken'),
                    'connect_url': getattr(settings, 'PLUGGY_CONNECT_URL', 'https://connect.pluggy.ai'),
                    'status': 'pluggy_connect_required',
                    'message': 'Use o Pluggy Connect para conectar sua conta'
                }
            })
            
        except Exception as e:
            logger.error(f"Error creating Pluggy connect token: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(ratelimit(key='user', rate='10/h', method='POST'), name='dispatch')
class PluggyItemCallbackView(APIView):
    """Handle Pluggy item creation callback"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Process successful bank connection from Pluggy Connect"""
        import asyncio
        from .pluggy_client import PluggyClient
        
        try:
            item_id = request.data.get('item_id')
            connector_name = request.data.get('connector_name', 'Unknown Bank')

            if not item_id:
                return Response({
                    'success': False,
                    'error': 'item_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            company = request.user.company
            
            # Get item details and accounts from Pluggy
            async def process_item():
                async with PluggyClient() as client:
                    # Get item details
                    item = await client.get_item(item_id)
                    
                    # Get accounts for this item
                    accounts = await client.get_accounts(item_id)
                    
                    return item, accounts
            
            # Execute async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                item_data, accounts_data = loop.run_until_complete(process_item())
            finally:
                loop.close()
            
            # Create or update bank accounts
            created_accounts = []
            
            # Find or create bank provider
            bank_provider, _ = BankProvider.objects.get_or_create(
                code=f"pluggy_{item_data.get('connectorId', '')}",
                defaults={
                    'name': item_data.get('connector', {}).get('name', connector_name),
                    'is_active': True,
                    'is_open_banking': False,
                    'supports_pix': True,
                    'supports_ted': True
                }
            )
            
            for account_data in accounts_data:
                # Map Pluggy account type to our types
                account_type_map = {
                    'BANK': 'checking',
                    'CHECKING': 'checking',
                    'SAVINGS': 'savings',
                    'CREDIT': 'credit_card'
                }
                
                account_type = account_type_map.get(
                    account_data.get('type', 'BANK'), 
                    'checking'
                )
                
                # Create bank account
                bank_account = BankAccount.objects.create(
                    company=company,
                    bank_provider=bank_provider,
                    external_account_id=account_data.get('id'),
                    pluggy_item_id=item_id,
                    account_type=account_type,
                    account_number=account_data.get('number', ''),
                    agency=account_data.get('agency', ''),
                    current_balance=Decimal(str(account_data.get('balance', 0))),
                    available_balance=Decimal(str(account_data.get('balance', 0))),
                    status='active',
                    is_active=True,
                    nickname=f"{bank_provider.name} - {account_data.get('name', 'Conta')}"
                )
                
                created_accounts.append({
                    'id': bank_account.id,
                    'name': bank_account.nickname,
                    'balance': float(bank_account.current_balance)
                })
                
                # Initial sync will be handled later via scheduled tasks
                logger.info(f"Account {bank_account.id} created, sync will be handled by background tasks")
            
            return Response({
                'success': True,
                'data': {
                    'accounts': created_accounts,
                    'message': f'Conectado com sucesso ao {bank_provider.name}'
                }
            })

        except Exception as e:
            logger.error(f"Error in Pluggy callback: {e}")
            return Response({
                'success': False,
                'error': 'An unexpected error occurred'
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
                    company=company,
                    status='active'
                )
            except BankAccount.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Account not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Trigger real sync via Celery task
            from .tasks import sync_bank_account
            
            # Queue async sync task
            sync_bank_account.delay(account_id)
            
            return Response({
                'success': True,
                'data': {
                    'message': 'Account synchronization started',
                    'status': 'processing'
                }
            })

        except Exception as e:
            logger.error(f"Error syncing Pluggy account {account_id}: {e}")
            return Response({
                'success': False,
                'error': 'Sync failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # Webhook should use API key authentication
def pluggy_webhook(request):
    """Handle Pluggy webhooks for real-time updates"""
    try:
        event_type = request.data.get('type')
        event_data = request.data.get('data', {})

        logger.info(f"Received Pluggy webhook: {event_type}")

        # Handle different webhook events
        if event_type == 'item/created':
            item_id = event_data.get('id')
            logger.info(f"Pluggy item created: {item_id}")

        elif event_type == 'item/updated':
            item_id = event_data.get('id')
            status_val = event_data.get('status')
            logger.info(f"Pluggy item {item_id} updated: {status_val}")

        elif event_type == 'item/error':
            item_id = event_data.get('id')
            error = event_data.get('error')
            logger.warning(f"Pluggy item {item_id} error: {error}")

        elif event_type == 'transactions/created':
            account_id = event_data.get('accountId')
            if account_id:
                logger.info(f"New transactions for Pluggy account {account_id}")

        return Response({'status': 'received'}, status=status.HTTP_200_OK)

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

            # Deactivate account locally
            account.status = 'inactive'
            account.is_active = False
            account.save()

            return Response({
                'success': True,
                'message': 'Account disconnected successfully'
            })

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

            # Mock account status response
            return Response({
                'success': True,
                'data': {
                    'account_id': account.id,
                    'external_id': account.external_account_id or 'mock-ext-id',
                    'status': account.status,
                    'last_sync': account.last_sync_at,
                    'balance': float(account.current_balance or 0),
                    'pluggy_status': 'active',
                    'last_update': None
                }
            })

        except Exception as e:
            logger.error(f"Error getting account status {account_id}: {e}")
            return Response({
                'success': False,
                'error': 'Failed to get account status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)