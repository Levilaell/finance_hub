"""
Teste ultra simples para cookies Mobile Safari
"""
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json


@method_decorator(csrf_exempt, name='dispatch')
class SimpleCookieTestView(View):
    """
    Teste mais simples possível para cookies
    """
    
    def get(self, request):
        """Mostrar cookies recebidos"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile = 'iPhone' in user_agent and 'Safari' in user_agent and 'Chrome' not in user_agent
        
        data = {
            'mobile_safari': is_mobile,
            'user_agent': user_agent[:50],
            'total_cookies_received': len(request.COOKIES),
            'test_cookies': {
                'simple': request.COOKIES.get('simple_test'),
                'secure': request.COOKIES.get('secure_test'), 
                'lax': request.COOKIES.get('lax_test'),
                'none': request.COOKIES.get('none_test'),
            },
            'all_cookies': dict(request.COOKIES) if len(request.COOKIES) < 10 else f"{len(request.COOKIES)} cookies total"
        }
        
        return JsonResponse(data)
    
    def post(self, request):
        """Definir cookies de teste e verificar imediatamente"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile = 'iPhone' in user_agent and 'Safari' in user_agent and 'Chrome' not in user_agent
        
        response = JsonResponse({
            'message': 'Setting test cookies',
            'mobile_safari': is_mobile,
            'strategies': []
        })
        
        strategies = []
        
        # 1. Cookie mais simples possível (sem restrições)
        response.set_cookie('simple_test', 'value1', max_age=300)
        strategies.append('simple_no_restrictions')
        
        # 2. Cookie com Secure (pode ser o problema)
        response.set_cookie('secure_test', 'value2', max_age=300, secure=True)
        strategies.append('secure_only')
        
        # 3. Cookie com SameSite=Lax  
        response.set_cookie('lax_test', 'value3', max_age=300, samesite='Lax')
        strategies.append('samesite_lax')
        
        # 4. Cookie com SameSite=None + Secure (configuração original problemática)
        response.set_cookie('none_test', 'value4', max_age=300, samesite='None', secure=True)
        strategies.append('samesite_none_secure')
        
        response_data = response.content.decode()
        data = json.loads(response_data)
        data['strategies'] = strategies
        data['cookies_set'] = len(strategies)
        
        response.content = json.dumps(data).encode()
        
        return response


# Versão ainda mais simples - apenas define e retorna cookie na mesma response
@csrf_exempt  
def immediate_cookie_test(request):
    """Teste imediato - define cookie e tenta ler na mesma response"""
    
    if request.method == 'GET':
        # Apenas mostrar cookies
        return JsonResponse({
            'cookies_received': dict(request.COOKIES),
            'total': len(request.COOKIES)
        })
    
    # POST - definir cookie e tentar verificar imediatamente
    test_value = f"test_{request.POST.get('test_id', '123')}"
    
    response = JsonResponse({
        'test_value_set': test_value,
        'message': 'Cookie set - check GET request immediately'
    })
    
    # Define cookie mais simples possível
    response.set_cookie('immediate_test', test_value, max_age=300, httponly=False, secure=False)
    
    return response