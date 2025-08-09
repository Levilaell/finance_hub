"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys

# Add better error handling for production
try:
    # Set default settings module - use environment-based selection
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        # Default to production if DJANGO_ENV is set to production
        if os.environ.get('DJANGO_ENV') == 'production':
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
        else:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    
    # Print startup information
    print(f"Starting Django with settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print(f"Python version: {sys.version}")
    print(f"DATABASE_URL configured: {'Yes' if os.environ.get('DATABASE_URL') else 'No'}")
    print(f"DJANGO_SECRET_KEY configured: {'Yes' if os.environ.get('DJANGO_SECRET_KEY') else 'No'}")
    
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    
except Exception as e:
    print(f"CRITICAL ERROR during Django startup: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    
    # Create a minimal WSGI application that returns error info
    def application(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-Type', 'text/plain')]
        start_response(status, response_headers)
        error_message = f"Django startup failed: {str(e)}\n"
        error_message += "Please check Railway logs for details.\n"
        error_message += f"Missing DATABASE_URL: {not bool(os.environ.get('DATABASE_URL'))}\n"
        error_message += f"Missing DJANGO_SECRET_KEY: {not bool(os.environ.get('DJANGO_SECRET_KEY'))}\n"
        return [error_message.encode('utf-8')]
