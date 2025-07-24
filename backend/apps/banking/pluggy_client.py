"""
Pluggy API Client
Handles authentication and communication with Pluggy API
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


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
        
    def _get_api_key(self) -> str:
        """
        Get or create API key using client credentials
        """
        # Check cache first
        cache_key = f'pluggy_api_key_{self.client_id}'
        cached_key = cache.get(cache_key)
        if cached_key:
            return cached_key
            
        # Create new API key
        try:
            response = requests.post(
                f"{self.base_url}/auth",
                json={
                    "clientId": self.client_id,
                    "clientSecret": self.client_secret
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            api_key = data['apiKey']
            
            # Cache for 55 minutes (API key expires in 60 minutes)
            cache.set(cache_key, api_key, 55 * 60)
            
            logger.info("Successfully created new Pluggy API key")
            return api_key
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create API key: {e}")
            raise Exception(f"Failed to authenticate with Pluggy: {str(e)}")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """
        Make authenticated request to Pluggy API
        """
        if not self.api_key:
            self.api_key = self._get_api_key()
            
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            # If unauthorized, refresh API key and retry
            if response.status_code == 401:
                logger.info("API key expired, refreshing...")
                cache.delete(f'pluggy_api_key_{self.client_id}')
                self.api_key = self._get_api_key()
                headers['X-API-KEY'] = self.api_key
                
                response = requests.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {method} {endpoint} - {e}")
            raise Exception(f"Pluggy API error: {str(e)}")
    
    def get_connectors(self, country: str = 'BR', type: Optional[str] = None, sandbox: Optional[bool] = None) -> List[Dict]:
        """
        List available bank connectors
        """
        params = {
            'countries': country
        }
        if type:
            params['types'] = type
        if sandbox is not None:
            params['sandbox'] = sandbox
        elif self.use_sandbox:
            params['sandbox'] = True
            
        response = self._make_request('GET', '/connectors', params=params)
        
        # Handle paginated response
        if isinstance(response, dict) and 'results' in response:
            return response['results']
        return response
    
    def create_connect_token(self, item_id: Optional[str] = None, client_user_id: Optional[str] = None) -> Dict:
        """
        Create a connect token for Pluggy Connect widget
        """
        data = {}
        if item_id:
            data['itemId'] = item_id
        if client_user_id:
            data['clientUserId'] = client_user_id
            
        response = self._make_request('POST', '/connect_token', data)
        return {
            'accessToken': response['accessToken'],
            'connectUrl': f"{settings.PLUGGY_CONNECT_URL}?token={response['accessToken']}"
        }
    
    def create_item(self, connector_id: int, credentials: Dict, client_user_id: Optional[str] = None) -> Dict:
        """
        Create a new item (bank connection)
        """
        data = {
            'connectorId': connector_id,
            'parameters': credentials
        }
        if client_user_id:
            data['clientUserId'] = client_user_id
            
        return self._make_request('POST', '/items', data)
    
    def get_item(self, item_id: str) -> Dict:
        """
        Get item details
        """
        return self._make_request('GET', f'/items/{item_id}')
    
    def update_item(self, item_id: str) -> Dict:
        """
        Update an existing item (refresh data)
        """
        return self._make_request('PATCH', f'/items/{item_id}')
    
    def delete_item(self, item_id: str) -> None:
        """
        Delete an item
        """
        self._make_request('DELETE', f'/items/{item_id}')
    
    def get_accounts(self, item_id: str) -> List[Dict]:
        """
        Get accounts for an item
        """
        return self._make_request('GET', f'/accounts?itemId={item_id}')
    
    def get_account(self, account_id: str) -> Dict:
        """
        Get specific account details
        """
        return self._make_request('GET', f'/accounts/{account_id}')
    
    def get_transactions(self, account_id: str, from_date: Optional[datetime] = None, 
                        to_date: Optional[datetime] = None, page: int = 1, page_size: int = 500) -> Dict:
        """
        Get transactions for an account
        """
        params = {
            'accountId': account_id,
            'pageSize': page_size,
            'page': page
        }
        
        if from_date:
            params['from'] = from_date.strftime('%Y-%m-%d')
        if to_date:
            params['to'] = to_date.strftime('%Y-%m-%d')
            
        return self._make_request('GET', '/transactions', params=params)
    
    def get_transaction(self, transaction_id: str) -> Dict:
        """
        Get specific transaction details
        """
        return self._make_request('GET', f'/transactions/{transaction_id}')
    
    def get_identity(self, item_id: str) -> Dict:
        """
        Get identity information for an item
        """
        return self._make_request('GET', f'/identity?itemId={item_id}')
    
    def get_income_reports(self, item_id: str) -> List[Dict]:
        """
        Get income reports for an item
        """
        return self._make_request('GET', f'/income/reports?itemId={item_id}')
    
    def get_investments(self, item_id: str) -> List[Dict]:
        """
        Get investments for an item
        """
        return self._make_request('GET', f'/investments?itemId={item_id}')
    
    def get_investment_transactions(self, investment_id: str) -> List[Dict]:
        """
        Get transactions for a specific investment
        """
        return self._make_request('GET', f'/investments/{investment_id}/transactions')
    
    def validate_webhook(self, signature: str, payload: str) -> bool:
        """
        Validate webhook signature
        """
        import hmac
        import hashlib
        
        webhook_secret = getattr(settings, 'PLUGGY_WEBHOOK_SECRET', '')
        if not webhook_secret:
            logger.warning("PLUGGY_WEBHOOK_SECRET not configured")
            return False
            
        expected_signature = hmac.new(
            webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)