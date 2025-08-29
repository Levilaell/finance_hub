"""
Redis-Independent Subscription Creation Service
For use when webhook processing fails and Redis/Celery is unavailable

This service provides a direct, synchronous way to create subscriptions
without depending on external services like Redis or Celery.
"""

from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging
import stripe
from django.conf import settings

logger = logging.getLogger(__name__)


class IndependentSubscriptionService:
    """Create subscriptions without Redis/Celery dependencies"""
    
    @staticmethod
    def create_subscription_from_stripe_session(session_id: str, user=None) -> dict:
        """
        Create subscription directly from Stripe session data
        Used as fallback when webhook processing fails
        
        Args:
            session_id: Stripe checkout session ID
            user: Django user object (optional, for company lookup)
            
        Returns:
            dict: Result with status and subscription info
        """
        from apps.payments.models import Subscription, Payment
        from apps.companies.models import Company, SubscriptionPlan
        from apps.companies.utils import get_user_company
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        try:
            # Retrieve session from Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            logger.info(f"🔍 Retrieved Stripe session: {session.id}, status: {session.payment_status}")
            
            # Verify payment was successful
            if session.payment_status != 'paid':
                return {
                    'status': 'error',
                    'message': f'Payment not completed. Status: {session.payment_status}'
                }
            
            # Get metadata
            metadata = session.get('metadata', {})
            if not metadata.get('company_id'):
                subscription_metadata = session.get('subscription_data', {}).get('metadata', {})
                if subscription_metadata:
                    metadata = subscription_metadata
            
            company_id = metadata.get('company_id')
            plan_id = metadata.get('plan_id')
            billing_period = metadata.get('billing_period', 'monthly')
            
            if not company_id or not plan_id:
                return {
                    'status': 'error',
                    'message': 'Missing company_id or plan_id in session metadata'
                }
            
            # If no user provided, try to identify from Stripe customer
            if not user:
                try:
                    customer = stripe.Customer.retrieve(session.customer)
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    user = User.objects.get(email=customer.email)
                    logger.info(f"👤 Identified user from Stripe customer: {customer.email}")
                except Exception as e:
                    logger.warning(f"Could not identify user from session: {e}")
            
            # Create subscription in atomic transaction
            with transaction.atomic():
                # Get company and plan
                company = Company.objects.select_for_update().get(id=company_id)
                plan = SubscriptionPlan.objects.get(id=plan_id)
                
                logger.info(f"🏢 Creating subscription for company: {company.name} ({company.id})")
                logger.info(f"📋 Plan: {plan.name} ({plan.id})")
                
                # Check for existing active subscription
                existing = Subscription.objects.filter(
                    company=company, 
                    status__in=['active', 'trial']
                ).first()
                
                if existing:
                    logger.warning(f"Company {company_id} already has active subscription {existing.id}")
                    return {
                        'status': 'warning',
                        'message': 'Company already has active subscription',
                        'subscription_id': existing.id
                    }
                
                # Create subscription
                subscription = Subscription.objects.create(
                    company=company,
                    plan=plan,
                    status='active',
                    billing_period=billing_period,
                    stripe_subscription_id=session.get('subscription', f"manual_{session_id}"),
                    stripe_customer_id=session.get('customer'),
                    current_period_start=timezone.now(),
                    current_period_end=timezone.now() + timezone.timedelta(
                        days=365 if billing_period == 'yearly' else 30
                    )
                )
                
                # Update company subscription status
                company.subscription_status = 'active'
                company.subscription_plan = plan
                company.save()
                
                # Create payment record
                amount = Decimal(session.amount_total) / 100  # Convert from cents
                payment = Payment.objects.create(
                    company=company,
                    subscription=subscription,
                    amount=amount,
                    currency=session.currency.upper(),
                    status='succeeded',
                    description=f"{plan.display_name} - {billing_period.title()} subscription",
                    gateway='stripe',
                    stripe_payment_intent_id=session.get('payment_intent'),
                    paid_at=timezone.now(),
                    metadata={
                        'session_id': session_id,
                        'subscription_id': session.get('subscription'),
                        'manual_creation': True,
                        'created_by': 'independent_service'
                    }
                )
                
                # Log successful creation
                logger.info(f"✅ Successfully created subscription {subscription.id} for company {company.name}")
                
                # Log audit trail
                from ..services.audit_service import PaymentAuditService
                try:
                    PaymentAuditService.log_subscription_created(
                        subscription,
                        user=user,
                        metadata={
                            'source': 'independent_service_fallback',
                            'session_id': session_id,
                            'redis_unavailable': True
                        }
                    )
                    
                    PaymentAuditService.log_payment_attempt(
                        payment,
                        metadata={
                            'source': 'independent_service_fallback',
                            'manual_creation': True
                        }
                    )
                except Exception as audit_error:
                    # Don't fail the whole operation if audit logging fails
                    logger.warning(f"⚠️ Audit logging failed: {audit_error}")
                
                return {
                    'status': 'success',
                    'message': 'Subscription created successfully',
                    'subscription_id': subscription.id,
                    'payment_id': payment.id,
                    'company_id': company.id
                }
                
        except stripe.error.StripeError as e:
            logger.error(f"❌ Stripe error in independent service: {e}")
            return {
                'status': 'error',
                'message': f'Stripe error: {str(e)}',
                'code': 'STRIPE_ERROR'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in independent subscription creation: {e}")
            return {
                'status': 'error',
                'message': f'Failed to create subscription: {str(e)}',
                'code': 'CREATION_ERROR'
            }
    
    @staticmethod
    def verify_subscription_creation(session_id: str) -> dict:
        """
        Verify that a subscription was created for a given session
        
        Args:
            session_id: Stripe checkout session ID
            
        Returns:
            dict: Verification result
        """
        from apps.payments.models import Subscription, Payment
        
        try:
            # Look for subscription created from this session
            payments = Payment.objects.filter(
                metadata__session_id=session_id,
                status='succeeded'
            ).select_related('subscription', 'company')
            
            if not payments.exists():
                return {
                    'status': 'not_found',
                    'message': 'No payment record found for session'
                }
            
            payment = payments.first()
            subscription = payment.subscription
            
            if subscription and subscription.status == 'active':
                return {
                    'status': 'verified',
                    'message': 'Subscription is active',
                    'subscription_id': subscription.id,
                    'company_id': payment.company.id
                }
            else:
                return {
                    'status': 'inactive',
                    'message': 'Subscription exists but not active',
                    'subscription_id': subscription.id if subscription else None
                }
                
        except Exception as e:
            logger.error(f"❌ Error verifying subscription: {e}")
            return {
                'status': 'error',
                'message': f'Verification failed: {str(e)}'
            }


# Convenience function for easy import
def create_subscription_from_session(session_id: str, user=None) -> dict:
    """Convenience function to create subscription from Stripe session"""
    return IndependentSubscriptionService.create_subscription_from_stripe_session(session_id, user)