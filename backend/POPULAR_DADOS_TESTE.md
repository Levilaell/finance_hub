# Como Popular Conta com Transações de Teste

Este guia mostra como alimentar uma conta em produção com transações irreais/de teste.

## Script Criado

Foi criado o comando Django: `populate_test_transactions.py`

**Localização:** `backend/apps/banking/management/commands/populate_test_transactions.py`

## Características das Transações Geradas

### Categorias e Frequências

O script cria transações realistas baseadas em templates com as seguintes categorias:

#### Despesas (DEBIT)
- **Food & Dining** (20%): Restaurantes, pizzarias, cafés, etc.
- **Groceries** (15%): Supermercados, hortifruti, empórios
- **Transportation** (15%): Uber, postos, estacionamento
- **Shopping** (10%): Magazine Luiza, Amazon, Mercado Livre
- **Bills & Utilities** (8%): Energia, água, internet, condomínio
- **Entertainment** (8%): Cinema, Spotify, Netflix, bares
- **Healthcare** (5%): Farmácias, clínicas, academia
- **Subscriptions** (5%): Netflix, Spotify, Amazon Prime
- **Other Expenses** (6%): Diversos

#### Receitas (CREDIT)
- **Salary** (3%): Salário mensal
- **Freelance** (3%): Trabalhos freelance
- **Investments** (2%): Dividendos, rendimentos

### Valores Realistas

Cada categoria tem uma faixa de valores:
- Alimentação: R$ 15 - R$ 150
- Supermercado: R$ 50 - R$ 350
- Transporte: R$ 10 - R$ 200
- Compras: R$ 50 - R$ 500
- Contas: R$ 80 - R$ 450
- Salário: R$ 3.000 - R$ 8.000
- Freelance: R$ 500 - R$ 2.500

### Dados Incluídos em Cada Transação

- ✅ ID único (formato: `test_tx_XXXXXXXXXXXXXXXX`)
- ✅ Tipo (DEBIT/CREDIT)
- ✅ Descrição realista (nome do estabelecimento)
- ✅ Valor aleatório dentro da faixa
- ✅ Data/hora aleatória no período especificado
- ✅ Categoria do Pluggy
- ✅ Categoria do usuário (vinculada automaticamente)
- ✅ Nome do estabelecimento (merchant)
- ✅ Moeda (BRL)

## Como Usar

### 1. Opção 1: Popular por ID da Conta

```bash
cd backend

# Criar 100 transações dos últimos 90 dias
python manage.py populate_test_transactions --account-id UUID_DA_CONTA

# Criar 200 transações dos últimos 180 dias
python manage.py populate_test_transactions --account-id UUID_DA_CONTA --count 200 --days-back 180

# Limpar transações de teste existentes antes de criar novas
python manage.py populate_test_transactions --account-id UUID_DA_CONTA --clear-existing
```

### 2. Opção 2: Popular por Email do Usuário

```bash
cd backend

# O script usará a primeira conta ativa do usuário
python manage.py populate_test_transactions --user-email usuario@example.com

# Com mais opções
python manage.py populate_test_transactions \
  --user-email usuario@example.com \
  --count 150 \
  --days-back 120 \
  --clear-existing
```

### 3. Como Descobrir o ID da Conta

#### Via Django Shell:
```bash
cd backend
python manage.py shell
```

```python
from apps.banking.models import BankAccount

# Listar todas as contas
for account in BankAccount.objects.all():
    print(f"ID: {account.id}")
    print(f"Nome: {account.name}")
    print(f"Tipo: {account.type}")
    print(f"Usuário: {account.connection.user.email}")
    print("-" * 50)

# Ou buscar por email
from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.get(email='usuario@example.com')
accounts = BankAccount.objects.filter(connection__user=user, is_active=True)

for account in accounts:
    print(f"ID: {account.id} | Nome: {account.name}")
```

#### Via API (se tiver acesso):
```bash
# GET /api/banking/accounts/
# Pegar o campo "id" da conta desejada
```

## Parâmetros Disponíveis

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `--account-id` | UUID | - | ID da conta bancária (obrigatório se não usar --user-email) |
| `--user-email` | String | - | Email do usuário (usa primeira conta ativa) |
| `--count` | Integer | 100 | Quantidade de transações a criar |
| `--days-back` | Integer | 90 | Criar transações dos últimos N dias |
| `--clear-existing` | Flag | False | Deletar transações de teste existentes antes |

## Exemplos Práticos

### Exemplo 1: Popular conta nova com 3 meses de histórico
```bash
python manage.py populate_test_transactions \
  --user-email joao@example.com \
  --count 150 \
  --days-back 90
```

### Exemplo 2: Popular com 6 meses de histórico detalhado
```bash
python manage.py populate_test_transactions \
  --account-id a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6 \
  --count 300 \
  --days-back 180
```

