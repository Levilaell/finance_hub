"""
Sandbox Views - Simulate realistic Open Banking endpoints
"""
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import json
import logging
from urllib.parse import parse_qs, urlparse
from .sandbox import sandbox

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def sandbox_authorization_endpoint(request, bank_code):
    """
    Simulate bank authorization endpoint
    This would normally redirect to the bank's login page
    """
    logger.info(f"Sandbox authorization request for bank {bank_code}")
    
    # Extract parameters
    response_type = request.GET.get('response_type')
    client_id = request.GET.get('client_id')
    scope = request.GET.get('scope')
    redirect_uri = request.GET.get('redirect_uri')
    consent_id = request.GET.get('consent_id')
    state = request.GET.get('state')
    nonce = request.GET.get('nonce')
    
    # Validate required parameters
    if not all([response_type, client_id, redirect_uri, state]):
        return JsonResponse({
            'error': 'invalid_request',
            'error_description': 'Missing required parameters'
        }, status=400)
    
    # Simulate realistic bank authorization page
    # In reality, this would show the bank's login page
    # For sandbox, we'll show a simulation page
    
    auth_page_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sandbox Bank Authorization - {bank_code}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 50px; background: #f5f5f5; }}
            .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .bank-header {{ text-align: center; margin-bottom: 30px; }}
            .bank-logo {{ font-size: 24px; font-weight: bold; color: #333; }}
            .form-group {{ margin-bottom: 20px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
            .btn {{ background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-size: 16px; }}
            .btn:hover {{ background: #0056b3; }}
            .sandbox-notice {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin-bottom: 20px; color: #856404; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="bank-header">
                <div class="bank-logo">🏦 Banco Sandbox ({bank_code})</div>
                <p>Autorização de Acesso - Ambiente de Desenvolvimento</p>
            </div>
            
            <div class="sandbox-notice">
                <strong>⚠️ Ambiente Sandbox:</strong> Esta é uma simulação realista do fluxo de autorização bancária para fins de desenvolvimento e teste.
            </div>
            
            <form onsubmit="authorize(event)">
                <div class="form-group">
                    <label>CPF/CNPJ:</label>
                    <input type="text" id="document" placeholder="000.000.000-00" required>
                </div>
                
                <div class="form-group">
                    <label>Senha do Internet Banking:</label>
                    <input type="password" id="password" placeholder="Digite sua senha" required>
                </div>
                
                <div class="form-group">
                    <label>Código de Autorização (2FA):</label>
                    <input type="text" id="auth_code" placeholder="Código enviado por SMS" required>
                </div>
                
                <button type="submit" class="btn">Autorizar Acesso</button>
            </form>
            
            <p style="text-align: center; margin-top: 20px; font-size: 12px; color: #666;">
                O aplicativo FinanceHub está solicitando acesso às suas informações bancárias.
                <br>Dados serão acessados de forma segura e criptografada.
            </p>
        </div>
        
        <script>
            function authorize(event) {{
                event.preventDefault();
                
                // Simulate authorization processing
                const btn = event.target.querySelector('.btn');
                btn.textContent = 'Processando...';
                btn.disabled = true;
                
                // Simulate realistic processing time
                setTimeout(() => {{
                    // Generate authorization code
                    const authCode = 'sandbox-auth-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
                    
                    // Redirect back to callback
                    const redirectUrl = '{redirect_uri}' + 
                                      '?code=' + encodeURIComponent(authCode) + 
                                      '&state=' + encodeURIComponent('{state}');
                    
                    window.location.href = redirectUrl;
                }}, 2000); // 2 second delay to simulate processing
            }}
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(auth_page_html, content_type='text/html')


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def sandbox_token_endpoint(request, bank_code):
    """
    Simulate bank token endpoint
    Exchange authorization code for access tokens
    """
    logger.info(f"Sandbox token request for bank {bank_code}")
    
    try:
        # Parse request data
        if request.content_type == 'application/x-www-form-urlencoded':
            data = dict(request.POST)
        else:
            data = json.loads(request.body) if request.body else {}
        
        grant_type = data.get('grant_type')
        auth_code = data.get('code')
        client_id = data.get('client_id')
        redirect_uri = data.get('redirect_uri')
        
        # Validate parameters
        if grant_type != 'authorization_code':
            return JsonResponse({
                'error': 'unsupported_grant_type',
                'error_description': 'Only authorization_code grant type is supported'
            }, status=400)
        
        if not auth_code or not auth_code.startswith('sandbox-auth-'):
            return JsonResponse({
                'error': 'invalid_grant',
                'error_description': 'Invalid authorization code'
            }, status=400)
        
        # Use sandbox to generate tokens
        tokens = sandbox.exchange_code_for_tokens(auth_code, bank_code)
        
        return JsonResponse(tokens)
        
    except Exception as e:
        logger.error(f"Sandbox token error: {e}")
        return JsonResponse({
            'error': 'server_error',
            'error_description': str(e)
        }, status=500)


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def sandbox_accounts_endpoint(request, bank_code):
    """
    Simulate bank accounts endpoint
    """
    logger.info(f"Sandbox accounts request for bank {bank_code}")
    
    try:
        # Validate authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer sandbox-'):
            return JsonResponse({
                'error': 'invalid_token',
                'error_description': 'Invalid or missing access token'
            }, status=401)
        
        access_token = auth_header.replace('Bearer ', '')
        
        # Get account info from sandbox
        account_info = sandbox.get_account_info(access_token, bank_code)
        
        # Format response according to Open Banking standards
        response_data = {
            'data': {
                'accounts': [account_info]
            },
            'links': {
                'self': f'https://api.sandbox.bank{bank_code}.com.br/open-banking/accounts/v1/accounts'
            },
            'meta': {
                'totalRecords': 1,
                'totalPages': 1,
                'requestDateTime': '2025-06-02T13:30:00Z'
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Sandbox accounts error: {e}")
        return JsonResponse({
            'error': 'server_error',
            'error_description': str(e)
        }, status=500)


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def sandbox_transactions_endpoint(request, bank_code, account_id):
    """
    Simulate bank transactions endpoint
    """
    logger.info(f"Sandbox transactions request for bank {bank_code}, account {account_id}")
    
    try:
        # Validate authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer sandbox-'):
            return JsonResponse({
                'error': 'invalid_token',
                'error_description': 'Invalid or missing access token'
            }, status=401)
        
        access_token = auth_header.replace('Bearer ', '')
        
        # Extract query parameters
        from_date = request.GET.get('fromBookingDate')
        to_date = request.GET.get('toBookingDate')
        
        # Get transactions from sandbox
        transactions = sandbox.get_transactions(access_token, bank_code, account_id, from_date, to_date)
        
        # Format response according to Open Banking standards
        response_data = {
            'data': {
                'transactions': transactions
            },
            'links': {
                'self': f'https://api.sandbox.bank{bank_code}.com.br/open-banking/accounts/v1/accounts/{account_id}/transactions'
            },
            'meta': {
                'totalRecords': len(transactions),
                'totalPages': 1,
                'requestDateTime': '2025-06-02T13:30:00Z'
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Sandbox transactions error: {e}")
        return JsonResponse({
            'error': 'server_error',
            'error_description': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def sandbox_status(request):
    """
    Sandbox status and information endpoint
    """
    return JsonResponse({
        'status': 'active',
        'mode': 'sandbox',
        'supported_banks': list(sandbox.bank_configs.keys()),
        'message': 'Open Banking Sandbox - Realistic simulation for development',
        'features': [
            'OAuth2 authorization flow',
            'Token management',
            'Account information',
            'Transaction history',
            'Error simulation',
            'Rate limiting simulation',
            'Realistic response times'
        ]
    })