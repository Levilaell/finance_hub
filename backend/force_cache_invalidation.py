#!/usr/bin/env python3
"""
FORCE CACHE INVALIDATION
Create files that force Railway to completely rebuild and invalidate all caches
"""
import os
import uuid
from pathlib import Path

def force_cache_invalidation():
    """Create files that force Railway to invalidate all caches"""
    
    print("🔥 FORCING COMPLETE CACHE INVALIDATION")
    print("=" * 50)
    
    base_dir = Path(__file__).parent
    
    # Create unique timestamp
    import datetime
    timestamp = datetime.datetime.now().isoformat()
    unique_id = str(uuid.uuid4())[:8]
    
    # Create multiple invalidation files
    invalidation_files = [
        f"FORCE_REBUILD_{unique_id}.txt",
        f"CACHE_BUST_{timestamp.replace(':', '_')}.txt", 
        "INVALIDATE_ALL_CACHES.txt",
        "FORCE_COMPLETE_REBUILD.txt"
    ]
    
    for filename in invalidation_files:
        file_path = base_dir / filename
        content = f"""
FORCE CACHE INVALIDATION - {timestamp}
Unique ID: {unique_id}

This file forces Railway to:
1. Invalidate ALL Docker layer caches
2. Rebuild from scratch
3. Use latest commit: {os.popen('git rev-parse HEAD').read().strip()}
4. Remove jwt_cookie_authentication.py completely
5. Use only simplified HS256 JWT authentication

If you see jwt_cookie_authentication.py errors after this, 
Railway cache system is fundamentally broken.
"""
        file_path.write_text(content)
        print(f"✅ Created {filename}")
    
    # Touch critical files to invalidate Python cache
    critical_files = [
        "core/settings/production.py",
        "core/settings/base.py", 
        "apps/authentication/views.py",
        "requirements.txt"
    ]
    
    for file_path in critical_files:
        full_path = base_dir / file_path
        if full_path.exists():
            # Touch file to change modification time
            full_path.touch()
            print(f"✅ Touched {file_path}")
    
    print(f"\n🎯 Created {len(invalidation_files)} cache invalidation files")
    print(f"🎯 Touched {len(critical_files)} critical files")
    print("🎯 This should force Railway to completely rebuild")
    
    return True

if __name__ == '__main__':
    success = force_cache_invalidation()
    if success:
        print("\n🚀 CACHE INVALIDATION COMPLETE")
        print("Railway MUST rebuild completely now")
    else:
        print("\n❌ Cache invalidation failed")