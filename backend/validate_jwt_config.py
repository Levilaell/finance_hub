#!/usr/bin/env python3
"""
JWT Configuration Validator
Ensures JWT setup is correct after authentication simplification
"""
import os
import sys
import django
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

def validate_jwt_config():
    """Validate JWT configuration and authentication setup"""
    print("🔍 VALIDATING JWT CONFIGURATION")
    print("=" * 40)
    
    # Test Django settings
    from django.conf import settings
    
    print("✅ Django settings loaded")
    
    # Check REST Framework config
    rest_config = settings.REST_FRAMEWORK
    auth_classes = rest_config.get('DEFAULT_AUTHENTICATION_CLASSES', [])
    
    print(f"📋 Authentication classes: {len(auth_classes)}")
    for auth_class in auth_classes:
        print(f"   • {auth_class}")
    
    # Validate only standard JWT auth is used
    expected_auth = 'rest_framework_simplejwt.authentication.JWTAuthentication'
    if expected_auth in auth_classes:
        print("✅ Standard JWT authentication configured")
    else:
        print("❌ Standard JWT authentication NOT found")
        return False
    
    # Check for unwanted custom auth
    custom_jwt_auth = 'apps.authentication.jwt_cookie_authentication.JWTCookieAuthentication'
    if custom_jwt_auth in auth_classes:
        print("❌ Custom JWT cookie authentication still configured")
        return False
    else:
        print("✅ No custom JWT cookie authentication")
    
    # Check JWT settings
    jwt_config = settings.SIMPLE_JWT
    algorithm = jwt_config.get('ALGORITHM')
    
    print(f"🔐 JWT Algorithm: {algorithm}")
    
    if algorithm == 'HS256':
        print("✅ Simplified HS256 algorithm configured")
    else:
        print(f"⚠️  Algorithm is {algorithm}, expected HS256")
    
    # Test JWT token creation
    try:
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        # Try to create a test token (won't work without user, but tests import)
        print("✅ JWT token classes import successfully")
        
    except Exception as e:
        print(f"❌ JWT token creation failed: {e}")
        return False
    
    # Test authentication class
    try:
        from rest_framework_simplejwt.authentication import JWTAuthentication
        auth_instance = JWTAuthentication()
        print("✅ JWT Authentication class instantiated")
        
    except Exception as e:
        print(f"❌ JWT Authentication failed: {e}")
        return False
    
    # Check if old authentication file was removed
    old_auth_file = Path(__file__).parent / 'apps' / 'authentication' / 'jwt_cookie_authentication.py'
    if old_auth_file.exists():
        print("❌ Old jwt_cookie_authentication.py still exists")
        return False
    else:
        print("✅ Old JWT cookie authentication file removed")
    
    print()
    print("🎉 JWT CONFIGURATION VALIDATION PASSED")
    print("✅ Authentication system ready for deployment")
    return True

if __name__ == '__main__':
    success = validate_jwt_config()
    if not success:
        print("\n❌ Validation failed - fix issues before deployment")
        sys.exit(1)
    else:
        print("\n🚀 System ready for deployment")
        sys.exit(0)