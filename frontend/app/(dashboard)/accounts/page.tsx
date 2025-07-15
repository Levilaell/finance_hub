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
import { PluggyConnectWidget } from '@/components/banking/pluggy-connect-widget';
import { PluggyInfoDialog } from '@/components/banking/pluggy-info-dialog';

// ✅ Hook customizado para Pluggy Providers
function usePluggyProviders() {
  const [providers, setProviders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sandboxMode, setSandboxMode] = useState(false);

  const fetchProviders = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🏦 Fetching Pluggy banks...');
      
      const response = await bankingService.getPluggyBanks();
      
      console.log('🏦 Pluggy banks response:', response);
      
      if (response.success) {
        setProviders(response.data);
        setSandboxMode(response.sandbox_mode);
        console.log(`🏦 Loaded ${response.data.length} banks (sandbox: ${response.sandbox_mode})`);
      } else {
        throw new Error('Failed to fetch banks from Pluggy');
      }
    } catch (err: any) {
      console.error('❌ Error fetching Pluggy providers:', err);
      setError(err.message || 'Failed to fetch bank providers');
      
      // Fallback providers para desenvolvimento
      setProviders([
        {
          id: 999,
          name: 'Pluggy Bank (Sandbox)',
          code: 'pluggy-sandbox',
          health_status: 'ONLINE',
          supports_accounts: true,
          supports_transactions: true,
          is_sandbox: true,
          primary_color: '#007BFF',
          is_open_banking: true,
          supports_pix: true
        }
      ]);
      setSandboxMode(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProviders();
  }, []);

  return { 
    providers, 
    loading, 
    error, 
    sandboxMode,
    refresh: fetchProviders
  };
}

