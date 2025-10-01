"""
Subscription signals for tracking trial usage
"""
from django.dispatch import receiver
from djstripe import signals
from djstripe.models import Customer
from .models import TrialUsageTracking
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@receiver(signals.WEBHOOK_SIGNALS["customer.subscription.created"])
def track_trial_on_subscription_created(sender, event, **kwargs):
    """
    Mark trial as used when subscription is created with trial
    """
    try:
        subscription_data = event.data.get('object', {})

        if subscription_data.get('trial_end'):
            customer_id = subscription_data.get('customer')
            customer = Customer.objects.filter(id=customer_id).first()

            if customer and customer.subscriber:
                tracking, created = TrialUsageTracking.objects.get_or_create(
                    user=customer.subscriber
                )

                if not tracking.has_used_trial:
                    tracking.has_used_trial = True
                    tracking.first_trial_at = timezone.now()
                    tracking.save()
                    logger.info(f"Trial tracked via webhook for user {customer.subscriber.id}")

    except Exception as e:
        logger.error(f"Error tracking trial in webhook: {str(e)}")