### Exemplo 3: Resetar e criar novos dados de teste
```bash
python manage.py populate_test_transactions \
  --user-email maria@example.com \
  --count 200 \
  --clear-existing
```

## Saída Esperada

```
Target Account: Minha Conta Corrente (CHECKING)
User: usuario@example.com
Transactions to create: 100
Date range: 90 days back

Checking categories...
  + Created category: Food & Dining
  + Created category: Groceries
  ...

Creating 100 test transactions...

  Created 10/100 transactions...
  Created 20/100 transactions...
  ...
  Created 100/100 transactions...

Successfully created 100 test transactions!

==================================================
SUMMARY
==================================================
Total Test Transactions: 100
Total Income: R$ 12,450.00
Total Expenses: R$ 8,732.50
Net Balance: R$ 3,717.50
==================================================
```

## Identificando Transações de Teste

Todas as transações criadas pelo script têm:
- `pluggy_transaction_id` começando com `test_tx_`
- Podem ser facilmente deletadas depois:

```python
# Django Shell
from apps.banking.models import Transaction

# Deletar todas as transações de teste de uma conta
Transaction.objects.filter(
    account_id='UUID_DA_CONTA',
    pluggy_transaction_id__startswith='test_tx_'
).delete()

# Ou de todas as contas
Transaction.objects.filter(
    pluggy_transaction_id__startswith='test_tx_'
).delete()
```

## Garantindo Categorias

O script automaticamente cria todas as categorias necessárias para o usuário. Se preferir criar as categorias manualmente primeiro:

```bash
# Criar categorias padrão para um usuário específico
python manage.py create_default_categories --user-id 1

# Criar para todos os usuários
python manage.py create_default_categories --all-users
```

## Considerações de Segurança

⚠️ **IMPORTANTE:**
- Este script é para **ambientes de desenvolvimento/teste**
- As transações são marcadas com `test_tx_` para fácil identificação
- Em produção, use com cuidado e apenas em contas de teste
- Sempre use `--clear-existing` se quiser resetar os dados

## Verificando os Resultados

### Via API:
```bash
# Listar transações
GET /api/banking/transactions/?account_id=UUID_DA_CONTA

# Ver resumo financeiro
GET /api/banking/transactions/summary/?date_from=2024-01-01&date_to=2024-12-31
```

### Via Django Shell:
```python
from apps.banking.models import Transaction
from django.db.models import Sum

account_id = 'UUID_DA_CONTA'

# Contar transações de teste
test_count = Transaction.objects.filter(
    account_id=account_id,
    pluggy_transaction_id__startswith='test_tx_'
).count()

print(f"Total de transações de teste: {test_count}")

# Ver resumo
transactions = Transaction.objects.filter(account_id=account_id)
income = transactions.filter(type='CREDIT').aggregate(Sum('amount'))['amount__sum'] or 0
expenses = transactions.filter(type='DEBIT').aggregate(Sum('amount'))['amount__sum'] or 0

print(f"Receitas: R$ {income:,.2f}")
print(f"Despesas: R$ {expenses:,.2f}")
print(f"Saldo: R$ {income - expenses:,.2f}")
```

## Próximos Passos

Após popular os dados, você pode:
1. Testar a visualização de transações na interface
2. Testar filtros por categoria, período, tipo
3. Testar o resumo financeiro (dashboard)
4. Testar a atualização de categorias
5. Testar exportação de dados (se implementado)

## Troubleshooting

### Erro: "No active bank account found"
**Solução:** Certifique-se de que o usuário tem pelo menos uma conta ativa:
```python
from apps.banking.models import BankAccount
BankAccount.objects.filter(connection__user__email='usuario@example.com', is_active=True)
```

### Erro: "Category not found"
**Solução:** Execute primeiro o comando de criar categorias:
```bash
python manage.py create_default_categories --user-email usuario@example.com
```

### Transações não aparecem no frontend
**Solução:** Verifique:
1. As transações foram criadas para a conta correta
2. O usuário está autenticado
3. A conta está ativa (`is_active=True`)
4. A conexão está ativa (`connection.is_active=True`)

## Limpeza de Dados de Teste

Para limpar todas as transações de teste:

```bash
# Via Django Shell
python manage.py shell
```

```python
from apps.banking.models import Transaction

# Contar transações de teste
count = Transaction.objects.filter(
    pluggy_transaction_id__startswith='test_tx_'
).count()

print(f"Encontradas {count} transações de teste")

# Deletar
Transaction.objects.filter(
    pluggy_transaction_id__startswith='test_tx_'
).delete()

print("Transações de teste deletadas!")
```

---

## Suporte

Se encontrar problemas, verifique:
1. ✅ O banco de dados está acessível
2. ✅ O usuário/conta existe e está ativo
3. ✅ As migrations estão atualizadas (`python manage.py migrate`)
4. ✅ Os logs de erro em `logs/error.log`
