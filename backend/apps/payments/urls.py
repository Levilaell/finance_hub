from django.urls import path
from .views import (
    SubscriptionPlanListView,
    SubscriptionStatusView,
    CreateCheckoutSessionView,
    ValidatePaymentView,
    PaymentMethodListCreateView,
    PaymentMethodDetailView,
    PaymentHistoryView,
    CancelSubscriptionView,
    StripeWebhookView,
)
from .health_checks import (
    PaymentHealthCheckView,
    PaymentMetricsView,
    PaymentAlertsView,
)
from .views_subscription import (
    SubscriptionChangePlanView,
    SubscriptionProrationView,
    SubscriptionUsageLimitsView,
)

app_name = 'payments'

urlpatterns = [
    # Subscription plans
    path('plans/', SubscriptionPlanListView.as_view(), name='plan-list'),
    
    # Subscription management
    path('subscription/status/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('subscription/cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('subscription/change-plan/', SubscriptionChangePlanView.as_view(), name='change-plan'),
    path('subscription/calculate-proration/', SubscriptionProrationView.as_view(), name='calculate-proration'),
    path('subscription/usage-limits/', SubscriptionUsageLimitsView.as_view(), name='usage-limits'),
    
    # Checkout flow
    path('checkout/create/', CreateCheckoutSessionView.as_view(), name='create-checkout'),
    path('checkout/validate/', ValidatePaymentView.as_view(), name='validate-payment'),
    
    # Payment methods
    path('payment-methods/', PaymentMethodListCreateView.as_view(), name='payment-method-list'),
    path('payment-methods/<int:pk>/', PaymentMethodDetailView.as_view(), name='payment-method-detail'),
    
    # Payment history
    path('payments/', PaymentHistoryView.as_view(), name='payment-history'),
    
    
    # Webhooks
    path('webhooks/stripe/', StripeWebhookView.as_view(), name='stripe-webhook'),
    
    # Health checks and monitoring
    path('health/', PaymentHealthCheckView.as_view(), name='health-check'),
    path('metrics/', PaymentMetricsView.as_view(), name='metrics'),
    path('alerts/', PaymentAlertsView.as_view(), name='alerts'),
]