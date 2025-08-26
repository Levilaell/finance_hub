#!/usr/bin/env python3
"""
Generate JWT RSA keys for Railway environment variables
Solves Railway's ephemeral filesystem issue by storing keys as env vars
"""
import base64
import os
import sys
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_rsa_keypair(key_size=2048):
    """Generate RSA key pair for JWT signing"""
    print("🔑 Generating RSA key pair for JWT authentication...")
    
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


def encode_for_env(key_bytes):
    """Encode key bytes for environment variable storage"""
    return base64.b64encode(key_bytes).decode('utf-8')


def main():
    """Generate JWT keys and display Railway environment variables"""
    print("🚀 JWT Key Generator for Railway Environment Variables")
    print("=" * 60)
    
    try:
        # Generate keys
        private_key, public_key = generate_rsa_keypair()
        
        # Encode for environment variables
        private_key_b64 = encode_for_env(private_key)
        public_key_b64 = encode_for_env(public_key)
        
        print("✅ RSA key pair generated successfully!")
        print()
        print("📋 Railway Environment Variables to Set:")
        print("=" * 60)
        print()
        print("🔐 JWT Private Key:")
        print(f"JWT_PRIVATE_KEY_B64={private_key_b64}")
        print()
        print("🔐 JWT Public Key:")
        print(f"JWT_PUBLIC_KEY_B64={public_key_b64}")
        print()
        print("=" * 60)
        print()
        print("📝 Instructions:")
        print("1. Copy the environment variables above")
        print("2. Go to Railway Dashboard → Your Project → Variables")
        print("3. Add both JWT_PRIVATE_KEY_B64 and JWT_PUBLIC_KEY_B64")
        print("4. Redeploy your application")
        print("5. JWT authentication will use persistent keys!")
        print()
        print("⚠️  SECURITY NOTES:")
        print("• Keep these keys secret and secure")
        print("• Don't share them in public repositories")
        print("• Store them only in Railway environment variables")
        print("• These keys will persist across deployments")
        
        # Also save to local file for backup
        backup_file = "jwt_keys_backup.txt"
        with open(backup_file, 'w') as f:
            f.write("# JWT Keys for Railway Environment Variables\n")
            f.write("# Generated at: " + str(os.popen('date').read().strip()) + "\n\n")
            f.write(f"JWT_PRIVATE_KEY_B64={private_key_b64}\n")
            f.write(f"JWT_PUBLIC_KEY_B64={public_key_b64}\n")
        
        print(f"💾 Keys also saved to: {backup_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error generating JWT keys: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())