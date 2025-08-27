"""
Enhanced ValidatePaymentView with comprehensive error handling and logging

Esta versão adiciona:
1. Logging detalhado de cada passo
2. Melhor tratamento de erros Stripe
3. Validações adicionais
4. Informações de debug
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import stripe
import logging

logger = logging.getLogger(__name__)

class EnhancedValidatePaymentView(APIView):
    """Enhanced payment validation with detailed logging"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Enhanced validation with comprehensive error handling
        """
        from .serializers import ValidatePaymentSerializer
        from .exceptions import PaymentException
        from .services.audit_service import PaymentAuditService
        from apps.companies.models import Company
        from .models import Subscription
        from .serializers import SubscriptionSerializer
        
        # Function to get user company (same as current code)
        def get_user_company(user):
            try:
                return Company.objects.get(owner=user)
            except Company.DoesNotExist:
                return None
            except Company.MultipleObjectsReturned:
                return Company.objects.filter(owner=user).first()
        
        logger.info(f"🔍 Payment validation started for user: {request.user.email}")
        
        # Validate request data
        serializer = ValidatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"❌ Invalid request data: {serializer.errors}")
            return Response({
                'status': 'error',
                'message': 'Invalid request data',
                'code': 'INVALID_REQUEST',
                'details': serializer.errors
            }, status=400)
        
        session_id = serializer.validated_data['session_id']
        logger.info(f"📋 Session ID to validate: {session_id}")
        
        # Get user company
        company = get_user_company(request.user)
        if not company:
            logger.error(f"❌ No company found for user: {request.user.email}")
            raise PaymentException(
                message='No active company found',
                details={'user_id': request.user.id}
            )
        
        logger.info(f"🏢 User company: {company.id} - {company.name}")
        
        try:
            # Configure Stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe_mode = "TEST" if settings.STRIPE_SECRET_KEY.startswith('sk_test_') else "LIVE"
            logger.info(f"🔑 Stripe mode: {stripe_mode}")
            
            # Validate session with Stripe
            logger.info(f"🌐 Retrieving session from Stripe: {session_id}")
            session = stripe.checkout.Session.retrieve(session_id)
            
            logger.info(f"✅ Session retrieved successfully")
            logger.info(f"   Payment Status: {session.payment_status}")
            logger.info(f"   Customer: {session.customer}")
            logger.info(f"   Amount: {session.amount_total}")
            
            # Extract metadata
            metadata = session.get('metadata', {})
            if not metadata.get('company_id'):
                # Try subscription_data metadata
                subscription_metadata = session.get('subscription_data', {}).get('metadata', {})
                if subscription_metadata:
                    metadata = subscription_metadata
                    logger.info(f"📄 Using subscription_data metadata: {metadata}")
                else:
                    logger.warning(f"⚠️  No metadata found in session")
            else:
                logger.info(f"📄 Session metadata: {metadata}")
            
            # Enhanced company validation with better error handling
            metadata_company_id = str(metadata.get('company_id', ''))
            current_company_id = str(company.id)
            
            logger.info(f"🔍 Company ID comparison:")
            logger.info(f"   Metadata company_id: '{metadata_company_id}'")
            logger.info(f"   Current company_id: '{current_company_id}'")
            
            if metadata_company_id != current_company_id:
                logger.warning(
                    f"⚠️  Company ID mismatch during payment validation. "
                    f"Session company_id: '{metadata_company_id}', "
                    f"Current company_id: '{current_company_id}', "
                    f"User: {request.user.email}, "
                    f"Session: {session_id}"
                )
                
                # Check if payment was actually successful
                if session.payment_status == 'paid':
                    logger.info(f"💰 Payment was successful but company mismatch - offering support contact")
                    return Response({
                        'status': 'error',
                        'message': 'Payment was processed successfully, but there was an account issue. Please contact support for assistance.',
                        'code': 'COMPANY_MISMATCH',
                        'details': {
                            'payment_processed': True,
                            'session_id': session_id,
                            'support_message': f'Reference session ID: {session_id}',
                            'expected_company_id': current_company_id,
                            'session_company_id': metadata_company_id
                        }
                    }, status=400)
                else:
                    logger.info(f"💸 Payment not completed and company mismatch")
                    return Response({
                        'status': 'error',
                        'message': 'Invalid payment session. Please try again.',
                        'code': 'INVALID_SESSION',
                        'details': {
                            'expected_company_id': current_company_id,
                            'session_company_id': metadata_company_id
                        }
                    }, status=400)
            
            # Check payment status
            logger.info(f"💳 Checking payment status: {session.payment_status}")
            if session.payment_status != 'paid':
                logger.warning(f"❌ Payment not completed. Status: {session.payment_status}")
                return Response({
                    'status': 'error',
                    'message': f'Payment not completed. Status: {session.payment_status}',
                    'code': 'PAYMENT_NOT_COMPLETED',
                    'details': {'payment_status': session.payment_status}
                }, status=400)
            
            # Check if webhook was processed (subscription created)
            logger.info(f"🔍 Checking if subscription exists for company {company.id}")
            try:
                subscription = company.subscription
                logger.info(f"📋 Found subscription: {subscription.id} (status: {subscription.status})")
                
                if subscription and subscription.is_active:
                    # Payment was successful and subscription is active
                    logger.info(f"✅ Payment validation successful - subscription active")
                    
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
                    logger.info(f"⏳ Subscription exists but not active - webhook may still be processing")
                    return Response({
                        'status': 'processing',
                        'message': 'Payment completed. Activating subscription...',
                        'retry_after': 5  # Suggest retry after 5 seconds
                    })
                    
            except Subscription.DoesNotExist:
                # Payment completed but webhook not processed yet
                logger.info(f"⏳ No subscription found - webhook may still be processing")
                return Response({
                    'status': 'processing',
                    'message': 'Payment completed. Setting up subscription...',
                    'retry_after': 10  # Suggest retry after 10 seconds
                })
                
        except stripe.error.InvalidRequestError as e:
            # This is the main error we're trying to fix
            logger.error(f"❌ Stripe InvalidRequestError:")
            logger.error(f"   Message: {str(e)}")
            logger.error(f"   Code: {getattr(e, 'code', 'N/A')}")
            logger.error(f"   Param: {getattr(e, 'param', 'N/A')}")
            logger.error(f"   Type: {getattr(e, 'type', 'N/A')}")
            logger.error(f"   Session ID attempted: {session_id}")
            
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
            logger.error(f"❌ Stripe error during payment validation: {e}")
            return Response({
                'status': 'error',
                'message': 'Unable to validate payment. Please contact support.',
                'code': 'STRIPE_ERROR',
                'details': {
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, status=500)
        
        except Exception as e:
            logger.error(f"❌ Unexpected error during payment validation: {e}")
            return Response({
                'status': 'error',
                'message': 'An unexpected error occurred. Please contact support.',
                'code': 'UNEXPECTED_ERROR',
                'details': {
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, status=500)