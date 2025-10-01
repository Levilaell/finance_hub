# Reports API Documentation

## Overview
The Reports API provides comprehensive financial data aggregation and analysis endpoints designed to feed various types of graphs and dashboards.

## Available Endpoints

### 1. Cash Flow Report
**GET** `/api/reports/cash-flow/`

Returns income vs expenses over time.

**Query Parameters:**
- `start_date` (optional): ISO datetime string (default: 30 days ago)
- `end_date` (optional): ISO datetime string (default: now)
- `granularity` (optional): `daily`, `weekly`, `monthly`, `yearly` (default: `daily`)

**Response Format:**
```json
{
  "generated_at": "2024-01-15T10:30:00Z",
  "report_type": "cash_flow",
  "data": {
    "labels": ["2024-01-01", "2024-01-02", ...],
    "datasets": [
      {
        "label": "Income",
        "data": [1000, 1500, ...],
        "borderColor": "rgb(75, 192, 192)",
        "backgroundColor": "rgba(75, 192, 192, 0.2)"
      },
      {
        "label": "Expenses",
        "data": [800, 900, ...],
        "borderColor": "rgb(255, 99, 132)",
        "backgroundColor": "rgba(255, 99, 132, 0.2)"
      }
    ],
    "summary": {
      "total_income": 15000,
      "total_expenses": 10000,
      "net_cash_flow": 5000,
      "period": "2024-01-01 to 2024-01-31",
      "granularity": "daily"
    }
  }
}
```

### 2. Category Breakdown
**GET** `/api/reports/category-breakdown/`

Returns expenses or income by category (ideal for pie/donut charts).

**Query Parameters:**
- `start_date` (optional): ISO datetime string
- `end_date` (optional): ISO datetime string
- `transaction_type` (optional): `DEBIT` or `CREDIT` (default: `DEBIT`)

**Response Format:**
```json
{
  "generated_at": "2024-01-15T10:30:00Z",
  "report_type": "category_breakdown",
  "data": {
    "labels": ["Food", "Transport", "Entertainment", ...],
    "datasets": [{
      "data": [2000, 1500, 800, ...],
      "backgroundColor": [...],
      "borderColor": [...],
      "borderWidth": 1
    }],
    "percentages": [25.5, 19.1, 10.2, ...],
    "summary": {
      "total_amount": 7850,
      "categories_count": 8,
      "transaction_type": "Expenses",
      "period": "2024-01-01 to 2024-01-31"
    }
  }
}
```

### 3. Account Balances Evolution
**GET** `/api/reports/account-balances/`

Returns balance evolution over time for multiple accounts.

**Query Parameters:**
- `start_date` (optional): ISO datetime string
- `end_date` (optional): ISO datetime string
- `account_ids` (optional): Comma-separated list of account UUIDs

**Response Format:**
```json
{
  "generated_at": "2024-01-15T10:30:00Z",
  "report_type": "account_balances",
  "data": {
    "labels": ["2024-01-01", "2024-01-02", ...],
    "datasets": [
      {
        "label": "Checking Account",
        "data": [5000, 5200, 4800, ...],
        "borderColor": "rgb(255, 99, 132)",
        "backgroundColor": "rgba(255, 99, 132, 0.2)",
        "tension": 0.1,
        "fill": false
      },
      ...
    ],
    "summary": {
      "accounts_count": 3,
      "period": "2024-01-01 to 2024-01-31"
    }
  }
}
```

### 4. Monthly Summary
**GET** `/api/reports/monthly-summary/`

Returns comprehensive monthly financial summary.

**Query Parameters:**
- `month` (required): Month number (1-12)
- `year` (required): Year (e.g., 2024)

**Response Format:**
```json
{
  "generated_at": "2024-01-15T10:30:00Z",
  "report_type": "monthly_summary",
  "data": {
    "month": "2024-01",
    "income": {
      "total": 8000,
      "count": 5,
      "daily_avg": 258.06
    },
    "expenses": {
      "total": 6500,
      "count": 45,
      "daily_avg": 209.68
    },
    "net_savings": 1500,
    "top_expenses": [...],
    "top_income": [...],
    "daily_chart": {
      "labels": ["1", "2", "3", ...],
      "datasets": [...]
    }
  }
}
```

### 5. Trend Analysis
**GET** `/api/reports/trend-analysis/`

Returns financial trends over multiple months.

**Query Parameters:**
- `months` (optional): Number of months to analyze (1-24, default: 6)
- `end_date` (optional): ISO datetime string (default: now)

