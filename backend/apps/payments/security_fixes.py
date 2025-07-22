"""
Security fixes for payment system
"""
import hashlib
import logging
from django.core.cache import cache
from django.db import transaction
from typing import Dict, Any

logger = logging.getLogger(__name__)


class WebhookSecurity:
    """Security improvements for webhook processing"""
    
    @staticmethod
    def check_idempotency(event_id: str, event_type: str) -> bool:
        """Check if webhook event was already processed"""
        cache_key = f"webhook_processed:{event_type}:{event_id}"
        
        if cache.get(cache_key):
            logger.info(f"Duplicate webhook event ignored: {event_id}")
            return False
            
        # Mark as processed for 24 hours
        cache.set(cache_key, True, 86400)
        return True
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> bool:
        """Validate webhook metadata contains required fields"""
        required_fields = ['company_id', 'plan_id', 'user_id']
        
        for field in required_fields:
            if field not in metadata:
                logger.error(f"Missing required metadata field: {field}")
                return False
                
        # Validate IDs are integers
        try:
            for field in required_fields:
                int(metadata[field])
        except (ValueError, TypeError):
            logger.error("Invalid metadata format")
            return False
            
        return True
    
    @staticmethod
    @transaction.atomic
    def process_webhook_atomic(handler_func, *args, **kwargs):
        """Process webhook in atomic transaction"""
        try:
            return handler_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}", exc_info=True)
            raise


class UsageLimitsFixes:
    """Fixes for usage limits enforcement"""
    
    @staticmethod
    def increment_usage_safe(company, usage_type: str) -> bool:
        """Safely increment usage counters with validation"""
        from apps.companies.models import Company
        
        # Use select_for_update to prevent race conditions
        with transaction.atomic():
            company = Company.objects.select_for_update().get(pk=company.pk)
            
            if usage_type == 'transactions':
                limit = company.subscription_plan.max_transactions
                current = company.current_month_transactions
                
                if current >= limit and limit != 999999:  # 999999 = unlimited
                    return False
                    
                company.current_month_transactions += 1
                
            elif usage_type == 'ai_requests':
                limit = company.subscription_plan.max_ai_requests_per_month
                current = company.current_month_ai_requests
                
                if current >= limit and limit != 999999:
                    return False
                    
                company.current_month_ai_requests += 1
                
            company.save(update_fields=[f'current_month_{usage_type}'])
            return True
    
    @staticmethod
    def check_rate_limit(user_id: int, action: str, limit: int = 10, window: int = 60) -> bool:
        """Check rate limiting for specific actions"""
        cache_key = f"rate_limit:{user_id}:{action}"
        
        # Get current count
        current = cache.get(cache_key, 0)
        
        if current >= limit:
            logger.warning(f"Rate limit exceeded for user {user_id} on action {action}")
            return False
            
        # Increment with expiry
        cache.set(cache_key, current + 1, window)
        return True


class SubscriptionValidation:
    """Additional validation for subscription operations"""
    
    @staticmethod
    def can_upgrade_to_plan(company, target_plan) -> Dict[str, Any]:
        """Check if upgrade is valid"""
        current_plan = company.subscription_plan
        
        if not current_plan:
            return {'valid': False, 'reason': 'No current plan'}
            
        if current_plan.id == target_plan.id:
            return {'valid': False, 'reason': 'Already on this plan'}
            
        if current_plan.price_monthly > target_plan.price_monthly:
            return {'valid': True, 'is_downgrade': True}
            
        return {'valid': True, 'is_downgrade': False}
    
    @staticmethod
    def calculate_proration(company, new_plan, billing_cycle='monthly') -> Dict[str, Any]:
        """Calculate proration for plan changes"""
        from datetime import datetime
        from decimal import Decimal
        
        if not company.next_billing_date:
            return {'amount': 0, 'credit': 0}
            
        days_remaining = (company.next_billing_date - datetime.now().date()).days
        
        if days_remaining <= 0:
            return {'amount': 0, 'credit': 0}
            
        # Calculate credit for unused time
        current_price = company.subscription_plan.price_monthly
        if billing_cycle == 'yearly':
            current_price = company.subscription_plan.price_yearly / 12
            
        daily_rate = current_price / 30
        credit = daily_rate * days_remaining
        
        # Calculate charge for new plan
        new_price = new_plan.price_monthly
        if billing_cycle == 'yearly':
            new_price = new_plan.price_yearly / 12
            
        new_daily_rate = new_price / 30
        charge = new_daily_rate * days_remaining
        
        return {
            'credit': round(credit, 2),
            'charge': round(charge, 2),
            'net_amount': round(charge - credit, 2),
            'days_remaining': days_remaining
        }