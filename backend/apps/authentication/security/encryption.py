"""
Encryption utilities for sensitive authentication data
"""
from django.conf import settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import secrets
import logging

logger = logging.getLogger(__name__)


class SecureEncryption:
    """
    Handles encryption/decryption of sensitive data using Fernet symmetric encryption
    """
    
    def __init__(self, key=None):
        """Initialize with encryption key from settings or provided key"""
        if key:
            self.key = key
        else:
            self.key = getattr(settings, 'ENCRYPTION_KEY', None)
            if not self.key:
                # Generate a new key if none exists (for development)
                self.key = Fernet.generate_key()
                logger.warning("No ENCRYPTION_KEY found in settings. Generated temporary key.")
        
        if isinstance(self.key, str):
            self.key = self.key.encode()
        
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data and return base64 encoded string"""
        if not data:
            return ""
        
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded encrypted data and return original string"""
        if not encrypted_data:
            return ""
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    @staticmethod
    def generate_key():
        """Generate a new Fernet key"""
        return Fernet.generate_key()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: bytes = None) -> bytes:
        """Derive an encryption key from a password using PBKDF2"""
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def rotate_key(self, old_key: bytes, new_key: bytes, data: str) -> str:
        """Rotate encryption key for existing encrypted data"""
        # Decrypt with old key
        old_cipher = Fernet(old_key)
        decoded = base64.urlsafe_b64decode(data.encode())
        decrypted = old_cipher.decrypt(decoded)
        
        # Encrypt with new key
        new_cipher = Fernet(new_key)
        encrypted = new_cipher.encrypt(decrypted)
        return base64.urlsafe_b64encode(encrypted).decode()


# Global instance for convenience
default_encryption = SecureEncryption()