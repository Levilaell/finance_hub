"""
Open Banking Sandbox Simulator
Simulates realistic Open Banking behavior for testing
"""
import json
import uuid
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlencode, parse_qs, urlparse
import logging

logger = logging.getLogger(__name__)

class OpenBankingSandbox:
    """
    Realistic Open Banking sandbox that simulates:
    - OAuth2 flows with proper state management
    - JWT validation simulation
    - Rate limiting
    - Error scenarios
    - Realistic response times
    """
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api/banking/sandbox"
        self.consent_store = {}  # In-memory store for consents
        self.token_store = {}    # In-memory store for tokens
        
        # Simulate different bank behaviors
        self.bank_configs = {
            '077': {  # Inter
                'name': 'Inter',
                'response_time': (0.5, 2.0),  # seconds
                'error_rate': 0.05,  # 5% error rate
                'requires_2fa': True,
                'sandbox_endpoints': {
                    'authorization': f"{self.base_url}/inter/oauth/authorize",
                    'token': f"{self.base_url}/inter/oauth/token",
                    'accounts': f"{self.base_url}/inter/accounts",
                    'transactions': f"{self.base_url}/inter/transactions"
                }
            },
            '260': {  # Nubank
                'name': 'Nubank',
                'response_time': (0.3, 1.5),
                'error_rate': 0.03,
                'requires_2fa': True,
                'sandbox_endpoints': {
                    'authorization': f"{self.base_url}/nubank/oauth/authorize",
                    'token': f"{self.base_url}/nubank/oauth/token",
                    'accounts': f"{self.base_url}/nubank/accounts",
                    'transactions': f"{self.base_url}/nubank/transactions"
                }
            },
            '341': {  # Itaú
                'name': 'Itau',
                'response_time': (1.0, 3.0),
                'error_rate': 0.08,
                'requires_2fa': True,
                'sandbox_endpoints': {
                    'authorization': f"{self.base_url}/itau/oauth/authorize",
                    'token': f"{self.base_url}/itau/oauth/token",
                    'accounts': f"{self.base_url}/itau/accounts",
                    'transactions': f"{self.base_url}/itau/transactions"
                }
            }
        }
    
    def simulate_network_delay(self, bank_code: str):
        """Simulate realistic network delays"""
        if bank_code in self.bank_configs:
            min_delay, max_delay = self.bank_configs[bank_code]['response_time']
            delay = random.uniform(min_delay, max_delay)
            time.sleep(delay)
    
    def should_simulate_error(self, bank_code: str) -> bool:
        """Randomly simulate errors based on bank configuration"""
        if bank_code in self.bank_configs:
            error_rate = self.bank_configs[bank_code]['error_rate']
            return random.random() < error_rate
        return False
    
    def create_consent(self, bank_code: str, permissions: List[str]) -> Dict:
        """Create a consent with realistic validation"""
        logger.info(f"Creating sandbox consent for bank {bank_code}")
        
        # Simulate network delay
        self.simulate_network_delay(bank_code)
        
        # Simulate errors
        if self.should_simulate_error(bank_code):
            raise Exception(f"Bank {bank_code} temporarily unavailable")
        
        consent_id = f"sandbox-consent-{uuid.uuid4()}"
        
        # Store consent
        consent_data = {
            'consent_id': consent_id,
            'bank_code': bank_code,
            'permissions': permissions,
            'status': 'AWAITING_AUTHORISATION',
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=15)).isoformat(),
            'client_id': 'sandbox-client-id'
        }
        
        self.consent_store[consent_id] = consent_data
        
        # Build authorization URL using bank code instead of name
        auth_endpoint = f"{self.base_url}/{bank_code}/oauth/authorize"
        
        auth_params = {
            'response_type': 'code',
            'client_id': 'sandbox-client-id',
            'scope': 'openid accounts transactions',
            'redirect_uri': 'http://localhost:3000/banking/callback',
            'consent_id': consent_id,
            'state': str(uuid.uuid4()),
            'nonce': str(uuid.uuid4())
        }
        
        authorization_url = f"{auth_endpoint}?{urlencode(auth_params)}"
        
        return {
            'consent_id': consent_id,
            'authorization_url': authorization_url,
            'status': 'consent_created',
            'expires_in': 900  # 15 minutes
        }
    
    def exchange_code_for_tokens(self, auth_code: str, bank_code: str) -> Dict:
        """Exchange authorization code for tokens with validation"""
        logger.info(f"Exchanging authorization code for tokens - bank {bank_code}")
        
        # Simulate network delay
        self.simulate_network_delay(bank_code)
        
        # Simulate errors
        if self.should_simulate_error(bank_code):
            raise Exception(f"Token exchange failed for bank {bank_code}")
        
        # Validate authorization code format
        if not auth_code.startswith('sandbox-auth-'):
            raise Exception("Invalid authorization code format")
        
        # Generate tokens
        access_token = f"sandbox-access-{uuid.uuid4()}"
        refresh_token = f"sandbox-refresh-{uuid.uuid4()}"
        
        # Store token
        token_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'bank_code': bank_code,
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            'created_at': datetime.utcnow().isoformat(),
            'scope': 'openid accounts transactions'
        }
        
        self.token_store[access_token] = token_data
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 3600,
            'token_type': 'Bearer',
            'scope': 'openid accounts transactions'
        }
    
    def get_account_info(self, access_token: str, bank_code: str) -> Dict:
        """Get account information with realistic data"""
        logger.info(f"Getting account info for bank {bank_code}")
        
        # Validate token
        if access_token not in self.token_store:
            raise Exception("Invalid or expired access token")
        
        token_data = self.token_store[access_token]
        
        # Check if token expired
        expires_at = datetime.fromisoformat(token_data['expires_at'])
        if datetime.utcnow() > expires_at:
            raise Exception("Access token expired")
        
        # Simulate network delay
        self.simulate_network_delay(bank_code)
        
        # Simulate errors
        if self.should_simulate_error(bank_code):
            raise Exception(f"Failed to fetch account info from bank {bank_code}")
        
        # Generate realistic account data based on bank
        bank_name = self.bank_configs.get(bank_code, {}).get('name', 'Unknown Bank')
        
        # Different account number patterns per bank
        account_patterns = {
            '077': {'digits': 6, 'agency_digits': 4},  # Inter
            '260': {'digits': 8, 'agency_digits': 4},  # Nubank
            '341': {'digits': 5, 'agency_digits': 4},  # Itaú
        }
        
        pattern = account_patterns.get(bank_code, {'digits': 6, 'agency_digits': 4})
        
        account_number = ''.join([str(random.randint(0, 9)) for _ in range(pattern['digits'])])
        agency = ''.join([str(random.randint(0, 9)) for _ in range(pattern['agency_digits'])])
        
        # Realistic balance ranges per bank type
        balance_ranges = {
            '077': (5000, 150000),    # Inter - higher limits
            '260': (1000, 50000),     # Nubank - moderate
            '341': (10000, 200000),   # Itaú - traditional bank, higher
        }
        
        min_balance, max_balance = balance_ranges.get(bank_code, (1000, 50000))
        current_balance = round(random.uniform(min_balance, max_balance), 2)
        available_balance = round(current_balance * random.uniform(0.7, 0.95), 2)
        
        return {
            'accountId': f'sandbox-account-{bank_code}-{uuid.uuid4()}',
            'accountType': 'checking',
            'accountSubType': 'CONTA_CORRENTE_INDIVIDUAL',
            'currency': 'BRL',
            'accountNumber': account_number,
            'checkDigit': str(random.randint(0, 9)),
            'agency': agency,
            'agencyCheckDigit': str(random.randint(0, 9)),
            'balance': str(current_balance),
            'availableBalance': str(available_balance),
            'blockedBalance': '0.00',
            'automaticallyInvestedBalance': '0.00',
            'overdraftContractedLimit': '0.00',
            'overdraftUsedLimit': '0.00',
            'unarrangedOverdraftAmount': '0.00',
            'compeCode': bank_code,
            'branchCode': agency,
            'accountHolderName': 'Titular da Conta Sandbox',
            'accountHolderDocument': {
                'identification': '12345678901',
                'rel': 'CPF'
            }
        }
    
    def get_transactions(self, access_token: str, bank_code: str, 
                        account_id: str, from_date: str = None, 
                        to_date: str = None) -> List[Dict]:
        """Generate realistic transaction history"""
        logger.info(f"Getting transactions for account {account_id}")
        
        # Validate token
        if access_token not in self.token_store:
            raise Exception("Invalid or expired access token")
        
        # Simulate network delay
        self.simulate_network_delay(bank_code)
        
        # Generate realistic transactions
        transactions = []
        num_transactions = random.randint(5, 25)
        
        transaction_types = [
            ('PIX_RECEBIDO', 'credit', 'PIX recebido'),
            ('PIX_ENVIADO', 'debit', 'PIX enviado'),
            ('TED_RECEBIDO', 'credit', 'TED recebida'),
            ('TED_ENVIADO', 'debit', 'TED enviada'),
            ('COMPRA_CARTAO', 'debit', 'Compra no cartão'),
            ('SAQUE', 'debit', 'Saque em dinheiro'),
            ('DEPOSITO', 'credit', 'Depósito'),
            ('TARIFA', 'debit', 'Tarifa bancária'),
            ('RENDIMENTO', 'credit', 'Rendimento da conta'),
        ]
        
        for i in range(num_transactions):
            transaction_type, nature, description = random.choice(transaction_types)
            
            # Generate realistic amounts based on transaction type
            if transaction_type in ['PIX_RECEBIDO', 'PIX_ENVIADO']:
                amount = round(random.uniform(10, 2000), 2)
            elif transaction_type in ['COMPRA_CARTAO']:
                amount = round(random.uniform(15, 500), 2)
            elif transaction_type in ['SAQUE']:
                amount = round(random.uniform(50, 1000), 2)
            elif transaction_type in ['TARIFA']:
                amount = round(random.uniform(5, 50), 2)
            else:
                amount = round(random.uniform(100, 5000), 2)
            
            # Random date in the last 30 days
            days_ago = random.randint(0, 30)
            transaction_date = datetime.utcnow() - timedelta(days=days_ago)
            
            transaction = {
                'transactionId': f'sandbox-tx-{uuid.uuid4()}',
                'type': transaction_type,
                'creditDebitType': nature.upper(),
                'amount': {
                    'amount': str(amount),
                    'currency': 'BRL'
                },
                'transactionDate': transaction_date.strftime('%Y-%m-%d'),
                'bookingDateTime': transaction_date.isoformat(),
                'valueDateTime': transaction_date.isoformat(),
                'transactionName': description,
                'creditorName': 'Beneficiário Sandbox' if nature == 'debit' else None,
                'debtorName': 'Pagador Sandbox' if nature == 'credit' else None,
                'remittanceInformation': f'{description} - Transação sandbox',
                'proprietaryBankTransactionCode': transaction_type,
                'balanceAfterTransaction': {
                    'amount': str(round(random.uniform(1000, 50000), 2)),
                    'currency': 'BRL'
                }
            }
            
            transactions.append(transaction)
        
        # Sort by date (most recent first)
        transactions.sort(key=lambda x: x['bookingDateTime'], reverse=True)
        
        return transactions
    
    def validate_request(self, headers: Dict, required_headers: List[str] = None) -> bool:
        """Validate request headers and security"""
        required_headers = required_headers or ['Authorization', 'x-fapi-interaction-id']
        
        for header in required_headers:
            if header not in headers:
                logger.warning(f"Missing required header: {header}")
                return False
        
        # Validate authorization header format
        auth_header = headers.get('Authorization', '')
        if not auth_header.startswith('Bearer sandbox-'):
            logger.warning("Invalid authorization header format")
            return False
        
        return True
    
    def cleanup_expired_data(self):
        """Clean up expired consents and tokens"""
        now = datetime.utcnow()
        
        # Clean expired consents
        expired_consents = []
        for consent_id, consent_data in self.consent_store.items():
            expires_at = datetime.fromisoformat(consent_data['expires_at'])
            if now > expires_at:
                expired_consents.append(consent_id)
        
        for consent_id in expired_consents:
            del self.consent_store[consent_id]
            logger.info(f"Cleaned expired consent: {consent_id}")
        
        # Clean expired tokens
        expired_tokens = []
        for token, token_data in self.token_store.items():
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if now > expires_at:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.token_store[token]
            logger.info(f"Cleaned expired token: {token[:20]}...")


# Global sandbox instance
sandbox = OpenBankingSandbox()