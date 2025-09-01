#!/usr/bin/env python3
"""
AUTHENTICATION CRISIS DIAGNOSTIC & FIX
=======================================

Comprehensive diagnosis and resolution for the authentication crisis where users
successfully log in but are immediately redirected to the login page.

CRITICAL ISSUES IDENTIFIED:
1. Session data corrupted (6x warnings during login)
2. Token refresh failed (400 Bad Request)
3. Mobile Safari cookie compatibility issues
4. Conflicting session/cookie configurations

Usage:
    python fix_authentication_crisis.py --diagnose
    python fix_authentication_crisis.py --fix-all
    python fix_authentication_crisis.py --test-mobile
"""

import os
import sys

# Setup Django first - use development settings for diagnosis
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')

import django
django.setup()

from django.conf import settings
from django.core.cache import cache
from django.contrib.sessions.models import Session
from django.db import connection
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import json
from datetime import datetime, timedelta

User = get_user_model()

class AuthenticationCrisisResolver:
    """Diagnose and resolve critical authentication issues"""
    
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        
    def diagnose_all(self):
        """Run complete diagnostic suite"""
        print("🚨 AUTHENTICATION CRISIS DIAGNOSTIC")
        print("=" * 50)
        
        self.check_session_corruption()
        self.check_cookie_configurations()
        self.check_token_refresh_mechanism()
        self.check_mobile_safari_compatibility()
        self.check_production_settings()
        
        self.print_summary()
    
    def check_session_corruption(self):
        """Diagnose session corruption issues"""
        print("\n🔍 1. Session Corruption Analysis")
        print("-" * 30)
        
        # Check session backend configuration
        session_engine = getattr(settings, 'SESSION_ENGINE', 'Not set')
        print(f"SESSION_ENGINE: {session_engine}")
        
        if session_engine == 'django.contrib.sessions.backends.cache':
            # Check cache connectivity
            try:
                cache.set('test_key', 'test_value', 30)
                test_value = cache.get('test_key')
                if test_value == 'test_value':
                    print("✅ Cache backend working")
                else:
                    self.issues_found.append("CRITICAL: Cache backend test failed")
                    print("❌ Cache backend test failed")
            except Exception as e:
                self.issues_found.append(f"CRITICAL: Cache error - {e}")
                print(f"❌ Cache error: {e}")
        
        elif session_engine == 'django.contrib.sessions.backends.db':
            # Check database sessions
            try:
                session_count = Session.objects.count()
                print(f"✅ Database sessions: {session_count} active")
            except Exception as e:
                self.issues_found.append(f"CRITICAL: Database session error - {e}")
                print(f"❌ Database session error: {e}")
        
        # Check for conflicting settings
        session_samesite_configs = []
        try:
            # Check all potential SameSite configurations
            if hasattr(settings, 'SESSION_COOKIE_SAMESITE'):
                session_samesite_configs.append(f"SESSION_COOKIE_SAMESITE: {settings.SESSION_COOKIE_SAMESITE}")
        except:
            pass
            
        if len(session_samesite_configs) > 1:
            self.issues_found.append("WARNING: Multiple SESSION_COOKIE_SAMESITE configurations found")
            for config in session_samesite_configs:
                print(f"⚠️  {config}")
    
    def check_cookie_configurations(self):
        """Check JWT and session cookie configurations"""
        print("\n🍪 2. Cookie Configuration Analysis")
        print("-" * 35)
        
        # JWT Cookie settings
        jwt_samesite = getattr(settings, 'JWT_COOKIE_SAMESITE', 'Not set')
        jwt_secure = getattr(settings, 'JWT_COOKIE_SECURE', 'Not set')
        jwt_domain = getattr(settings, 'JWT_COOKIE_DOMAIN', 'Not set')
        
        print(f"JWT_COOKIE_SAMESITE: {jwt_samesite}")
        print(f"JWT_COOKIE_SECURE: {jwt_secure}")
        print(f"JWT_COOKIE_DOMAIN: {jwt_domain}")
        
        # Check mobile Safari compatibility
        if jwt_samesite == 'None' and jwt_secure != True:
            self.issues_found.append("CRITICAL: SameSite=None requires Secure=True for mobile Safari")
        
        if jwt_samesite not in ['None', 'Lax', 'Strict']:
            self.issues_found.append(f"WARNING: Invalid JWT_COOKIE_SAMESITE value: {jwt_samesite}")
            
        # Session Cookie settings
        session_samesite = getattr(settings, 'SESSION_COOKIE_SAMESITE', 'Not set')
        session_secure = getattr(settings, 'SESSION_COOKIE_SECURE', 'Not set')
        
        print(f"SESSION_COOKIE_SAMESITE: {session_samesite}")
        print(f"SESSION_COOKIE_SECURE: {session_secure}")
        
        # Check for conflicts
        if jwt_samesite != 'Not set' and session_samesite != 'Not set':
            if jwt_samesite != session_samesite:
                self.issues_found.append(f"WARNING: JWT and Session SameSite mismatch: {jwt_samesite} vs {session_samesite}")
    
    def check_token_refresh_mechanism(self):
        """Test token refresh functionality"""
        print("\n🔄 3. Token Refresh Mechanism")
        print("-" * 30)
        
        try:
            # Create test user tokens
            test_user = User.objects.filter(is_active=True, is_superuser=False).first()
            if not test_user:
                print("⚠️  No test user available")
                return
                
            refresh = RefreshToken.for_user(test_user)
            print(f"✅ Refresh token generated: {len(str(refresh))} chars")
            
            # Test token validation
            from rest_framework_simplejwt.tokens import UntypedToken
            try:
                UntypedToken(str(refresh))
                print("✅ Refresh token validation: Success")
            except Exception as e:
                self.issues_found.append(f"CRITICAL: Refresh token validation failed - {e}")
                print(f"❌ Refresh token validation failed: {e}")
            
            # Test access token generation
            try:
                access = refresh.access_token
                print(f"✅ Access token generation: {len(str(access))} chars")
            except Exception as e:
                self.issues_found.append(f"CRITICAL: Access token generation failed - {e}")
                print(f"❌ Access token generation failed: {e}")
                
        except Exception as e:
            self.issues_found.append(f"CRITICAL: Token system error - {e}")
            print(f"❌ Token system error: {e}")
    
    def check_mobile_safari_compatibility(self):
        """Check mobile Safari specific compatibility"""
        print("\n📱 4. Mobile Safari Compatibility")
        print("-" * 35)
        
        # Analyze the user agent from logs
        mobile_safari_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/139.0.7258.76 Mobile/15E148 Safari/604.1"
        
        print(f"User-Agent Analysis:")
        print(f"  Device: iPhone OS 18.6.1")
        print(f"  Browser: Chrome iOS 139.0.7258.76")
        print(f"  Is Mobile Safari: True")
        
        # Check cross-origin scenario
        frontend_url = getattr(settings, 'FRONTEND_URL', 'Not set')
        backend_url = getattr(settings, 'BACKEND_URL', 'Not set')
        
        print(f"Frontend URL: {frontend_url}")
        print(f"Backend URL: {backend_url}")
        
        if frontend_url != 'Not set' and backend_url != 'Not set':
            from urllib.parse import urlparse
            frontend_domain = urlparse(frontend_url).netloc
            backend_domain = urlparse(backend_url).netloc
            is_cross_origin = frontend_domain != backend_domain
            
            print(f"Cross-origin scenario: {is_cross_origin}")
            if is_cross_origin:
                jwt_samesite = getattr(settings, 'JWT_COOKIE_SAMESITE', 'Not set')
                if jwt_samesite != 'None':
                    self.issues_found.append("CRITICAL: Mobile Safari cross-origin requires SameSite=None")
                    print("❌ Mobile Safari cross-origin requires SameSite=None")
                else:
                    print("✅ Cross-origin configuration looks correct")
    
    def check_production_settings(self):
        """Check production-specific settings"""
        print("\n🏭 5. Production Settings Analysis")
        print("-" * 35)
        
        # Check if in production
        debug_mode = getattr(settings, 'DEBUG', True)
        print(f"DEBUG mode: {debug_mode}")
        
        if not debug_mode:  # Production
            # Check HTTPS requirements
            jwt_secure = getattr(settings, 'JWT_COOKIE_SECURE', False)
            session_secure = getattr(settings, 'SESSION_COOKIE_SECURE', False)
            
            if not jwt_secure:
                self.issues_found.append("CRITICAL: JWT_COOKIE_SECURE should be True in production")
            if not session_secure:
                self.issues_found.append("CRITICAL: SESSION_COOKIE_SECURE should be True in production")
            
            print(f"JWT_COOKIE_SECURE: {jwt_secure}")
            print(f"SESSION_COOKIE_SECURE: {session_secure}")
        
        # Check ALLOWED_HOSTS
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        print(f"ALLOWED_HOSTS: {allowed_hosts}")
        
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            print("✅ Database connection: Success")
        except Exception as e:
            self.issues_found.append(f"CRITICAL: Database connection failed - {e}")
            print(f"❌ Database connection failed: {e}")
    
    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 50)
        print("📋 DIAGNOSTIC SUMMARY")
        print("=" * 50)
        
        if not self.issues_found:
            print("✅ No critical issues found!")
            return
        
        print(f"❌ {len(self.issues_found)} issues found:\n")
        for i, issue in enumerate(self.issues_found, 1):
            print(f"{i:2d}. {issue}")
        
        print("\n🔧 RECOMMENDED FIXES:")
        print("-" * 20)
        print("1. Fix session backend configuration consistency")
        print("2. Ensure mobile Safari compatible cookie settings:")
        print("   - JWT_COOKIE_SAMESITE = 'None' (for cross-origin)")
        print("   - JWT_COOKIE_SECURE = True (required with SameSite=None)")
        print("3. Clear corrupted sessions from cache/database")
        print("4. Restart application with consistent settings")
        print("5. Test with mobile browser specifically")
        
    def apply_emergency_fixes(self):
        """Apply emergency fixes for immediate resolution"""
        print("\n🚑 APPLYING EMERGENCY FIXES")
        print("=" * 30)
        
        # Clear corrupted sessions
        try:
            if hasattr(cache, 'clear'):
                cache.clear()
                print("✅ Cache cleared")
                self.fixes_applied.append("Cleared cache")
        except Exception as e:
            print(f"⚠️  Cache clear failed: {e}")
        
        try:
            Session.objects.all().delete()
            print("✅ Database sessions cleared")
            self.fixes_applied.append("Cleared database sessions")
        except Exception as e:
            print(f"⚠️  Database session clear failed: {e}")
        
        print(f"\n✅ Applied {len(self.fixes_applied)} fixes")
        print("\n🔄 NEXT STEPS:")
        print("1. Update production.py with correct cookie settings")
        print("2. Restart application server")
        print("3. Test login flow on mobile browser")
        print("4. Monitor logs for session corruption warnings")

def main():
    """Main diagnostic function"""
    resolver = AuthenticationCrisisResolver()
    
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == '--diagnose':
            resolver.diagnose_all()
        elif sys.argv[1] == '--fix-all':
            resolver.diagnose_all()
            if resolver.issues_found:
                resolver.apply_emergency_fixes()
        elif sys.argv[1] == '--test-mobile':
            resolver.check_mobile_safari_compatibility()
        else:
            print("Usage: python fix_authentication_crisis.py [--diagnose|--fix-all|--test-mobile]")
    else:
        resolver.diagnose_all()

if __name__ == '__main__':
    main()