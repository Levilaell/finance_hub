# Vinculação de Transações a Contas (Transaction-Bill Linking)

## Sumário
- [Visão Geral](#visão-geral)
- [Comparação: Planejamento vs Implementação](#comparação-planejamento-vs-implementação)
- [Arquitetura](#arquitetura)
- [Backend](#backend)
- [Frontend](#frontend)
- [Fluxos de Uso](#fluxos-de-uso)
- [API Reference](#api-reference)
- [Próximos Passos](#próximos-passos)

---

## Visão Geral

Esta funcionalidade permite vincular transações bancárias extraídas automaticamente via Open Banking (Pluggy) a contas a pagar/receber (Bills), marcando-as automaticamente como pagas quando vinculadas.

### Características Principais
- **Vinculação 1:1**: Uma transação só pode estar vinculada a uma única conta
- **Auto-match inteligente**: Vinculação automática quando há única correspondência
- **Sugestões ranqueadas**: Sistema de relevância para ordenar sugestões
- **Configuração por usuário**: Toggle para ativar/desativar auto-match

---

## Comparação: Planejamento vs Implementação

### Regras de Negócio

| Requisito | Planejado | Implementado | Status |
|-----------|-----------|--------------|--------|
| Cardinalidade 1:1 (Transaction ↔ Bill) | OneToOneField | OneToOneField em `Bill.linked_transaction` | ✅ |
| Match por valor exato | Sim | Sim, via `get_eligible_bills_for_transaction()` | ✅ |
| Apenas bills "virgens" podem ser vinculadas | status='pending', amount_paid=0 | Validação completa no service | ✅ |
| Desvincular reverte para 'pending' | Sim | `unlink_transaction_from_bill()` zera amount_paid e status | ✅ |
| Configuração de auto-match por usuário | UserSettings.auto_match_transactions | Implementado com default=True | ✅ |
| Compatibilidade de tipos | CREDIT↔receivable, DEBIT↔payable | Validação em todos os métodos | ✅ |

### Sistema de Sugestões

| Requisito | Planejado | Implementado | Status |
|-----------|-----------|--------------|--------|
| Sugestões ordenadas por relevância | Score 0-100 | `calculate_relevance_score()` | ✅ |
| Proximidade de data (peso maior) | 50 pontos | Até 50 pontos (mesmo dia=50, 3 dias=40, etc.) | ✅ |
| Similaridade de descrição | 30 pontos | Até 30 pontos (10/palavra comum) | ✅ |
| Mesma categoria | 20 pontos | 20 pontos bonus | ✅ |
| Remoção de stopwords | Sim | Lista: de, da, do, para, a, o, e, em, com, por | ✅ |

### Auto-Match

| Requisito | Planejado | Implementado | Status |
|-----------|-----------|--------------|--------|
| Auto-match durante sync | Sim | Chamado em `sync_transactions()` | ✅ |
| Só vincula se única correspondência | Sim | Verifica `len(eligible_bills) == 1` | ✅ |
| Reporta correspondências ambíguas | Sim | Retorna lista 'ambiguous' | ✅ |
| Respeita configuração do usuário | Sim | Verifica `auto_match_transactions` | ✅ |

### Endpoints Backend

| Endpoint | Planejado | Implementado | Status |
|----------|-----------|--------------|--------|
| GET bills/{id}/suggested_transactions/ | Sim | BillViewSet | ✅ |
| POST bills/{id}/link_transaction/ | Sim | BillViewSet | ✅ |
| POST bills/{id}/unlink_transaction/ | Sim | BillViewSet | ✅ |
| GET transactions/{id}/suggested_bills/ | Sim | TransactionViewSet | ✅ |
| POST transactions/{id}/link_bill/ | Sim | TransactionViewSet | ✅ |
| GET/PATCH auth/settings/ | Sim | user_settings_view | ✅ |

### Frontend

| Componente | Planejado | Implementado | Status |
|------------|-----------|--------------|--------|
| LinkTransactionDialog | Sim | `components/banking/LinkTransactionDialog.tsx` | ✅ |
| LinkBillDialog | Sim | `components/banking/LinkBillDialog.tsx` | ✅ |
| Badge "Vinculada" em Bills | Sim | Com tooltip mostrando detalhes | ✅ |
| Badge "Vinculada" em Transactions | Sim | Nova coluna "Vínculo" na tabela | ✅ |
| Botão vincular em Bills | Sim | Ícone de link para bills pendentes | ✅ |
| Botão vincular em Transactions | Sim | Ícone de link na coluna Vínculo | ✅ |
| Botão desvincular em Bills | Sim | Ícone de unlink com confirmação | ✅ |
| Aba Automação em Settings | Sim | Toggle auto_match_transactions | ✅ |
| Services atualizados | Sim | banking.service.ts, bills.service.ts, settings.service.ts | ✅ |
| Types atualizados | Sim | banking.ts com novos interfaces | ✅ |

---

## Arquitetura

### Diagrama de Relacionamento

```
┌─────────────────┐         ┌─────────────────┐
│   Transaction   │         │      Bill       │
├─────────────────┤         ├─────────────────┤
│ id              │◄───────►│ id              │
│ description     │   1:1   │ description     │
│ amount          │         │ amount          │
│ date            │         │ due_date        │
│ type (CREDIT/   │         │ type (receivable│
│       DEBIT)    │         │       /payable) │
│ user_id         │         │ linked_trans_id │
│                 │         │ status          │
│                 │         │ amount_paid     │
└─────────────────┘         └─────────────────┘
        │                           │
        └───────────┬───────────────┘
                    │
            ┌───────▼───────┐
            │ UserSettings  │
            ├───────────────┤
            │ user_id (PK)  │
            │ auto_match_   │
            │  transactions │
            └───────────────┘
```

### Fluxo de Dados

```
Sync de Transações (Pluggy)
         │
         ▼
┌─────────────────────────────┐
│  TransactionService.sync()  │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ TransactionMatchService.auto_match()│
└─────────────────────────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌────────┐
│ 0 bill│ │ 1 bill │ ──► Auto-vincula
└───────┘ └────────┘
    │         │
    ▼         ▼
┌───────┐ ┌────────────┐
│Ignora │ │ >1 bills   │ ──► Lista "ambígua" (usuário decide)
└───────┘ └────────────┘
```

---

## Backend

### Models

#### Bill (banking/models.py)
```python
class Bill(models.Model):
    linked_transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_bill'  # Acesso reverso: transaction.linked_bill
    )
    # ... outros campos
```

#### UserSettings (authentication/models.py)
```python
class UserSettings(models.Model):
    user = models.OneToOneField(User, primary_key=True, related_name='settings')
    auto_match_transactions = models.BooleanField(default=True)

    @classmethod
    def get_or_create_for_user(cls, user):
        settings, _ = cls.objects.get_or_create(user=user)
        return settings
```

### TransactionMatchService (banking/services.py)

Serviço principal para vinculação de transações.

#### Métodos Principais

| Método | Descrição |
|--------|-----------|
| `get_eligible_bills_for_transaction(transaction)` | Retorna bills elegíveis para vinculação |
| `get_eligible_transactions_for_bill(bill)` | Retorna transações elegíveis para vinculação |
| `calculate_relevance_score(transaction, bill)` | Calcula score de relevância (0-100) |
| `get_suggested_transactions_for_bill(bill)` | Retorna sugestões ranqueadas |
| `get_suggested_bills_for_transaction(transaction)` | Retorna sugestões ranqueadas |
| `link_transaction_to_bill(transaction, bill)` | Vincula e marca como pago |
| `unlink_transaction_from_bill(bill)` | Desvincula e reverte para pendente |
| `auto_match_transactions(user, transactions)` | Auto-match para lista de transações |

#### Critérios de Elegibilidade

**Para Bills:**
- Mesmo usuário
- Status = 'pending'
- amount_paid = 0 (sem pagamento parcial)
- Sem linked_transaction
- Valor exato igual
- Tipo compatível (CREDIT→receivable, DEBIT→payable)

**Para Transações:**
- Mesmo usuário
- Sem linked_bill
- Valor exato igual
- Tipo compatível

#### Algoritmo de Relevância

```python
def calculate_relevance_score(transaction, bill):
    score = 0

    # Proximidade de data (até 50 pontos)
    days_diff = abs((transaction.date.date() - bill.due_date).days)
    if days_diff == 0:     score += 50
    elif days_diff <= 3:   score += 40
    elif days_diff <= 7:   score += 30
    elif days_diff <= 15:  score += 20
    elif days_diff <= 30:  score += 10

    # Similaridade de descrição (até 30 pontos)
    trans_words = normalize(transaction.description + merchant_name)
    bill_words = normalize(bill.description + customer_supplier)
    common = trans_words & bill_words - STOPWORDS
    score += min(len(common) * 10, 30)

    # Mesma categoria (20 pontos)
    if transaction.category == bill.category:
        score += 20

    return score
```

### Migrations

| Migration | Descrição |
|-----------|-----------|
| `0010_bill.py` | Criação inicial do model Bill |
| `0011_change_linked_transaction_to_onetoone.py` | Altera ForeignKey para OneToOneField |
| `0005_add_user_settings.py` | Criação do model UserSettings |

---

## Frontend

### Componentes Criados

#### LinkTransactionDialog.tsx
```typescript
interface LinkTransactionDialogProps {
  bill: Bill | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onLinked: () => void;
}
```
- Exibe informações da conta (bill)
- Lista transações sugeridas com score de relevância
- Badges coloridos por nível de relevância (Alta/Média/Baixa)
- Botão "Vincular" para cada sugestão

#### LinkBillDialog.tsx
```typescript
interface LinkBillDialogProps {
  transaction: Transaction | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onLinked: () => void;
}
```
- Exibe informações da transação
- Lista contas sugeridas com score de relevância
- Badge de tipo (A Pagar/A Receber)
- Botão "Vincular" para cada sugestão

### Services Atualizados

#### bills.service.ts
```typescript
class BillsService {
  async getSuggestedTransactions(billId: string): Promise<TransactionSuggestion[]>
  async linkTransaction(billId: string, transactionId: string): Promise<Bill>
  async unlinkTransaction(billId: string): Promise<Bill>
}
```

#### banking.service.ts
```typescript
class BankingService {
  async getSuggestedBills(transactionId: string): Promise<BillSuggestion[]>
  async linkBill(transactionId: string, billId: string): Promise<Transaction>
}
```

#### settings.service.ts (novo)
```typescript
class SettingsService {
  async getSettings(): Promise<UserSettings>
  async updateSettings(data: Partial<UserSettings>): Promise<UserSettings>
}
```

### Types Adicionados (banking.ts)

```typescript
// Resumo de transação vinculada (embedded em Bill)
interface LinkedTransactionSummary {
  id: string;
  description: string;
  amount: string;
  date: string;
  account_name?: string;
}

// Resumo de conta vinculada (embedded em Transaction)
interface LinkedBillSummary {
  id: string;
  description: string;
  amount: string;
  due_date: string;
  type: BillType;
}

// Sugestão de transação para vinculação
interface TransactionSuggestion {
  id: string;
  description: string;
  amount: number;
  date: string;
  type: TransactionType;
  account_name: string;
  merchant_name?: string;
  relevance_score: number;
}

// Sugestão de conta para vinculação
interface BillSuggestion {
  id: string;
  description: string;
  amount: number;
  due_date: string;
  type: BillType;
  customer_supplier?: string;
  category_name?: string;
  category_icon?: string;
  relevance_score: number;
}

// Configurações do usuário
interface UserSettings {
  auto_match_transactions: boolean;
}
```

### Páginas Atualizadas

#### bills/page.tsx
- Badge "Vinculada" com tooltip (detalhes da transação)
- Botão de vincular (🔗) para bills pendentes sem vínculo
- Botão de desvincular (↗️) para bills vinculadas
- Botão "Registrar" oculto quando há vínculo
- Integração com LinkTransactionDialog

#### transactions/page.tsx
- Nova coluna "Vínculo" na tabela
- Badge "Vinculada" com tooltip (detalhes da conta)
- Botão de vincular (🔗) para transações sem vínculo
- Integração com LinkBillDialog

#### settings/page.tsx
- Nova aba "Automação"
- Toggle "Vinculação Automática de Transações"
- Descrição explicativa do funcionamento
- Dica sobre como desvincular manualmente

---

## Fluxos de Uso

### Fluxo 1: Vinculação Manual via Bills

```
1. Usuário acessa /bills
2. Localiza conta pendente sem vínculo
3. Clica no ícone de link (🔗)
4. Dialog abre com sugestões de transações
5. Seleciona uma transação e clica "Vincular"
6. Conta é marcada como paga automaticamente
7. Badge "Vinculada" aparece na conta
```

### Fluxo 2: Vinculação Manual via Transactions

```
1. Usuário acessa /transactions
2. Localiza transação sem vínculo na coluna "Vínculo"
3. Clica no ícone de link (🔗)
4. Dialog abre com sugestões de contas
5. Seleciona uma conta e clica "Vincular"
6. Conta é marcada como paga automaticamente
7. Badge "Vinculada" aparece na transação
```

### Fluxo 3: Vinculação Automática

```
1. Sistema sincroniza transações via Pluggy
2. Para cada nova transação:
   a. Busca contas elegíveis (mesmo valor, tipo compatível)
   b. Se encontrar exatamente 1 conta → vincula automaticamente
   c. Se encontrar 0 ou >1 → não vincula (usuário decide)
3. Usuário vê transações já vinculadas ao acessar páginas
```

### Fluxo 4: Desvinculação

```
1. Usuário acessa /bills
2. Localiza conta vinculada (badge "Vinculada")
3. Clica no botão de desvincular (↗️)
4. Confirma no dialog de confirmação
5. Conta volta para status "pendente"
6. Transação fica livre para nova vinculação
```

### Fluxo 5: Configurar Auto-Match

```
1. Usuário acessa /settings
2. Clica na aba "Automação"
3. Toggle "Vinculação Automática de Transações"
   - ON: Novas transações serão auto-vinculadas
   - OFF: Todas vinculações são manuais
4. Configuração salva automaticamente
```

---

## API Reference

### Bills Endpoints

#### GET /api/banking/bills/{id}/suggested_transactions/
Retorna transações sugeridas para vincular a uma conta.

**Response:**
```json
[
  {
    "id": "uuid",
    "description": "PIX Recebido",
    "amount": 1500.00,
    "date": "2024-01-15",
    "type": "CREDIT",
    "account_name": "Conta Corrente",
    "merchant_name": "João Silva",
    "relevance_score": 85
  }
]
```

#### POST /api/banking/bills/{id}/link_transaction/
Vincula uma transação a uma conta.

**Request:**
```json
{
  "transaction_id": "uuid"
}
```

**Response:** Bill atualizada

#### POST /api/banking/bills/{id}/unlink_transaction/
Desvincula a transação de uma conta.

**Response:** Bill atualizada (status='pending', amount_paid=0)

### Transactions Endpoints

#### GET /api/banking/transactions/{id}/suggested_bills/
Retorna contas sugeridas para vincular a uma transação.

**Response:**
```json
[
  {
    "id": "uuid",
    "description": "Aluguel Janeiro",
    "amount": 2000.00,
    "due_date": "2024-01-10",
    "type": "payable",
    "customer_supplier": "Imobiliária XYZ",
    "category_name": "Moradia",
    "category_icon": "🏠",
    "relevance_score": 92
  }
]
```

#### POST /api/banking/transactions/{id}/link_bill/
Vincula uma conta a uma transação.

**Request:**
```json
{
  "bill_id": "uuid"
}
```

**Response:** Transaction atualizada

### Settings Endpoints

#### GET /api/auth/settings/
Retorna configurações do usuário.

**Response:**
```json
{
  "auto_match_transactions": true
}
```

#### PATCH /api/auth/settings/
Atualiza configurações do usuário.

**Request:**
```json
{
  "auto_match_transactions": false
}
```

---

## Próximos Passos

### Pendências para Deploy

1. **Aplicar Migrations**
   ```bash
   cd backend
   python manage.py migrate
   ```

2. **Testar Fluxo Completo**
   - Criar bills de teste
   - Sincronizar transações
   - Verificar auto-match
   - Testar vinculação/desvinculação manual

### Melhorias Futuras

1. **Notificações de Auto-Match**
   - Toast/notification quando transações são auto-vinculadas
   - Resumo de matches após sync

2. **Vinculação em Lote**
   - Permitir vincular múltiplas transações de uma vez
   - Resolver ambiguidades em bulk

3. **Regras de Match Customizáveis**
   - Permitir tolerância de valor (ex: ±5%)
   - Configurar pesos do algoritmo de relevância

4. **Histórico de Vinculações**
   - Log de quando/como cada vinculação foi feita
   - Auditoria de auto-matches

5. **Match por Descrição**
   - Aprender padrões de descrição
   - Sugerir baseado em histórico de vinculações

---

## Arquivos Modificados/Criados

### Backend
| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `apps/banking/models.py` | Modificado | Bill.linked_transaction → OneToOneField |
| `apps/banking/migrations/0011_*.py` | Criado | Migration OneToOneField |
| `apps/authentication/models.py` | Modificado | UserSettings model |
| `apps/authentication/migrations/0005_*.py` | Criado | Migration UserSettings |
| `apps/banking/services.py` | Modificado | TransactionMatchService |
| `apps/banking/serializers.py` | Modificado | Linking serializers |
| `apps/banking/views.py` | Modificado | Linking endpoints |
| `apps/authentication/views.py` | Modificado | user_settings_view |
| `apps/authentication/urls.py` | Modificado | Settings URL |

### Frontend
| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `components/banking/LinkTransactionDialog.tsx` | Criado | Dialog para vincular transação |
| `components/banking/LinkBillDialog.tsx` | Criado | Dialog para vincular conta |
| `components/banking/index.ts` | Modificado | Exportar novos componentes |
| `services/settings.service.ts` | Criado | Service de configurações |
| `services/bills.service.ts` | Modificado | Métodos de vinculação |
| `services/banking.service.ts` | Modificado | Métodos de vinculação |
| `types/banking.ts` | Modificado | Novos tipos |
| `app/(dashboard)/bills/page.tsx` | Modificado | UI de vinculação |
| `app/(dashboard)/transactions/page.tsx` | Modificado | Coluna e UI de vinculação |
| `app/(dashboard)/settings/page.tsx` | Modificado | Aba Automação |

---

*Documentação gerada em: Dezembro 2024*
*Versão: 1.0*
