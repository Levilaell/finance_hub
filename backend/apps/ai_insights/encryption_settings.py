"""
Encryption settings for AI Insights
Add these to your Django settings file
"""

# AI Insights Encryption Configuration
AI_INSIGHTS_ENCRYPTION_SETTINGS = {
    # Encryption key - MUST be kept secret and consistent across deployments
    # Generate with: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
    'ENCRYPTION_KEY': None,  # Set via environment variable AI_INSIGHTS_ENCRYPTION_KEY
    
    # Fields that should always be encrypted
    'ALWAYS_ENCRYPT_FIELDS': [
        'account_number', 'routing_number', 'card_number', 'cvv', 'pin',
        'social_security_number', 'tax_id', 'balance', 'transaction_amount',
        'salary', 'income', 'revenue', 'expense_amount', 'credit_limit',
        'available_credit', 'bank_credentials', 'api_credentials',
        'financial_summary', 'investment_value', 'net_worth'
    ],
    
    # Patterns to detect sensitive fields
    'SENSITIVE_PATTERNS': [
        'account', 'balance', 'amount', 'value', 'credit', 'debit',
        'income', 'expense', 'revenue', 'cost', 'price', 'salary',
        'card', 'bank', 'financial', 'money', 'payment', 'transaction'
    ],
    
    # Enable/disable encryption features
    'ENABLE_FIELD_ENCRYPTION': True,
    'ENABLE_AUTO_DETECTION': True,
    'ENABLE_AUDIT_LOGGING': True,
    
    # Performance settings
    'CACHE_DECRYPTED_VALUES': False,  # Set to True for better performance (less secure)
    'CACHE_TIMEOUT': 300,  # 5 minutes
}


def configure_ai_insights_encryption(settings_dict):
    """
    Configure AI Insights encryption in Django settings
    
    Usage in settings.py:
        from apps.ai_insights.encryption_settings import configure_ai_insights_encryption
        configure_ai_insights_encryption(locals())
    """
    import os
    from cryptography.fernet import Fernet
    
    # Get encryption key from environment or generate from SECRET_KEY
    encryption_key = os.environ.get('AI_INSIGHTS_ENCRYPTION_KEY')
    
    if not encryption_key:
        # In production, you should set a specific encryption key
        # This is a fallback that derives a key from SECRET_KEY
        import hashlib
        import base64
        
        secret_key = settings_dict.get('SECRET_KEY', '')
        if secret_key:
            # Create a deterministic key from SECRET_KEY
            key_bytes = hashlib.pbkdf2_hmac(
                'sha256',
                secret_key.encode('utf-8'),
                b'ai_insights_encryption_salt_v1',
                100000,
                dklen=32
            )
            encryption_key = base64.urlsafe_b64encode(key_bytes).decode()
    
    # Set the encryption key
    settings_dict['AI_INSIGHTS_ENCRYPTION_KEY'] = encryption_key
    
    # Apply encryption settings
    if 'AI_INSIGHTS_ENCRYPTION_SETTINGS' not in settings_dict:
        settings_dict['AI_INSIGHTS_ENCRYPTION_SETTINGS'] = {}
    
    settings_dict['AI_INSIGHTS_ENCRYPTION_SETTINGS'].update(AI_INSIGHTS_ENCRYPTION_SETTINGS)
    
    # Production security warnings
    if settings_dict.get('DEBUG', False):
        import warnings
        if not os.environ.get('AI_INSIGHTS_ENCRYPTION_KEY'):
            warnings.warn(
                "AI_INSIGHTS_ENCRYPTION_KEY not set. Using derived key from SECRET_KEY. "
                "In production, set AI_INSIGHTS_ENCRYPTION_KEY environment variable.",
                UserWarning
            )


# Helper function to generate a new encryption key
def generate_encryption_key():
    """Generate a new Fernet encryption key"""
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()


# Add to your .env file:
# AI_INSIGHTS_ENCRYPTION_KEY=your-generated-key-here