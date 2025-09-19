"""
Company permissions
"""
from rest_framework import permissions


class CompanyOwnerPermission(permissions.BasePermission):
    """
    Unified permission to check if user owns the company, with optional staff access
    """

    def __init__(self, allow_staff=False):
        """
        Initialize permission

        Args:
            allow_staff (bool): If True, staff users are always allowed
        """
        self.allow_staff = allow_staff
        super().__init__()

    def has_permission(self, request, view):
        """Check if user has a company"""
        if not request.user.is_authenticated:
            return False

        # Staff access if enabled
        if self.allow_staff and request.user.is_staff:
            return True

        # Check if user has a company
        return hasattr(request.user, 'company')

    def has_object_permission(self, request, view, obj):
        """Check object-level permissions with strict validation"""
        # Staff has all permissions if enabled
        if self.allow_staff and request.user.is_staff:
            return True

        # Ensure user has a company
        if not hasattr(request.user, 'company') or not request.user.company:
            return False

        user_company = request.user.company

        # Direct company object check
        if obj.__class__.__name__ == 'Company':
            return obj.id == user_company.id

        # Check if object has company field (most common case)
        if hasattr(obj, 'company_id'):
            return obj.company_id == user_company.id
        elif hasattr(obj, 'company'):
            return obj.company.id == user_company.id

        # Check for nested relationships (e.g., transaction.bank_account.company)
        if hasattr(obj, 'bank_account') and hasattr(obj.bank_account, 'company_id'):
            return obj.bank_account.company_id == user_company.id

        # Default deny for safety
        return False


# Factory functions for convenience
def IsCompanyOwner():
    """Company owner only (no staff access)"""
    return CompanyOwnerPermission(allow_staff=False)


def IsCompanyOwnerOrStaff():
    """Company owner or staff"""
    return CompanyOwnerPermission(allow_staff=True)