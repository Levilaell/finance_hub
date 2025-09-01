#!/usr/bin/env python3
"""
FORCE HS256 PRODUCTION CONFIG
Override all JWT configurations to use HS256 only
"""
import os
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
django.setup()

def force_hs256_config():
    """Force HS256 configuration in production"""
    from django.conf import settings
    
    print("🔧 FORCING HS256 CONFIGURATION")
    print("=" * 40)
    
    # Check current config
    jwt_config = settings.SIMPLE_JWT
    algorithm = jwt_config.get('ALGORITHM')
    signing_key = jwt_config.get('SIGNING_KEY')
    
    print(f"Current Algorithm: {algorithm}")
    print(f"Signing Key Length: {len(str(signing_key))}")
    
    # Override JWT configuration at runtime
    new_jwt_config = {
        'ACCESS_TOKEN_LIFETIME': jwt_config.get('ACCESS_TOKEN_LIFETIME'),
        'REFRESH_TOKEN_LIFETIME': jwt_config.get('REFRESH_TOKEN_LIFETIME'),
        'ROTATE_REFRESH_TOKENS': True,
        'BLACKLIST_AFTER_ROTATION': True,
        'UPDATE_LAST_LOGIN': True,
        'ALGORITHM': 'HS256',  # FORCE HS256
        'SIGNING_KEY': os.environ.get('JWT_SECRET_KEY') or os.environ.get('DJANGO_SECRET_KEY'),
        'AUTH_HEADER_TYPES': ('Bearer',),
        'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
        'USER_ID_FIELD': 'id',
        'USER_ID_CLAIM': 'user_id',
    }
    
    # Override settings
    settings.SIMPLE_JWT = new_jwt_config
    
    print("✅ JWT configuration overridden to HS256")
    print(f"New Algorithm: {settings.SIMPLE_JWT['ALGORITHM']}")
    
    # Test token creation
    try:
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        test_user = User.objects.first()
        
        if test_user:
            refresh = RefreshToken.for_user(test_user)
            access = str(refresh.access_token)
            
            print(f"✅ Token creation successful")
            print(f"Access token length: {len(access)}")
            print(f"Token starts with: {access[:20]}...")
        else:
            print("⚠️  No users found for token test")
            
    except Exception as e:
        print(f"❌ Token creation failed: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = force_hs256_config()
    if success:
        print("\n🎉 HS256 CONFIGURATION FORCED")
        print("🚀 System should now use HS256 tokens")
    else:
        print("\n❌ Configuration override failed")