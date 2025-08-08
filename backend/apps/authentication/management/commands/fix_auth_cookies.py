"""
Fix authentication cookies issue
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.conf import settings
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Test and fix authentication cookies issue'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🔧 Testing Authentication Flow\n'))
        
        # Create test client
        client = Client()
        
        # Test data
        email = 'arabel.bebel@hotmail.com'
        password = 'Levi123*'
        
        # 1. Test login
        self.stdout.write('1️⃣ Testing login endpoint...')
        login_response = client.post(
            '/api/auth/login/',
            data=json.dumps({'email': email, 'password': password}),
            content_type='application/json'
        )
        
        if login_response.status_code == 200:
            self.stdout.write(self.style.SUCCESS('   ✅ Login successful'))
            
            # Check cookies
            self.stdout.write('\n2️⃣ Checking cookies set by login:')
            for cookie_name, cookie in client.cookies.items():
                self.stdout.write(f'   🍪 {cookie_name}: {str(cookie.value)[:50]}...')
                self.stdout.write(f'      - HttpOnly: {cookie.get("httponly", False)}')
                self.stdout.write(f'      - Secure: {cookie.get("secure", False)}')
                self.stdout.write(f'      - SameSite: {cookie.get("samesite", "Not set")}')
                self.stdout.write(f'      - Path: {cookie.get("path", "/")}')
            
            # 3. Test reports endpoint
            self.stdout.write('\n3️⃣ Testing reports endpoint with cookies...')
            reports_response = client.get('/api/reports/reports/')
            
            if reports_response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('   ✅ Reports endpoint accessible!'))
                data = json.loads(reports_response.content)
                self.stdout.write(f'   📊 Found {len(data.get("results", []))} reports')
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Reports endpoint returned: {reports_response.status_code}'))
                self.stdout.write(f'   Response: {reports_response.content.decode()}')
            
            # 4. Debug authentication
            self.stdout.write('\n4️⃣ Debug information:')
            self.stdout.write(f'   - User authenticated: {client.session.get("_auth_user_id") is not None}')
            self.stdout.write(f'   - Session key: {client.session.session_key}')
            self.stdout.write(f'   - CORS origins: {settings.CORS_ALLOWED_ORIGINS}')
            self.stdout.write(f'   - Cookie settings:')
            self.stdout.write(f'     - JWT_COOKIE_SECURE: {getattr(settings, "JWT_COOKIE_SECURE", "Not set")}')
            self.stdout.write(f'     - JWT_COOKIE_SAMESITE: {getattr(settings, "JWT_COOKIE_SAMESITE", "Not set")}')
            
        else:
            self.stdout.write(self.style.ERROR(f'   ❌ Login failed: {login_response.status_code}'))
            self.stdout.write(f'   Response: {login_response.content.decode()}')