"""
Simplified Companies views - Essential functionality only
"""
import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SubscriptionPlan
from .serializers import (
    SubscriptionPlanSerializer,
    CompanySerializer,
    UsageLimitsSerializer,
    SubscriptionStatusSerializer
)
from .mixins import CompanyValidationMixin

logger = logging.getLogger(__name__)


class SubscriptionPlansView(APIView):
    """List subscription plans - works for both public and authenticated users"""
    permission_classes = [AllowAny]  # Allow both public and authenticated users

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('display_order')
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)


class CompanyDetailView(CompanyValidationMixin, APIView):
    """Get company details"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        company, error_response = self.get_user_company(request)
        if error_response:
            return Response(error_response['error'], status=error_response['status'])
        
        serializer = CompanySerializer(company)
        return Response(serializer.data)


class UsageLimitsView(CompanyValidationMixin, APIView):
    """Get current usage and limits"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        company, error_response = self.get_user_company(request)
        if error_response:
            return Response(error_response['error'], status=error_response['status'])
        
        # Get current usage
        from apps.banking.models import BankAccount
        bank_accounts_count = BankAccount.objects.filter(
            company=company,
            is_active=True
        ).count()

        # Get plan limits (simplified - no external ResourceUsage tracking)
        plan = company.subscription_plan
        if not plan:
            # Default limits for trial/no plan
            limits = {
                'transactions': {
                    'used': company.current_month_transactions,
                    'limit': 100,  # Trial limit
                    'percentage': min(100, (company.current_month_transactions / 100) * 100)
                },
                'bank_accounts': {
                    'used': bank_accounts_count,
                    'limit': 2,  # Trial limit
                    'percentage': min(100, (bank_accounts_count / 2) * 100)
                }
            }
        else:
            limits = {
                'transactions': {
                    'used': company.current_month_transactions,
                    'limit': 1000,  # Default paid plan limit
                    'percentage': min(100, (company.current_month_transactions / 1000) * 100)
                },
                'bank_accounts': {
                    'used': bank_accounts_count,
                    'limit': plan.max_bank_accounts,
                    'percentage': min(100, (bank_accounts_count / plan.max_bank_accounts) * 100) if plan.max_bank_accounts > 0 else 0
                }
            }

        return Response(limits)


class SubscriptionStatusView(CompanyValidationMixin, APIView):
    """Get subscription status"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        company, error_response = self.get_user_company(request)
        if error_response:
            return Response(error_response['error'], status=error_response['status'])
        
        # Check payment method (simplified - just check if subscription_id exists)
        has_payment_method = bool(company.subscription_id)
        
        # Check if payment setup required
        requires_payment_setup = (
            company.subscription_status in ['trial', 'expired'] and
            not has_payment_method
        )
        
        data = {
            'subscription_status': company.subscription_status,
            'plan': SubscriptionPlanSerializer(company.subscription_plan).data if company.subscription_plan else None,
            'trial_days_left': company.days_until_trial_ends,
            'trial_ends_at': company.trial_ends_at,
            'requires_payment_setup': requires_payment_setup,
            'has_payment_method': has_payment_method
        }
        
        return Response(data)