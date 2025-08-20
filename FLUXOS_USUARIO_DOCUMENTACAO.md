# 📋 Documentação Completa: Fluxos do Usuário - Conexão Bancária, Pagamentos e Webhooks

## 🎯 Visão Geral

Este documento detalha todos os fluxos que um usuário pode experimentar no sistema Finance Hub, incluindo conexões bancárias via Pluggy, gerenciamento de pagamentos/assinaturas via Stripe, e os webhooks que são acionados durante esses processos.

---

## 🏦 FLUXOS DE CONEXÃO BANCÁRIA (PLUGGY)

### 📊 Estados do Sistema

#### **Estados do PluggyItem**
```
ITEM_STATUS_CHOICES:
- LOGIN_IN_PROGRESS    → Conectando ao banco
- WAITING_USER_INPUT   → Aguardando MFA/2FA do usuário  
- UPDATING            → Sincronizando dados
- UPDATED             → Dados atualizados com sucesso
- LOGIN_ERROR         → Erro de credenciais
- OUTDATED            → Dados desatualizados
- ERROR               → Erro geral
- DELETED             → Item removido
- CONSENT_REVOKED     → Consentimento revogado
```

#### **Estados de Execução**
```
EXECUTION_STATUS_CHOICES:
- CREATED                        → Item criado
- SUCCESS                        → Sucesso
- PARTIAL_SUCCESS               → Sucesso parcial
- LOGIN_ERROR                   → Erro de login
- INVALID_CREDENTIALS           → Credenciais inválidas
- USER_INPUT_TIMEOUT            → Timeout de MFA
- USER_AUTHORIZATION_PENDING    → Aguardando autorização
- USER_AUTHORIZATION_NOT_GRANTED → Autorização negada
```

### 🔄 Jornada Completa do Usuário

#### **1. Iniciar Conexão Bancária**

**Endpoint**: `POST /api/banking/pluggy/connect-token/`

**Fluxo**:
```
1. Usuário clica "Conectar Banco"
2. Sistema verifica limites do plano
   ✅ Dentro do limite → Continua
   ❌ Limite excedido → Retorna erro 403 com upgrade
3. Cria Connect Token com Pluggy
4. Retorna URL do Pluggy Connect
5. Usuário é redirecionado para interface Pluggy
```

**Validações de Plano**:
```python
# Verificação de limite de contas bancárias
if not company.can_add_bank_account():
    return Response({
        'error': 'Limite de contas bancárias atingido',
        'current': current_count,
        'limit': plan_limit,
        'upgrade_required': True,
        'suggested_plan': 'professional' | 'enterprise'
    }, status=403)
```

#### **2. Autenticação no Pluggy Connect**

**Interface Externa (Pluggy)**:
```
1. Usuário seleciona banco
2. Insere credenciais
3. Banco pode solicitar MFA/2FA
4. Pluggy retorna para callback URL
```

**Estados Possíveis**:
- ✅ **Sucesso**: Credenciais válidas → `status: UPDATING`
- ⚠️ **MFA Requerido**: `status: WAITING_USER_INPUT`
- ❌ **Falha**: Credenciais inválidas → `status: LOGIN_ERROR`

#### **3. Callback - Processar Conexão**

**Endpoint**: `POST /api/banking/pluggy/callback/`

**Fluxo Detalhado**:
```
1. Recebe item_id do Pluggy
2. Busca dados do item via API Pluggy
3. Verifica/cria Connector:
   - Busca connector existente
   - Se não existe, busca da API Pluggy
   - Cria registro local
4. Cria/atualiza PluggyItem:
   - Status, execution_status
   - Dados de erro se houver
   - Parâmetros MFA criptografados
5. Busca contas bancárias
6. Cria registros BankAccount
7. Enfileira sincronização inicial (se item pronto)
```

**Resultados**:
- ✅ **Sucesso**: Item criado, contas disponíveis
- ⚠️ **MFA Pendente**: Aguardando input do usuário
- ❌ **Erro**: Falha na conexão

#### **4. Tratamento de MFA (Multi-Factor Authentication)**

**Cenário**: Status `WAITING_USER_INPUT`

