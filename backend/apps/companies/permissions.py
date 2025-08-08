"""
Company permissions
"""
from rest_framework import permissions


class IsCompanyOwnerOrStaff(permissions.BasePermission):
    """
    Permission to check if user owns the company or is staff
    """
    
    def has_permission(self, request, view):
        """Check if user has a company"""
        if not request.user.is_authenticated:
            return False
        
        # Staff always has permission
        if request.user.is_staff:
            return True
        
        # Check if user has a company
        return hasattr(request.user, 'company')
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permissions with strict validation"""
        # Staff has all permissions
        if request.user.is_staff:
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


class IsCompanyOwner(permissions.BasePermission):
    """
    Permission to check if user owns the company
    """
    
    def has_permission(self, request, view):
        """Check if user has a company"""
        if not request.user.is_authenticated:
            return False
        
        return hasattr(request.user, 'company')
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permissions with strict validation"""
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