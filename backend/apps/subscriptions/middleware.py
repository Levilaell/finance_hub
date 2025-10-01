"""
Subscription verification middleware
"""
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


class SubscriptionRequiredMiddleware:
    """
    Middleware to verify user has active subscription before accessing protected routes
    """

    # Paths that don't require subscription verification
    EXEMPT_PATHS = [
        '/api/auth/',
        '/api/subscriptions/',
        '/api/subscriptions/webhooks/',
        '/admin/',
        '/subscription/expired',
        '/checkout',
        '/pricing',
        '/register',
        '/login',
    ]

    # Additional paths allowed when subscription is expired or not created
    ALLOWED_WHEN_NO_SUBSCRIPTION = [
        '/checkout',
        '/pricing',
        '/settings',
        '/api/subscriptions/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip if user is not authenticated
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Skip if path is exempt
        if self.is_exempt_path(request.path):
            return self.get_response(request)

        # Skip for superusers
        if request.user.is_superuser:
            return self.get_response(request)

        # Check if user has ANY subscription (even if expired)
        from djstripe.models import Subscription
        has_any_subscription = Subscription.objects.filter(
            customer__subscriber=request.user
        ).exists()

        # User has NO subscription at all (new user who didn't complete checkout)
        if not has_any_subscription:
            # Allow checkout flow
            if self.is_allowed_without_subscription(request.path):
                return self.get_response(request)

            # Block access and redirect to checkout
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Subscription required. Please complete checkout.',
                    'code': 'CHECKOUT_REQUIRED',
                    'redirect': '/checkout'
                }, status=402)
            else:
                return redirect('/checkout')

        # User has subscription but it's not active (expired/canceled/past_due)
        if not request.user.has_active_subscription:
            # Allow certain paths even when subscription is expired
            if self.is_allowed_without_subscription(request.path):
                return self.get_response(request)

            # Block access
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Active subscription required',
                    'code': 'SUBSCRIPTION_REQUIRED',
                    'redirect': '/subscription/expired'
                }, status=402)
            else:
                return redirect('/subscription/expired')

        return self.get_response(request)

    def is_exempt_path(self, path):
        """Check if path is exempt from subscription verification"""
        return any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS)

    def is_allowed_without_subscription(self, path):
        """Check if path is allowed when user has no subscription"""
        return any(path.startswith(allowed) for allowed in self.ALLOWED_WHEN_NO_SUBSCRIPTION)
