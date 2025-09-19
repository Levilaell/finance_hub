# backend/apps/companies/decorators.py
from functools import wraps
from rest_framework.response import Response
from rest_framework import status

def requires_plan_feature(feature_name):
    """
    Simplified decorator to check plan features
    Most limit checking has been removed from the models
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

            # Verificações simplificadas por feature
            if feature_name == 'create_transaction':
                # Transactions are now unlimited in the simplified model
                # Just check if company has a plan
                if not company.subscription_plan:
                    return Response({
                        'error': 'Plano de assinatura necessário',
                        'upgrade_required': True,
                        'current_plan': 'Nenhum'
                    }, status=status.HTTP_403_FORBIDDEN)

            elif feature_name == 'create_bank_account' or feature_name == 'add_bank_account':
                # Check simplified bank account limit
                if company.subscription_plan:
                    current_count = company.bank_accounts.filter(is_active=True).count()
                    limit = company.subscription_plan.max_bank_accounts

                    if current_count >= limit:
                        return Response({
                            'error': f'Limite de contas bancárias atingido ({current_count}/{limit})',
                            'limit_type': 'bank_accounts',
                            'current': current_count,
                            'limit': limit,
                            'upgrade_required': True,
                            'current_plan': company.subscription_plan.name if company.subscription_plan else 'Nenhum',
                            'suggested_plan': 'professional' if company.subscription_plan.plan_type == 'starter' else 'enterprise',
                            'redirect': '/dashboard/subscription/upgrade'
                        }, status=status.HTTP_403_FORBIDDEN)
                else:
                    return Response({
                        'error': 'Plano de assinatura necessário',
                        'upgrade_required': True
                    }, status=status.HTTP_403_FORBIDDEN)

            # AI insights and advanced reports features have been removed
            # API access checks have been removed

            # Executar a view original
            return view_func(self, request, *args, **kwargs)

        return wrapped_view

    return decorator