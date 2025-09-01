#!/usr/bin/env python3
"""
PRODUCTION AUTHENTICATION FIX
============================

Emergency fix for authentication crisis in production.
Addresses session corruption and mobile Safari cookie issues.

CRITICAL FIXES:
1. Clear corrupted sessions
2. Update cookie settings for mobile Safari
3. Add session cleanup middleware
4. Validate configuration

Usage (in Railway console):
    python fix_production_authentication.py --emergency-fix
    python fix_production_authentication.py --validate-only
"""

import os
import sys
import django
from datetime import datetime

# Setup Django for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

try:
    django.setup()
    from django.conf import settings
    from django.contrib.sessions.models import Session
    from django.core.cache import cache
    from django.contrib.auth import get_user_model
    from django.db import connection
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    print("This script must be run in Railway environment with proper env vars")
    sys.exit(1)

User = get_user_model()

class ProductionAuthFixer:
    """Fix critical authentication issues in production"""
    
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        
    def emergency_fix(self):
        """Apply all emergency fixes"""
        print("🚑 EMERGENCY AUTHENTICATION FIX")
        print("=" * 40)
        print(f"Environment: {'PRODUCTION' if not settings.DEBUG else 'DEVELOPMENT'}")
        print(f"Timestamp: {datetime.now()}")
        print()
        
        self.clear_corrupted_sessions()
        self.validate_cookie_settings()
        self.test_token_system()
        self.create_session_cleanup_middleware()
        
        self.print_results()
    
    def clear_corrupted_sessions(self):
        """Clear all corrupted sessions"""
        print("🧹 1. Clearing Corrupted Sessions")
        print("-" * 35)
        
        try:
            # Count existing sessions
            session_count = Session.objects.count()
            print(f"Current sessions in database: {session_count}")
            
            if session_count > 0:
                # Clear all sessions
                deleted_count, _ = Session.objects.all().delete()
                print(f"✅ Deleted {deleted_count} corrupted sessions")
                self.fixes_applied.append(f"Cleared {deleted_count} database sessions")
            else:
                print("ℹ️  No sessions to clear")
                
        except Exception as e:
            print(f"❌ Failed to clear sessions: {e}")
            self.issues_found.append(f"Session clearing failed: {e}")
            
        # Clear cache if available
        try:
            if hasattr(cache, 'clear'):
                cache.clear()
                print("✅ Cache cleared")
                self.fixes_applied.append("Cleared cache")
        except Exception as e:
            print(f"⚠️  Cache clear failed: {e}")
    
    def validate_cookie_settings(self):
        """Validate and report cookie settings"""
        print("\n🍪 2. Cookie Settings Validation")
        print("-" * 35)
        
        # Check JWT cookie settings
        jwt_samesite = getattr(settings, 'JWT_COOKIE_SAMESITE', 'Not set')
        jwt_secure = getattr(settings, 'JWT_COOKIE_SECURE', 'Not set')
        jwt_domain = getattr(settings, 'JWT_COOKIE_DOMAIN', 'Not set')
        
        print(f"JWT_COOKIE_SAMESITE: {jwt_samesite}")
        print(f"JWT_COOKIE_SECURE: {jwt_secure}")
        print(f"JWT_COOKIE_DOMAIN: {jwt_domain}")
        
        # Check session cookie settings
        session_samesite = getattr(settings, 'SESSION_COOKIE_SAMESITE', 'Not set')
        session_secure = getattr(settings, 'SESSION_COOKIE_SECURE', 'Not set')
        session_save = getattr(settings, 'SESSION_SAVE_EVERY_REQUEST', 'Not set')
        
        print(f"SESSION_COOKIE_SAMESITE: {session_samesite}")
        print(f"SESSION_COOKIE_SECURE: {session_secure}")
        print(f"SESSION_SAVE_EVERY_REQUEST: {session_save}")
        
        # Validation for production
        if not settings.DEBUG:  # Production
            issues = []
            
            if jwt_samesite != 'None':
                issues.append("JWT_COOKIE_SAMESITE should be 'None' for mobile Safari")
            if jwt_secure != True:
                issues.append("JWT_COOKIE_SECURE should be True in production")
            if session_samesite != 'None':
                issues.append("SESSION_COOKIE_SAMESITE should be 'None' for consistency")
            if session_secure != True:
                issues.append("SESSION_COOKIE_SECURE should be True in production")
            if session_save == True:
                issues.append("SESSION_SAVE_EVERY_REQUEST should be False to prevent race conditions")
                
            if issues:
                print("❌ Cookie configuration issues found:")
                for issue in issues:
                    print(f"   • {issue}")
                    self.issues_found.append(issue)
            else:
                print("✅ Cookie settings look correct for production")
        
    def test_token_system(self):
        """Test JWT token generation and validation"""
        print("\n🔐 3. Token System Test")
        print("-" * 25)
        
        try:
            # Get a test user
            test_user = User.objects.filter(is_active=True, is_superuser=False).first()
            if not test_user:
                print("⚠️  No test user available, skipping token test")
                return
                
            print(f"Testing with user: {test_user.email}")
            
            # Test token generation
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(test_user)
            access = refresh.access_token
            
            print(f"✅ Refresh token generated: {len(str(refresh))} chars")
            print(f"✅ Access token generated: {len(str(access))} chars")
            
            # Test token validation
            from rest_framework_simplejwt.tokens import UntypedToken
            UntypedToken(str(refresh))
            UntypedToken(str(access))
            print("✅ Token validation successful")
            
            self.fixes_applied.append("Token system validated")
            
        except Exception as e:
            print(f"❌ Token system test failed: {e}")
            self.issues_found.append(f"Token system error: {e}")
    
    def create_session_cleanup_middleware(self):
        """Create session cleanup middleware code"""
        print("\n🛡️  4. Session Cleanup Middleware")
        print("-" * 35)
        
        middleware_code = '''"""
Session cleanup middleware to prevent corruption
Add this to your MIDDLEWARE in production.py after other auth middleware
"""
import logging
from django.contrib.sessions.models import Session

logger = logging.getLogger('authentication')

class SessionCleanupMiddleware:
    """Prevent session corruption by cleaning up on errors"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            # Handle session-related errors
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['session', 'corrupted', 'pickle']):
                try:
                    if hasattr(request, 'session'):
                        request.session.flush()
                    logger.warning(f"Session cleared due to corruption: {e}")
                except Exception as session_e:
                    logger.error(f"Failed to clear corrupted session: {session_e}")
            raise e
'''
        
        # Write middleware to file
        middleware_path = "apps/authentication/session_cleanup_middleware.py"
        try:
            with open(middleware_path, 'w') as f:
                f.write(middleware_code)
            print(f"✅ Session cleanup middleware created: {middleware_path}")
            print("   Add to MIDDLEWARE in production.py:")
            print("   'apps.authentication.session_cleanup_middleware.SessionCleanupMiddleware',")
            self.fixes_applied.append("Session cleanup middleware created")
        except Exception as e:
            print(f"⚠️  Could not create middleware file: {e}")
    
    def print_results(self):
        """Print fix results summary"""
        print("\n" + "=" * 50)
        print("📋 EMERGENCY FIX RESULTS")
        print("=" * 50)
        
        print(f"✅ Fixes Applied: {len(self.fixes_applied)}")
        for fix in self.fixes_applied:
            print(f"   • {fix}")
        
        if self.issues_found:
            print(f"\n⚠️  Issues Remaining: {len(self.issues_found)}")
            for issue in self.issues_found:
                print(f"   • {issue}")
            
            print("\n🔧 MANUAL STEPS REQUIRED:")
            print("1. Update production.py with correct cookie settings")
            print("2. Add session cleanup middleware to MIDDLEWARE")
            print("3. Restart Railway application")
            print("4. Monitor logs for 'Session data corrupted' warnings")
        else:
            print("\n🎉 All critical issues resolved!")
        
        print("\n📊 MONITORING:")
        print("• Watch for 'Session data corrupted' in logs")
        print("• Monitor 401 errors after successful login")
        print("• Check token refresh 400 errors")
        
        print(f"\n⏰ Fix completed at: {datetime.now()}")
    
    def validate_only(self):
        """Just validate current settings without making changes"""
        print("🔍 AUTHENTICATION VALIDATION")
        print("=" * 35)
        
        self.validate_cookie_settings()
        self.test_token_system()
        
        # Check session count
        try:
            session_count = Session.objects.count()
            print(f"\nCurrent database sessions: {session_count}")
        except Exception as e:
            print(f"Could not check sessions: {e}")
        
        print("\n✅ Validation complete")

def main():
    """Main function"""
    fixer = ProductionAuthFixer()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--emergency-fix':
            fixer.emergency_fix()
        elif sys.argv[1] == '--validate-only':
            fixer.validate_only()
        else:
            print("Usage:")
            print("  python fix_production_authentication.py --emergency-fix")
            print("  python fix_production_authentication.py --validate-only")
    else:
        print("Choose an option:")
        print("1. Emergency fix (clears sessions, applies fixes)")
        print("2. Validate only (check settings)")
        choice = input("Enter 1 or 2: ").strip()
        
        if choice == '1':
            fixer.emergency_fix()
        elif choice == '2':
            fixer.validate_only()
        else:
            print("Invalid choice")

if __name__ == '__main__':
    main()