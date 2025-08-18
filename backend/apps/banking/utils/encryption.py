"""
Banking-specific encryption utilities
Handles encryption of sensitive MFA parameters and credentials
"""
import json
import logging
import re
from typing import Any, Dict, Optional, Tuple
from apps.ai_insights.services.encryption_service import EncryptionService

logger = logging.getLogger(__name__)


class BankingEncryption:
    """Encryption service for banking sensitive data"""
    
    def __init__(self):
        """Initialize with the shared encryption service"""
        self.encryption_service = EncryptionService()
    
    def encrypt_mfa_parameter(self, parameter: Optional[Dict]) -> Optional[str]:
        """
        Encrypt MFA parameter data
        
        Args:
            parameter: Dictionary containing MFA parameter info
            
        Returns:
            Encrypted string or None if parameter is None/empty
        """
        if parameter is None or (isinstance(parameter, dict) and not parameter):
            return None
        
        try:
            # Log that we're encrypting (but not the actual values)
            if 'value' in parameter:
                logger.info("Encrypting MFA parameter with sensitive value")
            
            return self.encryption_service.encrypt_value(parameter)
        except Exception as e:
            logger.error(f"Failed to encrypt MFA parameter: {str(e)}")
            raise
    
    def decrypt_mfa_parameter(self, encrypted_parameter: Optional[str]) -> Optional[Dict]:
        """
        Decrypt MFA parameter data
        
        Args:
            encrypted_parameter: Encrypted string
            
        Returns:
            Decrypted dictionary or None if encrypted_parameter is None/empty
        """
        if not encrypted_parameter:
            return None
        
        try:
            decrypted = self.encryption_service.decrypt_value(encrypted_parameter)
            
            # Ensure it's a dictionary
            if not isinstance(decrypted, dict):
                logger.warning(f"Decrypted parameter is not a dict: {type(decrypted)}")
                return {}
            
            return decrypted
        except Exception as e:
            logger.error(f"Failed to decrypt MFA parameter: {str(e)}")
            # Return empty dict to avoid breaking the flow
            return {}
    
    def is_encrypted(self, value: Any) -> bool:
        """
        Check if a value appears to be encrypted
        
        Args:
            value: Value to check
            
        Returns:
            True if value appears to be encrypted
        """
        if not value or not isinstance(value, str):
            return False
        
        # Encrypted values are base64 encoded strings
        # They typically have a specific pattern
        try:
            # Try to detect if it's a JSON object (unencrypted)
            json.loads(value)
            return False
        except (json.JSONDecodeError, TypeError):
            # If it's not JSON, check if it looks like base64
            import base64
            try:
                decoded = base64.b64decode(value)
                # If it decodes and starts with typical Fernet prefix
                return len(decoded) > 0 and value.count('=') <= 2
            except Exception:
                return False

    def validate_mfa_value(self, mfa_value: Any, parameter_name: str = 'token') -> Tuple[bool, str]:
        """
        Validate MFA value format, type and length
        
        Args:
            mfa_value: The MFA value to validate
            parameter_name: The parameter name (token, code, password, etc.)
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if mfa_value is None:
            return False, "MFA value is required"
        
        # Convert to string and strip whitespace
        mfa_str = str(mfa_value).strip()
        
        if not mfa_str:
            return False, "MFA value cannot be empty"
        
        # Length validation
        if len(mfa_str) > 500:
            return False, "MFA value is too long (max 500 characters)"
        
        if len(mfa_str) < 1:
            return False, "MFA value is too short"
        
        # Type-specific validation
        parameter_lower = parameter_name.lower()
        
        if parameter_lower in ['token', 'code', 'sms_token', 'sms_code']:
            # Numeric tokens/codes
            if not re.match(r'^[0-9]{3,10}$', mfa_str):
                # Allow alphanumeric for some banks
                if not re.match(r'^[A-Za-z0-9]{3,20}$', mfa_str):
                    return False, f"Invalid {parameter_name} format (expected 3-20 alphanumeric characters)"
        
        elif parameter_lower in ['password', 'pin']:
            # Passwords/PINs - more permissive but check for common issues
            if len(mfa_str) < 3:
                return False, f"{parameter_name} is too short (minimum 3 characters)"
            if len(mfa_str) > 50:
                return False, f"{parameter_name} is too long (maximum 50 characters)"
            
            # Check for obviously invalid characters
            if any(ord(char) < 32 or ord(char) > 126 for char in mfa_str):
                return False, f"{parameter_name} contains invalid characters"
        
        elif parameter_lower in ['email', 'user', 'username']:
            # Email/username validation
            if '@' in mfa_str:
                # Basic email validation
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, mfa_str):
                    return False, "Invalid email format"
            else:
                # Username validation
                if not re.match(r'^[a-zA-Z0-9._-]{3,50}$', mfa_str):
                    return False, "Invalid username format (3-50 alphanumeric characters, dots, underscores, hyphens)"
        
        # Security checks - only reject obviously dangerous values
        if mfa_str.lower() in ['admin', 'password', '000000', '111111']:
            return False, f"Invalid {parameter_name} (common/test values not allowed)"
        
        # Check for potential injection attempts
        suspicious_patterns = [
            r'[<>\"\'`]',  # HTML/SQL injection chars
            r'javascript:',  # XSS
            r'data:',  # Data URLs
            r'\\x[0-9a-fA-F]{2}',  # Hex encoding
            r'%[0-9a-fA-F]{2}',  # URL encoding
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, mfa_str, re.IGNORECASE):
                logger.warning(f"Suspicious pattern detected in MFA value: {pattern}")
                return False, f"Invalid {parameter_name} format"
        
        return True, ""


# Singleton instance
banking_encryption = BankingEncryption()