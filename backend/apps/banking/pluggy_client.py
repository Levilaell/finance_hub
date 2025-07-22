"""
Pluggy API Client for Brazilian Bank Integration
Replaces Open Banking Brasil with Pluggy's unified API
"""
import asyncio
import logging
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

import httpx
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class PluggyError(Exception):
    """Base exception for Pluggy API errors"""
    pass


class PluggyAuthenticationError(PluggyError):
    """Authentication errors with Pluggy API"""
    pass


class PluggyAPIError(PluggyError):
    """General API errors from Pluggy"""
    pass


class PluggyRateLimitError(PluggyError):
    """Rate limit exceeded"""
    pass


def is_retryable_error(status_code: int, error_response: dict = None) -> bool:
    """Determine if an error is retryable"""
    # Retryable HTTP status codes
    retryable_codes = {429, 500, 502, 503, 504}
    if status_code in retryable_codes:
        return True
    
    # Check for specific Pluggy error codes that are retryable
    if error_response and isinstance(error_response, dict):
        error_code = error_response.get('code', '')
        retryable_error_codes = {
            'ITEM_NOT_READY',
            'ITEM_UPDATING',
            'TEMPORARY_ERROR',
            'BANK_UNAVAILABLE'
        }
        if error_code in retryable_error_codes:
            return True
    
    return False