**Fluxo MFA**:
```
1. Sistema detecta MFA via webhook ou polling
2. Usuário é direcionado para tela MFA
3. Usuário insere código/resposta MFA
4. Sistema envia para Pluggy via PATCH /items/{id}
5. Pluggy processa MFA
6. Webhook confirma sucesso/falha
```

**Timeout MFA**:
```
- Timeout: 60 segundos
- Status resultante: USER_INPUT_TIMEOUT
- Ação necessária: Reconexão completa
```

#### **5. Sincronização de Transações**

**Trigger Automático**:
```
- Item status: UPDATED | OUTDATED
- Via webhook: item/updated
- Via manual: Botão "Sincronizar"
```

**Endpoint Manual**: `POST /api/banking/accounts/{id}/sync/`

**Processo de Sincronização**:
```
1. Verifica status do item
   ❌ LOGIN_ERROR → Solicita reconexão
   ❌ WAITING_USER_INPUT → Solicita MFA
   ✅ UPDATED/OUTDATED → Continua

2. Enfileira task assíncrona (Celery):
   - Busca transações via API Pluggy
   - Processa paginação
   - Categoriza transações
   - Salva no banco local
   - Atualiza contadores de uso

3. Fallback síncrono se Celery indisponível
```

---

## 💳 FLUXOS DE PAGAMENTO E ASSINATURA (STRIPE)

### 📊 Estados do Sistema

#### **Estados de Assinatura**
```
STATUS_CHOICES:
- trial     → Período de teste
- active    → Assinatura ativa
- cancelled → Cancelada
- expired   → Expirada
- past_due  → Pagamento em atraso
```

#### **Estados de Pagamento**
```
STATUS_CHOICES:
- pending    → Aguardando processamento
- processing → Processando
- succeeded  → Sucesso
- failed     → Falhou
- cancelled  → Cancelado
- refunded   → Reembolsado
```

### 🔄 Jornada de Assinatura

#### **1. Seleção de Plano**

**Endpoint**: `GET /api/payments/plans/`

**Planos Disponíveis**:
```
- starter: R$ 29/mês
  ├── 3 contas bancárias
  ├── 1.000 transações/mês
  └── Suporte básico

- professional: R$ 79/mês
  ├── 10 contas bancárias
  ├── 5.000 transações/mês
  ├── AI Insights
  └── Suporte prioritário

- enterprise: R$ 199/mês
  ├── Contas ilimitadas
  ├── Transações ilimitadas
  ├── AI Insights avançado
  └── Suporte dedicado
```

#### **2. Criar Sessão de Checkout**

**Endpoint**: `POST /api/payments/checkout/`

**Validações**:
```python
# Verificar se já tem assinatura ativa
if company.subscription.is_active:
    raise PaymentException('Company already has active subscription')

# Validar plano selecionado
if not SubscriptionPlan.objects.filter(id=plan_id, is_active=True).exists():
    raise InvalidRequestException('Invalid subscription plan')
```

**Processo**:
```
1. Valida empresa e plano
2. Cria customer no Stripe (se não existe)
3. Cria checkout session com metadata:
   - company_id
   - plan_id
   - billing_period (monthly/yearly)
4. Retorna checkout URL
5. Usuário é redirecionado para Stripe
```

#### **3. Processamento de Pagamento (Stripe)**

**Interface Externa (Stripe)**:
```
1. Usuário insere dados do cartão
2. Stripe processa pagamento
3. Cria subscription automática
4. Envia webhooks para sistema
```

#### **4. Webhooks de Confirmação**

**Webhook**: `checkout.session.completed`

**Processamento**:
```
1. Valida webhook signature
2. Extrai metadata (company_id, plan_id)
3. Previne race conditions com locks
4. Cria/atualiza Subscription:
   - Status: active
   - Períodos de billing
   - Referências Stripe
5. Cria registro Payment
6. Envia notificações real-time
7. Log de auditoria
```

#### **5. Renovações Automáticas**

**Webhook**: `invoice.payment_succeeded`

**Fluxo**:
```
1. Stripe cobra renovação automática
2. Sistema recebe webhook
3. Atualiza períodos da subscription
4. Registra novo payment
5. Notifica usuário do sucesso
```

#### **6. Falhas de Pagamento**

**Webhook**: `invoice.payment_failed`

