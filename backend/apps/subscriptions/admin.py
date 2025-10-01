"""
Admin interface for subscriptions management

dj-stripe automatically registers Customer and Subscription models.
Access them at /admin/ under the "Djstripe" section.

To manage subscriptions:
1. Go to /admin/djstripe/subscription/
2. Use filters to find subscriptions by status
3. Click on a subscription to view/edit
4. Use Stripe Dashboard for advanced operations

To cancel a subscription programmatically:
- Use the Stripe Dashboard Customer Portal
- Or use the services.cancel_subscription() function
"""

# dj-stripe handles all admin registration automatically
# Models available in admin:
# - Customer
# - Subscription
# - Price
# - Product
# - PaymentMethod
# - Invoice
# - Charge
# - etc.

