"""
Security decorators for payment webhooks
"""
import hmac
import hashlib
import json
from functools import wraps
from django.http import HttpResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def verify_stripe_webhook(f):
    """Decorator to verify Stripe webhook signatures"""
    @wraps(f)
    def decorator(request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not sig_header:
            logger.warning("Missing Stripe signature header")
            return HttpResponse(status=400)
        
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            
            # Add event to request for use in view
            request.stripe_event = event
            
        except ValueError:
            logger.error("Invalid Stripe webhook payload")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid Stripe webhook signature")
            return HttpResponse(status=400)
        
        return f(request, *args, **kwargs)
    
    return decorator


def verify_mercadopago_webhook(f):
    """Decorator to verify MercadoPago webhook signatures"""
    @wraps(f)
    def decorator(request, *args, **kwargs):
        # MercadoPago uses query params for validation
        topic = request.GET.get('topic')
        id = request.GET.get('id')
        
        if not topic or not id:
            logger.warning("Missing MercadoPago webhook parameters")
            return HttpResponse(status=400)
        
        # Verify x-signature header if present
        signature = request.META.get('HTTP_X_SIGNATURE')
        if signature and settings.MERCADOPAGO_WEBHOOK_SECRET:
            # Extract ts and v1 from signature
            parts = {}
            for item in signature.split(','):
                key, value = item.split('=')
                parts[key] = value
            
            if 'ts' in parts and 'v1' in parts:
                # Recreate signature
                signed_payload = f"id={id}&topic={topic}&ts={parts['ts']}"
                expected_signature = hmac.new(
                    settings.MERCADOPAGO_WEBHOOK_SECRET.encode(),
                    signed_payload.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(parts['v1'], expected_signature):
                    logger.error("Invalid MercadoPago webhook signature")
                    return HttpResponse(status=401)
        
        # Add webhook data to request
        request.mercadopago_data = {
            'topic': topic,
            'id': id
        }
        
        return f(request, *args, **kwargs)
    
    return decorator


def require_webhook_ip_whitelist(f):
    """Decorator to restrict webhooks to whitelisted IPs"""
    @wraps(f)
    def decorator(request, *args, **kwargs):
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Check if IP is whitelisted
        webhook_whitelist = getattr(settings, 'WEBHOOK_IP_WHITELIST', [])
        if webhook_whitelist and ip not in webhook_whitelist:
            logger.warning(f"Webhook request from non-whitelisted IP: {ip}")
            return HttpResponse(status=403)
        
        return f(request, *args, **kwargs)
    
    return decorator