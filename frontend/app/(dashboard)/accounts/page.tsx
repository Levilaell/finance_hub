'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

import { useAuthStore } from '@/store/auth-store';
import { bankingService } from '@/services/banking.service';
import { BankAccount, BankConnection } from '@/types/banking';
import { useSyncStatus } from '@/hooks/useSyncStatus';

import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { EmptyState } from '@/components/ui/empty-state';
import { BankAccountCard } from '@/components/banking/bank-account-card';
import { PluggyConnectWidget } from '@/components/banking/pluggy-connect-widget';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

import {
  CreditCardIcon,
  LinkIcon,
  DocumentChartBarIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

export default function AccountsPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuthStore();
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [connections, setConnections] = useState<BankConnection[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [showPluggyWidget, setShowPluggyWidget] = useState(false);
  const [connectToken, setConnectToken] = useState<string | null>(null);
  const [updateItemId, setUpdateItemId] = useState<string | null>(null);
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [accountToDelete, setAccountToDelete] = useState<BankAccount | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [syncingConnectionId, setSyncingConnectionId] = useState<string | null>(null);
  const { syncStatus, startPolling, stopPolling } = useSyncStatus(syncingConnectionId);

  // Check authentication
  useEffect(() => {
    if (!isAuthenticated && !authLoading) {
      router.push('/login');
      return;
    }
    if (isAuthenticated) {
      fetchData();
    }
  }, [isAuthenticated, authLoading, router]);

  // Handle sync status updates
  useEffect(() => {
    // Show initial toast when sync starts
    if (syncingConnectionId && !syncStatus.isPolling && !syncStatus.isComplete && !syncStatus.hasError) {
      toast.loading('Iniciando sincronização...', { id: 'sync-progress' });
      return;
    }

    if (!syncingConnectionId) {
      return;
    }

    if (syncStatus.isPolling) {
      // Update toast with current progress
      toast.loading(syncStatus.message, { id: 'sync-progress' });
    } else if (syncStatus.isComplete) {
      // Sync completed successfully
      toast.success(syncStatus.message, { id: 'sync-progress' });
      setSyncingConnectionId(null);

      // Reload data after a short delay to ensure backend has processed
      setTimeout(() => {
        fetchData();
      }, 1500);
    } else if (syncStatus.hasError) {
      // Sync failed
      toast.error(syncStatus.errorMessage || syncStatus.message, { id: 'sync-progress' });
      setSyncingConnectionId(null);
    }
  }, [syncStatus, syncingConnectionId]);

  // Fetch accounts and connections
  const fetchData = async () => {
    setIsLoadingData(true);
    try {
      const [accountsData, connectionsData] = await Promise.all([
        bankingService.getAccounts(),
        bankingService.getConnections(),
      ]);
      setAccounts(accountsData);
      setConnections(connectionsData);
    } catch (error) {
      console.error('Error fetching banking data:', error);
      toast.error('Erro ao carregar dados bancários');
    } finally {
      setIsLoadingData(false);
    }
  };

  // Connect new bank
  const handleConnectBank = async () => {
    try {
      const response = await bankingService.getConnectToken();
      setConnectToken(response.token);
      setShowPluggyWidget(true);
    } catch (error) {
      toast.error('Erro ao obter token de conexão');
      console.error(error);
    }
  };

  // Handle successful connection
  const handleConnectionSuccess = async (itemId: string) => {
    try {
      // Create the connection in our backend
      const payload = { pluggy_item_id: itemId };

      await bankingService.createConnection(payload);

      toast.success('Banco conectado com sucesso! Sincronizando dados...');

      // Close widget and refresh data
      setShowPluggyWidget(false);
      setConnectToken(null);

      // Wait a bit for initial sync then refresh
      setTimeout(async () => {
        await fetchData();
      }, 2000);
    } catch (error: any) {
      console.error('Error saving connection:', error);
      console.error('Error response:', error.response?.data);
      toast.error('Erro ao salvar conexão bancária');
    }
  };

  // Handle widget close
  const handleWidgetClose = () => {
    setShowPluggyWidget(false);
    setConnectToken(null);
    setUpdateItemId(null);
  };

  // Handle reconnection
  const handleReconnectAccount = async (connectionId: string) => {
    try {
      const response = await bankingService.getReconnectToken(connectionId);
      setConnectToken(response.token);
      setUpdateItemId(response.item_id);
      setShowPluggyWidget(true);
    } catch (error) {
      toast.error('Erro ao obter token de reconexão');
      console.error(error);
    }
  };

  // Handle successful reconnection
  const handleReconnectionSuccess = async (itemId: string) => {
    try {
      toast.success('Conta reconectada com sucesso! Atualizando dados...');

      // Close widget
      setShowPluggyWidget(false);
      setConnectToken(null);
      setUpdateItemId(null);

      // Wait a bit then refresh
      setTimeout(async () => {
        await fetchData();
      }, 2000);
    } catch (error: any) {
      console.error('Error after reconnection:', error);
      toast.error('Conta reconectada, mas houve erro ao atualizar dados');
    }
  };

  // Sync account transactions
  const handleSyncAccount = useCallback(async (accountId: string) => {
    try {
      // Find the connection for this account
      const account = accounts.find(a => a.id === accountId);
      if (!account) {
        toast.error('Conta não encontrada');
        return;
      }

      // Set syncing connection (this will trigger the useEffect to show initial toast)
      setSyncingConnectionId(account.connection_id);

      // Trigger sync
      const response = await bankingService.syncConnectionTransactions(account.connection_id);

      // Check if requires action (MFA, credentials, etc)
      if (response.requires_action) {
        toast.error('Ação necessária: verifique suas credenciais ou autenticação', { id: 'sync-progress' });
        setSyncingConnectionId(null);
        return;
      }

      // Check if sync was initiated or is already running
      const validStatuses = ['SYNC_TRIGGERED', 'ALREADY_SYNCING'];
      if (!validStatuses.includes(response.sync_status)) {
        toast.error(`Status inesperado: ${response.sync_status}`, { id: 'sync-progress' });
        setSyncingConnectionId(null);
        return;
      }

      // Start polling for status (works for both new syncs and already running syncs)
      // Pass connection ID explicitly to avoid race condition with setState
      startPolling(account.connection_id);

    } catch (error: any) {
      console.error('Error syncing account:', error);
      toast.error('Erro ao iniciar sincronização', { id: 'sync-progress' });
      setSyncingConnectionId(null);
    }
  }, [accounts, startPolling]);

  // Sync all connections
  const handleSyncAll = useCallback(async () => {
    if (connections.length === 0) return;

    try {
      // Sync first connection with polling
      const firstConnection = connections[0];
      setSyncingConnectionId(firstConnection.id);

      const response = await bankingService.syncConnectionTransactions(firstConnection.id);

      if (response.requires_action) {
        toast.error('Ação necessária: verifique suas credenciais', { id: 'sync-progress' });
        setSyncingConnectionId(null);
        return;
      }

      // Start polling for the first connection
      startPolling(firstConnection.id);

      // For subsequent connections, trigger sync without waiting
      // (They will sync via webhooks in the background)
      for (let i = 1; i < connections.length; i++) {
        try {
          await bankingService.syncConnectionTransactions(connections[i].id);
        } catch (error) {
          console.error(`Error syncing connection ${connections[i].id}:`, error);
        }
      }

    } catch (error) {
      console.error('Error syncing all accounts:', error);
      toast.error('Erro ao iniciar sincronização', { id: 'sync-progress' });
      setSyncingConnectionId(null);
    }
  }, [connections, startPolling]);

  // Open delete confirmation dialog
  const handleDeleteAccount = (accountId: string) => {
    const account = accounts.find(a => a.id === accountId);
    if (!account) return;

    setAccountToDelete(account);
    setDeleteConfirmOpen(true);
  };

  // Confirm and execute deletion
  const confirmDelete = async () => {
    if (!accountToDelete) return;

    setIsDeleting(true);
    try {
      // Delete the connection (which will delete all associated accounts)
      await bankingService.deleteConnection(accountToDelete.connection_id);
      toast.success('Conta desconectada com sucesso!');
      setDeleteConfirmOpen(false);
      setAccountToDelete(null);
      await fetchData();
    } catch (error) {
      toast.error('Erro ao desconectar conta');
      console.error('Error deleting connection:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  // Cancel deletion
  const cancelDelete = () => {
    setDeleteConfirmOpen(false);
    setAccountToDelete(null);
  };

  // Loading state
  if (authLoading || isLoadingData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const hasAccounts = accounts.length > 0;

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">
            Contas Bancárias
          </h1>
          <p className="text-muted-foreground mt-1">
            Gerencie suas contas conectadas via Open Banking
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          {hasAccounts && (
            <Button
              onClick={handleSyncAll}
              variant="outline"
              className="w-full sm:w-auto border-white/20 text-white hover:bg-white/10 transition-all duration-300"
            >
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Sincronizar Tudo
            </Button>
          )}
          <Button
            onClick={handleConnectBank}
            className="w-full sm:w-auto bg-white text-black hover:bg-white/90 transition-all duration-300"
          >
            <LinkIcon className="h-4 w-4 mr-2" />
            Conectar Banco
          </Button>
        </div>
      </div>

      {/* Main Content */}
      {hasAccounts ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {accounts.map((account) => {
            // Find the connection for this account to get its status
            const connection = connections.find(c => c.id === account.connection_id);
            const connectionStatus = connection?.status;
            const connectionStatusDetail = connection?.status_detail;

            return (
              <BankAccountCard
                key={account.id}
                account={account}
                connectionStatus={connectionStatus}
                connectionStatusDetail={connectionStatusDetail}
                onSync={() => handleSyncAccount(account.id)}
                onReconnect={() => handleReconnectAccount(account.connection_id)}
                onView={() => setSelectedAccountId(account.id)}
                onDelete={() => handleDeleteAccount(account.id)}
              />
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={CreditCardIcon}
          title="Nenhuma conta conectada"
          description="Conecte sua primeira conta bancária para começar a acompanhar suas finanças"
          action={
            <Button onClick={handleConnectBank}>
              <LinkIcon className="h-4 w-4 mr-2" />
              Conectar Banco
            </Button>
          }
        />
      )}

      {/* Pluggy Connect Widget Overlay */}
      {showPluggyWidget && connectToken && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-y-auto">
          <PluggyConnectWidget
            connectToken={connectToken}
            updateItemId={updateItemId || undefined}
            onSuccess={updateItemId ? handleReconnectionSuccess : handleConnectionSuccess}
            onClose={handleWidgetClose}
          />
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent className="bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-white">Desconectar conta bancária</DialogTitle>
            <DialogDescription className="text-gray-400">
              {accountToDelete && (
                <>
                  Você tem certeza que deseja desconectar a conta <span className="font-semibold text-white">{accountToDelete.name}</span>?
                  <br />
                  <br />
                  Esta ação irá:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Remover a conexão com o banco</li>
                    <li>Excluir todas as transações sincronizadas</li>
                    <li>Remover o histórico de sincronização</li>
                  </ul>
                  <br />
                  <span className="text-amber-400 font-medium">Esta ação não pode ser desfeita.</span>
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-6">
            <Button
              variant="outline"
              onClick={cancelDelete}
              disabled={isDeleting}
              className="border-gray-700 text-gray-300 hover:bg-gray-800"
            >
              Cancelar
            </Button>
            <Button
              onClick={confirmDelete}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {isDeleting ? (
                <>
                  <LoadingSpinner className="w-4 h-4 mr-2" />
                  Desconectando...
                </>
              ) : (
                'Desconectar'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}