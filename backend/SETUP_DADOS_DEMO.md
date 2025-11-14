# Setup de Dados Demo para Gravação de Vídeo

Este script cria um ambiente completo e realista para demonstração do sistema de gestão financeira para PMEs, lojistas e varejistas.

## 🎯 O que o script cria

### 1. **3 Contas Bancárias Fake** (Contas Correntes)
- ✅ **Conta Empresarial BB** - Banco do Brasil
  - Agência: 1234-5
  - Conta: 12345-6
  - Saldo inicial: R$ 45.280,75

- ✅ **Conta Corrente Itaú** - Itaú Unibanco
  - Agência: 6789
  - Conta: 67890-1
  - Saldo inicial: R$ 28.950,40

- ✅ **Conta PJ Bradesco** - Bradesco
  - Agência: 5432
  - Conta: 54321-9
  - Saldo inicial: R$ 19.635,20

### 2. **24 Categorias Específicas para Varejo**

#### Receitas (6 categorias)
- 💵 Vendas à Vista
- 💳 Vendas Cartão Débito
- 💳 Vendas Cartão Crédito
- 📱 Vendas Pix
- 🛒 Vendas Online
- ➕ Outras Receitas

#### Despesas (18 categorias)
- 📦 Compra de Mercadorias
- 🏭 Fornecedores
- 🏢 Aluguel
- 💡 Energia Elétrica
- 💧 Água
- 📡 Internet/Telefone
- 👥 Salários
- 📋 Encargos Trabalhistas
- 🧮 Contador
- 📢 Marketing
- 🔧 Manutenção
- 🧹 Limpeza
- 🏛️ Impostos
- 🏦 Taxas Bancárias
- 📦 Embalagens
- 🚚 Transporte/Frete
- ⚙️ Equipamentos
- ➖ Outras Despesas

### 3. **Transações Realistas dos Últimos 90 Dias**

#### RECEITAS (Vendas Diárias)
- **Vendas à Vista (Dinheiro)**
  - 4-10 vendas por dia útil
  - 8-15 vendas em fins de semana
  - Valores: R$ 10,00 a R$ 250,00
  - Horário comercial: 8h às 20h

- **Vendas Cartão Débito**
  - Valores: R$ 20,00 a R$ 380,00
  - 30% das transações

- **Vendas Cartão Crédito**
  - Valores: R$ 30,00 a R$ 650,00
  - 25% das transações
  - Valores médios mais altos

- **Vendas Pix**
  - Valores: R$ 15,00 a R$ 450,00
  - 35% das transações
  - Método mais popular

#### DESPESAS (Recorrentes e Variáveis)

**Mensais Fixas:**
- 🏢 Aluguel: R$ 2.800,00 (dia 5)
- 💡 Energia: R$ 450,00 - R$ 850,00 (dia 10)
- 💧 Água: R$ 120,00 - R$ 280,00 (dia 12)
- 📡 Internet: R$ 299,90 (dia 15)
- 🧮 Contador: R$ 450,00 (dia 20)
- 🏛️ Impostos (DAS): R$ 800,00 - R$ 1.500,00 (dia 20)

**Folha de Pagamento (dia 5):**
- Maria Silva - Vendedora: R$ 1.850,00
- João Santos - Estoquista: R$ 1.650,00
- Ana Costa - Caixa: R$ 1.750,00
- INSS Empresa: R$ 1.245,50
- FGTS: R$ 525,00

**Semanais:**
- 📦 Compra de Mercadorias (Segunda/Terça)
  - Atacadão Martins: R$ 1.500,00 - R$ 4.500,00
  - Distribuidora Central: R$ 2.000,00 - R$ 5.500,00
  - Fornecedor ABC Ltda: R$ 1.800,00 - R$ 4.000,00

**Variáveis (Aleatórias):**
- 📢 Marketing (Google/Facebook Ads): R$ 150,00 - R$ 800,00
- 🔧 Manutenção: R$ 180,00 - R$ 450,00
- 🧹 Limpeza: R$ 120,00 - R$ 280,00
- 📦 Embalagens: R$ 150,00 - R$ 350,00
- 🏦 Taxas Bancárias: R$ 35,00 - R$ 85,00
- 🚚 Frete: R$ 180,00 - R$ 450,00

## 🚀 Como usar

### Comando Básico
```bash
cd backend
python manage.py setup_demo_data --user-email seu@email.com
```

### Com limpeza de dados anteriores
```bash
python manage.py setup_demo_data --user-email seu@email.com --clear-all
```

## 📊 Exemplo de Saída

