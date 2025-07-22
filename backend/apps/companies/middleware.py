"""
Middleware para verificar status de trial e assinatura
"""
from django.utils import timezone
from django.http import JsonResponse
from django.urls import resolve
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
            # User might be a team member, try to get company through CompanyUser
            try:
                from apps.companies.models import CompanyUser
                company_user = CompanyUser.objects.get(user=request.user, is_active=True)
                company = company_user.company
            except:
                # No company found, allow request
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
        
        # Check if subscription is expired or suspended
        if company.subscription_status in ['expired', 'suspended']:
            # Check if path is allowed for expired subscriptions
            path_allowed_when_expired = any(
                path.startswith(p) for p in self.ALLOWED_EXPIRED_PATHS
            )
            
            # Block access to most features
            if path.startswith('/api/') and not path_allowed_when_expired:
                return JsonResponse({
                    'error': 'subscription_inactive',
                    'message': 'Sua assinatura está inativa. Por favor, regularize para continuar.',
                    'subscription_status': company.subscription_status,
                    'redirect': '/dashboard/subscription'
                }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # Check usage limits for active subscriptions
        if company.subscription_status in ['trial', 'active'] and company.subscription_plan:
            # Check transaction limit
            if path.startswith('/api/transactions/') and request.method == 'POST':
                if company.current_month_transactions >= company.subscription_plan.max_transactions:
                    return JsonResponse({
                        'error': 'limit_reached',
                        'message': f'Você atingiu o limite de {company.subscription_plan.max_transactions} transações mensais. Faça upgrade do plano para continuar.',
                        'limit_type': 'transactions',
                        'current': company.current_month_transactions,
                        'limit': company.subscription_plan.max_transactions,
                        'redirect': '/dashboard/subscription/upgrade'
                    }, status=status.HTTP_402_PAYMENT_REQUIRED)
            
            # Check AI request limit
            if ('ai' in path.lower() or 'insight' in path.lower() or 'categorize' in path.lower()) and request.method == 'POST':
                # Rate limiting check first
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
                
                # Check monthly limit
                if company.subscription_plan.max_ai_requests_per_month > 0:
                    if company.current_month_ai_requests >= company.subscription_plan.max_ai_requests_per_month:
                        return JsonResponse({
                            'error': 'limit_reached',
                            'message': f'Você atingiu o limite de {company.subscription_plan.max_ai_requests_per_month} requisições de IA mensais.',
                            'limit_type': 'ai_requests',
                            'current': company.current_month_ai_requests,
                            'limit': company.subscription_plan.max_ai_requests_per_month,
                            'redirect': '/dashboard/subscription/upgrade'
                        }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        response = self.get_response(request)
        return response


class PlanLimitsMiddleware:
    """
    Middleware para adicionar informações de limites do plano ao request
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'company'):
            company = request.user.company
            
            # Reset monthly usage if needed
            if self._should_reset_monthly_usage(company):
                company.reset_monthly_usage()
                logger.info(f"Reset monthly usage for company {company.id} - {company.name}")
            
            # Add plan limits to request
            request.plan_limits = {
                'subscription_status': company.subscription_status,
                'plan_type': company.subscription_plan.plan_type if company.subscription_plan else None,
                'can_use_ai': company.subscription_plan.enable_ai_insights if company.subscription_plan else False,
                'remaining_transactions': company.get_remaining_transactions() if hasattr(company, 'get_remaining_transactions') else 0,
                'can_add_bank_account': company.can_add_bank_account(),
                'can_generate_reports': company.subscription_plan.has_advanced_reports if company.subscription_plan else False,
                'usage_summary': company.get_usage_summary(),
            }
            
            # Add trial info if applicable
            if company.subscription_status == 'trial':
                request.plan_limits['trial_days_left'] = company.days_until_trial_ends
                request.plan_limits['trial_ends_at'] = company.trial_ends_at
        
        response = self.get_response(request)
        return response
    
    def _should_reset_monthly_usage(self, company):
        """Check if monthly usage should be reset"""
        if not company.last_usage_reset:
            return True
        
        now = timezone.now()
        last_reset = company.last_usage_reset
        
        # Reset on the first day of each month
        return (now.month != last_reset.month or now.year != last_reset.year)