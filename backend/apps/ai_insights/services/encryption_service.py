"""
Encryption Service for Sensitive Financial Data
Implements field-level encryption for AI Insights
"""
import base64
import json
import logging
from typing import Any, Dict, List, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting sensitive financial data"""
    
    # Fields that should always be encrypted
    SENSITIVE_FIELDS = {
        'account_number',
        'routing_number',
        'card_number',
        'cvv',
        'pin',
        'social_security_number',
        'tax_id',
        'balance',
        'transaction_amount',
        'salary',
        'income',
        'revenue',
        'expense_amount',
        'credit_limit',
        'available_credit',
        'bank_credentials',
        'api_credentials',
        'financial_summary',
        'investment_value',
        'net_worth'
    }
    
    # Patterns to detect sensitive data in nested structures
    SENSITIVE_PATTERNS = [
        'account', 'balance', 'amount', 'value', 'credit', 'debit',
        'income', 'expense', 'revenue', 'cost', 'price', 'salary',
        'card', 'bank', 'financial', 'money', 'payment', 'transaction'
    ]
    
    def __init__(self):
        """Initialize encryption service with key from settings"""
        encryption_key = getattr(settings, 'AI_INSIGHTS_ENCRYPTION_KEY', None)
        
        if not encryption_key:
            # Generate a key from SECRET_KEY if specific key not provided
            logger.warning("AI_INSIGHTS_ENCRYPTION_KEY not set, deriving from SECRET_KEY")
            encryption_key = self._derive_key_from_secret(settings.SECRET_KEY)
        
        try:
            self.cipher_suite = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        except Exception as e:
            raise ImproperlyConfigured(f"Invalid encryption key: {str(e)}")
    
    def _derive_key_from_secret(self, secret: str) -> bytes:
        """Derive encryption key from Django SECRET_KEY"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'ai_insights_salt_v1',  # Static salt for consistency
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        return key
    
    def encrypt_value(self, value: Any) -> str:
        """Encrypt a single value"""
        if value is None:
            return None
        
        try:
            # Convert to JSON string for consistent handling
            json_value = json.dumps(value)
            encrypted = self.cipher_suite.encrypt(json_value.encode())
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            raise
    
    def decrypt_value(self, encrypted_value: str) -> Any:
        """Decrypt a single value"""
        if encrypted_value is None:
            return None
        
        try:
            decoded = base64.b64decode(encrypted_value.encode('utf-8'))
            decrypted = self.cipher_suite.decrypt(decoded)
            return json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            raise
    
    def encrypt_dict(self, data: Dict[str, Any], fields_to_encrypt: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Encrypt specific fields in a dictionary
        
        Args:
            data: Dictionary containing data
            fields_to_encrypt: Specific fields to encrypt. If None, uses auto-detection
            
        Returns:
            Dictionary with encrypted fields
        """
        if not data:
            return data
        
        encrypted_data = data.copy()
        
        # Determine which fields to encrypt
        if fields_to_encrypt:
            target_fields = fields_to_encrypt
        else:
            # Auto-detect sensitive fields
            target_fields = self._detect_sensitive_fields(data)
        
        # Encrypt each target field
        for field in target_fields:
            if field in data and data[field] is not None:
                try:
                    encrypted_data[field] = {
                        '_encrypted': True,
                        'value': self.encrypt_value(data[field])
                    }
                except Exception as e:
                    logger.error(f"Failed to encrypt field {field}: {str(e)}")
                    # Continue with other fields
        
        return encrypted_data
    
    def decrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt encrypted fields in a dictionary
        
        Args:
            data: Dictionary potentially containing encrypted fields
            
        Returns:
            Dictionary with decrypted fields
        """
        if not data:
            return data
        
        decrypted_data = {}
        
        for key, value in data.items():
            if isinstance(value, dict) and value.get('_encrypted'):
                try:
                    decrypted_data[key] = self.decrypt_value(value['value'])
                except Exception as e:
                    logger.error(f"Failed to decrypt field {key}: {str(e)}")
                    decrypted_data[key] = None
            elif isinstance(value, dict):
                # Recursively decrypt nested dictionaries
                decrypted_data[key] = self.decrypt_dict(value)
            elif isinstance(value, list):
                # Handle lists that might contain dictionaries
                decrypted_data[key] = [
                    self.decrypt_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                decrypted_data[key] = value
        
        return decrypted_data
    
    def _detect_sensitive_fields(self, data: Dict[str, Any]) -> List[str]:
        """Auto-detect sensitive fields based on field names and patterns"""
        sensitive_fields = []
        
        for field_name, value in data.items():
            # Check exact matches
            if field_name.lower() in self.SENSITIVE_FIELDS:
                sensitive_fields.append(field_name)
                continue
            
            # Check patterns
            field_lower = field_name.lower()
            for pattern in self.SENSITIVE_PATTERNS:
                if pattern in field_lower:
                    # Additional validation - check if it's numeric or financial data
                    if isinstance(value, (int, float, str)) or \
                       (isinstance(value, str) and any(c.isdigit() for c in value)):
                        sensitive_fields.append(field_name)
                        break
        
        return sensitive_fields
    
    def encrypt_financial_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt financial context data for AI conversations
        
        Args:
            context: Financial context dictionary
            
        Returns:
            Encrypted context
        """
        if not context:
            return context
        
        # Define specific fields that should be encrypted in financial context
        financial_fields = [
            'current_balance', 'monthly_income', 'monthly_expenses',
            'net_cash_flow', 'avg_transaction_value', 'total_income',
            'total_expenses', 'income', 'expenses', 'balance',
            'total', 'amount', 'value'
        ]
        
        encrypted_context = {}
        
        for key, value in context.items():
            if key in financial_fields and isinstance(value, (int, float, str)):
                encrypted_context[key] = {
                    '_encrypted': True,
                    'value': self.encrypt_value(value)
                }
            elif isinstance(value, dict):
                # Recursively encrypt nested dictionaries
                encrypted_context[key] = self.encrypt_financial_context(value)
            elif isinstance(value, list) and key == 'top_expense_categories':
                # Special handling for category lists
                encrypted_context[key] = []
                for item in value:
                    if isinstance(item, dict):
                        encrypted_item = item.copy()
                        if 'total' in encrypted_item:
                            encrypted_item['total'] = {
                                '_encrypted': True,
                                'value': self.encrypt_value(encrypted_item['total'])
                            }
                        encrypted_context[key].append(encrypted_item)
                    else:
                        encrypted_context[key].append(item)
            else:
                encrypted_context[key] = value
        
        return encrypted_context
    
    def mask_sensitive_data(self, data: Union[Dict, str], mask_char: str = '*') -> Union[Dict, str]:
        """
        Mask sensitive data for logging or display purposes
        
        Args:
            data: Data to mask
            mask_char: Character to use for masking
            
        Returns:
            Masked data
        """
        if isinstance(data, str):
            # For strings, mask middle portion
            if len(data) <= 4:
                return mask_char * len(data)
            return data[:2] + mask_char * (len(data) - 4) + data[-2:]
        
        if not isinstance(data, dict):
            return data
        
        masked_data = {}
        sensitive_fields = self._detect_sensitive_fields(data)
        
        for key, value in data.items():
            if key in sensitive_fields:
                if isinstance(value, (int, float)):
                    # For numbers, show range
                    masked_data[key] = f"<numeric:{mask_char * 6}>"
                elif isinstance(value, str):
                    masked_data[key] = self.mask_sensitive_data(value, mask_char)
                else:
                    masked_data[key] = f"<{type(value).__name__}:masked>"
            elif isinstance(value, dict):
                masked_data[key] = self.mask_sensitive_data(value, mask_char)
            else:
                masked_data[key] = value
        
        return masked_data


# Singleton instance
encryption_service = EncryptionService()