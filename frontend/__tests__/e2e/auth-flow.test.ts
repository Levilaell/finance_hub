/**
 * End-to-end tests for authentication flow
 * These tests require a running backend and frontend
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000';
const API_URL = process.env.E2E_API_URL || 'http://localhost:8000';

// Test data
const TEST_USER = {
  email: `test.${Date.now()}@example.com`,
  password: 'TestPass123!',
  firstName: 'Test',
  lastName: 'User',
  phone: '(11) 99999-9999',
  companyName: 'Test Company E2E',
  companyCnpj: '12345678000195',
  companyType: 'ME',
  businessSector: 'Tecnologia',
};

const EXISTING_USER = {
  email: 'existing@example.com',
  password: 'ExistingPass123!',
};

class AuthPage {
  constructor(private page: Page) {}

  async goto(path: string = '/') {
    await this.page.goto(`${BASE_URL}${path}`);
  }

  async fillLoginForm(email: string, password: string) {
    await this.page.fill('[data-testid="email-input"]', email);
    await this.page.fill('[data-testid="password-input"]', password);
  }

  async fillRegistrationForm(userData: typeof TEST_USER) {
    await this.page.fill('[data-testid="email-input"]', userData.email);
    await this.page.fill('[data-testid="password-input"]', userData.password);
    await this.page.fill('[data-testid="password2-input"]', userData.password);
    await this.page.fill('[data-testid="first-name-input"]', userData.firstName);
    await this.page.fill('[data-testid="last-name-input"]', userData.lastName);
    await this.page.fill('[data-testid="phone-input"]', userData.phone);
    await this.page.fill('[data-testid="company-name-input"]', userData.companyName);
    await this.page.fill('[data-testid="company-cnpj-input"]', userData.companyCnpj);
    await this.page.selectOption('[data-testid="company-type-select"]', userData.companyType);
    await this.page.fill('[data-testid="business-sector-input"]', userData.businessSector);
  }

  async submitLoginForm() {
    await this.page.click('[data-testid="login-submit"]');
  }

  async submitRegistrationForm() {
    await this.page.click('[data-testid="register-submit"]');
  }

  async waitForAuthSuccess() {
    // Wait for redirect to dashboard or success message
    await this.page.waitForURL('**/dashboard/**', { timeout: 10000 });
  }

  async waitForAuthError() {
    await this.page.waitForSelector('[data-testid="error-message"]', { timeout: 5000 });
  }

  async logout() {
    await this.page.click('[data-testid="user-menu"]');
    await this.page.click('[data-testid="logout-button"]');
  }

  async expectToBeOnLoginPage() {
    await expect(this.page).toHaveURL(`${BASE_URL}/login`);
    await expect(this.page.locator('h2')).toContainText(/sign in|login/i);
  }

  async expectToBeOnRegisterPage() {
    await expect(this.page).toHaveURL(`${BASE_URL}/register`);
    await expect(this.page.locator('h2')).toContainText(/sign up|register|create account/i);
  }

  async expectToBeOnDashboard() {
    await expect(this.page).toHaveURL(/.*\/dashboard.*/);
  }

  async expectErrorMessage(message: string) {
    await expect(this.page.locator('[data-testid="error-message"]')).toContainText(message);
  }
}

test.describe('Authentication Flow', () => {
  let authPage: AuthPage;

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page);
  });

  test.describe('User Registration', () => {
    test('should register new user successfully', async () => {
      await authPage.goto('/register');
      await authPage.expectToBeOnRegisterPage();

      await authPage.fillRegistrationForm(TEST_USER);
      await authPage.submitRegistrationForm();

      // Should redirect to dashboard after successful registration
      await authPage.waitForAuthSuccess();
      await authPage.expectToBeOnDashboard();

      // Should display user information
      await expect(authPage.page.locator('[data-testid="user-name"]')).toContainText(
        `${TEST_USER.firstName} ${TEST_USER.lastName}`
      );
    });

    test('should show validation errors for invalid data', async () => {
      await authPage.goto('/register');

      // Submit empty form
      await authPage.submitRegistrationForm();

      // Should show validation errors
      await expect(authPage.page.locator('[data-testid="email-error"]')).toBeVisible();
      await expect(authPage.page.locator('[data-testid="password-error"]')).toBeVisible();
      await expect(authPage.page.locator('[data-testid="first-name-error"]')).toBeVisible();
    });

    test('should show error for duplicate email', async () => {
      await authPage.goto('/register');

      // Try to register with existing email
      await authPage.fillRegistrationForm({
        ...TEST_USER,
        email: EXISTING_USER.email,
      });
      await authPage.submitRegistrationForm();

      await authPage.waitForAuthError();
      await authPage.expectErrorMessage('email already exists');
    });

    test('should show error for password mismatch', async () => {
      await authPage.goto('/register');

      await authPage.fillRegistrationForm(TEST_USER);
      
      // Change password confirmation to create mismatch
      await authPage.page.fill('[data-testid="password2-input"]', 'DifferentPassword123!');
      await authPage.submitRegistrationForm();

      await expect(authPage.page.locator('[data-testid="password2-error"]')).toContainText(/passwords.*match/i);
    });

    test('should validate password strength', async () => {
      await authPage.goto('/register');

      await authPage.fillRegistrationForm({
        ...TEST_USER,
        password: 'weak',
      });
      await authPage.page.fill('[data-testid="password2-input"]', 'weak');
      await authPage.submitRegistrationForm();

      await expect(authPage.page.locator('[data-testid="password-error"]')).toContainText(/password.*requirements/i);
    });
  });

  test.describe('User Login', () => {
    test('should login existing user successfully', async () => {
      await authPage.goto('/login');
      await authPage.expectToBeOnLoginPage();

      await authPage.fillLoginForm(EXISTING_USER.email, EXISTING_USER.password);
      await authPage.submitLoginForm();

      await authPage.waitForAuthSuccess();
      await authPage.expectToBeOnDashboard();
    });

    test('should show error for invalid credentials', async () => {
      await authPage.goto('/login');

      await authPage.fillLoginForm('invalid@example.com', 'wrongpassword');
      await authPage.submitLoginForm();

      await authPage.waitForAuthError();
      await authPage.expectErrorMessage('Invalid credentials');
    });

    test('should show error for empty fields', async () => {
      await authPage.goto('/login');

      await authPage.submitLoginForm();

      await expect(authPage.page.locator('[data-testid="email-error"]')).toBeVisible();
      await expect(authPage.page.locator('[data-testid="password-error"]')).toBeVisible();
    });

    test('should handle non-existent user', async () => {
      await authPage.goto('/login');

      await authPage.fillLoginForm('nonexistent@example.com', 'somepassword');
      await authPage.submitLoginForm();

      await authPage.waitForAuthError();
      await authPage.expectErrorMessage('Invalid credentials');
    });
  });

  test.describe('Protected Routes', () => {
    test('should redirect to login when accessing protected route without auth', async () => {
      await authPage.goto('/dashboard');

      // Should redirect to login
      await authPage.expectToBeOnLoginPage();
    });

    test('should allow access to protected routes when authenticated', async () => {
      // First login
      await authPage.goto('/login');
      await authPage.fillLoginForm(EXISTING_USER.email, EXISTING_USER.password);
      await authPage.submitLoginForm();
      await authPage.waitForAuthSuccess();

      // Now access protected route
      await authPage.goto('/dashboard/settings');
      await expect(authPage.page).toHaveURL(/.*\/dashboard\/settings/);
    });

    test('should maintain authentication across page reloads', async () => {
      // First login
      await authPage.goto('/login');
      await authPage.fillLoginForm(EXISTING_USER.email, EXISTING_USER.password);
      await authPage.submitLoginForm();
      await authPage.waitForAuthSuccess();

      // Reload the page
      await authPage.page.reload();

      // Should still be authenticated
      await authPage.expectToBeOnDashboard();
    });
  });

  test.describe('Logout', () => {
    test('should logout user successfully', async () => {
      // First login
      await authPage.goto('/login');
      await authPage.fillLoginForm(EXISTING_USER.email, EXISTING_USER.password);
      await authPage.submitLoginForm();
      await authPage.waitForAuthSuccess();

      // Then logout
      await authPage.logout();

      // Should redirect to login page
      await authPage.expectToBeOnLoginPage();

      // Should not be able to access protected routes
      await authPage.goto('/dashboard');
      await authPage.expectToBeOnLoginPage();
    });

    test('should clear authentication state on logout', async () => {
      // Login first
      await authPage.goto('/login');
      await authPage.fillLoginForm(EXISTING_USER.email, EXISTING_USER.password);
      await authPage.submitLoginForm();
      await authPage.waitForAuthSuccess();

      // Verify we're authenticated
      await expect(authPage.page.locator('[data-testid="user-menu"]')).toBeVisible();

      // Logout
      await authPage.logout();

      // Go to login page and verify no auto-login occurs
      await authPage.goto('/login');
      await authPage.expectToBeOnLoginPage();
    });
  });

  test.describe('Password Reset', () => {
    test('should initiate password reset flow', async () => {
      await authPage.goto('/forgot-password');

      await authPage.page.fill('[data-testid="email-input"]', EXISTING_USER.email);
      await authPage.page.click('[data-testid="reset-submit"]');

      // Should show success message
      await expect(authPage.page.locator('[data-testid="success-message"]')).toContainText(
        /reset link.*sent/i
      );
    });

    test('should handle non-existent email in password reset', async () => {
      await authPage.goto('/forgot-password');

      await authPage.page.fill('[data-testid="email-input"]', 'nonexistent@example.com');
      await authPage.page.click('[data-testid="reset-submit"]');

      await expect(authPage.page.locator('[data-testid="error-message"]')).toContainText(
        /email.*not.*found/i
      );
    });
  });

  test.describe('Email Verification', () => {
    test('should show email verification required message', async () => {
      // Register a new user (they start unverified)
      await authPage.goto('/register');
      const unverifiedUser = {
        ...TEST_USER,
        email: `unverified.${Date.now()}@example.com`,
      };
      
      await authPage.fillRegistrationForm(unverifiedUser);
      await authPage.submitRegistrationForm();

      // Should show verification required message
      await expect(authPage.page.locator('[data-testid="verification-banner"]')).toContainText(
        /verify.*email/i
      );
    });

    test('should allow resending verification email', async () => {
      // Register and go to dashboard with unverified email
      await authPage.goto('/register');
      const unverifiedUser = {
        ...TEST_USER,
        email: `resend.${Date.now()}@example.com`,
      };
      
      await authPage.fillRegistrationForm(unverifiedUser);
      await authPage.submitRegistrationForm();

      // Click resend verification
      await authPage.page.click('[data-testid="resend-verification"]');

      // Should show success message
      await expect(authPage.page.locator('[data-testid="success-message"]')).toContainText(
        /verification.*sent/i
      );
    });
  });

  test.describe('Session Management', () => {
    test('should handle session expiration', async () => {
      // Login first
      await authPage.goto('/login');
      await authPage.fillLoginForm(EXISTING_USER.email, EXISTING_USER.password);
      await authPage.submitLoginForm();
      await authPage.waitForAuthSuccess();

      // Simulate session expiration by clearing cookies
      await authPage.page.context().clearCookies();

      // Try to access a protected resource
      await authPage.goto('/dashboard/settings');

      // Should redirect to login due to expired session
      await authPage.expectToBeOnLoginPage();
    });

    test('should handle token refresh automatically', async () => {
      // This test would require mocking token expiration times
      // For now, we'll test that the app continues to work over time
      
      await authPage.goto('/login');
      await authPage.fillLoginForm(EXISTING_USER.email, EXISTING_USER.password);
      await authPage.submitLoginForm();
      await authPage.waitForAuthSuccess();

      // Wait a bit and make sure we're still authenticated
      await authPage.page.waitForTimeout(2000);
      
      // Access another protected route
      await authPage.goto('/dashboard/reports');
      await expect(authPage.page).toHaveURL(/.*\/dashboard\/reports/);
    });
  });

  test.describe('Navigation and UI', () => {
    test('should navigate between auth pages', async () => {
      await authPage.goto('/login');
      await authPage.expectToBeOnLoginPage();

      // Go to register page
      await authPage.page.click('[data-testid="register-link"]');
      await authPage.expectToBeOnRegisterPage();

      // Go back to login page
      await authPage.page.click('[data-testid="login-link"]');
      await authPage.expectToBeOnLoginPage();
    });

    test('should show loading states during authentication', async () => {
      await authPage.goto('/login');

      await authPage.fillLoginForm(EXISTING_USER.email, EXISTING_USER.password);
      
      // Click submit and immediately check for loading state
      await authPage.page.click('[data-testid="login-submit"]');
      
      // Should show loading state briefly
      await expect(authPage.page.locator('[data-testid="login-submit"]')).toContainText(/loading|signing/i);
    });

    test('should display form validation errors inline', async () => {
      await authPage.goto('/register');

      // Fill invalid email
      await authPage.page.fill('[data-testid="email-input"]', 'invalid-email');
      await authPage.page.fill('[data-testid="password-input"]', 'short');
      
      // Move focus away to trigger validation
      await authPage.page.click('[data-testid="first-name-input"]');

      // Should show inline validation errors
      await expect(authPage.page.locator('[data-testid="email-error"]')).toContainText(/invalid.*email/i);
      await expect(authPage.page.locator('[data-testid="password-error"]')).toContainText(/password.*requirements/i);
    });
  });

  test.describe('Security Features', () => {
    test('should handle CSRF protection', async () => {
      // This test verifies that the frontend properly handles CSRF tokens
      await authPage.goto('/login');
      
      // The login should work normally (CSRF handled automatically)
      await authPage.fillLoginForm(EXISTING_USER.email, EXISTING_USER.password);
      await authPage.submitLoginForm();
      await authPage.waitForAuthSuccess();
    });

    test('should handle rate limiting gracefully', async () => {
      await authPage.goto('/login');

      // Make multiple rapid failed login attempts
      for (let i = 0; i < 6; i++) {
        await authPage.fillLoginForm('test@example.com', 'wrongpassword');
        await authPage.submitLoginForm();
        
        if (i < 4) {
          await authPage.waitForAuthError();
        }
      }

      // Should show rate limiting message
      await expect(authPage.page.locator('[data-testid="error-message"]')).toContainText(
        /too many attempts|rate limit|try again later/i
      );
    });

    test('should secure password inputs', async () => {
      await authPage.goto('/login');

      const passwordInput = authPage.page.locator('[data-testid="password-input"]');
      
      // Password input should have type="password"
      await expect(passwordInput).toHaveAttribute('type', 'password');
      
      // Should not be visible in the input
      await passwordInput.fill('secretpassword');
      const inputValue = await passwordInput.inputValue();
      expect(inputValue).toBe('secretpassword'); // Value is there but visually hidden
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper form labels and ARIA attributes', async () => {
      await authPage.goto('/login');

      // Check for proper labeling
      await expect(authPage.page.locator('label[for="email"]')).toBeVisible();
      await expect(authPage.page.locator('label[for="password"]')).toBeVisible();

      // Check for ARIA attributes
      const emailInput = authPage.page.locator('[data-testid="email-input"]');
      await expect(emailInput).toHaveAttribute('aria-label');
    });

    test('should support keyboard navigation', async () => {
      await authPage.goto('/login');

      // Should be able to navigate with Tab key
      await authPage.page.keyboard.press('Tab'); // Focus email input
      await authPage.page.keyboard.type(EXISTING_USER.email);
      
      await authPage.page.keyboard.press('Tab'); // Focus password input
      await authPage.page.keyboard.type(EXISTING_USER.password);
      
      await authPage.page.keyboard.press('Tab'); // Focus submit button
      await authPage.page.keyboard.press('Enter'); // Submit form

      await authPage.waitForAuthSuccess();
    });

    test('should announce errors to screen readers', async () => {
      await authPage.goto('/login');

      await authPage.submitLoginForm(); // Submit empty form

      // Error messages should have proper ARIA attributes
      const errorMessage = authPage.page.locator('[data-testid="error-message"]');
      await expect(errorMessage).toHaveAttribute('role', 'alert');
    });
  });

  test.describe('Error Handling', () => {
    test('should handle network errors gracefully', async () => {
      // Simulate network error by blocking API requests
      await authPage.page.route(`${API_URL}/api/auth/login/`, (route) => {
        route.abort('failed');
      });

      await authPage.goto('/login');
      await authPage.fillLoginForm(EXISTING_USER.email, EXISTING_USER.password);
      await authPage.submitLoginForm();

      // Should show network error message
      await expect(authPage.page.locator('[data-testid="error-message"]')).toContainText(
        /network.*error|connection.*failed/i
      );
    });

    test('should handle server errors gracefully', async () => {
      // Mock server error response
      await authPage.page.route(`${API_URL}/api/auth/login/`, (route) => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal server error' }),
        });
      });

      await authPage.goto('/login');
      await authPage.fillLoginForm(EXISTING_USER.email, EXISTING_USER.password);
      await authPage.submitLoginForm();

      // Should show server error message
      await expect(authPage.page.locator('[data-testid="error-message"]')).toContainText(
        /server.*error|try.*again.*later/i
      );
    });

    test('should recover from errors after correction', async () => {
      await authPage.goto('/login');

      // First attempt with wrong password
      await authPage.fillLoginForm(EXISTING_USER.email, 'wrongpassword');
      await authPage.submitLoginForm();
      await authPage.waitForAuthError();

      // Clear error and try again with correct password
      await authPage.page.fill('[data-testid="password-input"]', '');
      await authPage.page.fill('[data-testid="password-input"]', EXISTING_USER.password);
      await authPage.submitLoginForm();

      // Should succeed this time
      await authPage.waitForAuthSuccess();
    });
  });
});