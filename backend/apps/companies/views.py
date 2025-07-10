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

from .models import Company, CompanyUser, SubscriptionPlan, PaymentMethod, PaymentHistory
from .serializers import (
    CompanySerializer,
    CompanyUpdateSerializer,
    CompanyUserSerializer,
    InviteUserSerializer,
    SubscriptionPlanSerializer,
    UpgradeSubscriptionSerializer,
    PaymentMethodSerializer,
    PaymentHistorySerializer,
)

User = get_user_model()


class CompanyDetailView(generics.RetrieveAPIView):
    """Get company profile details"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CompanySerializer
    
    def get_object(self):
        # Get the user's company - either as owner or team member
        user = self.request.user
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
            from django.http import Http404
            raise Http404("User is not associated with any company")
        
        return company


class CompanyUpdateView(generics.UpdateAPIView):
    """Update company profile"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CompanyUpdateSerializer
    
    def get_object(self):
        # Get the user's company - either as owner or team member
        user = self.request.user
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
            from django.http import Http404
            raise Http404("User is not associated with any company")
        
        return company


class SubscriptionPlansView(generics.ListAPIView):
    """List available subscription plans"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscriptionPlanSerializer
    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by('price_monthly')


class UpgradeSubscriptionView(APIView):
    """Upgrade company subscription"""
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
        
        # Update subscription
        company.subscription_plan = new_plan
        company.subscription_status = 'active'
        company.save()
        
        # Integrate with payment provider
        from apps.payments.payment_service import PaymentService
        
        try:
            payment_service = PaymentService()
            result = payment_service.create_subscription(company, new_plan)
            
            # Return payment intent for frontend to complete
            return Response({
                'message': 'Subscription upgrade initiated',
                'new_plan': SubscriptionPlanSerializer(new_plan).data,
                'payment_intent': result.get('client_secret'),  # For Stripe
                'payment_url': result.get('init_point'),  # For MercadoPago
                'subscription_id': result['subscription_id']
            })
        except Exception as e:
            logger.error(f"Payment error: {e}")
            return Response({
                'error': 'Payment processing failed. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': 'Subscription upgraded successfully',
            'new_plan': SubscriptionPlanSerializer(new_plan).data
        })


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
        
        # Update subscription status
        company.subscription_status = 'cancelled'
        company.save()
        
        # Handle cancellation with payment provider
        from apps.payments.payment_service import PaymentService
        
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


class CompanyUsersView(generics.ListAPIView):
    """List company users/team members"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CompanyUserSerializer
    
    def get_queryset(self):
        # Get the user's company - either as owner or team member
        user = self.request.user
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
            return CompanyUser.objects.none()
        
        return CompanyUser.objects.filter(
            company=company
        ).select_related('user')


class InviteUserView(APIView):
    """Invite user to company"""
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
        
        # Check if company plan allows more users
        current_users = CompanyUser.objects.filter(
            company=company,
            is_active=True
        ).count() + 1  # +1 for owner
        
        if current_users >= company.subscription_plan.max_users:
            return Response({
                'error': 'User limit reached for current subscription plan'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = InviteUserSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        role = serializer.validated_data['role']
        permissions = serializer.validated_data.get('permissions', {})
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Send invitation email to new user
            from apps.notifications.email_service import EmailService
            from django.conf import settings
            
            invitation_url = f"{settings.FRONTEND_URL}/accept-invitation?email={email}&company={company.id}"
            EmailService.send_invitation_email(
                email=email,
                inviter=request.user,
                company=company,
                invitation_url=invitation_url
            )
            
            return Response({
                'message': 'Invitation sent to new user',
                'email': email
            })
        
        # Add existing user to company
        company_user = CompanyUser.objects.create(
            company=company,
            user=user,
            role=role,
            permissions=permissions,
            joined_at=timezone.now()
        )
        
        # Send notification to user
        from apps.notifications.email_service import EmailService
        from django.conf import settings
        
        EmailService.send_invitation_email(
            email=user.email,
            inviter=request.user,
            company=company,
            invitation_url=f"{settings.FRONTEND_URL}/dashboard"
        )
        
        return Response({
            'message': 'User added to company',
            'user': CompanyUserSerializer(company_user).data
        })


class RemoveUserView(APIView):
    """Remove user from company"""
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, user_id):
        # Get the user's company - only owners can remove users
        user = request.user
        company = None
        
        # Check if user is a company owner
        if hasattr(user, 'company'):
            try:
                company = user.company
            except Company.DoesNotExist:
                pass
        
        if not company:
            return Response({
                'error': 'Only company owner can remove users'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Only owner can remove users
        if request.user != company.owner:
            return Response({
                'error': 'Only company owner can remove users'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if trying to remove the owner
        if int(user_id) == company.owner.id:
            return Response({
                'error': 'Cannot remove company owner'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            company_user = CompanyUser.objects.get(
                company=company,
                user_id=user_id
            )
        except CompanyUser.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        company_user.delete()
        
        return Response({
            'message': 'User removed successfully'
        }, status=status.HTTP_204_NO_CONTENT)


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