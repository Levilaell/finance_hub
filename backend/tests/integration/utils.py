"""
Utilities for integration tests
"""
from apps.companies.models import CompanyUser


def setup_user_company(user):
    """
    Setup user company relationship for tests.
    Returns the company if user has one, None otherwise.
    """
    try:
        # Get the first company the user belongs to
        company_user = CompanyUser.objects.filter(user=user, is_active=True).first()
        if company_user:
            # Add company property to user instance for the test
            user.company = company_user.company
            return company_user.company
    except Exception:
        pass
    return None


class CompanyPropertyMixin:
    """
    Mixin to add company property to user for tests
    """
    @property
    def company(self):
        if not hasattr(self, '_company'):
            company_user = CompanyUser.objects.filter(user=self, is_active=True).first()
            self._company = company_user.company if company_user else None
        return self._company