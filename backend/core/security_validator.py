"""
Security Configuration Validator for Finance Hub
Validates critical security settings before application startup
"""
import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class SecurityValidator:
    """Validates critical security configurations"""
    
    @staticmethod
    def validate_production_security():
        """
        Validates security settings required for production deployment.
        Raises ImproperlyConfigured if any critical settings are missing or insecure.
        """
        errors = []
        warnings = []
        
        # 1. SECRET_KEY validation
        if not getattr(settings, 'SECRET_KEY', None):
            errors.append("SECRET_KEY is not set")
        elif settings.SECRET_KEY == 'INSECURE-TEMPORARY-KEY-PLEASE-SET-DJANGO_SECRET_KEY':
            errors.append("SECRET_KEY is using temporary insecure value")
        elif len(settings.SECRET_KEY) < 50:
            warnings.append("SECRET_KEY should be at least 50 characters long")
        
        # 2. Debug mode validation
        if getattr(settings, 'DEBUG', False):
            errors.append("DEBUG must be False in production")
        
        # 3. Allowed hosts validation
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        if not allowed_hosts or allowed_hosts == ['*']:
            warnings.append("ALLOWED_HOSTS should be configured with specific domains")
        
        # 4. Database security
        db_config = getattr(settings, 'DATABASES', {}).get('default', {})
        if db_config.get('ENGINE') == 'django.db.backends.sqlite3':
            warnings.append("SQLite should not be used in production")
        
        # 5. SSL/HTTPS validation
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            warnings.append("SECURE_SSL_REDIRECT should be True in production")
        
        # 6. Session security
        if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
            warnings.append("SESSION_COOKIE_SECURE should be True in production")
        
        if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
            warnings.append("CSRF_COOKIE_SECURE should be True in production")
        
        # 7. Stripe configuration (if using Stripe)
        if getattr(settings, 'DEFAULT_PAYMENT_GATEWAY', '') == 'stripe':
            stripe_settings = {
                'STRIPE_SECRET_KEY': getattr(settings, 'STRIPE_SECRET_KEY', ''),
                'STRIPE_PUBLIC_KEY': getattr(settings, 'STRIPE_PUBLIC_KEY', ''),
                'STRIPE_WEBHOOK_SECRET': getattr(settings, 'STRIPE_WEBHOOK_SECRET', ''),
            }
            
            missing_stripe = [name for name, value in stripe_settings.items() if not value]
            if missing_stripe:
                errors.append(f"Missing Stripe configuration: {', '.join(missing_stripe)}")
        
        # 8. Webhook security
        pluggy_webhook_secret = getattr(settings, 'PLUGGY_WEBHOOK_SECRET', '')
        if not pluggy_webhook_secret:
            warnings.append("PLUGGY_WEBHOOK_SECRET should be set for webhook security")
        
        # 9. Rate limiting
        if not hasattr(settings, 'REST_FRAMEWORK'):
            warnings.append("REST_FRAMEWORK throttling should be configured")
        
        return errors, warnings
    
    @staticmethod
    def validate_development_setup():
        """
        Validates development environment setup.
        Returns suggestions for missing configurations.
        """
        suggestions = []
        
        # Check if common development tools are configured
        if not getattr(settings, 'STRIPE_SECRET_KEY', ''):
            suggestions.append("Set STRIPE_SECRET_KEY for payment testing")
        
        if not getattr(settings, 'OPENAI_API_KEY', ''):
            suggestions.append("Set OPENAI_API_KEY for AI features")
        
        if not getattr(settings, 'PLUGGY_CLIENT_ID', ''):
            suggestions.append("Set PLUGGY_CLIENT_ID for banking integration")
        
        return suggestions
    
    @staticmethod
    def get_security_report():
        """
        Generate a comprehensive security report.
        Returns dict with errors, warnings, and suggestions.
        """
        is_production = not getattr(settings, 'DEBUG', True)
        
        if is_production:
            errors, warnings = SecurityValidator.validate_production_security()
            suggestions = []
        else:
            errors = []
            warnings = []
            suggestions = SecurityValidator.validate_development_setup()
        
        return {
            'environment': 'production' if is_production else 'development',
            'errors': errors,
            'warnings': warnings,
            'suggestions': suggestions,
            'is_secure': len(errors) == 0
        }


def validate_security_on_startup():
    """
    Validates security configuration on application startup.
    Prints warnings and errors, raises exception for critical errors.
    """
    try:
        report = SecurityValidator.get_security_report()
        
        if report['errors']:
            error_msg = "\n".join([
                "🚨 CRITICAL SECURITY ERRORS:",
                *[f"   • {error}" for error in report['errors']],
                "",
                "Application cannot start with these security issues.",
                "Please fix the configuration and restart."
            ])
            raise ImproperlyConfigured(error_msg)
        
        if report['warnings']:
            print("\n⚠️  SECURITY WARNINGS:")
            for warning in report['warnings']:
                print(f"   • {warning}")
            print()
        
        if report['suggestions'] and report['environment'] == 'development':
            print("💡 DEVELOPMENT SUGGESTIONS:")
            for suggestion in report['suggestions']:
                print(f"   • {suggestion}")
            print()
        
        if report['environment'] == 'production' and report['is_secure']:
            print("✅ SECURITY VALIDATION PASSED - Production ready")
        
    except Exception as e:
        # Don't break startup for validation errors, just log them
        print(f"⚠️  Security validation error: {e}")