**Tratamento**:
```
1. Subscription → status: past_due
2. Registra payment com status: failed
3. Inicia retry logic inteligente:
   - Tentativa 1: 3 dias
   - Tentativa 2: 7 dias  
   - Tentativa 3: 14 dias
4. Notifica usuário
5. Eventual cancelamento se não resolvido
```

---

## 🔔 SISTEMA DE WEBHOOKS

### 📊 Cobertura de Webhooks

#### **Stripe Webhooks (18 Suportados)**

**Subscription Events** ✅:
```
- checkout.session.completed         → Assinatura criada
- customer.subscription.created      → Nova subscription
- customer.subscription.updated      → Subscription alterada
- customer.subscription.deleted      → Subscription cancelada
- customer.subscription.trial_will_end → Trial terminando
```

**Invoice Events** ✅:
```
- invoice.payment_succeeded          → Pagamento aprovado
- invoice.payment_failed            → Pagamento falhou
- invoice.payment_action_required   → Ação necessária
```

**Payment Events** ✅:
```
- payment_intent.succeeded          → Pagamento confirmado
- payment_intent.payment_failed     → Pagamento falhou
```

**Customer Events** ✅:
```
- customer.updated                  → Cliente atualizado
- customer.deleted                  → Cliente removido
```

**Payment Method Events** ✅:
```
- payment_method.attached           → Método adicionado
- payment_method.detached          → Método removido
- payment_method.updated           → Método atualizado
```

**Security Events** ✅:
```
- charge.dispute.created           → Disputa iniciada
- charge.dispute.closed           → Disputa resolvida
- charge.dispute.funds_withdrawn  → Fundos retidos
- charge.dispute.funds_reinstated → Fundos devolvidos
```

#### **Pluggy Webhooks (12 Suportados)**

**Item Events** ✅:
```
- item/created              → Item conectado
- item/updated              → Item sincronizado
- item/error                → Erro no item
- item/deleted              → Item removido
- item/waiting_user_input   → Aguardando MFA
- item/login_succeeded      → Login bem-sucedido
```

**Transaction Events** ✅:
```
- transactions/created      → Novas transações
- transactions/updated      → Transações alteradas
- transactions/deleted      → Transações removidas
```

**Account Events** ✅:
```
- accounts/created          → Novas contas
- accounts/updated          → Contas alteradas
```

**Other Events** ✅:
```
- consent/revoked           → Consentimento revogado
```

### 🚨 Webhooks Críticos Não Suportados

#### **Stripe - Gaps Críticos** ❌:
```
- invoice.created                    → Não detecta criação de faturas
- invoice.finalized                  → Não detecta finalização
- payment_intent.requires_action     → Ações de usuário perdidas
- charge.succeeded/failed            → Charges básicos ignorados
- radar.early_fraud_warning.created  → Sem alertas de fraude
```

#### **Pluggy - Gaps Críticos** ❌:
```
- connector/status_updated           → Status de conectores perdido
- payment_intent/created             → Pagamentos PIX não suportados
- payment_intent/completed           → Confirmação PIX perdida
- scheduled_payment/*                → Pagamentos agendados ignorados
- automatic_pix_payment/*            → PIX automático não suportado
```

### ⚙️ Processamento de Webhooks

#### **Stripe - Pipeline de Segurança**

**7 Camadas de Validação**:
```
1. Signature validation (HMAC-SHA256)
2. Timestamp validation (5min tolerance)
3. Event structure validation
4. Replay attack protection
5. Event type validation
6. Rate limiting per event type
7. Content validation
```

**Processamento**:
```
1. Webhook recebido
2. Validação de segurança
3. Distributed lock (event_id)
4. Database transaction
5. Handler específico
6. Audit logging
7. Real-time notifications
8. Success/error tracking
```

#### **Pluggy - Pipeline Básico**

**Validação Atual**:
```
1. HMAC-SHA256 signature (se configurado)
2. Event structure parsing
3. Idempotency check (event_id)
4. Async processing (Celery)
```

**⚠️ Vulnerabilidades Identificadas**:
```
- Sem autenticação obrigatória
- Aceita webhooks sem secret
- Logs expõem headers sensíveis
- Sem rate limiting específico
```

---

## 🔄 FLUXOS INTEGRADOS E JORNADAS COMPLETAS

### 🎯 Jornada 1: Novo Usuário - Setup Completo

