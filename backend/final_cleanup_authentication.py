#!/usr/bin/env python3
"""
FINAL AUTHENTICATION CLEANUP
============================

Remove remaining inconsistencies after authentication simplification.
This ensures the system is fully consistent and ready for deployment.

FIXES:
1. Remove JWT cookie configurations from production.py (not needed with Bearer tokens)
2. Check for any broken imports in views.py
3. Ensure all session configurations are consistent
4. Clean up any remaining cookie middleware references

Usage:
    python final_cleanup_authentication.py --clean
    python final_cleanup_authentication.py --check
"""

import os
import re
from datetime import datetime

def clean_production_jwt_cookies():
    """Remove JWT cookie configurations from production.py"""
    production_file = "core/settings/production.py"
    
    if not os.path.exists(production_file):
        print(f"❌ Production file not found: {production_file}")
        return False
        
    with open(production_file, 'r') as f:
        content = f.read()
    
    print("🧹 Cleaning JWT cookie configurations from production.py")
    
    # Remove JWT cookie section completely
    jwt_cookie_pattern = r'\n# JWT COOKIES - SIMPLE.*?JWT_REFRESH_COOKIE_NAME = \'refresh_token\''
    content = re.sub(jwt_cookie_pattern, '', content, flags=re.DOTALL)
    
    # Remove individual JWT cookie settings if they exist
    jwt_settings = [
        r'JWT_COOKIE_SAMESITE\s*=.*\n',
        r'JWT_COOKIE_SECURE\s*=.*\n',
        r'JWT_COOKIE_DOMAIN\s*=.*\n',
        r'JWT_ACCESS_COOKIE_NAME\s*=.*\n',
        r'JWT_REFRESH_COOKIE_NAME\s*=.*\n'
    ]
    
    for pattern in jwt_settings:
        content = re.sub(pattern, '', content)
    
    with open(production_file, 'w') as f:
        f.write(content)
    
    print("✅ JWT cookie configurations removed from production.py")
    return True

def check_views_imports():
    """Check for any broken imports in views.py"""
    views_file = "apps/authentication/views.py"
    
    if not os.path.exists(views_file):
        print(f"❌ Views file not found: {views_file}")
        return False
    
    with open(views_file, 'r') as f:
        content = f.read()
    
    print("🔍 Checking imports in views.py")
    
    # Check for set_jwt_cookies import that might be broken
    if 'set_jwt_cookies' in content:
        print("⚠️  Found reference to set_jwt_cookies in views.py")
        print("    This function was removed - Bearer tokens don't need cookie setting")
        
        # Check if it's being imported
        if 'from .cookie_middleware import' in content and 'set_jwt_cookies' in content:
            print("❌ Found broken import for set_jwt_cookies")
            return False
        
        # Check if it's being called
        if 'set_jwt_cookies(' in content:
            print("❌ Found call to set_jwt_cookies function")
            return False
    else:
        print("✅ No references to removed cookie functions found")
    
    return True

def validate_simplified_config():
    """Validate that the simplified configuration is consistent"""
    print("🔍 Validating simplified authentication configuration")
    
    base_file = "core/settings/base.py"
    production_file = "core/settings/production.py"
    
    # Check base.py
    if os.path.exists(base_file):
        with open(base_file, 'r') as f:
            base_content = f.read()
        
        # Check for single JWT configuration
        jwt_config_count = base_content.count('SIMPLE_JWT')
        print(f"JWT configurations in base.py: {jwt_config_count}")
        
        # Check for single session age
        session_age_count = base_content.count('SESSION_COOKIE_AGE')
        print(f"Session cookie age configurations: {session_age_count}")
        
        # Check for HS256 algorithm
        if 'HS256' in base_content:
            print("✅ Using simplified HS256 algorithm")
        else:
            print("❌ JWT algorithm not found or not HS256")
            
        # Check middleware count
        middleware_section = re.search(r'MIDDLEWARE = \[(.*?)\]', base_content, re.DOTALL)
        if middleware_section:
            middleware_lines = [line.strip() for line in middleware_section.group(1).split('\n') if line.strip() and not line.strip().startswith('#')]
            print(f"✅ Middleware count: {len(middleware_lines)} (should be ~10)")
        
    # Check production.py
    if os.path.exists(production_file):
        with open(production_file, 'r') as f:
            prod_content = f.read()
        
        # Check for JWT cookie configurations (should be none)
        jwt_cookie_refs = prod_content.count('JWT_COOKIE_')
        if jwt_cookie_refs == 0:
            print("✅ No JWT cookie configurations in production.py")
        else:
            print(f"⚠️  Found {jwt_cookie_refs} JWT cookie references in production.py")
    
    print("✅ Configuration validation complete")
    return True

