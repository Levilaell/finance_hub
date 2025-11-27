# PROVA REAL - Relatórios

**Usuário:** usuario@local.com
**Data de geração:** 26/11/2025
**Última atualização:** 26/11/2025

---

## IMPORTANTE: Consistência de Dados

Os **Cards de Resumo** e o **Gráfico Receitas vs Despesas** usam a **mesma fonte de dados** (transações carregadas no frontend), garantindo que os totais sejam idênticos.

---

## 1. Filtro: Mês Atual (Novembro/2025)

**Período:** 01/11/2025 a 30/11/2025

### Cards de Resumo

| Métrica | Valor Esperado |
|---------|----------------|
| Receitas | R$ 130.779,11 |
| Despesas | R$ 85.525,47 |
| Resultado | R$ 45.253,64 |
| Taxa Poupança | 34,6% |

### Gráfico Receitas vs Despesas (1 mês)

| Mês | Receitas | Despesas | Resultado |
|-----|----------|----------|-----------|
| nov/25 | R$ 130.779,11 | R$ 85.525,47 | R$ 45.253,64 |

**Verificação:** Cards = Soma do gráfico ✓

---

## 2. Filtro: Últimos 3 Meses

**Período:** 01/09/2025 a 30/11/2025

### Cards de Resumo

| Métrica | Valor Esperado |
|---------|----------------|
| Receitas | R$ 444.457,51 |
| Despesas | R$ 250.236,63 |
| Resultado | R$ 194.220,88 |
| Taxa Poupança | 43,7% |
| Transações | 2096 |

### Gráfico Receitas vs Despesas (3 meses)

| Mês | Receitas | Despesas | Resultado |
|-----|----------|----------|-----------|
| set/25 | R$ 156.272,55 | R$ 75.389,52 | R$ 80.883,03 |
| out/25 | R$ 157.405,85 | R$ 89.321,64 | R$ 68.084,21 |
| nov/25 | R$ 130.779,11 | R$ 85.525,47 | R$ 45.253,64 |
| **TOTAL** | **R$ 444.457,51** | **R$ 250.236,63** | **R$ 194.220,88** |

**Verificação:** Cards = Soma do gráfico ✓

---

## 3. Filtro: Últimos 6 Meses

**Período:** 01/06/2025 a 30/11/2025

*(Valores a serem verificados se necessário)*

---

## 4. Filtro: Todas as Transações

### Cards de Resumo

*(Valores a serem verificados se necessário)*

---

## 5. Saldo das Contas Bancárias

| Conta | Saldo |
|-------|-------|
| Conta Corrente Itaú | R$ 28.950,40 |
| Conta Empresarial BB | R$ 45.280,75 |
| Conta PJ Bradesco | R$ 19.635,20 |
| **TOTAL** | **R$ 93.866,35** |

---

## 6. Fluxo de Caixa - Projeção (Próximos 12 Meses)

**Nota:** A projeção mostra apenas bills com vencimento >= hoje. Bills vencidas não aparecem.

| Mês | A Receber | A Pagar | Resultado |
|-----|-----------|---------|-----------|
| nov/25 | R$ 0,00 | R$ 0,00 | R$ 0,00 | *(bills de nov já venceram)*
| dez/25 | R$ 29.700,00 | R$ 8.299,00 | R$ 21.401,00 |
| jan/26 | R$ 29.700,00 | R$ 8.299,00 | R$ 21.401,00 |
| fev/26 | R$ 29.700,00 | R$ 10.699,00 | R$ 19.001,00 |
| mar/26 | R$ 29.700,00 | R$ 8.299,00 | R$ 21.401,00 |
| abr/26 | R$ 29.700,00 | R$ 8.299,00 | R$ 21.401,00 |

## 6.1 Gráfico Previsto vs Realizado

| Mês | Previsto | Realizado |
|-----|----------|-----------|
| nov/25 | R$ 0,00 | R$ 38.101,00 |
| dez/25 | R$ 21.401,00 | R$ 0,00 |
| jan/26 | R$ 21.401,00 | R$ 0,00 |
| fev/26 | R$ 19.001,00 | R$ 0,00 |
| mar/26 | R$ 21.401,00 | R$ 0,00 |
| abr/26 | R$ 21.401,00 | R$ 0,00 |

**Interpretação:**
- **Previsto (linha tracejada azul):** O que ainda falta pagar/receber (bills futuras)
- **Realizado (linha sólida verde):** O que já foi pago/recebido este mês

---

## 7. Aba Comparativo - Mês Atual vs Anterior

*(Filtro: Mês atual - novembro/2025)*
*(Período anterior: outubro/2025)*

### Receitas

| Período | Valor |
|---------|-------|
| nov/25 (Atual) | R$ 130.779,11 |
| out/25 (Anterior) | R$ 150.658,40 |
| **Variação** | **-13,2%** |

### Despesas

| Período | Valor |
|---------|-------|
| nov/25 (Atual) | R$ 85.525,47 |
| out/25 (Anterior) | R$ 89.105,90 |
| **Variação** | **-4,0%** |

---

*Arquivo atualizado com valores reais do banco de dados.*
