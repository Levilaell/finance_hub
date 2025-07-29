# Frontend Inconsistencies Mapping

## Analysis Summary

After analyzing Django models and TypeScript interfaces, several critical inconsistencies were found that need immediate correction for proper frontend-backend integration.

## 1. User Model Inconsistencies

### Django Model (authentication/models.py)
```python
class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    preferred_language = models.CharField(max_length=10, choices=[('pt-br', 'Português'), ('en', 'English')], default='pt-br')
    timezone = models.CharField(max_length=50, default='America/Sao_Paulo')
    is_two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True)
    backup_codes = models.JSONField(default=list, blank=True)
    payment_customer_id = models.CharField(max_length=255, blank=True, null=True)
    payment_gateway = models.CharField(max_length=50, choices=[('stripe', 'Stripe'), ('mercadopago', 'MercadoPago')], blank=True, null=True)
```

### TypeScript Interface (types/index.ts)
```typescript
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  company: Company;
  role: "owner" | "admin" | "member";  // ❌ Not in Django model
  is_active: boolean;
  is_email_verified: boolean;
  is_two_factor_enabled: boolean;
  created_at: string;
  updated_at: string;
}
```

### Missing Fields in TypeScript:
- `phone` (string)
- `is_phone_verified` (boolean)
- `avatar` (string)
- `date_of_birth` (string)
- `last_login_ip` (string)
- `preferred_language` (string)
- `timezone` (string)
- `two_factor_secret` (string)
- `backup_codes` (string[])
- `payment_customer_id` (string)
- `payment_gateway` (string)

### Incorrect Fields in TypeScript:
- `role` field doesn't exist in User model (it's in CompanyUser model)

## 2. SubscriptionPlan Model Inconsistencies

### Django Model (companies/models.py)
```python
class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ('starter', 'Inicial'),
        ('professional', 'Profissional'),  
        ('enterprise', 'Empresarial'),
    ]
    # NO FREE PLAN - Only paid plans with 14-day trial
```

### TypeScript Interface (types/index.ts)
```typescript
export interface SubscriptionPlan {
  plan_type: 'free' | 'starter' | 'professional' | 'enterprise';  // ❌ 'free' doesn't exist
  yearly_discount: number;  // ❌ Not in Django model
}
```

### Issues:
- TypeScript includes 'free' plan type, but Django explicitly states "NO FREE PLAN"  
- `yearly_discount` field doesn't exist in Django (there's a method `get_yearly_discount_percentage()`)

## 3. Banking Models Major Inconsistencies

### Account Interface Issues

#### Django Model (banking/models.py)
```python
class BankAccount(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('BANK', 'Bank Account'),
        ('CREDIT', 'Credit Card'),
        ('INVESTMENT', 'Investment'),
        ('LOAN', 'Loan'),
        ('OTHER', 'Other'),
    ]
    
    ACCOUNT_SUBTYPE_CHOICES = [
        ('CHECKING_ACCOUNT', 'Checking Account'),
        ('SAVINGS_ACCOUNT', 'Savings Account'),
        ('CREDIT_CARD', 'Credit Card'),
        ('PREPAID_CARD', 'Prepaid Card'),
        ('INVESTMENT_ACCOUNT', 'Investment Account'),
        ('LOAN_ACCOUNT', 'Loan Account'),
        ('OTHER', 'Other'),
    ]
```

#### TypeScript Interface (types/index.ts)
```typescript
export interface Account {
  account_type: "checking" | "savings" | "credit_card" | "investment";  // ❌ Wrong values
}
```

### Issues:
- TypeScript uses lowercase values while Django uses uppercase
- TypeScript missing 'LOAN' and 'OTHER' types
- Field name inconsistency: `type` in Django vs `account_type` in TypeScript

## 4. Pluggy Models Inconsistencies

### Major Issue: Complete Structure Mismatch

#### Django Uses Full Pluggy API v2 Structure:
- `PluggyConnector` model with all fields
- `PluggyItem` model with proper status choices  
- `BankAccount` with Pluggy relationships
- `Transaction` with full Pluggy metadata
- `ItemWebhook` for webhook events

#### TypeScript Missing Key Fields:
- No `pluggy_id` in PluggyConnector
- Missing status enums don't match Django choices
- Transaction structure incomplete
- Missing webhook event handling types

## 5. Categories Model Inconsistencies

### Django Model (banking/models.py)
```python
class TransactionCategory(models.Model):
    CATEGORY_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
        ('both', 'Both'),
    ]
    type = models.CharField(max_length=20, choices=CATEGORY_TYPE_CHOICES)
```

### TypeScript Interface (types/index.ts)
```typescript
export interface Category {
  category_type: "income" | "expense";  // ❌ Missing 'transfer' and 'both'
  parent: number | null;  // ❌ Should be string (UUID in Django)
}
```

### Issues:
- Missing 'transfer' and 'both' category types
- `parent` field type mismatch (number vs UUID string)

## 6. Notification Model Inconsistencies

### Django Model (notifications/models.py)
```python
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('low_balance', 'Saldo Baixo'),
        ('large_transaction', 'Transação Grande'),
        ('recurring_payment', 'Pagamento Recorrente'),
        ('sync_error', 'Erro de Sincronização'),
        ('report_ready', 'Relatório Pronto'),
        ('subscription_expiring', 'Assinatura Expirando'),
        ('user_invited', 'Usuário Convidado'),
        ('budget_exceeded', 'Orçamento Excedido'),
        ('ai_insight', 'Insight IA'),
        ('custom', 'Personalizado'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
```

### TypeScript Interface (types/index.ts)
```typescript
export interface Notification {
  type: "info" | "warning" | "error" | "success";  // ❌ Wrong enum values
  category: "transaction" | "account" | "system" | "security";  // ❌ Not in Django model
}
```

### Issues:
- TypeScript `type` field uses generic values instead of specific notification types
- TypeScript `category` field doesn't exist in Django model
- Missing `priority` field and all specific notification types

## 7. Reports Model Inconsistencies

### Reports Missing from Main Types
The main `types/index.ts` has a basic Report interface, but it's missing many fields from the Django model:

#### Missing Fields:
- `company` relationship
- `description`
- `parameters` (different structure)
- `filters` (different structure)
- `generation_time`
- `error_message`
- `created_by` relationship

## 8. Critical Missing Models in TypeScript

### Completely Missing Models:
1. `CompanyUser` - For additional users in companies
2. `PaymentMethod` - For payment methods
3. `PaymentHistory` - For payment history
4. `ResourceUsage` - For usage tracking
5. `AIAnalysis` - For AI analyses
6. `ReportTemplate` - For report templates
7. `NotificationPreference` - For user notification preferences
8. `EmailVerification` - For email verification
9. `PasswordReset` - For password reset

## 9. ID Field Type Inconsistencies

### Major Issue: UUID vs Number
- Django uses UUID fields for most models (string representation)
- TypeScript interfaces sometimes use `number` for IDs
- This causes serialization/deserialization issues

### Examples:
- Category `parent` field: number in TS, UUID string in Django
- Various model IDs should be strings, not numbers

## 10. Pluggy API v2 Compliance Issues

Based on the official Pluggy documentation study:

### Missing Pluggy Features:
1. **Connect Token Management**: TypeScript missing proper token interfaces
2. **Webhook Event Types**: Django has comprehensive webhook support, TypeScript doesn't
3. **Item Status Management**: Status enums don't match official Pluggy statuses
4. **Account Type Structure**: Account types don't match Pluggy's official structure
5. **Transaction Enrichment**: Missing merchant data and payment metadata

## Priority Fix List

### High Priority (Breaks Functionality):
1. Fix User interface - remove non-existent `role` field
2. Remove 'free' plan type from SubscriptionPlan interface
3. Fix Account type enum values and field names
4. Add missing UUID string types for all IDs
5. Fix Category types and parent field type

### Medium Priority (Missing Features):
1. Add all missing User fields
2. Add missing notification types and priority field
3. Add missing report fields
4. Create interfaces for missing models

### Low Priority (Enhancements):
1. Add Pluggy Connect token management interfaces
2. Add comprehensive webhook event types
3. Add transaction enrichment interfaces
4. Add AI analysis interfaces

## Recommended Action Plan

1. **Immediate**: Fix breaking inconsistencies (wrong field types, non-existent fields)
2. **Phase 1**: Add missing fields to existing interfaces
3. **Phase 2**: Create missing model interfaces
4. **Phase 3**: Enhance Pluggy integration with full API v2 compliance
5. **Phase 4**: Add advanced features (AI, webhooks, etc.)