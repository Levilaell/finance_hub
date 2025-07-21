'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { useBankingStore } from '@/store/banking-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
  BanknotesIcon,
  BuildingLibraryIcon
} from '@heroicons/react/24/outline';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { bankingService } from '@/services/banking.service';
import { PluggyConnectModal } from '@/components/banking/pluggy-connect-widget';
import { PluggyInfoDialog } from '@/components/banking/pluggy-info-dialog';

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
  
  const [selectedAccount, setSelectedAccount] = useState<any>(null);
  const [syncingAccountId, setSyncingAccountId] = useState<string | null>(null);
  const [pluggyConnectToken, setPluggyConnectToken] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [pluggyError, setPluggyError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    fetchAccounts();
    
    // Check if user is returning from Pluggy Connect
    const providerName = sessionStorage.getItem('pluggy_provider');
    
    // Check URL parameters for Pluggy response
    const urlParams = new URLSearchParams(window.location.search);
    const itemId = urlParams.get('itemId');
    const error = urlParams.get('error');
    const status = urlParams.get('status');
    
    if (itemId && status === 'success') {
      // Success - item was created
      const provider = providerName || 'Banco';
      toast.success(`Conta ${provider} conectada com sucesso!`);
      
      // Handle the callback to create bank accounts
      handlePluggyCallback(itemId);
      
      // Clear the stored values and URL parameters
      sessionStorage.removeItem('pluggy_provider');
      sessionStorage.removeItem('pluggy_bank_code');
      window.history.replaceState({}, '', window.location.pathname);
    } else if (error && status === 'error') {
      // Error occurred
      const provider = providerName || 'Banco';
      toast.error(`Erro ao conectar ${provider}: ${error}`);
      
      // Clear the stored values and URL parameters
      sessionStorage.removeItem('pluggy_provider');
      sessionStorage.removeItem('pluggy_bank_code');
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [isAuthenticated]);

  // ✅ Função simplificada - abre Pluggy Connect diretamente
  const handleConnectBank = async () => {
    try {
      toast.info('Iniciando conexão com seu banco...');

      const result = await bankingService.createPluggyConnectToken();


      if (result.success && result.data?.connect_token) {
        const connectToken = result.data.connect_token;
        
        
        // Setup Pluggy Connect widget
        setPluggyConnectToken(connectToken);
        setIsConnecting(true);
        
        // Show sandbox credentials if in sandbox mode
        if (result.data.sandbox_mode && result.data.sandbox_credentials) {
          const creds = result.data.sandbox_credentials;
          toast.info(
            `🧪 Modo Sandbox - Use as credenciais: ${creds.user} / ${creds.password} / ${creds.token}`,
            { duration: 15000 }
          );
        }
        
        toast.success('Abrindo Pluggy Connect...');
        return;
      }

      // Se chegou aqui, algo deu errado
      throw new Error(result.data?.message || 'Erro ao criar token de conexão');
      
    } catch (error: any) {
      toast.error(
        error.message || 
        'Erro ao conectar com o banco. Tente novamente.'
      );
      
      // Reset states on error
      setIsConnecting(false);
      setPluggyConnectToken(null);
    }
  };

  // ✅ Função handleSyncAccount (mantida como está)
  const handleSyncAccount = async (accountId: string) => {
    setSyncingAccountId(accountId);
    try {
      
      const result = await bankingService.syncPluggyAccount(accountId);
      
      
      if (result.success) {
        const transactionCount = result.data.transactions_synced;
        toast.success(`✅ ${transactionCount} transações sincronizadas`);
        fetchAccounts(); // Refresh accounts list
      } else {
        throw new Error('Falha na sincronização');
      }
    } catch (error: any) {
      toast.error('Erro ao sincronizar conta: ' + (error.message || 'Erro desconhecido'));
    } finally {
      setSyncingAccountId(null);
    }
  };

  const handleDeleteAccount = async () => {
    if (!selectedAccount) return;
    
    try {
      await deleteAccount(selectedAccount.id);
      setSelectedAccount(null);
      toast.success('Conta removida com sucesso');
    } catch (error) {
      toast.error('Erro ao remover conta');
    }
  };

  const handleRefreshToken = async (accountId: string) => {
    try {
      const result = await bankingService.refreshAccountToken(accountId.toString());
      
      if (result.status === 'success') {
        toast.success('Token atualizado com sucesso');
        fetchAccounts(); // Refresh the accounts list
      } else {
        throw new Error(result.message || 'Erro ao atualizar token');
      }
    } catch (error: any) {
      toast.error(error.message || 'Erro ao atualizar token. Tente reconectar a conta.');
    }
  };

  // ✅ Função handlePluggyCallback (mantida como está)
  const handlePluggyCallback = async (itemId: string) => {
    try {
      
      // Get stored provider info
      const providerName = sessionStorage.getItem('pluggy_provider') || 'Banco';
      const bankCode = sessionStorage.getItem('pluggy_bank_code') || '';
      
      const response = await bankingService.handlePluggyCallback(itemId);
      
      
      if (response.success && response.data) {
        const accountsCreated = response.data.accounts?.length || 0;
        toast.success(`🎉 ${accountsCreated} conta(s) conectada(s) com sucesso!`);
        
        // Clear stored data
        sessionStorage.removeItem('pluggy_provider');
        sessionStorage.removeItem('pluggy_bank_code');
        
        // Refresh accounts list
        fetchAccounts();
        
        return response.data;
      } else {
        throw new Error(response.message || 'Erro ao processar callback');
      }
    } catch (error: any) {
      toast.error('Erro ao finalizar conexão: ' + error.message);
      throw error;
    }
  };

  const getAccountTypeInfo = (type: string) => {
    switch (type) {
      case 'checking':
        return { label: 'Conta Corrente', color: 'bg-blue-100 text-blue-800' };
      case 'savings':
        return { label: 'Poupança', color: 'bg-green-100 text-green-800' };
      case 'business':
        return { label: 'Conta Empresarial', color: 'bg-purple-100 text-purple-800' };
      case 'digital':
        return { label: 'Conta Digital', color: 'bg-orange-100 text-orange-800' };
      default:
        return { label: type, color: 'bg-gray-100 text-gray-800' };
    }
  };

  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'active':
        return { label: 'Ativa', color: 'text-green-700', icon: CheckCircleIcon };
      case 'inactive':
        return { label: 'Inativa', color: 'text-gray-700', icon: XCircleIcon };
      case 'pending':
        return { label: 'Pendente', color: 'text-yellow-700', icon: ArrowPathIcon };
      case 'error':
        return { label: 'Erro', color: 'text-red-700', icon: XCircleIcon };
      case 'expired':
        return { label: 'Token Expirado', color: 'text-orange-700', icon: XCircleIcon };
      default:
        return { label: status, color: 'text-gray-700', icon: XCircleIcon };
    }
  };

  // ✅ Função para resetar o estado do widget
  const resetPluggyWidget = () => {
    setPluggyConnectToken(null);
    setIsConnecting(false);
    setPluggyError(null);
  };

  // Show loading state while auth is being checked
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  // Show loading state while accounts are being fetched
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

  // Ensure component returns something valid
  if (!isAuthenticated) {
    return null; // Layout will handle redirect
  }

  return (
    <div className="space-y-6">
      {/* Pluggy Connect Modal */}
      {pluggyConnectToken && isConnecting && !pluggyError && (
        <PluggyConnectModal
          connectToken={pluggyConnectToken}
          onSuccess={async (itemData) => {
            console.log('Pluggy Connect Success:', itemData);
            const itemId = itemData?.item?.id;
            
            if (itemId) {
              try {
                // Handle the callback to create bank accounts
                await handlePluggyCallback(itemId);
                
                // Force refresh after successful connection
                await fetchAccounts();
              } catch (error) {
                console.error('Error in handlePluggyCallback:', error);
              }
            }
            
            // Reset states
            resetPluggyWidget();
          }}
          onError={(error) => {
            console.error('Pluggy Connect Error:', error);
            const errorMessage = error.message || 'Erro desconhecido';
            setPluggyError(errorMessage);
            toast.error(`Erro na conexão: ${errorMessage}`);
            
            // Reset states after a delay to show error
            setTimeout(() => {
              resetPluggyWidget();
            }, 3000);
          }}
          onClose={() => {
            console.log('Pluggy Connect Closed');
            // Reset states if user closes without completing
            resetPluggyWidget();
          }}
        />
      )}
      
      {/* Error fallback */}
      {pluggyError && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-md">
            <h3 className="text-lg font-semibold text-red-600 mb-2">Erro ao conectar banco</h3>
            <p className="text-gray-700 mb-4">{pluggyError}</p>
            <Button onClick={resetPluggyWidget}>Fechar</Button>
          </div>
        </div>
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
          Conectar via Open Banking
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

            return (
              <Card key={account.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-lg flex items-center gap-2">
                        {account.provider?.logo_url ? (
                          <img 
                            src={account.provider.logo_url} 
                            alt={account.provider.name}
                            className="h-6 w-6 object-contain"
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
                          ? `Sincronizado ${formatDate(account.last_sync_at)}`
                          : 'Nunca sincronizado'}
                      </span>
                    </div>

                    {/* Actions */}
                    <div className="flex space-x-2">
                      {account.status === 'sync_error' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRefreshToken(account.id)}
                          className="text-orange-600 hover:text-orange-700"
                        >
                          <ArrowPathIcon className="h-4 w-4 mr-1" />
                          Renovar Token
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleSyncAccount(account.id)}
                        disabled={isSyncing || account.status === 'sync_error'}
                      >
                        <ArrowPathIcon className={`h-4 w-4 mr-1 ${isSyncing ? 'animate-spin' : ''}`} />
                        {isSyncing ? 'Sincronizando...' : 'Sincronizar'}
                      </Button>
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
          description="Conecte sua primeira conta bancária para começar a acompanhar suas finanças automaticamente"
          action={
            <Button onClick={handleConnectBank} className="w-full sm:w-auto">
              <LinkIcon className="h-4 w-4 mr-2" />
              Conectar via Open Banking
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
              Tem certeza que deseja remover a conta &ldquo;{selectedAccount?.display_name}&rdquo;? 
              Esta ação não pode ser desfeita e todas as transações associadas serão mantidas no histórico.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSelectedAccount(null)}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteAccount}
            >
              Remover Conta
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

    </div>
  );
}