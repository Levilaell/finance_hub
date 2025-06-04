"""
Payment URLs
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Webhook endpoints
    path('webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),
    path('webhooks/mercadopago/', views.mercadopago_webhook, name='mercadopago-webhook'),
]