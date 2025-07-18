# Reports API Documentation

## Generate Report

### Endpoint
```
POST /api/reports/reports/
```

### Headers
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

### Request Body
```json
{
    "report_type": "profit_loss",  // or "cash_flow", "monthly_summary", "category_analysis"
    "title": "Relatório DRE - Janeiro 2025",
    "description": "Demonstração de resultados do mês",
    "period_start": "2025-01-01",
    "period_end": "2025-01-31",
    "file_format": "pdf",  // or "xlsx"
    "parameters": {
        "account_ids": [],  // optional: filter by account IDs
        "category_ids": []  // optional: filter by category IDs
    }
}
```

### Report Types Available
1. **profit_loss** - DRE (Demonstração de Resultados)
   - Shows revenue and expenses by category
   - Monthly breakdown
   - Net profit/loss calculation

2. **cash_flow** - Fluxo de Caixa
   - Account balances (opening/closing)
   - Daily cash flow
   - Inflows and outflows by category

3. **monthly_summary** - Resumo Mensal
   - Key metrics and averages
   - Top 10 expenses and income
   - Category breakdown with pie chart
   - Account activity summary

4. **category_analysis** - Análise por Categoria
   - Detailed category breakdown
   - Category trends over time
   - Percentage analysis
   - Average transaction by category

## List Reports

### Endpoint
```
GET /api/reports/reports/
```

### Query Parameters
- `page`: Page number
- `limit`: Results per page
- `report_type`: Filter by type
- `is_generated`: Filter by generation status

## Download Report

### Endpoint
```
GET /api/reports/reports/{report_id}/download/
```

### Response
Binary file (PDF or Excel)

## Quick Reports

### List Quick Report Options
```
GET /api/reports/quick/
```

### Generate Quick Report
```
POST /api/reports/quick/
```

Body:
```json
{
    "report_id": "current_month"  // or "last_month", "quarterly", "year_to_date", "cash_flow_30"
}
```

## Report Summary Statistics

### Endpoint
```
GET /api/reports/reports/summary/
```

Returns summary statistics about generated reports.

## Testing with cURL

### Generate a Profit & Loss Report
```bash
curl -X POST http://localhost:8000/api/reports/reports/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "profit_loss",
    "title": "DRE - Janeiro 2025",
    "period_start": "2025-01-01",
    "period_end": "2025-01-31",
    "file_format": "pdf"
  }'
```

### Generate a Cash Flow Report
```bash
curl -X POST http://localhost:8000/api/reports/reports/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "cash_flow",
    "title": "Fluxo de Caixa - Janeiro 2025",
    "period_start": "2025-01-01",
    "period_end": "2025-01-31",
    "file_format": "pdf"
  }'
```

### Download a Report
```bash
curl -X GET http://localhost:8000/api/reports/reports/{REPORT_ID}/download/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o report.pdf
```