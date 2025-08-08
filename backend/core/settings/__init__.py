"""
Settings module initialization
"""
import os

environment = os.environ.get('DJANGO_ENV', 'development')

if environment == 'production':
    from .production import *
elif environment == 'staging':
    from .staging import *
elif environment == 'test':
    from .test import *
else:
    from .development import *