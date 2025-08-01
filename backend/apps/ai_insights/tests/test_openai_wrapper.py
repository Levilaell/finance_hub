"""
Unit tests for OpenAI Wrapper with comprehensive error handling
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.conf import settings
from django.core.cache import cache

from apps.ai_insights.services.openai_wrapper import (
    OpenAIWrapper,
    CircuitBreaker,
    OpenAIError,
    OpenAIRateLimitError,
    OpenAITimeoutError,
    OpenAIAPIError
)


class TestCircuitBreaker(TestCase):
    """Test circuit breaker functionality"""
    
    def setUp(self):
        cache.clear()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60,
            success_threshold=2
        )
    
    def test_initial_state_is_closed(self):
        """Test that circuit breaker starts in closed state"""
        state = self.circuit_breaker.get_state()
        self.assertEqual(state.state, 'closed')
        self.assertEqual(state.failure_count, 0)
        self.assertTrue(self.circuit_breaker.can_attempt())
    
    def test_failure_threshold_opens_circuit(self):
        """Test that circuit opens after failure threshold"""
        # Record failures up to threshold
        for _ in range(3):
            self.circuit_breaker.record_failure()
        
        state = self.circuit_breaker.get_state()
        self.assertEqual(state.state, 'open')
        self.assertFalse(self.circuit_breaker.can_attempt())
    
    def test_success_resets_failure_count(self):
        """Test that success resets failure count in closed state"""
        # Record some failures (but not enough to open)
        self.circuit_breaker.record_failure()
        self.circuit_breaker.record_failure()
        
        # Record success
        self.circuit_breaker.record_success()
        
        state = self.circuit_breaker.get_state()
        self.assertEqual(state.state, 'closed')
        self.assertTrue(self.circuit_breaker.can_attempt())
    
    def test_half_open_state_recovery(self):
        """Test recovery through half-open state"""
        # Open the circuit
        for _ in range(3):
            self.circuit_breaker.record_failure()
        
        # Simulate time passing
        state = self.circuit_breaker.get_state()
        state.last_failure_time = timezone.now() - timedelta(seconds=61)
        self.circuit_breaker.save_state(state)
        
        # Should allow attempt (half-open)
        self.assertTrue(self.circuit_breaker.can_attempt())
        
        # Record successes to close circuit
        for _ in range(2):
            self.circuit_breaker.record_success()
        
        state = self.circuit_breaker.get_state()
        self.assertEqual(state.state, 'closed')


class TestOpenAIWrapper(TestCase):
    """Test OpenAI wrapper functionality"""
    
    def setUp(self):
        cache.clear()
        self.wrapper = OpenAIWrapper()
    
    @patch('apps.ai_insights.services.openai_wrapper.openai')
    def test_successful_completion(self, mock_openai):
        """Test successful OpenAI completion"""
        # Mock successful response
        mock_openai.ChatCompletion.create.return_value = {
            'choices': [{
                'message': {'content': 'Test response'},
                'finish_reason': 'stop'
            }],
            'usage': {'total_tokens': 100}
        }
        
        response = self.wrapper.create_completion(
            messages=[{'role': 'user', 'content': 'test'}],
            request_type='general'
        )
        
        self.assertEqual(response['content'], 'Test response')
        self.assertEqual(response['usage']['total_tokens'], 100)
        self.assertFalse(response.get('is_fallback', False))
    
    @patch('apps.ai_insights.services.openai_wrapper.openai')
    def test_rate_limit_retry(self, mock_openai):
        """Test retry logic for rate limit errors"""
        # Mock rate limit error then success
        rate_limit_error = Mock()
        rate_limit_error.response = Mock()
        rate_limit_error.response.headers = {'Retry-After': '1'}
        
        mock_openai.error.RateLimitError = Exception
        mock_openai.ChatCompletion.create.side_effect = [
            mock_openai.error.RateLimitError(),
            {
                'choices': [{'message': {'content': 'Success after retry'}, 'finish_reason': 'stop'}],
                'usage': {'total_tokens': 50}
            }
        ]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            response = self.wrapper.create_completion(
                messages=[{'role': 'user', 'content': 'test'}],
                request_type='general'
            )
        
        self.assertEqual(response['content'], 'Success after retry')
        self.assertEqual(mock_openai.ChatCompletion.create.call_count, 2)
    
    @patch('apps.ai_insights.services.openai_wrapper.openai')
    def test_circuit_breaker_fallback(self, mock_openai):
        """Test fallback when circuit breaker is open"""
        # Open the circuit breaker
        for _ in range(5):
            self.wrapper.circuit_breaker.record_failure()
        
        response = self.wrapper.create_completion(
            messages=[{'role': 'user', 'content': 'test'}],
            request_type='general'
        )
        
        self.assertTrue(response.get('is_fallback', False))
        self.assertIn('temporarily unavailable', response['content'])
    
    @patch('apps.ai_insights.services.openai_wrapper.openai')
    def test_api_error_handling(self, mock_openai):
        """Test handling of API errors"""
        mock_openai.error.APIError = Exception
        mock_openai.ChatCompletion.create.side_effect = mock_openai.error.APIError("API Error")
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            response = self.wrapper.create_completion(
                messages=[{'role': 'user', 'content': 'test'}],
                request_type='general'
            )
        
        # Should fallback after retries
        self.assertTrue(response.get('is_fallback', False))
    
    @patch('apps.ai_insights.services.openai_wrapper.openai')
    def test_timeout_handling(self, mock_openai):
        """Test handling of timeout errors"""
        mock_openai.error.Timeout = Exception
        mock_openai.ChatCompletion.create.side_effect = [
            mock_openai.error.Timeout("Request timeout"),
            {
                'choices': [{'message': {'content': 'Success after timeout'}, 'finish_reason': 'stop'}],
                'usage': {'total_tokens': 75}
            }
        ]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            response = self.wrapper.create_completion(
                messages=[{'role': 'user', 'content': 'test'}],
                request_type='general'
            )
        
        self.assertEqual(response['content'], 'Success after timeout')
    
    def test_health_check_healthy(self):
        """Test health check when service is healthy"""
        with patch.object(self.wrapper, 'create_completion') as mock_create:
            mock_create.return_value = {
                'content': 'test',
                'model': 'gpt-4o-mini',
                'usage': {'total_tokens': 10},
                'finish_reason': 'stop'
            }
            
            health = self.wrapper.health_check()
            
            self.assertEqual(health['status'], 'healthy')
            self.assertTrue(health['api_available'])
    
    def test_health_check_unhealthy(self):
        """Test health check when service is unhealthy"""
        with patch.object(self.wrapper, 'create_completion') as mock_create:
            mock_create.side_effect = OpenAIError("Service unavailable")
            
            health = self.wrapper.health_check()
            
            self.assertEqual(health['status'], 'unhealthy')
            self.assertFalse(health['api_available'])
            self.assertIn('error', health)
    
    def test_request_logging(self):
        """Test that requests are properly logged"""
        with patch('apps.ai_insights.services.openai_wrapper.logger') as mock_logger:
            with patch('apps.ai_insights.services.openai_wrapper.openai') as mock_openai:
                mock_openai.ChatCompletion.create.return_value = {
                    'choices': [{'message': {'content': 'test'}, 'finish_reason': 'stop'}],
                    'usage': {'total_tokens': 20}
                }
                
                self.wrapper.create_completion(
                    messages=[{'role': 'user', 'content': 'test'}],
                    model='gpt-4o-mini',
                    request_type='general'
                )
                
                # Check that request and response were logged
                mock_logger.info.assert_called()
                call_args = [str(call) for call in mock_logger.info.call_args_list]
                
                # Should log request
                self.assertTrue(any('OpenAI request' in arg for arg in call_args))
                # Should log response
                self.assertTrue(any('OpenAI response received' in arg for arg in call_args))


@pytest.mark.django_db
class TestOpenAIWrapperIntegration:
    """Integration tests for OpenAI wrapper"""
    
    def test_wrapper_singleton(self):
        """Test that wrapper singleton works correctly"""
        from apps.ai_insights.services.openai_wrapper import openai_wrapper
        
        # Should be the same instance
        wrapper1 = openai_wrapper
        wrapper2 = openai_wrapper
        
        assert wrapper1 is wrapper2
    
    @patch('apps.ai_insights.services.openai_wrapper.openai')
    def test_invalid_response_handling(self, mock_openai):
        """Test handling of invalid response format"""
        # Mock invalid response
        mock_openai.ChatCompletion.create.return_value = {
            'choices': []  # Empty choices
        }
        
        wrapper = OpenAIWrapper()
        
        response = wrapper.create_completion(
            messages=[{'role': 'user', 'content': 'test'}],
            request_type='general'
        )
        
        # Should return fallback
        assert response.get('is_fallback', False)
    
    def test_encryption_key_validation(self):
        """Test that wrapper validates encryption key"""
        with patch('apps.ai_insights.services.openai_wrapper.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            
            with pytest.raises(ValueError, match="OPENAI_API_KEY not configured"):
                OpenAIWrapper()
    
    @patch('apps.ai_insights.services.openai_wrapper.openai')
    def test_concurrent_requests(self, mock_openai):
        """Test handling of concurrent requests"""
        import threading
        
        mock_openai.ChatCompletion.create.return_value = {
            'choices': [{'message': {'content': 'concurrent test'}, 'finish_reason': 'stop'}],
            'usage': {'total_tokens': 30}
        }
        
        wrapper = OpenAIWrapper()
        results = []
        
        def make_request():
            response = wrapper.create_completion(
                messages=[{'role': 'user', 'content': 'test'}],
                request_type='general'
            )
            results.append(response)
        
        # Create multiple threads
        threads = [threading.Thread(target=make_request) for _ in range(5)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 5
        for result in results:
            assert result['content'] == 'concurrent test'
            assert not result.get('is_fallback', False)