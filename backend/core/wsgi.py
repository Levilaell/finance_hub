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

    
except Exception as startup_error:
    print(f"CRITICAL ERROR during Django startup: {startup_error}")
    print(f"Error type: {type(startup_error).__name__}")
    import traceback
    traceback.print_exc()
    
    # Capture error details for closure
    error_message = str(startup_error)
    error_type = type(startup_error).__name__
    error_traceback = traceback.format_exc()
    
    # Create a minimal WSGI application that returns error info
    def application(environ, start_response):
        path = environ.get('PATH_INFO', '')
        
        # For health check endpoints, return JSON with error details
        if path in ['/health/', '/api/health/']:
            import json
            status = '500 Internal Server Error'
            response_data = {
                "status": "initialization_failed",
                "error": error_message,
                "error_type": error_type,
                "message": "Django failed to initialize during WSGI startup",
                "environment": {
                    "DJANGO_SETTINGS_MODULE": os.environ.get('DJANGO_SETTINGS_MODULE', 'not set'),
                    "DATABASE_URL": "configured" if os.environ.get('DATABASE_URL') else "missing",
                    "DJANGO_SECRET_KEY": "configured" if os.environ.get('DJANGO_SECRET_KEY') else "missing",
                    "OPENAI_API_KEY": "configured" if os.environ.get('OPENAI_API_KEY') else "missing",
                    "DJANGO_ENV": os.environ.get('DJANGO_ENV', 'not set')
                },
                "traceback": error_traceback[-1500:]  # Last 1500 chars of traceback
            }
            
            response_body = json.dumps(response_data, indent=2).encode('utf-8')
            response_headers = [
                ('Content-Type', 'application/json'),
                ('Content-Length', str(len(response_body)))
            ]
            start_response(status, response_headers)
            return [response_body]
        else:
            # For other paths, return HTML error
            status = '500 Internal Server Error'
            response_headers = [('Content-Type', 'text/html')]
            start_response(status, response_headers)
            error_html = f"""<html>
<head><title>Internal Server Error</title></head>
<body>
<h1><p>Internal Server Error</p></h1>
<p>Django initialization failed: {error_message}</p>
</body>
</html>"""
            return [error_html.encode('utf-8')]