```
============================================================
CONFIGURANDO DADOS DEMO PARA: loja@exemplo.com
============================================================

Limpando dados existentes...
✓ Dados anteriores removidos

Criando categorias...
✓ 24 categorias criadas

Verificando bancos disponíveis...
✓ 3 bancos disponíveis

Criando contas bancárias fake...
  ✓ Conta Empresarial BB - Saldo: R$ 45,280.75
  ✓ Conta Corrente Itaú - Saldo: R$ 28,950.40
  ✓ Conta PJ Bradesco - Saldo: R$ 19,635.20
✓ 3 contas criadas

Criando transações para: Conta Empresarial BB
  ✓ 287 transações criadas

Criando transações para: Conta Corrente Itaú
  ✓ 295 transações criadas

Criando transações para: Conta PJ Bradesco
  ✓ 281 transações criadas

============================================================
RESUMO FINAL
============================================================
Contas Bancárias: 3
Categorias: 24
Transações Totais: 863

============================================================
DETALHAMENTO POR CONTA
============================================================

Conta Empresarial BB (Banco do Brasil)
------------------------------------------------------------
  Transações: 287
  Receitas: R$ 52,450.80
  Despesas: R$ 28,720.35
  Saldo: R$ 23,730.45

Conta Corrente Itaú (Itaú Unibanco)
------------------------------------------------------------
  Transações: 295
  Receitas: R$ 48,920.60
  Despesas: R$ 31,280.90
  Saldo: R$ 17,639.70

Conta PJ Bradesco (Bradesco)
------------------------------------------------------------
  Transações: 281
  Receitas: R$ 45,680.30
  Despesas: R$ 29,450.70
  Saldo: R$ 16,229.60

============================================================
✓ DADOS DEMO CONFIGURADOS COM SUCESSO!
============================================================
```

## 📝 Características dos Dados

### Realismo
- ✅ Transações distribuídas ao longo de 90 dias
- ✅ Domingo = loja fechada (sem vendas)
- ✅ Fins de semana = mais vendas
- ✅ Horário comercial: 8h às 20h
- ✅ Datas específicas para contas fixas
- ✅ Folha de pagamento sempre dia 5
- ✅ Impostos sempre dia 20

### Variedade
- ✅ Múltiplos métodos de pagamento
- ✅ Diferentes fornecedores
- ✅ Despesas fixas e variáveis
- ✅ Valores realistas para cada categoria
- ✅ 3 funcionários com salários diferentes

### Categorização
- ✅ Todas as transações categorizadas
- ✅ Descrições em português
- ✅ Merchants/fornecedores brasileiros
- ✅ Cores e ícones apropriados

## 🎥 Ideal para Demonstração

Este setup é perfeito para gravar vídeos demonstrando:

1. **Dashboard Financeiro**
   - Visão geral de múltiplas contas
   - Gráficos de receitas vs despesas
   - Evolução mensal

2. **Gestão de Transações**
   - Listagem com filtros
   - Busca por categoria
   - Detalhes de cada transação

3. **Relatórios**
   - Relatório por categoria
   - Análise de despesas
   - Fluxo de caixa

4. **Gestão de Categorias**
   - Categorias customizadas
   - Cores e ícones
   - Reorganização

5. **Múltiplas Contas**
   - Comparação entre bancos
   - Consolidação de dados
   - Saldos individuais

## 🔄 Resetar os Dados

Para remover tudo e começar do zero:

```bash
python manage.py setup_demo_data --user-email seu@email.com --clear-all
```

## ⚠️ Importante

- Este script é para **demonstração apenas**
- Todas as transações são marcadas com `demo_tx_`
- Todas as contas são marcadas com `demo_acc_` e `demo_item_`
- Os bancos são cadastrados como conectores reais
- **NÃO USE EM PRODUÇÃO COM DADOS REAIS**

## 📋 Checklist Antes de Gravar

Após rodar o script, verifique:

- [ ] 3 contas bancárias aparecem no dashboard
- [ ] Saldos estão corretos
- [ ] Transações aparecem na lista
- [ ] Filtros por categoria funcionam
- [ ] Gráficos estão preenchidos
- [ ] Datas cobrem os últimos 90 dias
- [ ] Todas as categorias aparecem
- [ ] Descrições estão em português
- [ ] Ícones e cores estão visíveis

## 🛠️ Troubleshooting

### Erro: "User not found"
**Solução:** Verifique se o email está correto ou crie o usuário primeiro:
```bash
python manage.py createsuperuser
```

### Contas não aparecem no frontend
**Solução:** Verifique se:
1. O usuário está autenticado com o email correto
2. As migrations estão atualizadas
3. O cache foi limpo

### Transações duplicadas
**Solução:** Use `--clear-all` para limpar antes de criar novos dados:
```bash
python manage.py setup_demo_data --user-email seu@email.com --clear-all
```

## 💡 Dicas para Gravação

1. **Ordem de gravação sugerida:**
   - Dashboard geral
   - Detalhe de uma conta
   - Lista de transações com filtros
   - Categorias
   - Relatórios

2. **Pontos a destacar:**
   - Múltiplas contas em um lugar só
   - Categorização automática
   - Filtros poderosos
   - Dados em tempo real
   - Interface intuitiva

3. **Cenários de uso:**
   - "Como acompanhar vendas diárias"
   - "Como controlar despesas fixas"
   - "Como ver fluxo de caixa mensal"
   - "Como comparar bancos diferentes"

---

**Pronto para gravar!** 🎬
