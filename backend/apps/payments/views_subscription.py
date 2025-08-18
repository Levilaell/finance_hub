"""Additional views for subscription management"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from apps.companies.models import SubscriptionPlan
from .services.subscription_service import SubscriptionService
from .services.audit_service import PaymentAuditService
from .exceptions import PaymentException, SubscriptionNotActiveException
import logging

logger = logging.getLogger(__name__)


class ChangePlanSerializer(serializers.Serializer):
    """Serializer for plan change requests"""
    plan_id = serializers.IntegerField()
    billing_period = serializers.ChoiceField(choices=['monthly', 'yearly'], required=False)
    immediate = serializers.BooleanField(default=True)
    
    def validate_plan_id(self, value):
        try:
            SubscriptionPlan.objects.get(id=value, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid plan selected")
        return value


class CalculateProrationSerializer(serializers.Serializer):
    """Serializer for proration calculation requests"""
    plan_id = serializers.IntegerField()
    billing_period = serializers.ChoiceField(choices=['monthly', 'yearly'], required=False)
    
    def validate_plan_id(self, value):
        try:
            SubscriptionPlan.objects.get(id=value, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid plan selected")
        return value


class SubscriptionChangePlanView(APIView):
    """Change subscription plan with proration"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        company = request.user.current_company
        if not company:
            raise PaymentException(
                message='No active company found',
                details={'user_id': request.user.id}
            )
        
        try:
            subscription = company.subscription
            if not subscription or not subscription.is_active:
                raise SubscriptionNotActiveException(
                    message='No active subscription found'
                )
            
            new_plan = SubscriptionPlan.objects.get(id=serializer.validated_data['plan_id'])
            
            # Perform plan change
            result = SubscriptionService.change_subscription_plan(
                subscription=subscription,
                new_plan=new_plan,
                billing_period=serializer.validated_data.get('billing_period'),
                immediate=serializer.validated_data['immediate']
            )
            
            # Log subscription plan change
            PaymentAuditService.log_payment_action(
                action='subscription_plan_changed',
                user=request.user,
                company=company,
                subscription_id=subscription.id,
                metadata={
                    'old_plan': subscription.plan.name,
                    'new_plan': new_plan.name,
                    'billing_period': serializer.validated_data.get('billing_period', subscription.billing_period),
                    'immediate': serializer.validated_data['immediate'],
                    'proration_applied': result.get('proration_applied', False),
                    'proration_amount': str(result.get('proration_amount', 0))
                },
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            return Response(result)
            
        except ValueError as e:
            raise PaymentException(
                message=str(e),
                details={'current_plan': subscription.plan.name if subscription else None}
            )
        except Exception as e:
            logger.error(f"Plan change failed: {e}")
            raise PaymentException(
                message='Failed to change subscription plan',
                details={'error': str(e)}
            )


class SubscriptionProrationView(APIView):
    """Calculate proration for plan changes"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CalculateProrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        company = request.user.current_company
        if not company:
            raise PaymentException(
                message='No active company found',
                details={'user_id': request.user.id}
            )
        
        try:
            subscription = company.subscription
            if not subscription or not subscription.is_active:
                raise SubscriptionNotActiveException(
                    message='No active subscription found'
                )
            
            new_plan = SubscriptionPlan.objects.get(id=serializer.validated_data['plan_id'])
            billing_period = serializer.validated_data.get('billing_period', subscription.billing_period)
            
            # Check if plan change is allowed
            can_change, change_type = SubscriptionService.can_upgrade_plan(
                subscription.plan, new_plan
            )
            
            if not can_change:
                return Response({
                    'error': 'Cannot change to the same plan',
                    'current_plan': subscription.plan.name,
                    'requested_plan': new_plan.name
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate proration
            proration = SubscriptionService.calculate_proration(
                subscription, new_plan, billing_period
            )
            
            return Response({
                'current_plan': {
                    'name': subscription.plan.name,
                    'display_name': subscription.plan.display_name,
                    'price': float(subscription.plan.get_price(subscription.billing_period))
                },
                'new_plan': {
                    'name': new_plan.name,
                    'display_name': new_plan.display_name,
                    'price': float(new_plan.get_price(billing_period))
                },
                'change_type': change_type,
                'billing_period': billing_period,
                'proration': {
                    'amount': str(proration['proration_amount']),
                    'credit': str(proration['credit_amount']),
                    'charge': str(proration['charge_amount']),
                    'days_remaining': proration['days_remaining'],
                    'description': proration['description']
                }
            })
            
        except Exception as e:
            logger.error(f"Proration calculation failed: {e}")
            raise PaymentException(
                message='Failed to calculate proration',
                details={'error': str(e)}
            )


class SubscriptionUsageLimitsView(APIView):
    """Check current usage against subscription limits"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        company = request.user.current_company
        if not company:
            raise PaymentException(
                message='No active company found',
                details={'user_id': request.user.id}
            )
        
        subscription = getattr(company, 'subscription', None)
        
        # Validate limits
        limits = SubscriptionService.validate_subscription_limits(subscription)
        
        # Check if access should be suspended
        access_suspended = SubscriptionService.should_suspend_access(subscription)
        
        # Get grace period info if applicable
        grace_period_end = None
        if subscription and subscription.status == 'past_due':
            grace_period_end = SubscriptionService.get_grace_period_end(subscription)
        
        return Response({
            'has_active_subscription': subscription and subscription.is_active,
            'subscription_status': subscription.status if subscription else None,
            'access_suspended': access_suspended,
            'grace_period_end': grace_period_end.isoformat() if grace_period_end else None,
            'limits': {
                'can_add_transactions': limits.get('transactions', False),
                'can_add_bank_accounts': limits.get('bank_accounts', False),
                'can_use_ai': limits.get('ai_requests', False)
            }
        })