export default function AccountsPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { 
    accounts, 
    loading, 
    error,
    fetchAccounts,
    syncAccount,
    deleteAccount
  } = useBankingStore();
  
  // ✅ Use the custom Pluggy hook
  const { 
    providers, 
    loading: providersLoading, 
    error: providersError,
    sandboxMode,
    refresh: refreshProviders
  } = usePluggyProviders();
  
  const [isAddingAccount, setIsAddingAccount] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<any>(null);
  const [selectedAccount, setSelectedAccount] = useState<any>(null);
  const [syncingAccountId, setSyncingAccountId] = useState<string | null>(null);
  const [pluggyConnectToken, setPluggyConnectToken] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

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

  // Debug: log providers
  useEffect(() => {
    console.log('Providers loaded:', providers);
  }, [providers]);

  // ✅ NOVA função handleConnectBank (corrigida)
  const handleConnectBank = async (provider: any) => {
    try {
      setIsAddingAccount(false); // Close the bank selection dialog
      
      console.log('🔗 Starting bank connection with:', provider.name);
      toast.info('Iniciando conexão com seu banco...');

      // ✅ SEMPRE usar Pluggy (simplificado)
      const result = await bankingService.createPluggyConnectToken();

      console.log('🔗 Pluggy connect token response:', result);

      if (result.success && result.data?.connect_token) {
        const connectToken = result.data.connect_token;
        
        console.log('🔗 Connect token received:', connectToken.substring(0, 50) + '...');
        
        // Store provider info for callback handling
        sessionStorage.setItem('pluggy_provider', provider.name);
        sessionStorage.setItem('pluggy_bank_code', provider.code);
        
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
      throw new Error(result.message || 'Erro ao criar token de conexão');
      
    } catch (error: any) {
      console.error('❌ Error connecting bank:', error);
      toast.error(
        error.message || 
        'Erro ao conectar com o banco. Tente novamente.'
      );
      
      // Reset states on error
      setIsConnecting(false);
      setPluggyConnectToken(null);
    }
  };

  // ✅ NOVA função handleSyncAccount (corrigida)
  const handleSyncAccount = async (accountId: string) => {
    setSyncingAccountId(accountId);
    try {
      console.log('🔄 Syncing Pluggy account:', accountId);
      
      const result = await bankingService.syncPluggyAccount(accountId);
      
      console.log('🔄 Sync result:', result);
      
      if (result.success) {
        const transactionCount = result.data.transactions_synced;
        toast.success(`✅ ${transactionCount} transações sincronizadas`);
        fetchAccounts(); // Refresh accounts list
      } else {
        throw new Error('Falha na sincronização');
      }
    } catch (error: any) {
      console.error('❌ Sync error:', error);
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
      console.error('Token refresh error:', error);
      toast.error(error.message || 'Erro ao atualizar token. Tente reconectar a conta.');
    }
  };

  // ✅ NOVA função handlePluggyCallback (corrigida)
  const handlePluggyCallback = async (itemId: string) => {
    try {
      console.log('🎯 Processing Pluggy callback for item:', itemId);
      
      // Get stored provider info
      const providerName = sessionStorage.getItem('pluggy_provider') || 'Banco';
      const bankCode = sessionStorage.getItem('pluggy_bank_code') || '';
      
      const response = await bankingService.handlePluggyCallback(itemId);
      
      console.log('🎯 Callback response:', response);
      
      if (response.success && response.data) {
        const accountsCreated = response.data.accounts?.length || 0;
        toast.success(`🎉 ${accountsCreated} conta(s) conectada(s) com sucesso ao ${providerName}!`);
        
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
      console.error('❌ Pluggy callback error:', error);
      toast.error('Erro ao finalizar conexão: ' + error.message);
      throw error;
    }
  };

  // ✅ Função para renderizar informações de debug
  const renderDebugInfo = () => {
    if (!sandboxMode) return null;
    
    return (
      <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-center gap-2 text-blue-700">
          <span className="text-sm font-medium">🧪 Modo Sandbox Ativo</span>
        </div>
        <div className="text-xs text-blue-600 mt-1">
          Credenciais de teste: user-ok / password-ok / 123456
        </div>
      </div>
    );
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

  if (loading && accounts.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
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
      {/* Pluggy Connect Widget */}
      {pluggyConnectToken && isConnecting && (
        <PluggyConnectWidget
          connectToken={pluggyConnectToken}
          onSuccess={async (itemData) => {
            console.log('Pluggy Connect success:', itemData);
            const itemId = itemData?.item?.id;
            
            if (itemId) {
              // Handle the callback to create bank accounts
              await handlePluggyCallback(itemId);
            }
            
            // Reset states
            setPluggyConnectToken(null);
            setIsConnecting(false);
            setSelectedProvider(null);
          }}
          onError={(error) => {
            console.error('Pluggy Connect error:', error);
            toast.error(`Erro na conexão: ${error.message || 'Erro desconhecido'}`);
            
            // Reset states
            setPluggyConnectToken(null);
            setIsConnecting(false);
          }}
          onClose={() => {
            // Reset states if user closes without completing
            setPluggyConnectToken(null);
            setIsConnecting(false);
          }}
        />
      )}
      
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Contas Bancárias</h1>
          <p className="text-gray-600 mt-1">
            Gerencie suas contas conectadas via Open Banking
          </p>
        </div>
        <Button onClick={() => setIsAddingAccount(true)}>
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
                        {(() => {
                          console.log('Account sync data:', { 
                            id: account.id, 
                            last_sync_at: account.last_sync_at,
                            account_name: account.account_name 
                          });
                          return account.last_sync_at 
                            ? `Sincronizado ${formatDate(account.last_sync_at)}`
                            : 'Nunca sincronizado';
                        })()}
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
            <Button onClick={() => setIsAddingAccount(true)}>
              <LinkIcon className="h-4 w-4 mr-2" />
              Conectar via Open Banking
            </Button>
          }
        />
      )}

      {/* Connect Account Dialog */}
      <Dialog open={isAddingAccount} onOpenChange={setIsAddingAccount}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Conectar Conta Bancária</DialogTitle>
            <DialogDescription>
              Selecione seu banco para conectar via Open Banking de forma segura
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            {/* ✅ Info sobre sandbox */}
            {renderDebugInfo()}
            
            {/* Info about Pluggy */}
            <div className="mb-4">
              <PluggyInfoDialog />
            </div>
            
            {/* Search */}
            <div className="mb-4">
              <Input
                placeholder="Buscar banco..."
                className="w-full"
                onChange={(e) => {
                  // TODO: Implement search
                }}
              />
            </div>

            {/* Popular Banks */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-700 mb-3">
                Bancos Populares ({providers ? providers.length : 0} total)
                {sandboxMode && <span className="text-blue-600 ml-2">🧪 Sandbox</span>}
              </h4>
              
              {/* Loading state */}
              {providersLoading && (
                <div className="text-sm text-blue-500 mb-2">
                  Carregando bancos disponíveis...
                </div>
              )}
              
              {/* Error state */}
              {providersError && (
                <div className="text-sm text-red-500 mb-2">
                  Erro ao carregar bancos: {providersError}
                  <Button 
                    variant="link" 
                    size="sm" 
                    onClick={refreshProviders}
                    className="ml-2"
                  >
                    Tentar novamente
                  </Button>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-3">
                {(providers || [])
                  .filter(p => p.is_open_banking || p.supports_accounts)
                  .slice(0, 6)
                  .map((provider) => (
                    <button
                      key={provider.id}
                      onClick={() => setSelectedProvider(provider)}
                      className={`flex items-center gap-3 p-3 rounded-lg border transition-all hover:shadow-md ${
                        selectedProvider?.id === provider.id 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {provider.logo ? (
                        <img 
                          src={provider.logo} 
                          alt={provider.name}
                          className="h-8 w-8 object-contain"
                        />
                      ) : (
                        <div 
                          className="h-8 w-8 rounded-full flex items-center justify-center text-white font-bold"
                          style={{ backgroundColor: provider.primary_color || '#6B7280' }}
                        >
                          {provider.name.charAt(0)}
                        </div>
                      )}
                      <div className="flex-1 text-left">
                        <span className="font-medium text-sm">{provider.name}</span>
                        {provider.is_sandbox && (
                          <div className="text-xs text-blue-600">Sandbox</div>
                        )}
                      </div>
                      {provider.supports_pix && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                          PIX
                        </span>
                      )}
                    </button>
                  ))}
              </div>
            </div>

            {/* Other Banks */}
            <details className="group">
              <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-900">
                Ver todos os bancos ({(providers || []).length})
              </summary>
              <div className="mt-3 grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
                {(providers || []).map((provider) => (
                  <button
                    key={provider.id}
                    onClick={() => setSelectedProvider(provider)}
                    className="text-left px-3 py-2 text-sm hover:bg-gray-50 rounded"
                  >
                    {provider.name}
                    {provider.is_sandbox && <span className="text-blue-600 ml-1">🧪</span>}
                  </button>
                ))}
              </div>
            </details>
          </div>

          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => {
                setIsAddingAccount(false);
                setSelectedProvider(null);
              }}
            >
              Cancelar
            </Button>
            <Button 
              onClick={() => {
                if (selectedProvider) {
                  handleConnectBank(selectedProvider);
                }
              }}
              disabled={!selectedProvider}
            >
              <LinkIcon className="h-4 w-4 mr-2" />
              Conectar com {selectedProvider?.name || 'Banco'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!selectedAccount} onOpenChange={() => setSelectedAccount(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remover Conta Bancária</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja remover a conta "{selectedAccount?.display_name}"? 
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