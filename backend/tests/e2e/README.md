# E2E Tests

This directory contains end-to-end tests that simulate complete user journeys through the application.

## Test Files

### 1. `test_simple_registration_flow.py`
**Status: ✅ PASSING**

Tests the basic user journey:
- User registration
- Email verification (mocked)
- Login/logout
- Accessing protected endpoints
- Dashboard access
- Basic API functionality

### 2. `test_registration_to_login_flow.py`
**Status: 🟡 PARTIAL**

Tests more complex flows including:
- Complete registration with company creation
- Subscription plan selection
- Payment simulation (mocked)
- Feature access based on subscription
- Trial user experience
- Multi-step registration

Issues:
- Payment gateway configuration needs adjustment
- Some endpoints may require additional setup

### 3. `test_public_registration_flow.py`
**Status: 🔧 NOT TESTED**

Tests public-facing registration flows:
- Public API endpoints for plans
- Registration with plan selection
- Brazilian payment methods (PIX, Boleto)
- Free trial limitations
- Email/company validation

### 4. `test_user_registration_payment_flow.py`
**Status: 🔧 NOT TESTED**

Tests complete payment flows:
- Full payment processing simulation
- Trial to paid conversion
- Payment failure and retry
- Subscription management

Note: This test requires payment models that don't exist yet in the codebase.

### 5. `test_complete_user_journey.py` (Existing)
**Status: ✅ COMPREHENSIVE**

The original comprehensive e2e test that covers:
- Complete user journey from registration to report generation
- Bank account integration
- Transaction management
- Budget and goal setting
- Team invitations
- Multi-company scenarios

## Running the Tests

```bash
# Run all e2e tests
python manage.py test tests.e2e

# Run specific test file
python manage.py test tests.e2e.test_simple_registration_flow

# Run specific test method
python manage.py test tests.e2e.test_simple_registration_flow.TestSimpleRegistrationFlow.test_registration_to_dashboard

# Run with verbose output
python manage.py test tests.e2e -v 2

# Keep test database for debugging
python manage.py test tests.e2e --keepdb
```

## Test Coverage

The e2e tests cover:

1. **Authentication Flow**
   - Registration
   - Email verification
   - Login/logout
   - Token refresh
   - Password reset

2. **Company Management**
   - Company creation during registration
   - Profile completion
   - Subscription management
   - Team invitations

3. **Banking Features**
   - Dashboard access
   - Bank account management
   - Transaction handling
   - Budget tracking

4. **Payment Processing**
   - Plan selection
   - Payment method setup
   - Subscription upgrades
   - Brazilian payment methods

## Known Issues

1. **Payment Gateway**: Tests need `DEFAULT_PAYMENT_GATEWAY` setting
2. **Payment Models**: Some tests expect Payment/PaymentMethod models that don't exist
3. **Trial Logic**: Company subscription status varies between 'trial' and 'active'
4. **API Responses**: Some endpoints return different data structures than expected

## Recommendations

1. Focus on `test_simple_registration_flow.py` for basic smoke testing
2. Use `test_complete_user_journey.py` for comprehensive integration testing
3. Adapt payment-related tests when payment models are implemented
4. Add more specific tests for Brazilian market features (CNPJ, PIX, etc.)