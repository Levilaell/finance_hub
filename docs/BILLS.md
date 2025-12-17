# Sistema de Contas a Pagar/Receber (Bills)

Este documento explica como funciona o sistema de vinculação de contas (bills) com transações bancárias.

## Visão Geral

O sistema permite criar contas a pagar e receber e vinculá-las a transações bancárias reais quando os pagamentos são realizados.

```
┌─────────────────────────────────────────────────────────────┐
│                        BILL (Conta)                         │
│                                                             │
│  Aluguel - R$ 1.000,00                                     │
│  Status: partially_paid                                     │
│  Pago: R$ 400,00 | Restante: R$ 600,00                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Pagamentos:                                          │   │
│  │  • R$ 400,00 - PIX João Silva (vinculado)           │   │
│  │  • Adicionar pagamento...                            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Fluxo do Usuário

### 1. Criar uma Conta

```
[Contas a Pagar/Receber] → [+ Nova Conta]

Preencher:
- Tipo: A Pagar / A Receber
- Descrição: "Aluguel Janeiro"
- Valor: R$ 1.000,00
- Vencimento: 10/01/2025
- Categoria: Moradia (opcional)
```

### 2. Registrar Pagamentos

Existem duas formas de registrar pagamentos:

#### Opção A: Vincular Transação Existente

Quando o pagamento aparece no extrato bancário:

```
1. Acesse a conta criada
2. Clique em "Vincular Transação"
3. O sistema sugere transações compatíveis:
   - Mesmo tipo (conta a pagar → débito, conta a receber → crédito)
   - Valor menor ou igual ao restante
   - Ordenadas por relevância (data, descrição similar)
4. Selecione a transação
5. Pagamento registrado automaticamente
```

#### Opção B: Pagamento Manual

Para pagamentos em dinheiro ou não rastreados:

```
1. Acesse a conta
2. Clique em "Adicionar Pagamento"
3. Informe o valor pago
4. Adicione uma nota (opcional): "Pago em dinheiro"
5. Pagamento registrado
```

### 3. Pagamentos Parciais

O sistema suporta múltiplos pagamentos para uma única conta:

```
Conta: R$ 1.000,00 (Aluguel)
│
├── Pagamento 1: R$ 300,00 (PIX - 05/01)
│   Status: partially_paid (30%)
│
├── Pagamento 2: R$ 400,00 (TED - 08/01)
│   Status: partially_paid (70%)
│
└── Pagamento 3: R$ 300,00 (Dinheiro - 10/01)
    Status: paid (100%) ✓
```

### 4. Status das Contas

| Status | Descrição | Cor |
|--------|-----------|-----|
| `pending` | Nenhum pagamento registrado | Amarelo |
| `partially_paid` | Pagamento parcial realizado | Azul |
| `paid` | Totalmente paga | Verde |
| `cancelled` | Cancelada | Cinza |

## Exemplos Práticos

### Exemplo 1: Conta de Luz

```
1. Criar conta:
   - Tipo: A Pagar
   - Descrição: "Conta de Luz - Dezembro"
   - Valor: R$ 250,00
   - Vencimento: 15/01/2025

2. Quando pagar:
   - Acessar a conta
   - Clicar "Vincular Transação"
   - Selecionar o débito do pagamento
   - Conta marcada como paga ✓
```

### Exemplo 2: Recebimento de Cliente (Parcelado)

```
1. Criar conta:
   - Tipo: A Receber
   - Descrição: "Projeto Website - Cliente ABC"
   - Valor: R$ 5.000,00
   - Vencimento: 30/01/2025

2. Cliente paga 1ª parcela (R$ 2.000):
   - Vincular ao PIX recebido
   - Status: partially_paid (40%)

3. Cliente paga 2ª parcela (R$ 1.500):
   - Vincular ao TED recebido
   - Status: partially_paid (70%)

4. Cliente paga saldo (R$ 1.500):
   - Vincular ao crédito
   - Status: paid ✓
```

### Exemplo 3: Aluguel com Pagamento em Dinheiro

```
1. Criar conta:
   - Tipo: A Pagar
   - Descrição: "Aluguel Janeiro"
   - Valor: R$ 2.000,00

2. Pagar parte via PIX (R$ 1.500):
   - Vincular transação do extrato
   - Status: partially_paid

3. Pagar resto em dinheiro (R$ 500):
   - Adicionar Pagamento Manual
   - Informar valor: R$ 500
   - Nota: "Pago em espécie ao proprietário"
   - Status: paid ✓
```

## Regras de Vinculação

### Transações Elegíveis

Uma transação pode ser vinculada a uma conta se:

| Regra | Descrição |
|-------|-----------|
| Tipo compatível | Conta a Pagar → Débito / Conta a Receber → Crédito |
| Valor válido | Valor da transação ≤ Valor restante da conta |
| Não vinculada | Transação não está vinculada a outra conta |
| Mesmo usuário | Transação e conta pertencem ao mesmo usuário |

### Proteções do Sistema

- **Overpayment**: Não é possível adicionar pagamentos que excedam o valor restante
- **Concorrência**: Pagamentos simultâneos são serializados para evitar duplicação
- **Consistência**: Desvincular uma transação recalcula automaticamente o saldo

## Sugestões Inteligentes

O sistema ordena as transações sugeridas por relevância:

```
Relevância = Proximidade de Data (50pts)
           + Descrição Similar (30pts)
           + Mesma Categoria (20pts)
```

| Proximidade | Pontos |
|-------------|--------|
| Mesmo dia | 50 |
| 1-3 dias | 40 |
| 4-7 dias | 30 |
| 8-15 dias | 20 |
| 16-30 dias | 10 |

## API Endpoints (Referência)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/banking/bills/` | Listar contas |
| POST | `/api/banking/bills/` | Criar conta |
| GET | `/api/banking/bills/{id}/payments/` | Listar pagamentos |
| POST | `/api/banking/bills/{id}/add_payment/` | Adicionar pagamento |
| DELETE | `/api/banking/bills/{id}/payments/{pid}/` | Remover pagamento |
| GET | `/api/banking/bills/{id}/suggested_transactions_partial/` | Sugestões de transações |

## Dúvidas Frequentes

### Posso vincular a mesma transação a duas contas?
Não. Cada transação só pode estar vinculada a uma conta.

### O que acontece se eu desvincular um pagamento?
A conta é recalculada automaticamente. Se tinha outros pagamentos, eles são mantidos.

### Posso editar o valor de um pagamento?
Não diretamente. Remova o pagamento e adicione um novo com o valor correto.

### Contas recorrentes são criadas automaticamente?
Não na versão atual. Cada conta deve ser criada manualmente.
