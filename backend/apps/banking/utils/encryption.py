"""
Banking-specific encryption utilities
Handles encryption of sensitive MFA parameters and credentials
"""
import json
import logging
from typing import Any, Dict, Optional
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


# Singleton instance
banking_encryption = BankingEncryption()