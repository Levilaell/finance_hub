"""
Pluggy API Client
Handles authentication and communication with Pluggy API
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class PluggyError(Exception):
    """Custom exception for Pluggy API errors"""
    pass


class PluggyClient:
    """
    Client for Pluggy API communication
    """
    
    def __init__(self):
        self.client_id = settings.PLUGGY_CLIENT_ID
        self.client_secret = settings.PLUGGY_CLIENT_SECRET
        self.base_url = settings.PLUGGY_BASE_URL
        self.use_sandbox = getattr(settings, 'PLUGGY_USE_SANDBOX', True)
        self.api_key = None
        self.timeout = 30
        
        # Log configuration for debugging
        logger.info(f"Pluggy Client initialized - Base URL: {self.base_url}, Sandbox: {self.use_sandbox}")
        
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        pass
        
    def _get_api_key(self) -> str:
        """
        Get or create API key using client credentials
        """
        # Check cache first
        cache_key = f'pluggy_api_key_{self.client_id}'
        api_key = cache.get(cache_key)
        
        if api_key:
            return api_key
            
        # Create new API key
        url = f"{self.base_url}/auth"
        
        try:
            response = requests.post(
                url,
                json={
                    "clientId": self.client_id,
                    "clientSecret": self.client_secret
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            api_key = data['apiKey']
            
            # Cache for 23 hours (tokens last 24 hours)
            cache.set(cache_key, api_key, 82800)
            
            return api_key
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get API key: {e}")
            raise PluggyError(f"Authentication failed: {str(e)}")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Pluggy API
        """
        if not self.api_key:
            self.api_key = self._get_api_key()
            
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=self.timeout
            )
            
            # Handle 401 - token might be expired
            if response.status_code == 401:
                logger.info("API key expired, refreshing...")
                cache_key = f'pluggy_api_key_{self.client_id}'
                cache.delete(cache_key)
                self.api_key = self._get_api_key()
                
                # Retry request
                headers["X-API-KEY"] = self.api_key
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=self.timeout
                )
            
            response.raise_for_status()
            return response.json() if response.text else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {method} {endpoint} - {e}")
            raise PluggyError(f"API request failed: {str(e)}")
    
    # ===== Connectors =====
    
    def get_connectors(self, **filters) -> List[Dict[str, Any]]:
        """
        Get list of available connectors (banks)
        """
        params = {}
        if self.use_sandbox:
            params['sandbox'] = 'true'
        params.update(filters)
        
        data = self._make_request('GET', 'connectors', params=params)
        return data.get('results', [])
    
    def get_connector(self, connector_id: int) -> Dict[str, Any]:
        """
        Get specific connector details
        """
        return self._make_request('GET', f'connectors/{connector_id}')
    
    # ===== Items =====
    
    def create_item(self, connector_id: int, parameters: Dict[str, str]) -> Dict[str, Any]:
        """
        Create new item (connection to bank)
        """
        data = {
            "connectorId": connector_id,
            "parameters": parameters
        }
        return self._make_request('POST', 'items', data=data)
    
    def get_item(self, item_id: str) -> Dict[str, Any]:
        """
        Get item details
        """
        return self._make_request('GET', f'items/{item_id}')
    
    def update_item(self, item_id: str, parameters: Dict[str, str]) -> Dict[str, Any]:
        """
        Update item credentials
        """
        data = {"parameters": parameters}
        return self._make_request('PATCH', f'items/{item_id}', data=data)
    
    def delete_item(self, item_id: str) -> None:
        """
        Delete item
        """
        self._make_request('DELETE', f'items/{item_id}')
    
    def update_item_mfa(self, item_id: str, parameters: Dict[str, str]) -> Dict[str, Any]:
        """
        Send MFA response
        """
        data = {"parameters": parameters}
        return self._make_request('PATCH', f'items/{item_id}/mfa', data=data)
    
    # ===== Accounts =====
    
    def get_accounts(self, item_id: str) -> List[Dict[str, Any]]:
        """
        Get accounts for an item
        """
        data = self._make_request('GET', f'accounts', params={'itemId': item_id})
        return data.get('results', [])
    
    def get_account(self, account_id: str) -> Dict[str, Any]:
        """
        Get specific account
        """
        return self._make_request('GET', f'accounts/{account_id}')
    
    # ===== Transactions =====
    
    def get_transactions(
        self, 
        account_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 500
    ) -> Dict[str, Any]:
        """
        Get transactions for an account
        """
        params = {
            'accountId': account_id,
            'page': page,
            'pageSize': page_size
        }
        
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
            
        return self._make_request('GET', 'transactions', params=params)
    
    def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get specific transaction
        """
        return self._make_request('GET', f'transactions/{transaction_id}')
    
    # ===== Categories =====
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get available transaction categories
        """
        data = self._make_request('GET', 'categories')
        return data.get('results', [])
    
    # ===== Connect Token =====
    
    def create_connect_token(
        self,
        item_id: Optional[str] = None,
        client_user_id: Optional[str] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create connect token for Pluggy Connect widget
        """
        data = {}
        
        if item_id:
            data['itemId'] = item_id
        if client_user_id:
            data['clientUserId'] = client_user_id
        if webhook_url:
            data['webhookUrl'] = webhook_url
            
        return self._make_request('POST', 'connect_token', data=data)
    
    # ===== Webhooks =====
    
    def validate_webhook(self, signature: str, payload: str) -> bool:
        """
        Validate webhook signature
        """
        import hmac
        import hashlib
        
        webhook_secret = getattr(settings, 'PLUGGY_WEBHOOK_SECRET', '')
        if not webhook_secret:
            logger.warning("No webhook secret configured")
            return True  # Allow in development
            
        expected_signature = hmac.new(
            webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    # ===== Consent (Open Finance) =====
    
    def get_consent(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get consent details for Open Finance item
        """
        try:
            return self._make_request('GET', f'consents/{item_id}')
        except PluggyError:
            return None
    
    def revoke_consent(self, item_id: str) -> None:
        """
        Revoke consent for Open Finance item
        """
        self._make_request('DELETE', f'consents/{item_id}')