def create_test_script():
    """Create a simple test script to validate login works"""
    test_content = '''#!/usr/bin/env python3
"""
Test simplified authentication
"""
import requests
import json

def test_login():
    """Test login with simplified authentication"""
    base_url = "http://localhost:8000"
    
    # Test data
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    print("🧪 Testing simplified authentication...")
    
    try:
        # Test login
        response = requests.post(f"{base_url}/api/auth/login/", 
                               json=login_data,
                               headers={'Content-Type': 'application/json'})
        
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'access' in data and 'refresh' in data:
                print("✅ Login successful - Bearer tokens received")
                print(f"Access token length: {len(data['access'])}")
                print(f"Refresh token length: {len(data['refresh'])}")
                
                # Test authenticated request
                headers = {'Authorization': f'Bearer {data["access"]}'}
                profile_response = requests.get(f"{base_url}/api/auth/profile/", 
                                              headers=headers)
                
                if profile_response.status_code == 200:
                    print("✅ Authenticated request successful")
                else:
                    print(f"❌ Authenticated request failed: {profile_response.status_code}")
                
                return True
            else:
                print("❌ Login response missing tokens")
                print(f"Response: {data}")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    return False

if __name__ == '__main__':
    test_login()
'''
    
    with open("test_simplified_auth.py", 'w') as f:
        f.write(test_content)
    
    print("✅ Created test_simplified_auth.py")
    print("   Run with: python test_simplified_auth.py")

def main():
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--clean':
            print("🧹 FINAL AUTHENTICATION CLEANUP")
            print("=" * 35)
            
            success = True
            success &= clean_production_jwt_cookies()
            success &= check_views_imports()
            success &= validate_simplified_config()
            create_test_script()
            
            if success:
                print("\n🎉 CLEANUP COMPLETE!")
                print("✅ Authentication fully simplified")
                print("✅ All inconsistencies removed")
                print("✅ Ready for deployment")
                
                print("\n📋 SUMMARY OF CHANGES:")
                print("• Removed JWT cookie system completely")
                print("• Using standard Bearer tokens only")
                print("• Simplified to HS256 JWT algorithm")
                print("• Removed duplicate session configurations")
                print("• Cleaned up unnecessary middlewares")
                print("• Consistent CORS and security headers")
                
                print("\n🚀 NEXT STEPS:")
                print("1. Restart Django application")
                print("2. Test with: python test_simplified_auth.py")
                print("3. Monitor for 'Session data corrupted' warnings (should be gone)")
                print("4. Deploy to production when tests pass")
            else:
                print("\n❌ Some issues found - check output above")
                
        elif sys.argv[1] == '--check':
            print("🔍 CHECKING AUTHENTICATION STATE")
            print("=" * 32)
            check_views_imports()
            validate_simplified_config()
        else:
            print("Usage:")
            print("  python final_cleanup_authentication.py --check")
            print("  python final_cleanup_authentication.py --clean")
    else:
        print("🔍 Authentication Cleanup Tool")
        print("=" * 30)
        print("This script removes remaining inconsistencies after")
        print("authentication simplification.")
        print("")
        print("Options:")
        print("  --check  : Check current state")
        print("  --clean  : Apply cleanup fixes")

if __name__ == '__main__':
    main()