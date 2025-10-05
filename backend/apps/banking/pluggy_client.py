"""
Pluggy API Client - Handles authentication and communication with Pluggy API
Docs: https://docs.pluggy.ai/docs/authentication
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class PluggyClient:
    """
    Client for Pluggy API communication.
    Manages authentication tokens and API requests.
    Reference: https://docs.pluggy.ai/reference/getting-started-with-your-api
    """

    def __init__(self):
        # Use Django settings instead of direct env access
        self.base_url = getattr(settings, 'PLUGGY_BASE_URL', 'https://api.pluggy.ai')
        self.client_id = getattr(settings, 'PLUGGY_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'PLUGGY_CLIENT_SECRET', None)
        self.use_sandbox = getattr(settings, 'PLUGGY_USE_SANDBOX', False)

        if not self.client_id or not self.client_secret:
            raise ValueError("PLUGGY_CLIENT_ID and PLUGGY_CLIENT_SECRET must be set in Django settings")

    def _get_api_key(self) -> str:
        """
        Get or refresh API Key (expires in 2 hours).
        Uses caching to avoid unnecessary token generation.
        Ref: https://docs.pluggy.ai/reference/auth-create
        """
        cached_key = cache.get('pluggy_api_key')
        if cached_key:
            return cached_key

        url = f"{self.base_url}/auth"
        payload = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            api_key = data.get('apiKey')

            # Cache for 1h50m (just under 2 hours)
            cache.set('pluggy_api_key', api_key, 6600)
            return api_key

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get API key: {e}")
            raise

    def _get_connect_token(self, item_id: Optional[str] = None) -> str:
        """
        Get Connect Token for frontend usage (expires in 30 minutes).
        Ref: https://docs.pluggy.ai/docs/use-our-sdks-to-authenticate
        """
        cached_key = cache.get(f'pluggy_connect_token_{item_id or "new"}')
        if cached_key:
            return cached_key

        url = f"{self.base_url}/connect_token"
        headers = self._get_headers()
        payload = {}
        if item_id:
            payload['itemId'] = item_id

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            token = data.get('accessToken')

            # Cache for 25 minutes
            cache.set(f'pluggy_connect_token_{item_id or "new"}', token, 1500)
            return token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get connect token: {e}")
            raise

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication for API requests."""
        return {
            'X-API-KEY': self._get_api_key(),
            'Content-Type': 'application/json'
        }

    def get_connectors(self, country: str = 'BR', sandbox: Optional[bool] = None) -> List[Dict]:
        """
        Retrieve available bank connectors.
        Ref: https://docs.pluggy.ai/reference/connectors-retrieve
        """
        url = f"{self.base_url}/connectors"
        # Use sandbox from settings if not explicitly provided
        if sandbox is None:
            sandbox = self.use_sandbox

        params = {
            'countries': country,
            'sandbox': sandbox
        }

        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            return response.json()['results']
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get connectors: {e}")
            raise

    def create_item(self, connector_id: int, credentials: Dict[str, Any],
                   webhook_url: Optional[str] = None, user_data: Optional[Dict] = None) -> Dict:
        """
        Create a new item (bank connection).
        Ref: https://docs.pluggy.ai/reference/items-create
        """
        url = f"{self.base_url}/items"
        payload = {
            'connectorId': connector_id,
            'parameters': credentials
        }

        if webhook_url:
            payload['webhookUrl'] = webhook_url

        if user_data:
            payload['clientUserId'] = user_data.get('id')

        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create item: {e}")
            raise

    def get_item(self, item_id: str) -> Dict:
        """
        Get item details and status.
        Ref: https://docs.pluggy.ai/reference/items-retrieve
        """
        url = f"{self.base_url}/items/{item_id}"

        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get item {item_id}: {e}")
            raise

    def update_item(self, item_id: str, credentials: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Update item to trigger new data synchronization.
        Can be used with or without credentials.
        Ref: https://docs.pluggy.ai/reference/items-update

        Args:
            item_id: The Pluggy item ID
            credentials: Optional credentials for reconnection or MFA

        Returns:
            Updated item data
        """
        url = f"{self.base_url}/items/{item_id}"

        # Empty payload triggers sync with existing credentials
        # Credentials are only needed for reconnection or MFA
        payload = {}
        if credentials:
            payload['parameters'] = credentials

        logger.info(f"Updating item {item_id} with payload: {payload}")

        try:
            response = requests.patch(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            result = response.json()
            logger.info(f"Item {item_id} updated successfully. Status: {result.get('status')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update item {item_id}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise

    def trigger_item_update(self, item_id: str) -> Dict:
        """
        Trigger a data synchronization for an item without changing credentials.
        This forces Pluggy to fetch new data from the financial institution.
        Ref: https://docs.pluggy.ai/docs/data-sync-update-an-item

        Args:
            item_id: The Pluggy item ID

        Returns:
            Updated item data
        """
        logger.info(f"Triggering data sync for item {item_id}")
        return self.update_item(item_id, credentials=None)

    def send_mfa(self, item_id: str, mfa_value: str, mfa_parameter_name: str = 'token') -> Dict:
        """
        Send MFA (Multi-Factor Authentication) for an item.
        Used when item status is WAITING_USER_INPUT.
        Ref: https://docs.pluggy.ai/reference/items-send-mfa

        Args:
            item_id: The Pluggy item ID
            mfa_value: The MFA value (e.g., token, code)
            mfa_parameter_name: The parameter name expected by the connector (default: 'token')

        Returns:
            Updated item data
        """
        url = f"{self.base_url}/items/{item_id}/mfa"
        payload = {
            mfa_parameter_name: mfa_value
        }

        logger.info(f"Sending MFA for item {item_id}")

        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            result = response.json()
            logger.info(f"MFA sent successfully for item {item_id}. Status: {result.get('status')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send MFA for item {item_id}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise

    def delete_item(self, item_id: str) -> bool:
        """
        Delete an item (disconnect bank).
        Ref: https://docs.pluggy.ai/reference/items-delete
        """
        url = f"{self.base_url}/items/{item_id}"

        try:
            response = requests.delete(url, headers=self._get_headers())
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete item {item_id}: {e}")
            return False

    def get_accounts(self, item_id: str) -> List[Dict]:
        """
        Get all accounts for an item.
        Ref: https://docs.pluggy.ai/reference/accounts-list
        """
        url = f"{self.base_url}/accounts"
        params = {'itemId': item_id}

        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            return response.json()['results']
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get accounts for item {item_id}: {e}")
            raise

    def get_transactions(self, account_id: str,
                        date_from: Optional[datetime] = None,
                        date_to: Optional[datetime] = None,
                        page_size: int = 500) -> List[Dict]:
        """
        Get transactions for an account.
        Ref: https://docs.pluggy.ai/reference/transactions-list-1
        """
        url = f"{self.base_url}/transactions"
        params = {
            'accountId': account_id,
            'pageSize': page_size
        }

        if date_from:
            params['from'] = date_from.isoformat()
        if date_to:
            params['to'] = date_to.isoformat()

        from core.security_utils import sanitize_for_logging

        logger.info(f"Fetching transactions for account {account_id}")
        logger.info(f"Date range: {date_from} to {date_to}")
        logger.info(f"Request params: {sanitize_for_logging(params)}")

        all_transactions = []
        page = 1

        try:
            while True:
                params['page'] = page
                logger.debug(f"Fetching page {page}")
                response = requests.get(url, headers=self._get_headers(), params=params)
                response.raise_for_status()
                data = response.json()

                logger.info(f"Page {page}: found {len(data.get('results', []))} transactions")
                logger.debug(f"Response data keys: {data.keys()}")
                logger.debug(f"Total pages: {data.get('totalPages', 'N/A')}")

                all_transactions.extend(data.get('results', []))

                # Check if there are more pages
                if page >= data.get('totalPages', 1):
                    break
                page += 1

            logger.info(f"Total transactions fetched: {len(all_transactions)}")
            return all_transactions

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get transactions for account {account_id}: {e}")
            logger.error(f"Response status: {e.response.status_code if hasattr(e, 'response') else 'N/A'}")
            logger.error(f"Response body: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            raise

    def create_webhook(self, url: str, event: str = 'item/updated') -> Dict:
        """
        Create webhook for item updates.
        Ref: https://docs.pluggy.ai/reference/webhooks-create
        """
        endpoint = f"{self.base_url}/webhooks"
        payload = {
            'event': event,
            'url': url,
            'headers': {
                'X-Webhook-Secret': getattr(settings, 'PLUGGY_WEBHOOK_SECRET', '')
            }
        }

        try:
            response = requests.post(endpoint, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create webhook: {e}")
            raise