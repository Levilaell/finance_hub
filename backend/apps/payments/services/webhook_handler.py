import logging
import time
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from .webhook_handlers_extended import ExtendedWebhookHandlers
# from .webhook_handlers_production import ProductionWebhookHandlers  # TODO: Create this file
from .notification_service import notification_service
from .audit_service import PaymentAuditService
from .webhook_monitoring_service import webhook_monitoring_service

# Import secure logging and distributed locks
from core.logging_utils import get_secure_logger, log_webhook_event, sanitize_stripe_event
from core.locks import webhook_lock, subscription_lock, payment_lock

logger = get_secure_logger(__name__)


class WebhookHandler:
    """Unified webhook handler for payment gateways"""
    
    def __init__(self, gateway):
        self.gateway = gateway
    
    def handle_stripe_webhook(self, event):
        """Process Stripe webhook events with comprehensive production support"""
        
        from core.locks import lock_manager
        
        # Use distributed lock to ensure webhook idempotency
        event_id = event.get('id')
        if not event_id:
            logger.error("Webhook event missing ID, cannot ensure idempotency")
            return {'status': 'error', 'message': 'Missing event ID'}
        
        with lock_manager.acquire_lock(
            lock_key=f"webhook:process:{event_id}",
            timeout=30,
            retry_timeout=5
        ):
            # Log webhook event securely
            log_webhook_event(
                logger, 
                event, 
                f"Processing webhook event: {event.get('type')}"
            )
            
            return self._process_webhook_event(event)
    
    def _process_webhook_event(self, event):
        """Internal method to process webhook event with monitoring"""
        start_time = time.time()
        event_id = event.get('id', 'unknown')
        event_type = event.get('type', 'unknown')
        
        handlers = {
            # Core subscription events
            'checkout.session.completed': self._handle_checkout_completed,
            'customer.subscription.created': self._handle_subscription_created,
            'customer.subscription.updated': self._handle_subscription_updated,
            'customer.subscription.deleted': self._handle_subscription_deleted,
            'customer.subscription.trial_will_end': ExtendedWebhookHandlers.handle_trial_ending,
            # 'customer.subscription.paused': ProductionWebhookHandlers.handle_subscription_paused,
            # 'customer.subscription.resumed': ProductionWebhookHandlers.handle_subscription_resumed,
            
            # Invoice events
            # 'invoice.created': ProductionWebhookHandlers.handle_invoice_created,
            # 'invoice.finalized': ProductionWebhookHandlers.handle_invoice_finalized,
            'invoice.payment_succeeded': self._handle_invoice_payment,
            'invoice.payment_failed': self._handle_payment_failed,
            'invoice.payment_action_required': ExtendedWebhookHandlers.handle_payment_action_required,
            
            # Payment events
            # 'charge.succeeded': ProductionWebhookHandlers.handle_charge_succeeded,
            # 'charge.failed': ProductionWebhookHandlers.handle_charge_failed,
            'payment_intent.succeeded': self._handle_payment_intent_succeeded,
            'payment_intent.payment_failed': self._handle_payment_intent_failed,
            
            # Payment method events
            'payment_method.attached': ExtendedWebhookHandlers.handle_payment_method_attached,
            'payment_method.detached': ExtendedWebhookHandlers.handle_payment_method_detached,
            'payment_method.updated': ExtendedWebhookHandlers.handle_payment_method_updated,
            
            # Customer events
            # 'customer.created': ProductionWebhookHandlers.handle_customer_created,
            'customer.updated': self._handle_customer_updated,
            'customer.deleted': self._handle_customer_deleted,
            
            # Dispute events
            'charge.dispute.created': ExtendedWebhookHandlers.handle_dispute_created,
            'charge.dispute.closed': ExtendedWebhookHandlers.handle_dispute_closed,
            'charge.dispute.funds_withdrawn': self._handle_dispute_funds_withdrawn,
            'charge.dispute.funds_reinstated': self._handle_dispute_funds_reinstated,
            
            # Price and product events
            # 'price.updated': ProductionWebhookHandlers.handle_price_updated,
            'product.updated': self._handle_product_updated,
            
            # Billing portal events
            # 'billing_portal.session.created': ProductionWebhookHandlers.handle_billing_portal_session_created,
            
            # Security events
            # 'radar.early_fraud_warning.created': ProductionWebhookHandlers.handle_radar_early_fraud_warning,
            
            # Schedule events
            # 'subscription_schedule.created': ProductionWebhookHandlers.handle_subscription_schedule_created,
            'subscription_schedule.updated': self._handle_subscription_schedule_updated,
        }
        
        handler = handlers.get(event['type'])
        if handler:
            try:
                with transaction.atomic():
                    result = handler(event)
                    
                    # Record successful processing
                    processing_time_ms = (time.time() - start_time) * 1000
                    webhook_monitoring_service.record_webhook_success(
                        event_id=event_id,
                        event_type=event_type,
                        processing_time_ms=processing_time_ms
                    )
                    
                    return result
            except Exception as e:
                error_message = str(e)
                logger.error(f"Webhook handler error for {event['type']}: {error_message}")
                
                # Record webhook failure
                webhook_monitoring_service.record_webhook_failure(
                    event_id=event_id,
                    event_type=event_type,
                    event_data=event,
                    error_message=error_message,
                    is_retryable=True  # Most webhook failures are retryable
                )
                
                # Store failed webhook for retry (legacy support)
                ExtendedWebhookHandlers.store_failed_webhook(event, error_message)
                raise
        else:
            logger.info(f"Unhandled webhook event type: {event['type']}")
            
            # Record as non-retryable failure (unsupported event type)
            webhook_monitoring_service.record_webhook_failure(
                event_id=event_id,
                event_type=event_type,
                event_data=event,
                error_message=f"Unhandled webhook event type: {event_type}",
                is_retryable=False
            )
            
            return {'status': 'unhandled'}
    
    def _handle_subscription_created(self, event):
        """Handle subscription created event"""
        logger.info(f"Subscription created: {event['data']['object']['id']}")
        return {'status': 'success'}
    
    def _handle_subscription_updated(self, event):
        """Handle subscription updated event"""
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
            subscription.save()
            
            logger.info(f"Subscription {subscription.id} updated to status: {subscription.status}")
            return {'status': 'success'}
            
        except Subscription.DoesNotExist:
            logger.warning(f"Subscription not found for Stripe ID: {stripe_sub['id']}")
            return {'status': 'not_found'}
    
    def _handle_subscription_deleted(self, event):
        """Handle subscription deleted event"""
        from ..models import Subscription
        
        stripe_sub = event['data']['object']
        
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_sub['id']
            )
            subscription.status = 'cancelled'
            subscription.cancelled_at = timezone.now()
            subscription.save()
            
            logger.info(f"Subscription {subscription.id} cancelled")
            return {'status': 'success'}
            
        except Subscription.DoesNotExist:
            logger.warning(f"Subscription not found for Stripe ID: {stripe_sub['id']}")
            return {'status': 'not_found'}
    
    def _handle_payment_intent_succeeded(self, event):
        """Handle payment intent succeeded"""
        logger.info(f"Payment intent succeeded: {event['data']['object']['id']}")
        return {'status': 'success'}
    
    def _handle_payment_intent_failed(self, event):
        """Handle payment intent failed"""
        logger.error(f"Payment intent failed: {event['data']['object']['id']}")
        return {'status': 'success'}
    
    def _handle_customer_updated(self, event):
        """Handle customer updated event"""
        logger.info(f"Customer updated: {event['data']['object']['id']}")
        return {'status': 'success'}
    
    def _handle_customer_deleted(self, event):
        """Handle customer deleted event"""
        logger.info(f"Customer deleted: {event['data']['object']['id']}")
        return {'status': 'success'}
    
    def _handle_dispute_funds_withdrawn(self, event):
        """Handle dispute funds withdrawn"""
        logger.warning(f"Dispute funds withdrawn: {event['data']['object']['id']}")
        return {'status': 'success'}
    
    def _handle_dispute_funds_reinstated(self, event):
        """Handle dispute funds reinstated"""
        logger.info(f"Dispute funds reinstated: {event['data']['object']['id']}")
        return {'status': 'success'}
    
    def _handle_product_updated(self, event):
        """Handle product updated event"""
        logger.info(f"Product updated: {event['data']['object']['id']}")
        return {'status': 'success'}
    
    def _handle_subscription_schedule_updated(self, event):
        """Handle subscription schedule updated"""
        logger.info(f"Subscription schedule updated: {event['data']['object']['id']}")
        return {'status': 'success'}
    
    def _handle_checkout_completed(self, event):
        """Handle successful checkout session"""
        from ..models import Subscription, Payment
        from apps.companies.models import SubscriptionPlan
        from apps.companies.models import Company
        from core.locks import lock_manager
        
        session = event['data']['object']
        
        # Metadata can be at session level or in subscription_data
        metadata = session.get('metadata', {})
        
        # If metadata is not at session level, check subscription_data
        if not metadata.get('company_id'):
            subscription_metadata = session.get('subscription_data', {}).get('metadata', {})
            if subscription_metadata:
                metadata = subscription_metadata
        
        # Get company and plan from metadata
        company_id = metadata.get('company_id')
        plan_id = metadata.get('plan_id')
        billing_period = metadata.get('billing_period', 'monthly')
        
        if not company_id or not plan_id:
            logger.error("Missing metadata in checkout session", extra={
                'session_id': session['id'],
                'metadata_found': bool(metadata)
            })
            return {'status': 'error', 'message': 'Missing metadata'}
        
        # Use company-specific lock to prevent race conditions
        with lock_manager.acquire_lock(
            lock_key=f"subscription:create:{company_id}",
            timeout=45,
            retry_timeout=10
        ):
            try:
                company = Company.objects.get(id=company_id)
                plan = SubscriptionPlan.objects.get(id=plan_id)
            except (Company.DoesNotExist, SubscriptionPlan.DoesNotExist) as e:
                logger.error(f"Invalid company or plan in checkout", extra={
                    'company_id': company_id,
                    'plan_id': plan_id,
                    'error': str(e)
                })
                return {'status': 'error', 'message': 'Invalid data'}
            
            # Check if company already has active subscription (race condition protection)
            existing_subscription = Subscription.objects.filter(
                company=company,
                status__in=['active', 'trial']
            ).first()
            
            if existing_subscription:
                logger.warning("Company already has active subscription", extra={
                    'company_id': company_id,
                    'existing_subscription_id': existing_subscription.id,
                    'session_id': session['id']
                })
                return {'status': 'warning', 'message': 'Subscription already exists'}
            
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
            
            logger.info("Subscription activated for company", extra={
                'company_name': company.name,
                'subscription_id': subscription.id,
                'plan': plan.name
            })
            
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
        """Handle failed payment with intelligent retry logic"""
        from ..models import Subscription, Payment
        from .payment_retry_service import payment_retry_service
        
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
            
            # Extract error information from invoice
            error_code = 'generic_decline'
            error_message = 'Payment failed'
            
            # Try to get more specific error from last payment error
            if invoice.get('last_payment_error'):
                error_data = invoice['last_payment_error']
                error_code = error_data.get('decline_code') or error_data.get('code', 'generic_decline')
                error_message = error_data.get('message', 'Payment failed')
            
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
                metadata={
                    'attempt_count': invoice.get('attempt_count', 1),
                    'error_code': error_code,
                    'error_message': error_message
                }
            )
            
            # Log failed payment
            PaymentAuditService.log_payment_attempt(
                payment,
                error_message=f'Payment failed: {error_message}',
                metadata={
                    'source': 'invoice_webhook',
                    'attempt_count': invoice.get('attempt_count', 1),
                    'error_code': error_code
                }
            )
            
            # Handle payment failure with retry logic
            retry_result = payment_retry_service.handle_payment_failure(
                payment=payment,
                error_code=error_code,
                error_message=error_message,
                stripe_data={
                    'invoice_id': invoice['id'],
                    'subscription_id': subscription_id,
                    'last_payment_error': invoice.get('last_payment_error')
                }
            )
            
            logger.warning(f"Payment failed for {subscription.company.name}: {retry_result}")
            return {'status': 'success', 'retry_action': retry_result['action']}
            
        except Subscription.DoesNotExist:
            logger.warning(f"Subscription not found for Stripe ID: {subscription_id}")
            return {'status': 'error', 'message': 'Subscription not found'}
    
    def _handle_subscription_updated(self, event):
        """Handle subscription updates with special handling for trial→active transition"""
        from ..models import Subscription
        
        stripe_sub = event['data']['object']
        previous_attributes = event.get('data', {}).get('previous_attributes', {})
        
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_sub['id']
            )
            
            # Store previous status for transition detection
            previous_status = subscription.status
            
            # Update status
            status_map = {
                'trialing': 'trial',
                'active': 'active',
                'past_due': 'past_due',
                'canceled': 'cancelled',
                'unpaid': 'past_due'
            }
            
            new_status = status_map.get(stripe_sub['status'], 'expired')
            
            # Detect trial to active transition
            is_trial_to_active = (
                previous_status == 'trial' and 
                new_status == 'active' and
                previous_attributes.get('status') == 'trialing'
            )
            
            # Update subscription fields
            subscription.status = new_status
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                stripe_sub['current_period_start'], tz=timezone.utc
            )
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                stripe_sub['current_period_end'], tz=timezone.utc
            )
            
            # Handle trial end
            if stripe_sub.get('trial_end') and not subscription.trial_ends_at:
                subscription.trial_ends_at = timezone.datetime.fromtimestamp(
                    stripe_sub['trial_end'], tz=timezone.utc
                )
            
            if stripe_sub.get('cancel_at_period_end'):
                subscription.cancelled_at = timezone.now()
            else:
                subscription.cancelled_at = None  # Clear if reactivated
            
            subscription.save()
            
            # Log subscription status change with enhanced metadata
            metadata = {
                'status': new_status,
                'previous_status': previous_status,
                'cancel_at_period_end': stripe_sub.get('cancel_at_period_end', False),
                'source': 'subscription_webhook',
                'stripe_status': stripe_sub['status']
            }
            
            # Add trial conversion metadata
            if is_trial_to_active:
                metadata.update({
                    'trial_converted': True,
                    'trial_ended_at': subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
                    'plan_name': subscription.plan.name if subscription.plan else None,
                    'billing_period': subscription.billing_period
                })
                
                # Log specific trial conversion event
                PaymentAuditService.log_payment_action(
                    action='trial_converted_to_active',
                    company=subscription.company,
                    subscription_id=subscription.id,
                    metadata=metadata
                )
                
                # Send notification for trial conversion
                notification_service.notify_trial_converted(
                    subscription.company.id,
                    {
                        'subscription_id': subscription.id,
                        'plan_name': subscription.plan.name if subscription.plan else 'Unknown',
                        'billing_period': subscription.billing_period,
                        'converted_at': timezone.now().isoformat()
                    }
                )
                
                logger.info(f"Trial converted to active subscription for {subscription.company.name}")
            else:
                # Regular subscription update
                PaymentAuditService.log_payment_action(
                    action='subscription_updated',
                    company=subscription.company,
                    subscription_id=subscription.id,
                    metadata=metadata
                )
                
                logger.info(f"Subscription updated for {subscription.company.name}: {previous_status} → {new_status}")
            
            # Send real-time notification for status changes
            if previous_status != new_status:
                notification_service.notify_subscription_updated(
                    subscription.company.id,
                    {
                        'subscription_id': subscription.id,
                        'status': new_status,
                        'previous_status': previous_status,
                        'changes': {
                            'status_changed': True,
                            'trial_converted': is_trial_to_active
                        }
                    }
                )
            
            return {'status': 'success', 'trial_converted': is_trial_to_active}
            
        except Subscription.DoesNotExist:
            logger.warning(f"Subscription not found for Stripe ID: {stripe_sub['id']}")
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
    
    def _handle_subscription_created(self, event):
        """Handle new subscription creation"""
        from ..models import Subscription
        from apps.companies.models import SubscriptionPlan
        from apps.companies.models import Company
        
        stripe_sub = event['data']['object']
        metadata = stripe_sub.get('metadata', {})
        company_id = metadata.get('company_id')
        plan_id = metadata.get('plan_id')
        
        if not company_id or not plan_id:
            logger.error(f"Missing metadata in subscription: {stripe_sub['id']}")
            return {'status': 'error', 'message': 'Missing metadata'}
        
        try:
            company = Company.objects.get(id=company_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            subscription, created = Subscription.objects.update_or_create(
                company=company,
                defaults={
                    'plan': plan,
                    'status': 'active' if stripe_sub['status'] == 'active' else 'trial',
                    'billing_period': 'yearly' if stripe_sub['items']['data'][0]['price']['recurring']['interval'] == 'year' else 'monthly',
                    'stripe_subscription_id': stripe_sub['id'],
                    'stripe_customer_id': stripe_sub['customer'],
                    'current_period_start': timezone.datetime.fromtimestamp(
                        stripe_sub['current_period_start'], tz=timezone.utc
                    ),
                    'current_period_end': timezone.datetime.fromtimestamp(
                        stripe_sub['current_period_end'], tz=timezone.utc
                    ),
                    'trial_ends_at': timezone.datetime.fromtimestamp(
                        stripe_sub['trial_end'], tz=timezone.utc
                    ) if stripe_sub.get('trial_end') else None
                }
            )
            
            logger.info(f"Subscription {'created' if created else 'updated'} for {company.name}")
            return {'status': 'success', 'subscription_id': subscription.id}
            
        except (Company.DoesNotExist, SubscriptionPlan.DoesNotExist) as e:
            logger.error(f"Error creating subscription: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_payment_intent_succeeded(self, event):
        """Handle successful payment intent"""
        from ..models import Payment
        
        payment_intent = event['data']['object']
        metadata = payment_intent.get('metadata', {})
        
        # Check if this is already handled by invoice payment
        if metadata.get('invoice_id'):
            return {'status': 'skipped', 'reason': 'Invoice payment'}
        
        # Handle one-time payments
        payment_id = metadata.get('payment_id')
        if payment_id:
            try:
                payment = Payment.objects.get(id=payment_id)
                payment.status = 'succeeded'
                payment.stripe_payment_intent_id = payment_intent['id']
                payment.paid_at = timezone.now()
                payment.save()
                
                logger.info(f"Payment intent succeeded: {payment.id}")
                return {'status': 'success'}
            except Payment.DoesNotExist:
                logger.error(f"Payment not found: {payment_id}")
        
        return {'status': 'skipped'}
    
    def _handle_payment_intent_failed(self, event):
        """Handle failed payment intent"""
        payment_intent = event['data']['object']
        error = payment_intent.get('last_payment_error', {})
        
        logger.error(f"Payment intent failed: {error.get('message', 'Unknown error')}")
        return {'status': 'success'}
    
    def _handle_customer_updated(self, event):
        """Handle customer updates"""
        customer = event['data']['object']
        logger.info(f"Customer updated: {customer['id']}")
        return {'status': 'success'}
    
    def _handle_customer_deleted(self, event):
        """Handle customer deletion"""
        from ..models import Subscription
        
        customer = event['data']['object']
        
        # Mark all subscriptions as cancelled
        Subscription.objects.filter(
            stripe_customer_id=customer['id']
        ).update(
            status='cancelled',
            cancelled_at=timezone.now()
        )
        
        logger.info(f"Customer deleted: {customer['id']}")
        return {'status': 'success'}
    
    def _handle_dispute_funds_withdrawn(self, event):
        """Handle dispute funds withdrawal"""
        dispute = event['data']['object']
        
        PaymentAuditService.log_security_event(
            event_type='dispute_funds_withdrawn',
            company=None,
            details={
                'dispute_id': dispute['id'],
                'amount': dispute['amount'],
                'currency': dispute['currency']
            },
            severity='critical'
        )
        
        return {'status': 'success'}
    
    def _handle_dispute_funds_reinstated(self, event):
        """Handle dispute funds reinstatement"""
        dispute = event['data']['object']
        
        PaymentAuditService.log_payment_action(
            action='dispute_funds_reinstated',
            company=None,
            metadata={
                'dispute_id': dispute['id'],
                'amount': dispute['amount'],
                'currency': dispute['currency']
            }
        )
        
        return {'status': 'success'}
    
    def _handle_product_updated(self, event):
        """Handle product updates"""
        product = event['data']['object']
        logger.info(f"Product updated: {product['id']} - {product['name']}")
        return {'status': 'success'}
    
    def _handle_subscription_schedule_updated(self, event):
        """Handle subscription schedule updates"""
        schedule = event['data']['object']
        logger.info(f"Subscription schedule updated: {schedule['id']}")
        return {'status': 'success'}