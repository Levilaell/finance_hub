"""
Payment method management service
Handles secure card management with PCI DSS compliance
"""
import logging
from typing import Dict, Any, Optional, List
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
import re

from .stripe_service import StripeService
from .notification_service import notification_service
from .audit_service import PaymentAuditService
from ..exceptions import (
    PaymentMethodException,
    StripeException
)

logger = logging.getLogger(__name__)


class PaymentMethodManager:
    """Manages payment methods with security and compliance"""
    
    # Card validation patterns
    CARD_PATTERNS = {
        'visa': r'^4[0-9]{12}(?:[0-9]{3})?$',
        'mastercard': r'^5[1-5][0-9]{14}$|^2(?:2(?:2[1-9]|[3-9][0-9])|[3-6][0-9][0-9]|7(?:[01][0-9]|20))[0-9]{12}$',
        'amex': r'^3[47][0-9]{13}$',
        'discover': r'^6(?:011|5[0-9]{2})[0-9]{12}$',
        'diners': r'^3(?:0[0-5]|[68][0-9])[0-9]{11}$',
        'jcb': r'^(?:2131|1800|35\d{3})\d{11}$'
    }
    
    # Security configuration
    MAX_PAYMENT_METHODS_PER_COMPANY = 10
    MAX_FAILED_ATTEMPTS_PER_HOUR = 5
    
    def __init__(self):
        self.stripe_service = StripeService()
    
    @transaction.atomic
    def add_payment_method(self,
                         company: 'Company',
                         payment_method_id: str,
                         set_as_default: bool = True,
                         user: Optional['User'] = None,
                         request_metadata: Optional[Dict[str, Any]] = None) -> 'PaymentMethod':
        """
        Add a new payment method for a company
        
        Args:
            company: Company instance
            payment_method_id: Stripe payment method ID (pm_xxx)
            set_as_default: Set as default payment method
            user: User adding the payment method
            request_metadata: Request metadata (IP, user agent, etc.)
            
        Returns:
            Created PaymentMethod instance
            
        Raises:
            PaymentMethodException: If validation fails
            StripeException: If Stripe operation fails
        """
        from ..models import PaymentMethod, Subscription
        from django.core.cache import cache
        
        # Security check: Rate limiting
        rate_limit_key = f"pm_add_attempts:{company.id}"
        attempts = cache.get(rate_limit_key, 0)
        if attempts >= self.MAX_FAILED_ATTEMPTS_PER_HOUR:
            logger.warning(f"Rate limit exceeded for company {company.id}")
            PaymentAuditService.log_security_event(
                event_type='payment_method_rate_limit',
                user=user,
                company=company,
                details={
                    'attempts': attempts,
                    'ip_address': request_metadata.get('ip_address') if request_metadata else None
                }
            )
            raise PaymentMethodException("Too many attempts. Please try again later.")
        
        # Check payment method limit
        current_count = company.payment_methods.count()
        if current_count >= self.MAX_PAYMENT_METHODS_PER_COMPANY:
            raise PaymentMethodException(
                f"Maximum number of payment methods ({self.MAX_PAYMENT_METHODS_PER_COMPANY}) reached"
            )
        
        # Validate payment method ID format
        if not self._validate_payment_method_id(payment_method_id):
            cache.set(rate_limit_key, attempts + 1, 3600)  # 1 hour
            raise PaymentMethodException("Invalid payment method ID format")
        
        try:
            # Get or create Stripe customer
            subscription = getattr(company, 'subscription', None)
            if not subscription or not subscription.stripe_customer_id:
                # Create customer if doesn't exist
                user_for_customer = user or company.owner
                customer_id = self.stripe_service.create_or_get_customer(company, user_for_customer)
                
                # Create subscription record if doesn't exist
                if not subscription:
                    from apps.companies.models import SubscriptionPlan
                    default_plan = SubscriptionPlan.objects.filter(name='starter').first()
                    if not default_plan:
                        raise PaymentMethodException("No default plan available")
                    
                    subscription = Subscription.objects.create(
                        company=company,
                        plan=default_plan,
                        status='pending',
                        stripe_customer_id=customer_id
                    )
                else:
                    subscription.stripe_customer_id = customer_id
                    subscription.save()
            
            # Attach payment method in Stripe
            stripe_pm = self.stripe_service.attach_payment_method(
                payment_method_id=payment_method_id,
                customer_id=subscription.stripe_customer_id,
                set_default=set_as_default
            )
            
            # Validate card details
            if stripe_pm['type'] == 'card':
                card = stripe_pm['card']
                if not self._validate_card_details(card):
                    raise PaymentMethodException("Invalid card details")
            
            # Create local payment method record
            payment_method = PaymentMethod.objects.create(
                company=company,
                type=stripe_pm['type'],
                is_default=set_as_default,
                stripe_payment_method_id=payment_method_id,
                brand=stripe_pm.get('card', {}).get('brand', ''),
                last4=stripe_pm.get('card', {}).get('last4', ''),
                exp_month=stripe_pm.get('card', {}).get('exp_month'),
                exp_year=stripe_pm.get('card', {}).get('exp_year'),
                metadata={
                    'added_by': str(user.id) if user else None,
                    'added_at': timezone.now().isoformat(),
                    'fingerprint': stripe_pm.get('card', {}).get('fingerprint'),
                    'country': stripe_pm.get('card', {}).get('country'),
                    'funding': stripe_pm.get('card', {}).get('funding')
                }
            )
            
            # Clear rate limit on success
            cache.delete(rate_limit_key)
            
            # Log successful addition
            PaymentAuditService.log_payment_method_action(
                action_type='added',
                payment_method=payment_method,
                user=user,
                ip_address=request_metadata.get('ip_address') if request_metadata else None,
                user_agent=request_metadata.get('user_agent') if request_metadata else None,
                metadata={
                    'set_as_default': set_as_default,
                    'card_brand': payment_method.brand,
                    'card_country': stripe_pm.get('card', {}).get('country')
                }
            )
            
            # Send notification
            notification_service.notify_payment_method_added(
                company_id=company.id,
                data={
                    'brand': payment_method.brand,
                    'last4': payment_method.last4,
                    'is_default': payment_method.is_default
                }
            )
            
            logger.info(f"Added payment method {payment_method.id} for company {company.name}")
            return payment_method
            
        except Exception as e:
            # Increment rate limit on failure
            cache.set(rate_limit_key, attempts + 1, 3600)
            
            # Log failed attempt
            PaymentAuditService.log_security_event(
                event_type='payment_method_add_failed',
                user=user,
                company=company,
                details={
                    'error': type(e).__name__,
                    'payment_method_id': payment_method_id[:10] + '...' if payment_method_id else None,
                    'ip_address': request_metadata.get('ip_address') if request_metadata else None
                }
            )
            
            logger.error(f"Failed to add payment method: {e}")
            if isinstance(e, (PaymentMethodException, StripeException)):
                raise
            raise PaymentMethodException(f"Failed to add payment method: {str(e)}")
    
    @transaction.atomic
    def update_payment_method(self,
                            payment_method: 'PaymentMethod',
                            updates: Dict[str, Any],
                            user: Optional['User'] = None) -> 'PaymentMethod':
        """
        Update a payment method (limited to setting default)
        
        Args:
            payment_method: PaymentMethod instance
            updates: Dictionary of updates (only 'is_default' supported)
            user: User performing the update
            
        Returns:
            Updated PaymentMethod instance
        """
        # Only allow updating is_default
        allowed_updates = {'is_default'}
        invalid_keys = set(updates.keys()) - allowed_updates
        if invalid_keys:
            raise PaymentMethodException(f"Cannot update fields: {', '.join(invalid_keys)}")
        
        old_values = {}
        
        try:
            # Handle setting as default
            if 'is_default' in updates and updates['is_default']:
                old_values['is_default'] = payment_method.is_default
                
                # Update in Stripe
                subscription = payment_method.company.subscription
                if subscription and subscription.stripe_customer_id:
                    self.stripe_service.stripe.Customer.modify(
                        subscription.stripe_customer_id,
                        invoice_settings={
                            'default_payment_method': payment_method.stripe_payment_method_id
                        }
                    )
                
                # Update local records
                payment_method.is_default = True
                payment_method.save()
            
            # Log update
            PaymentAuditService.log_payment_method_action(
                action_type='updated',
                payment_method=payment_method,
                user=user,
                metadata={
                    'updates': updates,
                    'old_values': old_values
                }
            )
            
            logger.info(f"Updated payment method {payment_method.id}")
            return payment_method
            
        except Exception as e:
            logger.error(f"Failed to update payment method: {e}")
            raise PaymentMethodException(f"Failed to update payment method: {str(e)}")
    
    @transaction.atomic
    def remove_payment_method(self,
                            payment_method: 'PaymentMethod',
                            user: Optional['User'] = None,
                            reason: Optional[str] = None) -> bool:
        """
        Remove a payment method
        
        Args:
            payment_method: PaymentMethod to remove
            user: User removing the payment method
            reason: Reason for removal
            
        Returns:
            True if successfully removed
            
        Raises:
            PaymentMethodException: If removal fails
        """
        # Check if it's the only payment method
        if payment_method.is_default:
            other_methods = payment_method.company.payment_methods.exclude(
                id=payment_method.id
            ).exists()
            
            if not other_methods and payment_method.company.subscription_status == 'active':
                raise PaymentMethodException(
                    "Cannot remove the only payment method on an active subscription"
                )
        
        try:
            # Store details for audit before deletion
            pm_details = {
                'id': payment_method.id,
                'brand': payment_method.brand,
                'last4': payment_method.last4,
                'was_default': payment_method.is_default,
                'stripe_id': payment_method.stripe_payment_method_id
            }
            
            # Detach from Stripe
            self.stripe_service.detach_payment_method(
                payment_method.stripe_payment_method_id
            )
            
            # Delete local record
            payment_method.delete()
            
            # Log removal
            PaymentAuditService.log_payment_method_action(
                action_type='removed',
                payment_method=None,  # Already deleted
                user=user,
                metadata={
                    'payment_method_details': pm_details,
                    'reason': reason
                }
            )
            
            # Send notification
            notification_service.notify_payment_method_removed(
                company_id=payment_method.company.id,
                data={
                    'brand': pm_details['brand'],
                    'last4': pm_details['last4']
                }
            )
            
            logger.info(f"Removed payment method {pm_details['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove payment method: {e}")
            raise PaymentMethodException(f"Failed to remove payment method: {str(e)}")
    
    def list_payment_methods(self,
                           company: 'Company',
                           include_expired: bool = False) -> List['PaymentMethod']:
        """
        List payment methods for a company
        
        Args:
            company: Company instance
            include_expired: Include expired cards
            
        Returns:
            List of PaymentMethod instances
        """
        from ..models import PaymentMethod
        
        queryset = PaymentMethod.objects.filter(company=company)
        
        if not include_expired:
            # Filter out expired cards
            current_year = timezone.now().year
            current_month = timezone.now().month
            
            queryset = queryset.exclude(
                exp_year__lt=current_year
            ).exclude(
                exp_year=current_year,
                exp_month__lt=current_month
            )
        
        return queryset.order_by('-is_default', '-created_at')
    
    def validate_payment_method(self,
                              payment_method: 'PaymentMethod') -> Dict[str, Any]:
        """
        Validate a payment method status
        
        Args:
            payment_method: PaymentMethod instance
            
        Returns:
            Validation result dictionary
        """
        result = {
            'is_valid': True,
            'issues': [],
            'requires_update': False
        }
        
        # Check expiration
        if payment_method.exp_month and payment_method.exp_year:
            current_date = timezone.now().date()
            exp_date = timezone.datetime(
                payment_method.exp_year,
                payment_method.exp_month,
                1
            ).date()
            
            if exp_date < current_date:
                result['is_valid'] = False
                result['issues'].append('Card has expired')
            elif (exp_date - current_date).days <= 30:
                result['issues'].append('Card expires soon')
                result['requires_update'] = True
        
        # Check Stripe status
        try:
            stripe_pm = self.stripe_service.stripe.PaymentMethod.retrieve(
                payment_method.stripe_payment_method_id
            )
            
            if stripe_pm.get('card', {}).get('checks', {}):
                checks = stripe_pm['card']['checks']
                
                if checks.get('cvc_check') == 'fail':
                    result['issues'].append('CVC verification failed')
                
                if checks.get('address_postal_code_check') == 'fail':
                    result['issues'].append('Postal code verification failed')
        except Exception as e:
            logger.error(f"Failed to validate payment method in Stripe: {e}")
            result['issues'].append('Unable to verify payment method status')
        
        return result
    
    def _validate_payment_method_id(self, payment_method_id: str) -> bool:
        """
        Validate Stripe payment method ID format
        
        Args:
            payment_method_id: Payment method ID to validate
            
        Returns:
            True if valid format
        """
        # Stripe payment method IDs start with 'pm_' followed by 24 alphanumeric characters
        pattern = r'^pm_[a-zA-Z0-9]{24}$'
        return bool(re.match(pattern, payment_method_id))
    
    def _validate_card_details(self, card_details: Dict[str, Any]) -> bool:
        """
        Validate card details from Stripe
        
        Args:
            card_details: Card details from Stripe
            
        Returns:
            True if valid
        """
        # Basic validation
        required_fields = ['brand', 'last4', 'exp_month', 'exp_year']
        for field in required_fields:
            if field not in card_details:
                return False
        
        # Validate expiration
        try:
            exp_month = int(card_details['exp_month'])
            exp_year = int(card_details['exp_year'])
            
            if not (1 <= exp_month <= 12):
                return False
            
            current_year = timezone.now().year
            if exp_year < current_year:
                return False
            
        except (ValueError, TypeError):
            return False
        
        # Validate last4
        if not re.match(r'^\d{4}$', card_details['last4']):
            return False
        
        return True
    
    def get_payment_method_statistics(self, company: 'Company') -> Dict[str, Any]:
        """
        Get payment method statistics for a company
        
        Args:
            company: Company instance
            
        Returns:
            Statistics dictionary
        """
        payment_methods = self.list_payment_methods(company, include_expired=True)
        
        stats = {
            'total_count': len(payment_methods),
            'active_count': 0,
            'expired_count': 0,
            'expiring_soon_count': 0,
            'brands': {},
            'default_method': None
        }
        
        current_date = timezone.now().date()
        
        for pm in payment_methods:
            # Brand statistics
            stats['brands'][pm.brand] = stats['brands'].get(pm.brand, 0) + 1
            
            # Default method
            if pm.is_default:
                stats['default_method'] = {
                    'id': pm.id,
                    'brand': pm.brand,
                    'last4': pm.last4
                }
            
            # Expiration statistics
            if pm.exp_month and pm.exp_year:
                exp_date = timezone.datetime(pm.exp_year, pm.exp_month, 1).date()
                
                if exp_date < current_date:
                    stats['expired_count'] += 1
                else:
                    stats['active_count'] += 1
                    
                    days_until_expiry = (exp_date - current_date).days
                    if days_until_expiry <= 30:
                        stats['expiring_soon_count'] += 1
        
        return stats