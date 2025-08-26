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
    
    # Run JWT authentication diagnostics on startup (production only)
    if os.environ.get('DJANGO_ENV') == 'production':
        try:
            import django
            django.setup()
            from django.core.management import call_command
            from io import StringIO
            
            # Capture diagnostic output
            output = StringIO()
            print("🔐 Running JWT Authentication diagnostics during WSGI startup...")
            call_command('diagnose_jwt_auth', '--fix-permissions', stdout=output, stderr=output)
            diag_output = output.getvalue()
            
            # Parse and log critical issues
            for line in diag_output.split('\n'):
                if '❌' in line:
                    print(f"🚨 CRITICAL AUTH ERROR: {line}")
                elif '⚠️' in line:
                    print(f"⚠️ AUTH WARNING: {line}")
                elif '✅' in line and ('JWT' in line or 'Token' in line or 'Cookie' in line):
                    print(f"✅ AUTH OK: {line}")
                    
        except Exception as diag_error:
            print(f"⚠️ JWT diagnostics failed during WSGI startup: {diag_error}")
    
except Exception as e:
    print(f"CRITICAL ERROR during Django startup: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    
    # Create a minimal WSGI application that returns error info
    def application(environ, start_response):
        path = environ.get('PATH_INFO', '')
        
        # For health check endpoints, return JSON with error details
        if path in ['/health/', '/api/health/']:
            import json
            status = '500 Internal Server Error'
            response_data = {
                "status": "initialization_failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "Django failed to initialize during WSGI startup",
                "environment": {
                    "DJANGO_SETTINGS_MODULE": os.environ.get('DJANGO_SETTINGS_MODULE', 'not set'),
                    "DATABASE_URL": "configured" if os.environ.get('DATABASE_URL') else "missing",
                    "DJANGO_SECRET_KEY": "configured" if os.environ.get('DJANGO_SECRET_KEY') else "missing",
                    "OPENAI_API_KEY": "configured" if os.environ.get('OPENAI_API_KEY') else "missing",
                    "DJANGO_ENV": os.environ.get('DJANGO_ENV', 'not set')
                },
                "traceback": traceback.format_exc()[-1500:]  # Last 1500 chars of traceback
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
<p>Django initialization failed: {str(e)}</p>
</body>
</html>"""
            return [error_html.encode('utf-8')]
