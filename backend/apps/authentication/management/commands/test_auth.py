"""
Test authentication flow and diagnose issues
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Test authentication flow and diagnose issues'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🔍 Testing Authentication System\n'))
        
        # 1. Check JWT settings
        self.stdout.write('1️⃣ JWT Settings:')
        self.stdout.write(f'   ACCESS_TOKEN_LIFETIME: {settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME")}')
        self.stdout.write(f'   REFRESH_TOKEN_LIFETIME: {settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME")}')
        self.stdout.write(f'   JWT_COOKIE_SECURE: {getattr(settings, "JWT_COOKIE_SECURE", "Not set")}')
        self.stdout.write(f'   JWT_COOKIE_SAMESITE: {getattr(settings, "JWT_COOKIE_SAMESITE", "Not set")}')
        self.stdout.write(f'   JWT_ACCESS_COOKIE_NAME: {getattr(settings, "JWT_ACCESS_COOKIE_NAME", "Not set")}')
        self.stdout.write(f'   JWT_REFRESH_COOKIE_NAME: {getattr(settings, "JWT_REFRESH_COOKIE_NAME", "Not set")}\n')
        
        # 2. Check if user exists
        self.stdout.write('2️⃣ Checking user:')
        email = 'arabel.bebel@hotmail.com'
        try:
            user = User.objects.get(email=email)
            self.stdout.write(self.style.SUCCESS(f'   ✅ User found: {user.email}'))
            self.stdout.write(f'   - ID: {user.id}')
            self.stdout.write(f'   - Is active: {user.is_active}')
            # self.stdout.write(f'   - Is verified: {user.is_email_verified}')  # Field removed in migration
            self.stdout.write(f'   - Email verification: Disabled (field removed)')
            self.stdout.write(f'   - Company: {getattr(user, "company", "No company")}\n')
            
            # 3. Generate test tokens
            self.stdout.write('3️⃣ Generating test tokens:')
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            self.stdout.write(self.style.SUCCESS('   ✅ Tokens generated successfully'))
            self.stdout.write(f'   - Access token length: {len(str(access_token))}')
            self.stdout.write(f'   - Refresh token length: {len(str(refresh))}\n')
            
            # 4. Check authentication backends
            self.stdout.write('4️⃣ Authentication backends:')
            for backend in settings.AUTHENTICATION_BACKENDS:
                self.stdout.write(f'   - {backend}')
            
            # 5. Check REST framework authentication
            self.stdout.write('\n5️⃣ REST Framework Authentication:')
            for auth_class in settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', []):
                self.stdout.write(f'   - {auth_class}')
            
            # 6. CORS settings
            self.stdout.write('\n6️⃣ CORS Settings:')
            self.stdout.write(f'   CORS_ALLOWED_ORIGINS: {getattr(settings, "CORS_ALLOWED_ORIGINS", [])}')
            self.stdout.write(f'   CORS_ALLOW_CREDENTIALS: {getattr(settings, "CORS_ALLOW_CREDENTIALS", False)}')
            
            self.stdout.write(self.style.SUCCESS('\n✅ Authentication system check complete!\n'))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'   ❌ User not found: {email}'))
            self.stdout.write('   Please ensure the user is registered.')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error: {str(e)}'))