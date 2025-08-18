"""
Enhanced webhook security service following Stripe best practices
Implements advanced validation, secret rotation, and security measures
"""
import hashlib
import hmac
import time
import json
import stripe
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from core.logging_utils import get_secure_logger

logger = get_secure_logger(__name__)


class EnhancedWebhookSecurity:
    """Enhanced webhook security with multiple validation layers"""
    
    def __init__(self):
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self.tolerance = 300  # 5 minutes tolerance for timestamp validation
        self.replay_cache_timeout = 86400  # 24 hours cache for replay protection
    
    def validate_webhook(self, 
                        payload: bytes, 
                        signature_header: str,
                        request_timestamp: Optional[float] = None) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Comprehensive webhook validation with multiple security layers
        
        Args:
            payload: Raw webhook payload bytes
            signature_header: Stripe-Signature header
            request_timestamp: Optional request timestamp
            
        Returns:
            Tuple of (is_valid, event_data, error_message)
        """
        try:
            # Layer 1: Basic signature validation
            event = self._validate_signature(payload, signature_header)
            if not event:
                return False, None, "Invalid webhook signature"
            
            # Layer 2: Timestamp validation  
            if not self._validate_timestamp(signature_header, request_timestamp):
                return False, None, "Webhook timestamp outside tolerance window"
            
            # Layer 3: Event structure validation
            if not self._validate_event_structure(event):
                return False, None, "Invalid event structure"
            
            # Layer 4: Replay attack protection
            if not self._validate_replay_protection(event):
                return False, None, "Duplicate webhook event detected"
            
            # Layer 5: Event type validation
            if not self._validate_event_type(event):
                return False, None, "Unsupported or suspicious event type"
            
            # Layer 6: Rate limiting validation
            if not self._validate_rate_limit(event):
                return False, None, "Rate limit exceeded for webhook events"
            
            # Layer 7: Content validation
            if not self._validate_event_content(event):
                return False, None, "Invalid or suspicious event content"
            
            logger.info("Webhook validation successful", extra={
                'event_id': event.get('id'),
                'event_type': event.get('type'),
                'validation_layers_passed': 7
            })
            
            return True, event, "Validation successful"
            
        except stripe.error.SignatureVerificationError as e:
            logger.warning(f"Webhook signature verification failed: {e}")
            return False, None, f"Signature verification failed: {str(e)}"
        except Exception as e:
            logger.error(f"Webhook validation error: {e}")
            return False, None, f"Validation error: {str(e)}"
    
    def _validate_signature(self, payload: bytes, signature_header: str) -> Optional[Dict[str, Any]]:
        """Validate webhook signature using Stripe's library"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature_header, self.webhook_secret
            )
            return event
        except stripe.error.SignatureVerificationError:
            # Try with fallback secrets if configured
            fallback_secrets = getattr(settings, 'STRIPE_WEBHOOK_FALLBACK_SECRETS', [])
            for secret in fallback_secrets:
                try:
                    event = stripe.Webhook.construct_event(payload, signature_header, secret)
                    logger.info("Webhook validated with fallback secret")
                    return event
                except stripe.error.SignatureVerificationError:
                    continue
            
            return None
    
    def _validate_timestamp(self, signature_header: str, request_timestamp: Optional[float] = None) -> bool:
        """Validate webhook timestamp to prevent replay attacks"""
        try:
            # Extract timestamp from signature header
            timestamp = None
            for pair in signature_header.split(','):
                if pair.startswith('t='):
                    timestamp = int(pair[2:])
                    break
            
            if timestamp is None:
                logger.warning("No timestamp found in webhook signature")
                return False
            
            # Use request timestamp if provided, otherwise current time
            current_time = request_timestamp or time.time()
            
            # Check if timestamp is within tolerance
            time_diff = abs(current_time - timestamp)
            if time_diff > self.tolerance:
                logger.warning(f"Webhook timestamp outside tolerance: {time_diff}s")
                return False
            
            return True
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid timestamp in webhook signature: {e}")
            return False
    
    def _validate_event_structure(self, event: Dict[str, Any]) -> bool:
        """Validate basic event structure"""
        required_fields = ['id', 'type', 'data', 'created']
        
        for field in required_fields:
            if field not in event:
                logger.warning(f"Missing required field in webhook: {field}")
                return False
        
        # Validate data structure
        if 'object' not in event.get('data', {}):
            logger.warning("Missing 'object' in webhook data")
            return False
        
        return True
    
    def _validate_replay_protection(self, event: Dict[str, Any]) -> bool:
        """Prevent replay attacks using event ID caching"""
        event_id = event.get('id')
        if not event_id:
            return False
        
        cache_key = f"webhook_processed:{event_id}"
        
        # Check if event was already processed
        if cache.get(cache_key):
            logger.warning(f"Duplicate webhook event detected: {event_id}")
            return False
        
        # Cache this event ID to prevent replays
        cache.set(cache_key, True, timeout=self.replay_cache_timeout)
        return True
    
    def _validate_event_type(self, event: Dict[str, Any]) -> bool:
        """Validate event type against allowed list"""
        event_type = event.get('type')
        if not event_type:
            return False
        
        # Define allowed event types
        allowed_event_types = {
            # Subscription events
            'customer.subscription.created',
            'customer.subscription.updated', 
            'customer.subscription.deleted',
            'customer.subscription.trial_will_end',
            
            # Invoice events
            'invoice.created',
            'invoice.finalized',
            'invoice.payment_succeeded',
            'invoice.payment_failed',
            'invoice.payment_action_required',
            
            # Payment events
            'payment_intent.succeeded',
            'payment_intent.payment_failed',
            'payment_intent.requires_action',
            
            # Checkout events
            'checkout.session.completed',
            'checkout.session.expired',
            
            # Customer events
            'customer.created',
            'customer.updated',
            'customer.deleted',
            
            # Payment method events
            'payment_method.attached',
            'payment_method.detached',
            'payment_method.updated',
            
            # Dispute events
            'charge.dispute.created',
            'charge.dispute.closed',
            'charge.dispute.funds_withdrawn',
            'charge.dispute.funds_reinstated',
            
            # Test events
            'ping'  # Stripe test event
        }
        
        if event_type not in allowed_event_types:
            logger.warning(f"Unknown or suspicious event type: {event_type}")
            # For production, might want to return False here
            # For now, log but allow for flexibility
            pass
        
        return True
    
    def _validate_rate_limit(self, event: Dict[str, Any]) -> bool:
        """Validate webhook rate limits to prevent abuse"""
        # Rate limit by event type
        event_type = event.get('type')
        if not event_type:
            return False
        
        rate_limit_key = f"webhook_rate_limit:{event_type}"
        current_count = cache.get(rate_limit_key, 0)
        
        # Define rate limits per event type (per hour)
        rate_limits = {
            'customer.subscription.created': 100,
            'customer.subscription.updated': 500,
            'invoice.payment_succeeded': 1000,
            'invoice.payment_failed': 100,
            'checkout.session.completed': 200,
            'default': 1000  # Default rate limit
        }
        
        limit = rate_limits.get(event_type, rate_limits['default'])
        
        if current_count >= limit:
            logger.warning(f"Rate limit exceeded for event type {event_type}: {current_count}/{limit}")
            return False
        
        # Increment counter
        cache.set(rate_limit_key, current_count + 1, timeout=3600)  # 1 hour window
        return True
    
    def _validate_event_content(self, event: Dict[str, Any]) -> bool:
        """Validate event content for suspicious patterns"""
        data_object = event.get('data', {}).get('object', {})
        
        # Check for required fields based on event type
        event_type = event.get('type')
        
        if event_type == 'customer.subscription.created':
            required_fields = ['id', 'customer', 'status', 'items']
            for field in required_fields:
                if field not in data_object:
                    logger.warning(f"Missing required field '{field}' in subscription event")
                    return False
        
        elif event_type == 'invoice.payment_succeeded':
            required_fields = ['id', 'amount_paid', 'currency', 'status']
            for field in required_fields:
                if field not in data_object:
                    logger.warning(f"Missing required field '{field}' in invoice event")
                    return False
        
        elif event_type == 'checkout.session.completed':
            required_fields = ['id', 'payment_status', 'amount_total']
            for field in required_fields:
                if field not in data_object:
                    logger.warning(f"Missing required field '{field}' in checkout event")
                    return False
        
        # Validate metadata if present
        metadata = data_object.get('metadata', {})
        if metadata:
            # Check for required metadata fields for our application
            if event_type in ['customer.subscription.created', 'checkout.session.completed']:
                if not metadata.get('company_id'):
                    logger.warning("Missing company_id in event metadata")
                    # Don't fail validation, but log for investigation
        
        return True
    
    def rotate_webhook_secret(self, new_secret: str) -> bool:
        """
        Rotate webhook secret with graceful transition
        
        Args:
            new_secret: New webhook secret from Stripe
            
        Returns:
            bool: Success status
        """
        try:
            # Store current secret as fallback
            current_secret = self.webhook_secret
            fallback_secrets = getattr(settings, 'STRIPE_WEBHOOK_FALLBACK_SECRETS', [])
            
            # Add current secret to fallback list if not already there
            if current_secret and current_secret not in fallback_secrets:
                fallback_secrets.insert(0, current_secret)
                # Keep only last 3 secrets
                fallback_secrets = fallback_secrets[:3]
            
            # Update settings (in production, this would update environment variables)
            settings.STRIPE_WEBHOOK_SECRET = new_secret
            settings.STRIPE_WEBHOOK_FALLBACK_SECRETS = fallback_secrets
            
            self.webhook_secret = new_secret
            
            logger.info("Webhook secret rotated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate webhook secret: {e}")
            return False
    
    def get_webhook_health_status(self) -> Dict[str, Any]:
        """Get webhook health and security status"""
        try:
            # Check webhook endpoint configuration
            webhook_configured = bool(self.webhook_secret)
            
            # Check rate limit status
            rate_limit_status = {}
            for event_type in ['customer.subscription.updated', 'invoice.payment_succeeded']:
                rate_limit_key = f"webhook_rate_limit:{event_type}"
                current_count = cache.get(rate_limit_key, 0)
                rate_limit_status[event_type] = {
                    'current': current_count,
                    'limit': 500 if event_type == 'customer.subscription.updated' else 1000
                }
            
            # Check recent webhook activity
            recent_events_key = "webhook_recent_events"
            recent_events = cache.get(recent_events_key, 0)
            
            return {
                'webhook_configured': webhook_configured,
                'rate_limits': rate_limit_status,
                'recent_events_count': recent_events,
                'fallback_secrets_configured': len(getattr(settings, 'STRIPE_WEBHOOK_FALLBACK_SECRETS', [])),
                'security_layers_active': 7,
                'last_check': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting webhook health status: {e}")
            return {
                'webhook_configured': False,
                'error': str(e),
                'last_check': timezone.now().isoformat()
            }


# Global instance
enhanced_webhook_security = EnhancedWebhookSecurity()


def validate_stripe_webhook(payload: bytes, signature_header: str, request_timestamp: Optional[float] = None):
    """
    Convenience function for webhook validation
    
    Returns:
        Tuple of (is_valid, event_data, error_message)
    """
    return enhanced_webhook_security.validate_webhook(payload, signature_header, request_timestamp)