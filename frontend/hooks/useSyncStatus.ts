import { useState, useEffect, useCallback, useRef } from 'react';
import { bankingService } from '@/services/banking.service';

export type SyncStatus = {
  isPolling: boolean;
  status: string | null;
  executionStatus: string | null;
  message: string;
  isComplete: boolean;
  hasError: boolean;
  errorMessage?: string;
};

const POLLING_INTERVAL = 3000; // 3 seconds
const MAX_POLLING_TIME = 180000; // 3 minutes timeout (webhooks can take time)

const getProgressMessage = (
  executionStatus: string | null,
  status: string | null,
  elapsedTime?: number
): string => {
  // Map execution status to user-friendly messages
  const executionMessages: Record<string, string> = {
    'LOGIN_IN_PROGRESS': 'Conectando ao banco...',
    'ACCOUNTS_IN_PROGRESS': 'Carregando contas...',
    'TRANSACTIONS_IN_PROGRESS': 'Sincronizando transações... Isso pode levar alguns minutos.',
    'SUCCESS': 'Sincronização concluída com sucesso!',
    'PARTIAL_SUCCESS': 'Sincronização parcialmente concluída',
    'ERROR': 'Erro na sincronização',
    'INVALID_CREDENTIALS': 'Credenciais inválidas',
  };

  if (executionStatus && executionMessages[executionStatus]) {
    return executionMessages[executionStatus];
  }

  // Fallback to status-based messages
  const statusMessages: Record<string, string> = {
    'UPDATING': elapsedTime && elapsedTime > 30000
      ? 'Aguardando dados do banco... Isso pode demorar alguns minutos.'
      : 'Sincronizando dados...',
    'UPDATED': 'Sincronização concluída!',
    'LOGIN_ERROR': 'Erro no login - verifique suas credenciais',
    'WAITING_USER_INPUT': 'Aguardando autenticação adicional',
    'OUTDATED': 'Dados desatualizados - tente sincronizar novamente',
    'ERROR': 'Erro na sincronização',
  };

  if (status && statusMessages[status]) {
    return statusMessages[status];
  }

  return 'Processando...';
};

export const useSyncStatus = (connectionId: string | null) => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({
    isPolling: false,
    status: null,
    executionStatus: null,
    message: '',
    isComplete: false,
    hasError: false,
  });

  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);

  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    setSyncStatus(prev => ({ ...prev, isPolling: false }));
  }, []);

  const checkStatus = useCallback(async () => {
    if (!connectionId) {
      return;
    }

    try {
      const statusResponse = await bankingService.checkConnectionStatus(connectionId);
      const elapsed = Date.now() - startTimeRef.current;

      const message = getProgressMessage(
        statusResponse.execution_status,
        statusResponse.status,
        elapsed
      );
      const isComplete = statusResponse.sync_complete;
      const hasError = statusResponse.requires_action ||
                       ['ERROR', 'LOGIN_ERROR'].includes(statusResponse.status);

      setSyncStatus({
        isPolling: !isComplete && !hasError,
        status: statusResponse.status,
        executionStatus: statusResponse.execution_status,
        message,
        isComplete,
        hasError,
        errorMessage: statusResponse.error_message,
      });

      // Stop polling if complete or error
      if (isComplete || hasError) {
        stopPolling();
        return true; // Indicates polling should stop
      }

      // Check for timeout
      if (elapsed >= MAX_POLLING_TIME) {
        setSyncStatus(prev => ({
          ...prev,
          isPolling: false,
          hasError: true,
          message: 'A sincronização está demorando mais que o esperado. Aguarde alguns minutos e recarregue a página, ou tente novamente mais tarde.',
          errorMessage: 'Os dados podem estar sendo processados. Verifique novamente em alguns minutos.',
        }));
        stopPolling();
        return true;
      }

      return false; // Continue polling
    } catch (error) {
      console.error('[useSyncStatus] Error checking sync status:', error);
      setSyncStatus(prev => ({
        ...prev,
        isPolling: false,
        hasError: true,
        message: 'Erro ao verificar status da sincronização',
        errorMessage: 'Tente recarregar a página ou sincronizar novamente.',
      }));
      stopPolling();
      return true;
    }
  }, [connectionId, stopPolling]);

  const startPolling = useCallback((explicitConnectionId?: string) => {
    const targetConnectionId = explicitConnectionId || connectionId;

    if (!targetConnectionId) {
      return;
    }

    // Stop any existing polling first
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    // Initialize
    startTimeRef.current = Date.now();
    setSyncStatus({
      isPolling: true,
      status: 'UPDATING',
      executionStatus: null,
      message: 'Iniciando sincronização...',
      isComplete: false,
      hasError: false,
    });

    // Check immediately (use targetConnectionId directly to avoid closure issues)
    const checkStatusNow = async () => {
      try {
        const statusResponse = await bankingService.checkConnectionStatus(targetConnectionId);
        const elapsed = Date.now() - startTimeRef.current;

        const message = getProgressMessage(
          statusResponse.execution_status,
          statusResponse.status,
          elapsed
        );
        const isComplete = statusResponse.sync_complete;
        const hasError = statusResponse.requires_action ||
                         ['ERROR', 'LOGIN_ERROR'].includes(statusResponse.status);

        setSyncStatus({
          isPolling: !isComplete && !hasError,
          status: statusResponse.status,
          executionStatus: statusResponse.execution_status,
          message,
          isComplete,
          hasError,
          errorMessage: statusResponse.error_message,
        });

        // Check for timeout
        if (elapsed >= MAX_POLLING_TIME) {
          setSyncStatus(prev => ({
            ...prev,
            isPolling: false,
            hasError: true,
            message: 'A sincronização está demorando mais que o esperado. Aguarde alguns minutos e recarregue a página, ou tente novamente mais tarde.',
            errorMessage: 'Os dados podem estar sendo processados. Verifique novamente em alguns minutos.',
          }));
          return true;
        }

        return isComplete || hasError;
      } catch (error) {
        console.error('[useSyncStatus] Error in checkStatusNow:', error);
        setSyncStatus(prev => ({
          ...prev,
          isPolling: false,
          hasError: true,
          message: 'Erro ao verificar status da sincronização',
          errorMessage: 'Tente recarregar a página ou sincronizar novamente.',
        }));
        return true;
      }
    };

    checkStatusNow();

    // Then poll every interval using checkStatusNow
    pollingIntervalRef.current = setInterval(async () => {
      const shouldStop = await checkStatusNow();
      if (shouldStop) {
        stopPolling();
      }
    }, POLLING_INTERVAL);
  }, [connectionId, stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  // Auto-start polling when connectionId changes
  useEffect(() => {
    // If we have a connectionId but no polling is active, something went wrong
    if (connectionId && !pollingIntervalRef.current) {
      console.warn('[useSyncStatus] Have connectionId but no polling! This should not happen.');
    }
  }, [connectionId]);

  return {
    syncStatus,
    startPolling,
    stopPolling,
  };
};
