"""
Enhanced OpenAI API Wrapper with Comprehensive Error Handling
Includes circuit breaker, retry logic, and fallback mechanisms
"""
import logging
import time
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass, field
import openai
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class OpenAIError(Exception):
    """Base exception for OpenAI operations"""
    pass


class OpenAIRateLimitError(OpenAIError):
    """Rate limit exceeded"""
    pass


class OpenAITimeoutError(OpenAIError):
    """Request timeout"""
    pass


class OpenAIAPIError(OpenAIError):
    """API error from OpenAI"""
    pass


@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = 'closed'  # closed, open, half_open
    success_count: int = 0
    last_success_time: Optional[datetime] = None


class CircuitBreaker:
    """Circuit breaker pattern implementation for OpenAI calls"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.state_key = 'ai_insights:circuit_breaker:openai'
    
    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state from cache"""
        state_data = cache.get(self.state_key)
        if not state_data:
            return CircuitBreakerState()
        
        return CircuitBreakerState(
            failure_count=state_data.get('failure_count', 0),
            last_failure_time=state_data.get('last_failure_time'),
            state=state_data.get('state', 'closed'),
            success_count=state_data.get('success_count', 0),
            last_success_time=state_data.get('last_success_time')
        )
    
    def save_state(self, state: CircuitBreakerState):
        """Save circuit breaker state to cache"""
        state_data = {
            'failure_count': state.failure_count,
            'last_failure_time': state.last_failure_time,
            'state': state.state,
            'success_count': state.success_count,
            'last_success_time': state.last_success_time
        }
        cache.set(self.state_key, state_data, timeout=3600)  # 1 hour cache
    
    def record_success(self):
        """Record successful call"""
        state = self.get_state()
        state.success_count += 1
        state.last_success_time = timezone.now()
        
        if state.state == 'half_open' and state.success_count >= self.success_threshold:
            state.state = 'closed'
            state.failure_count = 0
            logger.info("Circuit breaker closed after successful recovery")
        
        self.save_state(state)
    
    def record_failure(self):
        """Record failed call"""
        state = self.get_state()
        state.failure_count += 1
        state.last_failure_time = timezone.now()
        
        if state.failure_count >= self.failure_threshold:
            state.state = 'open'
            logger.warning(f"Circuit breaker opened after {state.failure_count} failures")
        
        self.save_state(state)
    
    def can_attempt(self) -> bool:
        """Check if request can be attempted"""
        state = self.get_state()
        
        if state.state == 'closed':
            return True
        
        if state.state == 'open':
            if state.last_failure_time:
                time_since_failure = (timezone.now() - state.last_failure_time).seconds
                if time_since_failure >= self.recovery_timeout:
                    state.state = 'half_open'
                    state.success_count = 0
                    self.save_state(state)
                    logger.info("Circuit breaker entering half-open state")
                    return True
            return False
        
        # half_open state
        return True


