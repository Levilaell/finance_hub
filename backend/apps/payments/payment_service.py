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
from django.core.cache import cache

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
    
    def update_subscription(self, subscription_id: str, new_plan_id: str) -> Dict[str, Any]:
        """Update subscription to a new plan"""
        try:
            # Retrieve current subscription
            subscription = self.stripe.Subscription.retrieve(subscription_id)
            
            # Get the subscription item ID (assuming single item subscription)
            if not subscription.items or not subscription.items.data:
                raise ValueError("Subscription has no items")
            
            subscription_item_id = subscription.items.data[0].id
            
            # Update the subscription with new price
            updated_subscription = self.stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription_item_id,
                    'price': new_plan_id,
                }],
                proration_behavior='always_invoice',  # Criar fatura para diferença
                expand=['latest_invoice.payment_intent']
            )
            
            # Se houver uma fatura pendente, retornar o payment intent
            payment_intent_secret = None
            if (updated_subscription.latest_invoice and 
                hasattr(updated_subscription.latest_invoice, 'payment_intent') and
                updated_subscription.latest_invoice.payment_intent):
                payment_intent_secret = updated_subscription.latest_invoice.payment_intent.client_secret
            
            return {
                'subscription_id': updated_subscription.id,
                'status': updated_subscription.status,
                'new_price_id': new_plan_id,
                'client_secret': payment_intent_secret,
                'requires_payment': payment_intent_secret is not None,
                'data': updated_subscription
            }
        except Exception as e:
            logger.error(f"Error updating Stripe subscription: {e}")
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
        """Process webhook events with idempotency check"""
        event_type = event_data['event_type']
        event_id = event_data.get('event_id')
        
        # Check idempotency
        if event_id:
            cache_key = f"webhook_processed:{event_type}:{event_id}"
            if cache.get(cache_key):
                logger.info(f"Duplicate webhook event ignored: {event_id}")
                return
            # Mark as processed for 24 hours
            cache.set(cache_key, True, 86400)
        
        # Process with atomic transaction
        try:
            with transaction.atomic():
                # Stripe events
                if event_type == 'checkout.session.completed':
                    self._handle_checkout_completed(event_data['data'])
                elif 'subscription' in event_type:
                    self._handle_subscription_event(event_type, event_data['data'])
                elif 'payment_intent' in event_type:
                    self._handle_payment_event(event_type, event_data['data'])
                elif 'invoice' in event_type:
                    self._handle_invoice_event(event_type, event_data['data'])
                elif event_type == 'payment_method.attached':
                    self._handle_payment_method_attached(event_data['data'])
                elif event_type == 'charge.failed':
                    self._handle_charge_failed(event_data['data'])
                elif event_type == 'customer.subscription.trial_will_end':
                    self._handle_subscription_trial_will_end(event_data['data'])
        except Exception as e:
            logger.error(f"Error processing webhook {event_type}: {e}", exc_info=True)
            # Remove from cache so it can be retried
            if event_id:
                cache.delete(f"webhook_processed:{event_type}:{event_id}")
            raise
    
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
    
    def _handle_checkout_completed(self, data: Dict[str, Any]):
        """Handle checkout.session.completed event"""
        from apps.companies.models import Company, SubscriptionPlan
        
        session = data['object']
        metadata = session.get('metadata', {})
        
        # Detailed logging for audit
        logger.info("="*50)
        logger.info(f"CHECKOUT COMPLETED - Session ID: {session.get('id')}")
        logger.info(f"Customer: {session.get('customer')}")
        logger.info(f"Amount: {session.get('amount_total')/100} {session.get('currency', '').upper()}")
        logger.info(f"Payment Status: {session.get('payment_status')}")
        logger.info(f"Metadata: {metadata}")
        logger.info("="*50)
        
        # Validate metadata
        from .security_fixes import WebhookSecurity
        if not WebhookSecurity.validate_metadata(metadata):
            logger.error(f"Invalid metadata in checkout session: {session['id']}")
            logger.error(f"Metadata received: {metadata}")
            return
        
        # Get company and plan from metadata
        company_id = metadata.get('company_id')
        plan_id = metadata.get('plan_id')
        billing_cycle = metadata.get('billing_cycle', 'monthly')
        user_id = metadata.get('user_id')
        
        logger.info(f"Extracted - Company: {company_id}, Plan: {plan_id}, Cycle: {billing_cycle}")
        
        try:
            company = Company.objects.get(id=company_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            logger.info(f"Found company: {company.name} (ID: {company.id})")
            logger.info(f"Found plan: {plan.name} (ID: {plan.id})")
            logger.info(f"Previous status: {company.subscription_status}")
            
            # Update company subscription
            company.subscription_plan = plan
            company.subscription_status = 'active'
            company.billing_cycle = billing_cycle
            company.subscription_id = session.get('subscription')
            company.subscription_start_date = timezone.now()
            
            # Calculate next billing date
            current_date = timezone.now().date()
            if billing_cycle == 'yearly':
                # Add exactly one year
                try:
                    company.next_billing_date = current_date.replace(year=current_date.year + 1)
                except ValueError:
                    # Handle February 29 in leap years
                    company.next_billing_date = current_date.replace(year=current_date.year + 1, day=28)
            else:
                # Add exactly one month
                if current_date.month == 12:
                    company.next_billing_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    try:
                        company.next_billing_date = current_date.replace(month=current_date.month + 1)
                    except ValueError:
                        # Handle days that don't exist in next month (e.g., Jan 31 -> Feb 28/29)
                        next_month = current_date.month + 1
                        company.next_billing_date = current_date.replace(month=next_month, day=1) + timedelta(days=31)
                        company.next_billing_date = company.next_billing_date.replace(day=1) - timedelta(days=1)
            
            company.save()
            
            # Audit log
            logger.info(f"SUBSCRIPTION ACTIVATED:")
            logger.info(f"  Company: {company.name} (ID: {company.id})")
            logger.info(f"  Plan: {plan.name} ({billing_cycle})")
            logger.info(f"  Status: {company.subscription_status}")
            logger.info(f"  Subscription ID: {company.subscription_id}")
            logger.info(f"  Next Billing: {company.next_billing_date}")
            
            # Create payment history
            payment = PaymentHistory.objects.create(
                company=company,
                subscription_plan=plan,
                transaction_type='subscription',
                amount=plan.price_yearly if billing_cycle == 'yearly' else plan.price_monthly,
                currency='BRL',
                status='paid',
                description=f'Assinatura {plan.name} - Ciclo {billing_cycle}',
                invoice_number=f'INV-{timezone.now().strftime("%Y%m")}-{company.id:04d}',
                transaction_date=timezone.now(),
                paid_at=timezone.now(),
                stripe_payment_intent_id=session.get('payment_intent'),
                payment_method_display='Cartão de Crédito'
            )
            
            # Fetch expanded session details to get payment method
            if self.gateway_name == 'stripe':
                try:
                    import stripe
                    stripe.api_key = settings.STRIPE_SECRET_KEY
                    
                    # Retrieve session with expanded payment intent
                    full_session = stripe.checkout.Session.retrieve(
                        session.get('id'),
                        expand=['payment_intent.payment_method']
                    )
                    
                    if full_session.payment_intent and hasattr(full_session.payment_intent, 'payment_method'):
                        payment_method = full_session.payment_intent.payment_method
                        if payment_method and hasattr(payment_method, 'card'):
                            card = payment_method.card
                            
                            # Check if payment method already exists
                            existing_method = PaymentMethod.objects.filter(
                                company=company,
                                stripe_payment_method_id=payment_method.id,
                                is_active=True
                            ).first()
                            
                            if not existing_method:
                                PaymentMethod.objects.create(
                                    company=company,
                                    payment_type='credit_card',
                                    card_brand=card.brand.upper() if card.brand else 'UNKNOWN',
                                    last_four=card.last4,
                                    exp_month=card.exp_month,
                                    exp_year=card.exp_year,
                                    stripe_payment_method_id=payment_method.id,
                                    is_default=True,
                                    is_active=True
                                )
                                logger.info(f"PAYMENT METHOD SAVED:")
                                logger.info(f"  Company: {company.name}")
                                logger.info(f"  Brand: {card.brand}")
                                logger.info(f"  Last 4: {card.last4}")
                                logger.info(f"  Exp: {card.exp_month}/{card.exp_year}")
                except Exception as e:
                    logger.error(f"PAYMENT METHOD ERROR: Failed to save for company {company.id}", exc_info=True)
            
            logger.info(f"PAYMENT HISTORY CREATED:")
            logger.info(f"  ID: {payment.id}")
            logger.info(f"  Amount: {payment.amount} {payment.currency}")
            logger.info(f"  Invoice: {payment.invoice_number}")
            logger.info(f"✅ CHECKOUT COMPLETE: Subscription activated for {company.name}")
            logger.info("="*50)
            
        except Company.DoesNotExist:
            logger.error(f"Company not found with ID: {company_id}")
        except SubscriptionPlan.DoesNotExist:
            logger.error(f"Plan not found with ID: {plan_id}")
        except Exception as e:
            logger.error(f"Unexpected error processing checkout: {e}", exc_info=True)
    
    def _handle_payment_event(self, event_type: str, data: Dict[str, Any]):
        """Handle payment-related events"""
        # Implement payment event handling
        pass
    
    def _handle_invoice_event(self, event_type: str, data: Dict[str, Any]):
        """Handle invoice-related events"""
        from apps.companies.models import Company
        
        invoice = data['object']
        
        if event_type == 'invoice.payment_succeeded':
            # Payment successful - ensure subscription is active
            subscription_id = invoice.get('subscription')
            if subscription_id:
                try:
                    company = Company.objects.get(subscription_id=subscription_id)
                    company.subscription_status = 'active'
                    company.save()
                    
                    # Log payment
                    PaymentHistory.objects.create(
                        company=company,
                        subscription_plan=company.subscription_plan,
                        transaction_type='subscription',
                        amount=Decimal(invoice['amount_paid']) / 100,  # Convert from cents
                        currency='BRL',
                        status='paid',
                        description=f'Pagamento recorrente - {company.subscription_plan.name}',
                        transaction_date=timezone.now(),
                        paid_at=timezone.now(),
                        stripe_invoice_id=invoice['id']
                    )
                except Company.DoesNotExist:
                    logger.warning(f"Company not found for subscription {subscription_id}")
                    
        elif event_type == 'invoice.payment_failed':
            # Payment failed - update subscription status
            subscription_id = invoice.get('subscription')
            if subscription_id:
                try:
                    company = Company.objects.get(subscription_id=subscription_id)
                    company.subscription_status = 'past_due'
                    company.save()
                    
                    # TODO: Send email notification about failed payment
                    
                except Company.DoesNotExist:
                    logger.warning(f"Company not found for subscription {subscription_id}")

    def update_subscription(self, company, new_plan, billing_cycle='monthly'):
        """Update subscription with proration"""
        if not company.subscription_id:
            # No existing subscription, create new one
            return self.create_subscription(company, new_plan, billing_cycle)
        
        try:
            # Get correct price ID based on billing cycle
            if self.gateway_name == 'stripe':
                if billing_cycle == 'yearly':
                    price_id = new_plan.stripe_price_id_yearly
                else:
                    price_id = new_plan.stripe_price_id_monthly
                    
                if not price_id:
                    raise ValueError(f"Stripe price ID not configured for {billing_cycle} billing")
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
    
    def _handle_payment_method_attached(self, data: Dict[str, Any]):
        """Handle when a payment method is attached to customer"""
        from apps.companies.models import PaymentMethod
        from apps.authentication.models import User
        
        payment_method = data['object']
        customer_id = payment_method.get('customer')
        
        if not customer_id:
            logger.warning("Payment method attached without customer ID")
            return
            
        try:
            user = User.objects.get(payment_customer_id=customer_id)
            company = user.company
            
            # Check if payment method already exists
            if PaymentMethod.objects.filter(
                stripe_payment_method_id=payment_method['id']
            ).exists():
                logger.info(f"Payment method {payment_method['id']} already exists")
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
        except Exception as e:
            logger.error(f"Error saving payment method: {e}", exc_info=True)
    
    def _handle_charge_failed(self, data: Dict[str, Any]):
        """Handle failed payment attempts"""
        from apps.companies.models import Company, PaymentHistory
        from apps.authentication.models import User
        
        charge = data['object']
        customer_id = charge.get('customer')
        
        if not customer_id:
            logger.warning("Charge failed without customer ID")
            return
            
        try:
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
                logger.warning(f"Company {company.id} marked as past_due due to failed payment")
            
            logger.warning(f"Payment failed for company {company.id}")
            
            # Send alert for failed payment
            self._send_payment_failure_alert(company, charge)
            
        except User.DoesNotExist:
            logger.error(f"User not found for customer {customer_id}")
        except Exception as e:
            logger.error(f"Error handling failed charge: {e}", exc_info=True)
    
    def _handle_subscription_trial_will_end(self, data: Dict[str, Any]):
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
        except Exception as e:
            logger.error(f"Error handling trial ending notification: {e}", exc_info=True)
    
    def _send_payment_failure_alert(self, company, charge_data: Dict[str, Any]):
        """Send alerts for payment failures"""
        try:
            # Email to company owner
            from apps.notifications.email_service import EmailService
            email_service = EmailService()
            
            email_service.send_payment_failed_notification(
                email=company.owner.email,
                company_name=company.name,
                owner_name=company.owner.get_full_name(),
                amount=Decimal(charge_data['amount']) / 100,
                failure_reason=charge_data.get('failure_message', 'Erro no processamento do pagamento'),
                last_four=charge_data.get('payment_method_details', {}).get('card', {}).get('last4', '****')
            )
            
            # Alert to admin (could be Slack, Discord, etc)
            logger.critical(f"PAYMENT FAILURE ALERT - Company: {company.name} (ID: {company.id}), Amount: {charge_data['amount']/100} {charge_data['currency']}")
            
            # You could add more alert channels here:
            # - Slack webhook
            # - Discord notification
            # - SMS alert
            # - Create admin task
            
        except Exception as e:
            logger.error(f"Error sending payment failure alert: {e}", exc_info=True)
    
    def cancel_subscription(self, subscription_id: str, immediately: bool = False) -> Dict[str, Any]:
        """Cancel subscription in payment gateway"""
        try:
            if self.gateway_name == 'stripe':
                import stripe
                stripe.api_key = settings.STRIPE_SECRET_KEY
                
                # Cancel at period end by default, or immediately if specified
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=not immediately
                )
                
                if immediately:
                    subscription = stripe.Subscription.delete(subscription_id)
                
                return {
                    'success': True,
                    'cancelled_at': subscription.get('canceled_at'),
                    'cancel_at_period_end': subscription.get('cancel_at_period_end'),
                    'current_period_end': subscription.get('current_period_end')
                }
            
            elif self.gateway_name == 'mercadopago':
                # MercadoPago cancellation logic
                result = self.gateway.mp.subscription().update(
                    subscription_id,
                    {'status': 'cancelled'}
                )
                
                return {
                    'success': result['status'] == 200,
                    'data': result.get('response', {})
                }
            
            else:
                raise ValueError(f"Cancellation not implemented for {self.gateway_name}")
                
        except Exception as e:
            logger.error(f"Error cancelling subscription {subscription_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_proration(self, company, new_plan, billing_cycle='monthly') -> Dict[str, Any]:
        """Calculate proration for plan changes"""
        from decimal import Decimal
        
        if not company.next_billing_date or not company.subscription_plan:
            return {
                'credit': Decimal('0'),
                'charge': Decimal('0'),
                'net_amount': Decimal('0'),
                'days_remaining': 0
            }
        
        # Calculate days remaining in current period
        today = timezone.now().date()
        days_remaining = (company.next_billing_date - today).days
        
        if days_remaining <= 0:
            return {
                'credit': Decimal('0'),
                'charge': Decimal('0'),
                'net_amount': Decimal('0'),
                'days_remaining': 0
            }
        
        # Get current plan price
        current_price = company.subscription_plan.price_monthly
        if company.billing_cycle == 'yearly':
            current_price = company.subscription_plan.price_yearly / 12
        
        # Get new plan price
        new_price = new_plan.price_monthly
        if billing_cycle == 'yearly':
            new_price = new_plan.price_yearly / 12
        
        # Calculate daily rates
        days_in_month = 30  # Simplification
        current_daily_rate = current_price / days_in_month
        new_daily_rate = new_price / days_in_month
        
        # Calculate credit for unused time on current plan
        credit = current_daily_rate * days_remaining
        
        # Calculate charge for new plan
        charge = new_daily_rate * days_remaining
        
        return {
            'credit': round(credit, 2),
            'charge': round(charge, 2),
            'net_amount': round(charge - credit, 2),
            'days_remaining': days_remaining,
            'current_plan': company.subscription_plan.name,
            'new_plan': new_plan.name,
            'billing_cycle': billing_cycle
        }