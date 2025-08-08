/**
 * Banking error handling utilities
 */

export interface BankingError {
  code: string;
  message: string;
  type?: string;
  item_id?: string;
  account_id?: string;
  action_required?: string;
  retry_after?: number;
  help?: {
    documentation?: string;
    support?: string;
    steps?: string[];
    suggestion?: string;
  };
}

export class BankingErrorHandler {
  /**
   * Get user-friendly error message and action
   */
  static getErrorDisplay(error: BankingError): {
    title: string;
    message: string;
    action?: {
      label: string;
      type: 'reconnect' | 'retry' | 'contact_support' | 'wait';
    };
    severity: 'error' | 'warning' | 'info';
  } {
    switch (error.code) {
      case 'invalid_credentials':
        return {
          title: 'Credenciais Inválidas',
          message: error.message || 'Suas credenciais bancárias estão incorretas.',
          action: {
            label: 'Reconectar Conta',
            type: 'reconnect',
          },
          severity: 'error',
        };

      case 'mfa_required':
        return {
          title: 'Verificação Necessária',
          message: error.message || 'Seu banco está solicitando verificação adicional.',
          action: {
            label: 'Completar Verificação',
            type: 'reconnect',
          },
          severity: 'warning',
        };

      case 'rate_limit_exceeded':
        return {
          title: 'Limite de Requisições',
          message: error.message || 'Muitas tentativas. Por favor, aguarde.',
          action: {
            label: 'Tentar Novamente',
            type: 'wait',
          },
          severity: 'warning',
        };

      case 'institution_unavailable':
        return {
          title: 'Banco Indisponível',
          message: error.message || 'O banco está temporariamente indisponível.',
          action: {
            label: 'Tentar Mais Tarde',
            type: 'retry',
          },
          severity: 'warning',
        };

      case 'sync_error':
        return {
          title: 'Erro de Sincronização',
          message: error.message || 'Não foi possível sincronizar seus dados.',
          action: {
            label: 'Tentar Novamente',
            type: 'retry',
          },
          severity: 'error',
        };

      case 'account_not_found':
        return {
          title: 'Conta Não Encontrada',
          message: error.message || 'A conta bancária não foi encontrada.',
          severity: 'error',
        };

      case 'pluggy_connection_error':
        return {
          title: 'Erro de Conexão',
          message: error.message || 'Não foi possível conectar ao serviço bancário.',
          action: {
            label: 'Tentar Novamente',
            type: 'retry',
          },
          severity: 'error',
        };

      default:
        return {
          title: 'Erro',
          message: error.message || 'Ocorreu um erro inesperado.',
          action: {
            label: 'Contatar Suporte',
            type: 'contact_support',
          },
          severity: 'error',
        };
    }
  }

  /**
   * Check if error requires reconnection
   */
  static requiresReconnection(error: BankingError): boolean {
    return ['invalid_credentials', 'mfa_required'].includes(error.code);
  }

  /**
   * Get retry delay in milliseconds
   */
  static getRetryDelay(error: BankingError): number {
    if (error.retry_after) {
      return error.retry_after * 1000; // Convert to milliseconds
    }

    // Default retry delays by error type
    switch (error.code) {
      case 'rate_limit_exceeded':
        return 5 * 60 * 1000; // 5 minutes
      case 'institution_unavailable':
        return 30 * 60 * 1000; // 30 minutes
      case 'sync_error':
        return 1 * 60 * 1000; // 1 minute
      default:
        return 30 * 1000; // 30 seconds
    }
  }

  /**
   * Format error for toast notification
   */
  static formatForToast(error: BankingError): {
    title: string;
    description: string;
    variant: 'default' | 'destructive';
  } {
    const display = this.getErrorDisplay(error);
    
    return {
      title: display.title,
      description: display.message,
      variant: display.severity === 'error' ? 'destructive' : 'default',
    };
  }

  /**
   * Get help steps for error
   */
  static getHelpSteps(error: BankingError): string[] {
    if (error.help?.steps) {
      return error.help.steps;
    }

    // Default help steps by error type
    switch (error.code) {
      case 'invalid_credentials':
        return [
          'Clique em "Reconectar" ao lado do seu banco',
          'Digite suas credenciais atualizadas',
          'Complete qualquer etapa de segurança solicitada',
        ];

      case 'mfa_required':
        return [
          'Verifique seu celular ou email para o código',
          'Clique em "Inserir código" ao lado do banco',
          'Digite o código de verificação',
        ];

      case 'rate_limit_exceeded':
        return [
          'Aguarde alguns minutos',
          'Tente sincronizar novamente',
          'Se o problema persistir, contate o suporte',
        ];

      default:
        return [
          'Tente a operação novamente',
          'Se o erro persistir, contate nosso suporte',
        ];
    }
  }

  /**
   * Parse error from API response
   */
  static parseApiError(response: any): BankingError {
    // Handle structured error response
    if (response?.error && typeof response.error === 'object') {
      return response.error as BankingError;
    }

    // Handle simple error message
    if (response?.error && typeof response.error === 'string') {
      return {
        code: 'unknown_error',
        message: response.error,
      };
    }

    // Handle axios error response
    if (response?.response?.data?.error) {
      return this.parseApiError(response.response.data);
    }

    // Default error
    return {
      code: 'unknown_error',
      message: 'Ocorreu um erro inesperado. Por favor, tente novamente.',
    };
  }
}