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
        """Check if plan upgrade is allowed"""
        from ..models import SubscriptionPlan
        
        # Define plan hierarchy
        plan_hierarchy = {
            'starter': 1,
            'professional': 2,
            'enterprise': 3
        }
        
        current_level = plan_hierarchy.get(current_plan.name, 0)
        new_level = plan_hierarchy.get(new_plan.name, 0)
        
        if new_level > current_level:
            return True, "upgrade"
        elif new_level < current_level:
            return True, "downgrade"
        else:
            return False, "same_plan"
    
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
                
                # Update subscription with new price
                updated_sub = stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    items=[{
                        'id': stripe_sub['items']['data'][0]['id'],
                        'price_data': {
                            'currency': 'brl',
                            'product_data': {
                                'name': new_plan.display_name,
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
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    items=[{
                        'id': stripe_sub['items']['data'][0]['id'],
                        'price_data': {
                            'currency': 'brl',
                            'product_data': {
                                'name': new_plan.display_name,
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