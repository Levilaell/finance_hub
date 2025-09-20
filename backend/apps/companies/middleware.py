"""
Middleware para verificar status de trial e assinatura
"""
from django.utils import timezone
from django.http import JsonResponse
from django.core.cache import cache
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class TrialExpirationMiddleware:
    """
    Middleware que verifica se o trial expirou e bloqueia acesso se necessário
    """
    # URLs que são sempre permitidas (sem verificação de trial)
    ALLOWED_PATHS = [
        '/api/auth/login/',
        '/api/auth/logout/',
        '/api/auth/register/',
        '/api/auth/password-reset/',
        '/api/companies/public/plans/',
        '/api/companies/subscription/',
        '/api/companies/billing/',
        '/api/payments/',
        '/api/health/',
        '/admin/',
        '/static/',
        '/media/',
    ]
    
    # Paths permitidas mesmo com trial expirado
    ALLOWED_EXPIRED_PATHS = [
        '/api/companies/subscription/',
        '/api/companies/billing/',
        '/api/payments/',
        '/api/auth/profile/',
        '/api/auth/logout/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if path should be excluded from trial check
        path = request.path_info
        
        # Skip check for allowed paths
        for allowed_path in self.ALLOWED_PATHS:
            if path.startswith(allowed_path):
                return self.get_response(request)
        
        # Skip for unauthenticated requests
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return self.get_response(request)
        
        # Skip for admin users
        if request.user.is_staff or request.user.is_superuser:
            return self.get_response(request)
        
        # Check if user has a company
        try:
            company = request.user.company
        except:
            # No company found, allow request (multi-user support removed)
            return self.get_response(request)
        
        # Check trial expiration (don't update status here, let Celery task handle it)
        if company.subscription_status == 'trial' and company.trial_ends_at:
            current_time = timezone.now()
            
            if current_time > company.trial_ends_at:
                # Trial expired but not yet updated by task
                logger.debug(f"Trial expired for company {company.id} but status not yet updated")
                
                # Check if path is allowed for expired trials
                path_allowed_when_expired = any(
                    path.startswith(p) for p in self.ALLOWED_EXPIRED_PATHS
                )
                
                # Return error response for API requests
                if path.startswith('/api/') and not path_allowed_when_expired:
                    return JsonResponse({
                        'error': 'trial_expired',
                        'message': 'Seu período de teste expirou. Configure um método de pagamento para continuar.',
                        'trial_expired': True,
                        'redirect': '/dashboard/subscription/upgrade'
                    }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # Check if subscription is expired, suspended, or cancelled
        if company.subscription_status in ['expired', 'suspended', 'cancelled']:
            # Check if path is allowed for expired subscriptions
            path_allowed_when_expired = any(
                path.startswith(p) for p in self.ALLOWED_EXPIRED_PATHS
            )
            
            # Block access to most features
            if path.startswith('/api/') and not path_allowed_when_expired:
                messages = {
                    'expired': 'Sua assinatura expirou. Renove para continuar.',
                    'suspended': 'Sua assinatura está suspensa. Entre em contato com o suporte.',
                    'cancelled': 'Sua assinatura foi cancelada. Reative para continuar usando o sistema.'
                }
                
                return JsonResponse({
                    'error': 'subscription_inactive',
                    'message': messages.get(company.subscription_status, 'Sua assinatura está inativa. Por favor, regularize para continuar.'),
                    'subscription_status': company.subscription_status,
                    'redirect': '/dashboard/subscription-blocked'
                }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # Check usage limits for active subscriptions
        if company.subscription_status in ['trial', 'active'] and company.subscription_plan:
            # Transaction limits removed in simplified model
            # Transactions are now tracked for statistics only
            
            # AI request limits removed in simplified model
            # Only rate limiting remains for API protection
            if ('ai' in path.lower() or 'insight' in path.lower() or 'categorize' in path.lower()) and request.method == 'POST':
                # Rate limiting check for API protection
                rate_limit_key = f"rate_limit:{request.user.id}:ai_request"
                rate_limit_count = cache.get(rate_limit_key, 0)

                # Allow max 10 AI requests per minute
                if rate_limit_count >= 10:
                    return JsonResponse({
                        'error': 'rate_limit_exceeded',
                        'message': 'Muitas requisições. Por favor, aguarde um momento.',
                        'retry_after': 60
                    }, status=429)

                # Increment rate limit counter
                cache.set(rate_limit_key, rate_limit_count + 1, 60)
        
        response = self.get_response(request)
        return response

