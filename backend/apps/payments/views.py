from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from core.cache import cache_api_response
from .models import Subscription, PaymentMethod, Payment, UsageRecord
from apps.companies.models import SubscriptionPlan
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
from .services.webhook_security import SecureWebhookProcessor
from .services.customer_portal_service import CustomerPortalService
from .services.error_handler import ErrorHandler, payment_error_handler
from .services.health_check import get_health_status
from .services.monitoring_service import MonitoringService


def get_user_company(user):
    """
    Get the company for a user. 
    
    Note: This fixes the missing current_company property that was being used
    throughout the payment views but doesn't exist in the User model.
    """
    try:
        from apps.companies.models import Company
        return Company.objects.get(owner=user)
    except Company.DoesNotExist:
        return None
    except Company.MultipleObjectsReturned:
        # If user owns multiple companies, get the first one
        # TODO: Add proper current_company selection logic
        from apps.companies.models import Company
        return Company.objects.filter(owner=user).first()
from .exceptions import (
    PaymentException, StripeException, PaymentMethodRequiredException,
    SubscriptionNotActiveException, SubscriptionLimitExceededException,
    WebhookSignatureException, WebhookProcessingException,
    InvalidRequestException, CustomerPortalException
)
import logging
import json
import stripe

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60 * 60), name='dispatch')  # Cache for 1 hour
class SubscriptionPlanListView(generics.ListAPIView):
    """List available subscription plans"""
    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by('price_monthly')
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]


class SubscriptionStatusView(APIView):
    """Get current subscription status for user's company"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        company = get_user_company(request.user)
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
    
    @payment_error_handler
    def post(self, request):
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        company = get_user_company(request.user)
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
        
        # Validate plan exists
        try:
            plan = SubscriptionPlan.objects.get(id=serializer.validated_data['plan_id'])
        except SubscriptionPlan.DoesNotExist:
            raise InvalidRequestException(
                param='plan_id',
                message='Invalid subscription plan selected'
            )
        
        service = PaymentService()
        
        # Use retry logic for checkout session creation with circuit breaker
        session_data = RetryService.retry_with_backoff(
            lambda: ErrorHandler.with_circuit_breaker('stripe')(
                service.create_checkout_session
            )(
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


class ValidatePaymentView(APIView):
    """Validate payment after checkout completion"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        import stripe
        from django.conf import settings
        
        logger.info(f"🔍 Payment validation started for user: {request.user.email}")
        
        serializer = ValidatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_id = serializer.validated_data['session_id']
        logger.info(f"📋 Session ID to validate: {session_id}")
        
        company = get_user_company(request.user)
        if not company:
            logger.error(f"❌ No company found for user: {request.user.email}")
            raise PaymentException(
                message='No active company found',
                details={'user_id': request.user.id}
            )
        
        logger.info(f"🏢 User company: {company.id} - {company.name}")
        
        try:
            # Validate session with Stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe_mode = "TEST" if settings.STRIPE_SECRET_KEY.startswith('sk_test_') else "LIVE"
            logger.info(f"🔑 Stripe mode: {stripe_mode}")
            logger.info(f"🌐 Retrieving session from Stripe: {session_id}")
            
            session = stripe.checkout.Session.retrieve(session_id)
            logger.info(f"✅ Session retrieved - Status: {session.payment_status}, Amount: {session.amount_total}")
            
            # Check if session belongs to this company
            metadata = session.get('metadata', {})
            if not metadata.get('company_id'):
                # Try subscription_data metadata
                subscription_metadata = session.get('subscription_data', {}).get('metadata', {})
                if subscription_metadata:
                    metadata = subscription_metadata
            
            # Enhanced company validation with better error handling
            metadata_company_id = str(metadata.get('company_id', ''))
            current_company_id = str(company.id)
            
            logger.info(f"🔍 Company ID comparison:")
            logger.info(f"   Metadata company_id: '{metadata_company_id}'")
            logger.info(f"   Current company_id: '{current_company_id}'")
            logger.info(f"   Session metadata: {metadata}")
            
            if metadata_company_id != current_company_id:
                logger.warning(
                    f"Company ID mismatch during payment validation. "
                    f"Session company_id: {metadata_company_id}, "
                    f"Current company_id: {current_company_id}, "
                    f"User: {request.user.email}, "
                    f"Session: {session_id}"
                )
                
                # Check if payment was actually successful
                if session.payment_status == 'paid':
                    # Payment successful but company mismatch - this could be due to:
                    # 1. Company was deleted/recreated after checkout
                    # 2. User switched companies
                    # 3. Session belongs to different user's company
                    
                    return Response({
                        'status': 'error',
                        'message': 'Payment was processed successfully, but there was an account issue. Please contact support for assistance.',
                        'code': 'COMPANY_MISMATCH',
                        'details': {
                            'payment_processed': True,
                            'session_id': session_id,
                            'support_message': f'Reference session ID: {session_id}'
                        }
                    }, status=400)
                else:
                    return Response({
                        'status': 'error',
                        'message': 'Invalid payment session. Please try again.',
                        'code': 'INVALID_SESSION'
                    }, status=400)
            
            # Check payment status
            if session.payment_status != 'paid':
                return Response({
                    'status': 'error',
                    'message': f'Payment not completed. Status: {session.payment_status}',
                    'code': 'PAYMENT_NOT_COMPLETED'
                }, status=400)
            
            # Check if webhook was processed (subscription created)
            try:
                subscription = company.subscription
                if subscription and subscription.is_active:
                    # Payment was successful and subscription is active
                    PaymentAuditService.log_payment_validated(
                        company=company,
                        user=request.user,
                        metadata={
                            'session_id': session_id,
                            'subscription_id': subscription.id,
                            'validation_status': 'success'
                        }
                    )
                    
                    return Response({
                        'status': 'success',
                        'message': 'Payment validated successfully',
                        'subscription': SubscriptionSerializer(subscription).data
                    })
                else:
                    # Payment completed but webhook not processed yet
                    return Response({
                        'status': 'processing',
                        'message': 'Payment completed. Activating subscription...',
                        'retry_after': 5  # Suggest retry after 5 seconds
                    })
                    
            except Subscription.DoesNotExist:
                # Payment completed but webhook not processed yet
                return Response({
                    'status': 'processing',
                    'message': 'Payment completed. Setting up subscription...',
                    'retry_after': 10  # Suggest retry after 10 seconds
                })
                
        except stripe.error.InvalidRequestError as e:
            # This is the main error we're trying to fix - log detailed info
            logger.error(f"❌ Stripe InvalidRequestError:")
            logger.error(f"   Message: {str(e)}")
            logger.error(f"   Code: {getattr(e, 'code', 'N/A')}")
            logger.error(f"   Param: {getattr(e, 'param', 'N/A')}")
            logger.error(f"   Type: {getattr(e, 'type', 'N/A')}")
            logger.error(f"   Session ID attempted: {session_id}")
            logger.error(f"   User: {request.user.email}")
            logger.error(f"   Company: {company.id} - {company.name}")
            
            return Response({
                'status': 'error',
                'message': 'Invalid payment session. Please try again.',
                'code': 'INVALID_SESSION_ID',
                'details': {
                    'session_id': session_id,
                    'stripe_error': str(e),
                    'stripe_code': getattr(e, 'code', None),
                    'help': 'Session may have expired or does not exist. Please create a new payment.'
                }
            }, status=400)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error during payment validation: {e}")
            return Response({
                'status': 'error',
                'message': 'Unable to validate payment. Please contact support.',
                'code': 'STRIPE_ERROR'
            }, status=500)


