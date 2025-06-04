"""
Configurações para Open Banking Brasil - Produção
Este arquivo contém as configurações necessárias para integração real com bancos brasileiros
"""

# Open Banking Brasil - Configurações de Produção
OPEN_BANKING_CONFIG = {
    # Diretório oficial do Open Banking Brasil
    'DIRECTORY_URL': 'https://data.directory.openbankingbrasil.org.br',
    'SANDBOX_DIRECTORY_URL': 'https://data.sandbox.directory.openbankingbrasil.org.br',
    
    # Certificados necessários (devem ser obtidos do BACEN)
    'CLIENT_CERT_PATH': '/app/certificates/client_cert.pem',
    'CLIENT_KEY_PATH': '/app/certificates/client_key.pem',
    'CA_CERT_PATH': '/app/certificates/ca_cert.pem',
    'SIGNING_KEY_PATH': '/app/certificates/signing_key.pem',
    
    # URLs de callback para produção
    'REDIRECT_URI': 'https://api.financehub.com.br/banking/callback',
    'NOTIFICATION_URI': 'https://api.financehub.com.br/banking/notifications',
    
    # Configurações de segurança
    'JWT_ALGORITHM': 'PS256',
    'TOKEN_LIFETIME': 3600,  # 1 hora
    'REFRESH_TOKEN_LIFETIME': 2592000,  # 30 dias
    
    # Escopos padrão para contas e transações
    'DEFAULT_SCOPES': [
        'openid',
        'accounts',
        'resources'
    ],
    
    # Permissões específicas do Open Banking Brasil
    'ACCOUNT_PERMISSIONS': [
        'ACCOUNTS_READ',
        'ACCOUNTS_BALANCES_READ',
        'ACCOUNTS_TRANSACTIONS_READ',
        'ACCOUNTS_OVERDRAFT_LIMITS_READ'
    ],
    
    # Headers obrigatórios
    'REQUIRED_HEADERS': {
        'x-fapi-auth-date': True,
        'x-fapi-customer-ip-address': True,
        'x-fapi-interaction-id': True,
        'x-customer-user-agent': True
    }
}

