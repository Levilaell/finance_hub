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
        """Check object-level permissions"""
        # Staff has all permissions
        if request.user.is_staff:
            return True
        
        # Check if object has company field
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
        
        # Check if object is the company itself
        if obj.__class__.__name__ == 'Company':
            return obj == request.user.company
        
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
        """Check object-level permissions"""
        # Check if object has company field
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
        
        # Check if object is the company itself
        if obj.__class__.__name__ == 'Company':
            return obj == request.user.company
        
        return False