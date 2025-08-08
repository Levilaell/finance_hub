"""
Stripe Customer Portal Integration Service
Provides self-service billing management through Stripe's hosted portal
"""
import logging
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
import stripe

from .stripe_service import StripeService
from .audit_service import PaymentAuditService
from ..exceptions import (
    CustomerPortalException,
    StripeException
)

logger = logging.getLogger(__name__)


class CustomerPortalService:
    """Manages Stripe Customer Portal integration"""
    
    # Portal configuration
    PORTAL_FEATURES = {
        'subscription_cancel': True,
        'subscription_pause': True,
        'subscription_update': True,
        'payment_method_update': True,
        'invoice_history': True,
        'customer_update': {
            'allowed_updates': ['email', 'tax_id'],
            'enabled': True
        }
    }
    
    def __init__(self):
        self.stripe_service = StripeService()
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self._ensure_portal_configuration()
    
    def create_portal_session(self,
                            company: 'Company',
                            return_url: str,
                            user: Optional['User'] = None,
                            flow_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a Stripe Customer Portal session
        
        Args:
            company: Company accessing the portal
            return_url: URL to return to after portal session
            user: User initiating the session
            flow_data: Optional flow data for specific actions
            
        Returns:
            Portal session data with URL
            
        Raises:
            CustomerPortalException: If session creation fails
        """
        from ..models import Subscription
        
        # Get subscription and validate customer
        subscription = getattr(company, 'subscription', None)
        if not subscription or not subscription.stripe_customer_id:
            raise CustomerPortalException(
                "No active subscription found. Please contact support."
            )
        
        try:
            # Create portal session parameters
            session_params = {
                'customer': subscription.stripe_customer_id,
                'return_url': return_url
            }
            
            # Add flow data if specified (for specific actions)
            if flow_data:
                session_params['flow_data'] = flow_data
            
            # Create the session
            session = stripe.billing_portal.Session.create(**session_params)
            
            # Log portal access
            PaymentAuditService.log_payment_action(
                action='customer_portal_accessed',
                user=user,
                company=company,
                metadata={
                    'session_id': session.id,
                    'return_url': return_url,
                    'flow_type': flow_data.get('type') if flow_data else 'general',
                    'created_at': timezone.now().isoformat()
                }
            )
            
            logger.info(f"Created portal session for company {company.name}")
            
            return {
                'url': session.url,
                'session_id': session.id,
                'expires_at': timezone.datetime.fromtimestamp(
                    session.expires_at,
                    tz=timezone.utc
                ),
                'return_url': session.return_url
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create portal session: {e}")
            raise StripeException.from_stripe_error(e)
        except Exception as e:
            logger.error(f"Unexpected error creating portal session: {e}")
            raise CustomerPortalException(
                "Failed to create billing portal session. Please try again."
            )
    
    def create_subscription_update_session(self,
                                         company: 'Company',
                                         return_url: str,
                                         user: Optional['User'] = None) -> Dict[str, Any]:
        """
        Create a portal session specifically for subscription updates
        
        Args:
            company: Company updating subscription
            return_url: URL to return to after update
            user: User initiating the update
            
        Returns:
            Portal session data
        """
        flow_data = {
            'type': 'subscription_update',
            'subscription_update': {
                'subscription': company.subscription.stripe_subscription_id
            }
        }
        
        return self.create_portal_session(
            company=company,
            return_url=return_url,
            user=user,
            flow_data=flow_data
        )
    
    def create_payment_method_update_session(self,
                                           company: 'Company',
                                           return_url: str,
                                           user: Optional['User'] = None) -> Dict[str, Any]:
        """
        Create a portal session specifically for payment method updates
        
        Args:
            company: Company updating payment method
            return_url: URL to return to after update
            user: User initiating the update
            
        Returns:
            Portal session data
        """
        flow_data = {
            'type': 'payment_method_update'
        }
        
        return self.create_portal_session(
            company=company,
            return_url=return_url,
            user=user,
            flow_data=flow_data
        )
    
    def create_invoice_history_session(self,
                                     company: 'Company',
                                     return_url: str,
                                     user: Optional['User'] = None) -> Dict[str, Any]:
        """
        Create a portal session specifically for viewing invoice history
        
        Args:
            company: Company viewing invoices
            return_url: URL to return to after viewing
            user: User initiating the session
            
        Returns:
            Portal session data
        """
        flow_data = {
            'type': 'invoice_history'
        }
        
        return self.create_portal_session(
            company=company,
            return_url=return_url,
            user=user,
            flow_data=flow_data
        )
    
    def create_cancel_subscription_session(self,
                                         company: 'Company',
                                         return_url: str,
                                         user: Optional['User'] = None) -> Dict[str, Any]:
        """
        Create a portal session specifically for subscription cancellation
        
        Args:
            company: Company cancelling subscription
            return_url: URL to return to after cancellation
            user: User initiating the cancellation
            
        Returns:
            Portal session data
        """
        flow_data = {
            'type': 'cancel_subscription',
            'subscription_cancel': {
                'subscription': company.subscription.stripe_subscription_id
            }
        }
        
        return self.create_portal_session(
            company=company,
            return_url=return_url,
            user=user,
            flow_data=flow_data
        )
    
    def _ensure_portal_configuration(self):
        """
        Ensure Stripe Customer Portal is properly configured
        
        This creates or updates the portal configuration with our desired settings.
        In production, this should be done once during deployment.
        """
        try:
            # List existing configurations
            configurations = stripe.billing_portal.Configuration.list(limit=1)
            
            if configurations.data:
                # Update existing configuration
                config = configurations.data[0]
                if not config.active:
                    # Activate if not active
                    stripe.billing_portal.Configuration.modify(
                        config.id,
                        active=True
                    )
            else:
                # Create new configuration
                self._create_portal_configuration()
                
        except stripe.error.StripeError as e:
            logger.warning(f"Could not ensure portal configuration: {e}")
            # Don't fail if we can't configure - portal might still work
    
    def _create_portal_configuration(self):
        """
        Create a new portal configuration with our settings
        """
        try:
            # Build configuration
            config_params = {
                'business_profile': {
                    'headline': 'Manage your Finance Hub subscription',
                    'privacy_policy_url': f"{settings.FRONTEND_URL}/privacy",
                    'terms_of_service_url': f"{settings.FRONTEND_URL}/terms"
                },
                'features': {
                    'customer_update': {
                        'allowed_updates': ['email', 'tax_id'],
                        'enabled': True
                    },
                    'invoice_history': {
                        'enabled': True
                    },
                    'payment_method_update': {
                        'enabled': True
                    },
                    'subscription_cancel': {
                        'cancellation_reason': {
                            'enabled': True,
                            'options': [
                                'too_expensive',
                                'missing_features',
                                'switched_service',
                                'unused',
                                'customer_service',
                                'too_complex',
                                'low_quality',
                                'other'
                            ]
                        },
                        'enabled': True,
                        'mode': 'at_period_end',
                        'proration_behavior': 'none'
                    },
                    'subscription_pause': {
                        'enabled': False  # Not enabling pause for now
                    },
                    'subscription_update': {
                        'default_allowed_updates': ['price', 'quantity', 'promotion_code'],
                        'enabled': True,
                        'proration_behavior': 'create_prorations'
                    }
                }
            }
            
            # Create configuration
            config = stripe.billing_portal.Configuration.create(**config_params)
            
            # Activate it
            stripe.billing_portal.Configuration.modify(
                config.id,
                active=True
            )
            
            logger.info(f"Created portal configuration: {config.id}")
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create portal configuration: {e}")
            # Don't raise - portal might work with default config
    
    def get_portal_configuration(self) -> Optional[Dict[str, Any]]:
        """
        Get current portal configuration
        
        Returns:
            Configuration data or None
        """
        try:
            configurations = stripe.billing_portal.Configuration.list(
                limit=1,
                active=True
            )
            
            if configurations.data:
                config = configurations.data[0]
                return {
                    'id': config.id,
                    'active': config.active,
                    'features': config.features,
                    'business_profile': config.business_profile,
                    'created': timezone.datetime.fromtimestamp(
                        config.created,
                        tz=timezone.utc
                    )
                }
            
            return None
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get portal configuration: {e}")
            return None
    
    def validate_portal_access(self, company: 'Company') -> Tuple[bool, str]:
        """
        Validate if company can access customer portal
        
        Args:
            company: Company to validate
            
        Returns:
            Tuple of (can_access, reason)
        """
        # Check if company has subscription
        subscription = getattr(company, 'subscription', None)
        if not subscription:
            return False, "No subscription found"
        
        # Check if has Stripe customer
        if not subscription.stripe_customer_id:
            return False, "No billing account found"
        
        # Check subscription status
        if subscription.status in ['expired', 'cancelled']:
            return False, "Subscription is not active"
        
        # Check if in trial without payment method
        if subscription.status == 'trial':
            from ..models import PaymentMethod
            has_payment_method = PaymentMethod.objects.filter(
                company=company,
                is_default=True
            ).exists()
            
            if not has_payment_method:
                return False, "Please add a payment method first"
        
        return True, "Access granted"
    
    def generate_portal_links(self, company: 'Company', base_url: str) -> Dict[str, str]:
        """
        Generate quick access links for different portal actions
        
        Args:
            company: Company for links
            base_url: Base URL for return URLs
            
        Returns:
            Dictionary of action -> URL mappings
        """
        links = {}
        
        # Validate access first
        can_access, _ = self.validate_portal_access(company)
        if not can_access:
            return links
        
        # Define return URLs
        return_urls = {
            'general': f"{base_url}/dashboard/billing",
            'subscription': f"{base_url}/dashboard/billing/subscription",
            'payment_methods': f"{base_url}/dashboard/billing/payment-methods",
            'invoices': f"{base_url}/dashboard/billing/invoices"
        }
        
        try:
            # Generate links for each action
            actions = [
                ('manage_billing', 'general', None),
                ('update_subscription', 'subscription', self.create_subscription_update_session),
                ('update_payment_method', 'payment_methods', self.create_payment_method_update_session),
                ('view_invoices', 'invoices', self.create_invoice_history_session)
            ]
            
            for action, return_key, session_creator in actions:
                try:
                    if session_creator:
                        result = session_creator(
                            company=company,
                            return_url=return_urls[return_key]
                        )
                    else:
                        result = self.create_portal_session(
                            company=company,
                            return_url=return_urls[return_key]
                        )
                    
                    links[action] = result['url']
                    
                except Exception as e:
                    logger.error(f"Failed to generate {action} link: {e}")
                    links[action] = None
            
        except Exception as e:
            logger.error(f"Failed to generate portal links: {e}")
        
        return links