# Endpoints dos principais bancos brasileiros
BRAZILIAN_BANKS_CONFIG = {
    'bradesco': {
        'name': 'Bradesco',
        'organization_id': '237',
        'base_url': 'https://openbanking.bradesco.com.br',
        'authorization_endpoint': 'https://proxy.api.prebanco.com.br/auth/oauth/v2/authorize',
        'token_endpoint': 'https://proxy.api.prebanco.com.br/auth/oauth/v2/token',
        'accounts_endpoint': 'https://proxy.api.prebanco.com.br/open-banking/accounts/v1',
        'logo': 'https://cdn.financehub.com.br/banks/bradesco.png'
    },
    'itau': {
        'name': 'Itaú Unibanco',
        'organization_id': '341',
        'base_url': 'https://openbanking.itau.com.br',
        'authorization_endpoint': 'https://sts.itau.com.br/api/oauth/oauth20/authorize',
        'token_endpoint': 'https://sts.itau.com.br/api/oauth/oauth20/token',
        'accounts_endpoint': 'https://secure.api.itau/open-banking/accounts/v1',
        'logo': 'https://cdn.financehub.com.br/banks/itau.png'
    },
    'santander': {
        'name': 'Santander Brasil',
        'organization_id': '033',
        'base_url': 'https://openbanking.santander.com.br',
        'authorization_endpoint': 'https://obauth.santander.com.br/oauth2/authorize',
        'token_endpoint': 'https://obauth.santander.com.br/oauth2/token',
        'accounts_endpoint': 'https://trust-open.api.santander.com.br/bank/sb/gw/open-banking/v1/accounts',
        'logo': 'https://cdn.financehub.com.br/banks/santander.png'
    },
    'bb': {
        'name': 'Banco do Brasil',
        'organization_id': '001',
        'base_url': 'https://openbanking.bb.com.br',
        'authorization_endpoint': 'https://oauth.bb.com.br/oauth/authorize',
        'token_endpoint': 'https://oauth.bb.com.br/oauth/token',
        'accounts_endpoint': 'https://api.bb.com.br/open-banking/accounts/v1',
        'logo': 'https://cdn.financehub.com.br/banks/bb.png'
    },
    'caixa': {
        'name': 'Caixa Econômica Federal',
        'organization_id': '104',
        'base_url': 'https://openbanking.caixa.gov.br',
        'authorization_endpoint': 'https://apisec.caixa.gov.br/oauth2/authorize',
        'token_endpoint': 'https://apisec.caixa.gov.br/oauth2/token',
        'accounts_endpoint': 'https://api.caixa.gov.br/open-banking/accounts/v1',
        'logo': 'https://cdn.financehub.com.br/banks/caixa.png'
    },
    'nubank': {
        'name': 'Nu Pagamentos S.A.',
        'organization_id': '260',
        'base_url': 'https://openbanking.nubank.com.br',
        'authorization_endpoint': 'https://prod-s0-webapp-proxy.nubank.com.br/api/oauth/authorize',
        'token_endpoint': 'https://prod-s0-webapp-proxy.nubank.com.br/api/oauth/token',
        'accounts_endpoint': 'https://prod-s0-webapp-proxy.nubank.com.br/api/open-banking/accounts/v1',
        'logo': 'https://cdn.financehub.com.br/banks/nubank.png'
    },
    'inter': {
        'name': 'Banco Inter',
        'organization_id': '077',
        'base_url': 'https://openbanking.bancointer.com.br',
        'authorization_endpoint': 'https://cdpj.partners.bancointer.com.br/oauth/v2/authorize',
        'token_endpoint': 'https://cdpj.partners.bancointer.com.br/oauth/v2/token',
        'accounts_endpoint': 'https://cdpj.partners.bancointer.com.br/open-banking/accounts/v1',
        'logo': 'https://cdn.financehub.com.br/banks/inter.png'
    },
    'c6bank': {
        'name': 'C6 Bank',
        'organization_id': '336',
        'base_url': 'https://openbanking.c6bank.com.br',
        'authorization_endpoint': 'https://auth.c6bank.com.br/auth/realms/ob/protocol/openid-connect/auth',
        'token_endpoint': 'https://auth.c6bank.com.br/auth/realms/ob/protocol/openid-connect/token',
        'accounts_endpoint': 'https://ob.c6bank.com.br/open-banking/accounts/v1',
        'logo': 'https://cdn.financehub.com.br/banks/c6bank.png'
    },
    'original': {
        'name': 'Banco Original',
        'organization_id': '212',
        'base_url': 'https://openbanking.original.com.br',
        'authorization_endpoint': 'https://ob.original.com.br/auth/oauth2/authorize',
        'token_endpoint': 'https://ob.original.com.br/auth/oauth2/token',
        'accounts_endpoint': 'https://ob.original.com.br/open-banking/accounts/v1',
        'logo': 'https://cdn.financehub.com.br/banks/original.png'
    },
    'btg': {
        'name': 'BTG Pactual',
        'organization_id': '208',
        'base_url': 'https://openbanking.btgpactual.com',
        'authorization_endpoint': 'https://auth.btgpactual.com/auth/realms/openbanking/protocol/openid-connect/auth',
        'token_endpoint': 'https://auth.btgpactual.com/auth/realms/openbanking/protocol/openid-connect/token',
        'accounts_endpoint': 'https://api.btgpactual.com/open-banking/accounts/v1',
        'logo': 'https://cdn.financehub.com.br/banks/btg.png'
    }
}

# Configurações de compliance com BACEN
COMPLIANCE_CONFIG = {
    'MAX_TRANSACTION_HISTORY_DAYS': 2555,  # ~7 anos conforme regulamentação
    'CONSENT_EXPIRATION_DAYS': 366,  # Máximo 366 dias
    'RATE_LIMITING': {
        'ACCOUNTS': {'calls_per_minute': 300, 'calls_per_hour': 3000},
        'TRANSACTIONS': {'calls_per_minute': 100, 'calls_per_hour': 1000},
        'BALANCES': {'calls_per_minute': 300, 'calls_per_hour': 3000}
    },
    'REQUIRED_TLS_VERSION': '1.2',
    'ALLOWED_CIPHER_SUITES': [
        'ECDHE-RSA-AES256-GCM-SHA384',
        'ECDHE-RSA-AES128-GCM-SHA256',
        'ECDHE-RSA-AES256-SHA384',
        'ECDHE-RSA-AES128-SHA256'
    ]
}