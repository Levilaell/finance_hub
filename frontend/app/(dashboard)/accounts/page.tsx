'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

import { useAuthStore } from '@/store/auth-store';
import { bankingService } from '@/services/banking.service';
import { BankAccount, BankConnection, MFAParameter, ConnectionStatusResponse } from '@/types/banking';
import { useSyncStatus } from '@/hooks/useSyncStatus';

import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { EmptyState } from '@/components/ui/empty-state';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { BankAccountCard } from '@/components/banking/bank-account-card';
import { PluggyConnectWidget, MFAPrompt } from '@/components/banking';
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

  // MFA State
  const [mfaConnectionId, setMfaConnectionId] = useState<string | null>(null);
  const [mfaParameter, setMfaParameter] = useState<MFAParameter | null>(null);
  const [showMfaPrompt, setShowMfaPrompt] = useState(false);
  const [mfaPollingInterval, setMfaPollingInterval] = useState<NodeJS.Timeout | null>(null);

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

  // Check connection status for MFA
  const checkConnectionForMFA = useCallback(async (connectionId: string): Promise<ConnectionStatusResponse | null> => {
    try {
      const statusResponse = await bankingService.checkConnectionStatus(connectionId);
      return statusResponse;
    } catch (error) {
      console.error('Error checking connection status:', error);
      return null;
    }
  }, []);

  // Handle MFA submission
  const handleMFASubmit = async (mfaValue: string) => {
    if (!mfaConnectionId || !mfaParameter) return;

    try {
      // Send MFA code
      await bankingService.sendMFA(mfaConnectionId, mfaValue, mfaParameter.name);

      toast.success('Código MFA enviado! Aguardando validação...');
      setShowMfaPrompt(false);

      // Start polling for status change after MFA
      startMFAPolling(mfaConnectionId);
    } catch (error: any) {
      console.error('Error sending MFA:', error);
      throw new Error(error.response?.data?.error || 'Erro ao enviar código MFA');
    }
  };

  // Start polling for MFA status
  const startMFAPolling = (connectionId: string) => {
    // Clear any existing interval
    if (mfaPollingInterval) {
      clearInterval(mfaPollingInterval);
    }

    let pollCount = 0;
    const maxPolls = 40; // 40 * 3s = 2 minutes max

    const interval = setInterval(async () => {
      pollCount++;

      const statusResponse = await checkConnectionForMFA(connectionId);

      if (!statusResponse) {
        clearInterval(interval);
        setMfaPollingInterval(null);
        toast.error('Erro ao verificar status da conexão');
        return;
      }

      // Check if MFA was successful (status changed from WAITING_USER_INPUT/WAITING_USER_ACTION)
      if (statusResponse.status === 'UPDATED') {
        clearInterval(interval);
        setMfaPollingInterval(null);
        setMfaConnectionId(null);
        setMfaParameter(null);
        toast.success('Autenticação concluída com sucesso!');

        // Start sync polling
        setSyncingConnectionId(connectionId);
        startPolling(connectionId);
        return;
      }

      // Check if still waiting
      if (statusResponse.status === 'WAITING_USER_INPUT' || statusResponse.status === 'WAITING_USER_ACTION') {
        // Still waiting, continue polling
        return;
      }

      // Check for errors
      if (statusResponse.status === 'LOGIN_ERROR' || statusResponse.status === 'ERROR') {
        clearInterval(interval);
        setMfaPollingInterval(null);
        toast.error(statusResponse.error_message || 'Erro na autenticação');
        setMfaConnectionId(null);
        setMfaParameter(null);
        return;
      }

      // Check for timeout
      if (pollCount >= maxPolls) {
        clearInterval(interval);
        setMfaPollingInterval(null);
        toast.error('Timeout ao aguardar validação MFA');
        setMfaConnectionId(null);
        setMfaParameter(null);
        return;
      }
    }, 3000); // Poll every 3 seconds

    setMfaPollingInterval(interval);
  };

  // Cancel MFA
  const handleMFACancel = () => {
    setShowMfaPrompt(false);
    setMfaConnectionId(null);
    setMfaParameter(null);

    if (mfaPollingInterval) {
      clearInterval(mfaPollingInterval);
      setMfaPollingInterval(null);
    }
  };

  // Cleanup MFA polling on unmount
  useEffect(() => {
    return () => {
      if (mfaPollingInterval) {
        clearInterval(mfaPollingInterval);
      }
    };
  }, [mfaPollingInterval]);

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
        toast.dismiss('sync-progress');

        // Check status to see if it's MFA or credentials error
        const statusResponse = await checkConnectionForMFA(account.connection_id);

        if (statusResponse?.status === 'WAITING_USER_INPUT' || statusResponse?.status === 'WAITING_USER_ACTION') {
          // User action is required
          if (statusResponse.parameter && Object.keys(statusResponse.parameter).length > 0) {
            // MFA with parameter - show MFA prompt for user to enter code
            setMfaConnectionId(account.connection_id);
            setMfaParameter(statusResponse.parameter);
            setShowMfaPrompt(true);
            setSyncingConnectionId(null);
            toast.info('Autenticação adicional necessária');
            return;
          } else {
            // No parameter - likely needs approval in bank app (e.g., Inter direct connector)
            toast.dismiss('sync-progress');
            toast.info(
              'Aprove a sincronização no aplicativo do seu banco. Aguardando aprovação...',
              { id: 'sync-progress', duration: 30000 }
            );
            // Continue polling - don't stop sync, user needs time to approve
            startPolling(account.connection_id);
            return;
          }
        }

        if (statusResponse?.status === 'LOGIN_ERROR' || statusResponse?.status === 'OUTDATED') {
          // Credentials error - suggest reconnection
          setSyncingConnectionId(null);
          toast.error(
            'Credenciais inválidas ou expiradas. Por favor, reconecte sua conta.',
            { id: 'sync-progress', duration: 5000 }
          );
          return;
        }

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

      {/* MFA Prompt Dialog */}
      <Dialog open={showMfaPrompt} onOpenChange={(open) => !open && handleMFACancel()}>
        <DialogContent className="bg-gray-900 border-gray-800">
          {mfaParameter && mfaConnectionId && (
            <MFAPrompt
              parameter={mfaParameter}
              onSubmit={handleMFASubmit}
              onCancel={handleMFACancel}
              institutionName={
                connections.find(c => c.id === mfaConnectionId)?.connector.name || 'Banco'
              }
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}