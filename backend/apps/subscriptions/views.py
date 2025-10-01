"""
Subscription API views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import stripe
import logging

from .services import (
    get_subscription_status,
    create_customer_portal_session,
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    """
    Create a Stripe Checkout Session for subscription with trial

    Request body:
    {
        "success_url": "https://yourapp.com/checkout/success",  # Optional
        "cancel_url": "https://yourapp.com/checkout/cancel"     # Optional
    }

    Returns:
    {
        "checkout_url": "https://checkout.stripe.com/..."
    }
    """
    try:
        from .services import get_or_create_customer
        from .models import TrialUsageTracking
        from djstripe.models import Subscription
        from django.utils import timezone

        # Get URLs from request or use defaults
        success_url = request.data.get('success_url', f"{settings.FRONTEND_URL}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}")
        cancel_url = request.data.get('cancel_url', f"{settings.FRONTEND_URL}/checkout/cancel")

        # Get or create Stripe customer
        customer = get_or_create_customer(request.user)

        # Get price ID
        price_id = request.data.get('price_id', getattr(settings, 'STRIPE_DEFAULT_PRICE_ID', None))

        if not price_id:
            return Response(
                {'error': 'STRIPE_DEFAULT_PRICE_ID must be configured in settings'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user is eligible for trial
        trial_tracking, _ = TrialUsageTracking.objects.get_or_create(user=request.user)
        has_past_subscriptions = Subscription.objects.filter(customer=customer).exists()

        # Trial eligibility: no previous trials AND no past subscriptions
        trial_days = 7 if (not trial_tracking.has_used_trial and not has_past_subscriptions) else 0

        # DON'T mark trial as used here - let webhook handle it to avoid race condition

        # Create Checkout Session
        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            mode='subscription',
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            subscription_data={
                'trial_period_days': trial_days,
                'metadata': {
                    'user_id': str(request.user.id),
                    'trial_eligible': str(trial_days > 0),
                },
            },
            success_url=success_url,
            cancel_url=cancel_url,
            allow_promotion_codes=True,
            billing_address_collection='auto',
            phone_number_collection={
                'enabled': True,
            },
            locale='pt-BR',
        )

        return Response({
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in create_checkout_session: {str(e)}")
        return Response(
            {'error': 'Erro ao criar sessão de checkout'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_status(request):
    """
    Get current user's subscription status and details
    """
    try:
        subscription_data = get_subscription_status(request.user)

        if subscription_data:
            # Handle incomplete/unpaid status
            if subscription_data['status'] in ['incomplete', 'incomplete_expired', 'unpaid']:
                return Response({
                    **subscription_data,
                    'requires_action': True,
                    'message': 'Pagamento requer ação adicional'
                }, status=status.HTTP_200_OK)

            return Response(subscription_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {'status': 'none', 'message': 'No subscription found'},
                status=status.HTTP_200_OK
            )

    except Exception as e:
        logger.error(f"Error in subscription_status: {str(e)}")
        return Response(
            {'error': 'Erro ao buscar status da assinatura'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_portal_session(request):
    """
    Create Stripe Customer Portal session for subscription management

    Request body:
    {
        "return_url": "https://yourapp.com/settings"
    }
    """
    try:
        return_url = request.data.get('return_url', f"{settings.FRONTEND_URL}/settings")

        portal_url = create_customer_portal_session(
            user=request.user,
            return_url=return_url
        )

        if portal_url:
            return Response(
                {'url': portal_url},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Unable to create portal session'},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Error in create_portal_session: {str(e)}")
        return Response(
            {'error': 'Erro ao criar sessão do portal'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stripe_config(request):
    """
    Return Stripe publishable key for frontend
    """
    return Response({
        'publishable_key': settings.STRIPE_TEST_PUBLIC_KEY if not settings.STRIPE_LIVE_MODE else settings.STRIPE_LIVE_PUBLIC_KEY
    })
