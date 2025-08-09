"""
Encrypted field mixins for AI Insights models
Provides transparent encryption/decryption for sensitive fields
"""
from django.db import models
from .services.encryption_service import encryption_service


class EncryptedJSONField(models.JSONField):
    """Custom JSON field that automatically encrypts/decrypts sensitive data"""
    
    def __init__(self, *args, encrypt_fields=None, auto_detect=True, **kwargs):
        """
        Initialize encrypted JSON field
        
        Args:
            encrypt_fields: List of fields to encrypt. If None and auto_detect=True, will auto-detect
            auto_detect: Whether to auto-detect sensitive fields
        """
        self.encrypt_fields = encrypt_fields
        self.auto_detect = auto_detect
        super().__init__(*args, **kwargs)
    
    def get_prep_value(self, value):
        """Encrypt before saving to database"""
        if value is None:
            return None
        
        # Encrypt the data
        if isinstance(value, dict):
            if self.auto_detect and not self.encrypt_fields:
                # Auto-detect sensitive fields
                encrypted_value = encryption_service.encrypt_dict(value)
            else:
                # Encrypt specific fields
                encrypted_value = encryption_service.encrypt_dict(value, self.encrypt_fields)
        else:
            encrypted_value = value
        
        # Let parent handle JSON serialization
        return super().get_prep_value(encrypted_value)
    
    def from_db_value(self, value, expression, connection):
        """Decrypt after loading from database"""
        # Let parent handle JSON deserialization
        value = super().from_db_value(value, expression, connection)
        
        if value is None:
            return None
        
        # Decrypt the data
        if isinstance(value, dict):
            return encryption_service.decrypt_dict(value)
        
        return value
    
    def to_python(self, value):
        """Convert to Python value"""
        value = super().to_python(value)
        
        if value is None:
            return None
        
        # Decrypt if needed
        if isinstance(value, dict) and any(
            isinstance(v, dict) and v.get('_encrypted') 
            for v in value.values()
        ):
            return encryption_service.decrypt_dict(value)
        
        return value


class EncryptedTextField(models.TextField):
    """Text field that encrypts its content"""
    
    def get_prep_value(self, value):
        """Encrypt before saving"""
        if value is None:
            return None
        
        return encryption_service.encrypt_value(value)
    
    def from_db_value(self, value, expression, connection):
        """Decrypt after loading"""
        if value is None:
            return None
        
        try:
            return encryption_service.decrypt_value(value)
        except Exception:
            # If decryption fails, might be unencrypted legacy data
            return value
    
    def to_python(self, value):
        """Convert to Python value"""
        if value is None:
            return None
        
        if isinstance(value, str):
            try:
                # Try to decrypt
                return encryption_service.decrypt_value(value)
            except Exception:
                # If it fails, assume it's plain text
                return value
        
        return str(value)


class EncryptedDecimalField(models.DecimalField):
    """Decimal field that encrypts its value"""
    
    def get_prep_value(self, value):
        """Encrypt before saving"""
        if value is None:
            return None
        
        # Convert to string for encryption
        str_value = str(super().get_prep_value(value))
        encrypted = encryption_service.encrypt_value(str_value)
        
        # Store as string in database
        return encrypted
    
    def from_db_value(self, value, expression, connection):
        """Decrypt after loading"""
        if value is None:
            return None
        
        try:
            decrypted = encryption_service.decrypt_value(value)
            # Convert back to Decimal
            from decimal import Decimal
            return Decimal(decrypted)
        except Exception:
            # If decryption fails, might be unencrypted legacy data
            return super().from_db_value(value, expression, connection)
    
    def to_python(self, value):
        """Convert to Python value"""
        if value is None:
            return None
        
        if isinstance(value, str):
            try:
                # Try to decrypt
                decrypted = encryption_service.decrypt_value(value)
                from decimal import Decimal
                return Decimal(decrypted)
            except Exception:
                # If it fails, treat as normal decimal
                pass
        
        return super().to_python(value)


class FinancialDataMixin:
    """Mixin to add encryption helpers to models with financial data"""
    
    def get_decrypted_financial_context(self):
        """Get decrypted financial context"""
        if hasattr(self, 'financial_context') and self.financial_context:
            return encryption_service.decrypt_dict(self.financial_context)
        return {}
    
    def set_financial_context(self, context):
        """Set financial context with encryption"""
        if context:
            self.financial_context = encryption_service.encrypt_financial_context(context)
        else:
            self.financial_context = {}
    
    def get_masked_financial_data(self):
        """Get masked version of financial data for logging"""
        data = {}
        
        # Collect financial fields
        if hasattr(self, 'financial_context'):
            data['financial_context'] = self.financial_context
        
        if hasattr(self, 'structured_data'):
            data['structured_data'] = self.structured_data
        
        if hasattr(self, 'data_context'):
            data['data_context'] = self.data_context
        
        # Mask the data
        return encryption_service.mask_sensitive_data(data)
    
    class Meta:
        abstract = True