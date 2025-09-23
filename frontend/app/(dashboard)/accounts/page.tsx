'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

import { useAuthStore } from '@/store/auth-store';

import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { EmptyState } from '@/components/ui/empty-state';

import {
  CreditCardIcon,
  LinkIcon,
  DocumentChartBarIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

export default function AccountsPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuthStore();

  // Check authentication
  useEffect(() => {
    if (!isAuthenticated && !authLoading) {
      router.push('/login');
      return;
    }
  }, [isAuthenticated, authLoading, router]);

  // Connect new bank
  const handleConnectBank = () => {
    toast.info('Banking logic removed - no action taken');
  };

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

      {/* Empty State */}
      <EmptyState
        icon={CreditCardIcon}
        title="No accounts connected"
        description="Connect your first bank account to start tracking your finances"
        action={
          <Button onClick={handleConnectBank}>
            <LinkIcon className="h-4 w-4 mr-2" />
            Conectar Banco
          </Button>
        }
      />
    </div>
  );
}