```
1. Registro/Login
2. Criação de empresa
3. Período de trial automático (14 dias)
4. Conexão primeira conta bancária:
   ├── Connect token
   ├── Pluggy Connect
   ├── MFA (se necessário)
   ├── Callback success
   └── Primeira sincronização
5. Exploração das features
6. Upgrade para plano pago:
   ├── Checkout Stripe
   ├── Pagamento aprovado
   ├── Webhook confirmation
   └── Assinatura ativa
7. Uso contínuo com renovações automáticas
```

### 🎯 Jornada 2: Usuário Existente - Nova Conta

```
1. Login em conta existente
2. Verificação de limites:
   ✅ Dentro do limite → Continua
   ❌ Limite excedido → Upgrade necessário
3. Nova conexão bancária
4. Sincronização automática
5. Categorização de transações
6. Dashboards atualizados
```

### 🎯 Jornada 3: Problemas e Recuperação

#### **Conexão Bancária Falha**:
```
1. MFA timeout → Reconexão necessária
2. Login error → Verificar credenciais
3. Bank maintenance → Retry automático
4. Item deleted → Nova conexão
```

#### **Problemas de Pagamento**:
```
1. Cartão recusado → Retry logic
2. Cartão expirado → Solicitar atualização
3. Falta de fundos → Grace period
4. Disputa → Processo de resolução
```

---

## 🚨 TRATAMENTO DE ERROS E RECUPERAÇÃO

### 🔧 Estratégias de Resilência

#### **Pluggy API**:
```
- Rate limiting: 600 req/min
- Timeout configurável: 30s default
- Retry com exponential backoff
- Circuit breaker para falhas consecutivas
- Fallback para sync síncrono sem Celery
```

#### **Stripe API**:
```
- Webhook signature validation obrigatória
- Replay protection via cache
- Idempotency keys para operações
- Automatic retry para webhooks falhos
- Graceful degradation para falhas temporárias
```

#### **Sistema Interno**:
```
- Database transactions para consistência
- Distributed locks para race conditions
- Queue monitoring e dead letter handling
- Health checks para dependências externas
- Comprehensive audit logging
```

### 📊 Monitoramento e Alertas

#### **Métricas Críticas**:
```
- Webhook success rate: >99.5%
- API response time: <500ms p95
- Transaction sync success: >98%
- Payment success rate: >95%
- Error rate per endpoint: <1%
```

#### **Alertas Configurados**:
```
- Failed webhooks > 5/min
- API timeout > 30s
- Sync failures > 10/hour
- Payment failures > 2/hour
- Queue backup > 1000 jobs
```

---

## 🔐 SEGURANÇA E COMPLIANCE

### 🛡️ Medidas de Segurança

#### **Dados Bancários**:
```
- MFA parameters encrypted at rest
- TLS 1.3 for all communications
- No sensitive data in logs
- Credential rotation for API keys
- Webhook signature validation
```

#### **Pagamentos**:
```
- PCI DSS compliance via Stripe
- No card data storage local
- Encrypted webhook payloads
- IP allowlisting para webhooks
- Audit trail completo
```

### 📋 Compliance

```
✅ LGPD: Consentimento explícito para dados
✅ Open Banking: Integração via Pluggy certificado
✅ PCI DSS: Stripe como payment processor
✅ SOC 2: Logs de auditoria e monitoramento
```

---

## 📈 OTIMIZAÇÕES E MELHORIAS FUTURAS

### 🔄 Curto Prazo (2 semanas)

1. **Webhooks Críticos**:
   - Implementar todos os eventos Stripe ausentes
   - Adicionar eventos de pagamento PIX Pluggy
   - Melhorar validação de segurança Pluggy

2. **Experiência do Usuário**:
   - Real-time status updates via WebSocket
   - Retry automático para MFA timeout
   - Melhor feedback visual de progresso

### 🚀 Médio Prazo (1-2 meses)

1. **Performance**:
   - Webhook batching para volume alto
   - Cache inteligente para dados frequentes
   - Otimização de queries database

2. **Resilência**:
   - Circuit breakers para APIs externas
   - Dead letter queues para falhas
   - Health checks automatizados

### 🎯 Longo Prazo (3-6 meses)

