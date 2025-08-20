/**
 * Pluggy Status Dashboard
 * Real-time monitoring of Pluggy item status with health indicators
 */

import React, { useState, useMemo } from 'react';
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
import { PluggyItem } from '@/types/banking.types';
import { formatDistanceToNow, format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { cn } from '@/lib/utils';

// Utility functions moved outside to be accessible by ItemStatusCard
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
    case 'WAITING_USER_INPUT':
      return {
        color: 'warning',
        icon: Clock,
        label: 'Aguardando MFA',
        description: 'Código de verificação necessário'
      };
    case 'LOGIN_ERROR':
      return {
        color: 'error',
        icon: XCircle,
        label: 'Erro de Login',
        description: 'Credenciais inválidas'
      };
    case 'ERROR':
      return {
        color: 'error',
        icon: XCircle,
        label: 'Erro',
        description: 'Falha na sincronização'
      };
    case 'USER_INPUT_TIMEOUT':
      return {
        color: 'error',
        icon: AlertTriangle,
        label: 'Timeout de MFA',
        description: 'Código não fornecido a tempo'
      };
    default:
      return {
        color: 'info',
        icon: AlertTriangle,
        label: 'Desconhecido',
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
    default: return 'outline';
  }
};

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
    queryFn: () => bankingService.getItems(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const items: PluggyItem[] = itemsData?.results || [];
  
  // Calculate metrics from items data
  const metrics: StatusMetrics = useMemo(() => {
    if (!items.length) {
      return {
        total_items: 0,
        healthy_items: 0,
        warning_items: 0,
        error_items: 0,
        success_rate: 0,
        avg_sync_time: 0
      };
    }

    const total_items = items.length;
    let healthy_items = 0;
    let warning_items = 0;
    let error_items = 0;

    items.forEach(item => {
      const status = item.execution_status || item.status;
      switch (status) {
        case 'UPDATED':
        case 'SUCCESS':
          healthy_items++;
          break;
        case 'WAITING_USER_INPUT':
          warning_items++;
          break;
        case 'LOGIN_ERROR':
        case 'ERROR':
        case 'USER_INPUT_TIMEOUT':
        default:
          error_items++;
          break;
      }
    });

    const success_rate = total_items > 0 ? (healthy_items / total_items) * 100 : 0;

    return {
      total_items,
      healthy_items,
      warning_items,
      error_items,
      success_rate,
      avg_sync_time: 0 // We don't have sync time data, so set to 0
    };
  }, [items]);


  const handleRefresh = () => {
    refetchItems();
  };

  if (itemsLoading) {
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
                return ['WAITING_USER_INPUT', 'OUTDATED'].includes(status);
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
              {item.connector.image_url ? (
                <img 
                  src={item.connector.image_url} 
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
                <h3 className="font-semibold">{item.connector.name}</h3>
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
              <span>{item.accounts_count || 0} conta(s)</span>
            </div>
            <div className="text-xs text-muted-foreground">
              {item.last_successful_update ? (
                <span>Última sync: {formatDistanceToNow(new Date(item.last_successful_update), { 
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
          {['WAITING_USER_INPUT', 'LOGIN_ERROR', 'INVALID_CREDENTIALS'].includes(item.execution_status || item.status) && (
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
