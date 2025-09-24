'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

import { useAuthStore } from '@/store/auth-store';
import { bankingService } from '@/services/banking.service';
import { BankAccount, BankConnection } from '@/types/banking';

import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { EmptyState } from '@/components/ui/empty-state';
import { BankAccountCard } from '@/components/banking/bank-account-card';
import { PluggyConnectWidget } from '@/components/banking/pluggy-connect-widget';

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
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);

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
    console.log('Received itemId from Pluggy:', itemId);

    try {
      // Create the connection in our backend
      const payload = { pluggy_item_id: itemId };
      console.log('Sending to backend:', payload);

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
  };

  // Sync account transactions
  const handleSyncAccount = async (accountId: string) => {
    try {
      await bankingService.syncAccountTransactions(accountId);
      toast.success('Transações sincronizadas!');
      await fetchData();
    } catch (error) {
      toast.error('Erro ao sincronizar transações');
    }
  };

  // Sync all connections
  const handleSyncAll = async () => {
    try {
      for (const connection of connections) {
        await bankingService.syncConnectionTransactions(connection.id);
      }
      toast.success('Todas as contas foram sincronizadas!');
      await fetchData();
    } catch (error) {
      toast.error('Erro ao sincronizar contas');
    }
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
            onClick={() => router.push('/reports')}
            variant="outline"
            className="w-full sm:w-auto border-white/20 text-white hover:bg-white/10 transition-all duration-300"
          >
            <DocumentChartBarIcon className="h-4 w-4 mr-2" />
            Gerar Relatórios
          </Button>
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
          {accounts.map((account) => (
            <BankAccountCard
              key={account.id}
              account={account}
              onSync={() => handleSyncAccount(account.id)}
              onView={() => setSelectedAccountId(account.id)}
            />
          ))}
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
            onSuccess={handleConnectionSuccess}
            onClose={handleWidgetClose}
          />
        </div>
      )}
    </div>
  );
}