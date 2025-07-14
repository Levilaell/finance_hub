# Relatório de Inconsistências entre Modelos Django e Interfaces TypeScript

## Resumo Executivo

Este relatório identifica as inconsistências entre os modelos Django (backend) e as interfaces TypeScript (frontend) do sistema de gestão financeira. As inconsistências foram categorizadas por gravidade: **Crítica**, **Alta**, **Média** e **Baixa**.

## 1. MODELO USER

### Inconsistências Críticas
1. **Campos ausentes no TypeScript:**
   - `username` (campo obrigatório no Django)
   - `phone` 
   - `is_email_verified`
   - `is_phone_verified`
   - `avatar`
   - `date_of_birth`
   - `last_login_ip`
   - `preferred_language`
   - `timezone`
   - `two_factor_secret`
   - `backup_codes`
   - `payment_customer_id`
   - `payment_gateway`

2. **Tipo de campo incompatível:**
   - Django: `id` é um IntegerField (implícito)
   - TypeScript: `id` é string

3. **Campo adicional no TypeScript:**
   - `role` ("owner" | "admin" | "member") - não existe no modelo Django User

### Recomendações:
- Adicionar campos faltantes na interface TypeScript
- Criar uma interface separada `UserProfile` com campos adicionais
- Mover o campo `role` para o modelo `CompanyUser` onde pertence

## 2. MODELO COMPANY

### Inconsistências Críticas
1. **Campos ausentes no TypeScript:**
   - Endereço completo (address_street, address_number, etc.)
   - `email`, `phone`, `website`
   - `monthly_revenue`
   - `employee_count`
   - `subscription_id`
   - `last_usage_reset`
   - `notified_80_percent`, `notified_90_percent`
   - Configurações da empresa (logo, primary_color, currency, etc.)
   - Preferências de IA (enable_ai_categorization, auto_categorize_threshold, etc.)
   - `is_active`

2. **Tipo de campo incompatível:**
   - Django: `id` é um IntegerField (implícito)
   - TypeScript: `id` é string

### Recomendações:
- Criar interface `CompanyDetails` com informações completas
- Adicionar campos de configuração e preferências
- Padronizar tipos de ID

## 3. MODELO SUBSCRIPTIONPLAN

### Inconsistências Altas
1. **Campos ausentes no TypeScript:**
   - `stripe_price_id`
   - `mercadopago_plan_id`
   - `gateway_plan_id`
   - `display_order`
   - `is_active`
   - `created_at`, `updated_at`

2. **Campo adicional no TypeScript:**
   - `yearly_discount` - calculado no Django via método, não campo

### Recomendações:
- Adicionar campos de gateway de pagamento
- Remover `yearly_discount` ou marcá-lo como campo calculado

## 4. MODELO BANKACCOUNT

### Inconsistências Críticas
1. **Estrutura completamente diferente:**
   - Django: `BankAccount` com relação para `BankProvider`
   - TypeScript: Múltiplas interfaces (`Account`, `BankAccount`) com estruturas diferentes

2. **Campos ausentes no TypeScript:**
   - `agency`, `account_digit`
   - `external_id`, `pluggy_item_id`
   - Tokens criptografados
   - `sync_frequency`
   - `nickname`
   - `is_primary`

3. **Campos com nomes diferentes:**
   - Django: `bank_provider` (ForeignKey)
   - TypeScript: `provider` (objeto)

4. **Tipos de account_type diferentes:**
   - Django: inclui "business", "digital"
   - TypeScript: inclui "investment"

### Recomendações:
- Unificar as interfaces `Account` e `BankAccount`
- Adicionar campos de integração bancária
- Alinhar tipos de conta

## 5. MODELO TRANSACTION

### Inconsistências Críticas
1. **Nome do modelo diferente:**
   - Django: `Transaction`
   - TypeScript: `BankTransaction`

2. **Campos ausentes no TypeScript:**
   - `counterpart_name`, `counterpart_document`, `counterpart_bank`, etc.
   - `subcategory`
   - `ai_suggested_category`
   - `is_manually_reviewed`
   - `reference_number`
   - `pix_key`
   - `balance_after`
   - Campos de reconciliação

3. **Tipos de transação diferentes:**
   - Django: Tipos mais detalhados (transfer_in, transfer_out, pix_in, pix_out, etc.)
   - TypeScript: Apenas "debit" | "credit"

4. **Campos com nomes diferentes:**
   - Django: `ai_category_confidence`
   - TypeScript: `ai_confidence`

### Recomendações:
- Renomear interface para `Transaction`
- Adicionar tipos de transação detalhados
- Incluir campos de contrapartida e reconciliação

## 6. MODELO TRANSACTIONCATEGORY

