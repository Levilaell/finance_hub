"""
Stripe-only payment gateway service
Consolidated for production deployment with PCI DSS compliance
"""
import stripe
from django.conf import settings
from django.utils import timezone
from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PaymentGateway(ABC):
    """Abstract base class for payment gateways"""
    
    @abstractmethod
    def create_customer(self, company, user):
        """Create customer in payment gateway"""
        pass
    
    @abstractmethod
    def create_checkout_session(self, company, plan, billing_period, success_url, cancel_url):
        """Create checkout session for subscription"""
        pass
    
    @abstractmethod
    def create_payment_method(self, company, token, payment_data):
        """Store payment method"""
        pass
    
    @abstractmethod
    def cancel_subscription(self, subscription):
        """Cancel subscription"""
        pass
    
    @abstractmethod
    def get_subscription_status(self, subscription_id):
        """Get subscription status from gateway"""
        pass


class StripeGateway(PaymentGateway):
    """Stripe payment gateway implementation"""
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    def create_customer(self, company, user):
        """Create Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=company.name,
                metadata={
                    'company_id': str(company.id),
                    'user_id': str(user.id)
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed: {e}")
            raise
    
    def create_checkout_session(self, company, plan, billing_period, success_url, cancel_url):
        """Create Stripe checkout session using pre-configured price IDs"""
        try:
            # Get or create customer
            subscription = getattr(company, 'subscription', None)
            customer_id = subscription.stripe_customer_id if subscription else None
            
            if not customer_id:
                # Find primary user for company
                user = company.users.filter(is_company_admin=True).first()
                if not user:
                    user = company.users.first()
                customer_id = self.create_customer(company, user)
            
            # Use Stripe Price IDs instead of creating price_data dynamically
            price_id = None
            if billing_period == 'yearly':
                price_id = plan.stripe_price_id_yearly
            else:
                price_id = plan.stripe_price_id_monthly
            
            # Create line items based on whether we have price IDs
            if price_id:
                # Use pre-configured Stripe price ID (preferred)
                line_items = [{
                    'price': price_id,
                    'quantity': 1
                }]
                logger.info(f"Using Stripe price ID: {price_id} for plan: {plan.name}")
            else:
                # Fallback to dynamic price_data if IDs not configured
                logger.warning(f"No Stripe price ID for plan: {plan.name}, using dynamic pricing")
                price = plan.get_price(billing_period)
                interval = 'year' if billing_period == 'yearly' else 'month'
                line_items = [{
                    'price_data': {
                        'currency': 'brl',
                        'product_data': {
                            'name': plan.name,
                            'description': f'{plan.name} - {billing_period.title()} billing'
                        },
                        'unit_amount': int(price * 100),  # Convert to cents
                        'recurring': {
                            'interval': interval,
                            'interval_count': 1
                        }
                    },
                    'quantity': 1
                }]
            
            # Create checkout session with proper metadata
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=line_items,
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                # Store metadata at the session level for webhook processing
                metadata={
                    'company_id': str(company.id),
                    'plan_id': str(plan.id),
                    'billing_period': billing_period
                },
                subscription_data={
                    'trial_period_days': plan.trial_days if not subscription else 0,
                    'metadata': {
                        'company_id': str(company.id),
                        'plan_id': str(plan.id),
                        'billing_period': billing_period
                    }
                }
            )
            
            logger.info(f"Created checkout session {session.id} for company {company.id}")
            
            return {
                'session_id': session.id,
                'checkout_url': session.url
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe checkout session creation failed: {e}")
            raise
    
    def create_payment_method(self, company, token, payment_data):
        """Attach payment method to customer"""
        try:
            subscription = getattr(company, 'subscription', None)
            
            # Create customer if doesn't exist
            if not subscription or not subscription.stripe_customer_id:
                # Find primary user for company
                user = company.users.filter(is_company_admin=True).first()
                if not user:
                    user = company.users.first()
                    
                customer_id = self.create_customer(company, user)
                
                # Create or update subscription record
                from ..models import Subscription
                from apps.companies.models import SubscriptionPlan
                if not subscription:
                    # Get default plan (starter) for new subscriptions
                    default_plan = SubscriptionPlan.objects.filter(name='starter').first()
                    if not default_plan:
                        raise ValueError("No default plan available")
                        
                    subscription = Subscription.objects.create(
                        company=company,
                        plan=default_plan,
                        status='trial',
                        stripe_customer_id=customer_id,
                        trial_ends_at=timezone.now() + timezone.timedelta(days=14)
                    )
                else:
                    subscription.stripe_customer_id = customer_id
                    subscription.save()
            
            # Attach payment method to customer
            payment_method = stripe.PaymentMethod.attach(
                token,
                customer=subscription.stripe_customer_id
            )
            
            # Set as default if requested
            if payment_data.get('is_default'):
                stripe.Customer.modify(
                    subscription.stripe_customer_id,
                    invoice_settings={
                        'default_payment_method': payment_method.id
                    }
                )
            
            return payment_method.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe payment method creation failed: {e}")
            raise
    
    def cancel_subscription(self, subscription):
        """Cancel Stripe subscription"""
        try:
            if not subscription.stripe_subscription_id:
                return
            
            stripe_sub = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            return stripe_sub.canceled_at
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription cancellation failed: {e}")
            raise
    
    def get_subscription_status(self, subscription_id):
        """Get subscription status from Stripe"""
        try:
            stripe_sub = stripe.Subscription.retrieve(subscription_id)
            
            status_map = {
                'trialing': 'trial',
                'active': 'active',
                'past_due': 'past_due',
                'canceled': 'cancelled',
                'unpaid': 'past_due'
            }
            
            return {
                'status': status_map.get(stripe_sub.status, 'expired'),
                'current_period_start': timezone.datetime.fromtimestamp(
                    stripe_sub.current_period_start,
                    tz=timezone.utc
                ),
                'current_period_end': timezone.datetime.fromtimestamp(
                    stripe_sub.current_period_end,
                    tz=timezone.utc
                ),
                'cancel_at_period_end': stripe_sub.cancel_at_period_end
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve Stripe subscription: {e}")
            raise
    
    def verify_webhook(self, payload, signature):
        """Verify webhook signature"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return event
        except ValueError:
            logger.error("Invalid webhook payload")
            return None
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return None


