#!/usr/bin/env python3
"""
Test script to validate JWT keys from backup file
"""
import os
import sys
import base64
import django
from pathlib import Path

# Setup Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

def test_jwt_keys():
    """Test JWT keys from the backup file"""
    print("🔐 Testing JWT Keys from Backup File")
    print("=" * 50)
    
    # Read keys from backup file
    backup_file = Path(__file__).parent / "jwt_keys_backup.txt"
    
    if not backup_file.exists():
        print("❌ Backup file not found: jwt_keys_backup.txt")
        return
    
    print(f"✅ Backup file found: {backup_file}")
    
    # Parse the backup file
    try:
        with open(backup_file, 'r') as f:
            content = f.read()
        
        private_key_b64 = None
        public_key_b64 = None
        
        for line in content.split('\n'):
            if line.startswith('JWT_PRIVATE_KEY_B64='):
                private_key_b64 = line.split('=', 1)[1]
            elif line.startswith('JWT_PUBLIC_KEY_B64='):
                public_key_b64 = line.split('=', 1)[1]
        
        if not private_key_b64 or not public_key_b64:
            print("❌ Could not find JWT keys in backup file")
            return
        
        print(f"✅ Private key B64 length: {len(private_key_b64)} chars")
        print(f"✅ Public key B64 length: {len(public_key_b64)} chars")
        print(f"✅ Private key starts with: {private_key_b64[:20]}...")
        print(f"✅ Public key starts with: {public_key_b64[:20]}...")
        
        # Test base64 decoding
        try:
            private_key = base64.b64decode(private_key_b64).decode('utf-8')
            public_key = base64.b64decode(public_key_b64).decode('utf-8')
            print("✅ Base64 decoding successful")
            
            print(f"✅ Decoded private key length: {len(private_key)} chars")
            print(f"✅ Decoded public key length: {len(public_key)} chars")
            
            # Validate PEM format
            private_valid = private_key.startswith('-----BEGIN PRIVATE KEY-----')
            public_valid = public_key.startswith('-----BEGIN PUBLIC KEY-----')
            
            print(f"✅ Private key PEM format: {'Valid' if private_valid else 'INVALID'}")
            print(f"✅ Public key PEM format: {'Valid' if public_valid else 'INVALID'}")
            
            if not private_valid or not public_valid:
                print("❌ Keys are not in valid PEM format!")
                return
            
            # Test JWT operations with PyJWT
            try:
                import jwt
                
                # Test payload
                payload = {
                    'user_id': 123,
                    'exp': 9999999999  # Far future
                }
                
                # Sign token
                token = jwt.encode(payload, private_key, algorithm='RS256')
                print(f"✅ Token generation successful: {token[:50]}...")
                
                # Verify token
                decoded = jwt.decode(token, public_key, algorithms=['RS256'])
                print(f"✅ Token verification successful: {decoded}")
                
                print("\n🎉 ALL JWT KEY TESTS PASSED!")
                print("✅ Keys are valid and ready for production use")
                
                # Test with Django settings
                print("\n🔧 Testing with Django JWT settings...")
                from core.security import load_jwt_keys, get_jwt_private_key, get_jwt_public_key
                
                # Temporarily set environment variables
                os.environ['JWT_PRIVATE_KEY_B64'] = private_key_b64
                os.environ['JWT_PUBLIC_KEY_B64'] = public_key_b64
                
                print("✅ Environment variables set temporarily")
                
                # Test Django functions
                django_private, django_public = load_jwt_keys()
                
                if django_private == private_key and django_public == public_key:
                    print("✅ Django JWT functions working correctly")
                else:
                    print("❌ Django JWT functions returned different keys")
                
            except ImportError:
                print("⚠️  PyJWT not installed, skipping JWT operations test")
            except Exception as e:
                print(f"❌ JWT operations failed: {e}")
                import traceback
                print(traceback.format_exc())
                
        except Exception as e:
            print(f"❌ Base64 decoding failed: {e}")
            import traceback
            print(traceback.format_exc())
            
    except Exception as e:
        print(f"❌ Failed to read backup file: {e}")

if __name__ == "__main__":
    test_jwt_keys()