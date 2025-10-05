"""
Security utilities for safe logging and data handling
"""
import re
from typing import Any, Dict, Union


def sanitize_for_logging(data: Union[Dict, Any]) -> Union[Dict, Any]:
    """
    Remove sensitive data from logs

    Args:
        data: Dictionary or any data to sanitize

    Returns:
        Sanitized copy of the data with sensitive fields redacted
    """
    if not isinstance(data, dict):
        return data

    sensitive_keys = [
        'password', 'token', 'secret', 'key', 'credentials',
        'api_key', 'authorization', 'access_token', 'refresh_token',
        'client_secret', 'private_key', 'webhook_secret',
        'card_number', 'cvv', 'cvc', 'cpf', 'ssn'
    ]

    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()

        # Check if key contains sensitive keyword
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = '***REDACTED***'
        # Recursively sanitize nested dicts
        elif isinstance(value, dict):
            sanitized[key] = sanitize_for_logging(value)
        # Sanitize lists of dicts
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            sanitized[key] = [sanitize_for_logging(item) for item in value]
        else:
            sanitized[key] = value

    return sanitized


def sanitize_string(text: str) -> str:
    """
    Remove potential sensitive patterns from string

    Args:
        text: String to sanitize

    Returns:
        Sanitized string with patterns redacted
    """
    # Redact credit card patterns (4 groups of 4 digits)
    text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '****-****-****-****', text)

    # Redact CPF patterns (xxx.xxx.xxx-xx)
    text = re.sub(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b', '***.***.***-**', text)

    # Redact email addresses partially
    text = re.sub(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'\1***@\2', text)

    return text
