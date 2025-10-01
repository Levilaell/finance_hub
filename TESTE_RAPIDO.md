# 🚀 Teste Rápido do Sistema de Assinatura

## Erro: "Failed to load Stripe.js"

### Solução:

**1. Certifique-se que o backend está rodando:**

```bash
cd backend
python manage.py runserver
```

Deve aparecer:
```
Starting development server at http://0.0.0.0:8000/
```

**2. Teste se o endpoint está funcionando:**

Abra um novo terminal e execute:
```bash
curl http://localhost:8000/api/subscriptions/config/
```

Deve retornar:
```json
{"publishable_key":"pk_test_51Qp1nsPFSVtvOaJK..."}
```

**Se retornar erro 404 ou não conectar:**
- ✅ Verifique se o backend está realmente rodando
- ✅ Verifique se não há erros no terminal do backend
- ✅ Tente acessar: http://localhost:8000/health/
  - Deve retornar: `{"status":"ok"}`

---

## 🧪 Fluxo de Teste Passo a Passo

### Terminal 1: Backend
```bash
cd C:\Users\Levi Lael\Desktop\finance_hub\backend
python manage.py runserver
```

**Aguarde até ver:**
```
Starting development server at http://0.0.0.0:8000/
```

### Terminal 2: Frontend
```bash
cd C:\Users\Levi Lael\Desktop\finance_hub\frontend
npm run dev
```

**Aguarde até ver:**
```
Ready started on http://localhost:3000
```

### Terminal 3: Testar Endpoints

```bash
# 1. Health check
curl http://localhost:8000/health/

# 2. Stripe config
curl http://localhost:8000/api/subscriptions/config/
```

Se ambos funcionarem, o Stripe.js vai carregar corretamente!

---

## 🎯 Testar no Navegador

### 1. Cadastro + Checkout

1. Acesse: `http://localhost:3000/pricing`
2. Clique em **"Começar Trial de 7 Dias"**
3. Preencha o formulário (qualquer dados válidos)
4. Clique em **"Criar Conta e Iniciar Trial"**
5. Você será redirecionado para `/checkout`
6. **Agora deve aparecer o formulário do Stripe Elements**

### 2. Adicionar Cartão de Teste

No formulário de checkout:
```
Card number: 4242 4242 4242 4242
MM/YY: 12/34
CVC: 123
ZIP: 12345
```

Clique em **"Iniciar Trial de 7 Dias"**

### 3. Sucesso!

- ✅ Redirecionado para `/dashboard`
- ✅ Acesso completo liberado
- ✅ Status: Trial ativo (7 dias)

---

## 🐛 Troubleshooting

### Erro: "Failed to load Stripe.js"
**Causa:** Backend não está respondendo
**Solução:**
1. Reinicie o backend: `python manage.py runserver`
2. Verifique se porta 8000 está livre
3. Teste: `curl http://localhost:8000/health/`

### Erro: "publishable_key not configured"
**Causa:** Variável STRIPE_TEST_PUBLIC_KEY não está no .env
**Solução:**
1. Abra `backend/.env`
2. Verifique se tem: `STRIPE_TEST_PUBLIC_KEY=pk_test_...`
3. Reinicie o backend

### Erro: "price_id is required"
**Causa:** STRIPE_DEFAULT_PRICE_ID não está configurado
**Solução:**
1. Verifique no `.env`: `STRIPE_DEFAULT_PRICE_ID=price_1SDP6YPFSVtvOaJKcfspO91k`
2. Esse valor deve estar preenchido (não vazio)

### Erro no Console do Navegador
Abra F12 (DevTools) → Console
- Veja qual é o erro específico
- Geralmente mostra se é problema de CORS, network ou key inválida

---

## ✅ Checklist de Verificação

Antes de testar, confirme:

- [ ] Backend rodando (porta 8000)
- [ ] Frontend rodando (porta 3000)
- [ ] `.env` tem `STRIPE_TEST_PUBLIC_KEY`
- [ ] `.env` tem `STRIPE_TEST_SECRET_KEY`
- [ ] `.env` tem `STRIPE_DEFAULT_PRICE_ID=price_1SDP6YPFSVtvOaJKcfspO91k`
- [ ] Ngrok rodando para webhooks (opcional para teste inicial)

---

## 🎯 Comandos Úteis

```bash
# Ver logs do backend em tempo real
cd backend
tail -f debug.log

# Verificar se servidor está rodando (Windows)
netstat -an | findstr :8000

# Testar endpoint manualmente
curl -v http://localhost:8000/api/subscriptions/config/
```

---

**Se ainda tiver erro, me avise qual mensagem aparece no console do navegador (F12)!**
