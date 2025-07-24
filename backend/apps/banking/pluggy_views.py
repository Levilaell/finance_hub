"""
Pluggy integration views
Handles Pluggy-specific endpoints for bank account connections
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import json

from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BankAccount, BankProvider, Transaction
from .pluggy_client import PluggyClient
from .serializers import BankAccountSerializer

logger = logging.getLogger(__name__)


class PluggyConnectTokenView(APIView):
    """
    Generate Pluggy Connect token for widget integration
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Create a connect token for new or existing connections
        """
        try:
            logger.info(f"Creating Pluggy connect token for user {request.user.id}")
            pluggy = PluggyClient()
            
            # Get optional parameters
            item_id = request.data.get('itemId') or request.data.get('item_id')
            client_user_id = request.data.get('clientUserId', str(request.user.id))
            
            logger.info(f"Parameters - item_id: {item_id}, client_user_id: {client_user_id}")
            
            # Create connect token
            token_data = pluggy.create_connect_token(
                item_id=item_id,
                client_user_id=client_user_id
            )
            
            logger.info("Connect token created successfully")
            
            # Format response to match frontend expectations
            response_data = {
                'success': True,
                'data': {
                    'connect_token': token_data['accessToken'],
                    'connect_url': token_data['connectUrl'],
                    'sandbox_mode': pluggy.use_sandbox,
                    'expires_at': token_data.get('expiresAt')
                }
            }
            
            # Add sandbox credentials if in sandbox mode
            if pluggy.use_sandbox:
                response_data['data']['sandbox_credentials'] = {
                    'user': 'user-ok',
                    'password': 'password-ok', 
                    'token': '123456'
                }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Failed to create connect token: {e}", exc_info=True)
            return Response(
                {
                    'success': False,
                    'error': str(e),
                    'message': f'Erro ao criar token de conexão: {str(e)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class PluggyBanksView(APIView):
    """
    List available banks from Pluggy (alias for connectors)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get list of available banks
        """
        try:
            pluggy = PluggyClient()
            
            # Get query parameters
            country = request.query_params.get('country', 'BR')
            connector_type = request.query_params.get('type')
            sandbox = request.query_params.get('sandbox')
            
            # Get connectors
            connectors = pluggy.get_connectors(
                country=country,
                type=connector_type,
                sandbox=sandbox.lower() == 'true' if sandbox else None
            )
            
            # Filter and format for frontend
            formatted_banks = []
            for connector in connectors:
                # Skip if not a bank connector
                if connector.get('type') != 'PERSONAL_BANK':
                    continue
                    
                formatted_banks.append({
                    'id': connector['id'],
                    'code': str(connector['id']),  # Use ID as code
                    'name': connector['name'],
                    'institutionUrl': connector.get('institutionUrl', ''),
                    'logo_url': connector.get('imageUrl', ''),
                    'imageUrl': connector.get('imageUrl', ''),
                    'primary_color': connector.get('primaryColor', '#000000'),
                    'primaryColor': connector.get('primaryColor', '#000000'),
                    'country': connector.get('country', 'BR'),
                    'type': connector['type'],
                    'sandbox': connector.get('sandbox', False),
                    'oauth': connector.get('oauth', False),
                    'openFinance': connector.get('openFinance', False),
                    'is_active': True
                })
            
            return Response({
                'success': True,
                'data': formatted_banks,
                'total': len(formatted_banks),
                'sandbox_mode': pluggy.use_sandbox
            })
            
        except Exception as e:
            logger.error(f"Failed to get banks: {e}")
            return Response(
                {
                    'success': False,
                    'error': str(e),
                    'data': []
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class PluggyConnectorsView(APIView):
    """
    List available bank connectors
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get list of available bank connectors
        """
        try:
            pluggy = PluggyClient()
            
            # Get query parameters
            country = request.query_params.get('country', 'BR')
            connector_type = request.query_params.get('type')
            sandbox = request.query_params.get('sandbox')
            
            # Get connectors
            connectors = pluggy.get_connectors(
                country=country,
                type=connector_type,
                sandbox=sandbox.lower() == 'true' if sandbox else None
            )
            
            # Filter and format for frontend
            formatted_connectors = []
            for connector in connectors:
                # Skip if not a bank connector
                if connector.get('type') != 'PERSONAL_BANK':
                    continue
                    
                formatted_connectors.append({
                    'id': connector['id'],
                    'name': connector['name'],
                    'institutionUrl': connector.get('institutionUrl', ''),
                    'imageUrl': connector.get('imageUrl', ''),
                    'primaryColor': connector.get('primaryColor', '#000000'),
                    'country': connector.get('country', 'BR'),
                    'type': connector['type'],
                    'sandbox': connector.get('sandbox', False),
                    'oauth': connector.get('oauth', False),
                    'openFinance': connector.get('openFinance', False)
                })
            
            return Response(formatted_connectors)
            
        except Exception as e:
            logger.error(f"Failed to get connectors: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PluggyCallbackView(APIView):
    """
    Handle Pluggy Connect callback
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Process successful connection from Pluggy Connect
        """
        try:
            # Accept both itemId and item_id
            item_id = request.data.get('itemId') or request.data.get('item_id')
            status_callback = request.data.get('status')
            error = request.data.get('error')
            
            logger.info(f"Pluggy callback received - item_id: {item_id}, data: {request.data}")
            
            if error or status_callback == 'error':
                logger.error(f"Pluggy connection error: {error}")
                return Response(
                    {'error': error or 'Connection failed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not item_id:
                logger.error(f"No item ID provided. Request data: {request.data}")
                return Response(
                    {'error': 'itemId is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            pluggy = PluggyClient()
            
            # Get item details
            item = pluggy.get_item(item_id)

            logger.info(f"Item details: {json.dumps(item, indent=2)}")
            if item.get('statusDetail'):
                logger.info(f"Item status details: {json.dumps(item['statusDetail'], indent=2)}")

                transactions_detail = item['statusDetail'].get('transactions', {})
                if not transactions_detail.get('isUpdated', False):
                    logger.warning("Transactions are not yet updated for this item")
            
            # Get accounts for this item
            accounts_response = pluggy.get_accounts(item_id)
            
            # Debug: Log the raw response
            logger.info(f"Raw accounts response type: {type(accounts_response)}")
            logger.info(f"Raw accounts response: {accounts_response}")
            
            # Handle different response formats from Pluggy
            if isinstance(accounts_response, dict):
                # If response is a dict, look for 'results' or 'data' key
                accounts = accounts_response.get('results', accounts_response.get('data', []))
                logger.info(f"Extracted accounts from dict: {accounts}")
            elif isinstance(accounts_response, list):
                accounts = accounts_response
                logger.info(f"Using accounts list directly: {accounts}")
            else:
                logger.error(f"Unexpected accounts response type: {type(accounts_response)}, value: {accounts_response}")
                accounts = []
            
            logger.info(f"Found {len(accounts)} accounts for item {item_id}")
            
            created_accounts = []
            
            # Check if user has a company
            if not hasattr(request.user, 'company') or not request.user.company:
                logger.error(f"User {request.user.id} has no company associated")
                return Response(
                    {
                        'success': False,
                        'error': 'User has no company',
                        'message': 'Usuário não possui empresa associada. Por favor, complete seu cadastro.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user_company = request.user.company
            logger.info(f"Processing accounts for company {user_company.id}")
            
            with transaction.atomic():
                for account_data in accounts:
                    # Debug: Log each account data
                    logger.info(f"Processing account data - Type: {type(account_data)}, Value: {account_data}")
                    
                    # Skip if not a valid account object
                    if not isinstance(account_data, dict):
                        logger.warning(f"Skipping invalid account data: {account_data}")
                        continue
                        
                    logger.info(f"Processing account: {account_data.get('id', 'unknown')}, type: {account_data.get('type')}")
                    
                    # Create or update bank provider
                    connector = item.get('connector', {})
                    provider, _ = BankProvider.objects.get_or_create(
                        code=str(connector.get('id')),
                        defaults={
                            'name': connector.get('name', 'Unknown Bank'),
                            'logo_url': connector.get('imageUrl', ''),
                            'primary_color': connector.get('primaryColor', '#000000'),
                            'api_endpoint': '',  # Not used with Pluggy
                            'is_active': True
                        }
                    )
                    logger.info(f"Bank provider: {provider}")
                    
                    # Prepare account data - simplified approach
                    account_type = self._map_account_type(account_data.get('type'))
                    account_number = account_data.get('number', '') or 'N/A'
                    
                    # Optional: Extract agency if available (not required)
                    agency = account_data.get('agency', '')
                    if not agency and account_data.get('bankData', {}).get('transferNumber'):
                        # Try to extract from transferNumber if needed for display
                        transfer_number = account_data['bankData']['transferNumber']
                        parts = transfer_number.split('/')
                        if len(parts) >= 2:
                            agency = parts[1]
                    
                    # Extract account digit if present
                    account_digit = ''
                    if '-' in str(account_number):
                        parts = str(account_number).split('-')
                        account_number = parts[0]
                        account_digit = parts[1] if len(parts) > 1 else ''
                    
                    # Log the data for debugging
                    logger.info(f"Account data - Type: {account_type}, Number: {account_number}, Agency: {agency}")
                    
                    try:
                        # Create or update bank account
                        bank_account, created = BankAccount.objects.update_or_create(
                            external_id=account_data['id'],
                            company=user_company,
                            defaults={
                                'bank_provider': provider,
                                'pluggy_item_id': item_id,
                                'account_type': account_type,
                                'account_number': account_number,
                                'agency': agency,
                                'account_digit': account_digit,
                                'name': account_data.get('name', 'Conta Bancária'),
                                'current_balance': Decimal(str(account_data.get('balance', 0))),
                                'available_balance': Decimal(str(account_data.get('balance', 0))),
                                'currency': account_data.get('currencyCode', 'BRL'),
                                'is_active': True,
                                'status': 'active',
                                'last_sync_at': timezone.now(),
                                'metadata': {
                                    'owner': account_data.get('owner', ''),
                                    'subtype': account_data.get('subtype', ''),
                                    'bank_data': account_data.get('bankData', {}),
                                    'created_at': account_data.get('createdAt', ''),
                                    'updated_at': account_data.get('updatedAt', '')
                                }
                            }
                        )
                    except Exception as e:
                        logger.error(f"Error creating/updating bank account: {e}")
                        # If unique constraint fails, try to find existing account by external_id
                        bank_account = BankAccount.objects.filter(
                            company=user_company,
                            external_id=account_data['id']
                        ).first()
                        
                        if bank_account:
                            # Update existing account
                            bank_account.external_id = account_data['id']
                            bank_account.pluggy_item_id = item_id
                            bank_account.current_balance = Decimal(str(account_data.get('balance', 0)))
                            bank_account.available_balance = Decimal(str(account_data.get('balance', 0)))
                            bank_account.last_sync_at = timezone.now()
                            bank_account.status = 'active'
                            bank_account.save()
                            created = False
                            logger.info(f"Updated existing bank account: {bank_account}")
                        else:
                            raise e
                    
                    if created:
                        logger.info(f"Created new bank account: {bank_account}")
                    else:
                        logger.info(f"Updated bank account: {bank_account}")
                    
                    created_accounts.append(bank_account)
                
                # Fetch initial transactions only if accounts were created
                if created_accounts:
                    logger.info(f"Syncing transactions for {len(created_accounts)} accounts")
                    # Give Pluggy a moment to process the new connection
                    import time
                    time.sleep(5)

                    item_check = pluggy.get_item(item_id)
                    item_status = item_check.get('status')
                    execution_status = item_check.get('executionStatus')
                    logger.info(f"Item status before syncing transactions: {item_status}")
                    
                    # Log do statusDetail também
                    if item_check.get('statusDetail'):
                        logger.info(f"Status details: {json.dumps(item_check['statusDetail'], indent=2)}")
                    
                    if item_status not in ['UPDATED', 'PARTIAL_SUCCESS']:
                        logger.warning(f"Item not ready for transaction sync. Status: {item_status}")
                        # Talvez agendar uma tarefa assíncrona para sincronizar depois
                    
                    else:
                        for account in created_accounts:
                            try:
                                logger.info(f"Starting transaction sync for account {account.id} (external_id: {account.external_id})")
                                self._sync_transactions(account, pluggy)
                            except Exception as e:
                                logger.error(f"Error syncing transactions for account {account.id}: {e}", exc_info=True)
                
            # Return response even if no accounts were created
            if not created_accounts:
                logger.warning(f"No accounts created for item {item_id}")
                # Try to get existing accounts
                existing_accounts = BankAccount.objects.filter(
                    pluggy_item_id=item_id,
                    company=user_company
                )
                if existing_accounts.exists():
                    created_accounts = list(existing_accounts)
                    logger.info(f"Found {len(created_accounts)} existing accounts for item")
            
            # Return created accounts in the format expected by frontend
            serializer = BankAccountSerializer(created_accounts, many=True)
            return Response({
                'success': True,
                'data': {
                    'accounts': serializer.data,
                    'message': f'Successfully connected {len(created_accounts)} account(s)',
                    'sandbox_mode': pluggy.use_sandbox,
                    'item_id': item_id
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to process Pluggy callback: {e}", exc_info=True)
            return Response(
                {
                    'success': False,
                    'error': str(e),
                    'message': f'Erro ao processar conexão: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _map_account_type(self, pluggy_type: str) -> str:
        """
        Map Pluggy account type to our internal types
        """
        type_mapping = {
            'BANK': 'checking',  # Default bank accounts to checking
            'CHECKING': 'checking',
            'SAVINGS': 'savings',
            'CREDIT_CARD': 'credit_card',
            'INVESTMENT': 'investment',
            'OTHER': 'other'
        }
        return type_mapping.get(pluggy_type, 'checking')
    
    def _sync_transactions(self, bank_account: BankAccount, pluggy: PluggyClient):
        """
        Sync transactions for a bank account
        """
        try:
            # Get transactions for the last 90 days
            from_date = timezone.now() - timedelta(days=90)
            to_date = timezone.now()
            
            page = 1
            total_created = 0
            total_updated = 0
            
            while True:
                # Get transactions page
                logger.info(f"Fetching transactions for account {bank_account.external_id}, page {page}")
                result = pluggy.get_transactions(
                    account_id=bank_account.external_id,
                    from_date=from_date,
                    to_date=to_date,
                    page=page
                )
                
                # Handle None result
                if result is None:
                    logger.warning(f"No transactions data returned for account {bank_account.external_id}")
                    break
                    
                # Extract transactions from result
                if isinstance(result, dict):
                    transactions = result.get('results', [])
                    total_pages = result.get('totalPages', 1)
                elif isinstance(result, list):
                    transactions = result
                    total_pages = 1
                else:
                    logger.warning(f"Unexpected transaction result type: {type(result)}")
                    transactions = []
                    total_pages = 1
                
                if not transactions:
                    logger.info(f"No more transactions on page {page}")
                    break
                
                for trans_data in transactions:
                    created = self._process_transaction(bank_account, trans_data)
                    if created:
                        total_created += 1
                    else:
                        total_updated += 1
                
                # Check if there are more pages
                if page >= total_pages:
                    break
                    
                page += 1
            
            logger.info(f"Synced transactions for {bank_account}: {total_created} new, {total_updated} updated")
            
        except Exception as e:
            logger.error(f"Failed to sync transactions: {e}", exc_info=True)

    def _process_transaction(self, bank_account: BankAccount, trans_data: Dict) -> bool:
        """
        Process a single transaction
        """
        from .pluggy_category_mapper import PluggyCategoryMapper
        
        # Map transaction type
        transaction_type = self._map_transaction_type(trans_data)
        
        # Get amount (already includes sign based on type)
        amount = Decimal(str(trans_data.get('amount', 0)))
        
        # Parse date
        date_str = trans_data.get('date')
        if date_str:
            transaction_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            transaction_date = timezone.now()
        
        # Get or create category
        category = None
        if trans_data.get('category'):
            mapper = PluggyCategoryMapper()
            category = mapper.get_or_create_category(trans_data['category'])
        
        # Create or update transaction
        transaction_obj, created = Transaction.objects.update_or_create(
            external_id=trans_data['id'],
            bank_account=bank_account,
            defaults={
                'transaction_type': transaction_type,
                'amount': amount,
                'description': trans_data.get('description', '')[:500],
                'transaction_date': transaction_date,
                'counterpart_name': trans_data.get('merchant', {}).get('name', '')[:200],
                'category': category,
                'status': 'completed',
                'metadata': {
                    'pluggy_category': trans_data.get('category'),
                    'payment_method': trans_data.get('paymentMethod'),
                    'merchant': trans_data.get('merchant', {})
                }
            }
        )
        
        return created
    
    def _map_transaction_type(self, trans_data: Dict) -> str:
        """
        Map Pluggy transaction type to our internal types
        """
        amount = trans_data.get('amount', 0)
        payment_method = trans_data.get('paymentMethod')
        
        # Determine type based on amount and payment method
        if amount > 0:
            if payment_method == 'PIX':
                return 'pix_in'
            elif payment_method == 'TRANSFER':
                return 'transfer_in'
            else:
                return 'credit'
        else:
            if payment_method == 'PIX':
                return 'pix_out'
            elif payment_method == 'TRANSFER':
                return 'transfer_out'
            elif payment_method == 'DEBIT_CARD':
                return 'debit'
            else:
                return 'debit'


class PluggyAccountStatusView(APIView):
    """
    Get sync status for a bank account
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, account_id):
        """
        Get current sync status for an account
        """
        try:
            # Get account
            account = BankAccount.objects.get(
                id=account_id,
                company=request.user.company
            )
            
            return Response({
                'id': account.id,
                'status': account.status,
                'sync_status': account.sync_status,
                'last_sync_at': account.last_sync_at.isoformat() if account.last_sync_at else None,
                'sync_error_message': account.sync_error_message,
                'current_balance': float(account.current_balance),
                'available_balance': float(account.available_balance),
                'transaction_count': account.transactions.count()
            })
            
        except BankAccount.DoesNotExist:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class PluggyAccountSyncView(APIView):
    """
    Sync specific account data
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, account_id):
        """
        Trigger sync for a specific account
        """
        try:
            # Get account
            account = BankAccount.objects.get(
                id=account_id,
                company=request.user.company
            )
            
            if not account.pluggy_item_id:
                return Response(
                    {'error': 'Account not connected through Pluggy'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            pluggy = PluggyClient()
            
            # Update item to trigger sync
            pluggy.update_item(account.pluggy_item_id)
            
            # Get updated account info
            accounts = pluggy.get_accounts(account.pluggy_item_id)
            
            for acc_data in accounts:
                if acc_data['id'] == account.external_id:
                    # Update balance
                    account.current_balance = Decimal(str(acc_data.get('balance', 0)))
                    account.available_balance = Decimal(str(acc_data.get('balance', 0)))
                    account.last_sync_at = timezone.now()
                    account.save()
                    break
            
            # Sync recent transactions
            callback_view = PluggyCallbackView()
            callback_view._sync_transactions(account, pluggy)
            
            return Response({
                'message': 'Sync completed successfully',
                'account': BankAccountSerializer(account).data
            })
            
        except BankAccount.DoesNotExist:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Failed to sync account: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class PluggyWebhookView(APIView):
    """
    Handle Pluggy webhooks
    """
    permission_classes = []  # Webhooks don't use normal auth
    authentication_classes = []  # Disable authentication for webhooks
    throttle_classes = []  # Disable rate limiting for webhooks
    
    def post(self, request):
        """
        Process Pluggy webhook events
        """
        try:
            # Validate webhook signature (disabled for now)
            # TODO: Configure PLUGGY_WEBHOOK_SECRET in production
            signature = request.headers.get('X-Pluggy-Signature', '')
            pluggy = PluggyClient()
            
            # Temporarily disabled for testing
            # if not pluggy.validate_webhook(signature, request.body.decode()):
            #     logger.warning("Invalid webhook signature")
            #     return Response(
            #         {'error': 'Invalid signature'},
            #         status=status.HTTP_401_UNAUTHORIZED
            #     )
            
            logger.info(f"Webhook received with signature: {signature[:20]}..." if signature else "No signature")
            
            # Process event
            event_type = request.data.get('event')
            data = request.data.get('data', {})
            
            logger.info(f"Received Pluggy webhook: {event_type}")
            
            if event_type == 'item.updated':
                self._handle_item_updated(data)
            elif event_type == 'item.error':
                self._handle_item_error(data)
            elif event_type == 'item.deleted':
                self._handle_item_deleted(data)
            elif event_type == 'transactions.created':
                self._handle_transactions_created(data)
            
            return Response({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _handle_item_updated(self, data: Dict):
        """
        Handle item updated event
        """
        item_id = data.get('id')
        if not item_id:
            return
            
        # Find accounts with this item
        accounts = BankAccount.objects.filter(pluggy_item_id=item_id)
        
        for account in accounts:
            account.last_sync_at = timezone.now()
            account.status = 'active'
            account.save()
            
            logger.info(f"Updated account {account} from webhook")
    
    def _handle_item_error(self, data: Dict):
        """
        Handle item error event
        """
        item_id = data.get('id')
        error = data.get('error', {})
        
        if not item_id:
            return
            
        # Update account status
        accounts = BankAccount.objects.filter(pluggy_item_id=item_id)
        
        for account in accounts:
            account.status = 'error'
            account.sync_error_message = error.get('message', 'Unknown error')
            account.save()
            
            logger.error(f"Account {account} error: {error}")
    
    def _handle_item_deleted(self, data: Dict):
        """
        Handle item deleted event
        """
        item_id = data.get('id')
        if not item_id:
            return
            
        # Deactivate accounts
        accounts = BankAccount.objects.filter(pluggy_item_id=item_id)
        
        for account in accounts:
            account.is_active = False
            account.status = 'disconnected'
            account.save()
            
            logger.info(f"Deactivated account {account} from webhook")
    
    def _handle_transactions_created(self, data: Dict):
        """
        Handle new transactions event
        """
        # This would trigger a sync for the affected accounts
        # Implementation depends on webhook data structure
        pass