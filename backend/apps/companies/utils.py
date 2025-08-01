"""
Company utilities - Simplified version
"""


def get_user_company(user):
    """
    Get the company for a user.
    
    In the simplified version, each user has only one company.
    """
    if hasattr(user, 'company') and user.company:
        return user.company
    
    return None