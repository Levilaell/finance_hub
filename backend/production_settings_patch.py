#!/usr/bin/env python3
"""
PRODUCTION SETTINGS PATCH FOR AUTHENTICATION CRISIS
===================================================

This script applies the necessary configuration changes to fix the authentication
crisis in production. It updates the production.py settings file with the correct
cookie configurations for mobile Safari and cross-origin compatibility.

CRITICAL CHANGES:
1. SESSION_COOKIE_SAMESITE = 'None' (for mobile Safari)
2. SESSION_SAVE_EVERY_REQUEST = False (prevent race conditions)
3. Consistent cookie security settings

Usage:
    python production_settings_patch.py --apply
    python production_settings_patch.py --preview
"""

import os
import sys
import re
from datetime import datetime

def apply_production_patch():
    """Apply the production settings patch"""
    
    settings_file = "core/settings/production.py"
    backup_file = f"core/settings/production.py.backup.{int(datetime.now().timestamp())}"
    
    if not os.path.exists(settings_file):
        print(f"❌ Settings file not found: {settings_file}")
        return False
    
    print("🔧 APPLYING PRODUCTION SETTINGS PATCH")
    print("=" * 45)
    
    # Read current settings
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Create backup
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"✅ Backup created: {backup_file}")
    
    # Define the patch
    patch_config = """
# ===== SESSION CONFIGURATION - MOBILE SAFARI COMPATIBLE =====
# Fix for authentication crisis: session corruption and mobile Safari issues
SESSION_COOKIE_SAMESITE = 'None'    # Match JWT cookies for mobile Safari
SESSION_COOKIE_SECURE = True        # Required when SameSite=None
SESSION_SAVE_EVERY_REQUEST = False  # Prevent race conditions that cause corruption
SESSION_COOKIE_AGE = 86400          # 24 hours (not 7 days to prevent stale sessions)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Allow persistent sessions"""
    
    # Find where to insert the patch
    # Look for existing SESSION_ENGINE line
    session_engine_pattern = r'SESSION_ENGINE\s*=.*'
    
    if re.search(session_engine_pattern, content):
        # Insert after SESSION_ENGINE configuration
        content = re.sub(
            r'(SESSION_ENGINE\s*=.*\n)(SESSION_COOKIE_AGE\s*=.*\n)?(SESSION_SAVE_EVERY_REQUEST\s*=.*\n)?',
            r'\1' + patch_config + '\n\n',
            content,
            flags=re.MULTILINE
        )
        print("✅ Patch applied after SESSION_ENGINE")
    else:
        # Insert before the Channels section
        channels_pattern = r'# Channels'
        if re.search(channels_pattern, content):
            content = re.sub(
                r'(# Channels)',
                patch_config + '\n\n' + r'\1',
                content
            )
            print("✅ Patch applied before Channels section")
        else:
            # Append at the end
            content += '\n' + patch_config + '\n'
            print("✅ Patch appended at end of file")
    
    # Apply additional fixes
    
    # Update JWT cookie configuration comment
    jwt_comment_old = "# Mobile Safari compatibility: Use SameSite=None for cross-origin requests"
    jwt_comment_new = "# Mobile Safari + Session compatibility: Use SameSite=None for cross-origin requests"
    content = content.replace(jwt_comment_old, jwt_comment_new)
    
    # Ensure SESSION_COOKIE_AGE is not set to 7 days (conflict fix)
    content = re.sub(
        r'SESSION_COOKIE_AGE\s*=\s*86400\s*\*\s*7.*',
        'SESSION_COOKIE_AGE = 86400  # 24 hours (authentication fix)',
        content
    )
    
    # Write the patched settings
    with open(settings_file, 'w') as f:
        f.write(content)
    
    print("✅ Production settings patched successfully")
    print("\n📋 CHANGES APPLIED:")
    print("• SESSION_COOKIE_SAMESITE = 'None' (mobile Safari)")
    print("• SESSION_COOKIE_SECURE = True (security)")
    print("• SESSION_SAVE_EVERY_REQUEST = False (race condition fix)")
    print("• SESSION_COOKIE_AGE = 86400 (24h, not 7 days)")
    print("• SESSION_EXPIRE_AT_BROWSER_CLOSE = False")
    
    print(f"\n💾 Original backed up to: {backup_file}")
    
    return True

def preview_patch():
    """Preview what the patch will do"""
    print("👀 PREVIEW: Production Settings Patch")
    print("=" * 40)
    
    print("The following changes will be applied:\n")
    
    print("1. Add mobile Safari compatible session settings:")
    print("   SESSION_COOKIE_SAMESITE = 'None'")
    print("   SESSION_COOKIE_SECURE = True")
    print("   SESSION_SAVE_EVERY_REQUEST = False")
    print("   SESSION_COOKIE_AGE = 86400")
    print("   SESSION_EXPIRE_AT_BROWSER_CLOSE = False")
    
    print("\n2. Fix race condition that causes session corruption")
    print("3. Ensure consistent cookie policy for JWT and Session")
    print("4. Create backup of current production.py")
    
    print("\n⚠️  IMPORTANT:")
    print("• Restart Railway app after applying patch")
    print("• Monitor logs for 'Session data corrupted' warnings")
    print("• Test login with mobile Safari/Chrome iOS")
    
    print("\nTo apply: python production_settings_patch.py --apply")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--apply':
            success = apply_production_patch()
            if success:
                print("\n🚀 NEXT STEPS:")
                print("1. Restart Railway application")
                print("2. Run session cleanup: python fix_production_authentication.py --emergency-fix")
                print("3. Test login on mobile browser")
                print("4. Monitor logs for improvements")
            else:
                print("\n❌ Patch failed. Check file permissions and paths.")
        elif sys.argv[1] == '--preview':
            preview_patch()
        else:
            print("Usage:")
            print("  python production_settings_patch.py --preview")
            print("  python production_settings_patch.py --apply")
    else:
        preview_patch()

if __name__ == '__main__':
    main()