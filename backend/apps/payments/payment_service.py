"""
Payment service for handling subscriptions and payments
Supports multiple payment gateways: Stripe, MercadoPago, etc.
"""
import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from ..companies.models import PaymentHistory
from django.conf import settings
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class PaymentGateway(ABC):
    """Abstract base class for payment gateways"""
    
    @abstractmethod
    def create_customer(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a customer in the payment gateway"""
        pass
    
    @abstractmethod
    def create_subscription(self, customer_id: str, plan_id: str) -> Dict[str, Any]:
        """Create a subscription for a customer"""
        pass
    
    @abstractmethod
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription"""
        pass
    
    @abstractmethod
    def update_subscription(self, subscription_id: str, new_plan_id: str) -> Dict[str, Any]:
        """Update subscription to a new plan"""
        pass
    
    @abstractmethod
    def create_payment_method(self, customer_id: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a payment method for a customer"""
        pass
    
    @abstractmethod
    def charge_customer(self, customer_id: str, amount: Decimal, description: str) -> Dict[str, Any]:
        """Charge a customer one-time"""
        pass
    
    @abstractmethod
    def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> Dict[str, Any]:
        """Refund a payment"""
        pass
    
    @abstractmethod
    def get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """Get current subscription status"""
        pass
    
    @abstractmethod
    def handle_webhook(self, payload: Dict[str, Any], signature: str) -> Dict[str, Any]:
        """Handle webhook from payment gateway"""
        pass


class StripeGateway(PaymentGateway):
    """Stripe payment gateway implementation"""
    
    def __init__(self):
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            self.stripe = stripe
            self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        except ImportError:
            logger.error("Stripe library not installed. Run: pip install stripe")
            raise
        except AttributeError:
            logger.error("Stripe credentials not configured in settings")
            raise
    
    def create_customer(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Stripe customer"""
        try:
            customer = self.stripe.Customer.create(
                email=user_data['email'],
                name=user_data.get('name', ''),
                metadata={
                    'user_id': user_data['user_id'],
                    'company_id': user_data.get('company_id', '')
                }
            )
            return {
                'customer_id': customer.id,
                'gateway': 'stripe',
                'data': customer
            }
        except Exception as e:
            logger.error(f"Error creating Stripe customer: {e}")
            raise
    
    def create_subscription(self, customer_id: str, plan_id: str) -> Dict[str, Any]:
        """Create a Stripe subscription"""
        try:
            subscription = self.stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': plan_id}],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent']
            )
            return {
                'subscription_id': subscription.id,
                'status': subscription.status,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None,
                'data': subscription
            }
        except Exception as e:
            logger.error(f"Error creating Stripe subscription: {e}")
            raise
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a Stripe subscription"""
        try:
            subscription = self.stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return subscription.cancel_at_period_end
        except Exception as e:
            logger.error(f"Error canceling Stripe subscription: {e}")
            raise
    


    def create_payment_method(self, customer_id: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a payment method for Stripe customer"""
        try:
            payment_method = self.stripe.PaymentMethod.attach(
                payment_data['payment_method_id'],
                customer=customer_id
            )
            
            # Set as default payment method
            self.stripe.Customer.modify(
                customer_id,
                invoice_settings={'default_payment_method': payment_method.id}
            )
            
            return {
                'payment_method_id': payment_method.id,
                'type': payment_method.type,
                'data': payment_method
            }
        except Exception as e:
            logger.error(f"Error creating payment method: {e}")
            raise
    
    def charge_customer(self, customer_id: str, amount: Decimal, description: str) -> Dict[str, Any]:
        """Create a one-time charge"""
        try:
            charge = self.stripe.Charge.create(
                customer=customer_id,
                amount=int(amount * 100),  # Convert to cents
                currency='brl',
                description=description
            )
            return {
                'charge_id': charge.id,
                'status': charge.status,
                'amount': amount,
                'data': charge
            }
        except Exception as e:
            logger.error(f"Error charging customer: {e}")
            raise
    
    def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> Dict[str, Any]:
        """Refund a Stripe payment"""
        try:
            refund_data = {'charge': payment_id}
            if amount:
                refund_data['amount'] = int(amount * 100)
            
            refund = self.stripe.Refund.create(**refund_data)
            return {
                'refund_id': refund.id,
                'status': refund.status,
                'amount': Decimal(refund.amount) / 100,
                'data': refund
            }
        except Exception as e:
            logger.error(f"Error refunding payment: {e}")
            raise
    
    def get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """Get Stripe subscription status"""
        try:
            subscription = self.stripe.Subscription.retrieve(subscription_id)
            return {
                'status': subscription.status,
                'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'data': subscription
            }
        except Exception as e:
            logger.error(f"Error getting subscription status: {e}")
            raise
    
    def handle_webhook(self, payload: Dict[str, Any], signature: str) -> Dict[str, Any]:
        """Handle Stripe webhook"""
        try:
            event = self.stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            return {
                'event_type': event['type'],
                'event_id': event['id'],
                'data': event['data']
            }
        except Exception as e:
            logger.error(f"Error handling Stripe webhook: {e}")
            raise


