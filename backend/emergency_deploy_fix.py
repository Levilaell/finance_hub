#!/usr/bin/env python3
"""
EMERGENCY DEPLOY FIX
Remove ALL references to jwt_cookie_authentication to force clean production deploy
"""

import os
import shutil
from pathlib import Path

def emergency_cleanup():
    """Remove all problematic files that could cause import errors"""
    
    print("🚨 EMERGENCY CLEANUP - Removing all jwt_cookie references")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    
    # Remove diagnostic commands that have broken imports
    management_dir = base_dir / 'apps' / 'authentication' / 'management' / 'commands'
    
    problematic_files = [
        'diagnose_jwt_auth.py',
        'test_jwt_fix.py'
    ]
    
    for file_name in problematic_files:
        file_path = management_dir / file_name
        if file_path.exists():
            # Move to backup instead of delete
            backup_path = file_path.with_suffix('.py.broken')
            shutil.move(str(file_path), str(backup_path))
            print(f"✅ Moved {file_name} to {backup_path.name}")
        else:
            print(f"ℹ️  {file_name} already removed")
    
    # Double-check jwt_cookie_authentication.py is gone
    jwt_file = base_dir / 'apps' / 'authentication' / 'jwt_cookie_authentication.py'
    if jwt_file.exists():
        jwt_file.unlink()
        print("✅ Removed jwt_cookie_authentication.py")
    else:
        print("✅ jwt_cookie_authentication.py already removed")
    
    # Verify no problematic imports remain
    print("\n🔍 Verifying cleanup...")
    
    import subprocess
    result = subprocess.run([
        'grep', '-r', '--include=*.py', 
        'jwt_cookie_authentication', str(base_dir)
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("⚠️  Still found references:")
        for line in result.stdout.strip().split('\n')[:5]:  # Show first 5
            print(f"   {line}")
        return False
    else:
        print("✅ No jwt_cookie_authentication references found")
        return True

if __name__ == '__main__':
    success = emergency_cleanup()
    if success:
        print("\n🎉 EMERGENCY CLEANUP COMPLETE")
        print("🚀 Ready for clean deployment")
    else:
        print("\n❌ Some issues remain - check output above")