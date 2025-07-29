"""Debug views for payment system"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from apps.companies.models import SubscriptionPlan
import logging

logger = logging.getLogger(__name__)


class PaymentDebugView(APIView):
    """Debug payment configuration"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Return debug information"""
        try:
            # Check Stripe configuration
            stripe_configured = bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_PUBLIC_KEY)
            
            # Check plans
            plans = SubscriptionPlan.objects.filter(is_active=True)
            plan_info = []
            for plan in plans:
                plan_info.append({
                    'name': plan.name,
                    'slug': plan.slug,
                    'monthly_price': str(plan.price_monthly),
                    'yearly_price': str(plan.price_yearly),
                    'stripe_monthly_id': plan.stripe_price_id_monthly or 'NOT SET',
                    'stripe_yearly_id': plan.stripe_price_id_yearly or 'NOT SET'
                })
            
            # Check user
            user_info = {
                'email': request.user.email,
                'has_company': hasattr(request.user, 'company'),
                'payment_customer_id': request.user.payment_customer_id or 'NOT SET'
            }
            
            if hasattr(request.user, 'company'):
                company = request.user.company
                user_info['company'] = {
                    'name': company.name,
                    'status': company.subscription_status,
                    'plan': company.subscription_plan.name if company.subscription_plan else 'NO PLAN'
                }
            
            return Response({
                'stripe_configured': stripe_configured,
                'frontend_url': settings.FRONTEND_URL,
                'plans': plan_info,
                'user': user_info,
                'gateway': settings.DEFAULT_PAYMENT_GATEWAY
            })
            
        except Exception as e:
            logger.error(f"Debug view error: {e}")
            return Response({
                'error': str(e)
            }, status=500)