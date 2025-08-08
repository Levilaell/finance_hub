# Pluggy Integration Improvements

This document describes the improvements made to the Pluggy integration based on the official API documentation.

## 1. Transaction Category Synchronization

### Overview
When users update transaction categories in the Finance Hub, the changes are now synchronized with Pluggy's API. This helps improve Pluggy's categorization model.

### Implementation
- Added `update_transaction_category()` method to `PluggyClient`
- Modified `TransactionViewSet.update()` to sync category changes with Pluggy
- Categories are synced only when a Pluggy mapping exists

### Usage
```python
# Update transaction category (automatically syncs with Pluggy)
PATCH /api/banking/transactions/{id}/
{
    "category": "category-uuid"
}
```

## 2. Enhanced Connect Token Parameters

### Overview
The Connect Token creation now supports all parameters from Pluggy API v2, allowing better control over the connection flow.

### New Parameters
- `avoid_duplicates`: Prevents creating duplicate items for the same institution
- `country_codes`: Filter connectors by country (e.g., ['BR', 'US'])
- `connector_types`: Filter by connector type (e.g., ['PERSONAL_BANK', 'BUSINESS_BANK'])
- `connector_ids`: Show only specific connectors
- `products_types`: Enable specific products (e.g., ['ACCOUNTS', 'TRANSACTIONS'])
- `oauth_redirect_uri`: Custom redirect URL after OAuth flow

### Usage
```python
# Create connect token with filters
POST /api/banking/pluggy/connect-token/
{
    "avoid_duplicates": true,
    "country_codes": ["BR"],
    "connector_types": ["PERSONAL_BANK"],
    "products_types": ["ACCOUNTS", "TRANSACTIONS"]
}
```

## 3. Webhook Signature Validation

### Overview
Implemented proper webhook signature validation using HMAC-SHA256 to ensure webhook authenticity.

### Configuration
Add to your environment variables:
```bash
PLUGGY_WEBHOOK_SECRET=your-webhook-secret-from-pluggy
```

### How it Works
1. Pluggy sends webhooks with `X-Pluggy-Signature` header
2. The signature is validated using HMAC-SHA256 with the configured secret
3. Invalid signatures are rejected with 401 status
4. If no secret is configured, webhooks are accepted with a warning

### Security Benefits
- Prevents webhook spoofing
- Ensures data integrity
- Uses constant-time comparison to prevent timing attacks

## Testing

### Running Tests
```bash
python manage.py test apps.banking.tests.test_pluggy_integration
```

### Test Coverage
- Transaction category synchronization
- Connect token parameter handling
- Webhook signature validation (valid/invalid/no secret scenarios)

## Frontend Integration

### Connect Token with Filters
```javascript
// Example: Show only Brazilian personal banks
const response = await api.post('/banking/pluggy/connect-token/', {
  avoid_duplicates: true,
  country_codes: ['BR'],
  connector_types: ['PERSONAL_BANK']
});

// Use the token with Pluggy Connect
const connectUrl = response.data.data.connect_url;
```

### Category Update
```javascript
// Update transaction category (auto-syncs with Pluggy)
await api.patch(`/banking/transactions/${transactionId}/`, {
  category: categoryId
});
```

## Migration Notes

1. Set `PLUGGY_WEBHOOK_SECRET` in production environment
2. Test webhook validation in staging before deploying
3. Monitor logs for category sync failures
4. Consider implementing retry logic for failed Pluggy API calls

## Future Improvements

1. Add retry mechanism for failed category syncs
2. Implement webhook event replay functionality
3. Add metrics for sync success/failure rates
4. Create admin interface for managing Pluggy category mappings