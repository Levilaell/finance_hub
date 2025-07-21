"""
Payment views including checkout and webhooks
"""
import logging
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .payment_service import PaymentService
from apps.companies.models import SubscriptionPlan
from apps.companies.serializers import SubscriptionPlanSerializer

logger = logging.getLogger(__name__)


class CreateCheckoutSessionView(APIView):
    """Create a checkout session for immediate payment"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        plan_slug = request.data.get('plan_slug')
        billing_cycle = request.data.get('billing_cycle', 'monthly')
        
        if not plan_slug:
            return Response({
                'error': 'Plan slug is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the plan
            plan = SubscriptionPlan.objects.get(slug=plan_slug, is_active=True)
            
            # Get user's company
            company = request.user.company
            
            # Check if already on a paid plan
            if company.subscription_status == 'active' and company.subscription_plan.price_monthly > 0:
                return Response({
                    'error': 'You already have an active subscription. Use upgrade endpoint instead.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create checkout session
            payment_service = PaymentService()
            
            # Ensure customer exists
            if not request.user.payment_customer_id:
                payment_service.create_customer(request.user)
            
            # Create checkout session
            amount = plan.price_yearly if billing_cycle == 'yearly' else plan.price_monthly
            
            checkout_data = {
                'customer_id': request.user.payment_customer_id,
                'amount': amount,
                'currency': 'BRL',
                'description': f'{plan.name} - {billing_cycle}',
                'metadata': {
                    'company_id': company.id,
                    'plan_id': plan.id,
                    'billing_cycle': billing_cycle,
                    'user_id': request.user.id
                },
                'success_url': f"{settings.FRONTEND_URL}/dashboard/subscription/success",
                'cancel_url': f"{settings.FRONTEND_URL}/dashboard/subscription/upgrade"
            }
            
            if payment_service.gateway_name == 'stripe':
                # For Stripe, create a checkout session
                import stripe
                stripe.api_key = settings.STRIPE_SECRET_KEY
                
                # Selecionar o ID de preço correto baseado no ciclo de cobrança
                if billing_cycle == 'yearly':
                    price_id = plan.stripe_price_id_yearly
                else:
                    price_id = plan.stripe_price_id_monthly
                
                if not price_id:
                    return Response({
                        'error': f'Stripe price ID not configured for {billing_cycle} billing'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Criar cliente no Stripe se não existir
                customer_id = request.user.payment_customer_id
                if not customer_id:
                    customer = stripe.Customer.create(
                        email=request.user.email,
                        name=request.user.full_name,
                        metadata={
                            'user_id': request.user.id,
                            'company_id': company.id
                        }
                    )
                    customer_id = customer.id
                    # Salvar o ID do cliente no usuário
                    request.user.payment_customer_id = customer_id
                    request.user.save()
                
                session = stripe.checkout.Session.create(
                    customer=customer_id,
                    payment_method_types=['card'],
                    line_items=[{
                        'price': price_id,
                        'quantity': 1,
                    }],
                    mode='subscription',
                    success_url=checkout_data['success_url'],
                    cancel_url=checkout_data['cancel_url'],
                    metadata=checkout_data['metadata']
                )
                
                return Response({
                    'checkout_url': session.url,
                    'session_id': session.id
                })
                
            elif payment_service.gateway_name == 'mercadopago':
                # For MercadoPago, create a preference
                preference_data = {
                    'items': [{
                        'title': checkout_data['description'],
                        'quantity': 1,
                        'unit_price': float(amount)
                    }],
                    'payer': {
                        'email': request.user.email
                    },
                    'back_urls': {
                        'success': checkout_data['success_url'],
                        'failure': checkout_data['cancel_url'],
                        'pending': checkout_data['success_url']
                    },
                    'auto_return': 'approved',
                    'metadata': checkout_data['metadata']
                }
                
                result = payment_service.gateway.mp.preference().create(preference_data)
                
                if result['status'] == 201:
                    return Response({
                        'checkout_url': result['response']['init_point'],
                        'preference_id': result['response']['id']
                    })
                else:
                    raise Exception('Failed to create MercadoPago preference')
            
        except SubscriptionPlan.DoesNotExist:
            return Response({
                'error': 'Invalid plan'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Checkout error: {e}")
            return Response({
                'error': 'Failed to create checkout session'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ValidatePaymentView(APIView):
    """Validate payment after checkout"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        session_id = request.data.get('session_id')
        payment_id = request.data.get('payment_id')
        
        if not session_id and not payment_id:
            return Response({
                'error': 'Session ID or Payment ID required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            payment_service = PaymentService()
            
            if payment_service.gateway_name == 'stripe' and session_id:
                import stripe
                stripe.api_key = settings.STRIPE_SECRET_KEY
                
                session = stripe.checkout.Session.retrieve(session_id)
                
                if session.payment_status == 'paid':
                    # Payment successful, subscription should be activated via webhook
                    return Response({
                        'status': 'success',
                        'message': 'Payment confirmed. Your subscription is now active.'
                    })
                else:
                    return Response({
                        'status': 'pending',
                        'message': 'Payment is still being processed.'
                    })
                    
            elif payment_service.gateway_name == 'mercadopago' and payment_id:
                result = payment_service.gateway.mp.payment().get(payment_id)
                
                if result['status'] == 200:
                    payment = result['response']
                    if payment['status'] == 'approved':
                        return Response({
                            'status': 'success',
                            'message': 'Payment confirmed. Your subscription is now active.'
                        })
                    elif payment['status'] == 'pending':
                        return Response({
                            'status': 'pending',
                            'message': 'Payment is pending confirmation.'
                        })
                    else:
                        return Response({
                            'status': 'failed',
                            'message': 'Payment was not completed.'
                        })
                        
        except Exception as e:
            logger.error(f"Payment validation error: {e}")
            return Response({
                'error': 'Failed to validate payment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckSubscriptionStatusView(APIView):
    """Check if user has active paid subscription"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            company = request.user.company
        except:
            return Response({
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if has payment method
        has_payment_method = company.payment_methods.filter(is_active=True).exists()
        
        # Calculate days left in trial
        days_left = 0
        if company.trial_ends_at:
            from django.utils import timezone
            delta = company.trial_ends_at - timezone.now()
            days_left = max(0, delta.days)
        
        # Determine if payment setup is required
        requires_payment_setup = (
            company.subscription_status == 'trial' and 
            not has_payment_method
        )
        
        return Response({
            'subscription_status': company.subscription_status,
            'has_payment_method': has_payment_method,
            'trial_days_left': days_left,
            'plan': SubscriptionPlanSerializer(company.subscription_plan).data if company.subscription_plan else None,
            'requires_payment_setup': requires_payment_setup,
            'trial_ends_at': company.trial_ends_at.isoformat() if company.trial_ends_at else None,
            'next_billing_date': company.next_billing_date.isoformat() if company.next_billing_date else None,
        })


@api_view(['POST'])
@permission_classes([AllowAny])  # Webhooks don't use auth
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    try:
        payment_service = PaymentService(gateway_name='stripe')
        result = payment_service.handle_webhook(request)
        
        logger.info(f"Stripe webhook processed: {result['event_type']}")
        return Response({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])  # Webhooks don't use auth
def mercadopago_webhook(request):
    """Handle MercadoPago webhooks"""
    try:
        payment_service = PaymentService(gateway_name='mercadopago')
        result = payment_service.handle_webhook(request)
        
        logger.info(f"MercadoPago webhook processed: {result['event_type']}")
        return Response({'status': 'success'})
        
    except Exception as e:
        logger.error(f"MercadoPago webhook error: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )