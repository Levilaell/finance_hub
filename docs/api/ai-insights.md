# API de AI Insights

Base URL: `/api/ai-insights/`

## Endpoints

### GET /insights/can_enable/

Verificar se usuario pode habilitar AI Insights.

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "can_enable": true,
  "reasons": []
}
```

**Response 200 (nao pode)**:
```json
{
  "can_enable": false,
  "reasons": [
    "Nenhuma conexao bancaria ativa",
    "Sem transacoes nos ultimos 30 dias"
  ]
}
```

---

### GET /insights/config/

Obter configuracao atual.

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "is_enabled": true,
  "company_type": "mei",
  "business_sector": "services",
  "enabled_at": "2025-12-01T10:00:00Z",
  "last_generated_at": "2025-12-18T10:00:00Z"
}
```

---

### POST /insights/enable/

Habilitar AI Insights.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "company_type": "mei",
  "business_sector": "services"
}
```

| Campo | Tipo | Valores |
|-------|------|---------|
| company_type | string | mei, me, epp, ltda, sa, other |
| business_sector | string | retail, services, industry, technology, healthcare, education, food, construction, automotive, agriculture, other |

**Response 200**:
```json
{
  "is_enabled": true,
  "message": "AI Insights habilitado. Gerando primeiro insight..."
}
```

---

### POST /insights/disable/

Desabilitar AI Insights.

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "is_enabled": false
}
```

---

### GET /insights/latest/

Obter ultimo insight gerado.

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "id": "uuid",
  "health_score": 7.5,
  "health_status": "Bom",
  "score_change": 0.5,
  "summary": "Sua empresa apresenta boa saude financeira com receitas estaveis e despesas controladas. O fluxo de caixa esta positivo, mas ha oportunidades de otimizacao em algumas categorias.",
  "alerts": [
    {
      "type": "alert",
      "severity": "medium",
      "title": "Aumento em Despesas de Marketing",
      "description": "Despesas de marketing aumentaram 35% em relacao ao mes anterior.",
      "recommendation": "Avalie o ROI das campanhas atuais antes de aumentar investimentos."
    }
  ],
  "opportunities": [
    {
      "type": "opportunity",
      "title": "Potencial de Economia",
      "description": "Identificamos R$ 800 em servicos de assinatura pouco utilizados.",
      "recommendation": "Revise assinaturas de software e streaming."
    }
  ],
  "predictions": {
    "next_month_cash_flow": 16500.00,
    "confidence": "high",
    "reasoning": "Baseado em receitas recorrentes estaveis e padrao historico de despesas."
  },
  "recommendations": [
    "Criar reserva de emergencia equivalente a 3 meses de despesas fixas",
    "Renegociar tarifas bancarias - potencial de economia de R$ 150/mes",
    "Consolidar gastos de cartao de credito para melhor controle"
  ],
  "generated_at": "2025-12-18T10:00:00Z",
  "period_start": "2025-11-18",
  "period_end": "2025-12-18",
  "has_error": false,
  "is_recent": true
}
```

**Response 200 (sem insight)**:
```json
{
  "detail": "Nenhum insight encontrado"
}
```

---

### POST /insights/regenerate/

Forcar regeneracao de insight.

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "status": "generating",
  "message": "Regenerando insight. Aguarde alguns segundos."
}
```

---

### GET /insights/

Listar todos os insights (historico).

**Autenticacao**: Bearer Token

**Query Params**:
| Param | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| page | int | 1 | Pagina |
| page_size | int | 10 | Itens por pagina |

**Response 200**:
```json
{
  "count": 15,
  "next": "/api/ai-insights/insights/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "health_score": 7.5,
      "health_status": "Bom",
      "generated_at": "2025-12-18T10:00:00Z",
      "period_start": "2025-11-18",
      "period_end": "2025-12-18"
    }
  ]
}
```

---

### GET /insights/{id}/

Obter detalhes de um insight especifico.

**Autenticacao**: Bearer Token

**Response 200**: Mesmo formato do `/insights/latest/`

---

### GET /insights/{id}/compare/

Comparar insight com outro.

**Autenticacao**: Bearer Token

**Query Params**:
| Param | Tipo | Descricao |
|-------|------|-----------|
| with | uuid | ID do insight para comparar |

**Response 200**:
```json
{
  "current": {
    "id": "uuid",
    "health_score": 7.5,
    "period_end": "2025-12-18"
  },
  "previous": {
    "id": "uuid",
    "health_score": 7.0,
    "period_end": "2025-11-18"
  },
  "comparison": {
    "score_change": 0.5,
    "score_change_percentage": 7.14,
    "improved_areas": ["Controle de despesas"],
    "worsened_areas": ["Marketing"]
  }
}
```

---

### GET /insights/history/

Historico paginado de insights.

**Autenticacao**: Bearer Token

Alias para `GET /insights/` com formatacao simplificada.

---

### GET /insights/score_evolution/

Evolucao do health score ao longo do tempo.

**Autenticacao**: Bearer Token

**Response 200**:
```json
[
  {
    "date": "2025-10-18",
    "score": 6.5
  },
  {
    "date": "2025-11-18",
    "score": 7.0
  },
  {
    "date": "2025-12-18",
    "score": 7.5
  }
]
```

---

## Tipos de Dados

### Health Status

| Valor | Score Range | Descricao |
|-------|-------------|-----------|
| Excelente | 9.0 - 10.0 | Saude financeira otima |
| Bom | 7.0 - 8.9 | Boa gestao financeira |
| Regular | 5.0 - 6.9 | Atencao necessaria |
| Ruim | 0.0 - 4.9 | Situacao critica |

### Alert Severity

| Valor | Descricao |
|-------|-----------|
| high | Acao imediata necessaria |
| medium | Atencao recomendada |
| low | Informativo |

### Confidence Level

| Valor | Descricao |
|-------|-----------|
| high | Alta confianca na previsao |
| medium | Confianca moderada |
| low | Incerteza significativa |

---

## Erros Comuns

| Codigo | Situacao | Resposta |
|--------|----------|----------|
| 400 | Nao pode habilitar | `{"can_enable": false, "reasons": [...]}` |
| 404 | Insight nao encontrado | `{"detail": "Not found"}` |
| 500 | Erro na geracao | `{"has_error": true, "error_message": "..."}` |
