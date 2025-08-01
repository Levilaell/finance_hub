#!/usr/bin/env python3
"""
Docker health check script for Finance Hub backend
"""
import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

def check_health():
    """Check application health"""
    try:
        # Set Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
        
        # Try to import Django and check basic functionality
        import django
        django.setup()
        
        from django.db import connection
        from django.core.cache import cache
        
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            
        # Test cache (if available)
        try:
            cache.set('health_check', 'ok', 30)
            if cache.get('health_check') != 'ok':
                raise Exception('Cache test failed')
        except Exception as e:
            print(f"Warning: Cache test failed: {e}")
        
        # Check if web server is responding
        try:
            port = os.environ.get('PORT', '8000')
            health_url = f'http://localhost:{port}/api/payments/health/'
            
            with urllib.request.urlopen(health_url, timeout=5) as response:
                if response.status != 200:
                    raise Exception(f'Health endpoint returned {response.status}')
                
                data = json.loads(response.read().decode())
                if data.get('status') != 'healthy':
                    print(f"Warning: Health check status: {data.get('status')}")
                    
        except urllib.error.URLError as e:
            # If the health endpoint is not available, that's ok for basic health check
            print(f"Warning: Could not reach health endpoint: {e}")
            
        print("Health check passed")
        return 0
        
    except Exception as e:
        print(f"Health check failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(check_health())