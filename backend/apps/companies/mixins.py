"""
Company-level security mixins for views
"""
from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.response import Response


class CompanyOwnedMixin:
    """
    Mixin to ensure all queries are filtered by the user's company.
    Provides secure company-scoped querysets and validation.
    """
    
    def get_user_company(self):
        """Get the authenticated user's company with validation"""
        if not hasattr(self.request.user, 'company') or not self.request.user.company:
            raise PermissionDenied("User does not have an associated company")
        return self.request.user.company
    
    def get_queryset(self):
        """
        Filter queryset by user's company.
        Expects the model to have a 'company' field.
        """
        queryset = super().get_queryset()
        company = self.get_user_company()
        
        # Apply company filter
        if hasattr(queryset.model, 'company'):
            return queryset.filter(company=company)
        else:
            raise ValueError(f"Model {queryset.model} does not have a company field")
    
    def perform_create(self, serializer):
        """Automatically set company on create"""
        company = self.get_user_company()
        serializer.save(company=company)
    
    def get_object(self):
        """
        Get object with additional company validation.
        Ensures the object belongs to the user's company.
        """
        obj = super().get_object()
        company = self.get_user_company()
        
        # Validate company ownership
        if hasattr(obj, 'company_id'):
            if obj.company_id != company.id:
                raise PermissionDenied("Object does not belong to user's company")
        elif hasattr(obj, 'company'):
            if obj.company.id != company.id:
                raise PermissionDenied("Object does not belong to user's company")
        
        return obj


class CompanyValidationMixin:
    """
    Mixin for API views that need company validation but don't use viewsets
    """
    
    def get_user_company(self, request):
        """Get and validate user's company"""
        if not hasattr(request.user, 'company') or not request.user.company:
            return None, Response(
                {'error': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        return request.user.company, None
    
    def validate_company_ownership(self, obj, company):
        """Validate that an object belongs to the company"""
        if hasattr(obj, 'company_id'):
            return obj.company_id == company.id
        elif hasattr(obj, 'company'):
            return obj.company.id == company.id
        return False
    
    def filter_by_company(self, queryset, company):
        """Filter a queryset by company"""
        if hasattr(queryset.model, 'company'):
            return queryset.filter(company=company)
        return queryset