"""
Stripe service helpers for subscription management
"""
import stripe
from django.conf import settings
from djstripe.models import Customer, Subscription, PaymentMethod
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Configure Stripe API
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY if not settings.STRIPE_LIVE_MODE else settings.STRIPE_LIVE_SECRET_KEY


def get_or_create_customer(user) -> Customer:
    """
    Get existing Stripe customer or create a new one
    """
    customer = Customer.objects.filter(subscriber=user).first()

    if not customer:
        # Create customer in Stripe
        stripe_customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.first_name} {user.last_name}".strip() or user.email,
            metadata={
                'user_id': str(user.id),
                'email': user.email,
            }
        )

        # Sync to dj-stripe
        customer = Customer.sync_from_stripe_data(stripe_customer)

        # CRITICAL: Associate customer with user
        customer.subscriber = user
        customer.save()

        logger.info(f"Created and linked Customer {customer.id} to User {user.id}")

    return customer


def create_subscription_with_trial(
    user,
    payment_method_id: str,
    price_id: str,
    trial_days: int = 7
) -> Dict:
    """
    Create a subscription with trial period

    Args:
        user: Django user object
        payment_method_id: Stripe PaymentMethod ID from frontend
        price_id: Stripe Price ID (configured in Stripe Dashboard)
        trial_days: Number of trial days (default: 7)

    Returns:
        Dict with subscription data
    """
    try:
        # Get or create customer
        customer = get_or_create_customer(user)

        # Attach payment method to customer
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer.id,
        )

        # Set as default payment method
        stripe.Customer.modify(
            customer.id,
            invoice_settings={
                'default_payment_method': payment_method_id,
            },
        )

        # Create subscription with trial
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': price_id}],
            trial_period_days=trial_days,
            payment_behavior='default_incomplete',
            payment_settings={
                'save_default_payment_method': 'on_subscription'
            },
            expand=['latest_invoice.payment_intent'],
        )

        # Sync to dj-stripe
        dj_subscription = Subscription.sync_from_stripe_data(subscription)

        return {
            'success': True,
            'subscription_id': subscription.id,
            'status': subscription.status,
            'trial_end': subscription.trial_end,
            'current_period_end': subscription.current_period_end,
            'client_secret': subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None,
        }

    except stripe.error.CardError as e:
        logger.error(f"Card error creating subscription: {e.user_message}")
        return {
            'success': False,
            'error': e.user_message,
            'error_code': e.code,
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating subscription: {str(e)}")
        return {
            'success': False,
            'error': 'Erro ao processar pagamento. Tente novamente.',
        }
    except Exception as e:
        logger.error(f"Unexpected error creating subscription: {str(e)}")
        return {
            'success': False,
            'error': 'Erro inesperado. Contate o suporte.',
        }


def get_subscription_status(user) -> Optional[Dict]:
    """
    Get user's subscription status and details
    """
    try:
        # Get most recent active/trialing subscription first
        subscription = Subscription.objects.filter(
            customer__subscriber=user,
            status__in=['active', 'trialing', 'past_due']
        ).order_by('-created').first()

        # Fallback to any subscription if no active one found
        if not subscription:
            subscription = Subscription.objects.filter(
                customer__subscriber=user
            ).order_by('-created').first()

        if not subscription:
            return None

        # Calculate days until renewal/trial end
        from datetime import datetime

        if subscription.status == 'trialing' and subscription.trial_end:
            days_left = (subscription.trial_end - datetime.now(subscription.trial_end.tzinfo)).days
            period_end = subscription.trial_end
        else:
            days_left = (subscription.current_period_end - datetime.now(subscription.current_period_end.tzinfo)).days if subscription.current_period_end else None
            period_end = subscription.current_period_end

        # Get payment method
        payment_method = None
        if subscription.default_payment_method:
            pm = subscription.default_payment_method
            payment_method = {
                'last4': pm.card.get('last4') if pm.card else None,
                'brand': pm.card.get('brand') if pm.card else None,
            }

        return {
            'status': subscription.status,
            'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None,
            'current_period_end': period_end.isoformat() if period_end else None,
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'canceled_at': subscription.canceled_at.isoformat() if subscription.canceled_at else None,
            'days_until_renewal': days_left,
            'amount': float(subscription.plan.amount) if subscription.plan else 0,  # plan.amount já está em decimal
            'currency': subscription.plan.currency.upper() if subscription.plan else 'BRL',
            'payment_method': payment_method,
        }

    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        return None


def create_customer_portal_session(user, return_url: str) -> Optional[str]:
    """
    Create a Stripe Customer Portal session for subscription management

    Args:
        user: Django user object
        return_url: URL to return to after portal session

    Returns:
        Portal session URL or None if error
    """
    try:
        customer = Customer.objects.filter(subscriber=user).first()

        if not customer:
            logger.error(f"No customer found for user {user.id}")
            return None

        session = stripe.billing_portal.Session.create(
            customer=customer.id,
            return_url=return_url,
        )

        return session.url

    except Exception as e:
        logger.error(f"Error creating portal session: {str(e)}")
        return None


def cancel_subscription(user, at_period_end: bool = True) -> Dict:
    """
    Cancel user's subscription

    Args:
        user: Django user object
        at_period_end: If True, cancel at end of billing period. If False, cancel immediately.

    Returns:
        Dict with cancellation result
    """
    try:
        subscription = Subscription.objects.filter(
            customer__subscriber=user,
            status__in=['active', 'trialing']
        ).first()

        if not subscription:
            return {
                'success': False,
                'error': 'No active subscription found'
            }

        if at_period_end:
            # Cancel at period end
            updated_subscription = stripe.Subscription.modify(
                subscription.id,
                cancel_at_period_end=True
            )
        else:
            # Cancel immediately
            updated_subscription = stripe.Subscription.cancel(subscription.id)

        # Sync to dj-stripe
        Subscription.sync_from_stripe_data(updated_subscription)

        return {
            'success': True,
            'canceled_at_period_end': updated_subscription.cancel_at_period_end,
            'ended_at': updated_subscription.ended_at,
        }

    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