**Response Format:**
```json
{
  "generated_at": "2024-01-15T10:30:00Z",
  "report_type": "trend_analysis",
  "data": {
    "labels": ["2023-08", "2023-09", ...],
    "datasets": [
      {
        "label": "Income Trend",
        "data": [7000, 7500, 8000, ...],
        "borderColor": "rgb(75, 192, 192)",
        "backgroundColor": "rgba(75, 192, 192, 0.2)",
        "tension": 0.3
      },
      {
        "label": "Expense Trend",
        "data": [5000, 5500, 6000, ...],
        "borderColor": "rgb(255, 99, 132)",
        "backgroundColor": "rgba(255, 99, 132, 0.2)",
        "tension": 0.3
      }
    ],
    "analysis": {
      "income_trend_percentage": 15.5,
      "expense_trend_percentage": 20.3,
      "income_direction": "up",
      "expense_direction": "up",
      "avg_monthly_income": 7500,
      "avg_monthly_expenses": 5500,
      "months_analyzed": 6
    }
  }
}
```

### 6. Period Comparison
**POST** `/api/reports/comparison/`

Compares two different time periods.

**Request Body:**
```json
{
  "period1_start": "2023-12-01T00:00:00Z",
  "period1_end": "2023-12-31T23:59:59Z",
  "period2_start": "2024-01-01T00:00:00Z",
  "period2_end": "2024-01-31T23:59:59Z"
}
```

**Response Format:**
```json
{
  "generated_at": "2024-01-15T10:30:00Z",
  "report_type": "comparison",
  "data": {
    "period1": {
      "income": 7500,
      "expenses": 6000,
      "net": 1500,
      "transactions_count": 145,
      "top_categories": [...],
      "period": "2023-12-01 to 2023-12-31"
    },
    "period2": {
      "income": 8000,
      "expenses": 6500,
      "net": 1500,
      "transactions_count": 150,
      "top_categories": [...],
      "period": "2024-01-01 to 2024-01-31"
    },
    "changes": {
      "income": {
        "absolute": 500,
        "percentage": 6.7
      },
      "expenses": {
        "absolute": 500,
        "percentage": 8.3
      },
      "net": {
        "absolute": 0,
        "percentage": 0
      }
    },
    "comparison_chart": {
      "labels": ["Income", "Expenses", "Net Savings"],
      "datasets": [...]
    }
  }
}
```

### 7. Bulk Reports
**POST** `/api/reports/bulk/`

Generate multiple reports in a single request.

**Request Body:**
```json
{
  "reports": ["cash_flow", "category_breakdown", "trend_analysis"],
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z",
  "granularity": "daily"
}
```

### 8. Dashboard Summary
**GET** `/api/reports/dashboard-summary/`

Optimized endpoint for dashboard initial load.

**Response Format:**
```json
{
  "generated_at": "2024-01-15T10:30:00Z",
  "summary": {
    "current_month_income": 8000,
    "current_month_expenses": 6500,
    "net_cash_flow": 1500,
    "top_expense_category": "Food",
    "income_trend": "up",
    "expense_trend": "stable"
  },
  "charts": {
    "cash_flow": {...},
    "expenses_by_category": {...},
    "trend": {...}
  }
}
```

### 9. Available Reports
**GET** `/api/reports/available/`

Returns list of available reports and their metadata.

## Frontend Integration

### Chart.js Example

```javascript
// Cash Flow Line Chart
const cashFlowData = await fetch('/api/reports/cash-flow/?granularity=daily')
  .then(res => res.json());

new Chart(ctx, {
  type: 'line',
  data: cashFlowData.data,
  options: {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Cash Flow Report'
      }
    }
  }
});

// Category Breakdown Pie Chart
const categoryData = await fetch('/api/reports/category-breakdown/')
  .then(res => res.json());

new Chart(ctx, {
  type: 'pie',
  data: categoryData.data,
  options: {
    responsive: true,
    plugins: {
      legend: {
        position: 'right',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const percentage = categoryData.data.percentages[context.dataIndex];
            return `${label}: ${percentage}%`;
          }
        }
      }
    }
  }
});
```

## Authentication

All endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Error Responses

```json
{
  "error": "Error message",
  "detail": "Detailed error description"
}
```

## Performance Notes

- Dashboard Summary endpoint is optimized for initial dashboard load
- Use Bulk Reports endpoint to fetch multiple reports efficiently
- Consider implementing frontend caching for frequently accessed reports
- Date ranges are limited to prevent excessive database queries

## Testing

Run the test command to verify reports generation:

```bash
python manage.py test_reports --user-email=test@example.com
```