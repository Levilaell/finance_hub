"""WebSocket routing for payment consumers"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # General payment status updates
    re_path(r'ws/payments/status/$', consumers.PaymentStatusConsumer.as_asgi()),
    
    # Checkout session specific updates
    re_path(r'ws/payments/checkout/(?P<session_id>[\w-]+)/$', consumers.PaymentCheckoutConsumer.as_asgi()),
]