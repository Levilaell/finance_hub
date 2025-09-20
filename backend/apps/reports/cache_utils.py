"""
Cache utilities for reports module
"""
import hashlib
import re
from typing import Any


def make_cache_key(*parts: Any) -> str:
    """
    Create a safe cache key from arbitrary parts.
    
    Args:
        *parts: Any number of parts to combine into a cache key
        
    Returns:
        str: A memcached/redis safe cache key
    """
    # Convert all parts to strings and join with underscores
    key_parts = [str(part) for part in parts]
    raw_key = "_".join(key_parts)
    
    # Remove/replace problematic characters
    # Memcached doesn't allow: spaces, newlines, carriage returns, null bytes
    # and control characters, and keys must be < 250 characters
    safe_key = re.sub(r'[\s\n\r\x00-\x1f\x7f-\x9f]', '_', raw_key)
    safe_key = re.sub(r'[:]', '_', safe_key)  # Replace colons
    safe_key = re.sub(r'[.]', '_', safe_key)  # Replace dots  
    safe_key = re.sub(r'[-]', '_', safe_key)  # Replace hyphens with underscores
    safe_key = re.sub(r'[+]', '_', safe_key)  # Replace plus signs
    
    # If key is too long, hash it
    if len(safe_key) > 200:  # Leave room for prefixes
        # Keep first part readable, hash the rest
        prefix = safe_key[:50]
        suffix = hashlib.md5(safe_key.encode('utf-8')).hexdigest()
        safe_key = f"{prefix}_{suffix}"
    
    return safe_key


def make_date_cache_key(prefix: str, company_id: int, start_date, end_date, suffix: str = "") -> str:
    """
    Create a cache key for date-based queries.
    
    Args:
        prefix: Cache key prefix (e.g., 'cashflow', 'category_spending')
        company_id: Company ID
        start_date: Start date (datetime or string)
        end_date: End date (datetime or string)  
        suffix: Optional suffix (e.g., category type)
        
    Returns:
        str: Safe cache key
    """
    # Format dates as simple strings
    if hasattr(start_date, 'date'):
        start_str = start_date.date().isoformat()
    else:
        start_str = str(start_date)
        
    if hasattr(end_date, 'date'):
        end_str = end_date.date().isoformat()
    else:
        end_str = str(end_date)
    
    parts = [prefix, company_id, start_str, end_str]
    if suffix:
        parts.append(suffix)
        
    return make_cache_key(*parts)