class MercadoPagoGateway(PaymentGateway):
    """MercadoPago payment gateway implementation"""
    
    def __init__(self):
        try:
            import mercadopago
            sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
            self.mp = sdk
        except ImportError:
            logger.error("MercadoPago library not installed. Run: pip install mercadopago")
            raise
        except AttributeError:
            logger.error("MercadoPago credentials not configured in settings")
            raise
    
    def create_customer(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a MercadoPago customer"""
        try:
            customer_data = {
                "email": user_data['email'],
                "first_name": user_data.get('first_name', ''),
                "last_name": user_data.get('last_name', ''),
                "identification": {
                    "type": user_data.get('doc_type', 'CPF'),
                    "number": user_data.get('doc_number', '')
                }
            }
            
            result = self.mp.customer().create(customer_data)
            
            if result["status"] == 201:
                return {
                    'customer_id': result["response"]["id"],
                    'gateway': 'mercadopago',
                    'data': result["response"]
                }
            else:
                raise Exception(f"Failed to create customer: {result}")
        except Exception as e:
            logger.error(f"Error creating MercadoPago customer: {e}")
            raise
    
    def create_subscription(self, customer_id: str, plan_id: str) -> Dict[str, Any]:
        """Create a MercadoPago subscription"""
        try:
            subscription_data = {
                "plan_id": plan_id,
                "payer": {
                    "id": customer_id
                },
                "back_url": f"{settings.FRONTEND_URL}/subscription/success",
                "auto_recurring": {
                    "frequency": 1,
                    "frequency_type": "months",
                    "currency_id": "BRL"
                }
            }
            
            result = self.mp.subscription().create(subscription_data)
            
            if result["status"] == 201:
                return {
                    'subscription_id': result["response"]["id"],
                    'status': result["response"]["status"],
                    'init_point': result["response"]["init_point"],
                    'data': result["response"]
                }
            else:
                raise Exception(f"Failed to create subscription: {result}")
        except Exception as e:
            logger.error(f"Error creating MercadoPago subscription: {e}")
            raise
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a MercadoPago subscription"""
        try:
            result = self.mp.subscription().update(
                subscription_id,
                {"status": "cancelled"}
            )
            return result["status"] == 200
        except Exception as e:
            logger.error(f"Error canceling MercadoPago subscription: {e}")
            raise
    
    def update_subscription(self, subscription_id: str, new_plan_id: str) -> Dict[str, Any]:
        """Update MercadoPago subscription"""
        # MercadoPago doesn't support direct plan updates
        # Need to cancel current and create new subscription
        raise NotImplementedError("MercadoPago requires canceling and creating new subscription")
    
    def create_payment_method(self, customer_id: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a payment method for MercadoPago customer"""
        try:
            card_data = {
                "customer_id": customer_id,
                "token": payment_data['token']
            }
            
            result = self.mp.card().create(card_data)
            
            if result["status"] == 201:
                return {
                    'payment_method_id': result["response"]["id"],
                    'type': 'card',
                    'data': result["response"]
                }
            else:
                raise Exception(f"Failed to create payment method: {result}")
        except Exception as e:
            logger.error(f"Error creating payment method: {e}")
            raise
    
    def charge_customer(self, customer_id: str, amount: Decimal, description: str) -> Dict[str, Any]:
        """Create a one-time payment"""
        try:
            payment_data = {
                "transaction_amount": float(amount),
                "description": description,
                "payment_method_id": "pix",  # Using PIX by default
                "payer": {
                    "id": customer_id
                }
            }
            
            result = self.mp.payment().create(payment_data)
            
            if result["status"] == 201:
                return {
                    'charge_id': result["response"]["id"],
                    'status': result["response"]["status"],
                    'amount': amount,
                    'data': result["response"]
                }
            else:
                raise Exception(f"Failed to create payment: {result}")
        except Exception as e:
            logger.error(f"Error charging customer: {e}")
            raise
    
    def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> Dict[str, Any]:
        """Refund a MercadoPago payment"""
        try:
            refund_data = {}
            if amount:
                refund_data['amount'] = float(amount)
            
            result = self.mp.refund().create(payment_id, refund_data)
            
            if result["status"] == 201:
                return {
                    'refund_id': result["response"]["id"],
                    'status': result["response"]["status"],
                    'amount': Decimal(result["response"]["amount"]),
                    'data': result["response"]
                }
            else:
                raise Exception(f"Failed to create refund: {result}")
        except Exception as e:
            logger.error(f"Error refunding payment: {e}")
            raise
    
    def get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """Get MercadoPago subscription status"""
        try:
            result = self.mp.subscription().get(subscription_id)
            
            if result["status"] == 200:
                subscription = result["response"]
                return {
                    'status': subscription["status"],
                    'current_period_end': subscription.get("date_of_expiration"),
                    'data': subscription
                }
            else:
                raise Exception(f"Failed to get subscription: {result}")
        except Exception as e:
            logger.error(f"Error getting subscription status: {e}")
            raise
    
    def handle_webhook(self, payload: Dict[str, Any], signature: str) -> Dict[str, Any]:
        """Handle MercadoPago webhook"""
        try:
            # MercadoPago uses query params for webhook validation
            return {
                'event_type': payload.get('type'),
                'event_id': payload.get('id'),
                'data': payload.get('data', {})
            }
        except Exception as e:
            logger.error(f"Error handling MercadoPago webhook: {e}")
            raise


class PaymentService:
    """Main payment service that manages different gateways"""
    
    def __init__(self, gateway_name: Optional[str] = None):
        self.gateway_name = gateway_name or settings.DEFAULT_PAYMENT_GATEWAY
        self.gateway = self._get_gateway()
    
    def _get_gateway(self) -> PaymentGateway:
        """Get the appropriate payment gateway"""
        gateways = {
            'stripe': StripeGateway,
            'mercadopago': MercadoPagoGateway,
        }
        
        gateway_class = gateways.get(self.gateway_name)
        if not gateway_class:
            raise ValueError(f"Unknown payment gateway: {self.gateway_name}")
        
        return gateway_class()
    
    def create_customer(self, user) -> Dict[str, Any]:
        """Create a customer in the payment gateway"""
        user_data = {
            'user_id': user.id,
            'email': user.email,
            'name': user.get_full_name(),
            'company_id': user.company.id if hasattr(user, 'company') else None
        }
        
        result = self.gateway.create_customer(user_data)
        
        # Save customer ID to user profile
        user.payment_customer_id = result['customer_id']
        user.payment_gateway = self.gateway_name
        user.save(update_fields=['payment_customer_id', 'payment_gateway'])
        
        return result
    
    def create_subscription(self, company, plan, billing_cycle='monthly'):
        """Create a subscription for a company with proper error handling"""
        # Ensure customer exists
        if not company.owner.payment_customer_id:
            self.create_customer(company.owner)
        
        # Get correct price ID based on billing cycle and gateway
        if self.gateway_name == 'stripe':
            price_id = plan.stripe_price_id
        elif self.gateway_name == 'mercadopago':
            price_id = plan.mercadopago_plan_id
        else:
            raise ValueError(f"No price ID configured for {self.gateway_name}")
        
        if not price_id:
            raise ValueError(f"Plan {plan.name} not configured for {self.gateway_name}")
        
        # Create subscription
        try:
            result = self.gateway.create_subscription(
                customer_id=company.owner.payment_customer_id,
                plan_id=price_id
            )
            
            # Update company subscription info
            with transaction.atomic():
                company.subscription_id = result['subscription_id']
                company.subscription_plan = plan
                company.subscription_status = 'pending'  # Will be updated by webhook
                company.billing_cycle = billing_cycle
                company.subscription_start_date = timezone.now()
                
                # Calculate next billing date
                if billing_cycle == 'yearly':
                    company.next_billing_date = timezone.now().date() + timedelta(days=365)
                else:
                    # Add one month
                    next_month = timezone.now().date().replace(day=1) + timedelta(days=32)
                    company.next_billing_date = next_month.replace(day=1)
                
                company.save()
                
                # Log payment history
                PaymentHistory.objects.create(
                    company=company,
                    subscription_plan=plan,
                    transaction_type='subscription',
                    amount=plan.price_yearly if billing_cycle == 'yearly' else plan.price_monthly,
                    currency='BRL',
                    status='pending',
                    description=f'Assinatura {plan.name} - Ciclo {billing_cycle}',
                    transaction_date=timezone.now()
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            # Rollback any changes
            company.subscription_status = 'trial'
            company.save()
            raise
    
    def cancel_subscription(self, company) -> bool:
        """Cancel a company's subscription"""
        if not company.subscription_id:
            raise ValueError("Company has no active subscription")
        
        success = self.gateway.cancel_subscription(company.subscription_id)
        
        if success:
            company.subscription_status = 'cancelled'
            company.subscription_end_date = timezone.now()
            company.save()
        
        return success
    
    def handle_webhook(self, request) -> Dict[str, Any]:
        """Handle payment gateway webhooks"""
        # Get webhook data based on gateway
        if self.gateway_name == 'stripe':
            payload = request.body
            signature = request.META.get('HTTP_STRIPE_SIGNATURE')
        elif self.gateway_name == 'mercadopago':
            payload = request.GET.dict()
            signature = None
        else:
            raise ValueError(f"Webhook handling not implemented for {self.gateway_name}")
        
        event_data = self.gateway.handle_webhook(payload, signature)
        
        # Process event based on type
        self._process_webhook_event(event_data)
        
        return event_data
    
    def _process_webhook_event(self, event_data: Dict[str, Any]):
        """Process webhook events"""
        event_type = event_data['event_type']
        
        # Stripe events
        if 'subscription' in event_type:
            self._handle_subscription_event(event_type, event_data['data'])
        elif 'payment_intent' in event_type:
            self._handle_payment_event(event_type, event_data['data'])
        elif 'invoice' in event_type:
            self._handle_invoice_event(event_type, event_data['data'])
        
        # Add more event handlers as needed
    
    def _handle_subscription_event(self, event_type: str, data: Dict[str, Any]):
        """Handle subscription-related events"""
        from apps.companies.models import Company
        
        subscription_id = data['object']['id']
        
        try:
            company = Company.objects.get(subscription_id=subscription_id)
            
            if event_type == 'customer.subscription.created':
                company.subscription_status = 'active'
            elif event_type == 'customer.subscription.updated':
                company.subscription_status = data['object']['status']
            elif event_type == 'customer.subscription.deleted':
                company.subscription_status = 'cancelled'
                company.subscription_end_date = timezone.now()
            
            company.save()
            
        except Company.DoesNotExist:
            logger.warning(f"Company not found for subscription {subscription_id}")
    
    def _handle_payment_event(self, event_type: str, data: Dict[str, Any]):
        """Handle payment-related events"""
        # Implement payment event handling
        pass
    
    def _handle_invoice_event(self, event_type: str, data: Dict[str, Any]):
        """Handle invoice-related events"""
        # Implement invoice event handling
        pass

    def update_subscription(self, company, new_plan, billing_cycle='monthly'):
        """Update subscription with proration"""
        if not company.subscription_id:
            # No existing subscription, create new one
            return self.create_subscription(company, new_plan, billing_cycle)
        
        try:
            # Get correct price ID
            if self.gateway_name == 'stripe':
                price_id = new_plan.stripe_price_id
            else:
                price_id = new_plan.mercadopago_plan_id
            
            result = self.gateway.update_subscription(
                subscription_id=company.subscription_id,
                new_plan_id=price_id
            )
            
            # Update company
            old_plan = company.subscription_plan
            company.subscription_plan = new_plan
            company.billing_cycle = billing_cycle
            company.save()
            
            # Log the upgrade
            PaymentHistory.objects.create(
                company=company,
                subscription_plan=new_plan,
                transaction_type='upgrade',
                amount=new_plan.price_yearly if billing_cycle == 'yearly' else new_plan.price_monthly,
                currency='BRL',
                status='paid',
                description=f'Upgrade de {old_plan.name} para {new_plan.name}',
                transaction_date=timezone.now(),
                paid_at=timezone.now()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            raise

    def check_trial_expiration(self):
        """Check and handle trial expirations"""
        from apps.companies.models import Company
        from apps.notifications.email_service import EmailService
        
        now = timezone.now()
        
        # Find companies with expired trials
        expired_trials = Company.objects.filter(
            subscription_status='trial',
            trial_ends_at__lt=now
        )
        
        for company in expired_trials:
            company.subscription_status = 'expired'
            company.save()
            
            # Send notification
            EmailService.send_trial_expired_email(
                email=company.owner.email,
                company_name=company.name,
                owner_name=company.owner.get_full_name()
            )
        
        # Find companies with trials expiring soon (3 days)
        expiring_soon = Company.objects.filter(
            subscription_status='trial',
            trial_ends_at__lte=now + timedelta(days=3),
            trial_ends_at__gt=now
        )
        
        for company in expiring_soon:
            # Send reminder
            EmailService.send_trial_expiring_email(
                email=company.owner.email,
                company_name=company.name,
                owner_name=company.owner.get_full_name(),
                days_remaining=(company.trial_ends_at - now).days
            )
    
    def process_failed_payments(self):
        """Process failed payments and update subscription status"""
        from apps.companies.models import Company
        
        # This would be called by a cron job or celery task
        companies_with_failed_payments = Company.objects.filter(
            subscription_status='active',
            next_billing_date__lt=timezone.now().date()
        )
        
        for company in companies_with_failed_payments:
            # Check with payment provider
            try:
                status = self.gateway.get_subscription_status(company.subscription_id)
                
                if status['status'] == 'past_due':
                    company.subscription_status = 'past_due'
                    company.save()
                elif status['status'] == 'canceled':
                    company.subscription_status = 'cancelled'
                    company.subscription_end_date = timezone.now()
                    company.save()
                    
            except Exception as e:
                logger.error(f"Error checking payment status for company {company.id}: {e}")