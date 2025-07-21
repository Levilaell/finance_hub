"""Test webhook processing"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from apps.companies.models import Company
import stripe
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class WebhookTestView(APIView):
    """Test webhook processing for a checkout session"""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        session_id = request.data.get('session_id')
        
        if not session_id:
            return Response({'error': 'session_id is required'}, status=400)
        
        try:
            # Configure Stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Retrieve the session
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=['line_items', 'subscription']
            )
            
            # Get company info
            company = request.user.company
            
            response_data = {
                'session': {
                    'id': session.id,
                    'status': session.status,
                    'payment_status': session.payment_status,
                    'mode': session.mode,
                    'metadata': session.metadata,
                    'subscription_id': session.subscription
                },
                'company': {
                    'id': company.id,
                    'name': company.name,
                    'current_status': company.subscription_status,
                    'current_plan': company.subscription_plan.name if company.subscription_plan else 'None',
                    'subscription_id': company.subscription_id
                }
            }
            
            # Force process the webhook
            if request.data.get('force_process'):
                from apps.payments.payment_service import PaymentService
                
                # Create fake webhook data
                fake_event = {
                    'type': 'checkout.session.completed',
                    'data': {
                        'object': session
                    }
                }
                
                payment_service = PaymentService()
                payment_service._handle_checkout_completed(fake_event['data'])
                
                # Refresh company
                company.refresh_from_db()
                
                response_data['after_processing'] = {
                    'status': company.subscription_status,
                    'plan': company.subscription_plan.name if company.subscription_plan else 'None',
                    'subscription_id': company.subscription_id
                }
                
                response_data['message'] = 'Webhook processed manually'
            
            return Response(response_data)
            
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error in webhook test: {e}", exc_info=True)
            return Response({'error': str(e)}, status=500)


class CheckWebhookEventsView(APIView):
    """Check recent webhook events from Stripe"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # List recent events
            events = stripe.Event.list(
                limit=10,
                types=['checkout.session.completed']
            )
            
            event_list = []
            for event in events.data:
                event_list.append({
                    'id': event.id,
                    'type': event.type,
                    'created': event.created,
                    'livemode': event.livemode,
                    'pending_webhooks': event.pending_webhooks,
                    'session_id': event.data.object.id if hasattr(event.data.object, 'id') else None
                })
            
            return Response({
                'total_events': len(event_list),
                'events': event_list,
                'webhook_endpoint': f"{settings.BACKEND_URL}/api/payments/webhooks/stripe/"
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)