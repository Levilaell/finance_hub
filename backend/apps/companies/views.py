"""
Simplified Companies views - Essential functionality only
"""
import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Company, SubscriptionPlan, ResourceUsage
from .serializers import (
    SubscriptionPlanSerializer,
    CompanySerializer,
    UsageLimitsSerializer,
    SubscriptionStatusSerializer
)
from .mixins import CompanyValidationMixin

logger = logging.getLogger(__name__)


class PublicSubscriptionPlansView(APIView):
    """List subscription plans (public)"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('display_order')
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)


class SubscriptionPlansView(APIView):
    """List subscription plans (authenticated)"""
    permission_classes = [IsAuthenticated]
    
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
        
        # Get or create current month usage
        now = timezone.now()
        month_start = now.replace(day=1).date()
        
        usage, _ = ResourceUsage.objects.get_or_create(
            company=company,
            month=month_start,
            defaults={
                'transactions_count': company.current_month_transactions,
                'ai_requests_count': company.current_month_ai_requests
            }
        )
        
        # Build response
        plan = company.subscription_plan
        if not plan:
            # Default limits for trial/no plan
            limits = {
                'transactions': {
                    'used': usage.transactions_count,
                    'limit': 100,
                    'percentage': min(100, (usage.transactions_count / 100) * 100)
                },
                'bank_accounts': {
                    'used': bank_accounts_count,
                    'limit': 2,
                    'percentage': min(100, (bank_accounts_count / 2) * 100)
                },
                'ai_requests': {
                    'used': usage.ai_requests_count,
                    'limit': 10,
                    'percentage': min(100, (usage.ai_requests_count / 10) * 100)
                }
            }
        else:
            limits = {
                'transactions': {
                    'used': usage.transactions_count,
                    'limit': plan.max_transactions,
                    'percentage': min(100, (usage.transactions_count / plan.max_transactions) * 100) if plan.max_transactions > 0 else 0
                },
                'bank_accounts': {
                    'used': bank_accounts_count,
                    'limit': plan.max_bank_accounts,
                    'percentage': min(100, (bank_accounts_count / plan.max_bank_accounts) * 100) if plan.max_bank_accounts > 0 else 0
                },
                'ai_requests': {
                    'used': usage.ai_requests_count,
                    'limit': plan.max_ai_requests_per_month,
                    'percentage': min(100, (usage.ai_requests_count / plan.max_ai_requests_per_month) * 100) if plan.max_ai_requests_per_month > 0 else 0
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