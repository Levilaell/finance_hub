# ⚡ Guia Rápido de Configuração - Stripe

## ✅ Status: Backend Pronto!

- ✅ Dependências instaladas (stripe + dj-stripe)
- ✅ Migrations rodadas
- ✅ Endpoints criados
- ✅ Middleware configurado

---

## 📋 Falta Fazer: Configurar Stripe Dashboard

### Passo 1: Criar Product "Plano Pro"

1. **Acesse:** https://dashboard.stripe.com/test/products
2. **Certifique-se** de estar em **Test mode** (toggle no canto superior direito)
3. Clique em **"+ Add product"**

**Preencha:**
```
Name: Plano Pro
Description: Acesso completo ao CaixaHub - Finance Hub
```

**Na seção Pricing:**
```
Pricing model: Standard pricing
Price: 97.00
Currency: BRL (Brazilian Real)  ← IMPORTANTE: Selecione BRL
Billing period: Monthly
Recurring: ✅ (deixe marcado)
```

4. Clique em **"Save product"**

### Passo 2: Copiar Price ID

Após salvar o produto:
1. Role a página até a seção **"Pricing"**
2. Você verá algo como: `price_1Abc123XYZ...`
3. **Clique no ícone de copiar** ao lado do Price ID
4. **Abra** o arquivo `backend/.env`
5. **Cole** o Price ID em:

```bash
STRIPE_DEFAULT_PRICE_ID=price_XXXXXXXXXX  # Cole aqui
```

6. **Salve** o arquivo `.env`

### Passo 3: Ativar Customer Portal

1. **Acesse:** https://dashboard.stripe.com/test/settings/billing/portal
2. Clique em **"Activate test link"**
3. Configure as opções:
   - ✅ **Customers can update their payment methods**
   - ✅ **Customers can cancel subscriptions**
   - ✅ **Customers can view invoices**

4. Na seção **"Subscription cancellation":**
   - Selecione: **"Cancel subscriptions immediately"**

5. Clique em **"Save changes"**

### Passo 4: Configurar Grace Period (Opcional)

1. **Acesse:** https://dashboard.stripe.com/test/settings/billing/automatic
2. Em **"Smart Retries":**
   - ✅ Habilite smart retries
3. Em **"When to cancel":**
   - Selecione: **"After 3 days"**

### Passo 5: Ativar Emails Automáticos (Opcional)

1. **Acesse:** https://dashboard.stripe.com/test/settings/emails
2. Ative:
   - ✅ **Customer receipts** (recibos de pagamento)
   - ✅ **Upcoming invoices** (avisos de cobrança)
   - ✅ **Payment failed** (falha de pagamento)

---

## 🧪 Como Testar

### 1. Iniciar Servidores

**Terminal 1 (Backend):**
```bash
cd backend
python manage.py runserver
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

### 2. Fluxo de Teste Completo

#### Passo 1: Criar Conta
1. Acesse: `http://localhost:3000/pricing`
2. Clique em **"Começar Trial de 7 Dias"**
3. Preencha o formulário de cadastro
4. Clique em **"Criar Conta e Iniciar Trial"**

#### Passo 2: Adicionar Cartão (Checkout)
Use cartões de teste Stripe:

**✅ Cartão de Sucesso:**
```
Número: 4242 4242 4242 4242
Data: 12/34 (qualquer data futura)
CVC: 123 (qualquer 3 dígitos)
CEP: 12345
```

**❌ Cartão que Falha (para testar past_due):**
```
Número: 4000 0000 0000 0002
Data: 12/34
CVC: 123
CEP: 12345
```

**🔐 Cartão que requer 3D Secure:**
```
Número: 4000 0025 0000 3155
Data: 12/34
CVC: 123
CEP: 12345
```

#### Passo 3: Verificar no Admin

1. Acesse: `http://localhost:8000/admin/`
2. Login com seu superuser
3. Vá em **Djstripe** → **Subscriptions**
4. Veja a subscription com status **"trialing"**

#### Passo 4: Testar Gerenciamento

1. No frontend, vá em **Settings** (ainda precisa adicionar tab)
2. Ou acesse: `http://localhost:3000/settings`
3. Clique em **"Gerenciar Assinatura"**
4. Você será redirecionado para o Stripe Customer Portal
5. Lá pode: atualizar cartão, cancelar, ver faturas

---

## 🎯 Endpoints Disponíveis

| Endpoint | O que faz |
|----------|-----------|
| `GET /api/subscriptions/config/` | Retorna Stripe public key |
| `GET /api/subscriptions/status/` | Status da assinatura do usuário |
| `POST /api/subscriptions/checkout/` | Criar subscription com trial |
| `POST /api/subscriptions/portal/` | Criar sessão do portal |
| `POST /api/subscriptions/webhooks/stripe/` | Recebe webhooks do Stripe |

### Testar Endpoints (cURL)

**1. Obter Config:**
```bash
curl http://localhost:8000/api/subscriptions/config/
```

**2. Status (precisa autenticação):**
```bash
curl -H "Authorization: Bearer SEU_TOKEN" \
  http://localhost:8000/api/subscriptions/status/
```

---

## 🔧 Próximas Integrações Necessárias

### No Frontend

**1. Adicionar Checkout no Signup Flow:**

Opção A - Página separada:
```tsx
// Criar: frontend/app/checkout/page.tsx
import { CheckoutForm } from '@/components/subscription/CheckoutForm';

export default function CheckoutPage() {
  return <CheckoutForm />;
}
```

Opção B - Integrar no register:
```tsx
// Em: frontend/app/(auth)/register/page.tsx
// Após cadastro bem-sucedido:
router.push('/checkout');
```

**2. Adicionar Tab em Settings:**

```tsx
// Em: frontend/app/settings/page.tsx
import { SubscriptionManagement } from '@/components/subscription/SubscriptionManagement';

<Tabs>
  <TabsTrigger value="subscription">Assinatura</TabsTrigger>
  <TabsContent value="subscription">
    <SubscriptionManagement />
  </TabsContent>
</Tabs>
```

**3. Adicionar Trial Banner no Dashboard:**

```tsx
// Criar: frontend/components/subscription/TrialBanner.tsx
// Ver exemplo no STRIPE_SETUP.md
```

---

## 📊 Verificação Rápida

Execute estes comandos para confirmar que tudo está OK:

```bash
# 1. Backend rodando?
curl http://localhost:8000/health/
# Deve retornar: {"status": "ok"}

# 2. Stripe config OK?
curl http://localhost:8000/api/subscriptions/config/
# Deve retornar: {"publishable_key": "pk_test_..."}

# 3. Migrations OK?
cd backend
python manage.py showmigrations
# djstripe deve mostrar [X] em todas as migrations
```

---

## ⚠️ IMPORTANTE

**Antes de testar o checkout, certifique-se:**

1. ✅ `STRIPE_DEFAULT_PRICE_ID` está configurado no `.env` com o Price ID real
2. ✅ Backend está rodando (`python manage.py runserver`)
3. ✅ Frontend está rodando (`npm run dev`)
4. ✅ Você está em **Test mode** no Stripe Dashboard

---

## 🎯 Próximo Passo

1. **Agora:** Vá ao Stripe Dashboard e crie o Product conforme instruções acima
2. **Depois:** Cole o Price ID no `.env`
3. **Então:** Reinicie o backend
4. **Pronto:** Teste o fluxo completo!

---

**Precisa de ajuda em algum passo específico? Só me avisar! 🚀**
