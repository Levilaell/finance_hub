'use client';

import { useState } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

import {
  ArrowPathIcon,
  LinkIcon,
  BuildingLibraryIcon,
  EllipsisVerticalIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  WifiIcon,
  CreditCardIcon,
  BanknotesIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  InformationCircleIcon,
  LockClosedIcon,
} from '@heroicons/react/24/outline';

import { BankAccount, PluggyItemStatus } from '@/types/banking.types';
import { bankingService } from '@/services/banking.service';
import { testId, TEST_IDS, testIdWithIndex } from '@/utils/test-helpers';

interface BankAccountCardProps {
  account: BankAccount;
  isSyncing: boolean;
  onSync: (accountId: string) => void;
  onReconnect: (account: BankAccount) => void;
  onRemove: (account: BankAccount) => void;
}

export function BankAccountCard({
  account,
  isSyncing,
  onSync,
  onReconnect,
  onRemove,
}: BankAccountCardProps) {
  const router = useRouter();
  const [showDetails, setShowDetails] = useState(false);

  // Helpers
  const getAccountTypeInfo = (type: string) => {
    const types: Record<string, { label: string; icon: any; color: string }> = {
      BANK: { 
        label: 'Conta Bancária', 
        icon: BuildingLibraryIcon,
        color: 'bg-card border border-border text-foreground' 
      },
      CREDIT: { 
        label: 'Cartão de Crédito', 
        icon: CreditCardIcon,
        color: 'bg-card border border-primary/20 text-foreground' 
      },
      INVESTMENT: { 
        label: 'Investimento', 
        icon: ChartBarIcon,
        color: 'bg-card border border-success-subtle text-foreground' 
      },
      LOAN: { 
        label: 'Empréstimo', 
        icon: BanknotesIcon,
        color: 'bg-card border border-warning-subtle text-foreground' 
      },
      OTHER: { 
        label: 'Outro', 
        icon: BuildingLibraryIcon,
        color: 'bg-card border border-muted text-foreground' 
      },
    };
    return types[type] || types.OTHER;
  };

  const getStatusInfo = (status?: PluggyItemStatus) => {
    const statusMap: Record<string, { 
      label: string; 
      icon: any; 
      color: string;
      description: string;
    }> = {
      'UPDATED': { 
        label: 'Atualizado', 
        icon: CheckCircleIcon,
        color: 'text-success-subtle bg-success-subtle border border-success-subtle',
        description: 'Sincronização concluída com sucesso'
      },
      'LOGIN_ERROR': { 
        label: 'Erro de Login', 
        icon: XCircleIcon,
        color: 'text-error-subtle bg-error-subtle border border-error-subtle',
        description: 'Credenciais inválidas ou expiradas'
      },
      'ERROR': { 
        label: 'Erro', 
        icon: XCircleIcon,
        color: 'text-error-subtle bg-error-subtle border border-error-subtle',
        description: 'Erro ao sincronizar com o banco'
      },
      'WAITING_USER_INPUT': { 
        label: 'Aguardando', 
        icon: ExclamationTriangleIcon,
        color: 'text-warning-subtle bg-warning-subtle border border-warning-subtle',
        description: 'Necessária autenticação adicional'
      },
      'OUTDATED': { 
        label: 'Desatualizado', 
        icon: ClockIcon,
        color: 'text-warning-subtle bg-warning-subtle border border-warning-subtle',
        description: 'Dados precisam ser atualizados'
      },
      'UPDATING': { 
        label: 'Atualizando', 
        icon: ArrowPathIcon,
        color: 'text-info-subtle bg-info-subtle border border-info-subtle',
        description: 'Sincronização em andamento'
      },
      'LOGIN_IN_PROGRESS': { 
        label: 'Conectando', 
        icon: ArrowPathIcon,
        color: 'text-info-subtle bg-info-subtle border border-info-subtle',
        description: 'Estabelecendo conexão com o banco'
      },
    };
    return statusMap[status || ''] || statusMap.ERROR;
  };

  const formatLastSync = (date?: string) => {
    if (!date) return 'Nunca sincronizado';
    
    try {
      const syncDate = new Date(date);
      const now = new Date();
      const diffInHours = (now.getTime() - syncDate.getTime()) / (1000 * 60 * 60);
      
      if (diffInHours < 1) {
        return 'Há menos de 1 hora';
      } else if (diffInHours < 24) {
        return formatDistanceToNow(syncDate, { addSuffix: true, locale: ptBR });
      } else {
        return syncDate.toLocaleDateString('pt-BR', { 
          day: '2-digit', 
          month: 'short',
          hour: '2-digit',
          minute: '2-digit'
        });
      }
    } catch {
      return 'Data inválida';
    }
  };

  const getSyncProgress = () => {
    if (!account.pluggy_updated_at) return 0;
    
    const lastSync = new Date(account.pluggy_updated_at);
    const now = new Date();
    const hoursSinceSync = (now.getTime() - lastSync.getTime()) / (1000 * 60 * 60);
    
    // Considera 24h como período ideal, após isso começa a diminuir
    if (hoursSinceSync <= 24) return 100;
    if (hoursSinceSync <= 48) return 75;
    if (hoursSinceSync <= 72) return 50;
    if (hoursSinceSync <= 168) return 25; // 1 semana
    return 10;
  };

  const needsReconnection = bankingService.needsReconnection(account);
  const needsMFA = account.item_status === 'WAITING_USER_INPUT';
  const typeInfo = getAccountTypeInfo(account.type);
  const statusInfo = getStatusInfo(account.item_status);
  const syncProgress = getSyncProgress();
  return (
    <Card className="hover:shadow-xl transition-all duration-300 overflow-hidden hover:scale-105 bg-gradient-to-br from-card to-card/80" {...testId(TEST_IDS.banking.accountCard)}>
      {/* Status Bar */}
      <div className={`h-1 ${
        needsReconnection ? 'bg-red-500' : 
        syncProgress >= 75 ? 'bg-green-500' : 
        syncProgress >= 50 ? 'bg-yellow-500' : 
        'bg-orange-500'
      }`} />

      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            {/* Bank Logo */}
            <div className="relative">
              {account.connector?.image_url ? (
                <Image
                  src={account.connector.image_url}
                  alt={account.connector.name}
                  width={40}
                  height={40}
                  className="object-contain rounded-lg"
                />
              ) : (
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  <BuildingLibraryIcon className="h-6 w-6 text-gray-400" />
                </div>
              )}
              {account.connector?.is_open_finance && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="absolute -bottom-1 -right-1 bg-white rounded-full p-0.5">
                        <ShieldCheckIcon className="h-3 w-3 text-blue-600" />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Open Finance</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </div>

            {/* Account Info */}
            <div className="flex-1">
              <h3 className="font-semibold text-lg leading-tight bg-gradient-to-r from-blue-800 to-purple-800 bg-clip-text text-transparent">
                {account.display_name || account.name}
              </h3>
              <p className="text-sm text-muted-foreground">
                {account.connector?.name}
              </p>
              {account.masked_number && (
                <p className="text-xs text-muted-foreground/80 mt-1" {...testId(TEST_IDS.banking.accountNumber)}>
                  {account.masked_number}
                </p>
              )}
            </div>
          </div>

          {/* Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <EllipsisVerticalIcon className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem
                onClick={() => router.push(`/transactions?account=${account.id}`)}
              >
                Ver Transações
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => setShowDetails(!showDetails)}
              >
                <InformationCircleIcon className="h-4 w-4 mr-2" />
                Detalhes da Conta
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => onSync(account.id)}
                disabled={isSyncing || needsReconnection}
              >
                <ArrowPathIcon className="h-4 w-4 mr-2" />
                Sincronizar Agora
              </DropdownMenuItem>
              {needsReconnection && (
                <DropdownMenuItem
                  onClick={() => onReconnect(account)}
                  className="text-amber-600"
                >
                  <LinkIcon className="h-4 w-4 mr-2" />
                  Reconectar Conta
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-red-600"
                onClick={() => onRemove(account)}
                {...testId(TEST_IDS.banking.deleteAccountButton)}
              >
                Remover Conta
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Account Type & Status */}
        <div className="flex items-center justify-between gap-2">
          <Badge 
            variant="secondary" 
            className={`${typeInfo.color} border flex items-center gap-1`}
          >
            <typeInfo.icon className="h-3 w-3" />
            {typeInfo.label}
          </Badge>
          
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${statusInfo.color}`} {...testId(TEST_IDS.banking.accountStatus)}>
                  <statusInfo.icon className={`h-4 w-4 ${
                    statusInfo.label === 'Atualizando' || statusInfo.label === 'Conectando' 
                      ? 'animate-spin' 
                      : ''
                  }`} />
                  <span className="text-xs font-medium">{statusInfo.label}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>{statusInfo.description}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        {/* Balance */}
        <div className="space-y-1 p-3 rounded-lg bg-gradient-to-br from-blue-50/50 to-purple-50/50">
          <p className="text-sm text-muted-foreground">Saldo Disponível</p>
          <p className="text-2xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent" {...testId(TEST_IDS.banking.accountBalance)}>
            {bankingService.formatCurrency(account.balance)}
          </p>
          {account.credit_data?.availableCreditLimit && (
            <p className="text-xs text-muted-foreground/80">
              Limite disponível: {bankingService.formatCurrency(account.credit_data.availableCreditLimit)}
            </p>
          )}
        </div>

        {/* Sync Status */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Status da Sincronização</span>
            <span className="text-gray-900 font-medium">{syncProgress}%</span>
          </div>
          <Progress value={syncProgress} className="h-2" />
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Última atualização</span>
            <span>{formatLastSync(account.pluggy_updated_at)}</span>
          </div>
        </div>

        {/* Warnings */}
        {needsMFA && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start gap-2">
              <LockClosedIcon className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-900">
                  Autorização necessária
                </p>
                <p className="text-xs text-yellow-700 mt-1">
                  O banco está solicitando um código de verificação para continuar.
                </p>
              </div>
            </div>
          </div>
        )}
        
        {needsReconnection && !needsMFA && (
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-start gap-2">
              <ExclamationTriangleIcon className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-amber-900">
                  Reconexão necessária
                </p>
                <p className="text-xs text-amber-700 mt-1">
                  O banco solicita nova autenticação para continuar sincronizando.
                </p>
              </div>
            </div>
          </div>
        )}

        {isSyncing && (
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center gap-2">
              <ArrowPathIcon className="h-4 w-4 text-blue-600 animate-spin" />
              <p className="text-sm text-blue-800">
                Sincronizando transações...
              </p>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-2 pt-2">
          {needsMFA ? (
            <Button
              variant="default"
              size="sm"
              className="col-span-2 bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105"
              onClick={() => router.push(`/accounts/mfa/${account.item?.id || account.id}`)}
            >
              <LockClosedIcon className="h-4 w-4 mr-1" />
              Inserir Código de Verificação
            </Button>
          ) : needsReconnection ? (
            <Button
              variant="default"
              size="sm"
              className="col-span-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105"
              onClick={() => onReconnect(account)}
            >
              <LinkIcon className="h-4 w-4 mr-1" />
              Reconectar Conta
            </Button>
          ) : (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onSync(account.id)}
                disabled={isSyncing}
                className="hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 hover:border-blue-300 transition-all duration-300 hover:shadow-md"
                {...testId(TEST_IDS.banking.syncButton)}
              >
                <ArrowPathIcon className={`h-4 w-4 mr-1 ${isSyncing ? 'animate-spin' : ''}`} />
                {isSyncing ? 'Sincronizando' : 'Sincronizar'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push(`/transactions?account=${account.id}`)}
                className="hover:bg-gradient-to-r hover:from-green-50 hover:to-emerald-50 hover:border-green-300 transition-all duration-300 hover:shadow-md"
              >
                Ver Transações
              </Button>
            </>
          )}
        </div>

        {/* Extended Details (Collapsible) */}
        {showDetails && (
          <div className="pt-3 border-t space-y-2">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <p className="text-muted-foreground">Tipo de Conta</p>
                <p className="font-medium">{account.subtype || 'Não especificado'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Moeda</p>
                <p className="font-medium">{account.currency_code}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Número da Conta</p>
                <p className="font-medium">{account.masked_number || 'Não disponível'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Titular</p>
                <p className="font-medium">{account.owner || 'Não informado'}</p>
              </div>
            </div>
            
            {account.item && (
              <div className="pt-2 space-y-1">
                <p className="text-xs text-muted-foreground/80">
                  ID da Conexão: {account.item.pluggy_item_id}
                </p>
                <p className="text-xs text-muted-foreground/80">
                  Criado em: {new Date(account.created_at).toLocaleDateString('pt-BR')}
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}