async def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Retry a function with exponential backoff"""
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except (httpx.TimeoutException, httpx.ConnectError, PluggyRateLimitError) as e:
            last_exception = e
            if attempt == max_retries:
                break
                
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
            await asyncio.sleep(delay)
            
        except PluggyAPIError as e:
            # Only retry if the error is retryable
            if not hasattr(e, 'is_retryable') or not e.is_retryable:
                raise
                
            last_exception = e
            if attempt == max_retries:
                break
                
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"Attempt {attempt + 1} failed with retryable error, retrying in {delay:.2f}s: {e}")
            await asyncio.sleep(delay)
    
    raise last_exception


class PluggyClient:
    """
    Pluggy API client for banking operations
    Documentation: https://docs.pluggy.ai/
    """
    
    def __init__(self):
        self._validate_configuration()
        
        # Pluggy API configuration
        self.base_url = getattr(settings, 'PLUGGY_BASE_URL', 'https://api.pluggy.ai')
        self.client_id = settings.PLUGGY_CLIENT_ID
        self.client_secret = settings.PLUGGY_CLIENT_SECRET
        
        # HTTP client with timeout and retry configuration
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            headers={
                'User-Agent': 'CaixaHub/1.0 Pluggy-Integration',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
        )
        
        # Access token cache
        self._access_token = None
        self._token_expires_at = None
    
    def _validate_configuration(self):
        """Validate required Pluggy configuration"""
        required_settings = [
            'PLUGGY_CLIENT_ID',
            'PLUGGY_CLIENT_SECRET',
        ]
        
        for setting in required_settings:
            if not getattr(settings, setting, None):
                raise ImproperlyConfigured(f"{setting} must be configured for Pluggy integration")
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                return
        
        await self._authenticate()
    
    async def _authenticate(self):
        """Authenticate with Pluggy API and get access token"""
        try:
            auth_data = {
                'clientId': self.client_id,
                'clientSecret': self.client_secret
            }
            
            response = await self.client.post(
                f"{self.base_url}/auth",
                json=auth_data
            )
            
            if response.status_code != 200:
                raise PluggyAuthenticationError(f"Authentication failed: {response.text}")
            
            data = response.json()
            
            # Pluggy returns 'apiKey' instead of 'accessToken'
            if 'apiKey' in data:
                self._access_token = data['apiKey']
            elif 'accessToken' in data:
                self._access_token = data['accessToken']
            else:
                logger.error(f"No access token in response. Available keys: {list(data.keys())}")
                raise PluggyAuthenticationError(f"Missing access token in response: {data}")
            
            logger.info("Successfully authenticated with Pluggy API")
            
            # Pluggy tokens typically expire in 2 hours
            self._token_expires_at = datetime.now() + timedelta(hours=2)
            
        except Exception as e:
            logger.error(f"Pluggy authentication error: {e}")
            raise PluggyAuthenticationError(f"Failed to authenticate: {e}")
    
    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            'User-Agent': 'CaixaHub/1.0 Pluggy-Integration',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        
        if include_auth and self._access_token:
            headers['X-API-KEY'] = self._access_token
        
        return headers
    
    async def get_connectors(self, country: str = 'BR') -> List[Dict[str, Any]]:
        """Get available bank connectors (banks that can be connected)"""
        try:
            await self._ensure_authenticated()
            
            params = {'country': country}
            
            # NÃO adicionar sandbox=True quando usar trial/produção
            use_sandbox = getattr(settings, 'PLUGGY_USE_SANDBOX', False)
            if use_sandbox:
                params['sandbox'] = True
                logger.info("🧪 Using Pluggy SANDBOX connectors")
            else:
                logger.info("🚀 Using Pluggy PRODUCTION connectors")
                
            response = await self.client.get(
                f"{self.base_url}/connectors",
                params=params,
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise PluggyAPIError(f"Failed to get connectors: {response.text}")
            
            data = response.json()
            return data.get('results', [])
            
        except Exception as e:
            logger.error(f"Error getting connectors: {e}")
            raise PluggyAPIError(f"Failed to get connectors: {e}")
    
    async def create_item(self, connector_id: int, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item (bank connection) for a user"""
        try:
            await self._ensure_authenticated()
            
            item_data = {
                'connectorId': connector_id,
                'parameters': parameters
            }
            
            response = await self.client.post(
                f"{self.base_url}/items",
                json=item_data,
                headers=self._get_headers()
            )
            
            if response.status_code not in [200, 201]:
                raise PluggyAPIError(f"Failed to create item: {response.text}")
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error creating item: {e}")
            raise PluggyAPIError(f"Failed to create item: {e}")
    
    async def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get item details and status"""
        try:
            await self._ensure_authenticated()
            
            response = await self.client.get(
                f"{self.base_url}/items/{item_id}",
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise PluggyAPIError(f"Failed to get item: {response.text}")
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting item {item_id}: {e}")
            raise PluggyAPIError(f"Failed to get item: {e}")
    
    async def update_item(self, item_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update item credentials (for MFA or credential refresh)"""
        try:
            await self._ensure_authenticated()
            
            response = await self.client.patch(
                f"{self.base_url}/items/{item_id}",
                json={'parameters': parameters},
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise PluggyAPIError(f"Failed to update item: {response.text}")
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error updating item {item_id}: {e}")
            raise PluggyAPIError(f"Failed to update item: {e}")
    
    async def sync_item(self, item_id: str) -> Dict[str, Any]:
        """Force item sync to get latest data from bank"""
        try:
            await self._ensure_authenticated()
            
            # Trigger sync by sending empty PATCH request
            response = await self.client.patch(
                f"{self.base_url}/items/{item_id}",
                json={},  # Empty body triggers sync
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise PluggyAPIError(f"Failed to sync item: {response.text}")
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error syncing item {item_id}: {e}")
            raise PluggyAPIError(f"Failed to sync item: {e}")
    
    async def delete_item(self, item_id: str) -> bool:
        """Delete an item (disconnect bank)"""
        try:
            await self._ensure_authenticated()
            
            response = await self.client.delete(
                f"{self.base_url}/items/{item_id}",
                headers=self._get_headers()
            )
            
            return response.status_code == 204
            
        except Exception as e:
            logger.error(f"Error deleting item {item_id}: {e}")
            raise PluggyAPIError(f"Failed to delete item: {e}")
    
    async def get_accounts(self, item_id: str) -> List[Dict[str, Any]]:
        """Get accounts for an item"""
        try:
            await self._ensure_authenticated()
            
            params = {'itemId': item_id}
            response = await self.client.get(
                f"{self.base_url}/accounts",
                params=params,
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise PluggyAPIError(f"Failed to get accounts: {response.text}")
            
            data = response.json()
            return data.get('results', [])
            
        except Exception as e:
            logger.error(f"Error getting accounts for item {item_id}: {e}")
            raise PluggyAPIError(f"Failed to get accounts: {e}")
    
    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """Get specific account details"""
        try:
            await self._ensure_authenticated()
            
            response = await self.client.get(
                f"{self.base_url}/accounts/{account_id}",
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise PluggyAPIError(f"Failed to get account: {response.text}")
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting account {account_id}: {e}")
            raise PluggyAPIError(f"Failed to get account: {e}")
    
    async def get_transactions(
        self, 
        account_id: str, 
        from_date: Optional[str] = None, 
        to_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 500
    ) -> Dict[str, Any]:
        """Get transactions for an account"""
        try:
            await self._ensure_authenticated()
            
            params = {
                'accountId': account_id,
                'page': page,
                'pageSize': min(page_size, 500)  # Pluggy max page size
            }
            
            if from_date:
                params['from'] = from_date
            if to_date:
                params['to'] = to_date
            
            response = await self.client.get(
                f"{self.base_url}/transactions",
                params=params,
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise PluggyAPIError(f"Failed to get transactions: {response.text}")
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting transactions for account {account_id}: {e}")
            raise PluggyAPIError(f"Failed to get transactions: {e}")
    
    async def get_identity(self, item_id: str) -> Dict[str, Any]:
        """Get identity information for an item"""
        try:
            await self._ensure_authenticated()
            
            params = {'itemId': item_id}
            response = await self.client.get(
                f"{self.base_url}/identity",
                params=params,
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise PluggyAPIError(f"Failed to get identity: {response.text}")
            
            data = response.json()
            return data.get('results', [])
            
        except Exception as e:
            logger.error(f"Error getting identity for item {item_id}: {e}")
            raise PluggyAPIError(f"Failed to get identity: {e}")
    
    async def create_connect_token(self, item_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a connect token for Pluggy Connect widget"""
        try:
            await self._ensure_authenticated()
            
            token_data = {}
            if item_id:
                token_data['itemId'] = item_id
            
            response = await self.client.post(
                f"{self.base_url}/connect_token",
                json=token_data,
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise PluggyAPIError(f"Failed to create connect token: {response.text}")
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error creating connect token: {e}")
            raise PluggyAPIError(f"Failed to create connect token: {e}")
    
    async def get_webhook_url(self) -> str:
        """Get configured webhook URL"""
        try:
            await self._ensure_authenticated()
            
            response = await self.client.get(
                f"{self.base_url}/webhooks",
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                return ""
            
            data = response.json()
            webhooks = data.get('results', [])
            return webhooks[0].get('url', '') if webhooks else ""
            
        except Exception as e:
            logger.warning(f"Error getting webhook URL: {e}")
            return ""
    
    async def create_webhook(self, url: str, events: List[str] = None) -> Dict[str, Any]:
        """Create a webhook for real-time updates"""
        try:
            await self._ensure_authenticated()
            
            if events is None:
                events = [
                    'item/created',
                    'item/updated', 
                    'item/error',
                    'item/login_succeeded',
                    'account/created',
                    'account/updated',
                    'transactions/created',
                    'transactions/updated'
                ]
            
            webhook_data = {
                'url': url,
                'events': events
            }
            
            response = await self.client.post(
                f"{self.base_url}/webhooks",
                json=webhook_data,
                headers=self._get_headers()
            )
            
            if response.status_code not in [200, 201]:
                raise PluggyAPIError(f"Failed to create webhook: {response.text}")
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            raise PluggyAPIError(f"Failed to create webhook: {e}")
    
    async def close(self):
        """Close HTTP client connections"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class PluggyService:
    """High-level service for Pluggy operations"""
    
    def __init__(self):
        self.client = PluggyClient()
        self._connectors_cache = None
        self._cache_expires_at = None
    
    async def get_supported_banks(self) -> List[Dict[str, Any]]:
        """Get list of supported banks with caching"""
        try:
            # Check cache
            if (self._connectors_cache and self._cache_expires_at and 
                datetime.now() < self._cache_expires_at):
                return self._connectors_cache
            
            # Fetch from API
            connectors = await self.client.get_connectors()
            
            # Filter for banks only and format for our use
            banks = []
            for connector in connectors:
                if connector.get('type') == 'PERSONAL_BANK':
                    banks.append({
                        'id': connector['id'],
                        'name': connector['name'],
                        'code': str(connector['id']),  # Use Pluggy ID as code
                        'logo': connector.get('imageUrl'),
                        'color': connector.get('primaryColor', '#000000'),
                        'country': connector.get('country', 'BR'),
                        'health_status': connector.get('health', {}).get('status', 'ONLINE'),
                        'supports_identity': connector.get('supportsIdentity', False),
                        'supports_payment_initiation': connector.get('supportsPaymentInitiation', False),
                    })
            
            # Cache for 1 hour
            self._connectors_cache = banks
            self._cache_expires_at = datetime.now() + timedelta(hours=1)
            
            return banks
            
        except Exception as e:
            logger.error(f"Error getting supported banks: {e}")
            # Return cached data if available, even if expired
            return self._connectors_cache or []
    
    async def initiate_bank_connection(self, user_id: int, bank_id: int) -> Dict[str, Any]:
        """Initiate bank connection process"""
        try:
            # Create connect token for the specific bank
            connect_data = await self.client.create_connect_token()
            
            return {
                'connect_token': connect_data['accessToken'],
                'bank_id': bank_id,
                'user_id': user_id,
                'expires_at': datetime.now() + timedelta(hours=1)
            }
            
        except Exception as e:
            logger.error(f"Error initiating bank connection: {e}")
            raise PluggyAPIError(f"Failed to initiate bank connection: {e}")
    
    async def close(self):
        """Close service connections"""
        await self.client.close()


# Global service instance
pluggy_service = PluggyService()