"""
Pluggy-specific views for bank connection and management
"""
import logging
from typing import Dict, Any

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from .models import BankAccount, BankProvider
from .pluggy_client import pluggy_service, PluggyError
from .pluggy_sync_service import pluggy_sync_service
from .serializers import BankAccountSerializer, BankProviderSerializer

logger = logging.getLogger(__name__)


@method_decorator(ratelimit(key='user', rate='10/m', method='GET'), name='dispatch')
class PluggyBankProvidersView(APIView):
    """Get available banks from Pluggy"""
    permission_classes = [permissions.IsAuthenticated]
    
    async def get(self, request):
        """Get list of banks supported by Pluggy"""
        try:
            banks = await pluggy_service.get_supported_banks()
            
            # Filter for active banks only
            active_banks = [
                bank for bank in banks 
                if bank.get('health_status') in ['ONLINE', 'UNSTABLE']
            ]
            
            return Response({
                'success': True,
                'data': active_banks,
                'total': len(active_banks)
            })
            
        except Exception as e:
            logger.error(f"Error getting Pluggy banks: {e}")
            return Response({
                'success': False,
                'error': 'Failed to fetch available banks'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@method_decorator(ratelimit(key='user', rate='5/m', method='POST'), name='dispatch')
class PluggyConnectTokenView(APIView):
    """Create Pluggy Connect token for bank connection"""
    permission_classes = [permissions.IsAuthenticated]
    
    async def post(self, request):
        """Create a connect token for Pluggy Connect widget"""
        try:
            # Optional: specify item_id for reconnection
            item_id = request.data.get('item_id')\n            \n            connect_data = await pluggy_service.client.create_connect_token(item_id)\n            \n            return Response({\n                'success': True,\n                'data': {\n                    'connect_token': connect_data['accessToken'],\n                    'connect_url': settings.PLUGGY_CONNECT_URL,\n                    'expires_at': connect_data.get('expiresAt'),\n                }\n            })\n            \n        except PluggyError as e:\n            logger.error(f\"Pluggy error creating connect token: {e}\")\n            return Response({\n                'success': False,\n                'error': 'Failed to create bank connection token'\n            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)\n        except Exception as e:\n            logger.error(f\"Error creating Pluggy connect token: {e}\")\n            return Response({\n                'success': False,\n                'error': 'An unexpected error occurred'\n            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(ratelimit(key='user', rate='10/h', method='POST'), name='dispatch')
class PluggyItemCallbackView(APIView):\n    \"\"\"Handle Pluggy item creation callback\"\"\"\n    permission_classes = [permissions.IsAuthenticated]\n    \n    async def post(self, request):\n        \"\"\"Process successful bank connection from Pluggy Connect\"\"\"\n        try:\n            item_id = request.data.get('item_id')\n            connector_name = request.data.get('connector_name', 'Unknown Bank')\n            \n            if not item_id:\n                return Response({\n                    'success': False,\n                    'error': 'item_id is required'\n                }, status=status.HTTP_400_BAD_REQUEST)\n            \n            company = request.user.company\n            \n            # Connect accounts from the item\n            accounts = await pluggy_sync_service.connect_bank_account(\n                company.id, item_id, connector_name\n            )\n            \n            if not accounts:\n                return Response({\n                    'success': False,\n                    'error': 'No accounts found for this connection'\n                }, status=status.HTTP_404_NOT_FOUND)\n            \n            # Trigger initial sync\n            for account in accounts:\n                try:\n                    await pluggy_sync_service.sync_account_transactions(account)\n                except Exception as e:\n                    logger.warning(f\"Initial sync failed for account {account.id}: {e}\")\n            \n            # Serialize accounts for response\n            serialized_accounts = BankAccountSerializer(accounts, many=True).data\n            \n            return Response({\n                'success': True,\n                'data': {\n                    'accounts': serialized_accounts,\n                    'message': f'Successfully connected {len(accounts)} account(s) from {connector_name}'\n                }\n            })\n            \n        except PluggyError as e:\n            logger.error(f\"Pluggy error in callback: {e}\")\n            return Response({\n                'success': False,\n                'error': 'Bank connection failed. Please try again.'\n            }, status=status.HTTP_400_BAD_REQUEST)\n        except Exception as e:\n            logger.error(f\"Error in Pluggy callback: {e}\")\n            return Response({\n                'success': False,\n                'error': 'An unexpected error occurred'\n            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(ratelimit(key='user', rate='20/h', method='POST'), name='dispatch')
class PluggySyncAccountView(APIView):
    \"\"\"Manually trigger account sync\"\"\"\n    permission_classes = [permissions.IsAuthenticated]\n    \n    async def post(self, request, account_id):\n        \"\"\"Manually sync a specific account\"\"\"\n        try:\n            company = request.user.company\n            \n            # Get the account\n            try:\n                account = BankAccount.objects.get(\n                    id=account_id,\n                    company=company,\n                    status='active'\n                )\n            except BankAccount.DoesNotExist:\n                return Response({\n                    'success': False,\n                    'error': 'Account not found'\n                }, status=status.HTTP_404_NOT_FOUND)\n            \n            # Check if it's a Pluggy account\n            if not account.external_account_id:\n                return Response({\n                    'success': False,\n                    'error': 'This account is not connected via Pluggy'\n                }, status=status.HTTP_400_BAD_REQUEST)\n            \n            # Sync the account\n            result = await pluggy_sync_service.sync_account_transactions(account)\n            \n            if result.get('status') == 'success':\n                return Response({\n                    'success': True,\n                    'data': {\n                        'transactions_synced': result.get('transactions', 0),\n                        'message': 'Account synchronized successfully'\n                    }\n                })\n            else:\n                return Response({\n                    'success': False,\n                    'error': result.get('error', 'Sync failed')\n                }, status=status.HTTP_400_BAD_REQUEST)\n            \n        except Exception as e:\n            logger.error(f\"Error syncing Pluggy account {account_id}: {e}\")\n            return Response({\n                'success': False,\n                'error': 'Sync failed'\n            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])\n@permission_classes([permissions.AllowAny])  # Webhook should use API key authentication\ndef pluggy_webhook(request):\n    \"\"\"Handle Pluggy webhooks for real-time updates\"\"\"\n    try:\n        # TODO: Implement webhook signature verification\n        # webhook_signature = request.headers.get('X-Pluggy-Signature')\n        \n        event_type = request.data.get('type')\n        event_data = request.data.get('data', {})\n        \n        logger.info(f\"Received Pluggy webhook: {event_type}\")\n        \n        # Handle different webhook events\n        if event_type == 'item/created':\n            # Item successfully created\n            item_id = event_data.get('id')\n            logger.info(f\"Pluggy item created: {item_id}\")\n            \n        elif event_type == 'item/updated':\n            # Item status updated (e.g., login succeeded, MFA required)\n            item_id = event_data.get('id')\n            status_val = event_data.get('status')\n            logger.info(f\"Pluggy item {item_id} updated: {status_val}\")\n            \n        elif event_type == 'item/error':\n            # Item encountered an error\n            item_id = event_data.get('id')\n            error = event_data.get('error')\n            logger.warning(f\"Pluggy item {item_id} error: {error}\")\n            \n        elif event_type == 'transactions/created':\n            # New transactions available\n            account_id = event_data.get('accountId')\n            if account_id:\n                # Trigger sync for this account\n                # Note: In production, you'd use a task queue\n                logger.info(f\"New transactions for Pluggy account {account_id}\")\n        \n        return Response({'status': 'received'}, status=status.HTTP_200_OK)\n        \n    except Exception as e:\n        logger.error(f\"Error processing Pluggy webhook: {e}\")\n        return Response(\n            {'error': 'Webhook processing failed'}, \n            status=status.HTTP_500_INTERNAL_SERVER_ERROR\n        )


@method_decorator(ratelimit(key='user', rate='5/h', method='DELETE'), name='dispatch')\nclass PluggyDisconnectAccountView(APIView):\n    \"\"\"Disconnect a Pluggy account\"\"\"\n    permission_classes = [permissions.IsAuthenticated]\n    \n    async def delete(self, request, account_id):\n        \"\"\"Disconnect account from Pluggy\"\"\"\n        try:\n            company = request.user.company\n            \n            # Get the account\n            try:\n                account = BankAccount.objects.get(\n                    id=account_id,\n                    company=company\n                )\n            except BankAccount.DoesNotExist:\n                return Response({\n                    'success': False,\n                    'error': 'Account not found'\n                }, status=status.HTTP_404_NOT_FOUND)\n            \n            # Check if it's a Pluggy account\n            if not account.external_account_id:\n                return Response({\n                    'success': False,\n                    'error': 'This account is not connected via Pluggy'\n                }, status=status.HTTP_400_BAD_REQUEST)\n            \n            # Try to delete from Pluggy (if item_id is available)\n            # Note: We need to track item_id separately or derive it\n            try:\n                # In a real implementation, you'd store the item_id with the account\n                # For now, we'll just deactivate locally\n                pass\n            except PluggyError as e:\n                logger.warning(f\"Failed to delete from Pluggy: {e}\")\n            \n            # Deactivate account locally\n            account.status = 'inactive'\n            account.is_active = False\n            account.save()\n            \n            return Response({\n                'success': True,\n                'message': 'Account disconnected successfully'\n            })\n            \n        except Exception as e:\n            logger.error(f\"Error disconnecting Pluggy account {account_id}: {e}\")\n            return Response({\n                'success': False,\n                'error': 'Failed to disconnect account'\n            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(ratelimit(key='user', rate='10/h', method='GET'), name='dispatch')\nclass PluggyAccountStatusView(APIView):\n    \"\"\"Get Pluggy account connection status\"\"\"\n    permission_classes = [permissions.IsAuthenticated]\n    \n    async def get(self, request, account_id):\n        \"\"\"Get real-time status of Pluggy account\"\"\"\n        try:\n            company = request.user.company\n            \n            # Get the account\n            try:\n                account = BankAccount.objects.get(\n                    id=account_id,\n                    company=company\n                )\n            except BankAccount.DoesNotExist:\n                return Response({\n                    'success': False,\n                    'error': 'Account not found'\n                }, status=status.HTTP_404_NOT_FOUND)\n            \n            # Check if it's a Pluggy account\n            if not account.external_account_id:\n                return Response({\n                    'success': False,\n                    'error': 'This account is not connected via Pluggy'\n                }, status=status.HTTP_400_BAD_REQUEST)\n            \n            # Get account status from Pluggy\n            try:\n                account_data = await pluggy_service.client.get_account(account.external_account_id)\n                \n                return Response({\n                    'success': True,\n                    'data': {\n                        'account_id': account.id,\n                        'external_id': account.external_account_id,\n                        'status': account.status,\n                        'last_sync': account.last_sync_at,\n                        'balance': account.current_balance,\n                        'pluggy_status': account_data.get('status', 'unknown'),\n                        'last_update': account_data.get('lastUpdatedAt')\n                    }\n                })\n                \n            except PluggyError as e:\n                logger.error(f\"Error getting Pluggy account status: {e}\")\n                return Response({\n                    'success': True,\n                    'data': {\n                        'account_id': account.id,\n                        'status': account.status,\n                        'last_sync': account.last_sync_at,\n                        'balance': account.current_balance,\n                        'error': 'Could not fetch real-time status'\n                    }\n                })\n            \n        except Exception as e:\n            logger.error(f\"Error getting account status {account_id}: {e}\")\n            return Response({\n                'success': False,\n                'error': 'Failed to get account status'\n            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)