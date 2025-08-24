# 📱 Mobile Safari Cookie Troubleshooting Guide

## 🚨 Problema Atual
Mobile Safari não está enviando cookies JWT após login bem-sucedido, causando erro 401 em requests subsequentes.

## 🔧 Endpoints de Troubleshooting

### 1. Diagnóstico em Tempo Real
```bash
# Verificar que cookies o mobile está enviando
GET https://seu-backend.railway.app/api/auth/troubleshoot/mobile/

# Resposta mostra:
# - Detecção de Mobile Safari
# - Cookies recebidos pelo servidor
# - Configurações atuais
# - Info do browser (host, origin, etc)
```

### 2. Teste de Definição de Cookies
```bash
# Testar diferentes estratégias de cookies
POST https://seu-backend.railway.app/api/auth/troubleshoot/mobile/

# Define vários tipos de cookies para teste:
# - Cookies padrão (httpOnly, Secure)
# - Cookies mobile fallback (acessíveis por JS)
# - Cookies de teste (sem Secure)
```

## 🧪 Como Usar no Mobile

### Passo 1: Diagnóstico Inicial
1. Abra Safari no iPhone/iPad
2. Vá para: `https://seu-backend.railway.app/api/auth/troubleshoot/mobile/`
3. Analise JSON retornado:
   - `browser_info.is_mobile_safari` deve ser `true`
   - `cookies.total_received` mostra quantos cookies o Safari está enviando
   - `cookies.auth_cookies` mostra se cookies de auth estão presentes

### Passo 2: Teste de Login
1. Faça login normal no app
2. **Imediatamente** após login, acesse o endpoint de diagnóstico
3. Verifique se `auth_cookies` agora mostra cookies presentes

### Passo 3: Teste de Estratégias
1. Execute POST no endpoint de troubleshooting
2. Verifique headers de resposta (`X-*`)
3. Execute GET novamente para ver se cookies foram definidos

## 📊 Headers de Debug Disponíveis

Todos os responses incluem headers `X-*` com info de debug:
- `X-Mobile-Safari-Detected`: Se mobile Safari foi detectado
- `X-Cookie-*-Used`: Configurações aplicadas aos cookies
- `X-Request-Origin`: Origin da requisição
- `X-Access-Token-Length`: Tamanho do token (pode ser muito grande)
- `X-Total-Cookies-Received`: Quantos cookies o servidor recebeu

## 🐛 Possíveis Problemas Identificados

### 1. **Token Muito Grande**
- Tokens JWT podem ser muito grandes (>4KB)
- Mobile Safari pode rejeitar cookies grandes
- **Solução**: Headers mostram tamanho dos tokens

### 2. **Cross-Origin Issues**
- Frontend: `https://caixahub.com.br` 
- Backend: `https://financehub-production.up.railway.app`
- **Solução**: Headers mostram origin/host para debug

### 3. **SameSite/Secure Issues**
- Mobile Safari comportamento diferente com SameSite=None
- **Solução**: Sistema detecta mobile e usa SameSite=Lax automaticamente

### 4. **Domain/Path Issues**  
- Cookies podem estar sendo definidos para domínio errado
- **Solução**: Headers mostram domain/path usados

## 💡 Próximos Passos

### Se Cookies Não Aparecem no GET:
1. Verificar se `is_mobile_safari` = true
2. Verificar tamanho dos tokens nos headers
3. Verificar host/origin nos headers
4. Tentar estratégia alternativa

### Se Problema Persistir:
1. Implementar fallback com sessionStorage
2. Usar header-based auth para mobile
3. Implementar token refresh automático

## 🚀 Deploy Status

**Status**: ✅ Implementado em produção
**Endpoints ativos**: 
- `/api/auth/troubleshoot/mobile/` (GET/POST)
- Debug headers habilitados
- Detecção automática de Mobile Safari
- Múltiplas estratégias de cookies

**Como testar agora**:
1. Acesse os endpoints no mobile problemático
2. Compartilhe os JSONs de resposta 
3. Analisaremos os dados para próxima iteração