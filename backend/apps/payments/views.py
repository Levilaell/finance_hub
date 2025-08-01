from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import SubscriptionPlan, Subscription, PaymentMethod, Payment, UsageRecord
from .serializers import (
    SubscriptionPlanSerializer, SubscriptionSerializer,
    PaymentMethodSerializer, CreatePaymentMethodSerializer,
    PaymentSerializer, CreateCheckoutSessionSerializer,
    ValidatePaymentSerializer, CompanySubscriptionSerializer
)
from .services.payment_gateway import PaymentService, StripeGateway
from .services.webhook_handler import WebhookHandler
from .services.retry_service import RetryService
from .services.audit_service import PaymentAuditService
from .exceptions import (
    PaymentException, StripeException, PaymentMethodRequiredException,
    SubscriptionNotActiveException, SubscriptionLimitExceededException,
    WebhookSignatureException, WebhookProcessingException
)
import logging
import json
import stripe

logger = logging.getLogger(__name__)


class SubscriptionPlanListView(generics.ListAPIView):
    """List available subscription plans"""
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]


class SubscriptionStatusView(APIView):
    """Get current subscription status for user's company"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        company = request.user.current_company
        if not company:
            raise PaymentException(
                message='No active company found',
                details={'user_id': request.user.id}
            )
        
        serializer = CompanySubscriptionSerializer(company)
        return Response(serializer.data)


class CreateCheckoutSessionView(APIView):
    """Create payment checkout session"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        company = request.user.current_company
        if not company:
            raise PaymentException(
                message='No active company found',
                details={'user_id': request.user.id}
            )
        
        # Check if company already has active subscription
        if hasattr(company, 'subscription') and company.subscription.is_active:
            raise PaymentException(
                message='Company already has an active subscription',
                details={'subscription_id': company.subscription.id}
            )
        
        try:
            plan = SubscriptionPlan.objects.get(id=serializer.validated_data['plan_id'])
            service = PaymentService()
            
            # Use retry logic for checkout session creation
            session_data = RetryService.retry_with_backoff(
                lambda: service.create_checkout_session(
                    company=company,
                    plan=plan,
                    billing_period=serializer.validated_data['billing_period'],
                    success_url=serializer.validated_data['success_url'],
                    cancel_url=serializer.validated_data['cancel_url']
                ),
                max_retries=3
            )
            
            # Log checkout session creation
            PaymentAuditService.log_payment_action(
                action='payment_initiated',
                user=request.user,
                company=company,
                metadata={
                    'plan': plan.name,
                    'billing_period': serializer.validated_data['billing_period'],
                    'session_id': session_data.get('session_id')
                },
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            return Response(session_data)
            
        except SubscriptionPlan.DoesNotExist:
            raise PaymentException(
                message='Invalid subscription plan selected',
                details={'plan_id': serializer.validated_data['plan_id']}
            )
        except stripe.error.StripeError as e:
            logger.error(f"Stripe checkout session creation failed: {e}")
            raise StripeException.from_stripe_error(e)
        except Exception as e:
            logger.error(f"Checkout session creation failed: {e}")
            raise PaymentException(
                message='Failed to create checkout session',
                details={'error': str(e)}
            )


class ValidatePaymentView(APIView):
    """Validate payment after checkout completion"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ValidatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        company = request.user.current_company
        if not company:
            raise PaymentException(
                message='No active company found',
                details={'user_id': request.user.id}
            )
        
        # Check if subscription is now active
        try:
            subscription = company.subscription
            if subscription and subscription.is_active:
                return Response({
                    'status': 'success',
                    'subscription': SubscriptionSerializer(subscription).data
                })
            else:
                return Response({
                    'status': 'pending',
                    'message': 'Payment is still being processed'
                })
        except Subscription.DoesNotExist:
            return Response({
                'status': 'pending',
                'message': 'Subscription not found yet'
            })


class PaymentMethodListCreateView(generics.ListCreateAPIView):
    """List and create payment methods"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(
            company=self.request.user.current_company
        )
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreatePaymentMethodSerializer
        return PaymentMethodSerializer
    
    def perform_create(self, serializer):
        company = self.request.user.current_company
        if not company:
            raise ValueError("No active company")
        
        try:
            service = PaymentService()
            payment_method = service.create_payment_method(
                company=company,
                token=serializer.validated_data['token'],
                payment_data=serializer.validated_data
            )
            
            # Log payment method creation
            PaymentAuditService.log_payment_method_action(
                action_type='added',
                payment_method=payment_method,
                user=self.request.user,
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT')
            )
            
            # Return the created payment method
            serializer.instance = payment_method
            
        except stripe.error.StripeError as e:
            # Log failed attempt
            PaymentAuditService.log_security_event(
                event_type='payment_method_failed',
                user=self.request.user,
                company=company,
                details={
                    'error': str(e),
                    'error_type': type(e).__name__
                },
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT')
            )
            raise StripeException.from_stripe_error(e)


class PaymentMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manage individual payment methods"""
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentMethodSerializer
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(
            company=self.request.user.current_company
        )
    
    def perform_update(self, serializer):
        # Only allow updating is_default
        if 'is_default' in serializer.validated_data:
            instance = serializer.save()
            
            # Log payment method update
            PaymentAuditService.log_payment_method_action(
                action_type='updated' if not instance.is_default else 'set_default',
                payment_method=instance,
                user=self.request.user,
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT')
            )


class PaymentHistoryView(generics.ListAPIView):
    """List payment history"""
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        return Payment.objects.filter(
            company=self.request.user.current_company,
            status='succeeded'
        ).select_related('payment_method')


class CancelSubscriptionView(APIView):
    """Cancel active subscription"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
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
                    message='No active subscription found to cancel'
                )
            
            service = PaymentService()
            
            # Use retry logic for cancellation
            subscription = RetryService.retry_with_backoff(
                lambda: service.cancel_subscription(subscription),
                max_retries=3
            )
            
            # Log subscription cancellation
            PaymentAuditService.log_payment_action(
                action='subscription_cancelled',
                user=request.user,
                company=company,
                subscription_id=subscription.id,
                metadata={
                    'plan': subscription.plan.name,
                    'cancel_at_period_end': subscription.cancel_at_period_end,
                    'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None
                },
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            return Response({
                'status': 'success',
                'message': 'Subscription will be cancelled at the end of the billing period',
                'subscription': SubscriptionSerializer(subscription).data
            })
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription cancellation failed: {e}")
            raise StripeException.from_stripe_error(e)
        except Exception as e:
            logger.error(f"Subscription cancellation failed: {e}")
            raise PaymentException(
                message='Failed to cancel subscription',
                details={'error': str(e)}
            )


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """Handle Stripe webhook events"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not sig_header:
            raise WebhookSignatureException(
                message='Missing Stripe signature header'
            )
        
        gateway = StripeGateway()
        
        try:
            event = gateway.verify_webhook(payload, sig_header)
            
            if not event:
                raise WebhookSignatureException(
                    message='Invalid webhook signature'
                )
            
            # Process webhook
            handler = WebhookHandler(gateway)
            result = handler.handle_stripe_webhook(event)
            
            # Log successful webhook processing
            logger.info(
                f"Successfully processed webhook: {event.get('type')} - {event.get('id')}",
                extra={
                    'event_type': event.get('type'),
                    'event_id': event.get('id'),
                    'livemode': event.get('livemode', False)
                }
            )
            
            # Audit log the webhook event
            PaymentAuditService.log_webhook_event(
                event_type=event.get('type'),
                event_id=event.get('id'),
                status='processed',
                metadata={
                    'livemode': event.get('livemode', False),
                    'created': event.get('created'),
                    'api_version': event.get('api_version')
                }
            )
            
            return Response(result)
            
        except WebhookSignatureException:
            # Re-raise signature exceptions
            raise
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            
            # Extract event details for error reporting
            event_type = 'unknown'
            event_id = 'unknown'
            try:
                import json
                event_data = json.loads(payload)
                event_type = event_data.get('type', 'unknown')
                event_id = event_data.get('id', 'unknown')
            except:
                pass
            
            # Log failed webhook processing
            PaymentAuditService.log_webhook_event(
                event_type=event_type,
                event_id=event_id,
                status='failed',
                error=str(e),
                metadata={
                    'error_type': type(e).__name__,
                    'payload_size': len(payload) if payload else 0
                }
            )
            
            raise WebhookProcessingException(
                event_type=event_type,
                event_id=event_id,
                message='Failed to process webhook',
                details={'error': str(e)}
            )