"""
Enhanced password security policies and validation
"""
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from django.utils.translation import gettext as _
import re
import requests
import hashlib
import logging
from typing import List, Dict, Optional
from zxcvbn import zxcvbn

logger = logging.getLogger(__name__)


class PasswordStrengthValidator:
    """
    Advanced password strength validation using multiple criteria
    """
    
    def __init__(self):
        self.min_length = 12
        self.min_uppercase = 1
        self.min_lowercase = 1
        self.min_digits = 1
        self.min_special = 1
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
    def validate(self, password: str, user=None) -> Dict:
        """
        Validate password strength
        Returns: {'valid': bool, 'score': int, 'feedback': list, 'strength': str}
        """
        feedback = []
        score = 0
        
        # Length check
        if len(password) < self.min_length:
            feedback.append(f"Password must be at least {self.min_length} characters long")
        else:
            score += 2
        
        # Character requirements
        if not re.search(r'[A-Z]', password):
            feedback.append("Password must contain at least one uppercase letter")
        else:
            score += 1
            
        if not re.search(r'[a-z]', password):
            feedback.append("Password must contain at least one lowercase letter")
        else:
            score += 1
            
        if not re.search(r'\d', password):
            feedback.append("Password must contain at least one digit")
        else:
            score += 1
            
        if not re.search(f"[{re.escape(self.special_chars)}]", password):
            feedback.append("Password must contain at least one special character")
        else:
            score += 1
        
        # Advanced checks using zxcvbn
        try:
            zxcvbn_result = zxcvbn(password, user_inputs=self._get_user_inputs(user))
            zxcvbn_score = zxcvbn_result['score']
            
            if zxcvbn_score < 3:
                feedback.extend(zxcvbn_result['feedback']['suggestions'])
            
            # Adjust score based on zxcvbn
            score += zxcvbn_score
            
        except Exception as e:
            logger.warning(f"zxcvbn validation failed: {e}")
        
        # Common patterns check
        if self._has_common_patterns(password):
            feedback.append("Password contains common patterns")
            score -= 1
        
        # Personal information check
        if user and self._contains_personal_info(password, user):
            feedback.append("Password should not contain personal information")
            score -= 2
        
        # Determine strength
        if score >= 8:
            strength = 'very_strong'
        elif score >= 6:
            strength = 'strong'
        elif score >= 4:
            strength = 'medium'
        elif score >= 2:
            strength = 'weak'
        else:
            strength = 'very_weak'
        
        return {
            'valid': len(feedback) == 0 and strength in ['strong', 'very_strong'],
            'score': max(0, min(10, score)),
            'feedback': feedback,
            'strength': strength,
            'entropy': self._calculate_entropy(password),
        }
    
    def _get_user_inputs(self, user) -> List[str]:
        """Get user-specific inputs for zxcvbn"""
        if not user:
            return []
        
        inputs = []
        if hasattr(user, 'email'):
            inputs.append(user.email.split('@')[0])
        if hasattr(user, 'first_name'):
            inputs.append(user.first_name)
        if hasattr(user, 'last_name'):
            inputs.append(user.last_name)
        if hasattr(user, 'username'):
            inputs.append(user.username)
        
        return [inp.lower() for inp in inputs if inp]
    
    def _has_common_patterns(self, password: str) -> bool:
        """Check for common password patterns"""
        patterns = [
            r'123+',
            r'abc+',
            r'qwerty',
            r'password',
            r'admin',
            r'(.)\1{3,}',  # Repeated characters
        ]
        
        password_lower = password.lower()
        for pattern in patterns:
            if re.search(pattern, password_lower):
                return True
        
        return False
    
    def _contains_personal_info(self, password: str, user) -> bool:
        """Check if password contains personal information"""
        if not user:
            return False
        
        password_lower = password.lower()
        personal_info = self._get_user_inputs(user)
        
        for info in personal_info:
            if len(info) >= 3 and info in password_lower:
                return True
        
        return False
    
    def _calculate_entropy(self, password: str) -> float:
        """Calculate password entropy"""
        charset_size = 0
        
        if re.search(r'[a-z]', password):
            charset_size += 26
        if re.search(r'[A-Z]', password):
            charset_size += 26
        if re.search(r'\d', password):
            charset_size += 10
        if re.search(f"[{re.escape(self.special_chars)}]", password):
            charset_size += len(self.special_chars)
        
        if charset_size == 0:
            return 0
        
        import math
        return len(password) * math.log2(charset_size)


