"""
Middleware para verificar status de trial e assinatura
"""
from django.utils import timezone
from django.http import JsonResponse
from django.urls import resolve
from rest_framework import status


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
        '/api/companies/subscription/upgrade/',
        '/api/companies/billing/',
        '/api/payments/webhooks/',
        '/api/health/',
        '/admin/',
        '/static/',
        '/media/',
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
        
        # Check trial expiration
        if company.subscription_status == 'trial' and company.trial_ends_at:
            if timezone.now() > company.trial_ends_at:
                # Trial expired - update status
                company.subscription_status = 'expired'
                company.save()
                
                # Return error response for API requests
                if path.startswith('/api/'):
                    return JsonResponse({
                        'error': 'Período de teste expirado',
                        'message': 'Seu período de teste expirou. Por favor, escolha um plano para continuar.',
                        'redirect': '/dashboard/subscription/upgrade'
                    }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # Check if subscription is expired or suspended
        if company.subscription_status in ['expired', 'suspended']:
            # Block access to most features
            if path.startswith('/api/') and not any(path.startswith(p) for p in [
                '/api/companies/profile/',
                '/api/companies/subscription/',
                '/api/companies/billing/',
            ]):
                return JsonResponse({
                    'error': 'Assinatura inativa',
                    'message': 'Sua assinatura está inativa. Por favor, regularize para continuar.',
                    'redirect': '/dashboard/subscription'
                }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # Check usage limits
        if company.subscription_plan:
            # Check transaction limit
            if path.startswith('/api/transactions/') and request.method == 'POST':
                if company.current_month_transactions >= company.subscription_plan.max_transactions:
                    return JsonResponse({
                        'error': 'Limite de transações atingido',
                        'message': f'Você atingiu o limite de {company.subscription_plan.max_transactions} transações mensais. Faça upgrade do plano para continuar.',
                        'redirect': '/dashboard/subscription/upgrade'
                    }, status=status.HTTP_402_PAYMENT_REQUIRED)
            
            # Check AI request limit
            if 'ai' in path.lower() or 'categorize' in path.lower():
                if company.current_month_ai_requests >= company.subscription_plan.max_ai_requests_per_month:
                    return JsonResponse({
                        'error': 'Limite de requisições IA atingido',
                        'message': f'Você atingiu o limite de {company.subscription_plan.max_ai_requests_per_month} requisições de IA mensais.',
                        'redirect': '/dashboard/subscription/upgrade'
                    }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        response = self.get_response(request)
        return response
    
class PlanLimitsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'company'):
            company = request.user.company
            
            # Adicionar informações do plano ao request
            request.plan_limits = {
                'can_use_ai': company.subscription_plan.has_ai_categorization if company.subscription_plan else False,
                'remaining_transactions': company.get_remaining_transactions(),
                'can_add_bank_account': company.can_add_bank_account(),
                'can_generate_reports': company.subscription_plan.has_advanced_reports if company.subscription_plan else False,
            }
        
        response = self.get_response(request)
        return response
    
class EnforcePlanLimitsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'company'):
            company = request.user.company
            
            # Resetar contadores mensais se necessário
            if company.should_reset_monthly_usage():
                company.reset_monthly_usage()
            
            # Adicionar limites ao request
            request.plan_limits = {
                'can_create_transaction': not company.check_plan_limits('transactions')[0],
                'can_add_bank_account': company.can_add_bank_account(),
                'can_use_ai': company.can_use_ai_insight()[0],
                'remaining_ai_requests': (
                    company.subscription_plan.max_ai_requests_per_month - company.current_month_ai_requests
                    if company.subscription_plan and company.subscription_plan.plan_type == 'professional'
                    else None
                ),
            }
        
        response = self.get_response(request)
        return response