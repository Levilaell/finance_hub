# backend/apps/banking/exceptions.py
"""
Custom exceptions for banking app
"""


class BankingError(Exception):
    """Base exception for banking app"""
    pass


class PluggyError(BankingError):
    """Base Pluggy exception"""
    pass


class PluggyAuthError(PluggyError):
    """Authentication error with Pluggy"""
    pass


class PluggyRateLimitError(PluggyError):
    """Rate limit exceeded"""
    pass


class PluggyConnectionError(PluggyError):
    """Connection error with Pluggy"""
    pass


class PluggyItemError(PluggyError):
    """Item-related error"""
    pass


class PluggyWebhookError(PluggyError):
    """Webhook validation error"""
    pass