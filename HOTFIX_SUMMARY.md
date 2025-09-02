# 🚨 HOTFIX CRÍTICO - TokenRefreshView 

## 🐛 Problema Identificado

**Erro 500 no endpoint `/api/auth/refresh/`:**
```
AttributeError: 'Settings' object has no attribute 'JWT_REFRESH_COOKIE_NAME'
```

**Sequência de falha:**
1. ✅ Login funciona (200 OK)
2. ❌ Próxima requisição → 401 Unauthorized (sem Bearer token)
3. ❌ Token refresh tentativa → 500 Internal Server Error
4. ❌ Usuário volta para tela de login

## 🔧 Correção Aplicada

**Arquivo**: `backend/apps/authentication/views.py`
**View**: `CustomTokenRefreshView.post()`

### Antes (Problemático)
```python
# Tentava ler configuração inexistente
refresh_token = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)

# Definia cookies na resposta
response.set_cookie(settings.JWT_ACCESS_COOKIE_NAME, ...)
```

### Depois (Corrigido)
```python
# Usa apenas request body (Bearer tokens)
refresh_token = request.data.get('refresh')

# Retorna apenas JSON
return Response({'access': str(access_token), 'refresh': str(refresh)})
```

## 🎯 Resultado Esperado

Após o deploy do Railway:

1. **Login** → ✅ Funciona normalmente
2. **Token expira** → ✅ Frontend faz refresh automático
3. **Refresh bem-sucedido** → ✅ 200 OK com novos tokens
4. **Usuário permanece logado** → ✅ Não volta para login

## 📊 Status do Deploy

- **Commit**: `f703495` - HOTFIX: TokenRefreshView
- **Push**: ✅ Realizado com sucesso
- **Railway**: 🔄 Deploy automático em andamento
- **Teste**: ⏳ Aguardando deploy para validação

## 🧪 Validação

**Como testar:**
1. Fazer login no sistema
2. Aguardar alguns minutos (token expira em 30min)
3. Fazer alguma ação que requer autenticação
4. **Esperado**: Sistema faz refresh automático sem redirecionar para login
5. **Esperado**: Não há mais erros 500 nos logs

**Logs a observar:**
- ✅ Sem mais `AttributeError: JWT_REFRESH_COOKIE_NAME`
- ✅ `/api/auth/refresh/` retorna 200 OK
- ✅ Requisições subsequentes funcionam com Bearer tokens
