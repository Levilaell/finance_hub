'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuthStore } from '@/store/auth-store';
import { useBankingStore } from '@/store/banking-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { EmptyState } from '@/components/ui/empty-state';
import { formatCurrency, formatDate } from '@/lib/utils';
import { 
  CreditCardIcon, 
  PlusIcon, 
  TrashIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
  LinkIcon,
  BuildingLibraryIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { bankingService } from '@/services/banking.service';
import { PluggyConnect } from 'react-pluggy-connect';
import { 
  PluggyCallbackResponse,
  SyncError,
  PluggyConnectState, 
  SyncResult
} from '@/types/banking.types';

export default function AccountsPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuthStore();
  const { 
    accounts, 
    loading, 
    error,
    fetchAccounts,
    syncAccount,
    deleteAccount
  } = useBankingStore();
  
  // Estados principais
  const [selectedAccount, setSelectedAccount] = useState<any>(null);
  const [syncingAccountId, setSyncingAccountId] = useState<string | null>(null);
  const [pluggyConnect, setPluggyConnect] = useState<PluggyConnectState>({
    isOpen: false,
    token: null,
    mode: 'connect'
  });
  const [syncError, setSyncError] = useState<SyncError | null>(null);

  // Verificar autenticação
  useEffect(() => {
    if (!isAuthenticated && !authLoading) {
      router.push('/login');
      return;
    }

    if (isAuthenticated) {
      fetchAccounts();
    }
  }, [isAuthenticated, authLoading, fetchAccounts, router]);

  // Handler para conectar novo banco
  const handleConnectBank = useCallback(async () => {
    try {
      toast.info('Preparando conexão bancária...');

      const result = await bankingService.createPluggyConnectToken();

      if (result.success && result.data?.connect_token) {
        setPluggyConnect({
          isOpen: true,
          token: result.data.connect_token,
          mode: 'connect'
        });

        // Mostrar credenciais sandbox se aplicável
        if (result.data.sandbox_mode && result.data.sandbox_credentials) {
          const creds = result.data.sandbox_credentials;
          toast.info(
            `🧪 Modo Sandbox\nUsuário: ${creds.user}\nSenha: ${creds.password}\nToken: ${creds.token}`,
            { duration: 15000 }
          );
        }
      } else {
        throw new Error(result.data?.message || 'Erro ao criar token de conexão');
      }
    } catch (error: any) {
      console.error('[Accounts] Erro ao conectar banco:', error);
      toast.error(error.message || 'Erro ao conectar com o banco');
    }
  }, []);

  // Handler para reconectar conta
  const handleReconnectAccount = useCallback(async (accountId: string) => {
    try {
      const account = accounts.find(a => a.id === accountId);
      if (!account) return;

      toast.info(`Preparando reconexão da conta ${account.account_name}...`);

      const result = await bankingService.reconnectPluggyAccount(accountId);

      if (result.success && result.data?.connect_token) {
        setPluggyConnect({
          isOpen: true,
          token: result.data.connect_token,
          mode: 'reconnect',
          accountId: accountId,
          itemId: result.data.item_id
        });

        // Mostrar credenciais sandbox se aplicável
        if (result.data.sandbox_mode && result.data.sandbox_credentials) {
          const creds = result.data.sandbox_credentials;
          toast.info(
            `🧪 Modo Sandbox\nUsuário: ${creds.user}\nSenha: ${creds.password}`,
            { duration: 10000 }
          );
        }
      } else {
        throw new Error(result.data?.message || 'Erro ao gerar token de reconexão');
      }
    } catch (error: any) {
      console.error('[Accounts] Erro ao reconectar:', error);
      toast.error(error.message || 'Erro ao reconectar conta');
    }
  }, [accounts]);

  // Handler para sincronizar conta
  const handleSyncAccount = useCallback(async (accountId: string) => {
    console.log(`[Accounts] Sincronizando conta ${accountId}`);
    setSyncingAccountId(accountId);
    setSyncError(null);

    try {
      const result = await syncAccount(accountId) as SyncResult;
      console.log('[Accounts] Resultado sync:', result);

      if (result.success) {
        const txCount = result.data?.sync_stats?.transactions_synced || 0;
        
        if (txCount > 0) {
          toast.success(`✅ ${txCount} transações sincronizadas`);
        } else {
          toast.info('Nenhuma transação nova encontrada');
        }

        // Verificar avisos
        if (result.warning) {
          toast.warning(result.warning, { duration: 6000 });
        }

        await fetchAccounts();
      } else {
        // Tratar erros de autenticação
        if (result.error_code === 'MFA_REQUIRED' || 
            result.error_code === 'WAITING_USER_ACTION' ||
            result.error_code === 'LOGIN_ERROR' ||
            result.reconnection_required) {
          
          const account = accounts.find(a => a.id === accountId);
          setSyncError({
            accountId,
            accountName: account?.account_name || 'Conta bancária',
            errorCode: result.error_code,
            message: result.message || 'Autenticação necessária',
            requiresReconnect: true
          });
        } else {
          toast.error(result.message || 'Erro ao sincronizar');
        }
      }
    } catch (error: any) {
      console.error('[Accounts] Erro sync:', error);
      
      const account = accounts.find(a => a.id === accountId);
      
      // Verificar se é erro de autenticação
      if (error.response?.status === 401 || error.response?.status === 403) {
        setSyncError({
          accountId,
          accountName: account?.account_name || 'Conta bancária',
          message: 'Sessão expirada. É necessário reconectar.',
          requiresReconnect: true
        });
      } else {
        toast.error('Erro ao sincronizar conta');
      }
    } finally {
      setSyncingAccountId(null);
    }
  }, [accounts, syncAccount, fetchAccounts]);

  // Handler para sucesso do Pluggy Connect
  const handlePluggySuccess = useCallback(async (itemData: any) => {
    try {
      console.log('[Accounts] Pluggy success:', itemData);
      
      const itemId = itemData?.item?.id || itemData?.itemId;
      if (!itemId) {
        throw new Error('ID da conexão não encontrado');
      }

      // Se for reconexão
      if (pluggyConnect.mode === 'reconnect' && pluggyConnect.accountId) {
        toast.success('Conta reconectada! Sincronizando transações...');
        
        // Fechar modal
        setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
        
        // Atualizar lista primeiro
        await fetchAccounts();
        
        // Aguardar estabilização e sincronizar
        setTimeout(() => {
          handleSyncAccount(pluggyConnect.accountId!);
        }, 2000);
        
        return;
      }

      // Se for nova conexão
      toast.success('Processando conexão...');
      
      const response: PluggyCallbackResponse = await bankingService.handlePluggyCallback(itemId);
      
      if (response.success && response.data) {
        const accountsCreated = response.data.accounts?.length || 0;
        toast.success(`✅ ${accountsCreated} conta(s) conectada(s) com sucesso!`);
        
        // Fechar modal
        setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
        
        // Atualizar lista
        await fetchAccounts();
        
        // Sincronizar automaticamente as novas contas
        if (response.data.accounts && response.data.accounts.length > 0) {
          setTimeout(() => {
            response.data!.accounts.forEach((account) => {
              handleSyncAccount(account.id.toString());
            });
          }, 3000);
        }
      } else {
        throw new Error(response.message || 'Erro ao processar conexão');
      }
    } catch (error: any) {
      console.error('[Accounts] Erro no callback:', error);
      toast.error(error.message || 'Erro ao processar conexão');
      setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
    }
  }, [pluggyConnect.mode, pluggyConnect.accountId, fetchAccounts, handleSyncAccount]);


  // Handler para erro do Pluggy Connect
  const handlePluggyError = useCallback((error: any) => {
    console.error('[Accounts] Pluggy error:', error);
    
    const errorMessage = error?.message || error?.error || 'Erro ao conectar com o banco';
    toast.error(errorMessage);
    
    setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
  }, []);

  // Handler para fechar Pluggy Connect
  const handlePluggyClose = useCallback(() => {
    console.log('[Accounts] Pluggy closed');
    setPluggyConnect({ isOpen: false, token: null, mode: 'connect' });
  }, []);



  // Handler para deletar conta
  const handleDeleteAccount = useCallback(async () => {
    if (!selectedAccount) return;
    
    try {
      await deleteAccount(selectedAccount.id);
      setSelectedAccount(null);
      toast.success('Conta removida com sucesso');
    } catch (error) {
      toast.error('Erro ao remover conta');
    }
  }, [selectedAccount, deleteAccount]);

  // Helpers para UI
  const getAccountTypeInfo = (type: string) => {
    const types: Record<string, { label: string; color: string }> = {
      checking: { label: 'Conta Corrente', color: 'bg-blue-100 text-blue-800' },
      savings: { label: 'Poupança', color: 'bg-green-100 text-green-800' },
      credit_card: { label: 'Cartão de Crédito', color: 'bg-purple-100 text-purple-800' },
      investment: { label: 'Investimento', color: 'bg-orange-100 text-orange-800' },
      other: { label: 'Outro', color: 'bg-gray-100 text-gray-800' }
    };
    return types[type] || types.other;
  };

  const getStatusInfo = (status: string) => {
    const statuses: Record<string, { label: string; color: string; icon: any }> = {
      active: { label: 'Ativa', color: 'text-green-700', icon: CheckCircleIcon },
      error: { label: 'Erro', color: 'text-red-700', icon: XCircleIcon },
      sync_error: { label: 'Erro de Sincronização', color: 'text-orange-700', icon: ExclamationTriangleIcon },
      consent_revoked: { label: 'Consentimento Revogado', color: 'text-red-700', icon: XCircleIcon },
      expired: { label: 'Expirada', color: 'text-orange-700', icon: ExclamationTriangleIcon }
    };
    return statuses[status] || { label: status, color: 'text-gray-700', icon: XCircleIcon };
  };

  // Estados de carregamento
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

  if (loading && accounts.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-4 text-gray-600">Carregando contas bancárias...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <ErrorMessage message={error} onRetry={fetchAccounts} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Pluggy Connect Modal */}
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
          <h1 className="text-3xl font-bold text-gray-900">Contas Bancárias</h1>
          <p className="text-gray-600 mt-1">
            Gerencie suas contas conectadas via Open Banking
          </p>
        </div>
        <Button onClick={handleConnectBank} className="w-full sm:w-auto">
          <LinkIcon className="h-4 w-4 mr-2" />
          Conectar Banco
        </Button>
      </div>

      {/* Accounts Grid */}
      {accounts.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {accounts.map((account) => {
            const typeInfo = getAccountTypeInfo(account.account_type);
            const statusInfo = getStatusInfo(account.status);
            const StatusIcon = statusInfo.icon;
            const isSyncing = syncingAccountId === account.id;
            const needsReconnect = ['error', 'sync_error', 'expired', 'consent_revoked'].includes(account.status);

            return (
              <Card key={account.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-lg flex items-center gap-2">
                        {account.provider?.logo_url ? (
                          <Image 
                            src={account.provider.logo_url} 
                            alt={account.provider.name}
                            width={24}
                            height={24}
                            className="object-contain"
                          />
                        ) : (
                          <BuildingLibraryIcon className="h-6 w-6 text-gray-400" />
                        )}
                        {account.account_name}
                      </CardTitle>
                      <p className="text-sm text-gray-600">
                        {account.provider?.name} • {account.account_number}
                      </p>
                    </div>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${typeInfo.color}`}>
                      {typeInfo.label}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Balance */}
                    <div>
                      <p className="text-2xl font-bold">
                        {formatCurrency(account.current_balance || 0)}
                      </p>
                      <p className="text-sm text-gray-600">
                        Disponível: {formatCurrency(account.available_balance || 0)}
                      </p>
                    </div>

                    {/* Status */}
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center space-x-1">
                        <StatusIcon className={`h-4 w-4 ${statusInfo.color}`} />
                        <span className={statusInfo.color}>{statusInfo.label}</span>
                      </div>
                      <span className="text-gray-500">
                        {account.last_sync_at 
                          ? `Atualizado ${formatDate(account.last_sync_at)}`
                          : 'Nunca sincronizado'}
                      </span>
                    </div>

                    {/* Error Alert */}
                    {needsReconnect && (
                      <div className="p-3 bg-orange-50 border border-orange-200 rounded-md">
                        <p className="text-sm text-orange-800">
                          Reconexão necessária para sincronizar
                        </p>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex space-x-2">
                      {needsReconnect ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleReconnectAccount(account.id)}
                          className="flex-1"
                        >
                          <LinkIcon className="h-4 w-4 mr-1" />
                          Reconectar
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSyncAccount(account.id)}
                          disabled={isSyncing}
                          className="flex-1"
                        >
                          <ArrowPathIcon className={`h-4 w-4 mr-1 ${isSyncing ? 'animate-spin' : ''}`} />
                          {isSyncing ? 'Sincronizando...' : 'Sincronizar'}
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-red-600 hover:text-red-700"
                        onClick={() => setSelectedAccount(account)}
                      >
                        <TrashIcon className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
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

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!selectedAccount} onOpenChange={() => setSelectedAccount(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remover Conta Bancária</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja remover a conta &ldquo;{selectedAccount?.account_name}&rdquo;? 
              Esta ação não pode ser desfeita e todas as transações serão mantidas no histórico.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedAccount(null)}>
              Cancelar
            </Button>
            <Button variant="destructive" onClick={handleDeleteAccount}>
              Remover Conta
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Sync Error Dialog */}
      <Dialog open={!!syncError} onOpenChange={() => setSyncError(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {syncError?.errorCode === 'MFA_REQUIRED' ? 'Autenticação Necessária' : 'Reconexão Necessária'}
            </DialogTitle>
            <DialogDescription>
              {syncError?.message || `A conexão com ${syncError?.accountName} precisa ser renovada.`}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <h4 className="font-medium text-blue-900 mb-2">Por que isso acontece?</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Por segurança, os bancos exigem autenticação periódica</li>
                <li>• Alguns bancos requerem autenticação a cada sincronização</li>
                <li>• Suas transações anteriores estão preservadas</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSyncError(null)}>
              Cancelar
            </Button>
            {syncError?.requiresReconnect && (
              <Button
                onClick={() => {
                  const error = syncError;
                  setSyncError(null);
                  if (error.accountId) {
                    handleReconnectAccount(error.accountId);
                  }
                }}
              >
                <LinkIcon className="h-4 w-4 mr-2" />
                Reconectar Conta
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}