class BreachedPasswordValidator:
    """
    Check passwords against known breaches using HaveIBeenPwned API
    """
    
    def __init__(self):
        self.api_url = "https://api.pwnedpasswords.com/range/"
        self.timeout = 5
    
    def validate(self, password: str) -> Dict:
        """
        Check if password has been breached
        Returns: {'breached': bool, 'count': int, 'message': str}
        """
        try:
            # Hash password with SHA-1
            sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
            prefix = sha1_hash[:5]
            suffix = sha1_hash[5:]
            
            # Query API
            response = requests.get(
                f"{self.api_url}{prefix}",
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.warning(f"HIBP API returned status {response.status_code}")
                return {
                    'breached': False,
                    'count': 0,
                    'message': 'Could not check password against breach database'
                }
            
            # Parse response
            hashes = response.text.strip().split('\n')
            for hash_line in hashes:
                hash_suffix, count = hash_line.split(':')
                if hash_suffix == suffix:
                    count = int(count)
                    return {
                        'breached': True,
                        'count': count,
                        'message': f'This password has been found in {count:,} data breaches'
                    }
            
            return {
                'breached': False,
                'count': 0,
                'message': 'Password not found in known breaches'
            }
            
        except Exception as e:
            logger.error(f"Breached password check failed: {e}")
            return {
                'breached': False,
                'count': 0,
                'message': 'Could not verify password against breach database'
            }


class PasswordHistoryValidator:
    """
    Validate passwords against user's password history
    """
    
    def __init__(self, history_count=5):
        self.history_count = history_count
    
    def validate(self, password: str, user) -> Dict:
        """
        Check if password was used recently
        Returns: {'valid': bool, 'message': str}
        """
        if not user or not hasattr(user, 'password_history'):
            return {'valid': True, 'message': ''}
        
        password_history = user.password_history or []
        
        for entry in password_history:
            if isinstance(entry, dict) and 'hash' in entry:
                # Check if this password was used before
                if check_password(password, entry['hash']):
                    return {
                        'valid': False,
                        'message': f'Cannot reuse any of your last {self.history_count} passwords'
                    }
        
        return {'valid': True, 'message': 'Password not in recent history'}


class PasswordAgeValidator:
    """
    Validate password age and expiration policies
    """
    
    def __init__(self, max_age_days=90):
        self.max_age_days = max_age_days
    
    def should_force_change(self, user) -> Dict:
        """
        Check if user should be forced to change password
        Returns: {'force_change': bool, 'reason': str, 'days_overdue': int}
        """
        if not user or not hasattr(user, 'password_changed_at'):
            return {'force_change': False, 'reason': '', 'days_overdue': 0}
        
        if not user.password_changed_at:
            # No password change date recorded
            return {
                'force_change': True,
                'reason': 'Password change date not recorded',
                'days_overdue': 0
            }
        
        from django.utils import timezone
        age = (timezone.now() - user.password_changed_at).days
        
        if age > self.max_age_days:
            return {
                'force_change': True,
                'reason': f'Password is {age} days old (max {self.max_age_days})',
                'days_overdue': age - self.max_age_days
            }
        
        return {'force_change': False, 'reason': '', 'days_overdue': 0}


class ComprehensivePasswordValidator:
    """
    Comprehensive password validation combining all validators
    """
    
    def __init__(self):
        self.strength_validator = PasswordStrengthValidator()
        self.breach_validator = BreachedPasswordValidator()
        self.history_validator = PasswordHistoryValidator()
        self.age_validator = PasswordAgeValidator()
    
    def validate_password(self, password: str, user=None, check_breaches=True) -> Dict:
        """
        Comprehensive password validation
        Returns: {
            'valid': bool,
            'strength': dict,
            'breached': dict,
            'history': dict,
            'overall_score': int,
            'recommendations': list
        }
        """
        # Strength validation
        strength_result = self.strength_validator.validate(password, user)
        
        # Breach validation
        breach_result = {'breached': False, 'count': 0, 'message': ''}
        if check_breaches:
            breach_result = self.breach_validator.validate(password)
        
        # History validation
        history_result = self.history_validator.validate(password, user)
        
        # Calculate overall score
        overall_score = strength_result['score']
        
        if breach_result['breached']:
            overall_score -= 5  # Heavy penalty for breached passwords
        
        if not history_result['valid']:
            overall_score -= 3  # Penalty for reused passwords
        
        overall_score = max(0, min(10, overall_score))
        
        # Generate recommendations
        recommendations = []
        recommendations.extend(strength_result['feedback'])
        
        if breach_result['breached']:
            recommendations.append("This password has been compromised. Please choose a different one.")
        
        if not history_result['valid']:
            recommendations.append(history_result['message'])
        
        # Overall validity
        valid = (
            strength_result['valid'] and
            not breach_result['breached'] and
            history_result['valid']
        )
        
        return {
            'valid': valid,
            'strength': strength_result,
            'breached': breach_result,
            'history': history_result,
            'overall_score': overall_score,
            'recommendations': recommendations,
        }
    
    def get_password_requirements(self) -> Dict:
        """Get password requirements for display"""
        return {
            'min_length': self.strength_validator.min_length,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_digits': True,
            'require_special': True,
            'special_chars': self.strength_validator.special_chars,
            'check_breaches': True,
            'prevent_reuse': True,
            'max_age_days': self.age_validator.max_age_days,
        }


class PasswordGenerator:
    """
    Generate secure passwords with customizable options
    """
    
    def __init__(self):
        self.lowercase = 'abcdefghijklmnopqrstuvwxyz'
        self.uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.digits = '0123456789'
        self.special = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        self.ambiguous = 'il1Lo0O'  # Characters that might be confused
    
    def generate_password(self, 
                         length: int = 16,
                         include_lowercase: bool = True,
                         include_uppercase: bool = True,
                         include_digits: bool = True,
                         include_special: bool = True,
                         exclude_ambiguous: bool = True,
                         min_each_type: int = 1) -> str:
        """Generate a secure password"""
        import secrets
        
        charset = ''
        required_chars = []
        
        if include_lowercase:
            chars = self.lowercase
            if exclude_ambiguous:
                chars = ''.join(c for c in chars if c not in self.ambiguous)
            charset += chars
            required_chars.extend(secrets.choice(chars) for _ in range(min_each_type))
        
        if include_uppercase:
            chars = self.uppercase
            if exclude_ambiguous:
                chars = ''.join(c for c in chars if c not in self.ambiguous)
            charset += chars
            required_chars.extend(secrets.choice(chars) for _ in range(min_each_type))
        
        if include_digits:
            chars = self.digits
            if exclude_ambiguous:
                chars = ''.join(c for c in chars if c not in self.ambiguous)
            charset += chars
            required_chars.extend(secrets.choice(chars) for _ in range(min_each_type))
        
        if include_special:
            charset += self.special
            required_chars.extend(secrets.choice(self.special) for _ in range(min_each_type))
        
        # Fill remaining length with random characters
        remaining_length = length - len(required_chars)
        if remaining_length > 0:
            additional_chars = [secrets.choice(charset) for _ in range(remaining_length)]
            required_chars.extend(additional_chars)
        
        # Shuffle the password
        password_list = required_chars[:length]
        secrets.SystemRandom().shuffle(password_list)
        
        return ''.join(password_list)
    
    def generate_passphrase(self, word_count: int = 4, separator: str = '-') -> str:
        """Generate a passphrase using random words"""
        # Simple word list - in production, use a proper word list
        words = [
            'apple', 'banana', 'cherry', 'dragon', 'elephant', 'forest',
            'guitar', 'harmony', 'island', 'jungle', 'keyboard', 'lemon',
            'mountain', 'notebook', 'ocean', 'picture', 'question', 'rainbow',
            'sunshine', 'telescope', 'umbrella', 'volcano', 'waterfall', 'xylophone',
            'yellow', 'zebra', 'adventure', 'butterfly', 'carnival', 'diamond'
        ]
        
        import secrets
        selected_words = [secrets.choice(words) for _ in range(word_count)]
        
        # Add random numbers for extra security
        passphrase = separator.join(selected_words)
        passphrase += separator + str(secrets.randbelow(1000))
        
        return passphrase


# Global validator instance
password_validator = ComprehensivePasswordValidator()
password_generator = PasswordGenerator()