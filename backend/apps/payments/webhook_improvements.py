"""
Improvements for webhook handling
"""
import logging
from typing import Dict, Any
from django.utils import timezone
from decimal import Decimal

logger = logging.getLogger(__name__)


class ImprovedWebhookHandlers:
    """Additional webhook handlers for better payment synchronization"""
    
    @staticmethod
    def handle_invoice_payment_succeeded(data: Dict[str, Any]):
        """Handle successful renewal payments"""
        from apps.companies.models import Company, PaymentHistory
        
        invoice = data['object']
        subscription_id = invoice.get('subscription')
        
        if not subscription_id:
            logger.warning("Invoice without subscription ID")
            return
            
        try:
            company = Company.objects.get(subscription_id=subscription_id)
            
            # Create payment history for renewal
            PaymentHistory.objects.create(
                company=company,
                subscription_plan=company.subscription_plan,
                transaction_type='renewal',
                amount=Decimal(invoice['amount_paid']) / 100,
                currency=invoice['currency'].upper(),
                status='paid',
                description=f'Renovação automática - {company.subscription_plan.name}',
                invoice_number=invoice['number'],
                invoice_url=invoice['invoice_pdf'],
                transaction_date=timezone.now(),
                paid_at=timezone.now(),
                stripe_payment_intent_id=invoice.get('payment_intent'),
                payment_method_display='Cartão salvo'
            )
            
            # Update next billing date
            if invoice.get('lines', {}).get('data'):
                line = invoice['lines']['data'][0]
                period_end = line.get('period', {}).get('end')
                if period_end:
                    from datetime import datetime
                    company.next_billing_date = datetime.fromtimestamp(period_end).date()
                    company.save()
            
            logger.info(f"Renewal payment recorded for company {company.id}")
            
        except Company.DoesNotExist:
            logger.error(f"Company not found for subscription {subscription_id}")
    
    @staticmethod
    def handle_payment_method_attached(data: Dict[str, Any]):
        """Handle when a payment method is attached to customer"""
        from apps.companies.models import PaymentMethod
        from apps.authentication.models import User
        
        payment_method = data['object']
        customer_id = payment_method.get('customer')
        
        if not customer_id:
            return
            
        try:
            user = User.objects.get(payment_customer_id=customer_id)
            company = user.company
            
            # Check if payment method already exists
            if PaymentMethod.objects.filter(
                stripe_payment_method_id=payment_method['id']
            ).exists():
                return
            
            # Save payment method details
            card = payment_method.get('card', {})
            PaymentMethod.objects.create(
                company=company,
                payment_type='credit_card',
                card_brand=card.get('brand', '').upper(),
                last_four=card.get('last4'),
                exp_month=card.get('exp_month'),
                exp_year=card.get('exp_year'),
                stripe_payment_method_id=payment_method['id'],
                is_default=not PaymentMethod.objects.filter(
                    company=company, 
                    is_default=True
                ).exists(),
                is_active=True
            )
            
            logger.info(f"Payment method saved for company {company.id}")
            
        except User.DoesNotExist:
            logger.error(f"User not found for customer {customer_id}")
    
    @staticmethod
    def handle_subscription_trial_will_end(data: Dict[str, Any]):
        """Handle trial ending soon notification"""
        from apps.companies.models import Company
        from apps.notifications.email_service import EmailService
        
        subscription = data['object']
        subscription_id = subscription['id']
        
        try:
            company = Company.objects.get(subscription_id=subscription_id)
            
            # Send trial ending email
            email_service = EmailService()
            email_service.send_trial_ending_email(
                email=company.owner.email,
                company_name=company.name,
                owner_name=company.owner.get_full_name(),
                days_remaining=3  # Stripe sends this 3 days before
            )
            
            logger.info(f"Trial ending notification sent for company {company.id}")
            
        except Company.DoesNotExist:
            logger.error(f"Company not found for subscription {subscription_id}")
    
    @staticmethod
    def handle_charge_failed(data: Dict[str, Any]):
        """Handle failed payment attempts"""
        from apps.companies.models import Company, PaymentHistory
        
        charge = data['object']
        customer_id = charge.get('customer')
        
        if not customer_id:
            return
            
        try:
            from apps.authentication.models import User
            user = User.objects.get(payment_customer_id=customer_id)
            company = user.company
            
            # Record failed payment
            PaymentHistory.objects.create(
                company=company,
                subscription_plan=company.subscription_plan,
                transaction_type='charge',
                amount=Decimal(charge['amount']) / 100,
                currency=charge['currency'].upper(),
                status='failed',
                description=f'Falha na cobrança - {charge.get("failure_message", "Erro desconhecido")}',
                transaction_date=timezone.now(),
                stripe_payment_intent_id=charge.get('payment_intent')
            )
            
            # Update subscription status if needed
            if company.subscription_status == 'active':
                company.subscription_status = 'past_due'
                company.save()
            
            logger.warning(f"Payment failed for company {company.id}")
            
        except User.DoesNotExist:
            logger.error(f"User not found for customer {customer_id}")


def get_checkout_session_details(session_id: str) -> Dict[str, Any]:
    """Fetch complete checkout session details including payment method"""
    import stripe
    from django.conf import settings
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    try:
        # Expand payment intent and payment method
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=['payment_intent.payment_method']
        )
        
        payment_method = None
        if session.payment_intent and hasattr(session.payment_intent, 'payment_method'):
            payment_method = session.payment_intent.payment_method
            
        return {
            'session': session,
            'payment_method': payment_method
        }
    except Exception as e:
        logger.error(f"Error fetching checkout session details: {e}")
        return {}