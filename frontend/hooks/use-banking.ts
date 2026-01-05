/**
 * Banking Hook - State management for banking features
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { bankingService } from '@/services/banking.service';
import {
  BankConnection,
  BankAccount,
  Transaction,
  Connector,
  FinancialSummary,
  TransactionFilter,
} from '@/types/banking';
import { toast } from 'sonner';

// Query Keys
const QUERY_KEYS = {
  accounts: ['banking', 'accounts'],
  connections: ['banking', 'connections'],
  connectors: ['banking', 'connectors'],
  transactions: (filter?: TransactionFilter) => ['banking', 'transactions', filter],
  summary: (dateFrom?: string, dateTo?: string) => ['banking', 'summary', dateFrom, dateTo],
  categories: (dateFrom?: string, dateTo?: string) => ['banking', 'categories', dateFrom, dateTo],
};

/**
 * Hook for managing bank accounts
 */
export function useBankAccounts() {
  const queryClient = useQueryClient();

  const {
    data: accounts = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: QUERY_KEYS.accounts,
    queryFn: bankingService.getAccounts,
  });

  const syncAccountMutation = useMutation({
    mutationFn: (accountId: string) =>
      bankingService.syncAccountTransactions(accountId),
    onSuccess: () => {
      toast.success('Transações sincronizadas com sucesso!');
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.accounts });
      queryClient.invalidateQueries({ queryKey: ['banking', 'transactions'] });
    },
    onError: () => {
      toast.error('Erro ao sincronizar transações');
    },
  });

  return {
    accounts,
    isLoading,
    error,
    refetch,
    syncAccount: syncAccountMutation.mutate,
    isSyncing: syncAccountMutation.isPending,
  };
}

/**
 * Hook for managing bank connections
 */
export function useBankConnections() {
  const queryClient = useQueryClient();

  const {
    data: connections = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: QUERY_KEYS.connections,
    queryFn: bankingService.getConnections,
  });

  const createConnectionMutation = useMutation({
    mutationFn: bankingService.createConnection,
    onSuccess: () => {
      toast.success('Banco conectado com sucesso!');
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.connections });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.accounts });
    },
    onError: () => {
      toast.error('Erro ao conectar banco');
    },
  });

  const deleteConnectionMutation = useMutation({
    mutationFn: bankingService.deleteConnection,
    onSuccess: () => {
      toast.success('Banco desconectado');
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.connections });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.accounts });
    },
    onError: () => {
      toast.error('Erro ao desconectar banco');
    },
  });

  const syncConnectionMutation = useMutation({
    mutationFn: (connectionId: string) =>
      bankingService.syncConnectionTransactions(connectionId),
    onSuccess: () => {
      toast.success('Conexão sincronizada!');
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.connections });
      queryClient.invalidateQueries({ queryKey: ['banking'] });
    },
    onError: () => {
      toast.error('Erro ao sincronizar conexão');
    },
  });

  const syncAllConnections = useCallback(async () => {
    for (const connection of connections) {
      await syncConnectionMutation.mutateAsync(connection.id);
    }
  }, [connections]);

  return {
    connections,
    isLoading,
    error,
    refetch,
    createConnection: createConnectionMutation.mutate,
    deleteConnection: deleteConnectionMutation.mutate,
    syncConnection: syncConnectionMutation.mutate,
    syncAllConnections,
    isCreating: createConnectionMutation.isPending,
    isDeleting: deleteConnectionMutation.isPending,
    isSyncing: syncConnectionMutation.isPending,
  };
}

/**
 * Hook for managing transactions
 */
export function useTransactions(filter?: TransactionFilter) {
  const {
    data: transactions = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: QUERY_KEYS.transactions(filter),
    queryFn: () => bankingService.getTransactions(filter),
  });

  return {
    transactions,
    isLoading,
    error,
    refetch,
  };
}

/**
 * Hook for financial summary
 */
export function useFinancialSummary(dateFrom?: string, dateTo?: string) {
  const {
    data: summary,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: QUERY_KEYS.summary(dateFrom, dateTo),
    queryFn: () => bankingService.getTransactionsSummary(dateFrom, dateTo),
  });

  const {
    data: categories,
    isLoading: isLoadingCategories,
  } = useQuery({
    queryKey: QUERY_KEYS.categories(dateFrom, dateTo),
    queryFn: () => bankingService.getTransactionsByCategory(dateFrom, dateTo),
  });

  return {
    summary,
    categories,
    isLoading: isLoading || isLoadingCategories,
    error,
    refetch,
  };
}

/**
 * Hook for bank connectors
 */
export function useBankConnectors() {
  const queryClient = useQueryClient();

  const {
    data: connectors = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: QUERY_KEYS.connectors,
    queryFn: () => bankingService.getConnectors(),
  });

  const syncConnectorsMutation = useMutation({
    mutationFn: bankingService.syncConnectors,
    onSuccess: () => {
      toast.success('Conectores sincronizados!');
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.connectors });
    },
    onError: () => {
      toast.error('Erro ao sincronizar conectores');
    },
  });

  return {
    connectors,
    isLoading,
    error,
    refetch,
    syncConnectors: syncConnectorsMutation.mutate,
    isSyncing: syncConnectorsMutation.isPending,
  };
}

/**
 * Hook for Pluggy Connect Token
 */
export function usePluggyConnect() {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchToken = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await bankingService.getConnectToken();
      setToken(response.token);
      return response.token;
    } catch (err) {
      const error = err as Error;
      setError(error);
      toast.error('Erro ao obter token de conexão');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!token) {
      fetchToken();
    }
  }, []);

  return {
    token,
    isLoading,
    error,
    refetchToken: fetchToken,
  };
}