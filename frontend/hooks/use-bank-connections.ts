// Hook for managing bank connections

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { bankingService } from '@/services/banking.service';
import type { PluggyItem } from '@/types/banking.types';

export function useBankConnections() {
  const queryClient = useQueryClient();
  const [selectedConnection, setSelectedConnection] = useState<string | null>(null);

  // Fetch all connections
  const {
    data: connections,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['bankConnections'],
    queryFn: async () => {
      const response = await bankingService.getItems();
      return response.results || [];
    },
    staleTime: 60 * 1000, // 1 minute
  });

  // Create connection from item
  const createConnection = useMutation({
    mutationFn: async (data: any) => {
      // Placeholder - this method doesn't exist in the service yet
      return {};
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['bankConnections'] });
      queryClient.invalidateQueries({ queryKey: ['accountSummary'] });
      toast.success('Conta conectada com sucesso!');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Erro ao conectar conta');
    }
  });

  // Sync connection
  const syncConnection = useMutation({
    mutationFn: async (connectionId: string) => {
      return bankingService.syncItem(connectionId);
    },
    onSuccess: (data, connectionId) => {
      queryClient.invalidateQueries({ queryKey: ['bankConnections'] });
      queryClient.invalidateQueries({ queryKey: ['bankConnection', connectionId] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      toast.success('Sincronização iniciada');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Erro ao sincronizar');
    }
  });

  // Delete connection
  const deleteConnection = useMutation({
    mutationFn: async (connectionId: string) => {
      return bankingService.disconnectItem(connectionId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bankConnections'] });
      queryClient.invalidateQueries({ queryKey: ['accountSummary'] });
      toast.success('Conexão removida com sucesso');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Erro ao remover conexão');
    }
  });

  // Get connection by ID
  const getConnectionById = useCallback((id: string): PluggyItem | undefined => {
    return connections?.find(conn => conn.id === id);
  }, [connections]);

  // Check if any connection needs attention
  const hasConnectionErrors = useCallback(() => {
    return connections?.some(conn => 
      conn.status === 'LOGIN_ERROR' || 
      conn.status === 'ERROR' ||
      conn.status === 'WAITING_USER_INPUT'
    ) || false;
  }, [connections]);

  // Get connections that need sync
  const getConnectionsNeedingSync = useCallback(() => {
    return connections?.filter(conn => 
      conn.status === 'OUTDATED' || 
      (conn.next_auto_sync_at && new Date(conn.next_auto_sync_at) < new Date())
    ) || [];
  }, [connections]);

  return {
    // Data
    connections: connections || [],
    selectedConnection,
    isLoading,
    error,

    // Actions
    createConnection: createConnection.mutate,
    syncConnection: syncConnection.mutate,
    deleteConnection: deleteConnection.mutate,
    setSelectedConnection,
    refetch,

    // Utilities
    getConnectionById,
    hasConnectionErrors,
    getConnectionsNeedingSync,

    // Loading states
    isCreating: createConnection.isPending,
    isSyncing: syncConnection.isPending,
    isDeleting: deleteConnection.isPending,
  };
}