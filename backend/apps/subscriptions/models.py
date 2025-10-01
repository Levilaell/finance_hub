"""
Subscription models - Using dj-stripe models instead of custom models
"""
from django.db import models

# We use dj-stripe models (Customer, Subscription, PaymentMethod)
# No custom models needed - dj-stripe handles everything
