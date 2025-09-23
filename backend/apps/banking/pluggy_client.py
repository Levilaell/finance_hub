"""
Pluggy API Client for banking integration
"""
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger('apps.banking.pluggy_client')


class PluggyError(Exception):
    """Base exception for Pluggy API errors"""
    pass


class PluggyAuthError(PluggyError):
    """Authentication errors with Pluggy API"""
    pass


class PluggyRateLimitError(PluggyError):
    """Rate limiting errors"""
    pass


class PluggyClient:
    """
    Pluggy API Client
    Handles authentication, rate limiting, and API calls
    """
    
    def __init__(self):
        self.base_url = getattr(settings, 'PLUGGY_BASE_URL', 'https://api.pluggy.ai')
        self.client_id = getattr(settings, 'PLUGGY_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'PLUGGY_CLIENT_SECRET', '')
        self.use_sandbox = getattr(settings, 'PLUGGY_USE_SANDBOX', False)
        
        if not self.client_id or not self.client_secret:
            raise PluggyError("Pluggy credentials not configured")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'CaixaHub/1.0'
        })
        
        self._access_token = None
        self._token_expires_at = None

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def _get_access_token(self) -> str:
        """Get or refresh access token"""
        cache_key = 'pluggy_access_token'
        token = cache.get(cache_key)
        
        if token:
            return token
        
        logger.info("Requesting new Pluggy access token")
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth",
                json={
                    'clientId': self.client_id,
                    'clientSecret': self.client_secret
                },
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            access_token = data.get('accessToken')
            
            if not access_token:
                raise PluggyAuthError("No access token in response")
            
            # Cache token for 50 minutes (Pluggy tokens last 1 hour)
            cache.set(cache_key, access_token, 50 * 60)
            
            logger.info("Successfully obtained Pluggy access token")
            return access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Pluggy access token: {e}")
            raise PluggyAuthError(f"Authentication failed: {e}")

    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: int = 60
    ) -> Dict[Any, Any]:
        """Make authenticated request to Pluggy API"""
        
        # Get access token
        access_token = self._get_access_token()
        
        # Prepare headers
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-API-KEY': self.client_id  # Some endpoints may require this
        }
        
        url = f"{self.base_url}{endpoint}"
        
        logger.debug(f"Making {method} request to {url}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=timeout
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited by Pluggy API. Retry after {retry_after} seconds")
                raise PluggyRateLimitError(f"Rate limited. Retry after {retry_after} seconds")
            
            # Handle authentication errors
            if response.status_code == 401:
                # Clear cached token and retry once
                cache.delete('pluggy_access_token')
                access_token = self._get_access_token()
                headers['Authorization'] = f'Bearer {access_token}'
                
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers,
                    timeout=timeout
                )
            
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Successful response from {endpoint}")
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout on {method} {endpoint}")
            raise PluggyError(f"Request timeout: {endpoint}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed {method} {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('message', str(e))
                except:
                    error_message = str(e)
            else:
                error_message = str(e)
            raise PluggyError(f"API request failed: {error_message}")

    # === CONNECTOR METHODS ===
    
    def get_connectors(self, country: str = 'BR') -> List[Dict]:
        """Get list of available connectors"""
        params = {'country': country}
        if self.use_sandbox:
            params['sandbox'] = 'true'
            
        response = self._make_request('GET', '/connectors', params=params)
        return response.get('results', [])
    
    def get_connector(self, connector_id: int) -> Dict:
        """Get specific connector details"""
        return self._make_request('GET', f'/connectors/{connector_id}')

    # === ITEM METHODS ===
    
    def create_item(
        self, 
        connector_id: int,
        credentials: Dict,
        webhook_url: Optional[str] = None,
        client_user_id: Optional[str] = None,
        products: Optional[List[str]] = None
    ) -> Dict:
        """Create a new item (bank connection)"""
        
        data = {
            'connectorId': connector_id,
            'credentials': credentials
        }
        
        if webhook_url:
            data['webhookUrl'] = webhook_url
        if client_user_id:
            data['clientUserId'] = client_user_id
        if products:
            data['products'] = products
        
        logger.info(f"Creating item for connector {connector_id}")
        return self._make_request('POST', '/items', data=data)
    
    def get_item(self, item_id: str) -> Dict:
        """Get item details"""
        return self._make_request('GET', f'/items/{item_id}')
    
    def update_item(self, item_id: str, credentials: Dict) -> Dict:
        """Update item credentials"""
        data = {'credentials': credentials}
        return self._make_request('PATCH', f'/items/{item_id}', data=data)
    
    def delete_item(self, item_id: str) -> bool:
        """Delete an item"""
        try:
            self._make_request('DELETE', f'/items/{item_id}')
            return True
        except PluggyError:
            return False

    # === ACCOUNT METHODS ===
    
    def get_accounts(self, item_id: str) -> List[Dict]:
        """Get accounts for an item"""
        response = self._make_request('GET', f'/accounts?itemId={item_id}')
        return response.get('results', [])
    
    def get_account(self, account_id: str) -> Dict:
        """Get specific account details"""
        return self._make_request('GET', f'/accounts/{account_id}')

    # === TRANSACTION METHODS ===
    
    def get_transactions(
        self,
        account_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 500
    ) -> Dict:
        """Get transactions for an account"""
        
        params = {
            'accountId': account_id,
            'page': page,
            'pageSize': min(page_size, 500)  # Pluggy max is 500
        }
        
        if from_date:
            params['from'] = from_date.strftime('%Y-%m-%d')
        if to_date:
            params['to'] = to_date.strftime('%Y-%m-%d')
        
        response = self._make_request('GET', '/transactions', params=params)
        return response
    
    def get_all_transactions_for_account(
        self,
        account_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get all transactions for an account (handles pagination)"""
        
        all_transactions = []
        page = 1
        page_size = 500
        
        while True:
            logger.debug(f"Fetching transactions page {page} for account {account_id}")
            
            response = self.get_transactions(
                account_id=account_id,
                from_date=from_date,
                to_date=to_date,
                page=page,
                page_size=page_size
            )
            
            transactions = response.get('results', [])
            if not transactions:
                break
                
            all_transactions.extend(transactions)
            
            # Check if we have more pages
            total = response.get('total', 0)
            if len(all_transactions) >= total:
                break
                
            page += 1
        
        logger.info(f"Retrieved {len(all_transactions)} transactions for account {account_id}")
        return all_transactions

    # === CATEGORY METHODS ===
    
    def get_categories(self) -> List[Dict]:
        """Get transaction categories"""
        response = self._make_request('GET', '/categories')
        return response.get('results', [])

    # === IDENTITY METHODS ===
    
    def get_identity(self, item_id: str) -> Dict:
        """Get identity information for an item"""
        return self._make_request('GET', f'/identity/{item_id}')

    # === INVESTMENT METHODS ===
    
    def get_investments(self, item_id: str) -> List[Dict]:
        """Get investments for an item"""
        response = self._make_request('GET', f'/investments?itemId={item_id}')
        return response.get('results', [])
    
    def get_investment_transactions(
        self,
        item_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get investment transactions"""
        
        params = {'itemId': item_id}
        if from_date:
            params['from'] = from_date.strftime('%Y-%m-%d')
        if to_date:
            params['to'] = to_date.strftime('%Y-%m-%d')
        
        response = self._make_request('GET', '/investment-transactions', params=params)
        return response.get('results', [])

    # === PAYMENT METHODS ===
    
    def get_payment_data(self, item_id: str) -> Dict:
        """Get payment data for an item"""
        return self._make_request('GET', f'/payment-data/{item_id}')

    # === UTILITY METHODS ===
    
    def validate_credentials(self, connector_id: int, credentials: Dict) -> bool:
        """Validate credentials without creating an item"""
        try:
            data = {
                'connectorId': connector_id,
                'credentials': credentials
            }
            self._make_request('POST', '/validate-credentials', data=data)
            return True
        except PluggyError:
            return False
    
    def get_webhook_events(self, item_id: str) -> List[Dict]:
        """Get webhook events for an item"""
        response = self._make_request('GET', f'/webhooks/{item_id}')
        return response.get('results', [])
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            self._make_request('GET', '/connectors', params={'country': 'BR', 'limit': 1})
            return True
        except PluggyError:
            return False


# === UTILITY FUNCTIONS ===

def format_pluggy_date(date_str: str) -> datetime:
    """Convert Pluggy date string to datetime"""
    if not date_str:
        return None
    
    try:
        # Pluggy uses ISO format: 2023-01-01T10:00:00.000Z
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        # Fallback for different formats
        try:
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Could not parse Pluggy date: {date_str}")
                return timezone.now()


def get_pluggy_error_message(error_data: Dict) -> str:
    """Extract user-friendly error message from Pluggy error response"""
    
    if isinstance(error_data, str):
        return error_data
    
    # Common error patterns
    error_code = error_data.get('code', '')
    error_message = error_data.get('message', '')
    error_details = error_data.get('details', '')
    
    # Map common errors to user-friendly messages
    error_mappings = {
        'INVALID_CREDENTIALS': 'Credenciais inválidas. Verifique seu usuário e senha.',
        'ACCOUNT_LOCKED': 'Conta bloqueada no banco. Entre em contato com sua instituição.',
        'CONNECTION_ERROR': 'Erro de conexão com o banco. Tente novamente em alguns minutos.',
        'SITE_NOT_AVAILABLE': 'Site do banco indisponível. Tente novamente mais tarde.',
        'USER_INPUT_TIMEOUT': 'Tempo limite excedido. Tente novamente.',
        'INVALID_CREDENTIALS_MFA': 'Código de autenticação inválido.',
        'USER_NOT_SUPPORTED': 'Tipo de conta não suportado.',
        'ACCOUNT_NEEDS_ACTION': 'Sua conta precisa de ação no site do banco.',
    }
    
    if error_code in error_mappings:
        return error_mappings[error_code]
    
    if error_message:
        return error_message
    
    if error_details:
        return error_details
    
    return 'Erro desconhecido na conexão bancária.'