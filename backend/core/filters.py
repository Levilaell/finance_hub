"""
Custom logging filters for Finance Hub
"""
import logging
import re


class FilterUserAgentFilter(logging.Filter):
    """
    Filter to remove or shorten User-Agent strings from logs
    """
    
    def filter(self, record):
        """
        Remove or shorten User-Agent information from log messages
        """
        if hasattr(record, 'msg') and record.msg:
            message = str(record.msg)
            
            # Pattern to match User-Agent strings
            user_agent_pattern = r'"Mozilla/5\.0[^"]*"'
            
            # Replace full User-Agent with simplified version
            if re.search(user_agent_pattern, message):
                # Replace with just browser type
                message = re.sub(user_agent_pattern, '"[Browser]"', message)
                record.msg = message
                
            # Also clean up args if they contain User-Agent
            if hasattr(record, 'args') and record.args:
                cleaned_args = []
                for arg in record.args:
                    if isinstance(arg, str) and 'Mozilla/5.0' in arg:
                        arg = re.sub(user_agent_pattern, '[Browser]', arg)
                    cleaned_args.append(arg)
                record.args = tuple(cleaned_args)
        
        return True


class RequestLogFilter(logging.Filter):
    """
    Filter to clean up request logs by removing unnecessary headers
    """
    
    def filter(self, record):
        """
        Clean up request log messages
        """
        if hasattr(record, 'msg') and record.msg:
            message = str(record.msg)
            
            # Remove common unnecessary headers from logs
            patterns_to_clean = [
                r'"Mozilla/5\.0[^"]*"',  # User-Agent
                r'"[^"]*gzip[^"]*"',     # Accept-Encoding with gzip
                r'"text/html[^"]*"',     # Accept headers
            ]
            
            for pattern in patterns_to_clean:
                message = re.sub(pattern, '"[...]"', message)
            
            record.msg = message
            
        return True


class SensitiveDataFilter(logging.Filter):
    """
    Filter to remove sensitive data from logs
    """
    
    def filter(self, record):
        """
        Remove sensitive information from logs
        """
        if hasattr(record, 'msg') and record.msg:
            message = str(record.msg)
            
            # Patterns to hide sensitive data
            sensitive_patterns = [
                (r'"password":\s*"[^"]*"', '"password": "[HIDDEN]"'),
                (r'"token":\s*"[^"]*"', '"token": "[HIDDEN]"'),
                (r'"authorization":\s*"Bearer [^"]*"', '"authorization": "Bearer [HIDDEN]"'),
                (r'"x-api-key":\s*"[^"]*"', '"x-api-key": "[HIDDEN]"'),
                (r'cpf=\d{11}', 'cpf=[HIDDEN]'),
                (r'email=[^&\s]+@[^&\s]+', 'email=[HIDDEN]'),
            ]
            
            for pattern, replacement in sensitive_patterns:
                message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
            
            record.msg = message
            
        return True