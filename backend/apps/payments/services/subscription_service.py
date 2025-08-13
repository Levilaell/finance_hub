"""Service for subscription management with validation and proration"""
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from django.utils import timezone
from django.db import transaction
import stripe

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for managing subscription changes with proper validation and proration"""
    
    ALLOWED_TRANSITIONS = {
        'trial': ['active', 'cancelled', 'expired'],
        'active': ['cancelled', 'past_due', 'expired'],
        'past_due': ['active', 'cancelled', 'expired'],
        'cancelled': ['expired'],
        'expired': []  # No transitions from expired
    }
    
    @classmethod
    def validate_state_transition(cls, current_status: str, new_status: str) -> bool:
        """Validate if a subscription state transition is allowed"""
        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, [])
        return new_status in allowed
    
    @classmethod
    def can_upgrade_plan(cls, current_plan, new_plan) -> Tuple[bool, str]:
        """Check if plan change is allowed with proper validation"""
        from ..models import SubscriptionPlan
        
        # Define plan hierarchy
        plan_hierarchy = {
            'starter': 1,
            'professional': 2,
            'enterprise': 3
        }
        
        current_level = plan_hierarchy.get(current_plan.slug.lower(), 0)
        new_level = plan_hierarchy.get(new_plan.slug.lower(), 0)
        
        if new_level > current_level:
            return True, "upgrade"
        elif new_level < current_level:
            return True, "downgrade"
        else:
            return False, "same_plan"
    
    @classmethod
    def validate_downgrade(cls, company, current_plan, new_plan) -> Tuple[bool, str]:
        """
        Validate if downgrade is possible based on current usage.
        Returns (can_downgrade: bool, reason: str)
        """
        # Get current usage
        usage = company.get_usage_summary()
        
        # Check transactions
        if usage['transactions']['used'] > new_plan.max_transactions:
            return False, f"Current transactions ({usage['transactions']['used']}) exceed new plan limit ({new_plan.max_transactions})"
        
        # Check bank accounts
        if usage['bank_accounts']['used'] > new_plan.max_bank_accounts:
            return False, f"Current bank accounts ({usage['bank_accounts']['used']}) exceed new plan limit ({new_plan.max_bank_accounts})"
        
        # Check AI requests
        if usage['ai_requests']['used'] > new_plan.max_ai_requests_per_month:
            return False, f"Current AI requests ({usage['ai_requests']['used']}) exceed new plan limit ({new_plan.max_ai_requests_per_month})"
        
        # Check feature compatibility
        if current_plan.has_ai_categorization and not new_plan.has_ai_categorization:
            # Check if there are AI-categorized transactions
            from apps.banking.models import Transaction
            ai_categorized = Transaction.objects.filter(
                company=company,
                categorized_by='ai'
            ).exists()
            if ai_categorized:
                return False, "You have AI-categorized transactions. Please review them before downgrading."
        
        return True, "Downgrade allowed"
    
    @classmethod
    def calculate_proration(cls, subscription, new_plan, billing_period='monthly') -> Dict[str, Any]:
        """Calculate proration for plan changes"""
        if not subscription.current_period_start or not subscription.current_period_end:
            return {
                'proration_amount': Decimal('0'),
                'credit_amount': Decimal('0'),
                'charge_amount': Decimal('0'),
                'description': 'No proration needed'
            }
        
        now = timezone.now()
        period_start = subscription.current_period_start
        period_end = subscription.current_period_end
        
        # Calculate days remaining in current period
        total_days = (period_end - period_start).days
        days_used = (now - period_start).days
        days_remaining = max(0, (period_end - now).days)
        
        # Calculate prorated amounts
        current_price = subscription.plan.get_price(subscription.billing_period)
        new_price = new_plan.get_price(billing_period)
        
        # Credit for unused time on current plan
        daily_rate_current = current_price / Decimal(total_days)
        credit_amount = daily_rate_current * Decimal(days_remaining)
        
        # Charge for remaining time on new plan
        daily_rate_new = new_price / Decimal(total_days)
        charge_amount = daily_rate_new * Decimal(days_remaining)
        
        # Net proration amount (positive = customer owes, negative = credit)
        proration_amount = charge_amount - credit_amount
        
        return {
            'proration_amount': proration_amount.quantize(Decimal('0.01')),
            'credit_amount': credit_amount.quantize(Decimal('0.01')),
            'charge_amount': charge_amount.quantize(Decimal('0.01')),
            'days_remaining': days_remaining,
            'days_used': days_used,
            'total_days': total_days,
            'description': f'Proration for {days_remaining} days'
        }
    
    @classmethod
    @transaction.atomic
    def change_subscription_plan(cls, subscription, new_plan, billing_period=None,
                               immediate=True) -> Dict[str, Any]:
        """Change subscription plan with validation and proration"""
        from ..models import Payment
        from .payment_gateway import PaymentService
        from .notification_service import notification_service
        
        # Validate subscription is active
        if not subscription.is_active:
            raise ValueError("Cannot change plan for inactive subscription")
        
        # Check if plan change is allowed
        can_change, change_type = cls.can_upgrade_plan(subscription.plan, new_plan)
        if not can_change:
            raise ValueError("Cannot change to the same plan")
        
        # For downgrades, validate current usage
        if change_type == "downgrade":
            can_downgrade, reason = cls.validate_downgrade(
                subscription.company, subscription.plan, new_plan
            )
            if not can_downgrade:
                raise ValueError(f"Downgrade not allowed: {reason}")
        
        # Use current billing period if not specified
        if not billing_period:
            billing_period = subscription.billing_period
        
        # Calculate proration
        proration = cls.calculate_proration(subscription, new_plan, billing_period)
        
        # Store old plan for notification
        old_plan = subscription.plan
        
        if immediate:
            # Apply change immediately with proration
            if proration['proration_amount'] > 0:
                # Customer owes money - create invoice item
                try:
                    stripe.InvoiceItem.create(
                        customer=subscription.stripe_customer_id,
                        amount=int(proration['proration_amount'] * 100),  # Convert to cents
                        currency='brl',
                        description=f"Proration adjustment: {old_plan.display_name} to {new_plan.display_name}"
                    )
                except stripe.error.StripeError as e:
                    logger.error(f"Failed to create proration invoice item: {e}")
                    raise
            
            # Update subscription in Stripe
            try:
                stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                
                # Get the appropriate price ID
                price_id = new_plan.stripe_price_id_yearly if billing_period == 'yearly' else new_plan.stripe_price_id_monthly
                
                # Update subscription with new price
                if price_id:
                    # Use pre-configured price ID (preferred)
                    updated_sub = stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        items=[{
                            'id': stripe_sub['items']['data'][0]['id'],
                            'price': price_id,
                            'quantity': 1
                        }],
                        proration_behavior='create_prorations' if immediate else 'none'
                    )
                else:
                    # Fallback to dynamic pricing if no price ID
                    logger.warning(f"No Stripe price ID for plan {new_plan.name}, using dynamic pricing")
                    updated_sub = stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        items=[{
                            'id': stripe_sub['items']['data'][0]['id'],
                            'price_data': {
                                'currency': 'brl',
                                'product_data': {
                                    'name': new_plan.name,
                                },
                                'unit_amount': int(new_plan.get_price(billing_period) * 100),
                                'recurring': {
                                    'interval': 'year' if billing_period == 'yearly' else 'month',
                                    'interval_count': 1
                                }
                            }
                        }],
                        proration_behavior='create_prorations' if immediate else 'none'
                    )
                
                # Update local subscription
                subscription.plan = new_plan
                subscription.billing_period = billing_period
                subscription.save()
                
                # Record the plan change payment if there's a charge
                if proration['proration_amount'] > 0:
                    Payment.objects.create(
                        company=subscription.company,
                        subscription=subscription,
                        amount=proration['proration_amount'],
                        currency='BRL',
                        status='processing',
                        description=f"Plan change: {old_plan.display_name} to {new_plan.display_name}",
                        gateway='stripe',
                        metadata={
                            'type': 'plan_change',
                            'old_plan': old_plan.name,
                            'new_plan': new_plan.name,
                            'proration': proration
                        }
                    )
                
            except stripe.error.StripeError as e:
                logger.error(f"Failed to update Stripe subscription: {e}")
                raise
            
        else:
            # Schedule change for next billing period
            try:
                stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                
                # Get the appropriate price ID
                price_id = new_plan.stripe_price_id_yearly if billing_period == 'yearly' else new_plan.stripe_price_id_monthly
                
                if price_id:
                    # Use pre-configured price ID (preferred)
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        items=[{
                            'id': stripe_sub['items']['data'][0]['id'],
                            'price': price_id,
                            'quantity': 1
                        }],
                        proration_behavior='none'
                    )
                else:
                    # Fallback to dynamic pricing if no price ID
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        items=[{
                            'id': stripe_sub['items']['data'][0]['id'],
                            'price_data': {
                                'currency': 'brl',
                                'product_data': {
                                    'name': new_plan.name,
                                },
                                'unit_amount': int(new_plan.get_price(billing_period) * 100),
                                'recurring': {
                                    'interval': 'year' if billing_period == 'yearly' else 'month',
                                    'interval_count': 1
                                }
                            }
                        }],
                        proration_behavior='none'
                    )
                
                # Store pending change in metadata
                subscription.metadata = subscription.metadata or {}
                subscription.metadata['pending_plan_change'] = {
                    'plan_id': new_plan.id,
                    'billing_period': billing_period,
                    'effective_date': subscription.current_period_end.isoformat()
                }
                subscription.save()
                
            except stripe.error.StripeError as e:
                logger.error(f"Failed to schedule plan change: {e}")
                raise
        
        # Send notification
        notification_service.notify_subscription_updated(
            subscription.company.id,
            {
                'subscription_id': subscription.id,
                'status': subscription.status,
                'plan': new_plan.name,
                'changes': {
                    'plan_changed': True,
                    'old_plan': old_plan.name,
                    'new_plan': new_plan.name,
                    'change_type': change_type,
                    'immediate': immediate,
                    'proration': proration if immediate else None
                }
            }
        )
        
        return {
            'success': True,
            'subscription_id': subscription.id,
            'old_plan': old_plan.name,
            'new_plan': new_plan.name,
            'change_type': change_type,
            'immediate': immediate,
            'proration': proration if immediate else None,
            'effective_date': timezone.now() if immediate else subscription.current_period_end
        }
    
    @classmethod
    def validate_subscription_limits(cls, subscription) -> Dict[str, bool]:
        """Validate subscription against usage limits"""
        from ..models import UsageRecord
        
        if not subscription or not subscription.is_active:
            return {
                'transactions': False,
                'bank_accounts': False,
                'ai_requests': False
            }
        
        results = {}
        
        # Check each usage type
        usage_types = [
            ('transaction', 'max_transactions'),
            ('bank_account', 'max_bank_accounts'),
            ('ai_request', 'max_ai_requests')
        ]
        
        for usage_type, limit_field in usage_types:
            current_usage = UsageRecord.get_current_usage(
                subscription.company,
                usage_type
            )
            limit = getattr(subscription.plan, limit_field)
            results[f'{usage_type}s'] = current_usage.count < limit
        
        return results
    
    @classmethod
    def get_grace_period_end(cls, subscription) -> Optional[datetime]:
        """Get grace period end date for past due subscriptions"""
        if subscription.status != 'past_due':
            return None
        
        # 7-day grace period from when payment failed
        if subscription.current_period_end:
            return subscription.current_period_end + timedelta(days=7)
        
        return None
    
    @classmethod
    def should_suspend_access(cls, subscription) -> bool:
        """Determine if access should be suspended"""
        if not subscription:
            return True
        
        if subscription.status == 'expired':
            return True
        
        if subscription.status == 'cancelled' and subscription.current_period_end:
            # Allow access until end of paid period
            return timezone.now() > subscription.current_period_end
        
        if subscription.status == 'past_due':
            grace_period_end = cls.get_grace_period_end(subscription)
            if grace_period_end:
                return timezone.now() > grace_period_end
        
        return False