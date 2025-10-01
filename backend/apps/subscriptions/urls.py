"""
Subscription URLs
"""
from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # Subscription management
    path('checkout/', views.create_checkout_session, name='checkout'),
    path('status/', views.subscription_status, name='status'),
    path('portal/', views.create_portal_session, name='portal'),
    path('config/', views.stripe_config, name='config'),

    # Note: Webhook handling is done via djstripe.urls in core/urls.py
    # Webhook URL pattern: /stripe/webhook/<uuid>/
]
