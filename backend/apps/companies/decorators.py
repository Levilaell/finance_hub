# backend/apps/companies/decorators.py
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def requires_plan_feature(feature_name):
    """
    Decorator to check plan features and limits before executing view methods
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(self, request, *args, **kwargs):
            # Para ViewSets, self é a instância do ViewSet
            # Para APIViews, seria diferente
            if hasattr(request.user, 'company'):
                company = request.user.company
            else:
                return Response({
                    'error': 'Usuário não está associado a nenhuma empresa'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Verificações específicas por feature
            if feature_name == 'create_transaction':
                limit_reached, usage_info = company.check_plan_limits('transactions')
                if limit_reached:
                    # Determinar plano sugerido
                    suggested_plan = None
                    if company.subscription_plan:
                        if company.subscription_plan.plan_type == 'starter':
                            suggested_plan = 'professional'
                        elif company.subscription_plan.plan_type == 'professional':
                            suggested_plan = 'enterprise'
                    
                    return Response({
                        'error': 'Limite de transações atingido para este mês',
                        'usage_info': usage_info,
                        'current_usage': company.current_month_transactions,
                        'limit': company.subscription_plan.max_transactions if company.subscription_plan else 0,
                        'upgrade_required': True,
                        'current_plan': company.subscription_plan.name if company.subscription_plan else 'Nenhum',
                        'suggested_plan': suggested_plan
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            elif feature_name == 'create_bank_account' or feature_name == 'add_bank_account':
                if not company.can_add_bank_account():
                    current_count = company.bank_accounts.filter(is_active=True).count()
                    limit = company.subscription_plan.max_bank_accounts if company.subscription_plan else 0
                    
                    return Response({
                        'error': f'Limite de contas bancárias atingido ({current_count}/{limit})',
                        'limit_type': 'bank_accounts',
                        'current': current_count,
                        'limit': limit,
                        'upgrade_required': True,
                        'current_plan': company.subscription_plan.name if company.subscription_plan else 'Nenhum',
                        'suggested_plan': 'professional' if company.subscription_plan and company.subscription_plan.plan_type == 'starter' else 'enterprise',
                        'redirect': '/dashboard/subscription/upgrade'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            elif feature_name == 'ai_insights' or feature_name == 'use_ai':
                can_use_ai, message = company.can_use_ai_insight()
                if not can_use_ai:
                    # Incrementar contador mesmo quando bloqueado (para tracking)
                    if company.subscription_plan and company.subscription_plan.max_ai_requests_per_month > 0:
                        usage_info = {
                            'current': company.current_month_ai_requests,
                            'limit': company.subscription_plan.max_ai_requests_per_month,
                            'remaining': max(0, company.subscription_plan.max_ai_requests_per_month - company.current_month_ai_requests)
                        }
                    else:
                        usage_info = None
                    
                    return Response({
                        'error': message,
                        'limit_type': 'ai_requests',
                        'usage_info': usage_info,
                        'upgrade_required': True,
                        'current_plan': company.subscription_plan.name if company.subscription_plan else 'Nenhum',
                        'suggested_plan': 'professional' if company.subscription_plan and company.subscription_plan.plan_type == 'starter' else 'enterprise',
                        'feature_required': 'AI Insights'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            elif feature_name == 'advanced_reports':
                if not company.subscription_plan or not company.subscription_plan.has_advanced_reports:
                    return Response({
                        'error': 'Relatórios avançados não disponíveis no seu plano',
                        'upgrade_required': True,
                        'current_plan': company.subscription_plan.name if company.subscription_plan else 'Nenhum'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            elif feature_name == 'api_access':
                if not company.subscription_plan or not company.subscription_plan.has_api_access:
                    return Response({
                        'error': 'Acesso à API disponível apenas no plano Enterprise',
                        'upgrade_required': True,
                        'current_plan': company.subscription_plan.name if company.subscription_plan else 'Nenhum'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Verificação de notificações de uso
            if feature_name == 'create_transaction':
                self._check_and_send_usage_notifications(company)
            
            # Executar a view original
            return view_func(self, request, *args, **kwargs)
        
        def _check_and_send_usage_notifications(company):
            """Verifica e envia notificações de uso"""
            usage_percentage = company.get_usage_percentage('transactions')
            
            try:
                if usage_percentage >= 90 and not company.notified_90_percent:
                    from apps.notifications.email_service import EmailService
                    EmailService.send_usage_limit_warning(
                        email=company.owner.email,
                        company_name=company.name,
                        limit_type='transações',
                        percentage=90,
                        current=company.current_month_transactions,
                        limit=company.subscription_plan.max_transactions
                    )
                    company.notified_90_percent = True
                    company.save(update_fields=['notified_90_percent'])
                    
                elif usage_percentage >= 80 and not company.notified_80_percent:
                    from apps.notifications.email_service import EmailService
                    EmailService.send_usage_limit_warning(
                        email=company.owner.email,
                        company_name=company.name,
                        limit_type='transações',
                        percentage=80,
                        current=company.current_month_transactions,
                        limit=company.subscription_plan.max_transactions
                    )
                    company.notified_80_percent = True
                    company.save(update_fields=['notified_80_percent'])
            except Exception as e:
                logger.error(f"Erro ao enviar notificação de uso: {e}")
        
        wrapped_view._check_and_send_usage_notifications = _check_and_send_usage_notifications
        return wrapped_view
    
    return decorator