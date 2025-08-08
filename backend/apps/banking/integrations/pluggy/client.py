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
            
            # Cache for 1h50min (tokens expire in 2 hours per Pluggy docs)
            cache.set(cache_key, api_key, 6600)  # 110 minutes
            
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
        client_user_id: str,
        item_id: Optional[str] = None,
        webhook_url: Optional[str] = None,
        oauth_redirect_uri: Optional[str] = None,
        avoid_duplicates: Optional[bool] = None,
        country_codes: Optional[List[str]] = None,
        connector_types: Optional[List[str]] = None,
        connector_ids: Optional[List[int]] = None,
        products_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a connect token for Pluggy Connect
        
        Args:
            client_user_id: User reference for end-to-end traceability
            item_id: Item ID for updating existing connection
            webhook_url: URL to receive item events
            oauth_redirect_uri: Redirect URL after connect flow
            avoid_duplicates: Prevent creating duplicate items
            country_codes: List of country codes to filter connectors (e.g., ['BR', 'US'])
            connector_types: List of connector types to filter (e.g., ['PERSONAL_BANK', 'BUSINESS_BANK'])
            connector_ids: List of specific connector IDs to show
            products_types: List of product types to enable (e.g., ['ACCOUNTS', 'TRANSACTIONS'])
            
        Returns:
            Dict with accessToken and other connection details
        """
        # Build payload according to API v2 documentation
        payload: Dict[str, Any] = {}
        
        # Add parameters directly to payload (not nested in options)
        if client_user_id:
            payload["clientUserId"] = client_user_id
        if item_id:
            payload["itemId"] = item_id
        if webhook_url:
            payload["webhookUrl"] = webhook_url
        if oauth_redirect_uri:
            payload["oauthRedirectUri"] = oauth_redirect_uri
        if avoid_duplicates is not None:
            payload["avoidDuplicates"] = avoid_duplicates
        if country_codes:
            payload["countryCodes"] = country_codes
        if connector_types:
            payload["connectorTypes"] = connector_types
        if connector_ids:
            payload["connectorIds"] = connector_ids
        if products_types:
            payload["productsTypes"] = products_types
            
        # Use correct endpoint with underscore
        return self._make_request("POST", "connect_token", data=payload)
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
    
    # ===== Investments =====
    
    def get_investments(self, item_id: str) -> List[Dict[str, Any]]:
        """
        Get investments for an item
        """
        data = self._make_request('GET', 'investments', params={'itemId': item_id})
        return data.get('results', [])
    
    # ===== Categorization =====
    
    def categorize_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Categorize transactions using Pluggy's categorization API
        Maximum 5000 transactions per request
        """
        if len(transactions) > 5000:
            raise PluggyError("Maximum 5000 transactions per categorization request")
        
        data = {"transactions": transactions}
        return self._make_request('POST', 'categorize', data=data)
    
    def update_transaction_category(self, transaction_id: str, category_id: str) -> Dict[str, Any]:
        """
        Update a transaction's category
        This provides feedback to Pluggy's categorization model
        
        Args:
            transaction_id: The transaction ID to update
            category_id: The new category ID
            
        Returns:
            Updated transaction data
        """
        data = {"categoryId": category_id}
        return self._make_request('PATCH', f'transactions/{transaction_id}', data=data)
    
    # ===== Webhook Validation =====
    
    def validate_webhook(self, signature: str, payload: str) -> bool:
        """
        Validate webhook signature (alias for backward compatibility)
        """
        return self.validate_webhook_signature(signature, payload.encode('utf-8'))
    
    def validate_webhook_signature(self, signature: str, payload: bytes) -> bool:
        """
        Validate webhook signature using HMAC-SHA256
        
        Args:
            signature: The X-Pluggy-Signature header value
            payload: The raw request body bytes
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not signature:
            logger.warning("No signature provided for webhook validation")
            return False
        
        if not payload:
            logger.warning("Empty payload for webhook validation")
            return False
        
        # Get webhook secret from settings
        webhook_secret = getattr(settings, 'PLUGGY_WEBHOOK_SECRET', None)
        if not webhook_secret:
            logger.warning("PLUGGY_WEBHOOK_SECRET not configured, accepting webhook without validation")
            return True
        
        try:
            import hmac
            import hashlib
            
            # Compute expected signature
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures (constant time comparison to prevent timing attacks)
            is_valid = hmac.compare_digest(signature.lower(), expected_signature.lower())
            
            if not is_valid:
                logger.warning(f"Invalid webhook signature. Expected: {expected_signature[:10]}..., Got: {signature[:10]}...")
            else:
                logger.info("Webhook signature validated successfully")
                
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            return False