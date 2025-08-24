# 🚨 FRONTEND HOTFIX - Mobile Safari Authentication

## PROBLEMA URGENTE

O backend está funcionando perfeitamente e enviando tokens em múltiplos formatos, mas o frontend ainda não implementou os fallbacks. Mobile Safari não envia cookies em requests CORS.

## ⚡ HOTFIX IMEDIATO (5 minutos para implementar)

### 1. Atualizar o AuthService (frontend/services/auth.js)

```javascript
class AuthService {
  
  // Adicionar esta função no login existente
  async login(credentials) {
    const response = await fetch('/api/auth/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
      credentials: 'include'
    });
    
    const data = await response.json();
    
    // HOTFIX: Se Mobile Safari detectado, usar fallbacks  
    if (data.mobile_fallback?.detected) {
      console.log('🍎 Mobile Safari - implementing hotfix');
      
      // Armazenar tokens para uso posterior
      sessionStorage.setItem('hotfix_access_token', data.tokens.access);
      sessionStorage.setItem('hotfix_refresh_token', data.tokens.refresh);
      sessionStorage.setItem('hotfix_expires', Date.now() + (data.tokens.expires_in * 1000));
      
      // Backup nos headers se disponível
      const headerToken = response.headers.get('X-Access-Token');
      if (headerToken) {
        localStorage.setItem('hotfix_backup_token', headerToken);
      }
    }
    
    return data;
  }
  
  // Adicionar função para pegar token de qualquer fonte
  getToken() {
    // 1. Tentar sessionStorage (melhor para Mobile Safari)
    const sessionToken = sessionStorage.getItem('hotfix_access_token');
    const expires = parseInt(sessionStorage.getItem('hotfix_expires') || '0');
    
    if (sessionToken && Date.now() < expires) {
      return sessionToken;
    }
    
    // 2. Tentar backup localStorage
    const backupToken = localStorage.getItem('hotfix_backup_token');
    if (backupToken) {
      return backupToken;
    }
    
    return null;
  }
}

// Exportar instância global
export const authService = new AuthService();
```

### 2. Atualizar TODAS as chamadas de API

**CRÍTICO**: Adicionar Authorization header em TODA chamada de API:

```javascript
// No arquivo onde fazem as chamadas de API (apiClient.js ou similar)
import { authService } from './services/auth.js';

// Função helper para chamadas autenticadas
async function makeAuthenticatedRequest(url, options = {}) {
  const token = authService.getToken();
  
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      ...(token && { 'Authorization': `Bearer ${token}` })
    },
    credentials: 'include' // Manter para outros browsers
  });
}

// Substituir TODAS as chamadas existentes:

// ANTES:
// fetch('/api/auth/profile/', { credentials: 'include' })

// DEPOIS:  
// makeAuthenticatedRequest('/api/auth/profile/')

// ANTES:
// fetch('/api/companies/subscription-status/', { credentials: 'include' })

// DEPOIS:
// makeAuthenticatedRequest('/api/companies/subscription-status/')
```

### 3. Implementação Rápida nos Componentes

Se não quiserem mexer muito no código existente, podem adicionar este header interceptor:

```javascript
// No início do app, antes de qualquer chamada de API
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
  // Se for chamada para API autenticada
  if (url.includes('/api/') && !url.includes('/login') && !url.includes('/register')) {
    const token = authService.getToken();
    if (token) {
      options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
      };
    }
  }
  
  return originalFetch.call(this, url, options);
};
```

## 🎯 IMPLEMENTAÇÃO IMEDIATA

### Passo 1: Login (FUNCIONA)
```
✅ User faz login  
✅ Backend detecta Mobile Safari
✅ Backend envia tokens no body + headers
✅ Frontend armazena tokens no sessionStorage
```

### Passo 2: API Calls (PRECISA SER CONSERTADO)
```
❌ Frontend faz GET /api/auth/profile/ SEM Authorization header
❌ Backend rejeita (401 - sem credenciais)  
❌ Frontend redireciona para login

🎯 APÓS HOTFIX:
✅ Frontend faz GET /api/auth/profile/ COM Authorization: Bearer token
✅ Backend aceita e retorna dados
✅ App funciona normalmente
```

## 🚨 CHECKLIST URGENTE

- [ ] Implementar `getToken()` no AuthService
- [ ] Adicionar Authorization header em TODAS as chamadas de API
- [ ] Testar login Mobile Safari → deve funcionar imediatamente
- [ ] Verificar que não quebrou outros browsers

## ⏱️ TEMPO ESTIMADO: 15-30 minutos

Esta é uma solução temporária que pode ser implementada rapidamente. Depois podem implementar a solução completa com toda a arquitetura adequada.

## 🔍 DEBUGGING

Se continuarem tendo problemas, verifiquem no browser Mobile Safari:

```javascript
// No console do Safari Mobile após login:
console.log('Session token:', sessionStorage.getItem('hotfix_access_token'));
console.log('Token expires:', new Date(parseInt(sessionStorage.getItem('hotfix_expires'))));
console.log('Backup token:', localStorage.getItem('hotfix_backup_token'));
```

O problema está 100% no frontend - o backend está funcionando perfeitamente.