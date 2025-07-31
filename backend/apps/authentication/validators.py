"""
Enhanced password validators for comprehensive security
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from .security.password_policies import ComprehensivePasswordValidator as BasePasswordValidator


class ComprehensivePasswordValidator:
    """
    Django-compatible wrapper for comprehensive password validation
    """
    
    def __init__(self):
        self.validator = BasePasswordValidator()
    
    def validate(self, password, user=None):
        """
        Validate password against comprehensive security policies
        """
        result = self.validator.validate_password(password, user, check_breaches=True)
        
        if not result['valid']:
            # Convert recommendations to Django validation errors
            errors = []
            
            for recommendation in result['recommendations']:
                errors.append(ValidationError(_(recommendation)))
            
            if errors:
                raise ValidationError(errors)
    
    def password_changed(self, password, user=None):
        """
        Called after password is changed
        """
        if user and hasattr(user, 'add_to_password_history'):
            # Add to password history
            user.add_to_password_history(user.password)
    
    def get_help_text(self):
        """
        Return help text for password requirements
        """
        requirements = self.validator.get_password_requirements()
        
        help_texts = [
            f"Your password must be at least {requirements['min_length']} characters long.",
            "Include uppercase and lowercase letters, numbers, and special characters.",
            "Avoid common passwords and personal information.",
            "Cannot reuse your last 5 passwords.",
        ]
        
        if requirements['check_breaches']:
            help_texts.append("Password will be checked against known data breaches.")
        
        return " ".join(help_texts)


class MinimumStrengthValidator:
    """
    Validator that requires minimum password strength score
    """
    
    def __init__(self, min_score=6):
        self.min_score = min_score
        self.validator = BasePasswordValidator()
    
    def validate(self, password, user=None):
        """
        Validate minimum strength score
        """
        result = self.validator.validate_password(password, user, check_breaches=False)
        
        if result['overall_score'] < self.min_score:
            raise ValidationError(
                _("Password strength is too low. Score: %(score)d/10, minimum required: %(min_score)d/10"),
                params={'score': result['overall_score'], 'min_score': self.min_score}
            )
    
    def get_help_text(self):
        return _(f"Password must have a strength score of at least {self.min_score}/10.")


class NoPersonalInfoValidator:
    """
    Validator that prevents use of personal information in passwords
    """
    
    def validate(self, password, user=None):
        """
        Validate that password doesn't contain personal information
        """
        if not user:
            return
        
        password_lower = password.lower()
        personal_info = []
        
        # Collect personal information
        if hasattr(user, 'email') and user.email:
            personal_info.append(user.email.split('@')[0].lower())
        
        if hasattr(user, 'first_name') and user.first_name:
            personal_info.append(user.first_name.lower())
        
        if hasattr(user, 'last_name') and user.last_name:
            personal_info.append(user.last_name.lower())
        
        if hasattr(user, 'username') and user.username:
            personal_info.append(user.username.lower())
        
        # Check if password contains personal info
        for info in personal_info:
            if len(info) >= 3 and info in password_lower:
                raise ValidationError(
                    _("Password cannot contain personal information like your name or email."),
                )
    
    def get_help_text(self):
        return _("Password cannot contain your personal information such as name or email address.")


class HistoryValidator:
    """
    Validator that prevents password reuse
    """
    
    def __init__(self, history_count=5):
        self.history_count = history_count
    
    def validate(self, password, user=None):
        """
        Validate against password history
        """
        if not user or not hasattr(user, 'password_history'):
            return
        
        from .security.password_policies import PasswordHistoryValidator
        history_validator = PasswordHistoryValidator(self.history_count)
        
        result = history_validator.validate(password, user)
        
        if not result['valid']:
            raise ValidationError(_(result['message']))
    
    def get_help_text(self):
        return _(f"Cannot reuse any of your last {self.history_count} passwords.")


class BreachValidator:
    """
    Validator that checks passwords against known breaches
    """
    
    def validate(self, password, user=None):
        """
        Validate against known breaches
        """
        from .security.password_policies import BreachedPasswordValidator
        breach_validator = BreachedPasswordValidator()
        
        result = breach_validator.validate(password)
        
        if result['breached']:
            raise ValidationError(
                _("This password has been found in %(count)d data breaches. Please choose a different password."),
                params={'count': result['count']}
            )
    
    def get_help_text(self):
        return _("Password will be checked against known data breaches.")


# Export validators for easy import
__all__ = [
    'ComprehensivePasswordValidator',
    'MinimumStrengthValidator', 
    'NoPersonalInfoValidator',
    'HistoryValidator',
    'BreachValidator'
]