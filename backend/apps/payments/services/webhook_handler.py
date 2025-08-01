import logging
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from .webhook_handlers_extended import ExtendedWebhookHandlers
from .notification_service import notification_service
from .audit_service import PaymentAuditService

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Unified webhook handler for payment gateways"""
    
    def __init__(self, gateway):
        self.gateway = gateway
    
    def handle_stripe_webhook(self, event):
        """Process Stripe webhook events"""
        handlers = {
            'checkout.session.completed': self._handle_checkout_completed,
            'invoice.payment_succeeded': self._handle_invoice_payment,
            'invoice.payment_failed': self._handle_payment_failed,
            'invoice.payment_action_required': ExtendedWebhookHandlers.handle_payment_action_required,
            'customer.subscription.updated': self._handle_subscription_updated,
            'customer.subscription.deleted': self._handle_subscription_deleted,
            'customer.subscription.trial_will_end': ExtendedWebhookHandlers.handle_trial_ending,
            'payment_method.attached': ExtendedWebhookHandlers.handle_payment_method_attached,
            'payment_method.detached': ExtendedWebhookHandlers.handle_payment_method_detached,
            'payment_method.updated': ExtendedWebhookHandlers.handle_payment_method_updated,
            'charge.dispute.created': ExtendedWebhookHandlers.handle_dispute_created,
            'charge.dispute.closed': ExtendedWebhookHandlers.handle_dispute_closed,
        }
        
        handler = handlers.get(event['type'])
        if handler:
            try:
                with transaction.atomic():
                    return handler(event)
            except Exception as e:
                logger.error(f"Webhook handler error for {event['type']}: {e}")
                # Store failed webhook for retry
                ExtendedWebhookHandlers.store_failed_webhook(event, str(e))
                raise
        else:
            logger.info(f"Unhandled webhook event type: {event['type']}")
            return {'status': 'unhandled'}
    
    def _handle_checkout_completed(self, event):
        """Handle successful checkout session"""
        from ..models import Subscription, SubscriptionPlan, Payment
        from apps.companies.models import Company
        
        session = event['data']['object']
        metadata = session.get('subscription_metadata', {})
        
        # Get company and plan
        company_id = metadata.get('company_id')
        plan_id = metadata.get('plan_id')
        billing_period = metadata.get('billing_period', 'monthly')
        
        if not company_id or not plan_id:
            logger.error(f"Missing metadata in checkout session: {session['id']}")
            return {'status': 'error', 'message': 'Missing metadata'}
        
        try:
            company = Company.objects.get(id=company_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except (Company.DoesNotExist, SubscriptionPlan.DoesNotExist) as e:
            logger.error(f"Invalid company or plan in checkout: {e}")
            return {'status': 'error', 'message': 'Invalid data'}
        
        # Create or update subscription
        subscription, created = Subscription.objects.update_or_create(
            company=company,
            defaults={
                'plan': plan,
                'status': 'active',
                'billing_period': billing_period,
                'stripe_subscription_id': session.get('subscription'),
                'stripe_customer_id': session.get('customer'),
                'current_period_start': timezone.now(),
                'current_period_end': timezone.now() + timezone.timedelta(
                    days=365 if billing_period == 'yearly' else 30
                ),
            }
        )
        
        # Record payment
        amount = Decimal(session['amount_total']) / 100  # Convert from cents
        payment = Payment.objects.create(
            company=company,
            subscription=subscription,
            amount=amount,
            currency=session['currency'].upper(),
            status='succeeded',
            description=f"{plan.display_name} - {billing_period.title()} subscription",
            gateway='stripe',
            stripe_payment_intent_id=session.get('payment_intent'),
            paid_at=timezone.now(),
            metadata={
                'session_id': session['id'],
                'subscription_id': session.get('subscription')
            }
        )
        
        # Log subscription creation/activation and payment
        if created:
            PaymentAuditService.log_subscription_created(
                subscription,
                user=None,  # We don't have user context in webhook
                metadata={'source': 'checkout_webhook'}
            )
        else:
            PaymentAuditService.log_payment_action(
                action='subscription_activated',
                company=company,
                subscription_id=subscription.id,
                metadata={
                    'plan': plan.name,
                    'billing_period': billing_period,
                    'source': 'checkout_webhook'
                }
            )
        
        PaymentAuditService.log_payment_attempt(
            payment,
            metadata={'source': 'checkout_webhook'}
        )
        
        # Send real-time notification
        notification_service.notify_subscription_updated(
            company.id,
            {
                'subscription_id': subscription.id,
                'status': 'active',
                'plan': plan.name,
                'changes': {'activated': True}
            }
        )
        
        # Notify checkout completion
        if session.get('id'):
            notification_service.notify_checkout_completed(
                session['id'],
                {'subscription_id': subscription.id}
            )
        
        logger.info(f"Subscription activated for company {company.name}")
        return {'status': 'success', 'subscription_id': subscription.id}
    
    def _handle_invoice_payment(self, event):
        """Handle successful invoice payment"""
        from ..models import Subscription, Payment
        
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')
        
        if not subscription_id:
            return {'status': 'skipped', 'reason': 'No subscription'}
        
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=subscription_id
            )
        except Subscription.DoesNotExist:
            logger.warning(f"Subscription not found: {subscription_id}")
            return {'status': 'error', 'message': 'Subscription not found'}
        
        # Update subscription periods
        subscription.current_period_start = timezone.datetime.fromtimestamp(
            invoice['period_start'], tz=timezone.utc
        )
        subscription.current_period_end = timezone.datetime.fromtimestamp(
            invoice['period_end'], tz=timezone.utc
        )
        subscription.status = 'active'
        subscription.save()
        
        # Record payment
        amount = Decimal(invoice['amount_paid']) / 100
        payment = Payment.objects.create(
            company=subscription.company,
            subscription=subscription,
            amount=amount,
            currency=invoice['currency'].upper(),
            status='succeeded',
            description=f"Subscription renewal - {subscription.plan.display_name}",
            gateway='stripe',
            stripe_invoice_id=invoice['id'],
            stripe_payment_intent_id=invoice.get('payment_intent'),
            paid_at=timezone.now(),
            metadata={'invoice_number': invoice.get('number')}
        )
        
        # Log successful payment
        PaymentAuditService.log_payment_attempt(
            payment,
            metadata={'source': 'invoice_webhook', 'invoice_number': invoice.get('number')}
        )
        
        # Send real-time notification
        notification_service.notify_payment_success(
            subscription.company.id,
            {
                'payment_id': payment.id,
                'subscription_id': subscription.id,
                'amount': float(amount),
                'currency': invoice['currency'].upper()
            }
        )
        
        logger.info(f"Invoice payment recorded for {subscription.company.name}")
        return {'status': 'success'}
    
    def _handle_payment_failed(self, event):
        """Handle failed payment"""
        from ..models import Subscription, Payment
        
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')
        
        if not subscription_id:
            return {'status': 'skipped'}
        
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=subscription_id
            )
            subscription.status = 'past_due'
            subscription.save()
            
            # Record failed payment
            amount = Decimal(invoice['amount_due']) / 100
            payment = Payment.objects.create(
                company=subscription.company,
                subscription=subscription,
                amount=amount,
                currency=invoice['currency'].upper(),
                status='failed',
                description=f"Failed payment - {subscription.plan.display_name}",
                gateway='stripe',
                stripe_invoice_id=invoice['id'],
                metadata={'attempt_count': invoice.get('attempt_count', 1)}
            )
            
            # Log failed payment
            PaymentAuditService.log_payment_attempt(
                payment,
                error_message='Payment failed at gateway',
                metadata={
                    'source': 'invoice_webhook',
                    'attempt_count': invoice.get('attempt_count', 1)
                }
            )
            
            # Send real-time notification
            notification_service.notify_payment_failed(
                subscription.company.id,
                {
                    'payment_id': payment.id,
                    'reason': 'Payment failed - please update payment method',
                    'retry_available': True
                }
            )
            
            logger.warning(f"Payment failed for {subscription.company.name}")
            return {'status': 'success'}
            
        except Subscription.DoesNotExist:
            return {'status': 'error', 'message': 'Subscription not found'}
    
    def _handle_subscription_updated(self, event):
        """Handle subscription updates"""
        from ..models import Subscription
        
        stripe_sub = event['data']['object']
        
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_sub['id']
            )
            
            # Update status
            status_map = {
                'trialing': 'trial',
                'active': 'active',
                'past_due': 'past_due',
                'canceled': 'cancelled',
                'unpaid': 'past_due'
            }
            
            subscription.status = status_map.get(stripe_sub['status'], 'expired')
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                stripe_sub['current_period_end'], tz=timezone.utc
            )
            
            if stripe_sub.get('cancel_at_period_end'):
                subscription.cancelled_at = timezone.now()
            
            subscription.save()
            
            # Log subscription status change
            PaymentAuditService.log_payment_action(
                action='subscription_updated',
                company=subscription.company,
                subscription_id=subscription.id,
                metadata={
                    'status': subscription.status,
                    'cancel_at_period_end': stripe_sub.get('cancel_at_period_end', False),
                    'source': 'subscription_webhook'
                }
            )
            
            logger.info(f"Subscription updated for {subscription.company.name}")
            return {'status': 'success'}
            
        except Subscription.DoesNotExist:
            return {'status': 'error', 'message': 'Subscription not found'}
    
    def _handle_subscription_deleted(self, event):
        """Handle subscription deletion"""
        from ..models import Subscription
        
        stripe_sub = event['data']['object']
        
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_sub['id']
            )
            subscription.status = 'expired'
            subscription.save()
            
            # Log subscription expiration
            PaymentAuditService.log_payment_action(
                action='subscription_expired',
                company=subscription.company,
                subscription_id=subscription.id,
                metadata={
                    'plan': subscription.plan.name,
                    'source': 'subscription_webhook'
                }
            )
            
            logger.info(f"Subscription expired for {subscription.company.name}")
            return {'status': 'success'}
            
        except Subscription.DoesNotExist:
            return {'status': 'error', 'message': 'Subscription not found'}