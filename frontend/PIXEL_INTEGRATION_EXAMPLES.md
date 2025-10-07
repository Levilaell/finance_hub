# Meta Pixel - Exemplos de Integração

## 📍 Onde Adicionar Eventos no Código

### 1. Login (Recomendado)

**Arquivo:** `app/(auth)/login/page.tsx`

```typescript
// No topo do arquivo, adicione:
import { trackEvent, META_EVENTS } from '@/lib/meta-pixel';

// Na função onSubmit, após login bem-sucedido:
const onSubmit = async (data: LoginCredentials) => {
  try {
    await login(data.email, data.password);

    // 🎯 ADICIONAR AQUI - Rastrear login
    trackEvent(META_EVENTS.COMPLETE_REGISTRATION, {
      content_name: 'User Login',
      status: 'success'
    });

    toast.success('Login realizado com sucesso!');
    router.push('/dashboard');
  } catch (error: any) {
    // ... resto do código
  }
};
```

### 2. Registro/Cadastro

**Arquivo:** Procure por `app/(auth)/register/page.tsx` ou similar

```typescript
import { trackRegistration } from '@/lib/meta-pixel';

const onSubmit = async (data: RegisterData) => {
  try {
    await register(data);

    // 🎯 Rastrear novo cadastro
    trackRegistration({
      status: 'success',
      value: 0, // ou valor do plano se aplicável
      currency: 'BRL'
    });

    toast.success('Cadastro realizado!');
    router.push('/dashboard');
  } catch (error) {
    // ... erro
  }
};
```

### 3. Formulário de Contato

```typescript
import { trackLead, trackContact } from '@/lib/meta-pixel';

const handleContactForm = async (data: ContactFormData) => {
  try {
    await sendContactForm(data);

    // 🎯 Rastrear lead
    trackLead({
      content_name: 'Contact Form',
      value: 0,
      currency: 'BRL'
    });

    // OU usar trackContact
    trackContact({
      content_name: 'Website Contact Form'
    });

    toast.success('Mensagem enviada!');
  } catch (error) {
    // ... erro
  }
};
```

### 4. Seleção de Plano/Assinatura

```typescript
import { trackSubscribe, trackAddPaymentInfo } from '@/lib/meta-pixel';

// Quando usuário seleciona um plano
const handlePlanSelection = (plan: Plan) => {
  trackSubscribe({
    value: plan.price,
    currency: 'BRL',
    content_name: plan.name,
    predicted_ltv: plan.price * 12 // LTV anual
  });
};

// Quando usuário adiciona método de pagamento
const handleAddPayment = () => {
  trackAddPaymentInfo({
    value: selectedPlan.price,
    currency: 'BRL',
    content_category: 'subscription'
  });
};
```

### 5. Compra/Checkout

```typescript
import { trackPurchase } from '@/lib/meta-pixel';

const handlePurchase = async (orderData: OrderData) => {
  try {
    const order = await createOrder(orderData);

    // 🎯 Rastrear compra
    trackPurchase({
      value: order.total,
      currency: 'BRL',
      content_name: order.items.map(i => i.name).join(', '),
      content_ids: order.items.map(i => i.id),
      num_items: order.items.length
    });

    toast.success('Compra realizada!');
  } catch (error) {
    // ... erro
  }
};
```

### 6. Visualização de Página Importante

```typescript
import { trackViewContent } from '@/lib/meta-pixel';

// Em um useEffect quando página carrega
useEffect(() => {
  trackViewContent({
    content_name: 'Pricing Page',
    content_category: 'pricing'
  });
}, []);
```

### 7. Eventos Customizados

```typescript
import { trackCustomEvent } from '@/lib/meta-pixel';

// Para eventos específicos do seu negócio
const handleBankConnection = async () => {
  try {
    await connectBank();

    // 🎯 Evento customizado
    trackCustomEvent('BankConnected', {
      bank_name: selectedBank.name,
      connection_type: 'open_banking',
      status: 'success'
    });

    toast.success('Banco conectado!');
  } catch (error) {
    trackCustomEvent('BankConnectionFailed', {
      bank_name: selectedBank.name,
      error: error.message
    });
  }
};

const handleAIAutomation = () => {
  trackCustomEvent('AIAutomationEnabled', {
    feature: 'financial_automation',
    plan: currentPlan
  });
};
```

## 🎯 Eventos Recomendados para CaixaHub

Baseado na descrição "Automação Financeira para o pequeno e médio varejista brasileiro":

### 1. **Lead Generation**
- Formulário de contato
- Pedido de demo
- Download de material

```typescript
trackLead({ content_name: 'Demo Request', value: 50, currency: 'BRL' });
```

### 2. **Registration**
- Cadastro de conta
- Verificação de email

```typescript
trackRegistration({ status: 'email_verified' });
```

### 3. **Onboarding**
- Conexão de banco
- Configuração inicial
- Primeiro uso da IA

```typescript
trackCustomEvent('OnboardingCompleted', {
  steps_completed: 5,
  bank_connected: true,
  ai_enabled: true
});
```

### 4. **Subscription**
- Seleção de plano
- Upgrade de plano
- Renovação

```typescript
trackSubscribe({
  value: 99.90,
  currency: 'BRL',
  content_name: 'Plano Premium'
});
```

### 5. **Feature Usage**
- Uso de automação
- Relatórios gerados
- Integrações ativadas

```typescript
trackCustomEvent('AutomationCreated', {
  automation_type: 'monthly_report',
  complexity: 'advanced'
});
```

## 🧪 Como Testar

### No Console do Navegador:

```javascript
// 1. Verificar se o pixel está carregado
window.fbq

// 2. Testar evento manualmente
window.fbq('track', 'Lead', { content_name: 'Test', value: 10, currency: 'BRL' })

// 3. Verificar no Network
// Procure por requisições para: facebook.com/tr
```

### No Meta Events Manager:

1. Acesse: https://business.facebook.com/events_manager
2. Selecione seu Pixel: `24169428459391565`
3. Vá em **Test Events**
4. Digite a URL do seu site
5. Execute as ações que disparam eventos
6. Veja os eventos aparecerem em tempo real

## 📊 Eventos Padrão Disponíveis

Veja todos em: `/lib/meta-pixel.ts`

- `trackPageView()` - Automático em toda navegação
- `trackLead()` - Geração de leads
- `trackRegistration()` - Cadastros
- `trackContact()` - Formulário de contato
- `trackSubscribe()` - Assinaturas
- `trackAddPaymentInfo()` - Adicionar pagamento
- `trackPurchase()` - Compras
- `trackViewContent()` - Visualização de conteúdo
- `trackCustomEvent()` - Eventos customizados

## 🔗 Links Úteis

- [Meta Pixel Documentation](https://developers.facebook.com/docs/meta-pixel/)
- [Standard Events Reference](https://developers.facebook.com/docs/meta-pixel/reference)
- [Test Events Tool](https://business.facebook.com/events_manager)
