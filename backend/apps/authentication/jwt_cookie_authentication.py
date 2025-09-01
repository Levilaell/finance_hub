"""
POISON PILL - FORCE RAILWAY TO REBUILD
This file intentionally breaks if the old authentication is used
"""

# If this file is imported, it means Railway is still using cached code
# This will force an immediate error and rebuild

raise ImportError(
    "🚨 CRITICAL ERROR: jwt_cookie_authentication.py should not exist! "
    "Railway is using cached/stale code. This file was intentionally removed. "
    "System must use simplified JWTAuthentication only. "
    "Deploy timestamp: 2025-09-01T12:00:00Z - FORCE REBUILD REQUIRED"
)