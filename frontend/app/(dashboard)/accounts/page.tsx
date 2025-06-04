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
import { BankAccountForm } from '@/components/accounts/bank-account-form';
import { useBankProviders } from '@/hooks/use-bank-providers';
import { bankingService } from '@/services/banking.service';
import { PluggyConnectHandler } from '@/components/banking/pluggy-connect-handler';

interface BankProvider {
  id: number;
  name: string;
  code: string;
  logo?: string;
  color?: string;
  is_open_banking: boolean;
  supports_pix: boolean;
  supports_ted: boolean;
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
  
  // Use the custom hook for providers
  const { providers, loading: providersLoading, error: providersError } = useBankProviders();
  
  const [isAddingAccount, setIsAddingAccount] = useState(false);
  const [isManualForm, setIsManualForm] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<BankProvider | null>(null);
  const [selectedAccount, setSelectedAccount] = useState<any>(null);
  const [editingAccount, setEditingAccount] = useState<any>(null);
  const [syncingAccountId, setSyncingAccountId] = useState<number | null>(null);
  const [showAccountForm, setShowAccountForm] = useState(false);
  const [accountFormData, setAccountFormData] = useState({
    agency: '',
    account_number: '',
    account_digit: '',
    nickname: ''
  });

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    fetchAccounts();
  }, [isAuthenticated]);

  // Debug: log providers
  useEffect(() => {
    console.log('Providers loaded:', providers);
  }, [providers]);

  const handleConnectBank = async (provider: BankProvider) => {
    try {
      // Store the bank code for use in the callback
      localStorage.setItem('pending_bank_connection', provider.code);

      // Check if user wants to use Pluggy (real connection)
      const usePluggy = confirm('Deseja conectar com seu banco real usando o Pluggy?\n\nClique em "OK" para conexão real ou "Cancelar" para usar simulação.');

      // Use the banking service to initiate the connection
      const result = await bankingService.connectBankAccount({
        bank_code: provider.code,
        use_pluggy: usePluggy
      });

      if (result.data?.status === 'pluggy_connect_required') {
        // Pluggy Connect flow
        toast.info('Abrindo Pluggy Connect para conectar sua conta...');
        
        // Open Pluggy Connect widget
        const connectToken = result.data.connect_token;
        const connectUrl = result.data.connect_url;
        
        if (connectToken && connectUrl) {
          // Create Pluggy Connect URL with token
          const pluggyUrl = `${connectUrl}?connectToken=${connectToken}&updateItem=false`;
          window.open(pluggyUrl, '_blank', 'width=500,height=700');
          
          toast.success('Complete a conexão na janela do Pluggy');
          return;
        }
      }

      if (result.status === 'consent_required') {
        // Real Open Banking flow - redirect to authorization URL
        toast.info(`Redirecionando para autorização no ${provider.name}...`);
        
        // Store consent info for later use
        if (result.consent_id) {
          localStorage.setItem('consent_id', result.consent_id);
        }
        
        // Redirect to bank's authorization page
        if (result.authorization_url) {
          window.location.href = result.authorization_url;
        } else {
          throw new Error('URL de autorização não disponível');
        }
      } else if (result.status === 'success') {
        // Direct connection (fallback or test mode)
        setIsAddingAccount(false);
        setAccountFormData({ agency: '', account_number: '', account_digit: '', nickname: '' });
        setSelectedProvider(null);
        fetchAccounts();
        
        const balanceText = result.balance 
          ? new Intl.NumberFormat('pt-BR', {
              style: 'currency',
              currency: 'BRL'
            }).format(result.balance)
          : '';
        
        toast.success(`${result.message}${balanceText ? ` Saldo: ${balanceText}` : ''}`);
      } else {
        throw new Error(result.message || 'Erro ao iniciar conexão');
      }
    } catch (error: any) {
      console.error('Error connecting bank:', error);
      
      // Clean up stored data on error
      localStorage.removeItem('pending_bank_connection');
      localStorage.removeItem('consent_id');
      
      toast.error(
        error.message || 
        'Erro ao conectar com o banco. Verifique sua configuração de Open Banking.'
      );
    }
  };

  const handleSyncAccount = async (accountId: number) => {
    setSyncingAccountId(accountId);
    try {
      await syncAccount(accountId);
      toast.success('Sincronização iniciada');
    } catch (error) {
      toast.error('Erro ao sincronizar conta');
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

  const handleRefreshToken = async (accountId: number) => {
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
      {/* Pluggy Connect Handler */}
      <PluggyConnectHandler 
        onSuccess={() => {
          toast.success('Conta conectada com sucesso!');
          fetchAccounts();
          setIsAddingAccount(false);
          setShowAccountForm(false);
        }}
        onError={(error) => {
          toast.error(error);
        }}
      />
      
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Contas Bancárias</h1>
          <p className="text-gray-600 mt-1">
            Gerencie suas contas conectadas via Open Banking
          </p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={() => setIsAddingAccount(true)}>
            <LinkIcon className="h-4 w-4 mr-2" />
            Conectar via Open Banking
          </Button>
          <Button variant="outline" onClick={() => setIsManualForm(true)}>
            <PlusIcon className="h-4 w-4 mr-2" />
            Adicionar Manualmente
          </Button>
        </div>
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
                        {account.bank_provider?.logo ? (
                          <img 
                            src={account.bank_provider.logo} 
                            alt={account.bank_provider.name}
                            className="h-6 w-6 object-contain"
                          />
                        ) : (
                          <BuildingLibraryIcon className="h-6 w-6 text-gray-400" />
                        )}
                        {account.nickname || account.display_name}
                      </CardTitle>
                      <p className="text-sm text-gray-600">
                        {account.bank_provider?.name} • {account.masked_account}
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
                      {account.status === 'expired' ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRefreshToken(account.id)}
                          className="text-orange-600 hover:text-orange-700"
                        >
                          <ArrowPathIcon className="h-4 w-4 mr-1" />
                          Renovar Token
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setEditingAccount(account)}
                        >
                          Editar
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleSyncAccount(account.id)}
                        disabled={isSyncing || account.status === 'expired'}
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
            <div className="flex space-x-2">
              <Button onClick={() => setIsAddingAccount(true)}>
                <LinkIcon className="h-4 w-4 mr-2" />
                Conectar via Open Banking
              </Button>
              <Button variant="outline" onClick={() => setIsManualForm(true)}>
                <PlusIcon className="h-4 w-4 mr-2" />
                Adicionar Manualmente
              </Button>
            </div>
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
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-3">
                {(providers || [])
                  .filter(p => p.is_open_banking)
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
                          style={{ backgroundColor: provider.color || '#6B7280' }}
                        >
                          {provider.name.charAt(0)}
                        </div>
                      )}
                      <span className="font-medium text-sm">{provider.name}</span>
                      {provider.supports_pix && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full ml-auto">
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
                  setIsAddingAccount(false);
                  setShowAccountForm(true);
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

      {/* Manual Account Form */}
      <BankAccountForm
        isOpen={isManualForm}
        onClose={() => {
          setIsManualForm(false);
          setEditingAccount(null);
        }}
        account={editingAccount}
      />

      {/* Edit Account Form */}
      <BankAccountForm
        isOpen={!!editingAccount && !isManualForm}
        onClose={() => setEditingAccount(null)}
        account={editingAccount}
      />

      {/* Account Data Collection Form */}
      <Dialog open={showAccountForm} onOpenChange={setShowAccountForm}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Conectar com {selectedProvider?.name}</DialogTitle>
            <DialogDescription>
              Para conectar com segurança, precisamos de algumas informações da sua conta
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="agency">Agência</Label>
              <Input
                id="agency"
                placeholder="Ex: 0001"
                value={accountFormData.agency}
                onChange={(e) => setAccountFormData(prev => ({ ...prev, agency: e.target.value }))}
              />
            </div>
            
            <div className="flex gap-3">
              <div className="flex-1">
                <Label htmlFor="account_number">Número da Conta</Label>
                <Input
                  id="account_number"
                  placeholder="Ex: 12345"
                  value={accountFormData.account_number}
                  onChange={(e) => setAccountFormData(prev => ({ ...prev, account_number: e.target.value }))}
                />
              </div>
              <div className="w-20">
                <Label htmlFor="account_digit">Dígito</Label>
                <Input
                  id="account_digit"
                  placeholder="6"
                  maxLength={2}
                  value={accountFormData.account_digit}
                  onChange={(e) => setAccountFormData(prev => ({ ...prev, account_digit: e.target.value }))}
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="nickname">Apelido (opcional)</Label>
              <Input
                id="nickname"
                placeholder="Ex: Conta Principal"
                value={accountFormData.nickname}
                onChange={(e) => setAccountFormData(prev => ({ ...prev, nickname: e.target.value }))}
              />
            </div>
            
            <div className="bg-blue-50 p-3 rounded-lg">
              <p className="text-sm text-blue-700">
                🔒 Seus dados são criptografados e usados apenas para conectar com {selectedProvider?.name} via Open Banking.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowAccountForm(false);
                setAccountFormData({ agency: '', account_number: '', account_digit: '', nickname: '' });
              }}
            >
              Cancelar
            </Button>
            <Button
              onClick={() => {
                if (selectedProvider && accountFormData.agency && accountFormData.account_number) {
                  handleConnectBank(selectedProvider);
                  setShowAccountForm(false);
                } else {
                  toast.error('Preencha agência e número da conta');
                }
              }}
              disabled={!accountFormData.agency || !accountFormData.account_number}
            >
              <LinkIcon className="h-4 w-4 mr-2" />
              Conectar Agora
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}