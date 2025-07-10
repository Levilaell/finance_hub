"""
Public views for subscription plans (no authentication required)
"""
from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.companies.models import SubscriptionPlan
from apps.companies.serializers import SubscriptionPlanSerializer


class PublicSubscriptionPlansView(generics.ListAPIView):
    """
    List all active subscription plans (public endpoint)
    """
    permission_classes = [AllowAny]
    serializer_class = SubscriptionPlanSerializer
    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by('price_monthly')
    
    def get_queryset(self):
        """Get active subscription plans ordered by price"""
        return super().get_queryset()