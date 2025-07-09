"""
Company utilities
"""
from apps.companies.models import CompanyUser


def get_user_company(user):
    """
    Get the active company for a user.
    
    Returns the first active company the user belongs to.
    In a real multi-tenant app, this might use session data
    to determine which company is currently selected.
    """
    if hasattr(user, 'company') and user.company:
        return user.company
    
    try:
        company_user = CompanyUser.objects.filter(
            user=user,
            is_active=True
        ).select_related('company').first()
        
        if company_user:
            return company_user.company
    except Exception:
        pass
    
    return None