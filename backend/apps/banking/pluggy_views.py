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
            include_open_finance = request.data.get('includeOpenFinance', True)
            products = request.data.get('products', ['ACCOUNTS', 'TRANSACTIONS'])
            
            logger.info(f"Parameters - item_id: {item_id}, client_user_id: {client_user_id}, open_finance: {include_open_finance}")
            
            # Create connect token with Open Finance support
            token_data = pluggy.create_connect_token(
                item_id=item_id,
                client_user_id=client_user_id,
                products=products
            )
            
            logger.info("Connect token created successfully")
            
            # Format response to match frontend expectations
            response_data = {
                'success': True,
                'data': {
                    'connect_token': token_data['accessToken'],
                    'connect_url': token_data['connectUrl'],
                    'sandbox_mode': pluggy.use_sandbox,
                    'expires_at': token_data.get('expiresAt'),
                    'include_open_finance': include_open_finance
                }
            }
            
            # Add sandbox credentials if in sandbox mode
            if pluggy.use_sandbox:
                response_data['data']['sandbox_credentials'] = {
                    'user': 'user-ok',
                    'password': 'password-ok', 
                    'token': '123456',
                    'cpf': '76109277673',  # CPF para teste Open Finance
                    'open_finance_user': 'test@example.com',
                    'open_finance_password': 'P@ssword01'
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
            include_open_finance = request.query_params.get('includeOpenFinance', 'true').lower() == 'true'
            
            # Get connectors
            all_connectors = []
            
            # Get regular connectors
            regular_connectors = pluggy.get_connectors(
                country=country,
                type=connector_type,
                sandbox=sandbox.lower() == 'true' if sandbox else None,
                is_open_finance=False
            )
            all_connectors.extend(regular_connectors)
            
            # Get Open Finance connectors if requested
            if include_open_finance:
                of_connectors = pluggy.get_connectors(
                    country=country,
                    type=connector_type,
                    is_open_finance=True
                )
                all_connectors.extend(of_connectors)
            
            # Filter and format for frontend
            formatted_banks = []
            for connector in all_connectors:
                # Skip if not a bank connector
                if connector.get('type') not in ['PERSONAL_BANK', 'BUSINESS_BANK']:
                    continue
                    
                formatted_banks.append({
                    'id': connector['id'],
                    'code': str(connector['id']),
                    'name': connector['name'],
                    'displayName': f"[OF] {connector['name']}" if connector.get('isOpenFinance') else connector['name'],
                    'institutionUrl': connector.get('institutionUrl', ''),
                    'logo_url': connector.get('imageUrl', ''),
                    'imageUrl': connector.get('imageUrl', ''),
                    'primary_color': connector.get('primaryColor', '#000000'),
                    'primaryColor': connector.get('primaryColor', '#000000'),
                    'country': connector.get('country', 'BR'),
                    'type': connector['type'],
                    'sandbox': connector.get('sandbox', False),
                    'oauth': connector.get('oauth', False),
                    'openFinance': connector.get('isOpenFinance', False),
                    'isOpenFinance': connector.get('isOpenFinance', False),
                    'is_active': True,
                    'supportedProducts': connector.get('products', []),
                    'requiresCpfCnpj': connector.get('isOpenFinance', False)
                })
            
            return Response({
                'success': True,
                'data': formatted_banks,
                'total': len(formatted_banks),
                'sandbox_mode': pluggy.use_sandbox,
                'has_open_finance': any(bank['isOpenFinance'] for bank in formatted_banks)
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
            is_open_finance = request.query_params.get('isOpenFinance')
            
            # Convert string to boolean
            if is_open_finance is not None:
                is_open_finance = is_open_finance.lower() == 'true'
            
            # Get connectors
            connectors = pluggy.get_connectors(
                country=country,
                type=connector_type,
                sandbox=sandbox.lower() == 'true' if sandbox else None,
                is_open_finance=is_open_finance
            )
            
            # Filter and format for frontend
            formatted_connectors = []
            for connector in connectors:
                # Skip if not a bank connector
                if connector.get('type') not in ['PERSONAL_BANK', 'BUSINESS_BANK']:
                    continue
                    
                formatted_connectors.append({
                    'id': connector['id'],
                    'name': connector['name'],
                    'displayName': f"[OF] {connector['name']}" if connector.get('isOpenFinance') else connector['name'],
                    'institutionUrl': connector.get('institutionUrl', ''),
                    'imageUrl': connector.get('imageUrl', ''),
                    'primaryColor': connector.get('primaryColor', '#000000'),
                    'country': connector.get('country', 'BR'),
                    'type': connector['type'],
                    'sandbox': connector.get('sandbox', False),
                    'oauth': connector.get('oauth', False),
                    'openFinance': connector.get('isOpenFinance', False),
                    'isOpenFinance': connector.get('isOpenFinance', False),
                    'products': connector.get('products', []),
                    'credentials': connector.get('credentials', [])
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
            
            # Check if it's Open Finance
            connector = item.get('connector', {})
            is_open_finance = connector.get('isOpenFinance', False)
            logger.info(f"Is Open Finance connector: {is_open_finance}")
            
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
            
            # Get additional data if Open Finance
            identity_data = None
            if is_open_finance:
                try:
                    identity_data = pluggy.get_identity(item_id)
                    logger.info(f"Got identity data for Open Finance: {identity_data}")
                except Exception as e:
                    logger.warning(f"Could not get identity data: {e}")
            
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
                    provider, _ = BankProvider.objects.get_or_create(
                        code=str(connector.get('id')),
                        defaults={
                            'name': connector.get('name', 'Unknown Bank'),
                            'logo_url': connector.get('imageUrl', ''),
                            'primary_color': connector.get('primaryColor', '#000000'),
                            'api_endpoint': '',  # Not used with Pluggy
                            'is_active': True,
                            'is_open_finance': is_open_finance
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
                    
                    # Prepare metadata with Open Finance specific data
                    metadata = {
                        'owner': account_data.get('owner', ''),
                        'subtype': account_data.get('subtype', ''),
                        'bank_data': account_data.get('bankData', {}),
                        'created_at': account_data.get('createdAt', ''),
                        'updated_at': account_data.get('updatedAt', ''),
                        'is_open_finance': is_open_finance
                    }
                    
                    # Add credit card specific data if available
                    if account_data.get('creditData'):
                        metadata['credit_data'] = account_data['creditData']
                    
                    # Add identity data if available
                    if identity_data:
                        metadata['identity'] = identity_data
                    
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
                                'metadata': metadata
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
                            bank_account.metadata = metadata
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
                    'item_id': item_id,
                    'is_open_finance': is_open_finance
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
            'CREDIT': 'credit_card',
            'CREDIT_CARD': 'credit_card',
            'INVESTMENT': 'investment',
            'LOAN': 'loan',
            'OTHER': 'other'
        }
        return type_mapping.get(pluggy_type, 'checking')
    
    def _sync_transactions(self, bank_account: BankAccount, pluggy: PluggyClient):
        """
        Sync transactions for a bank account
        """
        try:
            # Get transactions for the last 90 days (365 for Open Finance)
            is_open_finance = bank_account.metadata.get('is_open_finance', False)
            days_back = 365 if is_open_finance else 90
            
            from_date = timezone.now() - timedelta(days=days_back)
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
                    try:
                        created = self._process_transaction(bank_account, trans_data)
                        if created:
                            total_created += 1
                        else:
                            total_updated += 1
                    except Exception as e:
                        logger.error(f"Error processing transaction {trans_data.get('id', 'unknown')}: {e}")
                        logger.error(f"Transaction data: {trans_data}")
                        continue
                
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
        
        # CORREÇÃO: Tratar merchant de forma segura
        merchant_data = trans_data.get('merchant')
        merchant_name = ''
        if merchant_data and isinstance(merchant_data, dict):
            merchant_name = merchant_data.get('name', '')
        
        # Handle payment data for Open Finance
        payment_data = trans_data.get('paymentData', {})
        metadata = {
            'pluggy_category': trans_data.get('category'),
            'payment_method': trans_data.get('paymentMethod'),
            'merchant': merchant_data,
            'operation_type': trans_data.get('operationType'),
            'provider_id': trans_data.get('providerId')
        }
        
        # Add payment data details
        if payment_data:
            metadata['payment_data'] = payment_data
            # Extract counterpart name from payment data if available
            if payment_data.get('receiver', {}).get('name'):
                merchant_name = payment_data['receiver']['name']
            elif payment_data.get('payer', {}).get('name'):
                merchant_name = payment_data['payer']['name']
        
        # Create or update transaction
        transaction_obj, created = Transaction.objects.update_or_create(
            external_id=trans_data['id'],
            bank_account=bank_account,
            defaults={
                'transaction_type': transaction_type,
                'amount': amount,
                'description': trans_data.get('description', '')[:500],
                'transaction_date': transaction_date,
                'counterpart_name': merchant_name[:200],
                'category': category,
                'status': 'completed' if trans_data.get('status') == 'POSTED' else 'pending',
                'metadata': metadata
            }
        )
        
        return created

    def _map_transaction_type(self, trans_data: Dict) -> str:
        """
        Map Pluggy transaction type to our internal types
        """
        # For Open Finance, check operationType first
        operation_type = trans_data.get('operationType')
        if operation_type:
            operation_map = {
                'PIX': 'pix_in' if trans_data.get('type') == 'CREDIT' else 'pix_out',
                'TED': 'transfer_in' if trans_data.get('type') == 'CREDIT' else 'transfer_out',
                'DOC': 'transfer_in' if trans_data.get('type') == 'CREDIT' else 'transfer_out',
                'TRANSFERENCIA_MESMA_INSTITUICAO': 'transfer_in' if trans_data.get('type') == 'CREDIT' else 'transfer_out',
                'BOLETO': 'debit',
                'CARTAO': 'debit',
                'DEPOSITO': 'credit',
                'SAQUE': 'debit'
            }
            if operation_type in operation_map:
                return operation_map[operation_type]
        
        # Fall back to original logic
        amount = trans_data.get('amount', 0)
        payment_method = trans_data.get('paymentMethod')
        pluggy_type = trans_data.get('type')
        
        # Determine type based on amount and payment method
        if pluggy_type == 'CREDIT' or amount > 0:
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
            
            # Check if it's Open Finance
            is_open_finance = account.metadata.get('is_open_finance', False)
            
            # Get rate limit info if Open Finance
            rate_limit_info = None
            if is_open_finance and account.pluggy_item_id:
                try:
                    pluggy = PluggyClient()
                    item = pluggy.get_item(account.pluggy_item_id)
                    status_detail = item.get('statusDetail', {})
                    
                    # Check for rate limit warnings
                    for product, details in status_detail.items():
                        if isinstance(details, dict) and details.get('warnings'):
                            for warning in details['warnings']:
                                if 'rate limit' in str(warning).lower():
                                    rate_limit_info = {
                                        'product': product,
                                        'warning': str(warning)
                                    }
                                    break
                except Exception as e:
                    logger.warning(f"Could not check rate limits: {e}")
            
            response_data = {
                'id': account.id,
                'status': account.status,
                'sync_status': account.sync_status,
                'last_sync_at': account.last_sync_at.isoformat() if account.last_sync_at else None,
                'sync_error_message': account.sync_error_message,
                'current_balance': float(account.current_balance),
                'available_balance': float(account.available_balance),
                'transaction_count': account.transactions.count(),
                'is_open_finance': is_open_finance,
                'rate_limit_info': rate_limit_info
            }
            
            return Response(response_data)
            
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
            is_open_finance = account.metadata.get('is_open_finance', False)

            # Check item status BEFORE trying to update
            item = pluggy.get_item(account.pluggy_item_id)
            item_status = item.get('status')
            execution_status = item.get('executionStatus')
            
            logger.info(f"Item status: {item_status}")
            logger.info(f"Execution status: {execution_status}")
            logger.info(f"Status detail: {json.dumps(item.get('statusDetail'), indent=2)}")
            logger.info(f"Last updated: {item.get('lastUpdatedAt')}")
            
            # Check for rate limits (Open Finance)
            if is_open_finance and item.get('statusDetail'):
                for product, details in item['statusDetail'].items():
                    if isinstance(details, dict) and details.get('warnings'):
                        for warning in details['warnings']:
                            if '423' in str(warning.get('code', '')) or 'rate limit' in str(warning).lower():
                                logger.warning(f"Rate limit reached for {product}")
                                return Response({
                                    'success': False,
                                    'error_code': 'RATE_LIMIT',
                                    'message': f'Limite de requisições mensais atingido para {product}. Tente novamente no próximo mês.',
                                    'data': {
                                        'product': product,
                                        'warning': str(warning)
                                    }
                                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Check if MFA is required or USER_INPUT_TIMEOUT
            if execution_status == 'USER_INPUT_TIMEOUT' or item_status == 'WAITING_USER_INPUT':
                logger.warning(f"Item {account.pluggy_item_id} requires user authentication (status: {item_status}, execution: {execution_status})")
                return Response({
                    'success': False,
                    'error_code': 'MFA_REQUIRED',
                    'message': 'Esta conta precisa ser reconectada para continuar sincronizando.',
                    'reconnection_required': True,
                    'data': {
                        'item_id': account.pluggy_item_id,
                        'status': item_status,
                        'execution_status': execution_status
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check for login errors
            if item_status == 'LOGIN_ERROR':
                logger.warning(f"Item {account.pluggy_item_id} has login error")
                return Response({
                    'success': False,
                    'error_code': 'LOGIN_ERROR',
                    'message': 'Credenciais inválidas. Por favor, reconecte a conta.',
                    'reconnection_required': True,
                    'data': {
                        'item_id': account.pluggy_item_id,
                        'status': item_status
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check for PARTIAL_SUCCESS with specific details
            if item_status == 'UPDATED' and execution_status == 'PARTIAL_SUCCESS':
                logger.info(f"Item {account.pluggy_item_id} has PARTIAL_SUCCESS, checking details...")
                status_detail = item.get('statusDetail', {})
                transactions_detail = status_detail.get('transactions', {})
                
                # Log all status details for debugging
                logger.info(f"Transactions detail: {json.dumps(transactions_detail, indent=2)}")
                
                # If transactions were not updated, it might need reconnection
                if not transactions_detail.get('isUpdated', False):
                    logger.warning("Transactions were not updated in PARTIAL_SUCCESS")
                    
                    # Check if it's because of authentication issues
                    warnings = transactions_detail.get('warnings', [])
                    needs_reconnection = any(
                        'auth' in str(w).lower() or 
                        'login' in str(w).lower() or 
                        'session' in str(w).lower() 
                        for w in warnings
                    )
                    
                    if needs_reconnection:
                        return Response({
                            'success': False,
                            'error_code': 'MFA_REQUIRED',
                            'message': 'A sincronização das transações requer nova autenticação.',
                            'reconnection_required': True,
                            'data': {
                                'item_id': account.pluggy_item_id,
                                'status': item_status,
                                'execution_status': execution_status
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    logger.info("Transactions were updated successfully despite PARTIAL_SUCCESS")
            
            # Check if item is outdated
            if item_status == 'OUTDATED':
                logger.info(f"Item {account.pluggy_item_id} is outdated, attempting sync anyway")
                # Continue with sync but warn that data might be stale
            
            # If status is OK or OUTDATED, proceed with update
            logger.info(f"Triggering update for item {account.pluggy_item_id}")
            
            try:
                update_result = pluggy.update_item(account.pluggy_item_id)
                logger.info(f"Update result: {json.dumps(update_result, indent=2)}")
            except Exception as update_error:
                logger.error(f"Error updating item: {update_error}")
                # If update fails, continue with existing data
                update_result = None
            
            # Wait a moment for the update to start
            import time
            time.sleep(3)  # Increased wait time for better stability
            
            # Check status after update
            updated_item = pluggy.get_item(account.pluggy_item_id)
            new_status = updated_item.get('status')
            new_execution_status = updated_item.get('executionStatus')
            
            logger.info(f"Status after update: {new_status}, execution: {new_execution_status}")
            
            # If it went to WAITING_USER_INPUT after update
            if new_status == 'WAITING_USER_INPUT' or new_execution_status == 'WAITING_USER_ACTION':
                logger.warning(f"Item now requires user input after update attempt")
                return Response({
                    'success': False,
                    'error_code': 'MFA_REQUIRED',
                    'message': 'A sincronização requer autenticação adicional. Por favor, reconecte a conta.',
                    'reconnection_required': True,
                    'data': {
                        'item_id': account.pluggy_item_id,
                        'status': new_status,
                        'execution_status': new_execution_status
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize sync statistics
            sync_stats = {
                'transactions_synced': 0,
                'sync_from': None,
                'sync_to': None,
                'days_searched': 0,
                'status': new_status,
                'execution_status': new_execution_status,
                'is_open_finance': is_open_finance
            }
            
            # Get updated account info
            try:
                accounts_response = pluggy.get_accounts(account.pluggy_item_id)
                
                # Handle different response formats
                if isinstance(accounts_response, dict):
                    accounts = accounts_response.get('results', accounts_response.get('data', []))
                elif isinstance(accounts_response, list):
                    accounts = accounts_response
                else:
                    accounts = []
                
                # Update account balance
                for acc_data in accounts:
                    if acc_data['id'] == account.external_id:
                        # Update balance
                        account.current_balance = Decimal(str(acc_data.get('balance', 0)))
                        account.available_balance = Decimal(str(acc_data.get('balance', 0)))
                        account.last_sync_at = timezone.now()
                        account.save()
                        logger.info(f"Updated balance: {account.current_balance}")
                        break
                        
            except Exception as e:
                logger.error(f"Error updating account info: {e}")
            
            # Sync recent transactions only if item is in a good state
            if new_status in ['UPDATED', 'PARTIAL_SUCCESS'] or (new_status == 'OUTDATED' and new_execution_status != 'ERROR'):
                try:
                    # Determine sync period based on status and connector type
                    if new_status == 'OUTDATED':
                        # For outdated items, try smaller window
                        from_date = timezone.now() - timedelta(days=3)
                    elif is_open_finance:
                        # Open Finance: check last 30 days
                        from_date = timezone.now() - timedelta(days=30)
                    else:
                        # Normal sync window
                        from_date = timezone.now() - timedelta(days=7)
                    
                    to_date = timezone.now()
                    
                    sync_stats['sync_from'] = from_date.isoformat()
                    sync_stats['sync_to'] = to_date.isoformat()
                    sync_stats['days_searched'] = (to_date - from_date).days
                    
                    # Count transactions before sync
                    before_count = account.transactions.count()
                    
                    # Use the callback view's sync method
                    callback_view = PluggyCallbackView()
                    callback_view._sync_transactions(account, pluggy)
                    
                    # Count transactions after sync
                    after_count = account.transactions.count()
                    sync_stats['transactions_synced'] = after_count - before_count
                    
                    logger.info(f"Synced {sync_stats['transactions_synced']} new transactions")
                    
                except Exception as e:
                    logger.error(f"Error syncing transactions: {e}")
                    sync_stats['sync_error'] = str(e)
            else:
                logger.warning(f"Skipping transaction sync due to item status: {new_status}")
                sync_stats['sync_skipped'] = True
                sync_stats['skip_reason'] = f'Item status {new_status} not suitable for sync'
            
            # Prepare response
            response_data = {
                'success': True,
                'message': 'Sincronização concluída',
                'data': {
                    'account': BankAccountSerializer(account).data,
                    'sync_stats': sync_stats,
                    'item_status': new_status,
                    'execution_status': new_execution_status
                }
            }
            
            # Add warnings if needed
            if new_status == 'OUTDATED':
                response_data['warning'] = 'A conexão com o banco está desatualizada. Alguns dados podem não estar completos.'
            elif sync_stats.get('transactions_synced', 0) == 0:
                response_data['info'] = 'Nenhuma transação nova encontrada no período.'
            
            return Response(response_data)
            
        except BankAccount.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'error': 'Account not found',
                    'message': 'Conta não encontrada'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Failed to sync account: {e}", exc_info=True)
            
            # Check if it's a Pluggy API error about MFA/authentication
            error_message = str(e).lower()
            if any(keyword in error_message for keyword in ['waiting', 'user', 'action', 'auth', 'session', 'timeout']):
                return Response({
                    'success': False,
                    'error_code': 'MFA_REQUIRED',
                    'message': 'Esta conta requer autenticação adicional.',
                    'reconnection_required': True,
                    'data': {
                        'item_id': account.pluggy_item_id if account else None
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(
                {
                    'success': False,
                    'error': str(e),
                    'message': f'Erro ao sincronizar: {str(e)}'
                },
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
            elif event_type == 'consent.revoked':
                self._handle_consent_revoked(data)
            
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
    
    def _handle_consent_revoked(self, data: Dict):
        """
        Handle Open Finance consent revoked event
        """
        item_id = data.get('id')
        if not item_id:
            return
            
        # Mark accounts as needing reconnection
        accounts = BankAccount.objects.filter(pluggy_item_id=item_id)
        
        for account in accounts:
            account.status = 'consent_revoked'
            account.sync_error_message = 'Consentimento revogado no Open Finance'
            account.save()
            
            logger.info(f"Consent revoked for account {account}")


class PluggyOpenFinanceInfoView(APIView):
    """
    Get information about Open Finance connectors and rate limits
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get Open Finance information
        """
        try:
            pluggy = PluggyClient()
            
            # Get Open Finance connectors
            of_connectors = pluggy.get_connectors(is_open_finance=True)
            
            # Format connector info
            connector_info = []
            for connector in of_connectors:
                connector_info.append({
                    'id': connector['id'],
                    'name': connector['name'],
                    'type': connector['type'],
                    'products': connector.get('products', []),
                    'imageUrl': connector.get('imageUrl', '')
                })
            
            # Rate limit information
            rate_limits = {
                'accounts': {
                    'list': 4,
                    'balance': 420,
                    'period': 'monthly',
                    'description': 'Lista de contas e saldos'
                },
                'credit_cards': {
                    'list': 4,
                    'bills': 30,
                    'limits': 240,
                    'period': 'monthly',
                    'description': 'Cartões de crédito, faturas e limites'
                },
                'transactions': {
                    'recent': 240,
                    'historical': 4,
                    'period': 'monthly',
                    'description': 'Transações recentes (1-6 dias) e históricas (7-365 dias)'
                },
                'identity': {
                    'requests': 4,
                    'period': 'monthly',
                    'description': 'Dados de identidade'
                },
                'investments': {
                    'list': 120,
                    'detail': 4,
                    'balance': 120,
                    'period': 'monthly',
                    'description': 'Investimentos, detalhes e saldos'
                },
                'loans': {
                    'requests': 4,
                    'period': 'monthly',
                    'description': 'Empréstimos e financiamentos'
                }
            }
            
            return Response({
                'success': True,
                'data': {
                    'connectors': connector_info,
                    'total_connectors': len(connector_info),
                    'rate_limits': rate_limits,
                    'info': {
                        'description': 'Open Finance Brasil permite acesso regulado aos dados bancários',
                        'requires_cpf_cnpj': True,
                        'consent_duration': '12 meses',
                        'data_retention': '365 dias de histórico'
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to get Open Finance info: {e}")
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )