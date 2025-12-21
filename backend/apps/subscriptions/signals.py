"""
Subscription signals for tracking trial usage and handling subscription events
"""
from django.dispatch import receiver
from django.db import transaction, OperationalError
from djstripe import signals
from djstripe.models import Customer, Subscription
from djstripe.signals import webhook_processing_error
from .models import TrialUsageTracking, AcquisitionTracking
from django.utils import timezone
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)


def retry_on_deadlock(func, max_retries=3, delay=0.1):
    """
    Retry decorator for handling database deadlocks
    """
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except OperationalError as e:
                error_msg = str(e)
                if 'deadlock' in error_msg.lower() or 'impasse' in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(
                            f"Deadlock in {func.__name__}, retrying in {wait_time}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                raise
        return None
    return wrapper


@receiver(signals.WEBHOOK_SIGNALS["customer.subscription.created"])
def track_trial_on_subscription_created(sender, event, **kwargs):
    """
    Mark trial as used when subscription is created with trial
    Also creates AcquisitionTracking record
    """
    def _track_trial():
        subscription_data = event.data.get('object', {})
        customer_id = subscription_data.get('customer')
        customer = Customer.objects.filter(id=customer_id).first()

        if not customer or not customer.subscriber:
            return

        user = customer.subscriber

        # Track trial usage
        if subscription_data.get('trial_end'):
            with transaction.atomic():
                tracking, created = TrialUsageTracking.objects.select_for_update().get_or_create(
                    user=user,
                    defaults={
                        'has_used_trial': True,
                        'first_trial_at': timezone.now()
                    }
                )

                if not created and not tracking.has_used_trial:
                    tracking.has_used_trial = True
                    tracking.first_trial_at = timezone.now()
                    tracking.save()
                    logger.info(f"Trial tracked via webhook for user {user.id}")
                elif created:
                    logger.info(f"Trial tracking created via webhook for user {user.id}")

        # Create AcquisitionTracking record
        _create_acquisition_tracking(user, subscription_data)

    try:
        retry_on_deadlock(_track_trial)()
    except Exception as e:
        logger.error(f"Error tracking trial in webhook: {str(e)}", exc_info=True)


def _create_acquisition_tracking(user, subscription_data):
    """
    Create or update AcquisitionTracking record for a user
    """
    try:
        # Get acquisition_angle from user (set during registration)
        acquisition_angle = user.acquisition_angle or 'unknown'

        # Map to valid choices
        valid_angles = ['time', 'price', 'delay', 'visibility', 'organic']
        if acquisition_angle not in valid_angles:
            acquisition_angle = 'unknown'

        # Parse trial dates
        trial_start = None
        trial_end = None
        if subscription_data.get('trial_start'):
            trial_start = datetime.fromtimestamp(
                subscription_data['trial_start'],
                tz=timezone.get_current_timezone()
            )
        if subscription_data.get('trial_end'):
            trial_end = datetime.fromtimestamp(
                subscription_data['trial_end'],
                tz=timezone.get_current_timezone()
            )

        status = subscription_data.get('status', 'trialing')

        with transaction.atomic():
            tracking, created = AcquisitionTracking.objects.update_or_create(
                user=user,
                defaults={
                    'acquisition_angle': acquisition_angle,
                    'signup_price_id': user.signup_price_id,
                    'subscription_status': status,
                    'stripe_subscription_id': subscription_data.get('id'),
                    'trial_started_at': trial_start,
                    'trial_ended_at': trial_end if status != 'trialing' else None,
                }
            )

            if created:
                logger.info(
                    f"AcquisitionTracking created for user {user.id} "
                    f"(angle: {acquisition_angle}, status: {status})"
                )
            else:
                logger.info(f"AcquisitionTracking updated for user {user.id}")

    except Exception as e:
        logger.error(f"Error creating AcquisitionTracking: {str(e)}", exc_info=True)


@receiver(signals.WEBHOOK_SIGNALS["customer.subscription.updated"])
def handle_subscription_updated(sender, event, **kwargs):
    """
    Handle subscription status changes (trialing → active, active → past_due, etc)
    Updates AcquisitionTracking accordingly
    """
    try:
        subscription_data = event.data.get('object', {})
        subscription_id = subscription_data.get('id')
        status = subscription_data.get('status')
        previous_attributes = event.data.get('previous_attributes', {})
        previous_status = previous_attributes.get('status')

        if previous_status and previous_status != status:
            logger.info(
                f"Subscription {subscription_id} status changed: "
                f"{previous_status} → {status}"
            )

            # Update AcquisitionTracking
            _update_acquisition_tracking(subscription_id, status, previous_status)

            # Log specific transitions
            if previous_status == 'trialing' and status == 'active':
                logger.info(f"Trial converted to paid: {subscription_id}")
            elif status == 'past_due':
                logger.warning(f"Subscription past due: {subscription_id}")
            elif status == 'canceled':
                logger.info(f"Subscription canceled: {subscription_id}")

    except Exception as e:
        logger.error(f"Error handling subscription.updated webhook: {str(e)}")


def _update_acquisition_tracking(subscription_id, new_status, previous_status):
    """
    Update AcquisitionTracking when subscription status changes
    """
    try:
        tracking = AcquisitionTracking.objects.filter(
            stripe_subscription_id=subscription_id
        ).first()

        if not tracking:
            logger.warning(
                f"AcquisitionTracking not found for subscription {subscription_id}"
            )
            return

        tracking.subscription_status = new_status

        # Track conversion (trial → active)
        if previous_status == 'trialing' and new_status == 'active':
            tracking.converted_at = timezone.now()
            tracking.trial_ended_at = timezone.now()
            logger.info(
                f"User {tracking.user.email} converted from trial "
                f"(angle: {tracking.acquisition_angle})"
            )

        # Track cancellation
        elif new_status == 'canceled':
            tracking.canceled_at = timezone.now()
            logger.info(
                f"User {tracking.user.email} canceled "
                f"(angle: {tracking.acquisition_angle})"
            )

        tracking.save()

    except Exception as e:
        logger.error(f"Error updating AcquisitionTracking: {str(e)}", exc_info=True)


@receiver(signals.WEBHOOK_SIGNALS["customer.subscription.deleted"])
def handle_subscription_deleted(sender, event, **kwargs):
    """
    Handle subscription deletion/cancellation
    """
    try:
        subscription_data = event.data.get('object', {})
        subscription_id = subscription_data.get('id')
        customer_id = subscription_data.get('customer')

        logger.info(f"Subscription deleted: {subscription_id} for customer {customer_id}")

        # Subscription will be synced by dj-stripe automatically
        # User will lose access on next middleware check

    except Exception as e:
        logger.error(f"Error handling subscription.deleted webhook: {str(e)}")


@receiver(signals.WEBHOOK_SIGNALS["invoice.payment_succeeded"])
def handle_payment_succeeded(sender, event, **kwargs):
    """
    Handle successful payment
    """
    try:
        invoice_data = event.data.get('object', {})
        subscription_id = invoice_data.get('subscription')
        customer_id = invoice_data.get('customer')
        amount_paid = invoice_data.get('amount_paid', 0) / 100  # Convert from cents

        logger.info(
            f"Payment succeeded: R$ {amount_paid:.2f} for subscription {subscription_id}"
        )

        # TODO: Send email notification to user
        # TODO: Log to analytics/metrics

    except Exception as e:
        logger.error(f"Error handling payment_succeeded webhook: {str(e)}")


@receiver(signals.WEBHOOK_SIGNALS["invoice.payment_failed"])
def handle_payment_failed(sender, event, **kwargs):
    """
    Handle failed payment
    """
    try:
        invoice_data = event.data.get('object', {})
        subscription_id = invoice_data.get('subscription')
        customer_id = invoice_data.get('customer')
        amount_due = invoice_data.get('amount_due', 0) / 100
        attempt_count = invoice_data.get('attempt_count', 0)

        logger.warning(
            f"Payment failed (attempt {attempt_count}): "
            f"R$ {amount_due:.2f} for subscription {subscription_id}"
        )

        # TODO: Send email notification to user
        # TODO: If final attempt, send cancellation warning

    except Exception as e:
        logger.error(f"Error handling payment_failed webhook: {str(e)}")


@receiver(signals.WEBHOOK_SIGNALS["customer.subscription.trial_will_end"])
def handle_trial_ending_soon(sender, event, **kwargs):
    """
    Handle trial ending soon (3 days before end)
    """
    try:
        subscription_data = event.data.get('object', {})
        subscription_id = subscription_data.get('id')
        trial_end = subscription_data.get('trial_end')

        logger.info(f"Trial ending soon for subscription {subscription_id}")

        # TODO: Send email notification to user
        # TODO: Remind user to update payment method if needed

    except Exception as e:
        logger.error(f"Error handling trial_will_end webhook: {str(e)}")


@receiver(webhook_processing_error)
def handle_webhook_processing_error(sender, exception, **kwargs):
    """
    Handle webhook processing errors, especially deadlocks.
    Log the error and allow retry mechanisms to handle it.

    Note: The 'event' parameter is optional and may not always be available
    """
    error_msg = str(exception)

    # Try to get event data from kwargs if available
    data = kwargs.get('data', {})

    # Handle case where data might be a string instead of dict
    if isinstance(data, str):
        event_id = 'unknown'
        event_type = 'unknown'
    else:
        event_id = data.get('id', 'unknown') if isinstance(data, dict) else 'unknown'
        event_type = data.get('type', 'unknown') if isinstance(data, dict) else 'unknown'

    if 'deadlock' in error_msg.lower() or 'impasse' in error_msg.lower():
        logger.warning(
            f"Deadlock detected while processing webhook event {event_id} "
            f"(type: {event_type}). Stripe will retry automatically."
        )
    elif 'DoesNotExist' in error_msg:
        logger.warning(
            f"Object not found while processing webhook event {event_id} "
            f"(type: {event_type}). This may resolve on retry."
        )
    else:
        logger.error(
            f"Error processing webhook event {event_id} (type: {event_type}): {error_msg}",
            exc_info=exception
        )
