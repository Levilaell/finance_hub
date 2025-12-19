# API de Reports

Base URL: `/api/reports/`

## Endpoints

### GET /dre/

Gerar DRE (Demonstrativo de Resultado do Exercicio).

**Autenticacao**: Bearer Token

**Query Params**:
| Param | Tipo | Obrigatorio | Descricao |
|-------|------|-------------|-----------|
| start_date | date | Sim | Data inicial (YYYY-MM-DD) |
| end_date | date | Sim | Data final (YYYY-MM-DD) |
| compare_with_previous | bool | Nao | Incluir periodo anterior |

**Response 200**:
```json
{
  "period": {
    "start": "2025-01-01",
    "end": "2025-12-18"
  },
  "revenue": {
    "total": 70000.00,
    "by_category": [
      {
        "category": "Vendas",
        "amount": 50000.00,
        "percentage": 71.43
      },
      {
        "category": "Servicos",
        "amount": 20000.00,
        "percentage": 28.57
      }
    ]
  },
  "expenses": {
    "total": 30000.00,
    "by_category": [
      {
        "category": "Custos Operacionais",
        "amount": 15000.00,
        "percentage": 50.00
      },
      {
        "category": "Despesas Administrativas",
        "amount": 10000.00,
        "percentage": 33.33
      },
      {
        "category": "Marketing",
        "amount": 5000.00,
        "percentage": 16.67
      }
    ]
  },
  "result": {
    "operating_result": 40000.00,
    "margin_percentage": 57.14
  },
  "comparison": {
    "previous_period": {
      "start": "2024-01-01",
      "end": "2024-12-18"
    },
    "revenue_change": 15.00,
    "expenses_change": -5.00,
    "result_change": 25.00
  }
}
```

---

### GET /dre_export_pdf/

Exportar DRE como PDF.

**Autenticacao**: Bearer Token

**Query Params**: Mesmos de `/dre/`

**Response 200**: Arquivo PDF (application/pdf)

