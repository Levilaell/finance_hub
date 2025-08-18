"""
Secure logging utilities to prevent sensitive data from being logged
Following Stripe security best practices
"""
import re
import json
import logging
from typing import Dict, Any, List, Union
from django.conf import settings


class SensitiveDataFilter:
    """Filter to remove sensitive data from log records"""
    
    # Sensitive field patterns to redact
    SENSITIVE_PATTERNS = {
        # Credit card patterns
        'card_number': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
        'cvv': re.compile(r'\b\d{3,4}\b(?=.*(?:cvv|cvc|security|code))'),
        
        # Personal information
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'\b(?:\+?55\s?)?(?:\(?[1-9]{2}\)?\s?)?(?:9\d{4}[-\s]?\d{4}|\d{4}[-\s]?\d{4})\b'),
        'cpf': re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'),
        'cnpj': re.compile(r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b'),
        
        # Payment tokens and secrets
        'stripe_secret': re.compile(r'sk_(?:test|live)_[A-Za-z0-9]{24,}'),
        'stripe_publishable': re.compile(r'pk_(?:test|live)_[A-Za-z0-9]{24,}'),
        'webhook_secret': re.compile(r'whsec_[A-Za-z0-9]+'),
        'payment_intent': re.compile(r'pi_[A-Za-z0-9]+'),
        'customer_id': re.compile(r'cus_[A-Za-z0-9]+'),
        
        # Generic secrets
        'password': re.compile(r'(?i)password["\']?\s*[:=]\s*["\']?[^"\'\s]+'),
        'secret': re.compile(r'(?i)secret["\']?\s*[:=]\s*["\']?[^"\'\s]+'),
        'key': re.compile(r'(?i)(?:api_?key|access_?key)["\']?\s*[:=]\s*["\']?[^"\'\s]+'),
        'token': re.compile(r'(?i)token["\']?\s*[:=]\s*["\']?[^"\'\s]+'),
    }
    
    # Sensitive field names in dictionaries/objects
    SENSITIVE_FIELDS = {
        'password', 'secret', 'token', 'key', 'api_key', 'access_key',
        'stripe_secret_key', 'stripe_publishable_key', 'webhook_secret',
        'card_number', 'cvv', 'cvc', 'security_code', 'exp_month', 'exp_year',
        'account_number', 'routing_number', 'iban', 'sort_code',
        'customer_id', 'payment_method_id', 'payment_intent_id', 'invoice_id',
        'email', 'phone', 'cpf', 'cnpj', 'ssn', 'tax_id',
        'address', 'street', 'city', 'zip_code', 'postal_code',
        'first_name', 'last_name', 'full_name', 'name'
    }
    
    def __init__(self):
        self.replacement_text = '[REDACTED]'
    
    def filter(self, record):
        """Filter log record to remove sensitive data"""
        if hasattr(record, 'msg'):
            record.msg = self.sanitize_data(record.msg)
        
        if hasattr(record, 'args') and record.args:
            record.args = tuple(self.sanitize_data(arg) for arg in record.args)
        
        return True
    
    def sanitize_data(self, data: Any) -> Any:
        """Recursively sanitize data to remove sensitive information"""
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return self._sanitize_dict(data)
        elif isinstance(data, (list, tuple)):
            return type(data)(self.sanitize_data(item) for item in data)
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string content using regex patterns"""
        if not isinstance(text, str):
            return text
        
        # Apply all sensitive patterns
        sanitized = text
        for pattern_name, pattern in self.SENSITIVE_PATTERNS.items():
            sanitized = pattern.sub(self.replacement_text, sanitized)
        
        return sanitized
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize dictionary by checking field names and values"""
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        for key, value in data.items():
            # Check if field name is sensitive
            if any(sensitive_field in key.lower() for sensitive_field in self.SENSITIVE_FIELDS):
                sanitized[key] = self.replacement_text
            else:
                sanitized[key] = self.sanitize_data(value)
        
        return sanitized


class SecureLogger:
    """Secure logger wrapper that automatically sanitizes sensitive data"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.filter = SensitiveDataFilter()
    
    def _log(self, level: int, msg: str, *args, **kwargs):
        """Internal logging method with sanitization"""
        # Sanitize the message and arguments
        sanitized_msg = self.filter.sanitize_data(msg)
        sanitized_args = tuple(self.filter.sanitize_data(arg) for arg in args)
        
        # Sanitize extra fields
        if 'extra' in kwargs:
            kwargs['extra'] = self.filter.sanitize_data(kwargs['extra'])
        
        # Log with sanitized data
        self.logger.log(level, sanitized_msg, *sanitized_args, **kwargs)
    
    def debug(self, msg, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        self._log(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        self._log(logging.CRITICAL, msg, *args, **kwargs)
    
    def exception(self, msg, *args, exc_info=True, **kwargs):
        self._log(logging.ERROR, msg, *args, exc_info=exc_info, **kwargs)


def get_secure_logger(name: str) -> SecureLogger:
    """Get a secure logger instance that automatically sanitizes sensitive data"""
    return SecureLogger(name)


def sanitize_stripe_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Specifically sanitize Stripe webhook event data for logging
    Keeps essential information while removing sensitive data
    """
    if not isinstance(event, dict):
        return event
    
    # Create a copy to avoid mutating original
    sanitized_event = {
        'id': event.get('id'),
        'type': event.get('type'),
        'livemode': event.get('livemode'),
        'created': event.get('created'),
        'api_version': event.get('api_version'),
        'pending_webhooks': event.get('pending_webhooks')
    }
    
    # Sanitize data object while preserving structure
    if 'data' in event and 'object' in event['data']:
        data_object = event['data']['object']
        sanitized_object = {
            'id': data_object.get('id'),
            'object': data_object.get('object'),
            'status': data_object.get('status'),
            'amount': data_object.get('amount'),
            'currency': data_object.get('currency'),
            'created': data_object.get('created'),
            'description': data_object.get('description'),
        }
        
        # Add metadata if present but sanitize it
        if 'metadata' in data_object:
            metadata = data_object['metadata']
            sanitized_metadata = {}
            allowed_metadata_keys = {'plan_id', 'company_id', 'billing_period', 'environment'}
            
            for key, value in metadata.items():
                if key in allowed_metadata_keys:
                    sanitized_metadata[key] = value
                else:
                    sanitized_metadata[key] = '[REDACTED]'
            
            sanitized_object['metadata'] = sanitized_metadata
        
        sanitized_event['data'] = {'object': sanitized_object}
    
    return sanitized_event


# Configure Django logging to use sensitive data filter
def configure_secure_logging():
    """Configure Django logging to automatically filter sensitive data"""
    sensitive_filter = SensitiveDataFilter()
    
    # Add filter to all existing loggers
    for logger_name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.addFilter(sensitive_filter)
    
    # Add filter to root logger
    logging.getLogger().addFilter(sensitive_filter)


# Utility function for secure logging of webhook events
def log_webhook_event(logger: SecureLogger, event: Dict[str, Any], message: str, level: str = 'info'):
    """
    Safely log webhook event with automatic sanitization
    
    Args:
        logger: SecureLogger instance
        event: Stripe webhook event
        message: Log message
        level: Log level ('info', 'warning', 'error', etc.)
    """
    sanitized_event = sanitize_stripe_event(event)
    
    log_method = getattr(logger, level, logger.info)
    log_method(
        message,
        extra={
            'event_id': sanitized_event.get('id'),
            'event_type': sanitized_event.get('type'),
            'event_data': sanitized_event
        }
    )