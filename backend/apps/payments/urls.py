"""
Payment URLs
"""
from django.urls import path
from . import views
from .debug_views import PaymentDebugView
from .temp_update_view import UpdateStripePricesView
from .webhook_test_view import WebhookTestView, CheckWebhookEventsView

app_name = 'payments'

urlpatterns = [
    # Checkout endpoints
    path('checkout/create/', views.CreateCheckoutSessionView.as_view(), name='create-checkout'),
    path('checkout/validate/', views.ValidatePaymentView.as_view(), name='validate-payment'),
    
    # Subscription status
    path('subscription-status/', views.CheckSubscriptionStatusView.as_view(), name='subscription-status'),
    
    # Webhook endpoints
    path('webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),
    path('webhooks/mercadopago/', views.mercadopago_webhook, name='mercadopago-webhook'),
    
    # Debug endpoints (remove in production)
    path('debug/', PaymentDebugView.as_view(), name='payment-debug'),
    path('webhook-test/', WebhookTestView.as_view(), name='webhook-test'),
    path('webhook-events/', CheckWebhookEventsView.as_view(), name='webhook-events'),
    
    # TEMPORARY - REMOVE AFTER USE
    path('update-stripe-prices/', UpdateStripePricesView.as_view(), name='update-stripe-prices'),
]