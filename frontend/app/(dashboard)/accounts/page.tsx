'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
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
import { PluggyConnectIframe } from '@/components/banking/pluggy-connect-iframe';
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
  const [useIframeMode, setUseIframeMode] = useState(false);
  const [reconnectingAccountId, setReconnectingAccountId] = useState<string | null>(null);
  const [reconnectError, setReconnectError] = useState<{accountId: string; message: string} | null>(null);
  const [showBankAuthDialog, setShowBankAuthDialog] = useState<{accountId: string; accountName?: string} | null>(null);

  // ✅ Função handlePluggyCallback (mantida como está)
  const handlePluggyCallback = useCallback(async (itemId: string) => {
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
        await fetchAccounts();
        
        // Aguardar um pouco para o item Pluggy se estabilizar
        console.log('[AccountsPage] Aguardando 3 segundos para o item Pluggy se estabilizar...');
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Sincronizar transações automaticamente após conectar
        console.log('[AccountsPage] Iniciando sincronização automática após conexão...');
        if (response.data.accounts && response.data.accounts.length > 0) {
          for (const account of response.data.accounts) {
            try {
              // Verificar status antes de sincronizar
              console.log(`[AccountsPage] Verificando status da conta ${account.id}...`);
              const statusCheck = await bankingService.checkAccountStatus(String(account.id));
              console.log(`[AccountsPage] Status do item: ${statusCheck.data?.item_status}`);
              
              if (statusCheck.data?.item_status === 'UPDATED' || statusCheck.data?.item_status === 'ACTIVE') {
                console.log(`[AccountsPage] Sincronizando conta ${account.id}...`);
                const syncResult = await syncAccount(String(account.id));
                if (syncResult.success) {
                  const txCount = syncResult.data?.transactions_synced || 0;
                  console.log(`[AccountsPage] Conta ${account.id}: ${txCount} transações sincronizadas`);
                }
              } else {
                console.warn(`[AccountsPage] Conta ${account.id} não está pronta para sync. Status: ${statusCheck.data?.item_status}`);
              }
            } catch (error) {
              console.error(`[AccountsPage] Erro ao sincronizar conta ${account.id}:`, error);
            }
          }
          
          // Atualizar lista de contas novamente após sincronização
          await fetchAccounts();
          toast.info('Sincronização inicial concluída!');
        }
        
        return response.data;
      } else {
        throw new Error(response.message || 'Erro ao processar callback');
      }
    } catch (error: any) {
      toast.error('Erro ao finalizar conexão: ' + error.message);
      throw error;
    }
  }, [fetchAccounts]);

  useEffect(() => {
    console.log('[AccountsPage] useEffect triggered', {
      isAuthenticated,
      pathname: window.location.pathname,
      search: window.location.search
    });

    if (!isAuthenticated) {
      console.log('[AccountsPage] Not authenticated, redirecting to login');
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
    
    console.log('[AccountsPage] URL params:', {
      itemId,
      error,
      status,
      providerName
    });
    
    if (itemId && status === 'success') {
      // Success - item was created
      const provider = providerName || 'Banco';
      toast.success(`Conta ${provider} conectada com sucesso!`);
      
      // Handle the callback to create bank accounts
      handlePluggyCallback(itemId).catch(err => {
        console.error('[AccountsPage] Error in handlePluggyCallback:', err);
        toast.error('Erro ao processar conexão bancária');
      });
      
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
  }, [isAuthenticated, fetchAccounts, handlePluggyCallback, router]);

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

  // ✅ Função handleSyncAccount - sincroniza transações diretamente
  const handleSyncAccount = async (accountId: string) => {
    console.log(`[SYNC] Iniciando sincronização da conta ${accountId}`);
    setSyncingAccountId(accountId);
    
    try {
      // Primeiro, verificar o status da conta
      console.log('[SYNC] Verificando status da conta antes de sincronizar...');
      const statusCheck = await bankingService.checkAccountStatus(accountId);
      console.log('[SYNC] Status da conta:', statusCheck);
      
      if (statusCheck.data?.item_status) {
        console.log(`[SYNC] Status do item Pluggy: ${statusCheck.data.item_status}`);
        
        // Se precisa reconexão, mostrar dialog direto
        if (statusCheck.data.needs_reconnection || statusCheck.data.item_status === 'WAITING_USER_ACTION') {
          console.log('[SYNC] Item precisa de reconexão, mostrando dialog...');
          const account = accounts.find(acc => acc.id === accountId);
          const accountName = account?.account_name || 'sua conta';
          setShowBankAuthDialog({ accountId, accountName });
          return;
        }
      }
      
      // Se o status está OK, tentar sincronizar
      console.log('[SYNC] Status OK, chamando API de sincronização...');
      const result = await syncAccount(String(accountId));
      console.log('[SYNC] Resultado da sincronização:', result);
      console.log('[SYNC] Detalhes da sincronização:', {
        transactions_synced: result.data?.transactions_synced,
        sync_from: result.data?.sync_from,
        sync_to: result.data?.sync_to,
        days_searched: result.data?.days_searched,
        status: result.data?.status,
        item_status: result.data?.item_status,
        full_data: result.data
      });
      
      if (result.success) {
        const transactionCount = result.data?.transactions_synced || 0;
        if (transactionCount > 0) {
          toast.success(`✅ ${transactionCount} transações sincronizadas`);
        } else {
          toast.info('Nenhuma transação nova encontrada');
        }
        
        // Atualizar lista de contas
        await fetchAccounts();
      } else {
        // Verificar se é erro de autenticação
        console.log('[SYNC] Erro na sincronização:', {
          error_code: result.error_code,
          reconnection_required: result.reconnection_required,
          message: result.message
        });
        
        if (result.error_code === 'WAITING_USER_ACTION' || result.error_code === 'MFA_REQUIRED' || result.reconnection_required) {
          // Só neste caso mostrar o dialog de reconexão
          console.log('[SYNC] Item requer reconexão, mostrando dialog...');
          const account = accounts.find(acc => acc.id === accountId);
          const accountName = account?.account_name || 'sua conta';
          setShowBankAuthDialog({ accountId, accountName });
        } else {
          toast.error(result.message || 'Erro ao sincronizar conta');
        }
      }
    } catch (error: any) {
      // Verificar se o erro indica necessidade de reconexão
      if (error.response?.status === 403 || error.response?.data?.reconnection_required) {
        const account = accounts.find(acc => acc.id === accountId);
        const accountName = account?.account_name || 'sua conta';
        setShowBankAuthDialog({ accountId, accountName });
      } else {
        toast.error('Erro ao sincronizar: ' + (error.message || 'Erro desconhecido'));
      }
    } finally {
      setSyncingAccountId(null);
    }
  };

  // ✅ Função para reconectar conta
  const handleReconnectAccount = async (accountId: string) => {
    setReconnectingAccountId(accountId);
    try {
      const result = await bankingService.reconnectPluggyAccount(accountId);
      
      if (result.success && result.data?.connect_token) {
        const { connect_token, item_id } = result.data;
        
        // Show sandbox credentials if in sandbox mode
        if (result.data.sandbox_mode && result.data.sandbox_credentials) {
          const creds = result.data.sandbox_credentials;
          toast.info(
            `🧪 Modo Sandbox - Use as credenciais: ${creds.user} / ${creds.password} / ${creds.token}`,
            { duration: 15000 }
          );
        }
        
        // Setup Pluggy Connect widget for reconnection
        setPluggyConnectToken(connect_token);
        setIsConnecting(true);
        setReconnectError(null);
        
        // Store item_id for updateItem parameter
        sessionStorage.setItem('pluggy_update_item', item_id);
        // Store account ID for automatic sync after reconnection
        sessionStorage.setItem('pluggy_reconnecting_account', accountId);
        
        toast.success('Abrindo conexão segura com seu banco...');
      } else {
        throw new Error(result.data?.message || 'Erro ao gerar token de reconexão');
      }
    } catch (error: any) {
      toast.error('Erro ao reconectar conta: ' + (error.message || 'Erro desconhecido'));
    } finally {
      setReconnectingAccountId(null);
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
    setUseIframeMode(false);
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
      {/* Pluggy Connect - Widget SDK ou Iframe */}
      {pluggyConnectToken && isConnecting && !pluggyError && (
        useIframeMode ? (
          <PluggyConnectIframe
            connectToken={pluggyConnectToken}
            updateItem={sessionStorage.getItem('pluggy_update_item') || undefined}
            onSuccess={async (itemData) => {
              console.log('[AccountsPage] Pluggy Iframe Success:', itemData);
              const itemId = itemData?.item?.id || itemData?.itemId;
              
              if (itemId) {
                try {
                  // Se é uma atualização de item (reconexão), sincronizar automaticamente
                  const updateItemId = sessionStorage.getItem('pluggy_update_item');
                  const reconnectingAccount = sessionStorage.getItem('pluggy_reconnecting_account');
                  
                  if (updateItemId && reconnectingAccount) {
                    console.log('[AccountsPage] Item updated via iframe, syncing automatically...');
                    
                    // Limpar dados de reconexão
                    sessionStorage.removeItem('pluggy_update_item');
                    sessionStorage.removeItem('pluggy_reconnecting_account');
                    
                    // Fechar widget
                    resetPluggyWidget();
                    
                    // Aguardar um momento para o Item ser processado
                    toast.success('Autenticação concluída! Buscando suas transações...');
                    
                    setTimeout(async () => {
                      try {
                        // Sincronizar conta usando o método correto
                        await handleSyncAccount(reconnectingAccount);
                        
                        // Atualizar lista de contas
                        await fetchAccounts();
                      } catch (error) {
                        console.error('[AccountsPage] Error syncing after reconnection:', error);
                        toast.error('Erro ao sincronizar após reconexão');
                      }
                    }, 2000); // Aguardar 2 segundos para o Item ser processado
                    
                    return;
                  }
                  
                  // Fluxo normal de nova conexão
                  console.log('[AccountsPage] Calling handlePluggyCallback with itemId:', itemId);
                  const result = await handlePluggyCallback(itemId);
                  console.log('[AccountsPage] handlePluggyCallback result:', result);
                  
                  await fetchAccounts();
                  
                } catch (error) {
                  console.error('[AccountsPage] Error in handlePluggyCallback:', error);
                  toast.error('Erro ao processar conexão bancária');
                }
              } else {
                console.error('[AccountsPage] No itemId found in iframe success response:', itemData);
                toast.error('Erro: ID da conexão não encontrado');
              }
              
              resetPluggyWidget();
              // Clear update item after use
              sessionStorage.removeItem('pluggy_update_item');
              sessionStorage.removeItem('pluggy_reconnecting_account');
            }}
            onError={(error) => {
              console.error('[AccountsPage] Pluggy Iframe Error:', error);
              const errorMessage = error.message || 'Erro desconhecido';
              toast.error(`Erro na conexão: ${errorMessage}`);
              resetPluggyWidget();
            }}
            onClose={() => {
              console.log('[AccountsPage] Pluggy Iframe Closed without success');
              resetPluggyWidget();
              // Clear update item after use
              sessionStorage.removeItem('pluggy_update_item');
              sessionStorage.removeItem('pluggy_reconnecting_account');
            }}
          />
        ) : (
          <PluggyConnectModal
            connectToken={pluggyConnectToken}
            updateItem={sessionStorage.getItem('pluggy_update_item') || undefined}
            onSuccess={async (itemData) => {
              console.log('[AccountsPage] Pluggy Connect Success:', itemData);
              console.log('[AccountsPage] Update item mode:', sessionStorage.getItem('pluggy_update_item'));
              console.log('[AccountsPage] Item status received:', itemData?.item?.status);
              const itemId = itemData?.item?.id || itemData?.itemId;
              
              if (itemId) {
                try {
                  // Se é uma atualização de item (reconexão), sincronizar automaticamente
                  const updateItemId = sessionStorage.getItem('pluggy_update_item');
                  const reconnectingAccount = sessionStorage.getItem('pluggy_reconnecting_account');
                  
                  if (updateItemId && reconnectingAccount) {
                    console.log('[AccountsPage] Item updated, syncing automatically...');
                    
                    // Limpar dados de reconexão
                    sessionStorage.removeItem('pluggy_update_item');
                    sessionStorage.removeItem('pluggy_reconnecting_account');
                    
                    // Fechar widget
                    resetPluggyWidget();
                    
                    // Aguardar um momento para o Item ser processado
                    toast.success('Autenticação concluída! Buscando suas transações...');
                    
                    setTimeout(async () => {
                      try {
                        // Sincronizar conta usando o método correto
                        await handleSyncAccount(reconnectingAccount);
                        
                        // Atualizar lista de contas
                        await fetchAccounts();
                      } catch (error) {
                        console.error('[AccountsPage] Error syncing after reconnection:', error);
                        toast.error('Erro ao sincronizar após reconexão');
                      }
                    }, 2000); // Aguardar 2 segundos para o Item ser processado
                    
                    return;
                  }
                  
                  // Fluxo normal de nova conexão
                  console.log('[AccountsPage] Calling handlePluggyCallback with itemId:', itemId);
                  const result = await handlePluggyCallback(itemId);
                  console.log('[AccountsPage] handlePluggyCallback result:', result);
                  
                  await fetchAccounts();
                  
                } catch (error) {
                  console.error('[AccountsPage] Error in handlePluggyCallback:', error);
                  toast.error('Erro ao processar conexão bancária');
                }
              } else {
                console.error('[AccountsPage] No itemId found in success response:', itemData);
                toast.error('Erro: ID da conexão não encontrado');
              }
              
              resetPluggyWidget();
              // Clear update item after use
              sessionStorage.removeItem('pluggy_update_item');
              sessionStorage.removeItem('pluggy_reconnecting_account');
            }}
            onError={(error) => {
              console.error('[AccountsPage] Pluggy Connect Error:', error);
              const errorMessage = error.message || 'Erro desconhecido';
              
              // Se falhar com SDK, tentar com iframe
              if (errorMessage.includes('SDK') || errorMessage.includes('script')) {
                toast.warning('Tentando modo alternativo...');
                setUseIframeMode(true);
                return;
              }
              
              setPluggyError(errorMessage);
              toast.error(`Erro na conexão: ${errorMessage}`);
              
              setTimeout(() => {
                resetPluggyWidget();
              }, 3000);
            }}
            onClose={() => {
              console.log('[AccountsPage] Pluggy Connect Closed without success');
              resetPluggyWidget();
              // Clear update item after use
              sessionStorage.removeItem('pluggy_update_item');
              sessionStorage.removeItem('pluggy_reconnecting_account');
            }}
          />
        )
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
                          ? `Sincronizado ${formatDate(account.last_sync_at)}`
                          : 'Nunca sincronizado'}
                      </span>
                    </div>

                    {/* Warning for sync errors */}
                    {account.status === 'sync_error' && (
                      <div className="mb-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                        <p className="text-sm text-yellow-800 flex items-center">
                          <ArrowPathIcon className="h-4 w-4 mr-2" />
                          Reconexão necessária para sincronizar
                        </p>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex space-x-2">
                      {account.status === 'sync_error' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSyncAccount(account.id)}
                          className="text-orange-600 hover:text-orange-700"
                        >
                          <LinkIcon className="h-4 w-4 mr-1" />
                          Reconectar
                        </Button>
                      )}
                      {account.status !== 'sync_error' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSyncAccount(account.id)}
                          disabled={isSyncing}
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

      {/* Reconnection Required Dialog */}
      <Dialog open={!!reconnectError} onOpenChange={() => setReconnectError(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reconexão Necessária</DialogTitle>
            <DialogDescription>
              {reconnectError?.message || 'O banco está solicitando que você faça login novamente. Isso é normal e acontece periodicamente por questões de segurança.'}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <p className="text-sm text-blue-800">
                Seus dados e transações anteriores serão mantidos. Após reconectar, a sincronização continuará normalmente.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setReconnectError(null)}
            >
              Cancelar
            </Button>
            <Button
              onClick={() => {
                if (reconnectError?.accountId) {
                  handleReconnectAccount(reconnectError.accountId);
                }
              }}
              disabled={reconnectingAccountId === reconnectError?.accountId}
            >
              {reconnectingAccountId === reconnectError?.accountId ? (
                <>
                  <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" />
                  Gerando token...
                </>
              ) : (
                <>
                  <LinkIcon className="h-4 w-4 mr-2" />
                  Reconectar Conta
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bank Authentication Required Dialog */}
      <Dialog open={!!showBankAuthDialog} onOpenChange={() => setShowBankAuthDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reautenticação Necessária</DialogTitle>
            <DialogDescription>
              {showBankAuthDialog?.accountName ? (
                <>A conexão com {showBankAuthDialog.accountName} expirou e precisa ser renovada.</>
              ) : (
                <>A conexão com seu banco expirou e precisa ser renovada.</>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <h4 className="font-medium text-blue-900 mb-2">Por que isso é necessário?</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Por segurança, os bancos exigem autenticação periódica</li>
                <li>• Isso garante que apenas você tem acesso às suas transações</li>
                <li>• É um procedimento padrão do Open Banking</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowBankAuthDialog(null)}
            >
              Cancelar
            </Button>
            <Button
              onClick={() => {
                const authInfo = showBankAuthDialog;
                setShowBankAuthDialog(null);
                if (authInfo?.accountId) {
                  handleReconnectAccount(authInfo.accountId);
                }
              }}
            >
              <LinkIcon className="h-4 w-4 mr-2" />
              Autenticar no Banco
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

    </div>
  );
}