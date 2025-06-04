"""
Simple Pluggy views for testing
"""
import logging
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

logger = logging.getLogger(__name__)


@method_decorator(ratelimit(key='user', rate='10/m', method='GET'), name='dispatch')
class PluggyBankProvidersView(APIView):
    """Get available banks from Pluggy"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get list of banks supported by Pluggy"""
        # Mock response for now
        mock_banks = [
            {
                'id': 1,
                'name': 'Banco do Brasil',
                'code': '001',
                'health_status': 'ONLINE'
            },
            {
                'id': 2, 
                'name': 'Itaú',
                'code': '341',
                'health_status': 'ONLINE'
            }
        ]
        
        return Response({
            'success': True,
            'data': mock_banks,
            'total': len(mock_banks)
        })


@method_decorator(ratelimit(key='user', rate='5/m', method='POST'), name='dispatch')
class PluggyConnectTokenView(APIView):
    """Create Pluggy Connect token for bank connection"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Create a connect token for Pluggy Connect widget"""
        return Response({
            'success': True,
            'data': {
                'connect_token': 'mock-token-123',
                'connect_url': 'https://connect.pluggy.ai',
                'expires_at': '2024-01-01T00:00:00Z',
            }
        })


class PluggyItemCallbackView(APIView):
    """Handle Pluggy item creation callback"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Process successful bank connection from Pluggy Connect"""
        return Response({
            'success': True,
            'data': {
                'accounts': [],
                'message': 'Bank connection successful (mock)'
            }
        })


def pluggy_webhook(request):
    """Handle Pluggy webhooks for real-time updates"""
    return Response({'status': 'received'}, status=status.HTTP_200_OK)


class PluggySyncAccountView(APIView):
    """Manually trigger account sync"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, account_id):
        """Manually sync a specific account"""
        return Response({
            'success': True,
            'data': {
                'transactions_synced': 0,
                'message': 'Sync completed (mock)'
            }
        })


class PluggyDisconnectAccountView(APIView):
    """Disconnect a Pluggy account"""
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, account_id):
        """Disconnect account from Pluggy"""
        return Response({
            'success': True,
            'message': 'Account disconnected successfully'
        })


class PluggyAccountStatusView(APIView):
    """Get Pluggy account connection status"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, account_id):
        """Get real-time status of Pluggy account"""
        return Response({
            'success': True,
            'data': {
                'account_id': account_id,
                'status': 'active',
                'last_sync': None,
                'balance': '0.00'
            }
        })