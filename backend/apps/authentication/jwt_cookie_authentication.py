"""
ULTRA-AGGRESSIVE POISON PILL v2.0
This file MUST trigger immediate system failure if executed
Multiple layers of failure to catch ANY execution path
"""

import sys
import os

# POISON PILL LAYER 1: Import-time error
def _poison_pill_error():
    error_msg = """
🚨🚨🚨 CRITICAL SYSTEM ERROR 🚨🚨🚨
jwt_cookie_authentication.py SHOULD NOT EXIST OR BE EXECUTED!

TIMESTAMP: 2025-09-01T12:30:00Z
RAILWAY CACHE INVALIDATION: FAILED
SYSTEM STATUS: CORRUPTED

This file was intentionally removed and replaced with simplified authentication.
If you see this error, Railway deployment system is fundamentally broken.

REQUIRED ACTION: Complete system rebuild from scratch
"""
    print(error_msg)
    raise SystemError(error_msg)

# Execute poison pill immediately on import
_poison_pill_error()

# POISON PILL LAYER 2: Class definition with errors
class JWTCookieAuthentication:
    def __init__(self):
        _poison_pill_error()
    
    def authenticate(self, request):
        _poison_pill_error()
    
    def __call__(self, *args, **kwargs):
        _poison_pill_error()

# POISON PILL LAYER 3: Function definition with errors  
def authenticate(*args, **kwargs):
    _poison_pill_error()

# POISON PILL LAYER 4: Module-level execution
if __name__ == "__main__":
    _poison_pill_error()

# POISON PILL LAYER 5: Any attribute access
class PoisonPillModule(type(sys)):
    def __getattr__(self, name):
        _poison_pill_error()
        
# Replace current module with poison pill
sys.modules[__name__] = PoisonPillModule(__name__)

# FINAL POISON PILL: Immediate error
_poison_pill_error()