"""
Production-ready Stripe webhook handlers
Comprehensive webhook event handling for all payment lifecycle events
"""
import logging
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from typing import Dict, Any, Optional
from django.core.mail import send_mail
from django.conf import settings
from .notification_service import notification_service
from .audit_service import PaymentAuditService

logger = logging.getLogger(__name__)


class ProductionWebhookHandlers:
    """Production-ready webhook handlers for comprehensive Stripe integration"""
    
    @staticmethod
    @transaction.atomic
    def handle_customer_created(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new Stripe customer creation"""
        from ..models import Subscription, SubscriptionPlan
        from apps.companies.models import Company
        
        customer = event['data']['object']
        metadata = customer.get('metadata', {})
        company_id = metadata.get('company_id')
        
        if not company_id:
            logger.warning(f"Customer created without company_id: {customer['id']}")
            return {'status': 'skipped', 'reason': 'No company_id in metadata'}
        
        try:
            company = Company.objects.get(id=company_id)
            
            # Create or update subscription record
            subscription, created = Subscription.objects.update_or_create(
                company=company,
                defaults={
                    'stripe_customer_id': customer['id'],
                    'status': 'pending',
                    'metadata': {
                        'customer_created': customer.get('created'),
                        'customer_email': customer.get('email')
                    }
                }
            )
            
            # Log customer creation
            PaymentAuditService.log_payment_action(
                action='customer_created',
                company=company,
                metadata={
                    'stripe_customer_id': customer['id'],
                    'subscription_id': subscription.id,
                    'created': created
                }
            )
            
            logger.info(f"Customer {customer['id']} {'created' if created else 'updated'} for company {company.name}")
            return {'status': 'success', 'subscription_id': subscription.id}
            
        except Company.DoesNotExist:
            logger.error(f"Company not found for customer creation: {company_id}")
            return {'status': 'error', 'message': 'Company not found'}
    
    @staticmethod
    @transaction.atomic
    def handle_subscription_schedule_created(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription schedule creation (for future dated subscriptions)"""
        from ..models import Subscription
        
        schedule = event['data']['object']
        customer_id = schedule.get('customer')
        
        try:
            subscription = Subscription.objects.get(stripe_customer_id=customer_id)
            
            # Store schedule information
            subscription.metadata['schedule_id'] = schedule['id']
            subscription.metadata['scheduled_start'] = schedule.get('phases', [{}])[0].get('start_date')
            subscription.save()
            
            # Log schedule creation
            PaymentAuditService.log_payment_action(
                action='subscription_scheduled',
                company=subscription.company,
                subscription_id=subscription.id,
                metadata={
                    'schedule_id': schedule['id'],
                    'phases': len(schedule.get('phases', [])),
                    'start_date': subscription.metadata.get('scheduled_start')
                }
            )
            
            return {'status': 'success'}
            
        except Subscription.DoesNotExist:
            logger.warning(f"Subscription not found for schedule: {customer_id}")
            return {'status': 'error', 'message': 'Subscription not found'}
    
    @staticmethod
    @transaction.atomic
    def handle_price_updated(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Stripe price updates"""
        from ..models import SubscriptionPlan
        
        price = event['data']['object']
        
        # Update plans with this price
        plans_updated = 0
        for plan in SubscriptionPlan.objects.filter(
            stripe_price_id_monthly=price['id']
        ) | SubscriptionPlan.objects.filter(
            stripe_price_id_yearly=price['id']
        ):
            if plan.stripe_price_id_monthly == price['id']:
                plan.price_monthly = Decimal(price['unit_amount']) / 100
            elif plan.stripe_price_id_yearly == price['id']:
                plan.price_yearly = Decimal(price['unit_amount']) / 100
            
            plan.metadata['price_updated_at'] = timezone.now().isoformat()
            plan.metadata['price_active'] = price.get('active', True)
            plan.save()
            plans_updated += 1
            
            # Log price update
            PaymentAuditService.log_payment_action(
                action='plan_price_updated',
                company=None,
                metadata={
                    'plan_id': plan.id,
                    'plan_name': plan.name,
                    'price_id': price['id'],
                    'new_amount': price['unit_amount'],
                    'currency': price.get('currency', 'brl').upper()
                }
            )
        
        logger.info(f"Price {price['id']} updated, affected {plans_updated} plans")
        return {'status': 'success', 'plans_updated': plans_updated}
    
    @staticmethod
    @transaction.atomic
    def handle_invoice_created(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice creation for upcoming charges"""
        from ..models import Subscription
        
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')
        
        if not subscription_id:
            return {'status': 'skipped', 'reason': 'No subscription'}
        
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=subscription_id
            )
            
            # Store upcoming invoice info
            subscription.metadata['upcoming_invoice'] = {
                'invoice_id': invoice['id'],
                'amount_due': invoice['amount_due'],
                'due_date': invoice.get('due_date'),
                'created': invoice.get('created')
            }
            subscription.save()
            
            # Send notification about upcoming charge
            amount = Decimal(invoice['amount_due']) / 100
            notification_service.notify_upcoming_charge(
                subscription.company.id,
                {
                    'subscription_id': subscription.id,
                    'amount': float(amount),
                    'currency': invoice['currency'].upper(),
                    'due_date': invoice.get('due_date')
                }
            )
            
            logger.info(f"Invoice created for {subscription.company.name}: {amount} {invoice['currency'].upper()}")
            return {'status': 'success'}
            
        except Subscription.DoesNotExist:
            return {'status': 'error', 'message': 'Subscription not found'}
    
    @staticmethod
    @transaction.atomic
    def handle_invoice_finalized(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice finalization before payment attempt"""
        from ..models import Subscription, Payment
        
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')
        
        if not subscription_id:
            return {'status': 'skipped', 'reason': 'No subscription'}
        
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=subscription_id
            )
            
            # Create pending payment record
            amount = Decimal(invoice['amount_due']) / 100
            payment = Payment.objects.create(
                company=subscription.company,
                subscription=subscription,
                amount=amount,
                currency=invoice['currency'].upper(),
                status='pending',
                description=f"Invoice {invoice.get('number', 'N/A')} - {subscription.plan.display_name}",
                gateway='stripe',
                stripe_invoice_id=invoice['id'],
                metadata={
                    'invoice_number': invoice.get('number'),
                    'billing_reason': invoice.get('billing_reason'),
                    'period_start': invoice.get('period_start'),
                    'period_end': invoice.get('period_end')
                }
            )
            
            # Log invoice finalization
            PaymentAuditService.log_payment_action(
                action='invoice_finalized',
                company=subscription.company,
                subscription_id=subscription.id,
                payment_id=payment.id,
                metadata={
                    'invoice_id': invoice['id'],
                    'amount': str(amount),
                    'attempt_count': invoice.get('attempt_count', 0)
                }
            )
            
            return {'status': 'success', 'payment_id': payment.id}
            
        except Subscription.DoesNotExist:
            return {'status': 'error', 'message': 'Subscription not found'}
    
    @staticmethod
    @transaction.atomic
    def handle_charge_succeeded(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful charge (one-time payments)"""
        from ..models import Payment
        from apps.companies.models import Company
        
        charge = event['data']['object']
        metadata = charge.get('metadata', {})
        
        # Handle one-time charges (not subscription related)
        if not charge.get('invoice'):
            company_id = metadata.get('company_id')
            if not company_id:
                return {'status': 'skipped', 'reason': 'No company_id'}
            
            try:
                company = Company.objects.get(id=company_id)
                
                # Create payment record for one-time charge
                amount = Decimal(charge['amount']) / 100
                payment = Payment.objects.create(
                    company=company,
                    amount=amount,
                    currency=charge['currency'].upper(),
                    status='succeeded',
                    description=charge.get('description', 'One-time payment'),
                    gateway='stripe',
                    stripe_payment_intent_id=charge.get('payment_intent'),
                    paid_at=timezone.now(),
                    metadata={
                        'charge_id': charge['id'],
                        'payment_method': charge.get('payment_method'),
                        'receipt_url': charge.get('receipt_url')
                    }
                )
                
                # Handle AI credit purchases
                if metadata.get('purchase_type') == 'ai_credits':
                    credits = int(metadata.get('credits', 0))
                    if credits > 0:
                        # Update company AI credits
                        company.ai_credits_balance = (
                            company.ai_credits_balance or 0
                        ) + credits
                        company.save()
                        
                        # Log credit purchase
                        PaymentAuditService.log_payment_action(
                            action='ai_credits_purchased',
                            company=company,
                            payment_id=payment.id,
                            metadata={
                                'credits': credits,
                                'amount': str(amount),
                                'new_balance': company.ai_credits_balance
                            }
                        )
                
                return {'status': 'success', 'payment_id': payment.id}
                
            except Company.DoesNotExist:
                return {'status': 'error', 'message': 'Company not found'}
        
        return {'status': 'skipped', 'reason': 'Invoice-related charge'}
    
    @staticmethod
    @transaction.atomic
    def handle_charge_failed(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed charge attempt"""
        from ..models import Payment
        
        charge = event['data']['object']
        failure_message = charge.get('failure_message', 'Unknown error')
        failure_code = charge.get('failure_code', 'unknown')
        
        # Log security event for certain failure codes
        security_failure_codes = [
            'fraudulent', 'stolen_card', 'pickup_card',
            'restricted_card', 'security_code_verification_failed'
        ]
        
        if failure_code in security_failure_codes:
            metadata = charge.get('metadata', {})
            company_id = metadata.get('company_id')
            
            PaymentAuditService.log_security_event(
                event_type='suspicious_payment_attempt',
                company_id=company_id,
                details={
                    'charge_id': charge['id'],
                    'failure_code': failure_code,
                    'failure_message': failure_message,
                    'amount': charge['amount'],
                    'card_last4': charge.get('payment_method_details', {}).get('card', {}).get('last4')
                }
            )
        
        logger.warning(f"Charge failed: {failure_code} - {failure_message}")
        return {'status': 'success'}
    
    @staticmethod
    @transaction.atomic
    def handle_subscription_paused(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription pause"""
        from ..models import Subscription
        
        stripe_sub = event['data']['object']
        
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_sub['id']
            )
            
            subscription.status = 'paused'
            subscription.metadata['paused_at'] = timezone.now().isoformat()
            subscription.metadata['pause_collection'] = stripe_sub.get('pause_collection', {})
            subscription.save()
            
            # Log subscription pause
            PaymentAuditService.log_payment_action(
                action='subscription_paused',
                company=subscription.company,
                subscription_id=subscription.id,
                metadata={
                    'resumes_at': stripe_sub.get('pause_collection', {}).get('resumes_at'),
                    'behavior': stripe_sub.get('pause_collection', {}).get('behavior')
                }
            )
            
            # Notify user
            notification_service.notify_subscription_updated(
                subscription.company.id,
                {
                    'subscription_id': subscription.id,
                    'status': 'paused',
                    'changes': {'paused': True}
                }
            )
            
            return {'status': 'success'}
            
        except Subscription.DoesNotExist:
            return {'status': 'error', 'message': 'Subscription not found'}
    
    @staticmethod
    @transaction.atomic
    def handle_subscription_resumed(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription resume after pause"""
        from ..models import Subscription
        
        stripe_sub = event['data']['object']
        
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_sub['id']
            )
            
            subscription.status = 'active'
            subscription.metadata['resumed_at'] = timezone.now().isoformat()
            subscription.metadata.pop('paused_at', None)
            subscription.metadata.pop('pause_collection', None)
            subscription.save()
            
            # Log subscription resume
            PaymentAuditService.log_payment_action(
                action='subscription_resumed',
                company=subscription.company,
                subscription_id=subscription.id,
                metadata={
                    'current_period_end': stripe_sub.get('current_period_end')
                }
            )
            
            return {'status': 'success'}
            
        except Subscription.DoesNotExist:
            return {'status': 'error', 'message': 'Subscription not found'}
    
    @staticmethod
    def handle_billing_portal_session_created(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer portal session creation"""
        session = event['data']['object']
        customer_id = session.get('customer')
        
        # Log portal access
        PaymentAuditService.log_payment_action(
            action='billing_portal_accessed',
            company=None,
            metadata={
                'customer_id': customer_id,
                'return_url': session.get('return_url'),
                'created': session.get('created')
            }
        )
        
        return {'status': 'success'}
    
    @staticmethod
    def handle_radar_early_fraud_warning(event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Stripe Radar fraud warnings"""
        warning = event['data']['object']
        charge_id = warning.get('charge')
        
        # Log critical security event
        PaymentAuditService.log_security_event(
            event_type='fraud_warning_received',
            company=None,
            details={
                'warning_id': warning['id'],
                'charge_id': charge_id,
                'fraud_type': warning.get('fraud_type'),
                'action_required': True
            },
            severity='critical'
        )
        
        # Send immediate alert to security team
        logger.critical(f"FRAUD WARNING: {warning['id']} for charge {charge_id}")
        
        return {'status': 'success'}