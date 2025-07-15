"""
Payment URLs
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Checkout endpoints
    path('checkout/create/', views.CreateCheckoutSessionView.as_view(), name='create-checkout'),
    path('checkout/validate/', views.ValidatePaymentView.as_view(), name='validate-payment'),
    
    # Webhook endpoints
    path('webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),
    path('webhooks/mercadopago/', views.mercadopago_webhook, name='mercadopago-webhook'),
]