"""
Test JWT fix for production environment
"""
import jwt
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from core.security import get_jwt_private_key, get_jwt_public_key


class Command(BaseCommand):
    help = 'Test JWT key parsing fix for production'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.stdout.write("🔧 Testing JWT Key Parsing Fix")
        self.stdout.write("=" * 50)

        success_count = 0
        total_tests = 5

        # Test 1: Key Loading
        self.stdout.write("\n1. Testing JWT key loading...")
        try:
            private_key = get_jwt_private_key()
            public_key = get_jwt_public_key()
            
            if self.verbose:
                self.stdout.write(f"   Private key length: {len(private_key)} chars")
                self.stdout.write(f"   Public key length: {len(public_key)} chars")
            
            self.stdout.write(self.style.SUCCESS("   ✅ Key loading: SUCCESS"))
            success_count += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Key loading: FAILED - {e}"))

        # Test 2: SIMPLE_JWT Settings
        self.stdout.write("\n2. Testing SIMPLE_JWT settings...")
        try:
            jwt_private = settings.SIMPLE_JWT.get('SIGNING_KEY')
            jwt_public = settings.SIMPLE_JWT.get('VERIFYING_KEY')
            
            if jwt_private and jwt_public:
                if self.verbose:
                    self.stdout.write(f"   SIGNING_KEY available: {bool(jwt_private)}")
                    self.stdout.write(f"   VERIFYING_KEY available: {bool(jwt_public)}")
                
                self.stdout.write(self.style.SUCCESS("   ✅ SIMPLE_JWT settings: SUCCESS"))
                success_count += 1
            else:
                self.stdout.write(self.style.ERROR("   ❌ SIMPLE_JWT settings: MISSING KEYS"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ SIMPLE_JWT settings: FAILED - {e}"))

        # Test 3: Token Encoding
        self.stdout.write("\n3. Testing JWT token encoding...")
        try:
            private_key = get_jwt_private_key()
            test_payload = {
                'test': 'payload',
                'user_id': 123,
                'exp': datetime.utcnow() + timedelta(minutes=1)
            }
            
            token = jwt.encode(test_payload, private_key, algorithm='RS256')
            
            if self.verbose:
                self.stdout.write(f"   Token preview: {token[:50]}...")
            
            self.stdout.write(self.style.SUCCESS("   ✅ Token encoding: SUCCESS"))
            success_count += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Token encoding: FAILED - {e}"))

        # Test 4: Token Decoding
        self.stdout.write("\n4. Testing JWT token decoding...")
        try:
            private_key = get_jwt_private_key()
            public_key = get_jwt_public_key()
            
            test_payload = {
                'test': 'payload',
                'user_id': 123,
                'exp': datetime.utcnow() + timedelta(minutes=1)
            }
            
            # Encode
            token = jwt.encode(test_payload, private_key, algorithm='RS256')
            
            # Decode
            decoded = jwt.decode(token, public_key, algorithms=['RS256'])
            
            if self.verbose:
                self.stdout.write(f"   Decoded payload: {decoded}")
            
            if decoded['test'] == 'payload' and decoded['user_id'] == 123:
                self.stdout.write(self.style.SUCCESS("   ✅ Token decoding: SUCCESS"))
                success_count += 1
            else:
                self.stdout.write(self.style.ERROR("   ❌ Token decoding: PAYLOAD MISMATCH"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Token decoding: FAILED - {e}"))

        # Test 5: Authentication Class
        self.stdout.write("\n5. Testing JWT authentication class...")
        try:
            from apps.authentication.authentication import JWTCookieAuthentication
            
            auth_class = JWTCookieAuthentication()
            
            if hasattr(auth_class, 'get_validated_token'):
                self.stdout.write(self.style.SUCCESS("   ✅ Authentication class: SUCCESS"))
                success_count += 1
            else:
                self.stdout.write(self.style.ERROR("   ❌ Authentication class: MISSING METHODS"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Authentication class: FAILED - {e}"))

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("🎯 TEST SUMMARY")
        self.stdout.write("=" * 50)
        
        if success_count == total_tests:
            self.stdout.write(self.style.SUCCESS(f"✅ ALL TESTS PASSED ({success_count}/{total_tests})"))
            self.stdout.write(self.style.SUCCESS("🚀 JWT authentication is ready for production!"))
        else:
            failed_count = total_tests - success_count
            self.stdout.write(self.style.ERROR(f"❌ {failed_count} TESTS FAILED ({success_count}/{total_tests})"))
            self.stdout.write(self.style.ERROR("🚨 JWT authentication needs attention!"))

        # Version info
        self.stdout.write(f"\n📋 Library versions:")
        self.stdout.write(f"   PyJWT: {jwt.__version__}")
        
        try:
            import cryptography
            self.stdout.write(f"   Cryptography: {cryptography.__version__}")
        except ImportError:
            self.stdout.write("   Cryptography: Not available")

        self.stdout.write(f"   Django settings: {settings.SETTINGS_MODULE}")
        self.stdout.write(f"   Algorithm: {settings.SIMPLE_JWT.get('ALGORITHM', 'Not set')}")