"""
Custom pagination classes for the API.
"""
from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination that allows clients to control page size.

    Usage:
    - Default page size: 20
    - Max page size: 1000 (to prevent abuse)
    - Client can override via 'page_size' query parameter

    Examples:
    - /api/transactions/ - Returns 20 items (default)
    - /api/transactions/?page_size=100 - Returns 100 items
    - /api/transactions/?page_size=1000 - Returns 1000 items (max)
    """
    page_size = 20
    page_size_query_param = 'page_size'  # Allow client to override page size
    max_page_size = 1000  # Maximum allowed page size
