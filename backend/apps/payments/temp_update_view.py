"""Temporary view to update Stripe IDs - REMOVE AFTER USE"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from apps.companies.models import SubscriptionPlan
from django.contrib.auth import get_user_model

User = get_user_model()


class UpdateStripePricesView(APIView):
    """Temporary endpoint to update Stripe prices"""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        # Extra security - only specific admin
        if request.user.email != 'admin@caixahub.com.br':
            return Response({'error': 'Unauthorized'}, status=403)
        
        try:
            updates = []
            
            # Starter
            plan = SubscriptionPlan.objects.get(slug='starter')
            plan.stripe_price_id_monthly = 'price_1RkePlPFSVtvOaJKYbiX6TqQ'
            plan.stripe_price_id_yearly = 'price_1RnPVfPFSVtvOaJKmwxNmUdz'
            plan.save()
            updates.append(f"{plan.name} updated")
            
            # Professional
            plan = SubscriptionPlan.objects.get(slug='professional')
            plan.stripe_price_id_monthly = 'price_1RkeQgPFSVtvOaJKgPOzW1SD'
            plan.stripe_price_id_yearly = 'price_1RnPVRPFSVtvOaJKIWxiSHfm'
            plan.save()
            updates.append(f"{plan.name} updated")
            
            # Enterprise
            plan = SubscriptionPlan.objects.get(slug='enterprise')
            plan.stripe_price_id_monthly = 'price_1RkeVLPFSVtvOaJKY5efgwca'
            plan.stripe_price_id_yearly = 'price_1RnPV8PFSVtvOaJKoiZxvjPa'
            plan.save()
            updates.append(f"{plan.name} updated")
            
            return Response({
                'success': True,
                'updates': updates,
                'message': 'Stripe price IDs updated successfully!'
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=500)