# 🧪 Guia de Teste - Sistema de Assinatura

## ✅ O que já está pronto:

- ✅ Backend rodando na porta 8000
- ✅ Stripe configurado (Price ID: `price_1SDP6YPFSVtvOaJKcfspO91k`)
- ✅ Webhooks configurados via ngrok
- ✅ Frontend integrado com fluxo de checkout

---

## 🚀 Como Testar AGORA

### Passo 1: Iniciar Frontend

**Terminal separado:**
```bash
cd frontend
npm run dev
```

### Passo 2: Testar Fluxo Completo

#### 1. Criar Nova Conta

1. Acesse: `http://localhost:3000/pricing`
2. Clique em **"Começar Trial de 7 Dias"**
3. Preencha o formulário de cadastro:
   ```
   Nome: Teste
   Sobrenome: Silva
   Email: teste@example.com
   Empresa: Empresa Teste Ltda
   CNPJ: 12.345.678/0001-90
   Telefone: (11) 99999-9999
   Tipo: MEI
   Setor: Tecnologia
   Senha: Teste@123
   ```
4. Clique em **"Criar Conta e Iniciar Trial"**

#### 2. Checkout (Adicionar Cartão)

Você será redirecionado para `/checkout`. Use o **cartão de teste Stripe**:

```
Número do cartão: 4242 4242 4242 4242
Data de validade: 12/34
CVC: 123
CEP: 12345
```

Clique em **"Iniciar Trial de 7 Dias"**

#### 3. Dashboard Liberado

Após o checkout bem-sucedido:
- ✅ Você será redirecionado para `/dashboard`
- ✅ Terá acesso completo ao sistema por 7 dias
- ✅ Status: **trialing**

---

## 🔍 Verificar no Admin

### 1. Acessar Django Admin

1. Acesse: `http://localhost:8000/admin/`
2. Faça login com seu superuser

### 2. Verificar Subscription Criada

1. Vá em **Djstripe** → **Subscriptions**
2. Você verá a subscription criada:
   - **Status:** trialing
   - **Customer:** Vinculado ao seu usuário
   - **Trial end:** Data daqui 7 dias

### 3. Gerenciar pelo Admin

No admin do dj-stripe você pode:
- ✅ Ver todas as subscriptions
- ✅ Filtrar por status
- ✅ Ver detalhes do customer
- ✅ Ver payment methods
- ✅ Ver invoices

**Para cancelar uma subscription pelo admin:**
1. Entre no Subscription
2. Clique em **"View in Stripe Dashboard"** (link no topo)
3. Ou use os métodos programáticos via shell

---

## 🎨 Testar Features de UX

### 1. Ver Status da Assinatura

1. No dashboard, vá em **Settings** (menu lateral)
2. Clique na tab **"Assinatura"**
3. Você verá:
   - Status: Trial Ativo
   - Dias restantes: 7
   - Próxima cobrança: Data daqui 7 dias
   - Cartão: •••• 4242

### 2. Gerenciar via Customer Portal

1. Em Settings → Assinatura
2. Clique em **"Gerenciar Assinatura"**
3. Você será redirecionado para o **Stripe Customer Portal**
4. Lá pode:
   - ✅ Atualizar método de pagamento
   - ✅ Cancelar assinatura
   - ✅ Ver histórico de faturas
   - ✅ Baixar recibos

### 3. Testar Cancelamento

No Customer Portal:
1. Clique em **"Cancel plan"**
2. Confirme o cancelamento
3. Volte ao CaixaHub
4. Refresh na página de Settings
5. Status mudará para **"Cancelado"**

---

## 🧪 Outros Cartões de Teste

### Cartão que Falha (testar past_due)
```
Número: 4000 0000 0000 0002
Data: 12/34
CVC: 123
```
Use este para simular falha de pagamento.

### Cartão com 3D Secure
```
Número: 4000 0025 0000 3155
Data: 12/34
CVC: 123
```
Testa autenticação adicional.

### Outros Cenários
```
Cartão declinado: 4000 0000 0000 0341
Cartão expirado: 4000 0000 0000 0069
Sem fundos: 4000 0000 0000 9995
```

Veja todos em: https://stripe.com/docs/testing

---

## 🔧 Endpoints para Testar Manualmente

### 1. Config (público)
```bash
curl http://localhost:8000/api/subscriptions/config/
```

Resposta esperada:
```json
{
  "publishable_key": "pk_test_..."
}
```

### 2. Status (precisa autenticação)

Primeiro, faça login e obtenha o token:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@example.com","password":"Teste@123"}'
```

Depois, use o token:
```bash
curl http://localhost:8000/api/subscriptions/status/ \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

Resposta esperada:
```json
{
  "status": "trialing",
  "trial_end": "2025-10-08T...",
  "current_period_end": "2025-10-08T...",
  "cancel_at_period_end": false,
  "days_until_renewal": 7,
  "amount": 97.0,
  "currency": "BRL",
  "payment_method": {
    "last4": "4242",
    "brand": "visa"
  }
}
```

---

## 🎯 Fluxo Completo a Testar

### Cenário 1: Novo Usuário com Sucesso
```
1. Register → 2. Checkout → 3. Dashboard → 4. Settings (ver status)
✅ Deve funcionar sem erros
✅ Status deve ser "trialing"
✅ Acesso completo liberado
```

### Cenário 2: Gerenciar Assinatura
```
1. Settings → 2. Tab Assinatura → 3. Gerenciar → 4. Customer Portal
✅ Deve redirecionar para portal.stripe.com
✅ Pode atualizar cartão
✅ Pode cancelar
```

### Cenário 3: Subscription Expirada
```
1. Cancelar via portal → 2. Tentar acessar Dashboard
✅ Deve redirecionar para /subscription/expired
✅ Opção de reativar disponível
```

### Cenário 4: Falha de Pagamento
```
1. Usar cartão 4000 0000 0000 0002 → 2. Aguardar fim do trial
✅ Status muda para "past_due"
✅ Banner de aviso aparece
✅ Botão para atualizar pagamento
```

---

## 🐛 Se Algo Não Funcionar

### Problema: "publishable_key não retorna"
```bash
# Verificar se variáveis estão corretas:
cd backend
cat .env | grep STRIPE
```

### Problema: "Erro ao criar subscription"
```bash
# Verificar logs do backend:
tail -f backend/debug.log

# Ou ver output do servidor no terminal
```

### Problema: "Redirect para /subscription/expired"
```bash
# Verificar se subscription foi criada:
python manage.py shell
>>> from djstripe.models import Subscription
>>> Subscription.objects.all()
```

### Problema: "Stripe Elements não carrega"
```bash
# Verificar se o frontend está pegando o publishable key:
# Abra o console do navegador (F12) e veja erros
```

---

## 📊 Verificações Finais

Execute estes comandos para validar:

```bash
# 1. Backend está rodando?
curl http://localhost:8000/health/
# Esperado: {"status": "ok"}

# 2. Stripe config OK?
curl http://localhost:8000/api/subscriptions/config/
# Esperado: {"publishable_key": "pk_test_..."}

# 3. Price ID configurado?
cd backend
grep STRIPE_DEFAULT_PRICE_ID .env
# Esperado: STRIPE_DEFAULT_PRICE_ID=price_1SDP6YPFSVtvOaJKcfspO91k
```

---

## 🎯 Próximos Passos Após Teste

Depois de testar tudo:

1. **Criar Superuser** (se ainda não tem):
```bash
python manage.py createsuperuser
```

2. **Acessar Admin** e explorar os modelos do dj-stripe

3. **Configurar emails** (opcional):
   - Trial ending notification
   - Payment failed notification
   - Subscription canceled confirmation

4. **Deploy em produção:**
   - Trocar `STRIPE_LIVE_MODE=True`
   - Adicionar keys de produção
   - Configurar webhook de produção
   - Criar Product/Price em modo live

---

## 📞 Suporte

Se tiver problemas:
1. Verificar logs: `backend/debug.log`
2. Console do navegador (F12)
3. Stripe Dashboard → Logs
4. Webhook logs no ngrok: `http://127.0.0.1:4040`

---

**Tudo pronto para testar! 🚀**

Inicie o frontend (`npm run dev`) e acesse `http://localhost:3000/pricing`