### Inconsistências Altas
1. **Campos ausentes no TypeScript:**
   - `keywords`
   - `confidence_threshold`
   - `order`

2. **Tipo de campo incompatível:**
   - Django: `parent` é ForeignKey (self)
   - TypeScript: `parent` é number | null

3. **Valores de category_type diferentes:**
   - Django: "income", "expense", "transfer"
   - TypeScript: "income", "expense", "both" (em alguns lugares)

### Recomendações:
- Adicionar campos de IA
- Padronizar tipos de categoria
- Corrigir tipo do campo parent

## 7. MODELO REPORT

### Inconsistências Médias
1. **Campos ausentes no TypeScript:**
   - `company` (relação)
   - `description` (duplicado nas interfaces)

2. **Interface duplicada:**
   - `Report` aparece duas vezes no arquivo TypeScript

### Recomendações:
- Remover duplicação de interface
- Adicionar relação com company

## 8. MODELO NOTIFICATION

### Inconsistências Altas
1. **Campos ausentes no TypeScript:**
   - `user`, `company` (relações)
   - `template`
   - `notification_type` (mais detalhado no Django)
   - `data`
   - `priority`
   - `read_at`
   - Campos de status de envio (email_sent, push_sent, etc.)
   - `expires_at`

2. **Campos com tipos diferentes:**
   - Django: `type` não existe, usa `notification_type`
   - TypeScript: `type` e `category` separados

### Recomendações:
- Alinhar estrutura de notificações
- Adicionar campos de rastreamento de entrega
- Incluir prioridade e expiração

## 9. MODELOS AUSENTES NO TYPESCRIPT

### Crítico - Modelos completamente ausentes:
1. **CompanyUser** - Gestão de usuários múltiplos
2. **PaymentMethod** - Métodos de pagamento
3. **PaymentHistory** - Histórico de pagamentos
4. **BankProvider** - Provedores bancários
5. **RecurringTransaction** - Transações recorrentes
6. **Budget** - Orçamentos
7. **FinancialGoal** - Metas financeiras
8. **BankSync** - Logs de sincronização
9. **CategoryRule** - Regras de categorização
10. **AITrainingData** - Dados de treinamento IA
11. **CategorySuggestion** - Sugestões de categoria
12. **CategoryPerformance** - Performance de categorização
13. **NotificationTemplate** - Templates de notificação
14. **NotificationPreference** - Preferências de notificação
15. **ReportSchedule** - Agendamento de relatórios
16. **ReportTemplate** - Templates de relatórios

### Recomendações:
- Criar interfaces TypeScript para todos os modelos ausentes
- Priorizar modelos críticos para funcionalidades principais

## 10. INTERFACES TYPESCRIPT SEM MODELOS DJANGO

### Interfaces auxiliares (não crítico):
1. **LoginCredentials**, **RegisterData**, **AuthTokens** - DTOs de autenticação
2. **DashboardStats**, **CashFlowData**, **CategorySpending** - Agregações
3. **PaginatedResponse**, **ApiError** - Tipos de resposta
4. **Formulários** (BankAccountForm, CategoryForm, etc.) - DTOs de entrada
5. **AIInsights** e relacionados - Estruturas de resposta de IA

## PRIORIZAÇÃO DE CORREÇÕES

### CRÍTICAS (Corrigir imediatamente):
1. Padronizar tipos de ID (int vs string)
2. Adicionar campos obrigatórios do User no TypeScript
3. Criar interfaces para modelos de pagamento
4. Alinhar estrutura de BankAccount
5. Corrigir tipos de transação

### ALTAS (Corrigir em 1-2 sprints):
1. Adicionar modelos de gestão financeira (Budget, Goals)
2. Implementar interfaces de categorização com IA
3. Alinhar campos de Company
4. Corrigir estrutura de Notification

### MÉDIAS (Corrigir em 3-4 sprints):
1. Adicionar campos de configuração e preferências
2. Implementar interfaces de relatórios avançados
3. Criar tipos para logs e auditoria

### BAIXAS (Melhorias futuras):
1. Adicionar campos calculados como propriedades
2. Documentar DTOs vs Modelos
3. Criar tipos utilitários compartilhados

## RECOMENDAÇÕES GERAIS

1. **Geração Automática**: Implementar geração automática de tipos TypeScript a partir dos modelos Django usando ferramentas como `django-typescript`

2. **Versionamento de API**: Implementar versionamento para permitir mudanças graduais

3. **Documentação**: Criar documentação clara sobre mapeamento entre modelos e interfaces

4. **Testes de Tipo**: Implementar testes que validem a consistência entre backend e frontend

5. **Padrões de Nomenclatura**: Estabelecer convenções claras para nomes de campos e tipos