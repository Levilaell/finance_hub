"""
Comprehensive subscription management service
Handles all subscription lifecycle operations with Stripe integration
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from .stripe_service import StripeService
from .notification_service import notification_service
from .audit_service import PaymentAuditService
from ..exceptions import (
    SubscriptionException,
    PaymentMethodRequiredException,
    SubscriptionLimitExceededException
)

logger = logging.getLogger(__name__)


class SubscriptionManager:
    """Manages subscription lifecycle and operations"""
    
    def __init__(self):
        self.stripe_service = StripeService()
    
    @transaction.atomic
    def create_subscription(self,
                          company: 'Company',
                          plan: 'SubscriptionPlan',
                          billing_period: str = 'monthly',
                          payment_method_id: Optional[str] = None,
                          user: Optional['User'] = None) -> 'Subscription':
        """
        Create a new subscription for a company
        
        Args:
            company: Company instance
            plan: SubscriptionPlan to subscribe to
            billing_period: 'monthly' or 'yearly'
            payment_method_id: Stripe payment method ID
            user: User creating the subscription
            
        Returns:
            Created Subscription instance
            
        Raises:
            SubscriptionException: If subscription creation fails
        """
        from ..models import Subscription, PaymentMethod
        
        # Check if company already has a subscription
        if hasattr(company, 'subscription') and company.subscription:
            raise SubscriptionException(
                "Company already has a subscription. Please upgrade or cancel existing subscription first."
            )
        
        # Get or create Stripe customer
        if not user:
            user = company.users.filter(is_company_admin=True).first() or company.users.first()
        
        customer_id = self.stripe_service.create_or_get_customer(company, user)
        
        # Validate payment method if not in trial
        if not plan.trial_days and not payment_method_id:
            raise PaymentMethodRequiredException(
                "Payment method required for non-trial subscriptions"
            )
        
        try:
            # Create Stripe subscription
            stripe_sub = self.stripe_service.create_subscription(
                customer_id=customer_id,
                plan=plan,
                billing_period=billing_period,
                trial_days=plan.trial_days,
                payment_method_id=payment_method_id
            )
            
            # Create local subscription record
            subscription = Subscription.objects.create(
                company=company,
                plan=plan,
                status='trial' if plan.trial_days else 'active',
                billing_period=billing_period,
                stripe_subscription_id=stripe_sub['id'],
                stripe_customer_id=customer_id,
                current_period_start=timezone.now(),
                current_period_end=timezone.now() + timedelta(
                    days=365 if billing_period == 'yearly' else 30
                ),
                trial_ends_at=timezone.now() + timedelta(days=plan.trial_days) if plan.trial_days else None,
                metadata={
                    'created_by': str(user.id) if user else None,
                    'stripe_status': stripe_sub['status'],
                    'has_payment_method': bool(payment_method_id)
                }
            )
            
            # Update company subscription fields
            company.subscription_plan = plan
            company.subscription_status = subscription.status
            company.billing_cycle = billing_period
            company.trial_ends_at = subscription.trial_ends_at
            company.save()
            
            # Store payment method if provided
            if payment_method_id:
                payment_method = self.stripe_service.attach_payment_method(
                    payment_method_id=payment_method_id,
                    customer_id=customer_id,
                    set_default=True
                )
                
                PaymentMethod.objects.create(
                    company=company,
                    type='card',
                    is_default=True,
                    stripe_payment_method_id=payment_method_id,
                    brand=payment_method['card']['brand'],
                    last4=payment_method['card']['last4'],
                    exp_month=payment_method['card']['exp_month'],
                    exp_year=payment_method['card']['exp_year']
                )
            
            # Log subscription creation
            PaymentAuditService.log_subscription_created(
                subscription=subscription,
                user=user,
                metadata={
                    'plan': plan.name,
                    'billing_period': billing_period,
                    'trial_days': plan.trial_days
                }
            )
            
            # Send notification
            notification_service.notify_subscription_created(
                company_id=company.id,
                subscription_data={
                    'plan_name': plan.display_name,
                    'billing_period': billing_period,
                    'trial_days': plan.trial_days
                }
            )
            
            logger.info(f"Created subscription for company {company.name} on plan {plan.name}")
            return subscription
            
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            raise SubscriptionException(f"Failed to create subscription: {str(e)}")
    
    @transaction.atomic
    def upgrade_subscription(self,
                           subscription: 'Subscription',
                           new_plan: 'SubscriptionPlan',
                           billing_period: Optional[str] = None,
                           user: Optional['User'] = None) -> 'Subscription':
        """
        Upgrade subscription to a new plan
        
        Args:
            subscription: Current subscription
            new_plan: Plan to upgrade to
            billing_period: New billing period (optional)
            user: User performing the upgrade
            
        Returns:
            Updated subscription
            
        Raises:
            SubscriptionException: If upgrade fails
        """
        # Validate upgrade
        if new_plan.price_monthly < subscription.plan.price_monthly:
            raise SubscriptionException(
                "Use downgrade_subscription for moving to a lower-priced plan"
            )
        
        old_plan = subscription.plan
        old_billing = subscription.billing_period
        new_billing = billing_period or subscription.billing_period
        
        try:
            # Calculate proration if needed
            proration_amount = Decimal('0.00')
            if subscription.status == 'active':
                price_id = (
                    new_plan.stripe_price_id_yearly if new_billing == 'yearly'
                    else new_plan.stripe_price_id_monthly
                )
                
                if not price_id:
                    price_id = self.stripe_service.create_or_get_price(new_plan, new_billing)
                
                proration_amount, _ = self.stripe_service.calculate_proration(
                    subscription_id=subscription.stripe_subscription_id,
                    new_price_id=price_id
                )
            
            # Update Stripe subscription
            stripe_sub = self.stripe_service.update_subscription(
                subscription_id=subscription.stripe_subscription_id,
                updates={
                    'plan_id': new_plan.id,
                    'billing_period': new_billing
                }
            )
            
            # Update local subscription
            subscription.plan = new_plan
            subscription.billing_period = new_billing
            subscription.metadata['upgraded_from'] = old_plan.name
            subscription.metadata['upgrade_date'] = timezone.now().isoformat()
            subscription.save()
            
            # Update company
            subscription.company.subscription_plan = new_plan
            subscription.company.billing_cycle = new_billing
            subscription.company.save()
            
            # Log upgrade
            PaymentAuditService.log_payment_action(
                action='subscription_upgraded',
                user=user,
                company=subscription.company,
                subscription_id=subscription.id,
                metadata={
                    'old_plan': old_plan.name,
                    'new_plan': new_plan.name,
                    'old_billing': old_billing,
                    'new_billing': new_billing,
                    'proration_amount': str(proration_amount)
                }
            )
            
            # Send notification
            notification_service.notify_subscription_updated(
                company_id=subscription.company.id,
                data={
                    'action': 'upgraded',
                    'old_plan': old_plan.display_name,
                    'new_plan': new_plan.display_name,
                    'proration_amount': float(proration_amount)
                }
            )
            
            logger.info(f"Upgraded subscription {subscription.id} from {old_plan.name} to {new_plan.name}")
            return subscription
            
        except Exception as e:
            logger.error(f"Failed to upgrade subscription: {e}")
            raise SubscriptionException(f"Failed to upgrade subscription: {str(e)}")
    
    @transaction.atomic
    def downgrade_subscription(self,
                             subscription: 'Subscription',
                             new_plan: 'SubscriptionPlan',
                             user: Optional['User'] = None) -> 'Subscription':
        """
        Downgrade subscription to a lower plan
        
        Args:
            subscription: Current subscription
            new_plan: Plan to downgrade to
            user: User performing the downgrade
            
        Returns:
            Updated subscription
            
        Raises:
            SubscriptionException: If downgrade fails
            SubscriptionLimitExceededException: If current usage exceeds new plan limits
        """
        # Check usage limits
        company = subscription.company
        if company.bank_accounts.count() > new_plan.max_bank_accounts:
            raise SubscriptionLimitExceededException(
                f"Current bank accounts ({company.bank_accounts.count()}) exceed "
                f"new plan limit ({new_plan.max_bank_accounts})"
            )
        
        if company.current_month_transactions > new_plan.max_transactions:
            raise SubscriptionLimitExceededException(
                f"Current month transactions ({company.current_month_transactions}) exceed "
                f"new plan limit ({new_plan.max_transactions})"
            )
        
        old_plan = subscription.plan
        
        try:
            # Update Stripe subscription (downgrade at period end)
            stripe_sub = self.stripe_service.update_subscription(
                subscription_id=subscription.stripe_subscription_id,
                updates={
                    'plan_id': new_plan.id,
                    'billing_period': subscription.billing_period,
                    'proration_behavior': 'none'  # Downgrade at period end
                }
            )
            
            # Update local subscription
            subscription.plan = new_plan
            subscription.metadata['downgraded_from'] = old_plan.name
            subscription.metadata['downgrade_date'] = timezone.now().isoformat()
            subscription.metadata['downgrade_effective'] = subscription.current_period_end.isoformat()
            subscription.save()
            
            # Log downgrade
            PaymentAuditService.log_payment_action(
                action='subscription_downgraded',
                user=user,
                company=company,
                subscription_id=subscription.id,
                metadata={
                    'old_plan': old_plan.name,
                    'new_plan': new_plan.name,
                    'effective_date': subscription.current_period_end.isoformat()
                }
            )
            
            # Send notification
            notification_service.notify_subscription_updated(
                company_id=company.id,
                data={
                    'action': 'downgraded',
                    'old_plan': old_plan.display_name,
                    'new_plan': new_plan.display_name,
                    'effective_date': subscription.current_period_end.isoformat()
                }
            )
            
            logger.info(f"Scheduled downgrade of subscription {subscription.id} to {new_plan.name}")
            return subscription
            
        except Exception as e:
            logger.error(f"Failed to downgrade subscription: {e}")
            raise SubscriptionException(f"Failed to downgrade subscription: {str(e)}")
    
    @transaction.atomic
    def cancel_subscription(self,
                          subscription: 'Subscription',
                          immediately: bool = False,
                          reason: Optional[str] = None,
                          user: Optional['User'] = None) -> 'Subscription':
        """
        Cancel a subscription
        
        Args:
            subscription: Subscription to cancel
            immediately: Cancel immediately vs end of period
            reason: Cancellation reason
            user: User cancelling the subscription
            
        Returns:
            Updated subscription
        """
        try:
            # Cancel in Stripe
            stripe_sub = self.stripe_service.cancel_subscription(
                subscription_id=subscription.stripe_subscription_id,
                immediately=immediately,
                feedback=reason
            )
            
            # Update local subscription
            if immediately:
                subscription.status = 'cancelled'
                subscription.company.subscription_status = 'cancelled'
            else:
                subscription.cancel_at_period_end = True
                subscription.metadata['cancel_scheduled'] = True
            
            subscription.cancelled_at = timezone.now()
            subscription.metadata['cancel_reason'] = reason
            subscription.metadata['cancelled_by'] = str(user.id) if user else None
            subscription.save()
            
            subscription.company.save()
            
            # Log cancellation
            PaymentAuditService.log_payment_action(
                action='subscription_cancelled',
                user=user,
                company=subscription.company,
                subscription_id=subscription.id,
                metadata={
                    'immediately': immediately,
                    'reason': reason,
                    'effective_date': 'immediate' if immediately else subscription.current_period_end.isoformat()
                }
            )
            
            # Send notification
            notification_service.notify_subscription_cancelled(
                company_id=subscription.company.id,
                data={
                    'immediately': immediately,
                    'effective_date': 'immediate' if immediately else subscription.current_period_end.isoformat(),
                    'reason': reason
                }
            )
            
            logger.info(f"Cancelled subscription {subscription.id} ({'immediately' if immediately else 'at period end'})")
            return subscription
            
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            raise SubscriptionException(f"Failed to cancel subscription: {str(e)}")
    
    @transaction.atomic
    def reactivate_subscription(self,
                              subscription: 'Subscription',
                              user: Optional['User'] = None) -> 'Subscription':
        """
        Reactivate a cancelled subscription
        
        Args:
            subscription: Subscription to reactivate
            user: User reactivating the subscription
            
        Returns:
            Updated subscription
        """
        if not subscription.cancel_at_period_end and subscription.status == 'cancelled':
            raise SubscriptionException(
                "Cannot reactivate a fully cancelled subscription. Please create a new subscription."
            )
        
        try:
            # Reactivate in Stripe
            stripe_sub = self.stripe_service.update_subscription(
                subscription_id=subscription.stripe_subscription_id,
                updates={'cancel_at_period_end': False}
            )
            
            # Update local subscription
            subscription.cancel_at_period_end = False
            subscription.cancelled_at = None
            subscription.metadata.pop('cancel_scheduled', None)
            subscription.metadata.pop('cancel_reason', None)
            subscription.metadata['reactivated_at'] = timezone.now().isoformat()
            subscription.metadata['reactivated_by'] = str(user.id) if user else None
            subscription.save()
            
            # Log reactivation
            PaymentAuditService.log_payment_action(
                action='subscription_reactivated',
                user=user,
                company=subscription.company,
                subscription_id=subscription.id
            )
            
            # Send notification
            notification_service.notify_subscription_updated(
                company_id=subscription.company.id,
                data={'action': 'reactivated'}
            )
            
            logger.info(f"Reactivated subscription {subscription.id}")
            return subscription
            
        except Exception as e:
            logger.error(f"Failed to reactivate subscription: {e}")
            raise SubscriptionException(f"Failed to reactivate subscription: {str(e)}")
    
    def get_subscription_usage(self, subscription: 'Subscription') -> Dict[str, Any]:
        """
        Get current usage statistics for a subscription
        
        Args:
            subscription: Subscription instance
            
        Returns:
            Dictionary with usage statistics
        """
        company = subscription.company
        plan = subscription.plan
        
        return {
            'transactions': {
                'used': company.current_month_transactions,
                'limit': plan.max_transactions,
                'percentage': round(
                    (company.current_month_transactions / plan.max_transactions * 100)
                    if plan.max_transactions > 0 else 0,
                    2
                )
            },
            'bank_accounts': {
                'used': company.bank_accounts.count(),
                'limit': plan.max_bank_accounts,
                'percentage': round(
                    (company.bank_accounts.count() / plan.max_bank_accounts * 100)
                    if plan.max_bank_accounts > 0 else 0,
                    2
                )
            },
            'ai_requests': {
                'used': company.current_month_ai_requests,
                'limit': plan.max_ai_requests_per_month,
                'percentage': round(
                    (company.current_month_ai_requests / plan.max_ai_requests_per_month * 100)
                    if plan.max_ai_requests_per_month > 0 else 0,
                    2
                )
            },
            'ai_credits': {
                'balance': getattr(company, 'ai_credits_balance', 0),
                'unlimited': plan.unlimited_ai_insights
            }
        }
    
    def check_usage_limits(self, company: 'Company', resource: str) -> bool:
        """
        Check if company has reached usage limits
        
        Args:
            company: Company instance
            resource: Resource type ('transactions', 'bank_accounts', 'ai_requests')
            
        Returns:
            True if within limits, False if exceeded
        """
        plan = company.subscription_plan
        if not plan:
            return False
        
        if resource == 'transactions':
            return company.current_month_transactions < plan.max_transactions
        elif resource == 'bank_accounts':
            return company.bank_accounts.count() < plan.max_bank_accounts
        elif resource == 'ai_requests':
            if plan.unlimited_ai_insights:
                return True
            return company.current_month_ai_requests < plan.max_ai_requests_per_month
        
        return False
    
    def get_available_plans(self, current_plan: Optional['SubscriptionPlan'] = None) -> Dict[str, List['SubscriptionPlan']]:
        """
        Get available plans categorized by upgrade/downgrade
        
        Args:
            current_plan: Current subscription plan
            
        Returns:
            Dictionary with 'upgrades' and 'downgrades' lists
        """
        from apps.companies.models import SubscriptionPlan
        
        all_plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price_monthly')
        
        if not current_plan:
            return {
                'available': list(all_plans),
                'upgrades': [],
                'downgrades': []
            }
        
        upgrades = []
        downgrades = []
        
        for plan in all_plans:
            if plan.id == current_plan.id:
                continue
            
            if plan.price_monthly > current_plan.price_monthly:
                upgrades.append(plan)
            else:
                downgrades.append(plan)
        
        return {
            'current': current_plan,
            'upgrades': upgrades,
            'downgrades': downgrades
        }