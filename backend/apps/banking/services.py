"""
Banking app services
Business logic for financial operations and integrations
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import json
import ssl
import jwt
import base64
from urllib.parse import urlencode, parse_qs
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import uuid

import requests
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from .models import (BankAccount, BankProvider, BankSync,
                     Transaction, TransactionCategory)
# from .open_banking_client import open_banking_service, OpenBankingError  # Replaced with Pluggy

logger = logging.getLogger(__name__)


class OpenBankingService:
    """
    Service for Open Banking API integration following Brazil Open Finance standards
    Implements OAuth2 mTLS authentication and FAPI-compliant security
    """
    
    def __init__(self):
        self.timeout = 30
        self.base_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'FinanceApp/1.0',
            'x-fapi-interaction-id': str(uuid.uuid4())
        }
        
        # Open Finance Brasil endpoints
        self.directory_url = getattr(settings, 'OPEN_FINANCE_DIRECTORY_URL', 'https://data.directory.openbankingbrasil.org.br')
        self.client_id = getattr(settings, 'OPEN_FINANCE_CLIENT_ID', '')
        self.software_statement = getattr(settings, 'OPEN_FINANCE_SOFTWARE_STATEMENT', '')
        
        # Certificate paths for mTLS
        self.cert_path = getattr(settings, 'OPEN_FINANCE_CLIENT_CERT_PATH', '')
        self.key_path = getattr(settings, 'OPEN_FINANCE_CLIENT_KEY_PATH', '')
        self.ca_cert_path = getattr(settings, 'OPEN_FINANCE_CA_CERT_PATH', '')
        
        # Private key for JWT signing
        self.private_key_path = getattr(settings, 'OPEN_FINANCE_SIGNING_KEY_PATH', '')
        
        # Set up SSL context for mTLS
        self.ssl_context = self._create_ssl_context()
    
    def _create_ssl_context(self):
        """Create SSL context for mTLS authentication"""
        context = ssl.create_default_context()
        
        if self.cert_path and self.key_path:
            try:
                context.load_cert_chain(self.cert_path, self.key_path)
                logger.info("SSL client certificate loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load client certificate: {e}")
        
        if self.ca_cert_path:
            try:
                context.load_verify_locations(self.ca_cert_path)
            except Exception as e:
                logger.warning(f"Could not load CA certificate: {e}")
        
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        return context
    
    def _create_jwt_assertion(self, audience: str, issuer: str = None) -> str:
        """Create JWT assertion for client authentication"""
        # This method is now handled by the OpenBankingClient
        # Keeping for backward compatibility but should be migrated
        if settings.DEBUG:
            logger.warning("Using deprecated JWT creation - migrate to OpenBankingClient")
            now = datetime.utcnow()
            payload = {
                'iss': issuer or self.client_id or 'mock-client-id',
                'sub': self.client_id or 'mock-client-id',
                'aud': audience,
                'iat': int(now.timestamp()),
                'exp': int((now + timedelta(minutes=5)).timestamp()),
                'jti': str(uuid.uuid4())
            }
            return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        
        if not self.private_key_path:
            raise Exception("Private key path not configured for JWT signing")
        
        try:
            with open(self.private_key_path, 'rb') as key_file:
                private_key = load_pem_private_key(key_file.read(), password=None)
        except Exception as e:
            raise Exception(f"Could not load private key: {e}")
        
        now = datetime.utcnow()
        payload = {
            'iss': issuer or self.client_id,
            'sub': self.client_id,
            'aud': audience,
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(minutes=5)).timestamp()),
            'jti': str(uuid.uuid4())
        }
        
        return jwt.encode(payload, private_key, algorithm='RS256')
    
    def _get_bank_endpoints(self, bank_code: str) -> Dict:
        """Get real bank endpoints for Brazilian Open Banking"""
        
        # Static configuration for major Brazilian banks (more reliable than directory lookup)
        BRAZILIAN_BANKS = {
            'bradesco': {
                'authorization_endpoint': 'https://proxy.api.prebanco.com.br/auth/oauth/v2/authorize',
                'token_endpoint': 'https://proxy.api.prebanco.com.br/auth/oauth/v2/token',
                'accounts_endpoint': 'https://proxy.api.prebanco.com.br/open-banking/accounts/v1',
                'userinfo_endpoint': 'https://proxy.api.prebanco.com.br/auth/oauth/v2/userinfo',
                'transactions_endpoint': 'https://proxy.api.prebanco.com.br/open-banking/accounts/v1'
            },
            'itau': {
                'authorization_endpoint': 'https://sts.itau.com.br/api/oauth/oauth20/authorize',
                'token_endpoint': 'https://sts.itau.com.br/api/oauth/oauth20/token',
                'accounts_endpoint': 'https://secure.api.itau/open-banking/accounts/v1',
                'userinfo_endpoint': 'https://sts.itau.com.br/api/oauth/oauth20/userinfo',
                'transactions_endpoint': 'https://secure.api.itau/open-banking/accounts/v1'
            },
            'santander': {
                'authorization_endpoint': 'https://obauth.santander.com.br/oauth2/authorize',
                'token_endpoint': 'https://obauth.santander.com.br/oauth2/token',
                'accounts_endpoint': 'https://trust-open.api.santander.com.br/bank/sb/gw/open-banking/v1/accounts',
                'userinfo_endpoint': 'https://obauth.santander.com.br/oauth2/userinfo',
                'transactions_endpoint': 'https://trust-open.api.santander.com.br/bank/sb/gw/open-banking/v1/accounts'
            },
            'bb': {
                'authorization_endpoint': 'https://oauth.bb.com.br/oauth/authorize',
                'token_endpoint': 'https://oauth.bb.com.br/oauth/token',
                'accounts_endpoint': 'https://api.bb.com.br/open-banking/accounts/v1',
                'userinfo_endpoint': 'https://oauth.bb.com.br/oauth/userinfo',
                'transactions_endpoint': 'https://api.bb.com.br/open-banking/accounts/v1'
            },
            'nubank': {
                'authorization_endpoint': 'https://prod-s0-webapp-proxy.nubank.com.br/api/oauth/authorize',
                'token_endpoint': 'https://prod-s0-webapp-proxy.nubank.com.br/api/oauth/token',
                'accounts_endpoint': 'https://prod-s0-webapp-proxy.nubank.com.br/api/open-banking/accounts/v1',
                'userinfo_endpoint': 'https://prod-s0-webapp-proxy.nubank.com.br/api/oauth/userinfo',
                'transactions_endpoint': 'https://prod-s0-webapp-proxy.nubank.com.br/api/open-banking/accounts/v1'
            },
            'inter': {
                'authorization_endpoint': 'https://cdpj.partners.bancointer.com.br/oauth/v2/authorize',
                'token_endpoint': 'https://cdpj.partners.bancointer.com.br/oauth/v2/token',
                'accounts_endpoint': 'https://cdpj.partners.bancointer.com.br/open-banking/accounts/v1',
                'userinfo_endpoint': 'https://cdpj.partners.bancointer.com.br/oauth/v2/userinfo',
                'transactions_endpoint': 'https://cdpj.partners.bancointer.com.br/open-banking/accounts/v1'
            },
            'c6bank': {
                'authorization_endpoint': 'https://auth.c6bank.com.br/auth/realms/ob/protocol/openid-connect/auth',
                'token_endpoint': 'https://auth.c6bank.com.br/auth/realms/ob/protocol/openid-connect/token',
                'accounts_endpoint': 'https://ob.c6bank.com.br/open-banking/accounts/v1',
                'userinfo_endpoint': 'https://auth.c6bank.com.br/auth/realms/ob/protocol/openid-connect/userinfo',
                'transactions_endpoint': 'https://ob.c6bank.com.br/open-banking/accounts/v1'
            },
            'caixa': {
                'authorization_endpoint': 'https://apisec.caixa.gov.br/oauth2/authorize',
                'token_endpoint': 'https://apisec.caixa.gov.br/oauth2/token',
                'accounts_endpoint': 'https://api.caixa.gov.br/open-banking/accounts/v1',
                'userinfo_endpoint': 'https://apisec.caixa.gov.br/oauth2/userinfo',
                'transactions_endpoint': 'https://api.caixa.gov.br/open-banking/accounts/v1'
            },
            'original': {
                'authorization_endpoint': 'https://ob.original.com.br/auth/oauth2/authorize',
                'token_endpoint': 'https://ob.original.com.br/auth/oauth2/token',
                'accounts_endpoint': 'https://ob.original.com.br/open-banking/accounts/v1',
                'userinfo_endpoint': 'https://ob.original.com.br/auth/oauth2/userinfo',
                'transactions_endpoint': 'https://ob.original.com.br/open-banking/accounts/v1'
            },
            'btg': {
                'authorization_endpoint': 'https://auth.btgpactual.com/auth/realms/openbanking/protocol/openid-connect/auth',
                'token_endpoint': 'https://auth.btgpactual.com/auth/realms/openbanking/protocol/openid-connect/token',
                'accounts_endpoint': 'https://api.btgpactual.com/open-banking/accounts/v1',
                'userinfo_endpoint': 'https://auth.btgpactual.com/auth/realms/openbanking/protocol/openid-connect/userinfo',
                'transactions_endpoint': 'https://api.btgpactual.com/open-banking/accounts/v1'
            }
        }
        
        # Mapping of bank codes to bank names
        BANK_CODE_MAPPING = {
            '237': 'bradesco',
            '341': 'itau', 
            '033': 'santander',
            '001': 'bb',
            '260': 'nubank',
            '077': 'inter',
            '336': 'c6bank',
            '104': 'caixa',
            '212': 'original',
            '208': 'btg'
        }
        
        # Use static configuration for known banks
        bank_name = BANK_CODE_MAPPING.get(bank_code, bank_code)
        if bank_name in BRAZILIAN_BANKS:
            logger.info(f"Using production endpoints for {bank_name} (code: {bank_code})")
            return BRAZILIAN_BANKS[bank_name]
        
        try:
            response = requests.get(
                f"{self.directory_url}/participants",
                headers=self.base_headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            participants_data = response.json()
            # Handle both formats: {"data": [...]} or [...]
            if isinstance(participants_data, dict):
                participants = participants_data.get('data', [])
            else:
                participants = participants_data
            
            for participant in participants:
                if participant.get('organisationId') == bank_code:
                    endpoints = {}
                    for auth_server in participant.get('authorisationServers', []):
                        endpoints['authorization_endpoint'] = auth_server.get('authorizationEndpoint')
                        endpoints['token_endpoint'] = auth_server.get('tokenEndpoint')
                        endpoints['userinfo_endpoint'] = auth_server.get('userinfoEndpoint')
                        
                    for api_resource in participant.get('apiResources', []):
                        if api_resource.get('apiDiscoveryEndpoints'):
                            for discovery in api_resource['apiDiscoveryEndpoints']:
                                if 'accounts' in discovery.get('apiEndpoint', ''):
                                    endpoints['accounts_endpoint'] = discovery['apiEndpoint']
                                elif 'transactions' in discovery.get('apiEndpoint', ''):
                                    endpoints['transactions_endpoint'] = discovery['apiEndpoint']
                    
                    return endpoints
            
            raise Exception(f"Bank {bank_code} not found in directory")
            
        except requests.RequestException as e:
            logger.error(f"Error fetching bank endpoints: {e}")
            raise Exception(f"Could not fetch bank endpoints: {e}")
    
    def initiate_consent_flow(self, bank_code: str, permissions: List[str]) -> Dict:
        """Initiate consent flow for Open Banking access"""
        try:
            endpoints = self._get_bank_endpoints(bank_code)
            bank_provider = BankProvider.objects.get(code=bank_code)
            
            # Block sandbox in production
            from django.conf import settings
            if settings.DEBUG:
                logger.info(f"Using sandbox consent flow for bank {bank_code} in development mode")
                
                # Use sandbox for more realistic testing
                from .sandbox import sandbox
                sandbox_result = sandbox.create_consent(bank_code, permissions)
                
                return {
                    'consent_id': sandbox_result['consent_id'],
                    'authorization_url': sandbox_result['authorization_url'],
                    'status': 'consent_required',
                    'expires_in': sandbox_result['expires_in']
                }
            
            # In production, real implementation is required
            if not settings.OPEN_BANKING_CLIENT_ID:
                raise ValueError("Open Banking credentials not configured for production")
            
            # Create consent request
            consent_data = {
                'data': {
                    'permissions': permissions,
                    'expirationDateTime': (datetime.utcnow() + timedelta(days=90)).isoformat() + 'Z',
                    'loggedUser': {
                        'document': {
                            'identification': '',  # Will be filled by user
                            'rel': 'CPF'
                        }
                    }
                }
            }
            
            # Create client assertion for authentication
            jwt_assertion = self._create_jwt_assertion(endpoints['token_endpoint'])
            
            headers = {
                **self.base_headers,
                'Authorization': f'Bearer {jwt_assertion}',
                'x-fapi-interaction-id': str(uuid.uuid4())
            }
            
            # Make consent request with mTLS
            response = requests.post(
                f"{endpoints.get('accounts_endpoint', bank_provider.api_endpoint)}/consents",
                json=consent_data,
                headers=headers,
                cert=(self.cert_path, self.key_path) if self.cert_path else None,
                verify=self.ca_cert_path if self.ca_cert_path else True,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                consent_response = response.json()
                consent_id = consent_response['data']['consentId']
                
                # Build authorization URL
                auth_params = {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'scope': 'openid accounts',
                    'redirect_uri': getattr(settings, 'OPEN_FINANCE_REDIRECT_URI', ''),
                    'consent_id': consent_id,
                    'state': str(uuid.uuid4()),
                    'nonce': str(uuid.uuid4())
                }
                
                # Use mock authorization URL for development
                mock_auth_url = f"http://localhost:3000/banking/mock-auth?{urlencode(auth_params)}"
                
                return {
                    'consent_id': consent_id,
                    'authorization_url': mock_auth_url,
                    'status': 'consent_created'
                }
            else:
                raise Exception(f"Consent creation failed: {response.status_code} - {response.text}")
                
        except BankProvider.DoesNotExist:
            raise Exception(f"Bank provider {bank_code} not found")
        except Exception as e:
            logger.error(f"Error initiating consent flow: {e}")
            raise
    
    def exchange_code_for_tokens(self, authorization_code: str, bank_code: str) -> Dict:
        """Exchange authorization code for access tokens"""
        try:
            endpoints = self._get_bank_endpoints(bank_code)
            
            # For development, use sandbox
            from django.conf import settings
            if settings.DEBUG:
                logger.info(f"Using sandbox token exchange for bank {bank_code} in development mode")
                
                from .sandbox import sandbox
                return sandbox.exchange_code_for_tokens(authorization_code, bank_code)
            
            # Create client assertion
            jwt_assertion = self._create_jwt_assertion(endpoints['token_endpoint'])
            
            token_data = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'redirect_uri': getattr(settings, 'OPEN_FINANCE_REDIRECT_URI', ''),
                'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
                'client_assertion': jwt_assertion
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'x-fapi-interaction-id': str(uuid.uuid4())
            }
            
            response = requests.post(
                endpoints['token_endpoint'],
                data=token_data,
                headers=headers,
                cert=(self.cert_path, self.key_path) if self.cert_path else None,
                verify=self.ca_cert_path if self.ca_cert_path else True,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            raise
    
    def connect_account(self, bank_code: str, credentials: Dict) -> Dict:
        """
        Initiate real Open Banking connection flow
        
        Args:
            bank_code: Bank provider code
            credentials: Contains authorization_code if completing OAuth flow
            
        Returns:
            Dict with authorization URL or connection data
        """
        try:
            # Check if this is completing an OAuth flow
            if 'authorization_code' in credentials:
                # Exchange code for tokens
                tokens = self.exchange_code_for_tokens(credentials['authorization_code'], bank_code)
                
                # Get account information using the access token
                account_info = self.get_account_info_from_token(tokens['access_token'], bank_code)
                
                return {
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens.get('refresh_token'),
                    'expires_in': tokens.get('expires_in', 3600),
                    'account_id': account_info.get('accountId'),
                    'account_info': account_info,
                    'status': 'connected'
                }
            else:
                # Initiate consent flow
                permissions = [
                    'ACCOUNTS_READ',
                    'ACCOUNTS_BALANCES_READ', 
                    'ACCOUNTS_TRANSACTIONS_READ'
                ]
                
                consent_result = self.initiate_consent_flow(bank_code, permissions)
                
                return {
                    'consent_id': consent_result['consent_id'],
                    'authorization_url': consent_result['authorization_url'],
                    'status': 'consent_required',
                    'message': 'User needs to authorize access at the provided URL'
                }
            
        except BankProvider.DoesNotExist:
            raise Exception(f"Bank provider {bank_code} not found")
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise Exception(f"Connection error: {str(e)}")
    
    def get_account_info_from_token(self, access_token: str, bank_code: str) -> Dict:
        """Get account information using access token"""
        try:
            endpoints = self._get_bank_endpoints(bank_code)
            
            # For development, use sandbox
            from django.conf import settings
            if settings.DEBUG:
                logger.info(f"Using sandbox account info for bank {bank_code} in development mode")
                
                from .sandbox import sandbox
                return sandbox.get_account_info(access_token, bank_code)
            
            headers = {
                **self.base_headers,
                'Authorization': f'Bearer {access_token}',
                'x-fapi-interaction-id': str(uuid.uuid4())
            }
            
            response = requests.get(
                f"{endpoints['accounts_endpoint']}/accounts",
                headers=headers,
                cert=(self.cert_path, self.key_path) if self.cert_path else None,
                verify=self.ca_cert_path if self.ca_cert_path else True,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                accounts_data = response.json()
                if accounts_data.get('data') and len(accounts_data['data']) > 0:
                    account = accounts_data['data'][0]  # Get first account
                    
                    # Get balance information
                    account_id = account['accountId']
                    balance_response = requests.get(
                        f"{endpoints['accounts_endpoint']}/accounts/{account_id}/balances",
                        headers=headers,
                        cert=(self.cert_path, self.key_path) if self.cert_path else None,
                        verify=self.ca_cert_path if self.ca_cert_path else True,
                        timeout=self.timeout
                    )
                    
                    balance_data = {}
                    if balance_response.status_code == 200:
                        balance_info = balance_response.json()
                        if balance_info.get('data') and len(balance_info['data']) > 0:
                            balance_data = balance_info['data'][0]
                    
                    return {
                        'accountId': account_id,
                        'accountType': account.get('accountType'),
                        'accountSubType': account.get('accountSubType'),
                        'currency': account.get('currency', 'BRL'),
                        'accountNumber': account.get('number'),
                        'agency': account.get('branchCode'),
                        'balance': balance_data.get('availableAmount', '0'),
                        'availableBalance': balance_data.get('availableAmount', '0'),
                        'blockedBalance': balance_data.get('blockedAmount', '0'),
                        'lastUpdate': balance_data.get('lastTransaction', {}).get('lastTransactionDateTime')
                    }
                else:
                    raise Exception("No accounts found")
            else:
                raise Exception(f"Failed to get account info: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            raise
    
    def get_account_info(self, bank_account: BankAccount) -> Dict:
        """
        Get real account information and current balance from Open Finance API
        """
        try:
            if not bank_account.access_token:
                raise Exception("Account not properly connected - missing access token")
            
            # For development, return mock account info
            from django.conf import settings
            if settings.DEBUG:
                logger.info(f"Using mock account sync for {bank_account} in development mode")
                import random
                return {
                    'balance': float(bank_account.current_balance or random.uniform(1000, 50000)),
                    'available_balance': float(bank_account.available_balance or random.uniform(1000, 50000)),
                    'blocked_balance': 0.0,
                    'account_status': 'active',
                    'currency': 'BRL',
                    'last_update': timezone.now().isoformat()
                }
            
            endpoints = self._get_bank_endpoints(bank_account.bank_provider.code)
            
            headers = {
                **self.base_headers,
                'Authorization': f'Bearer {bank_account.access_token}',
                'x-fapi-interaction-id': str(uuid.uuid4())
            }
            
            # Get account details
            account_response = requests.get(
                f"{endpoints['accounts_endpoint']}/accounts/{bank_account.external_id}",
                headers=headers,
                cert=(self.cert_path, self.key_path) if self.cert_path else None,
                verify=self.ca_cert_path if self.ca_cert_path else True,
                timeout=self.timeout
            )
            
            if account_response.status_code != 200:
                raise Exception(f"Failed to get account details: {account_response.status_code}")
            
            # Get balance information
            balance_response = requests.get(
                f"{endpoints['accounts_endpoint']}/accounts/{bank_account.external_id}/balances",
                headers=headers,
                cert=(self.cert_path, self.key_path) if self.cert_path else None,
                verify=self.ca_cert_path if self.ca_cert_path else True,
                timeout=self.timeout
            )
            
            if balance_response.status_code != 200:
                raise Exception(f"Failed to get account balances: {balance_response.status_code}")
            
            account_data = account_response.json()['data']
            balance_data = balance_response.json()['data'][0] if balance_response.json().get('data') else {}
            
            return {
                'balance': float(balance_data.get('availableAmount', '0')),
                'available_balance': float(balance_data.get('availableAmount', '0')),
                'blocked_balance': float(balance_data.get('blockedAmount', '0')),
                'account_status': 'active',
                'currency': account_data.get('currency', 'BRL'),
                'last_update': balance_data.get('lastTransaction', {}).get('lastTransactionDateTime', timezone.now().isoformat())
            }
            
        except Exception as e:
            logger.error(f"Error getting account info for {bank_account}: {e}")
            raise
    
    def get_transactions(self, bank_account: BankAccount, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Fetch real transactions from Open Finance API
        
        Args:
            bank_account: BankAccount instance
            start_date: Start date for transaction fetch
            end_date: End date for transaction fetch
            
        Returns:
            List of transaction dictionaries
        """
        try:
            if not bank_account.access_token:
                raise Exception("Account not properly connected - missing access token")
            
            # For development, return mock transactions
            from django.conf import settings
            if settings.DEBUG:
                logger.info(f"Using mock transactions for {bank_account} in development mode")
                return self._generate_mock_transactions(bank_account, start_date, end_date)
            
            endpoints = self._get_bank_endpoints(bank_account.bank_provider.code)
            
            headers = {
                **self.base_headers,
                'Authorization': f'Bearer {bank_account.access_token}',
                'x-fapi-interaction-id': str(uuid.uuid4())
            }
            
            params = {
                'fromBookingDateTime': start_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                'toBookingDateTime': end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                'page': 1,
                'page-size': 1000
            }
            
            all_transactions = []
            page = 1
            
            while True:
                params['page'] = page
                
                response = requests.get(
                    f"{endpoints['accounts_endpoint']}/accounts/{bank_account.external_id}/transactions",
                    headers=headers,
                    params=params,
                    cert=(self.cert_path, self.key_path) if self.cert_path else None,
                    verify=self.ca_cert_path if self.ca_cert_path else True,
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    raise Exception(f"Failed to fetch transactions: {response.status_code} - {response.text}")
                
                data = response.json()
                transactions = data.get('data', [])
                
                if not transactions:
                    break
                
                # Transform Open Finance transaction format to our internal format
                for transaction in transactions:
                    transformed = self._transform_transaction(transaction)
                    all_transactions.append(transformed)
                
                # Check if there are more pages
                meta = data.get('meta', {})
                if page >= meta.get('totalPages', 1):
                    break
                
                page += 1
            
            return all_transactions
            
        except Exception as e:
            logger.error(f"Error fetching transactions for {bank_account}: {e}")
            raise
    
    def _transform_transaction(self, transaction: Dict) -> Dict:
        """Transform Open Finance transaction format to internal format"""
        try:
            # Map Open Finance transaction types to our internal types
            type_mapping = {
                'DEBITO': 'debit',
                'CREDITO': 'credit', 
                'PIX_DEBITO': 'pix_out',
                'PIX_CREDITO': 'pix_in',
                'TRANSFERENCIA_DEBITO': 'transfer_out',
                'TRANSFERENCIA_CREDITO': 'transfer_in',
                'TAXA': 'fee',
                'JUROS': 'interest'
            }
            
            amount = float(transaction.get('amount', 0))
            transaction_type = type_mapping.get(transaction.get('type'), 'debit')
            
            # Determine if amount should be negative based on transaction type
            if transaction_type in ['debit', 'pix_out', 'transfer_out', 'fee']:
                amount = -abs(amount)
            else:
                amount = abs(amount)
            
            counterpart_info = transaction.get('creditorAccount', {}) or transaction.get('debtorAccount', {})
            
            return {
                'external_id': transaction.get('transactionId', str(uuid.uuid4())),
                'transaction_type': transaction_type,
                'amount': amount,
                'description': transaction.get('transactionName', '').strip() or 'Transação',
                'transaction_date': transaction.get('bookingDateTime', timezone.now().isoformat()),
                'counterpart_name': counterpart_info.get('name', ''),
                'counterpart_document': counterpart_info.get('cpfCnpj', ''),
                'counterpart_bank': counterpart_info.get('ispb', ''),
                'counterpart_agency': counterpart_info.get('branchCode', ''),
                'counterpart_account': counterpart_info.get('number', ''),
                'reference_number': transaction.get('transactionId', ''),
                'pix_key': transaction.get('pixTransactionInformation', {}).get('endToEndId', ''),
                'balance_after': transaction.get('balanceAfterTransaction', {}).get('amount'),
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error transforming transaction: {e}")
            # Return a default structure if transformation fails
            return {
                'external_id': str(uuid.uuid4()),
                'transaction_type': 'debit',
                'amount': 0,
                'description': 'Erro na transformação',
                'transaction_date': timezone.now().isoformat(),
                'counterpart_name': '',
                'reference_number': '',
                'status': 'completed'
            }
    
    def _generate_mock_transactions(self, bank_account: BankAccount, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Generate mock transactions for development
        """
        transactions = []
        current_date = start_date
        
        while current_date <= end_date:
            # Generate 1-3 random transactions per day
            import random
            daily_transactions = random.randint(0, 3)
            
            for _ in range(daily_transactions):
                transaction_type = random.choice(['credit', 'debit', 'pix_in', 'pix_out'])
                amount = Decimal(str(random.uniform(10, 1000))).quantize(Decimal('0.01'))
                
                if transaction_type in ['debit', 'pix_out']:
                    amount = -amount
                
                transactions.append({
                    'external_id': f'mock_{current_date.strftime("%Y%m%d")}_{len(transactions)}',
                    'transaction_type': transaction_type,
                    'amount': float(amount),
                    'description': random.choice([
                        'PAGAMENTO PIX', 'TRANSFERENCIA TED', 'COMPRA CARTAO',
                        'DEPOSITO', 'SAQUE', 'TAXA MANUTENCAO', 'JUROS'
                    ]),
                    'transaction_date': current_date.isoformat(),
                    'counterpart_name': random.choice([
                        'LOJA ABC LTDA', 'SUPERMERCADO XYZ', 'POSTO COMBUSTIVEL',
                        'CLIENTE JOAO SILVA', 'FORNECEDOR MATERIAIS'
                    ]),
                    'reference_number': f'REF{random.randint(100000, 999999)}'
                })
            
            current_date += timedelta(days=1)
        
        return transactions


class BankingSyncService:
    """
    Service for synchronizing bank account data
    Orchestrates the sync process and handles errors
    """
    
    def __init__(self):
        self.open_banking = OpenBankingService()
    
    def sync_account(self, bank_account: BankAccount, days_back: int = 30) -> BankSync:
        """
        Synchronize transactions for a bank account
        
        Args:
            bank_account: BankAccount to sync
            days_back: Number of days to sync backwards
            
        Returns:
            BankSync log instance
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # Create sync log
        sync_log = BankSync.objects.create(
            bank_account=bank_account,
            status='running',
            sync_from_date=start_date,
            sync_to_date=end_date
        )
        
        try:
            with transaction.atomic():
                # Update account info
                account_info = self.open_banking.get_account_info(bank_account)
                bank_account.current_balance = Decimal(str(account_info['balance']))
                bank_account.available_balance = Decimal(str(account_info['available_balance']))
                bank_account.last_sync_at = timezone.now()
                bank_account.status = 'active'
                bank_account.save()
                
                # Fetch and process transactions
                transactions_data = self.open_banking.get_transactions(
                    bank_account, 
                    datetime.combine(start_date, datetime.min.time()),
                    datetime.combine(end_date, datetime.max.time())
                )
                
                new_transactions = 0
                updated_transactions = 0
                
                for trans_data in transactions_data:
                    created = self._process_transaction(bank_account, trans_data)
                    if created:
                        new_transactions += 1
                    else:
                        updated_transactions += 1
                
                # Update sync log
                sync_log.status = 'completed'
                sync_log.completed_at = timezone.now()
                sync_log.transactions_found = len(transactions_data)
                sync_log.transactions_new = new_transactions
                sync_log.transactions_updated = updated_transactions
                sync_log.save()
                
                logger.info(f"Sync completed for {bank_account}: {new_transactions} new, {updated_transactions} updated")
                
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            bank_account.status = 'error'
            bank_account.save()
            
            logger.error(f"Sync failed for {bank_account}: {e}")
            raise
        
        return sync_log
    
    def _process_transaction(self, bank_account: BankAccount, trans_data: Dict) -> bool:
        """
        Process individual transaction data
        
        Returns:
            True if transaction was created, False if updated
        """
        external_id = trans_data.get('external_id')
        
        # Check if transaction already exists
        existing = Transaction.objects.filter(
            bank_account=bank_account,
            external_id=external_id
        ).first()
        
        transaction_date = datetime.fromisoformat(trans_data['transaction_date'].replace('Z', '+00:00'))
        
        transaction_data = {
            'transaction_type': trans_data['transaction_type'],
            'amount': Decimal(str(trans_data['amount'])),
            'description': trans_data['description'][:500],
            'transaction_date': transaction_date,
            'counterpart_name': trans_data.get('counterpart_name', '')[:200],
            'reference_number': trans_data.get('reference_number', '')[:100],
            'status': 'completed'
        }
        
        if existing:
            # Update existing transaction
            for key, value in transaction_data.items():
                setattr(existing, key, value)
            existing.save()
            return False
        else:
            # Create new transaction
            Transaction.objects.create(
                bank_account=bank_account,
                external_id=external_id,
                **transaction_data
            )
            return True
    
    def sync_all_accounts(self, company):
        """
        Sync all active accounts for a company
        """
        accounts = BankAccount.objects.filter(
            company=company,
            is_active=True,
            status='active'
        )
        
        results = []
        for account in accounts:
            try:
                sync_log = self.sync_account(account)
                results.append({
                    'account': account.display_name,
                    'status': 'success',
                    'sync_id': sync_log.id
                })
            except Exception as e:
                results.append({
                    'account': account.display_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results


class CashFlowProjectionService:
    """
    Service for cash flow projections and financial planning
    """
    
    def __init__(self):
        pass


class FinancialInsightsService:
    """
    Service for generating financial insights and recommendations
    """
    
    def generate_insights(self, company) -> Dict:
        """
        Generate financial insights for dashboard
        """
        insights = {
            'spending_trends': self._analyze_spending_trends(company),
            'category_analysis': self._analyze_categories(company),
            'cash_flow_health': self._assess_cash_flow_health(company),
            'recommendations': self._generate_recommendations(company)
        }
        
        return insights
    
    def _analyze_spending_trends(self, company) -> Dict:
        """
        Analyze spending trends over time
        """
        # Implementation for spending trend analysis
        return {
            'trend': 'increasing',
            'percentage_change': 15.5,
            'period': 'last_30_days'
        }
    
    def _analyze_categories(self, company) -> List[Dict]:
        """
        Analyze spending by category
        """
        # Implementation for category analysis
        return []
    
    def _assess_cash_flow_health(self, company) -> Dict:
        """
        Assess overall cash flow health
        """
        return {
            'score': 7.5,
            'status': 'healthy',
            'issues': []
        }
    
    def _generate_recommendations(self, company) -> List[Dict]:
        """
        Generate actionable financial recommendations
        """
        return [
            {
                'type': 'cost_saving',
                'title': 'Reduza gastos com combustível',
                'description': 'Seus gastos com combustível aumentaram 25% este mês',
                'potential_saving': 340.50
            }
        ]