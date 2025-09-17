from django.urls import path
from .views import (
    CreateCheckoutSessionView,
    ValidatePaymentView,
    CancelSubscriptionView,
    StripeWebhookView,
)

app_name = 'payments'

urlpatterns = [
    path('checkout/create/', CreateCheckoutSessionView.as_view()),
    path('checkout/validate/', ValidatePaymentView.as_view()),
    path('subscription/cancel/', CancelSubscriptionView.as_view()),
    path('webhook/stripe/', StripeWebhookView.as_view()),
]