1. **Escalabilidade**:
   - Horizontal scaling para webhooks
   - Database sharding por empresa
   - CDN para assets estáticos

2. **Features Avançadas**:
   - Machine learning para categorização
   - Fraud detection avançado
   - Multi-banco aggregation

---

## 📊 DIAGRAMAS DE FLUXO

### 🏦 Fluxo de Conexão Bancária Pluggy

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Usuário       │    │   Finance Hub    │    │     Pluggy      │
│   Frontend      │    │    Backend       │    │      API        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │ 1. Conectar Banco      │                        │
         ├───────────────────────►│                        │
         │                        │ 2. Verificar Plano    │
         │                        ├─────────────┐          │
         │                        │             │          │
         │                        │◄────────────┘          │
         │                        │ 3. Create Token       │
         │                        ├───────────────────────►│
         │                        │◄───────────────────────┤
         │ 4. Redirect Pluggy     │                        │
         │◄───────────────────────┤                        │
         │                        │                        │
         │ 5. User Auth + MFA     │                        │
         ├─────────────────────────────────────────────────►│
         │                        │                        │
         │                        │ 6. Webhook Callback   │
         │                        │◄───────────────────────┤
         │                        │                        │
         │                        │ 7. Get Item Data      │
         │                        ├───────────────────────►│
         │                        │◄───────────────────────┤
         │                        │                        │
         │ 8. Success Response    │                        │
         │◄───────────────────────┤                        │
         │                        │                        │
         │                        │ 9. Queue Sync         │
         │                        ├─────────────┐          │
         │                        │             ▼          │
         │                        │         [Celery]       │
         │                        │             │          │
         │                        │ 10. Fetch Transactions │
         │                        │◄────────────┼─────────►│
         │                        │             │          │
         │                        │ 11. Save to DB        │
         │                        │◄────────────┘          │
```

### 💳 Fluxo de Pagamento Stripe

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Usuário       │    │   Finance Hub    │    │     Stripe      │
│   Frontend      │    │    Backend       │    │      API        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │ 1. Selecionar Plano    │                        │
         ├───────────────────────►│                        │
         │                        │ 2. Verificar Assinatura │
         │                        ├─────────────┐          │
         │                        │             │          │
         │                        │◄────────────┘          │
         │                        │ 3. Create Customer    │
         │                        ├───────────────────────►│
         │                        │◄───────────────────────┤
         │                        │ 4. Create Checkout    │
         │                        ├───────────────────────►│
         │                        │◄───────────────────────┤
         │ 5. Redirect Stripe     │                        │
         │◄───────────────────────┤                        │
         │                        │                        │
         │ 6. Payment Process     │                        │
         ├─────────────────────────────────────────────────►│
         │                        │                        │
         │                        │ 7. Webhook: checkout.completed
         │                        │◄───────────────────────┤
         │                        │                        │
         │                        │ 8. Validate & Process │
         │                        ├─────────────┐          │
         │                        │             ▼          │
         │                        │    [Create Subscription] │
         │                        │             │          │
         │                        │    [Create Payment]    │
         │                        │             │          │
         │                        │    [Send Notification] │
         │                        │◄────────────┘          │
         │                        │                        │
         │ 9. Success Page        │                        │
         │◄───────────────────────┤                        │
```

### 🔔 Fluxo de Webhook Processing

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   External      │    │   Finance Hub    │    │     Handler     │
│   Service       │    │   Webhook EP     │    │    Pipeline     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │ 1. Send Webhook        │                        │
         ├───────────────────────►│                        │
         │                        │ 2. Security Validation │
         │                        ├─────────────┐          │
         │                        │   ┌─────────▼────────┐ │
         │                        │   │ • Signature     │ │
         │                        │   │ • Timestamp     │ │
         │                        │   │ • Rate Limit    │ │
         │                        │   │ • Idempotency   │ │
         │                        │   └─────────┬────────┘ │
         │                        │             │          │
         │                        │◄────────────┘          │
         │                        │ 3. Route to Handler   │
         │                        ├───────────────────────►│
         │                        │                        │
         │                        │                   ┌────▼────┐
         │                        │                   │ Handler │
         │                        │                   │ Logic   │
         │                        │                   └────┬────┘
         │                        │                        │
         │                        │ 4. Database Updates   │
         │                        │◄───────────────────────┤
         │                        │                        │
         │                        │ 5. Queue Tasks        │
         │                        ├─────────────┐          │
         │                        │             ▼          │
         │                        │         [Celery]       │
         │                        │                        │
         │ 6. HTTP 200 OK         │                        │
         │◄───────────────────────┤                        │