class PaymentService:
    """Main payment service orchestrator"""
    
    def __init__(self):
        self.gateway = StripeGateway()  # Default to Stripe
    
    def create_checkout_session(self, company, plan, billing_period, success_url, cancel_url):
        """Create checkout session"""
        return self.gateway.create_checkout_session(
            company, plan, billing_period, success_url, cancel_url
        )
    
    def create_payment_method(self, company, token, payment_data):
        """Store payment method"""
        from ..models import PaymentMethod
        
        # Create payment method in gateway
        gateway_id = self.gateway.create_payment_method(company, token, payment_data)
        
        # Store in database
        payment_method = PaymentMethod.objects.create(
            company=company,
            type=payment_data['type'],
            is_default=payment_data.get('is_default', False),
            stripe_payment_method_id=gateway_id,
            brand=payment_data.get('brand', ''),
            last4=payment_data.get('last4', ''),
            exp_month=payment_data.get('exp_month'),
            exp_year=payment_data.get('exp_year')
        )
        
        return payment_method
    
    def cancel_subscription(self, subscription):
        """Cancel subscription"""
        cancelled_at = self.gateway.cancel_subscription(subscription)
        
        subscription.status = 'cancelled'
        subscription.cancelled_at = cancelled_at
        subscription.save()
        
        return subscription
    
    def sync_subscription_status(self, subscription):
        """Sync subscription status with payment gateway"""
        if not subscription.stripe_subscription_id:
            return subscription
        
        status_data = self.gateway.get_subscription_status(
            subscription.stripe_subscription_id
        )
        
        subscription.status = status_data['status']
        subscription.current_period_start = status_data['current_period_start']
        subscription.current_period_end = status_data['current_period_end']
        
        if status_data['cancel_at_period_end'] and not subscription.cancelled_at:
            subscription.cancelled_at = timezone.now()
        
        subscription.save()
        return subscription