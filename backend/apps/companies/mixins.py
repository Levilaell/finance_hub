"""
Company-related mixins for safe access
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotAuthenticated


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
            # Return None with error data to be handled by view
            return None, {
                "error": {"message": "Authentication required"},
                "status": status.HTTP_401_UNAUTHORIZED
            }
        
        # Try to get company
        try:
            if hasattr(user, 'company') and user.company:
                return user.company, None
        except:
            pass
        
        # If no company, return error data
        return None, {
            "error": {"message": "You must be associated with a company to access this resource. "
                       "Please contact support if you believe this is an error."},
            "status": status.HTTP_403_FORBIDDEN
        }