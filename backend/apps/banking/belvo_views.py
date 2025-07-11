"""
Belvo integration views
Handles Belvo API connections and data synchronization
"""
import logging
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .belvo_client import BelvoClient
from .models import BankConnection, BankAccount
from .serializers import BankConnectionSerializer

logger = logging.getLogger(__name__)


class BelvoConnectionView(APIView):
    """
    Manage Belvo bank connections
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all connections for the user's company"""
        try:
            connections = BankConnection.objects.filter(
                company=request.user.company
            )
            serializer = BankConnectionSerializer(connections, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'count': connections.count()
            })
            
        except Exception as e:
            logger.error(f"Error listing Belvo connections: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create a new Belvo connection"""
        try:
            institution = request.data.get('institution')
            username = request.data.get('username')
            password = request.data.get('password')
            
            if not all([institution, username, password]):
                return Response({
                    'success': False,
                    'error': 'Institution, username, and password are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize Belvo client
            belvo_client = BelvoClient()
            
            # Create connection in Belvo
            connection_data = belvo_client.create_link(
                institution=institution,
                username=username,
                password=password
            )
            
            # Create local connection record
            connection = BankConnection.objects.create(
                belvo_id=connection_data['id'],
                institution=connection_data['institution'],
                display_name=connection_data.get('display_name', ''),
                company=request.user.company,
                created_by=request.user,
                status=connection_data['status'],
                last_access_mode=connection_data.get('last_access_mode', 'single'),
                external_id=connection_data.get('external_id', ''),
                credentials_stored=connection_data.get('credentials_stored', False),
                metadata=connection_data
            )
            
            serializer = BankConnectionSerializer(connection)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Connection created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating Belvo connection: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, connection_id):
        """Delete a Belvo connection"""
        try:
            connection = BankConnection.objects.get(
                id=connection_id,
                company=request.user.company
            )
            
            # Delete from Belvo
            belvo_client = BelvoClient()
            belvo_client.delete_link(connection.belvo_id)
            
            # Delete local record
            connection.delete()
            
            return Response({
                'success': True,
                'message': 'Connection deleted successfully'
            })
            
        except BankConnection.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Connection not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting Belvo connection: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BelvoAccountsView(APIView):
    """
    Fetch accounts from Belvo
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all accounts from Belvo connections"""
        try:
            belvo_client = BelvoClient()
            
            # Get all active connections for the company
            connections = BankConnection.objects.filter(
                company=request.user.company,
                status='valid'
            )
            
            if not connections.exists():
                return Response({
                    'success': True,
                    'data': [],
                    'message': 'No active connections found'
                })
            
            all_accounts = []
            
            for connection in connections:
                try:
                    # Fetch accounts from Belvo
                    accounts = belvo_client.get_accounts(connection.belvo_id)
                    
                    for account_data in accounts:
                        # Check if account already exists locally
                        existing_account = BankAccount.objects.filter(
                            external_id=account_data['id']
                        ).first()
                        
                        if not existing_account:
                            # Create new local account
                            bank_provider = None  # You might want to map this
                            
                            account = BankAccount.objects.create(
                                company=request.user.company,
                                bank_provider=bank_provider,
                                account_type=account_data.get('type', 'checking'),
                                account_name=account_data.get('name', ''),
                                account_number=account_data.get('number', ''),
                                agency=account_data.get('agency', ''),
                                current_balance=account_data.get('balance', {}).get('current', 0),
                                available_balance=account_data.get('balance', {}).get('available', 0),
                                external_id=account_data['id'],
                                belvo_connection=connection,
                                metadata=account_data
                            )
                            all_accounts.append(account.to_dict())
                        else:
                            # Update existing account
                            existing_account.current_balance = account_data.get('balance', {}).get('current', 0)
                            existing_account.available_balance = account_data.get('balance', {}).get('available', 0)
                            existing_account.save()
                            all_accounts.append(existing_account.to_dict())
                            
                except Exception as e:
                    logger.error(f"Error fetching accounts for connection {connection.belvo_id}: {e}")
                    continue
            
            return Response({
                'success': True,
                'data': all_accounts,
                'count': len(all_accounts)
            })
            
        except Exception as e:
            logger.error(f"Error fetching Belvo accounts: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BelvoTransactionsView(APIView):
    """
    Fetch transactions from Belvo
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Sync transactions from Belvo"""
        try:
            belvo_client = BelvoClient()
            account_id = request.query_params.get('account_id')
            
            if account_id:
                # Sync specific account
                try:
                    account = BankAccount.objects.get(
                        id=account_id,
                        company=request.user.company
                    )
                    
                    if not account.external_id:
                        return Response({
                            'success': False,
                            'error': 'Account is not connected to Belvo'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Fetch transactions from Belvo
                    transactions = belvo_client.get_transactions(account.external_id)
                    
                    # Process and save transactions
                    sync_results = self._process_transactions(transactions, account)
                    
                    return Response({
                        'success': True,
                        'data': sync_results,
                        'message': f'Synced {sync_results["new_transactions"]} new transactions'
                    })
                    
                except BankAccount.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Account not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Sync all accounts
                accounts = BankAccount.objects.filter(
                    company=request.user.company,
                    external_id__isnull=False
                )
                
                total_results = {
                    'new_transactions': 0,
                    'updated_transactions': 0,
                    'errors': 0
                }
                
                for account in accounts:
                    try:
                        transactions = belvo_client.get_transactions(account.external_id)
                        results = self._process_transactions(transactions, account)
                        
                        total_results['new_transactions'] += results['new_transactions']
                        total_results['updated_transactions'] += results['updated_transactions']
                        
                    except Exception as e:
                        logger.error(f"Error syncing transactions for account {account.id}: {e}")
                        total_results['errors'] += 1
                
                return Response({
                    'success': True,
                    'data': total_results,
                    'message': f'Sync completed. {total_results["new_transactions"]} new transactions'
                })
                
        except Exception as e:
            logger.error(f"Error syncing Belvo transactions: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _process_transactions(self, transactions_data, account):
        """Process and save transactions from Belvo"""
        from .models import Transaction
        from apps.categories.services import AICategorizationService
        
        results = {
            'new_transactions': 0,
            'updated_transactions': 0
        }
        
        ai_service = AICategorizationService()
        
        for transaction_data in transactions_data:
            # Check if transaction already exists
            existing_transaction = Transaction.objects.filter(
                external_id=transaction_data['id']
            ).first()
            
            if not existing_transaction:
                # Create new transaction
                transaction = Transaction.objects.create(
                    bank_account=account,
                    external_id=transaction_data['id'],
                    amount=transaction_data['amount'],
                    description=transaction_data.get('description', ''),
                    transaction_date=transaction_data['value_date'],
                    posted_date=transaction_data.get('accounting_date'),
                    transaction_type='credit' if transaction_data['amount'] > 0 else 'debit',
                    counterpart_name=transaction_data.get('merchant', {}).get('name', ''),
                    counterpart_account=transaction_data.get('account', ''),
                    reference=transaction_data.get('reference', ''),
                    metadata=transaction_data
                )
                
                # Auto-categorize
                try:
                    categorization = ai_service.categorize_transaction(transaction)
                    if categorization and categorization.get('category'):
                        transaction.category = categorization['category']
                        transaction.ai_category_confidence = categorization['confidence']
                        transaction.is_ai_categorized = True
                        transaction.save()
                except Exception as e:
                    logger.error(f"Error categorizing transaction {transaction.id}: {e}")
                
                results['new_transactions'] += 1
            else:
                # Update existing transaction if needed
                results['updated_transactions'] += 1
        
        return results


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def belvo_institutions(request):
    """Get list of supported institutions from Belvo"""
    try:
        belvo_client = BelvoClient()
        institutions = belvo_client.get_institutions()
        
        return Response({
            'success': True,
            'data': institutions
        })
        
    except Exception as e:
        logger.error(f"Error fetching Belvo institutions: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def belvo_refresh_connection(request, connection_id):
    """Refresh a Belvo connection"""
    try:
        connection = BankConnection.objects.get(
            id=connection_id,
            company=request.user.company
        )
        
        belvo_client = BelvoClient()
        
        # Refresh the connection
        updated_connection = belvo_client.refresh_link(connection.belvo_id)
        
        # Update local record
        connection.status = updated_connection['status']
        connection.metadata = updated_connection
        connection.save()
        
        serializer = BankConnectionSerializer(connection)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Connection refreshed successfully'
        })
        
    except BankConnection.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Connection not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error refreshing Belvo connection: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)