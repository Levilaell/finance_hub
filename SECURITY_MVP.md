# Segurança MVP - Implementações

## ✅ Correções Implementadas

### 1. **Sanitização de Logs**
- **Arquivo**: `backend/core/security_utils.py`
- **O que faz**: Remove dados sensíveis (passwords, tokens, CPF, cartões) antes de logar
- **Aplicado em**:
  - `backend/apps/banking/views.py:95`
  - `backend/apps/banking/pluggy_client.py:303`

### 2. **Proteção JWT**
- **Arquivo**: `backend/core/settings/production.py:60-66`
- **O que faz**: Exige JWT_SECRET_KEY separado do DJANGO_SECRET_KEY
- **Erro se faltar**: Sistema não inicia sem JWT_SECRET_KEY

### 3. **Headers de Segurança Frontend**
- **Arquivo**: `frontend/next.config.js:50-65`
- **Headers adicionados**:
  - `X-Frame-Options: DENY` - Previne clickjacking
  - `X-Content-Type-Options: nosniff` - Previne MIME sniffing
  - `Referrer-Policy: strict-origin-when-cross-origin` - Protege URLs
  - `Permissions-Policy` - Bloqueia acesso a câmera/mic/GPS

### 4. **Validação HTTPS**
- **Arquivo**: `frontend/lib/api-client.ts:7-10`
- **O que faz**: Bloqueia API HTTP em produção
- **Erro se HTTP**: Falha imediata com mensagem clara

---

## 🔑 Variáveis de Ambiente Necessárias

### Backend (Produção)

```bash
# Obrigatórias - Sistema não inicia sem elas
DJANGO_SECRET_KEY=<gerar_com_comando_abaixo>
JWT_SECRET_KEY=<gerar_com_comando_abaixo>
DATABASE_URL=postgresql://...

# Gerar secrets:
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Frontend (Produção)

```bash
# Obrigatória
NEXT_PUBLIC_API_URL=https://api.caixahub.com.br  # DEVE ser HTTPS

# Exemplo correto:
NEXT_PUBLIC_API_URL=https://financehub-production.up.railway.app

# ❌ Vai falhar:
NEXT_PUBLIC_API_URL=http://financehub-production.up.railway.app
```

---

## 🛡️ Vulnerabilidades Restantes (Próximas Iterações)

### CRÍTICO - Corrigir após MVP
1. **Rate Limiting** - Adicionar throttling nos endpoints de autenticação
2. **Webhook Signature** - Tornar PLUGGY_WEBHOOK_SECRET obrigatório

### ALTO - Próxima Sprint
3. **JWT em localStorage** - Migrar para httpOnly cookies
4. **Validação de senha** - Adicionar requisitos de complexidade (12+ caracteres)

---

## 📋 Checklist de Deploy

### Antes do Deploy

- [ ] Gerar DJANGO_SECRET_KEY único
- [ ] Gerar JWT_SECRET_KEY único (diferente do DJANGO)
- [ ] Configurar NEXT_PUBLIC_API_URL com HTTPS
- [ ] Verificar PLUGGY_WEBHOOK_SECRET configurado
- [ ] Testar login em ambiente de staging

### Validação Pós-Deploy

```bash
# Verificar headers de segurança
curl -I https://caixahub.com.br

# Deve retornar:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# Content-Security-Policy: ...
```

### Monitoramento

- Verificar logs não contêm dados sensíveis
- Confirmar todas as requisições usam HTTPS
- Testar webhooks com assinatura

---

## 🔧 Comandos Úteis

### Gerar Secret Keys

```bash
# DJANGO_SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# JWT_SECRET_KEY (deve ser diferente)
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Testar Sanitização de Logs

```python
from core.security_utils import sanitize_for_logging

# Teste
data = {
    'email': 'user@email.com',
    'password': 'secret123',
    'token': 'abc123',
    'amount': 100
}

print(sanitize_for_logging(data))
# Output: {'email': 'user@email.com', 'password': '***REDACTED***', 'token': '***REDACTED***', 'amount': 100}
```

---

## ⚠️ Avisos Importantes

1. **JWT_SECRET_KEY**: NUNCA use o mesmo valor de DJANGO_SECRET_KEY
2. **HTTPS**: Frontend SEMPRE requer HTTPS em produção (exceto localhost)
3. **Logs**: Sempre use `sanitize_for_logging()` antes de logar request.data
4. **Webhooks**: Configure PLUGGY_WEBHOOK_SECRET antes de ativar webhooks em produção

---

## 📞 Contato de Segurança

Para reportar vulnerabilidades:
- Email: security@caixahub.com.br (configurar)
- Tempo de resposta: 24-48h
