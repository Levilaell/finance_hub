"""
Production-ready Stripe payment service
Comprehensive subscription and payment management with PCI DSS compliance
"""
import stripe
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db import transaction
import logging
import json

logger = logging.getLogger(__name__)


class StripeService:
    """Production-ready Stripe payment processing service"""
    
    def __init__(self):
        """Initialize Stripe with API key"""
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.stripe = stripe
        
    # ========== Customer Management ==========
    
    def create_or_get_customer(self, company: 'Company', user: 'User') -> str:
        """
        Create or retrieve Stripe customer for a company
        
        Args:
            company: Company instance
            user: Primary user for the company
            
        Returns:
            Stripe customer ID
        """
        from ..models import Subscription
        
        # Check if customer already exists
        subscription = getattr(company, 'subscription', None)
        if subscription and subscription.stripe_customer_id:
            try:
                # Verify customer exists in Stripe
                customer = self.stripe.Customer.retrieve(subscription.stripe_customer_id)
                if not customer.deleted:
                    return customer.id
            except stripe.error.StripeError:
                logger.warning(f"Customer {subscription.stripe_customer_id} not found in Stripe")
        
        # Create new customer
        try:
            customer = self.stripe.Customer.create(
                email=user.email,
                name=company.name,
                metadata={
                    'company_id': str(company.id),
                    'user_id': str(user.id),
                    'environment': settings.ENVIRONMENT
                },
                tax_exempt='none',
                preferred_locales=['pt-BR', 'en']
            )
            
            logger.info(f"Created Stripe customer {customer.id} for company {company.name}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise
    
    def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update Stripe customer information
        
        Args:
            customer_id: Stripe customer ID
            updates: Dictionary of fields to update
            
        Returns:
            Updated customer data
        """
        try:
            customer = self.stripe.Customer.modify(customer_id, **updates)
            return customer.to_dict()
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update customer {customer_id}: {e}")
            raise
    
    # ========== Subscription Management ==========
    
    def create_subscription(self,
                          customer_id: str,
                          plan: 'SubscriptionPlan',
                          billing_period: str = 'monthly',
                          trial_days: Optional[int] = None,
                          payment_method_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new subscription
        
        Args:
            customer_id: Stripe customer ID
            plan: SubscriptionPlan instance
            billing_period: 'monthly' or 'yearly'
            trial_days: Number of trial days (overrides plan default)
            payment_method_id: Payment method to use
            
        Returns:
            Subscription data
        """
        try:
            # Get appropriate price ID
            price_id = (
                plan.stripe_price_id_yearly if billing_period == 'yearly'
                else plan.stripe_price_id_monthly
            )
            
            if not price_id:
                # Create price if not exists
                price_id = self.create_or_get_price(plan, billing_period)
            
            # Subscription parameters
            sub_params = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'metadata': {
                    'plan_id': str(plan.id),
                    'plan_name': plan.name,
                    'billing_period': billing_period
                },
                'expand': ['latest_invoice.payment_intent']
            }
            
            # Add trial period
            if trial_days is None:
                trial_days = plan.trial_days
            if trial_days:
                sub_params['trial_period_days'] = trial_days
            
            # Add payment method if provided
            if payment_method_id:
                sub_params['default_payment_method'] = payment_method_id
            
            # Create subscription
            subscription = self.stripe.Subscription.create(**sub_params)
            
            logger.info(f"Created subscription {subscription.id} for customer {customer_id}")
            return subscription.to_dict()
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {e}")
            raise
    
    def update_subscription(self,
                          subscription_id: str,
                          updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing subscription
        
        Args:
            subscription_id: Stripe subscription ID
            updates: Dictionary of fields to update
            
        Returns:
            Updated subscription data
        """
        try:
            # Handle plan changes
            if 'plan_id' in updates:
                plan_id = updates.pop('plan_id')
                billing_period = updates.pop('billing_period', 'monthly')
                
                # Get current subscription
                sub = self.stripe.Subscription.retrieve(subscription_id)
                
                # Update subscription item with new price
                from ..models import SubscriptionPlan
                plan = SubscriptionPlan.objects.get(id=plan_id)
                price_id = (
                    plan.stripe_price_id_yearly if billing_period == 'yearly'
                    else plan.stripe_price_id_monthly
                )
                
                if not price_id:
                    price_id = self.create_or_get_price(plan, billing_period)
                
                updates['items'] = [{
                    'id': sub['items']['data'][0].id,
                    'price': price_id
                }]
                
                # Set proration behavior
                updates['proration_behavior'] = 'create_prorations'
            
            subscription = self.stripe.Subscription.modify(subscription_id, **updates)
            return subscription.to_dict()
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription {subscription_id}: {e}")
            raise
    
    def cancel_subscription(self,
                          subscription_id: str,
                          immediately: bool = False,
                          feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel a subscription
        
        Args:
            subscription_id: Stripe subscription ID
            immediately: Cancel immediately vs end of period
            feedback: Cancellation reason/feedback
            
        Returns:
            Updated subscription data
        """
        try:
            params = {}
            
            if immediately:
                # Cancel immediately
                subscription = self.stripe.Subscription.delete(subscription_id)
            else:
                # Cancel at period end
                params['cancel_at_period_end'] = True
                if feedback:
                    params['cancellation_details'] = {'feedback': feedback}
                subscription = self.stripe.Subscription.modify(subscription_id, **params)
            
            logger.info(f"Cancelled subscription {subscription_id} ({'immediately' if immediately else 'at period end'})")
            return subscription.to_dict()
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {e}")
            raise
    
    def pause_subscription(self,
                         subscription_id: str,
                         resumes_at: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Pause a subscription
        
        Args:
            subscription_id: Stripe subscription ID
            resumes_at: When to resume (None = manual resume)
            
        Returns:
            Updated subscription data
        """
        try:
            pause_collection = {'behavior': 'mark_uncollectible'}
            if resumes_at:
                pause_collection['resumes_at'] = int(resumes_at.timestamp())
            
            subscription = self.stripe.Subscription.modify(
                subscription_id,
                pause_collection=pause_collection
            )
            
            logger.info(f"Paused subscription {subscription_id}")
            return subscription.to_dict()
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to pause subscription {subscription_id}: {e}")
            raise
    
    def resume_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Resume a paused subscription
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Updated subscription data
        """
        try:
            subscription = self.stripe.Subscription.modify(
                subscription_id,
                pause_collection=''
            )
            
            logger.info(f"Resumed subscription {subscription_id}")
            return subscription.to_dict()
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to resume subscription {subscription_id}: {e}")
            raise
    
    # ========== Payment Methods ==========
    
    def attach_payment_method(self,
                            payment_method_id: str,
                            customer_id: str,
                            set_default: bool = True) -> Dict[str, Any]:
        """
        Attach a payment method to a customer
        
        Args:
            payment_method_id: Stripe payment method ID
            customer_id: Stripe customer ID
            set_default: Set as default payment method
            
        Returns:
            Payment method data
        """
        try:
            # Attach payment method
            payment_method = self.stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            
            # Set as default if requested
            if set_default:
                self.stripe.Customer.modify(
                    customer_id,
                    invoice_settings={
                        'default_payment_method': payment_method_id
                    }
                )
            
            logger.info(f"Attached payment method {payment_method_id} to customer {customer_id}")
            return payment_method.to_dict()
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to attach payment method: {e}")
            raise
    
    def detach_payment_method(self, payment_method_id: str) -> Dict[str, Any]:
        """
        Detach a payment method from a customer
        
        Args:
            payment_method_id: Stripe payment method ID
            
        Returns:
            Payment method data
        """
        try:
            payment_method = self.stripe.PaymentMethod.detach(payment_method_id)
            logger.info(f"Detached payment method {payment_method_id}")
            return payment_method.to_dict()
        except stripe.error.StripeError as e:
            logger.error(f"Failed to detach payment method: {e}")
            raise
    
    def list_payment_methods(self, customer_id: str, type: str = 'card') -> List[Dict[str, Any]]:
        """
        List customer payment methods
        
        Args:
            customer_id: Stripe customer ID
            type: Payment method type (default: 'card')
            
        Returns:
            List of payment methods
        """
        try:
            payment_methods = self.stripe.PaymentMethod.list(
                customer=customer_id,
                type=type
            )
            return [pm.to_dict() for pm in payment_methods.data]
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list payment methods: {e}")
            raise
    
    # ========== One-time Payments ==========
    
    def create_payment_intent(self,
                            amount: Decimal,
                            currency: str = 'brl',
                            customer_id: Optional[str] = None,
                            payment_method_id: Optional[str] = None,
                            description: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None,
                            confirm: bool = True) -> Dict[str, Any]:
        """
        Create a payment intent for one-time payment
        
        Args:
            amount: Payment amount
            currency: Currency code
            customer_id: Stripe customer ID
            payment_method_id: Payment method to use
            description: Payment description
            metadata: Additional metadata
            confirm: Auto-confirm the payment
            
        Returns:
            Payment intent data
        """
        try:
            params = {
                'amount': int(amount * 100),  # Convert to cents
                'currency': currency,
                'automatic_payment_methods': {'enabled': True}
            }
            
            if customer_id:
                params['customer'] = customer_id
            if payment_method_id:
                params['payment_method'] = payment_method_id
            if description:
                params['description'] = description
            if metadata:
                params['metadata'] = metadata
            if confirm and payment_method_id:
                params['confirm'] = True
            
            payment_intent = self.stripe.PaymentIntent.create(**params)
            
            logger.info(f"Created payment intent {payment_intent.id} for {amount} {currency}")
            return payment_intent.to_dict()
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            raise
    
    @classmethod
    def process_credit_purchase(cls,
                              company: 'Company',
                              payment_method: 'PaymentMethod',
                              amount: Decimal,
                              description: str,
                              credits: int) -> Dict[str, Any]:
        """
        Process AI credit purchase via Stripe
        
        Args:
            company: Company instance
            payment_method: PaymentMethod instance
            amount: Payment amount
            description: Payment description
            credits: Number of credits to purchase
            
        Returns:
            Payment result dictionary
        """
        service = cls()
        
        try:
            # Get customer ID
            from ..models import Subscription
            subscription = getattr(company, 'subscription', None)
            if not subscription or not subscription.stripe_customer_id:
                raise ValueError("No Stripe customer found for company")
            
            # Create payment intent
            payment_intent = service.create_payment_intent(
                amount=amount,
                customer_id=subscription.stripe_customer_id,
                payment_method_id=payment_method.stripe_payment_method_id,
                description=description,
                metadata={
                    'company_id': str(company.id),
                    'purchase_type': 'ai_credits',
                    'credits': credits
                },
                confirm=True
            )
            
            # Check payment status
            if payment_intent['status'] == 'succeeded':
                return {
                    'success': True,
                    'payment_id': payment_intent['id'],
                    'gateway': 'stripe',
                    'status': 'succeeded',
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'payment_id': payment_intent['id'],
                    'gateway': 'stripe',
                    'status': payment_intent['status'],
                    'error': 'Payment requires additional action'
                }
                
        except stripe.error.CardError as e:
            logger.error(f"Card error during credit purchase: {e}")
            return {
                'success': False,
                'payment_id': None,
                'gateway': 'stripe',
                'status': 'failed',
                'error': e.user_message or 'Card was declined'
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error during credit purchase: {e}")
            return {
                'success': False,
                'payment_id': None,
                'gateway': 'stripe',
                'status': 'failed',
                'error': 'Payment processing error'
            }
        except Exception as e:
            logger.error(f"Unexpected error during credit purchase: {e}")
            return {
                'success': False,
                'payment_id': None,
                'gateway': 'stripe',
                'status': 'failed',
                'error': 'An unexpected error occurred'
            }
    
    # ========== Invoices & Billing ==========
    
    def retrieve_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Retrieve an invoice
        
        Args:
            invoice_id: Stripe invoice ID
            
        Returns:
            Invoice data
        """
        try:
            invoice = self.stripe.Invoice.retrieve(invoice_id)
            return invoice.to_dict()
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve invoice {invoice_id}: {e}")
            raise
    
    def list_invoices(self,
                     customer_id: Optional[str] = None,
                     subscription_id: Optional[str] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """
        List invoices
        
        Args:
            customer_id: Filter by customer
            subscription_id: Filter by subscription
            limit: Maximum number of invoices
            
        Returns:
            List of invoices
        """
        try:
            params = {'limit': limit}
            if customer_id:
                params['customer'] = customer_id
            if subscription_id:
                params['subscription'] = subscription_id
            
            invoices = self.stripe.Invoice.list(**params)
            return [inv.to_dict() for inv in invoices.data]
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list invoices: {e}")
            raise
    
    def upcoming_invoice(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get upcoming invoice for a customer
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            Upcoming invoice data or None
        """
        try:
            invoice = self.stripe.Invoice.upcoming(customer=customer_id)
            return invoice.to_dict()
        except stripe.error.InvalidRequestError:
            # No upcoming invoice
            return None
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get upcoming invoice: {e}")
            raise
    
    # ========== Prices & Products ==========
    
    def create_or_get_price(self, plan: 'SubscriptionPlan', billing_period: str) -> str:
        """
        Create or retrieve a Stripe price for a plan
        
        Args:
            plan: SubscriptionPlan instance
            billing_period: 'monthly' or 'yearly'
            
        Returns:
            Stripe price ID
        """
        try:
            # Create product if not exists
            product_id = f"prod_{plan.slug}_{settings.ENVIRONMENT}"
            
            try:
                product = self.stripe.Product.retrieve(product_id)
            except stripe.error.InvalidRequestError:
                # Create product
                product = self.stripe.Product.create(
                    id=product_id,
                    name=plan.display_name,
                    description=f"{plan.display_name} subscription plan",
                    metadata={
                        'plan_id': str(plan.id),
                        'environment': settings.ENVIRONMENT
                    }
                )
            
            # Create price
            amount = plan.price_yearly if billing_period == 'yearly' else plan.price_monthly
            interval = 'year' if billing_period == 'yearly' else 'month'
            
            price = self.stripe.Price.create(
                product=product.id,
                unit_amount=int(amount * 100),  # Convert to cents
                currency='brl',
                recurring={
                    'interval': interval,
                    'interval_count': 1
                },
                metadata={
                    'plan_id': str(plan.id),
                    'billing_period': billing_period
                }
            )
            
            # Update plan with price ID
            if billing_period == 'yearly':
                plan.stripe_price_id_yearly = price.id
            else:
                plan.stripe_price_id_monthly = price.id
            plan.save()
            
            logger.info(f"Created price {price.id} for plan {plan.name}")
            return price.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create price: {e}")
            raise
    
    # ========== Usage & Metering ==========
    
    def report_usage(self,
                    subscription_item_id: str,
                    quantity: int,
                    timestamp: Optional[datetime] = None,
                    action: str = 'increment') -> Dict[str, Any]:
        """
        Report usage for metered billing
        
        Args:
            subscription_item_id: Stripe subscription item ID
            quantity: Usage quantity
            timestamp: When the usage occurred
            action: 'increment' or 'set'
            
        Returns:
            Usage record data
        """
        try:
            params = {
                'quantity': quantity,
                'action': action
            }
            
            if timestamp:
                params['timestamp'] = int(timestamp.timestamp())
            else:
                params['timestamp'] = int(timezone.now().timestamp())
            
            usage_record = self.stripe.SubscriptionItem.create_usage_record(
                subscription_item_id,
                **params
            )
            
            return usage_record.to_dict()
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to report usage: {e}")
            raise
    
    # ========== Customer Portal ==========
    
    def create_billing_portal_session(self,
                                    customer_id: str,
                                    return_url: str) -> Dict[str, Any]:
        """
        Create a billing portal session for customer self-service
        
        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal
            
        Returns:
            Portal session data with URL
        """
        try:
            session = self.stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            
            logger.info(f"Created billing portal session for customer {customer_id}")
            return session.to_dict()
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create billing portal session: {e}")
            raise
    
    # ========== Utility Methods ==========
    
    def get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get detailed subscription status
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Subscription status information
        """
        try:
            subscription = self.stripe.Subscription.retrieve(
                subscription_id,
                expand=['latest_invoice', 'customer.default_source']
            )
            
            return {
                'status': subscription.status,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'current_period_start': datetime.fromtimestamp(
                    subscription.current_period_start, tz=timezone.utc
                ),
                'current_period_end': datetime.fromtimestamp(
                    subscription.current_period_end, tz=timezone.utc
                ),
                'trial_end': datetime.fromtimestamp(
                    subscription.trial_end, tz=timezone.utc
                ) if subscription.trial_end else None,
                'has_payment_method': bool(subscription.default_payment_method),
                'latest_invoice': {
                    'status': subscription.latest_invoice.status,
                    'amount_due': subscription.latest_invoice.amount_due,
                    'amount_paid': subscription.latest_invoice.amount_paid
                } if subscription.latest_invoice else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get subscription status: {e}")
            raise
    
    def calculate_proration(self,
                          subscription_id: str,
                          new_price_id: str) -> Tuple[Decimal, List[Dict[str, Any]]]:
        """
        Calculate proration for subscription change
        
        Args:
            subscription_id: Current subscription ID
            new_price_id: New price ID to switch to
            
        Returns:
            Tuple of (proration_amount, line_items)
        """
        try:
            # Preview the proration
            invoice = self.stripe.Invoice.upcoming(
                customer=self.stripe.Subscription.retrieve(subscription_id).customer,
                subscription=subscription_id,
                subscription_items=[{
                    'id': self.stripe.Subscription.retrieve(subscription_id)['items']['data'][0].id,
                    'price': new_price_id
                }],
                subscription_proration_behavior='create_prorations'
            )
            
            proration_amount = Decimal(invoice.amount_due - invoice.amount_paid) / 100
            line_items = [
                {
                    'description': item.description,
                    'amount': item.amount,
                    'period': {
                        'start': datetime.fromtimestamp(item.period.start, tz=timezone.utc),
                        'end': datetime.fromtimestamp(item.period.end, tz=timezone.utc)
                    }
                }
                for item in invoice.lines.data
            ]
            
            return proration_amount, line_items
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to calculate proration: {e}")
            raise