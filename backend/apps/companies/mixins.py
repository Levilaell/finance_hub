"""
Company-related mixins for safe access
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied


class CompanyValidationMixin:
    """
    Mixin to safely access user's company and handle cases where user has no company
    """
    
    def get_user_company(self, request):
        """
        Get the current user's company safely
        Returns tuple: (company, error_response)
        """
        user = request.user
        
        if not user.is_authenticated:
            return None, Response(
                {"error": {"message": "Authentication required"}},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Try to get company
        try:
            if hasattr(user, 'company') and user.company:
                return user.company, None
        except:
            pass
        
        # If no company, return error response
        return None, Response(
            {"error": {"message": "You must be associated with a company to access this resource. "
                       "Please contact support if you believe this is an error."}},
            status=status.HTTP_403_FORBIDDEN
        )
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to check company access early
        """
        if request.user.is_authenticated and request.method != 'OPTIONS':
            # Check if user has company access
            company, error_response = self.get_user_company(request)
            if error_response:
                return error_response
        
        return super().dispatch(request, *args, **kwargs)


# Alias for backward compatibility
CompanyAccessMixin = CompanyValidationMixin