class OpenAIWrapper:
    """Enhanced OpenAI wrapper with comprehensive error handling"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        openai.api_key = self.api_key
        self.circuit_breaker = CircuitBreaker()
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.timeout = 30  # seconds
        
        # Fallback responses
        self.fallback_responses = {
            'analysis': "Desculpe, estou temporariamente indisponível para análise detalhada. Por favor, tente novamente em alguns minutos.",
            'general': "Sistema temporariamente indisponível. Por favor, tente novamente mais tarde.",
            'error': "Ocorreu um erro ao processar sua solicitação. Nossa equipe foi notificada."
        }
    
    def with_retry(self, func: Callable) -> Callable:
        """Decorator for retry logic"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries):
                try:
                    # Check circuit breaker
                    if not self.circuit_breaker.can_attempt():
                        logger.warning("Circuit breaker is open, using fallback")
                        return self._get_fallback_response(kwargs.get('request_type', 'general'))
                    
                    # Attempt the call
                    result = func(*args, **kwargs)
                    
                    # Record success
                    self.circuit_breaker.record_success()
                    return result
                    
                except openai.error.RateLimitError as e:
                    last_exception = OpenAIRateLimitError(str(e))
                    wait_time = self._get_retry_wait_time(e, attempt)
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    
                except openai.error.Timeout as e:
                    last_exception = OpenAITimeoutError(str(e))
                    logger.warning(f"Request timeout on attempt {attempt + 1}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                    
                except openai.error.APIError as e:
                    last_exception = OpenAIAPIError(str(e))
                    logger.error(f"OpenAI API error: {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                    
                except Exception as e:
                    last_exception = OpenAIError(f"Unexpected error: {str(e)}")
                    logger.error(f"Unexpected error in OpenAI call: {str(e)}", exc_info=True)
                    break
            
            # All retries failed
            self.circuit_breaker.record_failure()
            self._log_failure(last_exception, args, kwargs)
            return self._get_fallback_response(kwargs.get('request_type', 'general'))
        
        return wrapper
    
    def create_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        request_type: str = 'general'
    ) -> Dict[str, Any]:
        """Create chat completion with error handling"""
        
        # Log request for monitoring (without sensitive data)
        logger.info(f"OpenAI request: model={model}, type={request_type}, messages={len(messages)}")
        
        # Make request with timeout
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=self.timeout
        )
        
        # Validate response
        if not response or 'choices' not in response or not response['choices']:
            raise OpenAIAPIError("Invalid response format from OpenAI")
        
        # Extract and validate content
        content = response['choices'][0]['message']['content']
        if not content:
            raise OpenAIAPIError("Empty response from OpenAI")
        
        # Log successful response
        logger.info(f"OpenAI response received: tokens={response.get('usage', {}).get('total_tokens', 0)}")
        
        return {
            'content': content,
            'model': model,
            'usage': response.get('usage', {}),
            'finish_reason': response['choices'][0].get('finish_reason', 'unknown')
        }
    
    def _get_retry_wait_time(self, error: Exception, attempt: int) -> float:
        """Calculate retry wait time based on error and attempt"""
        # Check if error has retry-after header
        if hasattr(error, 'response') and hasattr(error.response, 'headers'):
            retry_after = error.response.headers.get('Retry-After')
            if retry_after:
                return float(retry_after)
        
        # Exponential backoff
        return min(self.retry_delay * (2 ** attempt), 60)  # Max 60 seconds
    
    def _get_fallback_response(self, request_type: str) -> Dict[str, Any]:
        """Get fallback response for failed requests"""
        return {
            'content': self.fallback_responses.get(request_type, self.fallback_responses['general']),
            'model': 'fallback',
            'usage': {'total_tokens': 0},
            'finish_reason': 'fallback',
            'is_fallback': True
        }
    
    def _log_failure(self, exception: Exception, args: tuple, kwargs: dict):
        """Log detailed failure information for monitoring"""
        error_data = {
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'timestamp': timezone.now().isoformat(),
            'request_type': kwargs.get('request_type', 'unknown'),
            'model': kwargs.get('model', 'unknown')
        }
        
        # Log to file
        logger.error(f"OpenAI call failed: {json.dumps(error_data)}")
        
        # Could also send to monitoring service here
        # monitoring_service.record_error('openai_failure', error_data)
    
    def health_check(self) -> Dict[str, Any]:
        """Check OpenAI service health"""
        try:
            # Simple test request
            response = self.create_completion(
                messages=[{"role": "user", "content": "test"}],
                model="gpt-4o-mini",
                max_tokens=10,
                request_type='health_check'
            )
            
            return {
                'status': 'healthy',
                'circuit_breaker_state': self.circuit_breaker.get_state().state,
                'api_available': True,
                'last_check': timezone.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'circuit_breaker_state': self.circuit_breaker.get_state().state,
                'api_available': False,
                'error': str(e),
                'last_check': timezone.now().isoformat()
            }


# Singleton instance
openai_wrapper = OpenAIWrapper()