**Headers de Resposta**:
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="dre_2025-01-01_2025-12-18.pdf"
```

---

### GET /dre_export_excel/

Exportar DRE como Excel.

**Autenticacao**: Bearer Token

**Query Params**: Mesmos de `/dre/`

**Response 200**: Arquivo XLSX (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)

---

### GET /cash_flow/

Relatorio de fluxo de caixa.

**Autenticacao**: Bearer Token

**Query Params**:
| Param | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| start_date | date | - | Data inicial |
| end_date | date | - | Data final |
| granularity | string | monthly | daily, weekly, monthly, yearly |

**Response 200**:
```json
{
  "period": {
    "start": "2025-01-01",
    "end": "2025-12-18"
  },
  "granularity": "monthly",
  "data": [
    {
      "period": "2025-01",
      "inflows": 55000.00,
      "outflows": 25000.00,
      "net": 30000.00,
      "cumulative": 30000.00
    },
    {
      "period": "2025-02",
      "inflows": 60000.00,
      "outflows": 28000.00,
      "net": 32000.00,
      "cumulative": 62000.00
    }
  ],
  "summary": {
    "total_inflows": 700000.00,
    "total_outflows": 300000.00,
    "total_net": 400000.00,
    "average_monthly_net": 33333.33
  }
}
```

---

### GET /category_breakdown/

Detalhamento por categoria.

**Autenticacao**: Bearer Token

**Query Params**:
| Param | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| start_date | date | - | Data inicial |
| end_date | date | - | Data final |
| transaction_type | string | DEBIT | CREDIT, DEBIT |

**Response 200**:
```json
{
  "period": {
    "start": "2025-01-01",
    "end": "2025-12-18"
  },
  "type": "DEBIT",
  "total": 30000.00,
  "categories": [
    {
      "name": "Alimentacao",
      "amount": 8000.00,
      "percentage": 26.67,
      "transaction_count": 150,
      "subcategories": [
        {
          "name": "Restaurantes",
          "amount": 5000.00,
          "percentage": 62.50
        },
        {
          "name": "Supermercado",
          "amount": 3000.00,
          "percentage": 37.50
        }
      ]
    },
    {
      "name": "Transporte",
      "amount": 5000.00,
      "percentage": 16.67,
      "transaction_count": 80
    }
  ]
}
```

---

### GET /monthly_summary/

Resumo de um mes especifico.

**Autenticacao**: Bearer Token

**Query Params**:
| Param | Tipo | Descricao |
|-------|------|-----------|
| month | int | Mes (1-12) |
| year | int | Ano |

**Response 200**:
```json
{
  "month": 12,
  "year": 2025,
  "revenue": 70000.00,
  "expenses": 30000.00,
  "result": 40000.00,
  "margin": 57.14,
  "top_revenue_categories": [
    {"name": "Vendas", "amount": 50000.00}
  ],
  "top_expense_categories": [
    {"name": "Custos Operacionais", "amount": 15000.00}
  ],
  "comparison_with_previous": {
    "revenue_change": 5.00,
    "expenses_change": -2.00
  }
}
```

---

### GET /trend_analysis/

Analise de tendencias.

**Autenticacao**: Bearer Token

**Query Params**:
| Param | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| months | int | 6 | Numero de meses a analisar |
| end_date | date | hoje | Data final |

**Response 200**:
```json
{
  "period": {
    "months": 6,
    "end_date": "2025-12-18"
  },
  "revenue_trend": {
    "direction": "up",
    "average_monthly": 58333.33,
    "growth_rate": 8.5,
    "data": [
      {"month": "2025-07", "value": 50000.00},
      {"month": "2025-08", "value": 52000.00},
      {"month": "2025-12", "value": 70000.00}
    ]
  },
  "expense_trend": {
    "direction": "stable",
    "average_monthly": 28000.00,
    "growth_rate": 2.1,
    "data": [...]
  },
  "result_trend": {
    "direction": "up",
    "average_monthly": 30000.00,
    "growth_rate": 15.2
  },
  "projections": {
    "next_month_revenue": 75000.00,
    "next_month_expenses": 29000.00,
    "confidence": "medium"
  }
}
```

---

### POST /comparison/

Comparar dois periodos.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "period1_start": "2025-01-01",
  "period1_end": "2025-06-30",
  "period2_start": "2025-07-01",
  "period2_end": "2025-12-18"
}
```

**Response 200**:
```json
{
  "period1": {
    "label": "1o Semestre 2025",
    "start": "2025-01-01",
    "end": "2025-06-30",
    "revenue": 350000.00,
    "expenses": 150000.00,
    "result": 200000.00
  },
  "period2": {
    "label": "2o Semestre 2025",
    "start": "2025-07-01",
    "end": "2025-12-18",
    "revenue": 420000.00,
    "expenses": 180000.00,
    "result": 240000.00
  },
  "comparison": {
    "revenue_change": 70000.00,
    "revenue_change_percent": 20.00,
    "expenses_change": 30000.00,
    "expenses_change_percent": 20.00,
    "result_change": 40000.00,
    "result_change_percent": 20.00
  },
  "category_comparison": [
    {
      "category": "Vendas",
      "period1": 250000.00,
      "period2": 300000.00,
      "change_percent": 20.00
    }
  ]
}
```

---

## Formatos de Exportacao

### PDF

- Gerado com ReportLab ou WeasyPrint
- Inclui cabecalho com logo e periodo
- Tabelas formatadas
- Graficos (opcional)

### Excel

- Multiplas abas:
  - Resumo
  - Receitas por categoria
  - Despesas por categoria
  - Dados brutos
- Formatacao de moeda
- Formulas de soma

### CSV

- Delimitador: ponto-e-virgula (;)
- Encoding: UTF-8 com BOM
- Formato numerico brasileiro

---

## Erros

| Codigo | Situacao | Resposta |
|--------|----------|----------|
| 400 | Datas invalidas | `{"error": "Invalid date range"}` |
| 400 | Periodo muito longo | `{"error": "Period exceeds maximum"}` |
| 404 | Sem dados | `{"error": "No transactions found"}` |
