"""
Authentication utilities
"""
import base64
import hashlib
import io
import secrets

import pyotp
import qrcode
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password


def generate_2fa_secret():
    """Generate a new 2FA secret"""
    return pyotp.random_base32()


def generate_backup_codes(count=10):
    """Generate cryptographically secure backup codes for 2FA"""
    codes = []
    for _ in range(count):
        # Generate 8-digit codes using cryptographically secure random
        code = f"{secrets.randbelow(100000000):08d}"
        codes.append(code)
    return codes


def hash_backup_codes(codes):
    """Hash backup codes for secure storage"""
    return [make_password(code) for code in codes]


def get_totp_uri(user, secret):
    """Generate TOTP URI for QR code"""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name='CaixaHub'
    )


def generate_qr_code(uri):
    """Generate QR code image for 2FA setup"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def verify_totp_token(secret, token):
    """Verify TOTP token"""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)


def verify_backup_code(user, code):
    """Verify and consume hashed backup code"""
    for i, hashed_code in enumerate(user.backup_codes):
        if check_password(code, hashed_code):
            # Remove used code
            user.backup_codes.pop(i)
            user.save(update_fields=['backup_codes'])
            return True
    return False