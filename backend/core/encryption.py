"""
Encryption utilities for sensitive data storage
"""
import base64
import os
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class FieldEncryption:
    """
    Field-level encryption for sensitive data like OAuth tokens
    """
    
    def __init__(self):
        self._key = None
        
    @property
    def key(self):
        if self._key is None:
            # Get encryption key from environment
            key_string = getattr(settings, 'FIELD_ENCRYPTION_KEY', None)
            if not key_string:
                raise ImproperlyConfigured(
                    "FIELD_ENCRYPTION_KEY must be set in settings"
                )
            
            # Derive a proper Fernet key from the configured key
            # This ensures the key is properly formatted
            salt = b'finance_app_salt_v1'  # Application-specific salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(key_string.encode()))
            self._key = key
        return self._key
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return data
            
        fernet = Fernet(self.key)
        encrypted = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
            
        try:
            fernet = Fernet(self.key)
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            # If decryption fails, assume data is not encrypted (migration case)
            return encrypted_data


# Global encryption instance
field_encryption = FieldEncryption()


def generate_encryption_key():
    """Generate a new encryption key"""
    return Fernet.generate_key().decode()


def generate_secure_token(length=32):
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)


def hash_sensitive_data(data: str) -> str:
    """One-way hash for sensitive data like API keys in logs"""
    if not data:
        return data
    return hashlib.sha256(data.encode()).hexdigest()[:8] + '...'


class SecureTokenGenerator:
    """Generate and validate secure tokens for various purposes"""
    
    def __init__(self, namespace: str):
        self.namespace = namespace
        self.fernet = Fernet(field_encryption.key)
    
    def generate_token(self, data: dict, expires_in: int = 3600) -> str:
        """Generate a secure token with expiration"""
        import json
        import time
        
        payload = {
            'data': data,
            'namespace': self.namespace,
            'created_at': time.time(),
            'expires_at': time.time() + expires_in
        }
        
        json_payload = json.dumps(payload)
        encrypted = self.fernet.encrypt(json_payload.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def validate_token(self, token: str) -> dict:
        """Validate and decrypt a secure token"""
        import json
        import time
        
        try:
            decoded = base64.urlsafe_b64decode(token.encode())
            decrypted = self.fernet.decrypt(decoded)
            payload = json.loads(decrypted.decode())
            
            # Check namespace
            if payload.get('namespace') != self.namespace:
                raise ValueError("Invalid token namespace")
            
            # Check expiration
            if payload.get('expires_at', 0) < time.time():
                raise ValueError("Token has expired")
            
            return payload['data']
            
        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")


class EncryptedTextField:
    """
    Custom field descriptor for encrypted text fields
    """
    
    def __init__(self, field_name):
        self.field_name = field_name
        self.encrypted_field_name = f"_{field_name}_encrypted"
        
    def __get__(self, instance, owner):
        if instance is None:
            return self
            
        encrypted_value = getattr(instance, self.encrypted_field_name, None)
        if encrypted_value:
            return field_encryption.decrypt(encrypted_value)
        return None
        
    def __set__(self, instance, value):
        if value:
            encrypted_value = field_encryption.encrypt(value)
            setattr(instance, self.encrypted_field_name, encrypted_value)
        else:
            setattr(instance, self.encrypted_field_name, None)


class EncryptedJSONField:
    """
    Custom field descriptor for encrypted JSON fields
    """
    
    def __init__(self, field_name):
        self.field_name = field_name
        self.encrypted_field_name = f"_{field_name}_encrypted"
        
    def __get__(self, instance, owner):
        import json
        
        if instance is None:
            return self
            
        encrypted_value = getattr(instance, self.encrypted_field_name, None)
        if encrypted_value:
            decrypted = field_encryption.decrypt(encrypted_value)
            try:
                return json.loads(decrypted)
            except json.JSONDecodeError:
                return {}
        return {}
        
    def __set__(self, instance, value):
        import json
        
        if value:
            json_value = json.dumps(value)
            encrypted_value = field_encryption.encrypt(json_value)
            setattr(instance, self.encrypted_field_name, encrypted_value)
        else:
            setattr(instance, self.encrypted_field_name, None)