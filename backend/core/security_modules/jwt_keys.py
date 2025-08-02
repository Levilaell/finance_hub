"""
JWT RSA Key Management for Enhanced Security
Implements RS256 algorithm with proper key generation and management
"""
import os
import secrets
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.core.management.utils import get_random_secret_key
import logging

logger = logging.getLogger(__name__)


class JWTKeyManager:
    """
    Manages RSA key pairs for JWT signing and verification
    """
    
    def __init__(self):
        self.key_dir = Path(settings.BASE_DIR) / 'core' / 'security' / 'keys'
        self.private_key_file = self.key_dir / 'jwt_private.pem'
        self.public_key_file = self.key_dir / 'jwt_public.pem'
        
        # Ensure keys directory exists
        self.key_dir.mkdir(parents=True, exist_ok=True)
        
        # Set secure permissions on keys directory
        os.chmod(self.key_dir, 0o700)
    
    def generate_key_pair(self, key_size=2048):
        """
        Generate RSA key pair for JWT signing
        """
        logger.info("Generating new RSA key pair for JWT signing")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        
        # Get public key
        public_key = private_key.public_key()
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Serialize public key
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem
    
    def save_keys(self, private_key_pem, public_key_pem):
        """
        Save RSA keys to secure files
        """
        # Save private key
        with open(self.private_key_file, 'wb') as f:
            f.write(private_key_pem)
        
        # Save public key
        with open(self.public_key_file, 'wb') as f:
            f.write(public_key_pem)
        
        # Set secure permissions
        os.chmod(self.private_key_file, 0o600)  # Read/write for owner only
        os.chmod(self.public_key_file, 0o644)   # Read for all, write for owner
        
        logger.info("RSA key pair saved successfully")
    
    def load_private_key(self):
        """
        Load private key from file
        """
        if not self.private_key_file.exists():
            raise FileNotFoundError("Private key file not found. Generate keys first.")
        
        with open(self.private_key_file, 'rb') as f:
            return f.read()
    
    def load_public_key(self):
        """
        Load public key from file
        """
        if not self.public_key_file.exists():
            raise FileNotFoundError("Public key file not found. Generate keys first.")
        
        with open(self.public_key_file, 'rb') as f:
            return f.read()
    
    def keys_exist(self):
        """
        Check if both key files exist
        """
        return self.private_key_file.exists() and self.public_key_file.exists()
    
    def ensure_keys_exist(self):
        """
        Ensure RSA key pair exists, generate if missing
        """
        if not self.keys_exist():
            logger.info("RSA keys not found, generating new key pair")
            private_key, public_key = self.generate_key_pair()
            self.save_keys(private_key, public_key)
            return True
        return False
    
    def rotate_keys(self):
        """
        Generate new key pair and backup old ones
        """
        if self.keys_exist():
            # Backup existing keys
            backup_dir = self.key_dir / 'backup'
            backup_dir.mkdir(exist_ok=True)
            
            import time
            timestamp = int(time.time())
            
            # Move existing keys to backup
            if self.private_key_file.exists():
                backup_private = backup_dir / f'jwt_private_{timestamp}.pem'
                self.private_key_file.rename(backup_private)
            
            if self.public_key_file.exists():
                backup_public = backup_dir / f'jwt_public_{timestamp}.pem'
                self.public_key_file.rename(backup_public)
            
            logger.info(f"Existing keys backed up to {backup_dir}")
        
        # Generate new keys
        private_key, public_key = self.generate_key_pair()
        self.save_keys(private_key, public_key)
        
        logger.info("JWT keys rotated successfully")


def get_jwt_private_key():
    """
    Get JWT private key for signing
    """
    key_manager = JWTKeyManager()
    key_manager.ensure_keys_exist()
    return key_manager.load_private_key()


def get_jwt_public_key():
    """
    Get JWT public key for verification
    """
    key_manager = JWTKeyManager()
    key_manager.ensure_keys_exist()
    return key_manager.load_public_key()


def initialize_jwt_keys():
    """
    Initialize JWT keys on startup
    """
    key_manager = JWTKeyManager()
    if key_manager.ensure_keys_exist():
        logger.info("JWT keys initialized successfully")
    else:
        logger.info("JWT keys already exist")


# Global key manager instance
jwt_key_manager = JWTKeyManager()