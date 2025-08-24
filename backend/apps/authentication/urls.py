from django.urls import path
from django.conf import settings

from .views import (
    ChangePasswordView,
    CustomTokenRefreshView,
    DeleteAccountView,
    EarlyAccessRegisterView,
    # EmailVerificationView,  # Will be implemented in the future
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterView,
    # ResendVerificationView,  # Will be implemented in the future
    Setup2FAView,
    Enable2FAView,
    Disable2FAView,
)

# Import debug views for mobile troubleshooting
if settings.DEBUG:
    from .mobile_debug_views import MobileCookieDebugView, MobileAuthTestView

# Import troubleshooting views (available in production for urgent debugging)
from .mobile_troubleshoot_view import MobileTroubleshootView
from .emergency_cookie_test import EmergencyCookieTestView
from .simple_cookie_test import SimpleCookieTestView, immediate_cookie_test
from .jwt_size_test import JWTSizeTestView
from .mobile_fallback_auth import MobileAuthFallbackView, TokenValidationView
from .mobile_debug_endpoint import MobileSafariDebugView, QuickAuthTestView

app_name = 'authentication'

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('early-access/register/', EarlyAccessRegisterView.as_view(), name='early_access_register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    
    # Password reset
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Email verification - will be implemented in the future
    # path('verify-email/', EmailVerificationView.as_view(), name='verify_email'),
    # path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),
    
    # 2FA endpoints
    path('2fa/setup/', Setup2FAView.as_view(), name='setup_2fa'),
    path('2fa/enable/', Enable2FAView.as_view(), name='enable_2fa'),
    path('2fa/disable/', Disable2FAView.as_view(), name='disable_2fa'),
    
    # Mobile troubleshooting endpoints (available in production for critical debugging)
    path('troubleshoot/mobile/', MobileTroubleshootView.as_view(), name='mobile_troubleshoot'),
    path('emergency/cookie-test/', EmergencyCookieTestView.as_view(), name='emergency_cookie_test'),
    path('simple/cookie-test/', SimpleCookieTestView.as_view(), name='simple_cookie_test'),
    path('immediate/cookie-test/', immediate_cookie_test, name='immediate_cookie_test'),
    path('jwt-size-test/', JWTSizeTestView.as_view(), name='jwt_size_test'),
    
    # Multi-strategy authentication fallback (available in production)
    path('mobile-auth-fallback/', MobileAuthFallbackView.as_view(), name='mobile_auth_fallback'),
    path('validate-token/', TokenValidationView.as_view(), name='validate_token'),
    
    # Debug endpoints for frontend testing (available in production for urgent debugging)
    path('debug/mobile-safari-test/', MobileSafariDebugView.as_view(), name='mobile_safari_debug'),
    path('debug/quick-auth-test/', QuickAuthTestView.as_view(), name='quick_auth_test'),
]

# Debug endpoints only in development
if settings.DEBUG:
    urlpatterns += [
        # Mobile cookie debugging endpoints
        path('debug/mobile-cookies/', MobileCookieDebugView.as_view(), name='mobile_cookie_debug'),
        path('debug/mobile-auth/', MobileAuthTestView.as_view(), name='mobile_auth_test'),
    ]