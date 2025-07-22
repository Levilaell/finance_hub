"""
Companies app views
"""
import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

from .models import Company, CompanyUser, SubscriptionPlan, PaymentMethod, PaymentHistory, ResourceUsage
from .serializers import (
    SubscriptionPlanSerializer,
    UpgradeSubscriptionSerializer,
    PaymentMethodSerializer,
    PaymentHistorySerializer,
)

User = get_user_model()


# Views removed - not used by frontend
# CompanyDetailView, CompanyUpdateView


class SubscriptionPlansView(generics.ListAPIView):
    """List available subscription plans"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscriptionPlanSerializer
    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by('price_monthly')
    pagination_class = None  # Disable pagination for subscription plans


class UpgradeSubscriptionView(APIView):
    """Upgrade/Downgrade company subscription"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = UpgradeSubscriptionSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Get the user's company - either as owner or team member
        user = request.user
        company = None
        
        # Check if user is a company owner
        if hasattr(user, 'company'):
            try:
                company = user.company
            except Company.DoesNotExist:
                pass
        
        # If not owner, check if user is a team member
        if not company:
            try:
                company_user = CompanyUser.objects.get(user=user, is_active=True)
                company = company_user.company
            except CompanyUser.DoesNotExist:
                pass
        
        if not company:
            return Response({
                'error': 'User is not associated with any company'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        new_plan = SubscriptionPlan.objects.get(
            id=serializer.validated_data['plan_id']
        )
        billing_cycle = serializer.validated_data.get('billing_cycle', company.billing_cycle or 'monthly')
        
        # Check if it's actually a change
        if company.subscription_plan and company.subscription_plan.id == new_plan.id and company.billing_cycle == billing_cycle:
            return Response({
                'error': 'Already on this plan with same billing cycle'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user has active subscription
        if company.subscription_status not in ['active', 'trialing']:
            return Response({
                'error': 'No active subscription to update. Please create a new subscription.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from apps.payments.payment_service import PaymentService
        payment_service = PaymentService()
        
        # Calculate proration
        proration = payment_service.calculate_proration(
            company, new_plan, billing_cycle
        )
        
        logger.info(f"Upgrade/Downgrade - Company: {company.id}, Current: {company.subscription_plan.name}, New: {new_plan.name}")
        logger.info(f"Proration: {proration}")
        
        try:
            if company.subscription_id:
                # Existing subscription - update with payment provider
                result = payment_service.update_subscription(
                    company, new_plan, billing_cycle
                )
                
                # Log the change
                from ..companies.models import PaymentHistory
                PaymentHistory.objects.create(
                    company=company,
                    subscription_plan=new_plan,
                    transaction_type='plan_change',
                    amount=abs(proration['net_amount']),
                    currency='BRL',
                    status='pending' if proration['net_amount'] > 0 else 'completed',
                    description=f"{'Upgrade' if proration['net_amount'] > 0 else 'Downgrade'} de {proration['current_plan']} para {proration['new_plan']}",
                    transaction_date=timezone.now()
                )
                
                return Response({
                    'message': f"Subscription {'upgraded' if proration['net_amount'] > 0 else 'downgraded'} successfully",
                    'new_plan': SubscriptionPlanSerializer(new_plan).data,
                    'proration': proration,
                    'payment_required': proration['net_amount'] > 0,
                    'credit_applied': proration['net_amount'] < 0,
                    'amount': abs(proration['net_amount'])
                })
            else:
                # No subscription ID but active status - need to create checkout
                # This can happen for manual activations or legacy data
                return Response({
                    'error': 'Subscription ID not found. Please contact support or create a new subscription.',
                    'redirect': '/settings'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Upgrade/Downgrade error: {e}", exc_info=True)
            return Response({
                'error': 'Failed to update subscription. Please try again.',
                'detail': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelSubscriptionView(APIView):
    """Cancel company subscription"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Get the user's company - either as owner or team member
        user = request.user
        company = None
        
        # Check if user is a company owner
        if hasattr(user, 'company'):
            try:
                company = user.company
            except Company.DoesNotExist:
                pass
        
        # If not owner, check if user is a team member
        if not company:
            try:
                company_user = CompanyUser.objects.get(user=user, is_active=True)
                company = company_user.company
            except CompanyUser.DoesNotExist:
                pass
        
        if not company:
            return Response({
                'error': 'User is not associated with any company'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if company.subscription_status != 'active':
            return Response({
                'error': 'No active subscription to cancel'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not company.subscription_id:
            return Response({
                'error': 'No subscription ID found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle cancellation with payment provider
        from apps.payments.payment_service import PaymentService
        
        try:
            payment_service = PaymentService()
            
            # Cancel at end of billing period by default
            immediately = request.data.get('immediately', False)
            result = payment_service.cancel_subscription(company.subscription_id, immediately)
            
            if result['success']:
                # Update local status
                if immediately:
                    company.subscription_status = 'cancelled'
                    company.subscription_end_date = timezone.now()
                else:
                    company.subscription_status = 'cancelling'
                    # Will be cancelled at period end
                company.save()
                
                logger.info(f"Subscription cancelled for company {company.id}")
                
                return Response({
                    'message': 'Subscription cancelled successfully',
                    'cancel_at_period_end': not immediately,
                    'end_date': result.get('current_period_end')
                })
            else:
                return Response({
                    'error': 'Failed to cancel subscription',
                    'detail': result.get('error')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            return Response({
                'error': 'Failed to cancel subscription'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            payment_service = PaymentService()
            success = payment_service.cancel_subscription(company)
            
            if not success:
                return Response({
                    'error': 'Failed to cancel subscription with payment provider'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Payment cancellation error: {e}")
            return Response({
                'error': 'Payment cancellation failed. Please contact support.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': 'Subscription cancelled successfully'
        })


# View removed - not used by frontend
# CompanyUsersView


# Views removed - not used by frontend
# InviteUserView, RemoveUserView


class PaymentMethodsView(APIView):
    """Manage payment methods"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_company(self):
        """Get user's company"""
        user = self.request.user
        try:
            if hasattr(user, 'company'):
                return user.company
            company_user = CompanyUser.objects.get(user=user, is_active=True)
            return company_user.company
        except (Company.DoesNotExist, CompanyUser.DoesNotExist):
            return None
    
    def get(self, request):
        """List payment methods"""
        from .serializers import PaymentMethodSerializer
        
        company = self.get_company()
        if not company:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        
        payment_methods = PaymentMethod.objects.filter(
            company=company, 
            is_active=True
        ).order_by('-is_default', '-created_at')
        
        serializer = PaymentMethodSerializer(payment_methods, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Add new payment method"""
        from .serializers import AddPaymentMethodSerializer
        from apps.payments.payment_service import PaymentService
        
        company = self.get_company()
        if not company:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = AddPaymentMethodSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            # Process with payment service
            payment_service = PaymentService()
            
            if data['payment_type'] in ['credit_card', 'debit_card']:
                # Create payment method with Stripe/MercadoPago
                payment_method_result = payment_service.create_payment_method(
                    company=company,
                    card_data={
                        'number': data['card_number'],
                        'exp_month': data['exp_month'],
                        'exp_year': data['exp_year'],
                        'cvc': data['cvc'],
                        'name': data['cardholder_name']
                    }
                )
                
                # Save to database
                payment_method = PaymentMethod.objects.create(
                    company=company,
                    payment_type=data['payment_type'],
                    card_brand=payment_method_result.get('brand', '').lower(),
                    last_four=payment_method_result.get('last4', ''),
                    exp_month=data['exp_month'],
                    exp_year=data['exp_year'],
                    cardholder_name=data['cardholder_name'],
                    stripe_payment_method_id=payment_method_result.get('stripe_id', ''),
                    mercadopago_card_id=payment_method_result.get('mercadopago_id', ''),
                    is_default=not PaymentMethod.objects.filter(company=company, is_default=True).exists()
                )
            else:
                # PIX or other methods
                payment_method = PaymentMethod.objects.create(
                    company=company,
                    payment_type=data['payment_type'],
                    is_default=not PaymentMethod.objects.filter(company=company, is_default=True).exists()
                )
            
            from .serializers import PaymentMethodSerializer
            return Response(
                PaymentMethodSerializer(payment_method).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error adding payment method: {e}")
            return Response({
                'error': 'Failed to add payment method'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentMethodDetailView(APIView):
    """Manage individual payment method"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_company(self):
        """Get user's company"""
        user = self.request.user
        try:
            if hasattr(user, 'company'):
                return user.company
            company_user = CompanyUser.objects.get(user=user, is_active=True)
            return company_user.company
        except (Company.DoesNotExist, CompanyUser.DoesNotExist):
            return None
    
    def post(self, request, payment_method_id):
        """Set as default payment method"""
        company = self.get_company()
        if not company:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            payment_method = PaymentMethod.objects.get(
                id=payment_method_id,
                company=company,
                is_active=True
            )
        except PaymentMethod.DoesNotExist:
            return Response({'error': 'Payment method not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Set as default
        PaymentMethod.objects.filter(company=company).update(is_default=False)
        payment_method.is_default = True
        payment_method.save()
        
        return Response({'message': 'Default payment method updated'})
    
    def delete(self, request, payment_method_id):
        """Delete payment method"""
        company = self.get_company()
        if not company:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            payment_method = PaymentMethod.objects.get(
                id=payment_method_id,
                company=company,
                is_active=True
            )
        except PaymentMethod.DoesNotExist:
            return Response({'error': 'Payment method not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if payment_method.is_default:
            return Response({
                'error': 'Cannot delete default payment method'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payment_method.is_active = False
        payment_method.save()
        
        return Response({'message': 'Payment method deleted'})


class PaymentHistoryView(generics.ListAPIView):
    """List payment history"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentHistorySerializer
    
    def get_queryset(self):
        user = self.request.user
        try:
            if hasattr(user, 'company'):
                company = user.company
            else:
                company_user = CompanyUser.objects.get(user=user, is_active=True)
                company = company_user.company
        except (Company.DoesNotExist, CompanyUser.DoesNotExist):
            return PaymentHistory.objects.none()
        
        return PaymentHistory.objects.filter(
            company=company
        ).select_related('payment_method', 'subscription_plan')
    
    def get(self, request, *args, **kwargs):
        """Get payment history with optional filters"""
        queryset = self.get_queryset()
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(description__icontains=search) |
                models.Q(subscription_plan__name__icontains=search)
            )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class InvoiceDownloadView(APIView):
    """Download invoice PDF"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, payment_id):
        user = self.request.user
        try:
            if hasattr(user, 'company'):
                company = user.company
            else:
                company_user = CompanyUser.objects.get(user=user, is_active=True)
                company = company_user.company
        except (Company.DoesNotExist, CompanyUser.DoesNotExist):
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            payment = PaymentHistory.objects.get(
                id=payment_id,
                company=company,
                status='paid'
            )
        except PaymentHistory.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if payment.invoice_url:
            return Response({'download_url': payment.invoice_url})
        else:
            return Response({
                'error': 'Invoice not available for download'
            }, status=status.HTTP_404_NOT_FOUND)


class UsageLimitsView(APIView):
    """Get current usage limits for the company"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            company = request.user.company
        except Exception as e:
            logger.error(f"Error getting company for user {request.user.id}: {str(e)}")
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Get current usage counts
            from apps.banking.models import BankAccount
            
            # Get or create current month usage record
            usage_record = ResourceUsage.get_or_create_current_month(company)
            
            # Get transaction count from usage record
            transaction_count = usage_record.transactions_count
            
            # Get bank account count (real-time)
            bank_account_count = BankAccount.objects.filter(company=company, is_active=True).count()
            
            # Get AI requests count from usage record
            ai_requests_count = usage_record.total_ai_usage
            
        except Exception as e:
            logger.error(f"Error getting usage counts: {str(e)}")
            # Return default values if there's an error
            transaction_count = 0
            bank_account_count = 0
            ai_requests_count = 0
        
        try:
            # Get limits from subscription plan
            plan = company.subscription_plan
            if not plan:
                # Default limits for free/trial
                limits = {
                    'transactions': {'limit': 100, 'used': transaction_count},
                    'bank_accounts': {'limit': 2, 'used': bank_account_count},
                    'ai_requests': {'limit': 10, 'used': ai_requests_count}
                }
            else:
                limits = {
                    'transactions': {
                        'limit': plan.max_transactions,
                        'used': transaction_count
                    },
                    'bank_accounts': {
                        'limit': plan.max_bank_accounts,
                        'used': bank_account_count
                    },
                    'ai_requests': {
                        'limit': plan.max_ai_requests_per_month,
                        'used': ai_requests_count
                    }
                }
            
            # Calculate percentages
            for key in limits:
                limit_value = limits[key]['limit']
                used_value = limits[key]['used']
                if limit_value == 999999:  # Unlimited
                    limits[key]['percentage'] = 0
                else:
                    limits[key]['percentage'] = round((used_value / limit_value) * 100, 1) if limit_value > 0 else 0
            
            return Response(limits)
            
        except Exception as e:
            logger.error(f"Error in UsageLimitsView: {str(e)}", exc_info=True)
            return Response({
                'error': 'Failed to get usage limits',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)