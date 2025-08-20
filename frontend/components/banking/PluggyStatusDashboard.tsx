/**
 * Pluggy Status Dashboard
 * Real-time monitoring of Pluggy item status with health indicators
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle, 
  RefreshCw,
  Wifi,
  Activity,
  TrendingUp,
  Settings,
  Eye
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { bankingService } from '@/services/banking.service';
import { formatDistanceToNow, format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { cn } from '@/lib/utils';

interface PluggyItem {
  id: string;
  pluggy_item_id: string;
  status: string;
  execution_status: string;
  connector: {
    id: number;
    name: string;
    institutional_name: string;
    logo_url?: string;
  };
  created_at: string;
  updated_at: string;
  last_sync_at?: string;
  error_message?: string;
  accounts_count: number;
  transactions_count: number;
}

interface StatusMetrics {
  total_items: number;
  healthy_items: number;
  warning_items: number;
  error_items: number;
  success_rate: number;
  avg_sync_time: number;
}

export function PluggyStatusDashboard() {
  const [selectedTab, setSelectedTab] = useState('overview');

  // Query for items status
  const { data: itemsData, isLoading: itemsLoading, refetch: refetchItems } = useQuery({
    queryKey: ['banking', 'items-status'],
    queryFn: () => bankingService.getItemsStatus(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Query for status metrics
  const { data: metricsData, isLoading: metricsLoading } = useQuery({
    queryKey: ['banking', 'status-metrics'],
    queryFn: () => bankingService.getStatusMetrics(),
    refetchInterval: 60000, // Refresh every minute
  });

  const items: PluggyItem[] = itemsData?.data || [];
  const metrics: StatusMetrics = metricsData?.data || {
    total_items: 0,
    healthy_items: 0,
    warning_items: 0,
    error_items: 0,
    success_rate: 0,
    avg_sync_time: 0
  };

  const getStatusInfo = (item: PluggyItem) => {
    const status = item.execution_status || item.status;
    
    switch (status) {
      case 'UPDATED':
      case 'SUCCESS':
        return {
          color: 'success',
          icon: CheckCircle,
          label: 'Funcionando',
          description: 'Sincronizando normalmente'
        };
      case 'WAITING_USER_ACTION':
        return {
          color: 'warning',
          icon: Clock,
          label: 'Aguardando MFA',
          description: 'Código de verificação necessário'
        };
      case 'LOGIN_ERROR':
      case 'INVALID_CREDENTIALS':
        return {
          color: 'error',
          icon: XCircle,
          label: 'Erro de Login',
          description: 'Credenciais inválidas'
        };
      case 'OUTDATED':
        return {
          color: 'warning',
          icon: AlertTriangle,
          label: 'Desatualizado',
          description: 'Necessita sincronização'
        };
      case 'CREATING':
      case 'UPDATING':
        return {
          color: 'info',
          icon: RefreshCw,
          label: 'Processando',
          description: 'Sincronização em andamento'
        };
      default:
        return {
          color: 'secondary',
          icon: AlertTriangle,
          label: status || 'Desconhecido',
          description: 'Status não reconhecido'
        };
    }
  };

  const getVariantFromColor = (color: string) => {
    switch (color) {
      case 'success': return 'default';
      case 'warning': return 'secondary';
      case 'error': return 'destructive';
      case 'info': return 'outline';
      default: return 'secondary';
    }
  };

  const handleRefresh = () => {
    refetchItems();
  };

  if (itemsLoading || metricsLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin" />
          <span className="ml-2">Carregando status...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Status dos Bancos</h2>
          <p className="text-muted-foreground">
            Monitoramento em tempo real das conexões bancárias
          </p>
        </div>
        <Button onClick={handleRefresh} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Atualizar
        </Button>
      </div>

      {/* Metrics Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-blue-500" />
              <div>
                <p className="text-sm font-medium">Total</p>
                <p className="text-2xl font-bold">{metrics.total_items}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <div>
                <p className="text-sm font-medium">Funcionando</p>
                <p className="text-2xl font-bold text-green-600">{metrics.healthy_items}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              <div>
                <p className="text-sm font-medium">Atenção</p>
                <p className="text-2xl font-bold text-yellow-600">{metrics.warning_items}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <XCircle className="h-4 w-4 text-red-500" />
              <div>
                <p className="text-sm font-medium">Erro</p>
                <p className="text-2xl font-bold text-red-600">{metrics.error_items}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Success Rate */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4" />
              <span className="font-medium">Taxa de Sucesso</span>
            </div>
            <span className="text-sm font-medium">{metrics.success_rate.toFixed(1)}%</span>
          </div>
          <Progress value={metrics.success_rate} className="h-2" />
        </CardContent>
      </Card>

      {/* Items List */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Visão Geral</TabsTrigger>
          <TabsTrigger value="healthy">Funcionando ({metrics.healthy_items})</TabsTrigger>
          <TabsTrigger value="warning">Atenção ({metrics.warning_items})</TabsTrigger>
          <TabsTrigger value="error">Erros ({metrics.error_items})</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {items.length === 0 ? (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Nenhuma conta bancária conectada. Conecte uma conta para começar o monitoramento.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="grid gap-4">
              {items.map((item) => (
                <ItemStatusCard key={item.id} item={item} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="healthy" className="space-y-4">
          <div className="grid gap-4">
            {items
              .filter(item => {
                const status = item.execution_status || item.status;
                return ['UPDATED', 'SUCCESS'].includes(status);
              })
              .map((item) => (
                <ItemStatusCard key={item.id} item={item} />
              ))}
          </div>
        </TabsContent>

        <TabsContent value="warning" className="space-y-4">
          <div className="grid gap-4">
            {items
              .filter(item => {
                const status = item.execution_status || item.status;
                return ['WAITING_USER_ACTION', 'OUTDATED'].includes(status);
              })
              .map((item) => (
                <ItemStatusCard key={item.id} item={item} />
              ))}
          </div>
        </TabsContent>

        <TabsContent value="error" className="space-y-4">
          <div className="grid gap-4">
            {items
              .filter(item => {
                const status = item.execution_status || item.status;
                return ['LOGIN_ERROR', 'INVALID_CREDENTIALS', 'ERROR'].includes(status);
              })
              .map((item) => (
                <ItemStatusCard key={item.id} item={item} />
              ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ItemStatusCard({ item }: { item: PluggyItem }) {
  const statusInfo = getStatusInfo(item);
  const StatusIcon = statusInfo.icon;

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Bank Logo */}
            <div className="flex-shrink-0">
              {item.connector.logo_url ? (
                <img 
                  src={item.connector.logo_url} 
                  alt={item.connector.name}
                  className="w-12 h-12 rounded-lg object-contain"
                />
              ) : (
                <div className="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center">
                  <Wifi className="h-6 w-6 text-gray-400" />
                </div>
              )}
            </div>

            {/* Bank Info */}
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <h3 className="font-semibold">{item.connector.institutional_name}</h3>
                <Badge variant={getVariantFromColor(statusInfo.color)}>
                  <StatusIcon className="h-3 w-3 mr-1" />
                  {statusInfo.label}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">{statusInfo.description}</p>
              {item.error_message && (
                <p className="text-sm text-red-600 mt-1">{item.error_message}</p>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="text-right space-y-1">
            <div className="flex items-center space-x-4 text-sm text-muted-foreground">
              <span>{item.accounts_count} conta(s)</span>
              <span>{item.transactions_count} transações</span>
            </div>
            <div className="text-xs text-muted-foreground">
              {item.last_sync_at ? (
                <span>Última sync: {formatDistanceToNow(new Date(item.last_sync_at), { 
                  addSuffix: true, 
                  locale: ptBR 
                })}</span>
              ) : (
                <span>Atualizado: {formatDistanceToNow(new Date(item.updated_at), { 
                  addSuffix: true, 
                  locale: ptBR 
                })}</span>
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end space-x-2 mt-4 pt-4 border-t">
          <Button variant="outline" size="sm">
            <Eye className="h-3 w-3 mr-1" />
            Detalhes
          </Button>
          <Button variant="outline" size="sm">
            <Settings className="h-3 w-3 mr-1" />
            Configurar
          </Button>
          {['WAITING_USER_ACTION', 'LOGIN_ERROR', 'INVALID_CREDENTIALS'].includes(item.execution_status || item.status) && (
            <Button size="sm">
              <Wifi className="h-3 w-3 mr-1" />
              Reconectar
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}