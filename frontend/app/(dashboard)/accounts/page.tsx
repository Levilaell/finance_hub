'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { toast } from 'sonner';

const PluggyConnect = dynamic(
  () => import('react-pluggy-connect').then((mod) => mod.PluggyConnect),
  { ssr: false }
);

import { useAuthStore } from '@/store/auth-store';
import { useBankingStore } from '@/store/banking-store';
import { bankingService } from '@/services/banking.service';

import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { EmptyState } from '@/components/ui/empty-state';
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
} from '@heroicons/react/24/outline';
import { BankAccountCard } from '@/components/banking/bank-account-card';
import { MFATimeoutAlert } from '@/components/banking/MFATimeoutAlert';
import { testId, TEST_IDS } from '@/utils/test-helpers';

import {
  BankAccount,
  PluggyConnectState,
  SyncError,
} from '@/types/banking.types';

export default function AccountsPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuthStore();
  const {
    accounts,
    loadingAccounts,
    accountsError,
    fetchAccounts,
    syncAccount,
  } = useBankingStore();

  // Local state
  const [pluggyConnect, setPluggyConnect] = useState<PluggyConnectState>({
    isOpen: false,
    token: null,
    mode: 'connect',
  });
  const [syncingAccountId, setSyncingAccountId] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<SyncError | null>(null);
  const [selectedAccount, setSelectedAccount] = useState<BankAccount | null>(null);

  // Check authentication
  useEffect(() => {
    if (!isAuthenticated && !authLoading) {
      router.push('/login');
      return;
    }

    if (isAuthenticated) {
      fetchAccounts();
    }
  }, [isAuthenticated, authLoading, fetchAccounts, router]);

  // Connect new bank
  const handleConnectBank = useCallback(async () => {
    try {
      // Verificar se há conectores OAuth disponíveis
      const connectors = await bankingService.getConnectors();
      const oauthConnectors = connectors.filter(c => c.has_oauth);
      
      if (oauthConnectors.length > 0) {
        // TODO: Mostrar modal para selecionar banco se houver OAuth
        // OAuth connectors available: oauthConnectors
      }
      
      // Fluxo normal do Connect Widget
      const response = await bankingService.createConnectToken();

      if (response.success && response.data) {
        setPluggyConnect({
          isOpen: true,
          token: response.data.connect_token,
          mode: 'connect',
        });
      } else {
        throw new Error(response.error || 'Failed to create connect token');
      }
    } catch (error: any) {
      console.error('Failed to connect bank:', error);
      toast.error(error.message || 'Failed to connect bank');
    }
  }, []);

  // Update existing connection
  const handleUpdateConnection = useCallback(async (account: BankAccount) => {
    try {
      // Get the item ID from the account
      const itemId = account.item.pluggy_item_id;

      if (!itemId) {
        throw new Error('Account does not have an associated item');
      }
      
      const response = await bankingService.getUpdateToken(itemId);

      if (response.success && response.data) {
        setPluggyConnect({
          isOpen: true,
          token: response.data.connect_token,
          mode: 'update',
          itemId,
          accountId: account.id,
        });
      } else {
        throw new Error(response.error || 'Failed to create update token');
      }
    } catch (error: any) {
      console.error('Failed to update connection:', error);
      toast.error(error.message || 'Failed to update connection');
    }
  }, []);

  // Sync account
  const handleSyncAccount = useCallback(async (accountId: string) => {
    setSyncingAccountId(accountId);
    setSyncError(null);

    try {
      // Show initial toast
      toast.info('Iniciando sincronização...', {
        duration: 2000,
      });

      const response = await syncAccount(accountId);

      if (response.success) {
        // Show sync progress
        toast.info('Sincronizando transações...', {
          duration: 5000,
        });

        // Wait a bit for the sync to complete
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Fetch updated accounts - try multiple times to ensure status is updated
        await fetchAccounts();
        
        // If account is still updating after 5 seconds, fetch again
        setTimeout(async () => {
          const account = accounts.find(a => a.id === accountId);
          if (account?.item_status === 'UPDATING') {
            // Account still updating, fetching again...
            await fetchAccounts();
          }
        }, 5000);
        
        // And again after 10 seconds if needed
        setTimeout(async () => {
          const account = accounts.find(a => a.id === accountId);
          if (account?.item_status === 'UPDATING') {
            // Account still updating after 10s, fetching again...
            await fetchAccounts();
          }
        }, 10000);
        
        // Show success message
        toast.success('Sincronização concluída!', {
          description: 'Suas transações estão atualizadas.',
          duration: 4000,
        });
      } else {
        // Handle specific errors
        if (response.error_code === 'MFA_REQUIRED' || 
            response.error_code === 'LOGIN_ERROR' ||
            response.reconnection_required) {
          
          const account = accounts.find(a => a.id === accountId);
          setSyncError({
            accountId,
            accountName: account?.display_name || 'Conta bancária',
            errorCode: response.error_code,
            message: response.message || 'Authentication required',
            requiresReconnect: true,
          });
        } else {
          toast.error(response.message || 'Sync failed');
        }
      }
    } catch (error: any) {
      console.error('Sync error:', error);
      toast.error('Failed to sync account');
    } finally {
      setSyncingAccountId(null);
    }
  }, [accounts, syncAccount, fetchAccounts]);

  // Pluggy Connect callbacks
  const handlePluggySuccess = useCallback(async (data: any) => {
    try {
      // Pluggy success
      
      const itemId = data?.item?.id || data?.itemId;
      if (!itemId) {
        throw new Error('No item ID received');
      }

      // Handle update mode
      if (pluggyConnect.mode === 'update' && pluggyConnect.accountId) {
        toast.success('Connection updated! Syncing...');
        setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
        
        // Sync the account
        await handleSyncAccount(pluggyConnect.accountId);
        return;
      }

      // Handle new connection
      toast.info('Processing connection...');
      
      const response = await bankingService.handleCallback({
        item_id: itemId,
      });

      if (response.success && response.data) {
        const accountCount = response.data.accounts.length;
        toast.success(`Connected ${accountCount} account(s)`);
        
        setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
        await fetchAccounts();
      } else {
        throw new Error(response.error || 'Failed to process connection');
      }
    } catch (error: any) {
      console.error('Callback error:', error);
      toast.error(error.message || 'Failed to process connection');
      setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
    }
  }, [pluggyConnect, handleSyncAccount, fetchAccounts]);

  const handlePluggyError = useCallback((error: any) => {
    console.error('Pluggy error:', error);
    toast.error(error?.message || 'Connection failed');
    setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
  }, []);

  const handlePluggyClose = useCallback(() => {
    setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
  }, []);


  // Loading state
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (loadingAccounts && accounts.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-4 text-muted-foreground">Carregando contas...</p>
        </div>
      </div>
    );
  }

  if (accountsError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <ErrorMessage message={accountsError} onRetry={fetchAccounts} />
      </div>
    );
  }

  return (
    <div className="space-y-6" {...testId('accounts-page')}>
      {/* MFA Timeout Alert */}
      <MFATimeoutAlert />
      
      {/* Banking Stability Warning Banner */}
      <div className="bg-amber-50/10 border border-amber-500/20 rounded-lg p-3">
        <div className="flex items-start gap-3">
          <ExclamationTriangleIcon className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-amber-100 leading-relaxed">
              <span className="font-medium">Aviso:</span> Alguns bancos podem não funcionar corretamente devido a manutenções, 
              atualizações de segurança ou mudanças nos processos de autenticação. Caso encontre dificuldades, 
              tente novamente em alguns minutos ou entre em contato com o seu banco, se necessário.
            </p>
          </div>
        </div>
      </div>
      
      {/* Pluggy Connect Widget */}
      {pluggyConnect.isOpen && pluggyConnect.token && (
        <PluggyConnect
          connectToken={pluggyConnect.token}
          updateItem={pluggyConnect.itemId}
          onSuccess={handlePluggySuccess}
          onError={handlePluggyError}
          onClose={handlePluggyClose}
        />
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">
            Bank Accounts
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage your connected accounts via Open Banking
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          <Button 
            onClick={() => router.push('/reports')}
            variant="outline"
            className="w-full sm:w-auto border-white/20 text-white hover:bg-white/10 transition-all duration-300" 
            {...testId('reports-generator-button')}
          >
            <DocumentChartBarIcon className="h-4 w-4 mr-2" />
            Gerar Relatórios
          </Button>
          <Button 
            onClick={handleConnectBank} 
            className="w-full sm:w-auto bg-white text-black hover:bg-white/90 transition-all duration-300" 
            {...testId(TEST_IDS.banking.connectBankButton)}
          >
            <LinkIcon className="h-4 w-4 mr-2" />
            Conectar Banco
          </Button>
        </div>
      </div>

      {/* Accounts Grid */}
      {accounts.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3" {...testId(TEST_IDS.banking.accountsList)}>
          {accounts.map((account) => {
            const isSyncing = syncingAccountId === account.id;

            return (
              <BankAccountCard
                key={account.id}
                account={account}
                isSyncing={isSyncing}
                onSync={handleSyncAccount}
                onReconnect={handleUpdateConnection}
                onRemove={setSelectedAccount}
              />
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={CreditCardIcon}
          title="No accounts connected"
          description="Connect your first bank account to start tracking your finances"
          action={
            <Button onClick={handleConnectBank} {...testId(TEST_IDS.banking.connectBankButton)}>
              <LinkIcon className="h-4 w-4 mr-2" />
              Conectar Banco
            </Button>
          }
          {...testId(TEST_IDS.banking.noAccountsMessage)}
        />
      )}

      {/* Sync Error Dialog */}
      <Dialog open={!!syncError} onOpenChange={() => setSyncError(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Authentication Required</DialogTitle>
            <DialogDescription>
              {syncError?.message ||
                'Your bank requires additional authentication to continue syncing.'}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="bg-white/10 border border-white/20 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">Why does this happen?</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Banks require periodic re-authentication for security</li>
                <li>• Some banks need authentication for each sync</li>
                <li>• Your existing transactions are preserved</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setSyncError(null)}
              className="hover:bg-accent hover:text-accent-foreground transition-all duration-200"
            >
              Cancel
            </Button>
            {syncError?.requiresReconnect && (
              <Button
                onClick={() => {
                  const account = accounts.find(
                    (a) => a.id === syncError.accountId
                  );
                  if (account) {
                    setSyncError(null);
                    handleUpdateConnection(account);
                  }
                }}
              >
                <LinkIcon className="h-4 w-4 mr-2" />
                Reconnect Account
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={!!selectedAccount}
        onOpenChange={() => setSelectedAccount(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remover Conta</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja remover {selectedAccount?.display_name}?
              Isso desconectará a conta mas preservará todo o histórico de transações.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setSelectedAccount(null)}
              className="hover:bg-accent hover:text-accent-foreground transition-all duration-200"
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={async () => {
                if (selectedAccount) {
                  try {
                    // Find the item for this account
                    const itemId = selectedAccount.item?.id;
                    if (!itemId) {
                      toast.error('Não foi possível encontrar informações da conexão');
                      return;
                    }
                    
                    // Disconnect the item
                    await bankingService.disconnectItem(itemId);
                    
                    toast.success('Conta desconectada com sucesso');
                    setSelectedAccount(null);
                    await fetchAccounts();
                  } catch (error: any) {
                    toast.error(error.message || 'Falha ao desconectar conta');
                  }
                }
              }}
            >
              Remover Conta
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}