```

### 🔄 Fluxo de MFA Timeout e Recuperação

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Usuário       │    │   Finance Hub    │    │     Pluggy      │
│   Frontend      │    │    Backend       │    │      API        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │ 1. Connection Started  │                        │
         │                        │                        │
         │                        │ Status: WAITING_USER_INPUT
         │                        │◄───────────────────────┤
         │                        │                        │
         │ 2. Show MFA Screen     │                        │
         │◄───────────────────────┤                        │
         │                        │                        │
         │ 3. User Timeout (60s)  │                        │
         │ ╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱ │                        │
         │                        │ Webhook: item/error    │
         │                        │◄───────────────────────┤
         │                        │                        │
         │                        │ Status: USER_INPUT_TIMEOUT
         │                        ├─────────────┐          │
         │                        │             ▼          │
         │                        │    [Update Item]       │
         │                        │             │          │
         │                        │    [Clear MFA Data]    │
         │                        │◄────────────┘          │
         │                        │                        │
         │ 4. Show Reconnect UI   │                        │
         │◄───────────────────────┤                        │
         │                        │                        │
         │ 5. Try Again           │                        │
         ├───────────────────────►│                        │
         │                        │ 6. New Connect Token  │
         │                        ├───────────────────────►│
         │                        │◄───────────────────────┤
         │                        │                        │
         │ 7. New Pluggy Session  │                        │
         │◄───────────────────────┤                        │
```

### 💔 Fluxo de Falha de Pagamento e Recovery

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Stripe        │    │   Finance Hub    │    │     Usuário     │
│   Billing       │    │    Backend       │    │    Frontend     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │ 1. Auto Billing Fails  │                        │
         ├───────────────────────►│                        │
         │                        │                        │
         │ Webhook: invoice.payment_failed               │
         ├───────────────────────►│                        │
         │                        │ 2. Process Failure    │
         │                        ├─────────────┐          │
         │                        │   ┌─────────▼────────┐ │
         │                        │   │ • Set past_due  │ │
         │                        │   │ • Log payment   │ │
         │                        │   │ • Start retry   │ │
         │                        │   │ • Notify user   │ │
         │                        │   └─────────┬────────┘ │
         │                        │             │          │
         │                        │◄────────────┘          │
         │                        │ 3. Send Notification   │
         │                        ├───────────────────────►│
         │                        │                        │
         │                        │ 4. Retry Logic        │
         │                        ├─────────────┐          │
         │                        │             ▼          │
         │                        │    Day 3: Retry 1     │
         │◄───────────────────────┼────────────────────────│
         │                        │             │          │
         │ Still Fails            │    Day 7: Retry 2     │
         ├───────────────────────►│◄────────────┘          │
         │                        │             │          │
         │                        │    Day 14: Final      │
         │                        ├─────────────┼─────────►│
         │                        │             │          │
         │ Success/Final Fail     │    Cancel/Reactivate  │
         ├───────────────────────►│◄────────────┘          │
```

---

## 📞 Suporte e Troubleshooting

### 🔍 Logs Principais

```bash
# Conexões bancárias
tail -f backend/logs/banking.log

# Pagamentos e webhooks
tail -f backend/logs/payments.log

# Celery tasks
tail -f backend/logs/celery.log

# Erros gerais
tail -f backend/logs/django.log
```

### 🛠️ Comandos Úteis

```bash
# Health check Celery/Redis
curl /api/banking/health/celery/

# Reprocessar webhook falho
python manage.py retry_webhook <webhook_id>

# Sincronizar conta específica
python manage.py sync_account <account_id>

