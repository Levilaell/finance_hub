"""
AI Credit and usage-based billing service
Handles credit purchases, consumption tracking, and metered billing
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction, models
from django.core.cache import cache
from django.conf import settings

from .stripe_service import StripeService
from .notification_service import notification_service
from .audit_service import PaymentAuditService
from ..exceptions import (
    InsufficientCreditsException,
    CreditPurchaseException,
    UsageTrackingException
)

logger = logging.getLogger(__name__)


class AICreditService:
    """Manages AI credits and usage-based billing"""
    
    # Credit pricing configuration
    CREDIT_PACKAGES = [
        {
            'id': 'credits_100',
            'credits': 100,
            'price': Decimal('9.90'),
            'currency': 'BRL',
            'name': '100 AI Credits',
            'description': 'Perfect for trying out AI features'
        },
        {
            'id': 'credits_500',
            'credits': 500,
            'price': Decimal('39.90'),
            'currency': 'BRL',
            'name': '500 AI Credits',
            'description': 'Great for regular use',
            'savings': '20%'
        },
        {
            'id': 'credits_1000',
            'credits': 1000,
            'price': Decimal('69.90'),
            'currency': 'BRL',
            'name': '1000 AI Credits',
            'description': 'Best value for power users',
            'savings': '30%'
        },
        {
            'id': 'credits_5000',
            'credits': 5000,
            'price': Decimal('299.90'),
            'currency': 'BRL',
            'name': '5000 AI Credits',
            'description': 'Enterprise package',
            'savings': '40%'
        }
    ]
    
    # Credit consumption rates
    CREDIT_COSTS = {
        'transaction_categorization': 1,
        'ai_insight_generation': 5,
        'financial_report': 10,
        'cash_flow_prediction': 15,
        'investment_advice': 20,
        'tax_optimization': 25,
        'custom_analysis': 30
    }
    
    # Rate limiting
    MAX_CREDITS_PER_DAY = 1000
    MAX_CREDITS_PER_HOUR = 100
    
    def __init__(self):
        self.stripe_service = StripeService()
    
    @transaction.atomic
    def purchase_credits(self,
                       company: 'Company',
                       package_id: str,
                       payment_method_id: str,
                       user: Optional['User'] = None) -> Dict[str, Any]:
        """
        Purchase AI credits
        
        Args:
            company: Company purchasing credits
            package_id: Credit package ID
            payment_method_id: Payment method to use
            user: User making the purchase
            
        Returns:
            Purchase result with transaction details
            
        Raises:
            CreditPurchaseException: If purchase fails
        """
        from ..models import Payment, PaymentMethod, CreditTransaction
        
        # Validate package
        package = self._get_credit_package(package_id)
        if not package:
            raise CreditPurchaseException(f"Invalid credit package: {package_id}")
        
        # Validate payment method
        try:
            payment_method = PaymentMethod.objects.get(
                id=payment_method_id,
                company=company
            )
        except PaymentMethod.DoesNotExist:
            raise CreditPurchaseException("Invalid payment method")
        
        # Check daily purchase limit
        daily_purchased = self._get_daily_purchase_total(company)
        if daily_purchased + package['credits'] > self.MAX_CREDITS_PER_DAY:
            raise CreditPurchaseException(
                f"Daily credit purchase limit ({self.MAX_CREDITS_PER_DAY}) would be exceeded"
            )
        
        try:
            # Process payment through Stripe
            payment_result = self.stripe_service.process_credit_purchase(
                company=company,
                payment_method=payment_method,
                amount=package['price'],
                description=f"{package['name']} - {package['credits']} credits",
                credits=package['credits']
            )
            
            if not payment_result['success']:
                raise CreditPurchaseException(
                    payment_result.get('error', 'Payment failed')
                )
            
            # Create payment record
            payment = Payment.objects.create(
                company=company,
                payment_method=payment_method,
                amount=package['price'],
                currency=package['currency'],
                status='succeeded',
                description=package['name'],
                gateway='stripe',
                stripe_payment_intent_id=payment_result['payment_id'],
                paid_at=timezone.now(),
                metadata={
                    'type': 'credit_purchase',
                    'package_id': package_id,
                    'credits': package['credits']
                }
            )
            
            # Update company credit balance
            old_balance = getattr(company, 'ai_credits_balance', 0) or 0
            new_balance = old_balance + package['credits']
            company.ai_credits_balance = new_balance
            company.save(update_fields=['ai_credits_balance'])
            
            # Create credit transaction record
            credit_transaction = CreditTransaction.objects.create(
                company=company,
                transaction_type='purchase',
                credits=package['credits'],
                balance_before=old_balance,
                balance_after=new_balance,
                description=f"Purchased {package['name']}",
                payment=payment,
                metadata={
                    'package_id': package_id,
                    'price': str(package['price']),
                    'user_id': str(user.id) if user else None
                }
            )
            
            # Log purchase
            PaymentAuditService.log_payment_action(
                action='credits_purchased',
                user=user,
                company=company,
                payment_id=payment.id,
                metadata={
                    'package_id': package_id,
                    'credits': package['credits'],
                    'amount': str(package['price']),
                    'old_balance': old_balance,
                    'new_balance': new_balance
                }
            )
            
            # Send notification
            notification_service.notify_credits_purchased(
                company_id=company.id,
                data={
                    'credits': package['credits'],
                    'new_balance': new_balance,
                    'amount': float(package['price'])
                }
            )
            
            # Clear rate limit cache
            cache_key = f"credit_purchase_daily:{company.id}:{timezone.now().date()}"
            cache.delete(cache_key)
            
            return {
                'success': True,
                'payment_id': payment.id,
                'transaction_id': credit_transaction.id,
                'credits_purchased': package['credits'],
                'new_balance': new_balance,
                'amount': float(package['price'])
            }
            
        except Exception as e:
            logger.error(f"Credit purchase failed: {e}")
            if isinstance(e, CreditPurchaseException):
                raise
            raise CreditPurchaseException(f"Credit purchase failed: {str(e)}")
    
    @transaction.atomic
    def consume_credits(self,
                      company: 'Company',
                      operation: str,
                      quantity: int = 1,
                      description: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Consume AI credits for an operation
        
        Args:
            company: Company consuming credits
            operation: Operation type
            quantity: Number of operations
            description: Optional description
            metadata: Additional metadata
            
        Returns:
            Consumption result
            
        Raises:
            InsufficientCreditsException: If not enough credits
            UsageTrackingException: If tracking fails
        """
        from ..models import CreditTransaction, UsageRecord
        
        # Calculate credit cost
        credit_cost = self.CREDIT_COSTS.get(operation, 1) * quantity
        
        # Check if company has unlimited AI insights
        if company.subscription_plan and company.subscription_plan.unlimited_ai_insights:
            # Track usage but don't deduct credits
            usage_record = UsageRecord.objects.create(
                company=company,
                usage_type='ai_operation',
                quantity=quantity,
                unit_amount=0,  # Free for unlimited plans
                total_amount=0,
                description=description or f"{operation} (unlimited plan)",
                metadata={
                    'operation': operation,
                    'credits_equivalent': credit_cost,
                    'unlimited': True,
                    **(metadata or {})
                }
            )
            
            return {
                'success': True,
                'credits_consumed': 0,
                'unlimited': True,
                'usage_id': usage_record.id
            }
        
        # Check credit balance
        current_balance = getattr(company, 'ai_credits_balance', 0) or 0
        if current_balance < credit_cost:
            raise InsufficientCreditsException(
                f"Insufficient credits. Required: {credit_cost}, Available: {current_balance}"
            )
        
        # Check rate limits
        if not self._check_usage_rate_limit(company, credit_cost):
            raise UsageTrackingException(
                "AI credit usage rate limit exceeded. Please try again later."
            )
        
        try:
            # Deduct credits
            new_balance = current_balance - credit_cost
            company.ai_credits_balance = new_balance
            company.save(update_fields=['ai_credits_balance'])
            
            # Create credit transaction
            credit_transaction = CreditTransaction.objects.create(
                company=company,
                transaction_type='usage',
                credits=-credit_cost,  # Negative for consumption
                balance_before=current_balance,
                balance_after=new_balance,
                description=description or f"{operation} x{quantity}",
                metadata={
                    'operation': operation,
                    'quantity': quantity,
                    **(metadata or {})
                }
            )
            
            # Create usage record for billing
            usage_record = UsageRecord.objects.create(
                company=company,
                usage_type='ai_operation',
                quantity=credit_cost,
                unit_amount=Decimal('0.099'),  # Price per credit
                total_amount=credit_cost * Decimal('0.099'),
                description=description or operation,
                metadata={
                    'operation': operation,
                    'quantity': quantity,
                    'transaction_id': credit_transaction.id,
                    **(metadata or {})
                }
            )
            
            # Update monthly AI request counter
            company.increment_ai_requests()
            
            # Send low balance notification if needed
            if new_balance < 50 and new_balance > 0:
                notification_service.notify_low_credit_balance(
                    company_id=company.id,
                    data={'balance': new_balance}
                )
            
            # Log usage
            logger.info(
                f"AI credits consumed: {credit_cost} for {operation} "
                f"(Company: {company.name}, New balance: {new_balance})"
            )
            
            return {
                'success': True,
                'credits_consumed': credit_cost,
                'new_balance': new_balance,
                'transaction_id': credit_transaction.id,
                'usage_id': usage_record.id
            }
            
        except Exception as e:
            logger.error(f"Credit consumption failed: {e}")
            raise UsageTrackingException(f"Failed to track credit usage: {str(e)}")
    
    def get_credit_balance(self, company: 'Company') -> Dict[str, Any]:
        """
        Get current credit balance and usage statistics
        
        Args:
            company: Company instance
            
        Returns:
            Balance and usage information
        """
        from ..models import CreditTransaction
        from django.db.models import Sum, Count
        
        current_balance = getattr(company, 'ai_credits_balance', 0) or 0
        is_unlimited = (
            company.subscription_plan and
            company.subscription_plan.unlimited_ai_insights
        )
        
        # Get usage statistics for current month
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        
        monthly_stats = CreditTransaction.objects.filter(
            company=company,
            transaction_type='usage',
            created_at__gte=start_of_month
        ).aggregate(
            total_consumed=Sum('credits'),
            usage_count=Count('id')
        )
        
        # Get recent transactions
        recent_transactions = CreditTransaction.objects.filter(
            company=company
        ).order_by('-created_at')[:10]
        
        return {
            'balance': current_balance,
            'is_unlimited': is_unlimited,
            'monthly_usage': abs(monthly_stats['total_consumed'] or 0),
            'monthly_operations': monthly_stats['usage_count'] or 0,
            'recent_transactions': [
                {
                    'id': tx.id,
                    'date': tx.created_at,
                    'type': tx.transaction_type,
                    'credits': tx.credits,
                    'description': tx.description,
                    'balance_after': tx.balance_after
                }
                for tx in recent_transactions
            ],
            'low_balance_warning': current_balance < 50 and not is_unlimited,
            'suggested_package': self._suggest_credit_package(current_balance, monthly_stats)
        }
    
    def get_usage_history(self,
                        company: 'Company',
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        operation_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get detailed usage history
        
        Args:
            company: Company instance
            start_date: Start date filter
            end_date: End date filter
            operation_filter: Filter by operation type
            
        Returns:
            List of usage records
        """
        from ..models import CreditTransaction
        
        queryset = CreditTransaction.objects.filter(
            company=company,
            transaction_type='usage'
        )
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        if operation_filter:
            queryset = queryset.filter(metadata__operation=operation_filter)
        
        queryset = queryset.order_by('-created_at')
        
        return [
            {
                'id': tx.id,
                'date': tx.created_at,
                'operation': tx.metadata.get('operation', 'unknown'),
                'credits': abs(tx.credits),
                'description': tx.description,
                'metadata': tx.metadata
            }
            for tx in queryset[:100]  # Limit to recent 100
        ]
    
    def estimate_credit_usage(self,
                            company: 'Company',
                            operations: Dict[str, int]) -> Dict[str, Any]:
        """
        Estimate credit usage for planned operations
        
        Args:
            company: Company instance
            operations: Dict of operation_type -> quantity
            
        Returns:
            Usage estimate
        """
        total_credits = 0
        breakdown = []
        
        for operation, quantity in operations.items():
            credit_cost = self.CREDIT_COSTS.get(operation, 1)
            operation_total = credit_cost * quantity
            total_credits += operation_total
            
            breakdown.append({
                'operation': operation,
                'quantity': quantity,
                'credits_per_operation': credit_cost,
                'total_credits': operation_total,
                'cost_estimate': float(operation_total * Decimal('0.099'))
            })
        
        current_balance = getattr(company, 'ai_credits_balance', 0) or 0
        is_unlimited = (
            company.subscription_plan and
            company.subscription_plan.unlimited_ai_insights
        )
        
        return {
            'total_credits_required': total_credits,
            'current_balance': current_balance,
            'sufficient_balance': is_unlimited or current_balance >= total_credits,
            'is_unlimited': is_unlimited,
            'credits_needed': max(0, total_credits - current_balance) if not is_unlimited else 0,
            'estimated_cost': float(total_credits * Decimal('0.099')),
            'breakdown': breakdown,
            'suggested_package': self._suggest_credit_package(
                current_balance,
                {'required': total_credits}
            ) if not is_unlimited else None
        }
    
    def create_credit_subscription(self,
                                 company: 'Company',
                                 monthly_credits: int,
                                 price_per_credit: Decimal = Decimal('0.08')) -> Dict[str, Any]:
        """
        Create a recurring credit subscription (for enterprise)
        
        Args:
            company: Company instance
            monthly_credits: Credits to add each month
            price_per_credit: Price per credit
            
        Returns:
            Subscription details
        """
        # This would create a Stripe subscription for recurring credits
        # Implementation depends on business requirements
        raise NotImplementedError("Credit subscriptions coming soon")
    
    def _get_credit_package(self, package_id: str) -> Optional[Dict[str, Any]]:
        """
        Get credit package by ID
        
        Args:
            package_id: Package ID
            
        Returns:
            Package details or None
        """
        for package in self.CREDIT_PACKAGES:
            if package['id'] == package_id:
                return package
        return None
    
    def _get_daily_purchase_total(self, company: 'Company') -> int:
        """
        Get total credits purchased today
        
        Args:
            company: Company instance
            
        Returns:
            Total credits purchased today
        """
        cache_key = f"credit_purchase_daily:{company.id}:{timezone.now().date()}"
        total = cache.get(cache_key)
        
        if total is None:
            from ..models import CreditTransaction
            from django.db.models import Sum
            
            start_of_day = timezone.now().replace(hour=0, minute=0, second=0)
            
            result = CreditTransaction.objects.filter(
                company=company,
                transaction_type='purchase',
                created_at__gte=start_of_day
            ).aggregate(
                total=Sum('credits')
            )
            
            total = result['total'] or 0
            cache.set(cache_key, total, 86400)  # Cache for 24 hours
        
        return total
    
    def _check_usage_rate_limit(self, company: 'Company', credits: int) -> bool:
        """
        Check if usage is within rate limits
        
        Args:
            company: Company instance
            credits: Credits to consume
            
        Returns:
            True if within limits
        """
        # Hourly limit check
        hourly_key = f"credit_usage_hourly:{company.id}:{timezone.now().hour}"
        hourly_usage = cache.get(hourly_key, 0)
        
        if hourly_usage + credits > self.MAX_CREDITS_PER_HOUR:
            return False
        
        # Update cache
        cache.set(hourly_key, hourly_usage + credits, 3600)
        
        return True
    
    def _suggest_credit_package(self,
                              current_balance: int,
                              usage_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Suggest appropriate credit package based on usage
        
        Args:
            current_balance: Current credit balance
            usage_data: Usage statistics
            
        Returns:
            Suggested package or None
        """
        # If balance is low
        if current_balance < 50:
            # Suggest based on monthly usage or required credits
            monthly_usage = usage_data.get('total_consumed', 0)
            required_credits = usage_data.get('required', 0)
            
            target_credits = max(monthly_usage * 2, required_credits, 100)
            
            # Find appropriate package
            for package in self.CREDIT_PACKAGES:
                if package['credits'] >= target_credits:
                    return package
            
            # Return largest package if usage is very high
            return self.CREDIT_PACKAGES[-1]
        
        return None
    
    def get_credit_packages(self) -> List[Dict[str, Any]]:
        """
        Get available credit packages
        
        Returns:
            List of credit packages
        """
        return self.CREDIT_PACKAGES.copy()