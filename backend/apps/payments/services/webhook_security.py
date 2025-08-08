"""
Stripe webhook security layer
Implements PCI DSS compliant webhook handling with:
- IP allowlisting
- Replay attack protection  
- Rate limiting
- Idempotency checks
- Secure error handling
"""
import ipaddress
import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class WebhookSecurityException(Exception):
    """Base exception for webhook security issues"""
    pass


class WebhookSecurityManager:
    """Manages webhook security validation and protection"""
    
    # Stripe webhook IP ranges (as of 2024)
    STRIPE_WEBHOOK_IPS = [
        '3.18.12.63/32',
        '3.130.192.231/32', 
        '13.235.14.237/32',
        '13.235.122.149/32',
        '18.211.135.69/32',
        '35.154.171.200/32',
        '52.15.183.38/32',
        '54.88.130.119/32',
        '54.88.130.237/32',
        '54.187.174.169/32',
        '54.187.205.235/32',
        '54.187.216.72/32'
    ]
    
    # Security configuration
    WEBHOOK_TOLERANCE_SECONDS = 300  # 5 minutes
    RATE_LIMIT_WINDOW = 3600  # 1 hour
    RATE_LIMIT_MAX_REQUESTS = 100
    IDEMPOTENCY_CACHE_TTL = 86400  # 24 hours
    
    def __init__(self):
        self.ip_networks = [ipaddress.ip_network(ip) for ip in self.STRIPE_WEBHOOK_IPS]
    
    def validate_source_ip(self, ip_address: str) -> bool:
        """
        Validate webhook request comes from Stripe IP ranges
        
        Args:
            ip_address: Source IP of the request
            
        Returns:
            bool: True if IP is valid Stripe IP
            
        Raises:
            WebhookSecurityException: If IP is not from Stripe
        """
        if not ip_address:
            raise WebhookSecurityException("Missing source IP address")
        
        # Allow localhost in development
        if settings.DEBUG and ip_address in ['127.0.0.1', '::1']:
            return True
        
        try:
            ip = ipaddress.ip_address(ip_address)
            for network in self.ip_networks:
                if ip in network:
                    return True
        except ValueError:
            logger.error(f"Invalid IP address format: {ip_address}")
        
        raise WebhookSecurityException(f"Unauthorized webhook source IP: {ip_address}")
    
    def validate_timestamp(self, event_created: int) -> bool:
        """
        Validate webhook event is recent to prevent replay attacks
        
        Args:
            event_created: Unix timestamp when event was created
            
        Returns:
            bool: True if event is within tolerance window
            
        Raises:
            WebhookSecurityException: If event is too old
        """
        current_time = int(time.time())
        time_difference = current_time - event_created
        
        if time_difference > self.WEBHOOK_TOLERANCE_SECONDS:
            raise WebhookSecurityException(
                f"Webhook event too old: {time_difference} seconds"
            )
        
        if time_difference < -60:  # Allow 1 minute future tolerance for clock skew
            raise WebhookSecurityException(
                f"Webhook event timestamp in future: {time_difference} seconds"
            )
        
        return True
    
    def check_rate_limit(self, ip_address: str) -> bool:
        """
        Check if IP has exceeded rate limit
        
        Args:
            ip_address: Source IP to check
            
        Returns:
            bool: True if within rate limit
            
        Raises:
            WebhookSecurityException: If rate limit exceeded
        """
        cache_key = f"webhook_rate_limit:{ip_address}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= self.RATE_LIMIT_MAX_REQUESTS:
            raise WebhookSecurityException(
                f"Rate limit exceeded for IP {ip_address}: {current_count} requests"
            )
        
        # Increment counter
        cache.set(cache_key, current_count + 1, self.RATE_LIMIT_WINDOW)
        return True
    
    def check_idempotency(self, event_id: str) -> bool:
        """
        Check if event has already been processed (idempotency)
        
        Args:
            event_id: Stripe event ID
            
        Returns:
            bool: True if event is new, False if already processed
        """
        cache_key = f"webhook_processed:{event_id}"
        
        if cache.get(cache_key):
            logger.info(f"Duplicate webhook event detected: {event_id}")
            return False
        
        # Mark as processed
        cache.set(cache_key, True, self.IDEMPOTENCY_CACHE_TTL)
        return True
    
    def validate_webhook_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive webhook validation
        
        Args:
            request_data: Dictionary containing:
                - ip_address: Source IP
                - event_id: Stripe event ID
                - event_created: Event creation timestamp
                - signature: Stripe signature header
                
        Returns:
            Validation result dictionary
        """
        validation_result = {
            'is_valid': True,
            'checks_passed': [],
            'error': None
        }
        
        try:
            # 1. Validate source IP
            self.validate_source_ip(request_data.get('ip_address'))
            validation_result['checks_passed'].append('ip_validation')
            
            # 2. Check rate limit
            self.check_rate_limit(request_data.get('ip_address'))
            validation_result['checks_passed'].append('rate_limit')
            
            # 3. Validate timestamp
            self.validate_timestamp(request_data.get('event_created', 0))
            validation_result['checks_passed'].append('timestamp_validation')
            
            # 4. Check idempotency
            if not self.check_idempotency(request_data.get('event_id')):
                validation_result['is_valid'] = False
                validation_result['error'] = 'Duplicate event'
                return validation_result
            
            validation_result['checks_passed'].append('idempotency')
            
        except WebhookSecurityException as e:
            validation_result['is_valid'] = False
            validation_result['error'] = str(e)
            logger.warning(f"Webhook security validation failed: {e}")
        
        return validation_result
    
    def generate_event_hash(self, event_data: Dict[str, Any]) -> str:
        """
        Generate hash of event data for integrity checking
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            SHA256 hash of event data
        """
        # Sort keys for consistent hashing
        sorted_data = json.dumps(event_data, sort_keys=True)
        return hashlib.sha256(sorted_data.encode()).hexdigest()
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """
        Log security-related webhook events
        
        Args:
            event_type: Type of security event
            details: Event details
        """
        from ..services.audit_service import PaymentAuditService
        
        PaymentAuditService.log_security_event(
            event_type=f"webhook_{event_type}",
            user=None,  # No user context in webhooks
            company=None,
            details=details,
            ip_address=details.get('ip_address'),
            user_agent=details.get('user_agent')
        )


class SecureWebhookProcessor:
    """Process webhooks with security validation"""
    
    def __init__(self):
        self.security_manager = WebhookSecurityManager()
    
    def process_webhook(self, 
                       request,
                       payload: bytes,
                       signature: str,
                       gateway) -> Dict[str, Any]:
        """
        Process webhook with full security validation
        
        Args:
            request: Django request object
            payload: Raw webhook payload
            signature: Stripe signature header
            gateway: Payment gateway instance
            
        Returns:
            Processing result dictionary
        """
        # Extract request metadata
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        try:
            # Verify webhook signature first
            event = gateway.verify_webhook(payload, signature)
            if not event:
                raise WebhookSecurityException("Invalid webhook signature")
            
            # Perform security validation
            validation_data = {
                'ip_address': ip_address,
                'event_id': event.get('id'),
                'event_created': event.get('created', 0),
                'signature': signature[:20] + '...'  # Log partial signature only
            }
            
            validation_result = self.security_manager.validate_webhook_request(validation_data)
            
            if not validation_result['is_valid']:
                # Log security failure
                self.security_manager.log_security_event(
                    'validation_failed',
                    {
                        'ip_address': ip_address,
                        'user_agent': user_agent,
                        'error': validation_result['error'],
                        'event_type': event.get('type'),
                        'event_id': event.get('id')
                    }
                )
                
                # Return generic error (don't expose security details)
                return {
                    'status': 'error',
                    'message': 'Webhook validation failed'
                }
            
            # Log successful validation
            self.security_manager.log_security_event(
                'validation_success',
                {
                    'ip_address': ip_address,
                    'event_type': event.get('type'),
                    'event_id': event.get('id'),
                    'checks_passed': validation_result['checks_passed']
                }
            )
            
            # Process the webhook event
            return {
                'status': 'validated',
                'event': event,
                'metadata': {
                    'ip_address': ip_address,
                    'validated_at': timezone.now().isoformat(),
                    'security_checks': validation_result['checks_passed']
                }
            }
            
        except Exception as e:
            # Log error without exposing details
            logger.error(f"Webhook processing error: {type(e).__name__}")
            
            # Log security event
            self.security_manager.log_security_event(
                'processing_error',
                {
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'error_type': type(e).__name__,
                    'payload_size': len(payload) if payload else 0
                }
            )
            
            # Return generic error
            return {
                'status': 'error',
                'message': 'Webhook processing failed'
            }
    
    def get_client_ip(self, request) -> str:
        """
        Get client IP address from request, handling proxies
        
        Args:
            request: Django request object
            
        Returns:
            Client IP address
        """
        # Check for proxy headers
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the chain
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        return ip