# Verificar status Stripe
python manage.py check_stripe_status
```

### 📋 Checklist de Troubleshooting

**Conexão Bancária**:
- [ ] Verificar status do item no Pluggy
- [ ] Conferir logs de MFA timeout
- [ ] Validar webhook signature
- [ ] Checar rate limits API

**Pagamentos**:
- [ ] Verificar webhook Stripe recebido
- [ ] Conferir signature validation
- [ ] Validar metadata no checkout
- [ ] Checar status da subscription

**Performance**:
- [ ] Monitorar queue Celery
- [ ] Verificar Redis connectivity
- [ ] Checar database locks
- [ ] Validar API response times

---

---

## 📋 RESUMO EXECUTIVO - DESCOBERTAS PRINCIPAIS

### ✅ **Pontos Fortes Identificados**

1. **Arquitetura Robusta**:
   - Separação clara entre conexões bancárias (Pluggy) e pagamentos (Stripe)
   - Processamento assíncrono via Celery para performance
   - Validação de planos e limites bem implementada
   - Criptografia adequada para dados sensíveis MFA

2. **Segurança em Pagamentos**:
   - Stripe com validação multicamadas (7 layers)
   - PCI DSS compliance automática
   - Distributed locks para race conditions
   - Audit trails completos

3. **Resiliência Operacional**:
   - Fallbacks para falhas de Celery/Redis
   - Retry logic inteligente para pagamentos
   - Graceful degradation em falhas de API
   - Health checks automatizados

### ⚠️ **Vulnerabilidades Críticas**

1. **Webhooks Pluggy Inseguros**:
   - **CRÍTICO**: Sem autenticação obrigatória
   - Aceita webhooks sem validação de secret
   - Logs expõem dados sensíveis
   - Implementar correções IMEDIATAMENTE

2. **Cobertura Incompleta de Webhooks**:
   - **43% de cobertura geral** (30/70+ eventos)
   - Stripe: 18/45+ eventos suportados  
   - Pluggy: 12/25+ eventos suportados
   - Eventos críticos como PIX payments não suportados

3. **Gaps Funcionais**:
   - Zero suporte a pagamentos PIX Pluggy
   - Eventos de fraud detection Stripe ausentes
   - Connector status updates perdidos
   - Payment intents require_action ignorados

### 🎯 **Impacto nos Usuários**

#### **Experiências Positivas**:
- ✅ Conexão bancária fluida (quando funciona)
- ✅ Checkout Stripe profissional
- ✅ MFA handling adequado
- ✅ Limites de plano claros
- ✅ Fallbacks para problemas técnicos

#### **Pontos de Friction**:
- ❌ MFA timeout de 60s muito curto
- ❌ Reconexão necessária após timeouts
- ❌ Sem feedback real-time de status
- ❌ Falhas silenciosas em webhooks PIX
- ❌ Retry manual necessário para sync

### 📊 **Métricas de Qualidade Atual**

| Aspecto | Score | Status |
|---------|-------|---------|
| **Segurança Pagamentos** | 8.5/10 | 🟢 Bom |
| **Segurança Webhooks** | 4.0/10 | 🔴 Crítico |
| **Cobertura Funcional** | 6.5/10 | 🟡 Médio |
| **Experiência do Usuário** | 7.0/10 | 🟡 Médio |
| **Resiliência Técnica** | 8.0/10 | 🟢 Bom |

### 🚀 **Recomendações Prioritárias**

#### **Urgente (Esta Semana)**:
1. **Securizar webhooks Pluggy**
2. **Implementar eventos Stripe críticos**
3. **Adicionar suporte PIX payments**
4. **Corrigir logs de dados sensíveis**

#### **Alto (2 Semanas)**:
1. **WebSocket para status real-time**
2. **Aumentar timeout MFA para 120s**
3. **Circuit breakers para APIs**
4. **Monitoring dashboard**

#### **Médio (1-2 Meses)**:
1. **ML para categorização automática**
2. **Fraud detection avançado**
3. **Multi-banco aggregation**
4. **Performance optimization**

### 💡 **Próximos Passos**

1. **Implementar correções de segurança** (webhooks Pluggy)
2. **Expandir cobertura de webhooks** (43% → 85%+)
3. **Melhorar experiência do usuário** (real-time updates)
4. **Adicionar monitoring robusto** (alertas proativos)
5. **Documentar runbooks operacionais** (troubleshooting)

---

*Esta documentação cobre todos os fluxos principais do sistema Finance Hub. Para atualizações e detalhes técnicos específicos, consulte o código-fonte e logs do sistema.*

**Última atualização**: Janeiro 2025  
**Revisão necessária**: Após implementação das correções críticas