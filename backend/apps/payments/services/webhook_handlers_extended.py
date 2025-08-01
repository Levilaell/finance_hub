"""Extended webhook handlers for additional Stripe events"""
import logging
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings
from .notification_service import notification_service
from .audit_service import PaymentAuditService

logger = logging.getLogger(__name__)


class ExtendedWebhookHandlers:
    """Additional webhook handlers for comprehensive payment event handling"""
    
    @staticmethod
    def handle_payment_action_required(event):
        """Handle payment requiring additional action (3D Secure, etc)"""
        from ..models import Payment, Subscription
        
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')
        
        if not subscription_id:
            return {'status': 'skipped'}
        
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=subscription_id
            )
            
            # Record payment attempt
            amount = Decimal(invoice['amount_due']) / 100
            payment = Payment.objects.create(
                company=subscription.company,
                subscription=subscription,
                amount=amount,
                currency=invoice['currency'].upper(),
                status='processing',
                description=f"Payment requires authentication - {subscription.plan.display_name}",
                gateway='stripe',
                stripe_invoice_id=invoice['id'],
                metadata={
                    'requires_action': True,
                    'payment_intent': invoice.get('payment_intent')
                }
            )
            
            # Log payment requiring action
            PaymentAuditService.log_payment_action(
                action='payment_initiated',
                company=subscription.company,
                subscription_id=subscription.id,
                payment_id=payment.id,
                metadata={
                    'requires_action': True,
                    'amount': str(amount),
                    'currency': invoice['currency'].upper(),
                    'payment_intent': invoice.get('payment_intent')
                },
                severity='warning'
            )
            
            # Send notification to user
            notification_service.notify_payment_action_required(
                subscription.company,
                payment,
                invoice.get('hosted_invoice_url')
            )
            logger.warning(f"Payment action required for {subscription.company.name}")
            
            return {'status': 'success'}
            
        except Subscription.DoesNotExist:
            return {'status': 'error', 'message': 'Subscription not found'}
    
    @staticmethod
    def handle_trial_ending(event):
        """Handle trial ending soon notification"""
        from ..models import Subscription
        
        stripe_sub = event['data']['object']
        
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_sub['id']
            )
            
            # Log trial ending event
            PaymentAuditService.log_payment_action(
                action='subscription_trial_ending',
                company=subscription.company,
                subscription_id=subscription.id,
                metadata={
                    'trial_ends_at': subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
                    'plan': subscription.plan.name
                }
            )
            
            # Send trial ending email
            user = subscription.company.users.filter(is_company_admin=True).first()
            if user and user.email:
                send_mail(
                    subject='Your Finance Hub trial is ending soon',
                    message=f'Your trial for {subscription.company.name} ends in 3 days. Please add a payment method to continue using Finance Hub.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            
            logger.info(f"Trial ending notification sent for {subscription.company.name}")
            return {'status': 'success'}
            
        except Subscription.DoesNotExist:
            return {'status': 'error', 'message': 'Subscription not found'}
    
    @staticmethod
    def handle_payment_method_attached(event):
        """Handle payment method attached to customer"""
        from ..models import PaymentMethod
        from apps.companies.models import Company
        
        pm = event['data']['object']
        customer_id = pm.get('customer')
        
        if not customer_id:
            return {'status': 'skipped'}
        
        try:
            # Find company by customer ID
            company = Company.objects.filter(
                subscription__stripe_customer_id=customer_id
            ).first()
            
            if not company:
                logger.warning(f"Company not found for customer {customer_id}")
                return {'status': 'error', 'message': 'Company not found'}
            
            # Check if payment method already exists
            if not PaymentMethod.objects.filter(
                stripe_payment_method_id=pm['id']
            ).exists():
                payment_method = PaymentMethod.objects.create(
                    company=company,
                    type='card' if pm['type'] == 'card' else pm['type'],
                    stripe_payment_method_id=pm['id'],
                    brand=pm.get('card', {}).get('brand', ''),
                    last4=pm.get('card', {}).get('last4', ''),
                    exp_month=pm.get('card', {}).get('exp_month'),
                    exp_year=pm.get('card', {}).get('exp_year'),
                )
                
                # Log payment method attachment
                PaymentAuditService.log_payment_method_action(
                    action_type='added',
                    payment_method=payment_method,
                    metadata={
                        'source': 'webhook',
                        'customer_id': customer_id
                    }
                )
            
            logger.info(f"Payment method attached for {company.name}")
            return {'status': 'success'}
            
        except Exception as e:
            logger.error(f"Error handling payment method attachment: {e}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def handle_payment_method_detached(event):
        """Handle payment method removed from customer"""
        from ..models import PaymentMethod
        
        pm = event['data']['object']
        
        try:
            payment_method = PaymentMethod.objects.filter(
                stripe_payment_method_id=pm['id']
            ).first()
            
            if payment_method:
                # Log before deletion
                PaymentAuditService.log_payment_method_action(
                    action_type='removed',
                    payment_method=payment_method,
                    metadata={
                        'source': 'webhook',
                        'stripe_id': pm['id']
                    }
                )
                
                payment_method.delete()
                logger.info(f"Payment method {pm['id']} removed")
            
            return {'status': 'success'}
            
        except Exception as e:
            logger.error(f"Error handling payment method detachment: {e}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def handle_payment_method_updated(event):
        """Handle payment method update (e.g., card expiry)"""
        from ..models import PaymentMethod
        
        pm = event['data']['object']
        
        try:
            payment_method = PaymentMethod.objects.filter(
                stripe_payment_method_id=pm['id']
            ).first()
            
            if payment_method and pm['type'] == 'card':
                old_exp_month = payment_method.exp_month
                old_exp_year = payment_method.exp_year
                
                payment_method.exp_month = pm['card'].get('exp_month')
                payment_method.exp_year = pm['card'].get('exp_year')
                payment_method.save()
                
                # Log payment method update
                PaymentAuditService.log_payment_method_action(
                    action_type='updated',
                    payment_method=payment_method,
                    metadata={
                        'source': 'webhook',
                        'old_exp_month': old_exp_month,
                        'old_exp_year': old_exp_year,
                        'new_exp_month': payment_method.exp_month,
                        'new_exp_year': payment_method.exp_year
                    }
                )
                
                logger.info(f"Payment method {pm['id']} updated")
            
            return {'status': 'success'}
            
        except Exception as e:
            logger.error(f"Error handling payment method update: {e}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def handle_dispute_created(event):
        """Handle charge dispute/chargeback"""
        from ..models import Payment
        
        dispute = event['data']['object']
        charge_id = dispute.get('charge')
        
        try:
            # Find payment by charge ID
            payment = Payment.objects.filter(
                metadata__contains={'charge_id': charge_id}
            ).first()
            
            if payment:
                # Update payment status
                payment.status = 'disputed'
                payment.metadata['dispute_id'] = dispute['id']
                payment.metadata['dispute_amount'] = dispute['amount']
                payment.metadata['dispute_reason'] = dispute['reason']
                payment.save()
                
                # Suspend subscription if active
                if payment.subscription and payment.subscription.status == 'active':
                    payment.subscription.status = 'past_due'
                    payment.subscription.save()
                
                # Log dispute creation
                PaymentAuditService.log_security_event(
                    event_type='fraud_detected',
                    company=payment.company,
                    details={
                        'dispute_id': dispute['id'],
                        'payment_id': payment.id,
                        'amount': dispute['amount'],
                        'reason': dispute['reason'],
                        'subscription_suspended': payment.subscription is not None
                    }
                )
                
                # Send notification to admin
                notification_service.notify_dispute_created(
                    payment.company,
                    payment,
                    dispute
                )
                logger.error(f"Dispute created for payment {payment.id} - {dispute['reason']}")
            
            return {'status': 'success'}
            
        except Exception as e:
            logger.error(f"Error handling dispute: {e}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def handle_dispute_closed(event):
        """Handle dispute resolution"""
        from ..models import Payment
        
        dispute = event['data']['object']
        
        try:
            # Find payment by dispute ID
            payment = Payment.objects.filter(
                metadata__contains={'dispute_id': dispute['id']}
            ).first()
            
            if payment:
                # Update payment status based on dispute outcome
                if dispute['status'] == 'won':
                    payment.status = 'succeeded'
                    # Reactivate subscription if needed
                    if payment.subscription and payment.subscription.status == 'past_due':
                        payment.subscription.status = 'active'
                        payment.subscription.save()
                elif dispute['status'] == 'lost':
                    payment.status = 'refunded'
                
                payment.metadata['dispute_status'] = dispute['status']
                payment.metadata['dispute_resolved_at'] = timezone.now().isoformat()
                payment.save()
                
                # Log dispute resolution
                PaymentAuditService.log_payment_action(
                    action='payment_dispute_resolved',
                    company=payment.company,
                    payment_id=payment.id,
                    metadata={
                        'dispute_id': dispute['id'],
                        'dispute_status': dispute['status'],
                        'subscription_reactivated': payment.subscription.status == 'active' if payment.subscription else False
                    },
                    severity='info' if dispute['status'] == 'won' else 'warning'
                )
                
                logger.info(f"Dispute {dispute['id']} resolved - {dispute['status']}")
            
            return {'status': 'success'}
            
        except Exception as e:
            logger.error(f"Error handling dispute resolution: {e}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def store_failed_webhook(event, error_message):
        """Store failed webhook for retry"""
        from ..models import FailedWebhook
        
        FailedWebhook.objects.create(
            event_id=event.get('id'),
            event_type=event.get('type'),
            event_data=event,
            error_message=error_message,
            retry_count=0,
            next_retry_at=timezone.now() + timezone.timedelta(minutes=5)
        )