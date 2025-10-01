"""
Subscription URLs
"""
from django.urls import path
from djstripe.views import ProcessWebhookView
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # Subscription management
    path('checkout/', views.create_checkout_session, name='checkout'),
    path('status/', views.subscription_status, name='status'),
    path('portal/', views.create_portal_session, name='portal'),
    path('config/', views.stripe_config, name='config'),

    # dj-stripe webhook (direct view instead of include)
    path('webhooks/stripe/', ProcessWebhookView.as_view(), name='stripe_webhook'),
]
