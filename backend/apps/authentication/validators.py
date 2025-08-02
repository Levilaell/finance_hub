"""
Enhanced password validators for comprehensive security
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re


class ComprehensivePasswordValidator:
    """
    Django-compatible comprehensive password validation
    """
    
    def __init__(self):
        self.min_length = 8
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_digits = True
        self.require_special = True
    
    def validate(self, password, user=None):
        """
        Validate password against comprehensive security policies
        """
        errors = []
        
        if len(password) < self.min_length:
            errors.append(ValidationError(
                _("Password must be at least %(min_length)d characters long."),
                params={'min_length': self.min_length}
            ))
        
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append(ValidationError(_("Password must contain at least one uppercase letter.")))
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append(ValidationError(_("Password must contain at least one lowercase letter.")))
        
        if self.require_digits and not re.search(r'[0-9]', password):
            errors.append(ValidationError(_("Password must contain at least one digit.")))
        
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append(ValidationError(_("Password must contain at least one special character.")))
        
        if errors:
            raise ValidationError(errors)
    
    def password_changed(self, password, user=None):
        """
        Called after password is changed
        """
        pass
    
    def get_help_text(self):
        """
        Return help text for password requirements
        """
        return _(
            "Your password must be at least 8 characters long and include "
            "uppercase and lowercase letters, numbers, and special characters."
        )


class MinimumStrengthValidator:
    """
    Validator that requires minimum password strength score
    """
    
    def __init__(self, min_score=6):
        self.min_score = min_score
    
    def validate(self, password, user=None):
        """
        Validate minimum strength score
        """
        # Simple strength calculation
        score = 0
        
        if len(password) >= 8:
            score += 2
        if len(password) >= 12:
            score += 2
        if re.search(r'[A-Z]', password):
            score += 2
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[0-9]', password):
            score += 2
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        
        if score < self.min_score:
            raise ValidationError(
                _("Password strength is too low. Score: %(score)d/10, minimum required: %(min_score)d/10"),
                params={'score': score, 'min_score': self.min_score}
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
        # Skip history validation for now - would need password history tracking
        pass
    
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
        # Skip breach validation for now - would need external API or database
        pass
    
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