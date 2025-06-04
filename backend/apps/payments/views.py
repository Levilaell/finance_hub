"""
Payment webhook views
"""
import logging
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .payment_service import PaymentService

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])  # Webhooks don't use auth
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    try:
        payment_service = PaymentService(gateway_name='stripe')
        result = payment_service.handle_webhook(request)
        
        logger.info(f"Stripe webhook processed: {result['event_type']}")
        return Response({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])  # Webhooks don't use auth
def mercadopago_webhook(request):
    """Handle MercadoPago webhooks"""
    try:
        payment_service = PaymentService(gateway_name='mercadopago')
        result = payment_service.handle_webhook(request)
        
        logger.info(f"MercadoPago webhook processed: {result['event_type']}")
        return Response({'status': 'success'})
        
    except Exception as e:
        logger.error(f"MercadoPago webhook error: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )