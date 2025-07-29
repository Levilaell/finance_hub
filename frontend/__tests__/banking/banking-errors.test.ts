/**
 * Tests for banking error handling utilities
 */
import { BankingErrorHandler, BankingError } from '@/utils/banking-errors';

describe('BankingErrorHandler', () => {
  describe('getErrorDisplay', () => {
    it('should handle invalid credentials error', () => {
      const error: BankingError = {
        code: 'invalid_credentials',
        message: 'Suas credenciais estão incorretas',
      };

      const display = BankingErrorHandler.getErrorDisplay(error);

      expect(display.title).toBe('Credenciais Inválidas');
      expect(display.action?.type).toBe('reconnect');
      expect(display.severity).toBe('error');
    });

    it('should handle MFA required error', () => {
      const error: BankingError = {
        code: 'mfa_required',
        message: 'Verificação adicional necessária',
      };

      const display = BankingErrorHandler.getErrorDisplay(error);

      expect(display.title).toBe('Verificação Necessária');
      expect(display.action?.type).toBe('reconnect');
      expect(display.severity).toBe('warning');
    });

    it('should handle rate limit error', () => {
      const error: BankingError = {
        code: 'rate_limit_exceeded',
        message: 'Muitas tentativas',
        retry_after: 300,
      };

      const display = BankingErrorHandler.getErrorDisplay(error);

      expect(display.title).toBe('Limite de Requisições');
      expect(display.action?.type).toBe('wait');
      expect(display.severity).toBe('warning');
    });

    it('should handle unknown error', () => {
      const error: BankingError = {
        code: 'unknown_error',
        message: 'Something went wrong',
      };

      const display = BankingErrorHandler.getErrorDisplay(error);

      expect(display.title).toBe('Erro');
      expect(display.action?.type).toBe('contact_support');
      expect(display.severity).toBe('error');
    });
  });

  describe('requiresReconnection', () => {
    it('should return true for credential errors', () => {
      const error: BankingError = {
        code: 'invalid_credentials',
        message: 'Invalid credentials',
      };

      expect(BankingErrorHandler.requiresReconnection(error)).toBe(true);
    });

    it('should return true for MFA errors', () => {
      const error: BankingError = {
        code: 'mfa_required',
        message: 'MFA required',
      };

      expect(BankingErrorHandler.requiresReconnection(error)).toBe(true);
    });

    it('should return false for other errors', () => {
      const error: BankingError = {
        code: 'sync_error',
        message: 'Sync failed',
      };

      expect(BankingErrorHandler.requiresReconnection(error)).toBe(false);
    });
  });

  describe('getRetryDelay', () => {
    it('should return custom retry delay', () => {
      const error: BankingError = {
        code: 'rate_limit_exceeded',
        message: 'Rate limited',
        retry_after: 600,
      };

      expect(BankingErrorHandler.getRetryDelay(error)).toBe(600000);
    });

    it('should return default delay for rate limit', () => {
      const error: BankingError = {
        code: 'rate_limit_exceeded',
        message: 'Rate limited',
      };

      expect(BankingErrorHandler.getRetryDelay(error)).toBe(300000); // 5 minutes
    });

    it('should return default delay for institution unavailable', () => {
      const error: BankingError = {
        code: 'institution_unavailable',
        message: 'Bank unavailable',
      };

      expect(BankingErrorHandler.getRetryDelay(error)).toBe(1800000); // 30 minutes
    });

    it('should return default delay for unknown errors', () => {
      const error: BankingError = {
        code: 'unknown',
        message: 'Unknown error',
      };

      expect(BankingErrorHandler.getRetryDelay(error)).toBe(30000); // 30 seconds
    });
  });

  describe('formatForToast', () => {
    it('should format error for toast notification', () => {
      const error: BankingError = {
        code: 'invalid_credentials',
        message: 'Invalid credentials',
      };

      const toast = BankingErrorHandler.formatForToast(error);

      expect(toast.title).toBe('Credenciais Inválidas');
      expect(toast.variant).toBe('destructive');
    });

    it('should use default variant for warnings', () => {
      const error: BankingError = {
        code: 'rate_limit_exceeded',
        message: 'Rate limited',
      };

      const toast = BankingErrorHandler.formatForToast(error);

      expect(toast.title).toBe('Limite de Requisições');
      expect(toast.variant).toBe('default');
    });
  });

  describe('parseApiError', () => {
    it('should parse structured error response', () => {
      const response = {
        error: {
          code: 'invalid_credentials',
          message: 'Invalid credentials',
          type: 'InvalidCredentialsError',
        },
      };

      const error = BankingErrorHandler.parseApiError(response);

      expect(error.code).toBe('invalid_credentials');
      expect(error.message).toBe('Invalid credentials');
      expect(error.type).toBe('InvalidCredentialsError');
    });

    it('should parse simple error message', () => {
      const response = {
        error: 'Something went wrong',
      };

      const error = BankingErrorHandler.parseApiError(response);

      expect(error.code).toBe('unknown_error');
      expect(error.message).toBe('Something went wrong');
    });

    it('should parse axios error response', () => {
      const response = {
        response: {
          data: {
            error: {
              code: 'sync_error',
              message: 'Sync failed',
            },
          },
        },
      };

      const error = BankingErrorHandler.parseApiError(response);

      expect(error.code).toBe('sync_error');
      expect(error.message).toBe('Sync failed');
    });

    it('should return default error for invalid input', () => {
      const error = BankingErrorHandler.parseApiError(null);

      expect(error.code).toBe('unknown_error');
      expect(error.message).toBe('Ocorreu um erro inesperado. Por favor, tente novamente.');
    });
  });

  describe('getHelpSteps', () => {
    it('should return custom help steps', () => {
      const error: BankingError = {
        code: 'invalid_credentials',
        message: 'Invalid credentials',
        help: {
          steps: ['Step 1', 'Step 2', 'Step 3'],
        },
      };

      const steps = BankingErrorHandler.getHelpSteps(error);

      expect(steps).toEqual(['Step 1', 'Step 2', 'Step 3']);
    });

    it('should return default help steps for credential errors', () => {
      const error: BankingError = {
        code: 'invalid_credentials',
        message: 'Invalid credentials',
      };

      const steps = BankingErrorHandler.getHelpSteps(error);

      expect(steps).toHaveLength(3);
      expect(steps[0]).toContain('Reconectar');
    });

    it('should return default help steps for unknown errors', () => {
      const error: BankingError = {
        code: 'unknown',
        message: 'Unknown error',
      };

      const steps = BankingErrorHandler.getHelpSteps(error);

      expect(steps).toHaveLength(2);
      expect(steps[1]).toContain('suporte');
    });
  });
});