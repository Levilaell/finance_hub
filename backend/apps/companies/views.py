"""
Companies app views
"""
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Company, CompanyUser, SubscriptionPlan
from .serializers import (
    CompanySerializer,
    CompanyUpdateSerializer,
    CompanyUserSerializer,
    InviteUserSerializer,
    SubscriptionPlanSerializer,
    UpgradeSubscriptionSerializer,
)

User = get_user_model()


class CompanyDetailView(generics.RetrieveAPIView):
    """Get company profile details"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CompanySerializer
    
    def get_object(self):
        return self.request.user.company


class CompanyUpdateView(generics.UpdateAPIView):
    """Update company profile"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CompanyUpdateSerializer
    
    def get_object(self):
        return self.request.user.company


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
        
        company = request.user.company
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
        company = request.user.company
        
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
        return CompanyUser.objects.filter(
            company=self.request.user.company
        ).select_related('user')


class InviteUserView(APIView):
    """Invite user to company"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        company = request.user.company
        
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
        company = request.user.company
        
        # Only owner can remove users
        if request.user != company.owner:
            return Response({
                'error': 'Only company owner can remove users'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            company_user = CompanyUser.objects.get(
                company=company,
                user_id=user_id
            )
        except CompanyUser.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Can't remove owner
        if company_user.user == company.owner:
            return Response({
                'error': 'Cannot remove company owner'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        company_user.delete()
        
        return Response({
            'message': 'User removed successfully'
        }, status=status.HTTP_204_NO_CONTENT)