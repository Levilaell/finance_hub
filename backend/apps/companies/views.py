"""
Companies views
"""
import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, PermissionDenied

from .serializers import (
    CompanySerializer,

)

logger = logging.getLogger(__name__)


class CompanyDetailView(APIView):
    """Company detail operations"""
    permission_classes = [IsAuthenticated]
    
    def get_company(self):
        """Get current user's company or raise appropriate exception"""
        if not hasattr(self.request.user, 'company'):
            raise NotFound(
                detail="Empresa não encontrada. Entre em contato com o suporte.",
                code='company_not_found'
            )
        return self.request.user.company
    
    def get(self, request):
        """Get company details"""
        company = self.get_company()
        serializer = CompanySerializer(company)
        return Response(serializer.data)

