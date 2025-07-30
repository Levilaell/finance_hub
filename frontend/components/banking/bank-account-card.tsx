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
} from '@heroicons/react/24/outline';

import { BankAccount, PluggyItemStatus } from '@/types/banking.types';
import { bankingService } from '@/services/banking.service';

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
        color: 'bg-blue-100 text-blue-800 border-blue-200' 
      },
      CREDIT: { 
        label: 'Cartão de Crédito', 
        icon: CreditCardIcon,
        color: 'bg-purple-100 text-purple-800 border-purple-200' 
      },
      INVESTMENT: { 
        label: 'Investimento', 
        icon: ChartBarIcon,
        color: 'bg-green-100 text-green-800 border-green-200' 
      },
      LOAN: { 
        label: 'Empréstimo', 
        icon: BanknotesIcon,
        color: 'bg-orange-100 text-orange-800 border-orange-200' 
      },
      OTHER: { 
        label: 'Outro', 
        icon: BuildingLibraryIcon,
        color: 'bg-gray-100 text-gray-800 border-gray-200' 
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
        color: 'text-green-600 bg-green-50',
        description: 'Sincronização concluída com sucesso'
      },
      'LOGIN_ERROR': { 
        label: 'Erro de Login', 
        icon: XCircleIcon,
        color: 'text-red-600 bg-red-50',
        description: 'Credenciais inválidas ou expiradas'
      },
      'ERROR': { 
        label: 'Erro', 
        icon: XCircleIcon,
        color: 'text-red-600 bg-red-50',
        description: 'Erro ao sincronizar com o banco'
      },
      'WAITING_USER_INPUT': { 
        label: 'Aguardando', 
        icon: ExclamationTriangleIcon,
        color: 'text-amber-600 bg-amber-50',
        description: 'Necessária autenticação adicional'
      },
      'OUTDATED': { 
        label: 'Desatualizado', 
        icon: ClockIcon,
        color: 'text-amber-600 bg-amber-50',
        description: 'Dados precisam ser atualizados'
      },
      'UPDATING': { 
        label: 'Atualizando', 
        icon: ArrowPathIcon,
        color: 'text-blue-600 bg-blue-50',
        description: 'Sincronização em andamento'
      },
      'LOGIN_IN_PROGRESS': { 
        label: 'Conectando', 
        icon: ArrowPathIcon,
        color: 'text-blue-600 bg-blue-50',
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
  const typeInfo = getAccountTypeInfo(account.type);
  const statusInfo = getStatusInfo(account.item_status);
  const syncProgress = getSyncProgress();
  
  // Debug log para verificar o status
  console.log(`Account ${account.display_name} - Status: ${account.item_status}`);

  return (
    <Card className="hover:shadow-lg transition-all duration-300 overflow-hidden">
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
              <h3 className="font-semibold text-lg leading-tight">
                {account.display_name || account.name}
              </h3>
              <p className="text-sm text-gray-600">
                {account.connector?.name}
              </p>
              {account.masked_number && (
                <p className="text-xs text-gray-500 mt-1">
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
                <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${statusInfo.color}`}>
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
        <div className="space-y-1">
          <p className="text-sm text-gray-600">Saldo Disponível</p>
          <p className="text-2xl font-bold">
            {bankingService.formatCurrency(account.balance)}
          </p>
          {account.credit_data?.availableCreditLimit && (
            <p className="text-xs text-gray-500">
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
        {needsReconnection && (
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
          {needsReconnection ? (
            <Button
              variant="default"
              size="sm"
              className="col-span-2"
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
              >
                <ArrowPathIcon className={`h-4 w-4 mr-1 ${isSyncing ? 'animate-spin' : ''}`} />
                {isSyncing ? 'Sincronizando' : 'Sincronizar'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push(`/transactions?account=${account.id}`)}
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
                <p className="text-gray-600">Tipo de Conta</p>
                <p className="font-medium">{account.subtype || 'Não especificado'}</p>
              </div>
              <div>
                <p className="text-gray-600">Moeda</p>
                <p className="font-medium">{account.currency_code}</p>
              </div>
              <div>
                <p className="text-gray-600">Número da Conta</p>
                <p className="font-medium">{account.masked_number || 'Não disponível'}</p>
              </div>
              <div>
                <p className="text-gray-600">Titular</p>
                <p className="font-medium">{account.owner || 'Não informado'}</p>
              </div>
            </div>
            
            {account.item && (
              <div className="pt-2 space-y-1">
                <p className="text-xs text-gray-500">
                  ID da Conexão: {account.item.pluggy_item_id}
                </p>
                <p className="text-xs text-gray-500">
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