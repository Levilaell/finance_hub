"""
Validators for company-related fields
"""
# Re-export common validators to maintain backward compatibility
from core.common_validators import (
    validate_cnpj,
    validate_phone,
    format_cnpj,
    format_phone
)


__all__ = ['validate_cnpj', 'validate_phone', 'format_cnpj', 'format_phone']