class PaymentMethodListCreateView(generics.ListCreateAPIView):
    """List and create payment methods"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(
            company=get_user_company(self.request.user)
        )
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreatePaymentMethodSerializer
        return PaymentMethodSerializer
    
    def perform_create(self, serializer):
        company = get_user_company(self.request.user)
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
            company=get_user_company(self.request.user)
        ).select_related('company').order_by('-is_default', '-created_at')
    
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
            company=get_user_company(self.request.user),
            status='succeeded'
        ).select_related('payment_method', 'subscription', 'company').order_by('-created_at')


class CancelSubscriptionView(APIView):
    """Cancel active subscription"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        company = get_user_company(request.user)
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
    """Handle Stripe webhook events with enhanced security"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not sig_header:
            # Log missing signature as security event
            PaymentAuditService.log_security_event(
                event_type='webhook_missing_signature',
                user=None,
                company=None,
                details={
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT')
                },
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            raise WebhookSignatureException(
                message='Missing Stripe signature header'
            )
        
        gateway = StripeGateway()
        secure_processor = SecureWebhookProcessor()
        
        try:
            # Process webhook with security validation
            security_result = secure_processor.process_webhook(
                request=request,
                payload=payload,
                signature=sig_header,
                gateway=gateway
            )
            
            if security_result['status'] == 'error':
                # Security validation failed
                return Response(
                    {'error': security_result['message']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Extract validated event
            event = security_result['event']
            
            # Process webhook with retry protection
            handler = WebhookHandler(gateway)
            result = RetryService.retry_with_backoff(
                lambda: handler.handle_stripe_webhook(event),
                max_retries=3,
                exceptions=(Exception,)
            )
            
            # Log successful webhook processing
            logger.info(
                f"Successfully processed webhook: {event.get('type')} - {event.get('id')}",
                extra={
                    'event_type': event.get('type'),
                    'event_id': event.get('id'),
                    'livemode': event.get('livemode', False),
                    'security_metadata': security_result.get('metadata', {})
                }
            )
            
            # Comprehensive audit log
            PaymentAuditService.log_webhook_event(
                event_type=event.get('type'),
                event_id=event.get('id'),
                status='processed',
                metadata={
                    'livemode': event.get('livemode', False),
                    'created': event.get('created'),
                    'api_version': event.get('api_version'),
                    'security_checks': security_result.get('metadata', {}).get('security_checks', []),
                    'processing_time_ms': int((timezone.now() - timezone.now()).total_seconds() * 1000)
                }
            )
            
            return Response(result)
            
        except WebhookSignatureException as e:
            # Log signature failure
            PaymentAuditService.log_security_event(
                event_type='webhook_signature_invalid',
                user=None,
                company=None,
                details={
                    'error': str(e),
                    'ip_address': request.META.get('REMOTE_ADDR')
                },
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            raise
        except Exception as e:
            logger.error(f"Webhook processing error: {type(e).__name__}")
            
            # Extract event details safely
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
                error=type(e).__name__,  # Don't expose error details
                metadata={
                    'error_type': type(e).__name__,
                    'payload_size': len(payload) if payload else 0,
                    'has_signature': bool(sig_header)
                }
            )
            
            # Return generic error response
            return Response(
                {'error': 'Webhook processing failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CustomerPortalView(APIView):
    """Create Stripe Customer Portal session"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create portal session for billing management"""
        company = get_user_company(request.user)
        if not company:
            raise PaymentException(
                message='No active company found',
                details={'user_id': request.user.id}
            )
        
        # Get return URL from request or use default
        return_url = request.data.get(
            'return_url',
            f"{settings.FRONTEND_URL}/dashboard/billing"
        )
        
        # Get optional flow type
        flow_type = request.data.get('flow_type', 'general')
        
        try:
            portal_service = CustomerPortalService()
            
            # Validate portal access
            can_access, reason = portal_service.validate_portal_access(company)
            if not can_access:
                raise PaymentException(
                    message='Cannot access billing portal',
                    details={'reason': reason}
                )
            
            # Create appropriate session based on flow type
            if flow_type == 'update_subscription':
                result = portal_service.create_subscription_update_session(
                    company=company,
                    return_url=return_url,
                    user=request.user
                )
            elif flow_type == 'update_payment_method':
                result = portal_service.create_payment_method_update_session(
                    company=company,
                    return_url=return_url,
                    user=request.user
                )
            elif flow_type == 'view_invoices':
                result = portal_service.create_invoice_history_session(
                    company=company,
                    return_url=return_url,
                    user=request.user
                )
            elif flow_type == 'cancel_subscription':
                result = portal_service.create_cancel_subscription_session(
                    company=company,
                    return_url=return_url,
                    user=request.user
                )
            else:
                # General portal access
                result = portal_service.create_portal_session(
                    company=company,
                    return_url=return_url,
                    user=request.user
                )
            
            return Response({
                'portal_url': result['url'],
                'session_id': result['session_id'],
                'expires_at': result['expires_at'].isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to create customer portal session: {e}")
            if isinstance(e, PaymentException):
                raise
            raise PaymentException(
                message='Failed to create billing portal session',
                details={'error': str(e)}
            )


class CustomerPortalLinksView(APIView):
    """Get quick access links for different portal actions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all available portal links"""
        company = get_user_company(request.user)
        if not company:
            raise PaymentException(
                message='No active company found',
                details={'user_id': request.user.id}
            )
        
        # Get base URL from request or use default
        base_url = request.query_params.get(
            'base_url',
            settings.FRONTEND_URL
        )
        
        try:
            portal_service = CustomerPortalService()
            
            # Validate access first
            can_access, reason = portal_service.validate_portal_access(company)
            
            response_data = {
                'can_access': can_access,
                'reason': reason if not can_access else None,
                'links': {}
            }
            
            if can_access:
                # Generate all portal links
                links = portal_service.generate_portal_links(company, base_url)
                response_data['links'] = links
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Failed to generate portal links: {e}")
            raise PaymentException(
                message='Failed to generate portal links',
                details={'error': str(e)}
            )


class HealthCheckView(APIView):
    """Health check endpoint for monitoring"""
    permission_classes = [AllowAny]  # Allow monitoring tools
    
    def get(self, request):
        """Get payment system health status"""
        health_data, http_status = get_health_status()
        
        # Add request metadata
        health_data['request_id'] = getattr(request, 'id', None)
        
        return Response(health_data, status=http_status)


class MonitoringDashboardView(APIView):
    """Payment monitoring dashboard data"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get monitoring dashboard metrics"""
        # Check if user has permission
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get time range from query params
        hours = int(request.query_params.get('hours', 24))
        if hours > 168:  # Max 7 days
            hours = 168
        
        try:
            metrics = MonitoringService.get_payment_dashboard_metrics(hours)
            
            # Add health status
            health_data, _ = get_health_status()
            metrics['health'] = health_data
            
            return Response(metrics)
            
        except Exception as e:
            logger.error(f"Failed to get monitoring metrics: {e}")
            return Response(
                {'error': 'Failed to retrieve metrics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )