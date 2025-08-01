'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  TrendingUp, 
  TrendingDown,
  RefreshCw,
  Clock,
  CreditCard,
  Users,
  AlertTriangle
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

interface HealthCheck {
  status: 'healthy' | 'unhealthy' | 'skipped';
  message: string;
  metrics?: Record<string, any>;
}

interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  version: string;
  environment: string;
  checks: {
    database: HealthCheck;
    redis: HealthCheck;
    stripe: HealthCheck;
    payments: HealthCheck;
    webhooks: HealthCheck;
    subscriptions: HealthCheck;
  };
}

interface PaymentMetrics {
  timestamp: string;
  periods: {
    last_hour: PeriodMetrics;
    last_24h: PeriodMetrics;
    last_week: PeriodMetrics;
  };
  current_status: {
    active_subscriptions: number;
    trial_subscriptions: number;
    failed_webhooks_pending: number;
  };
}

interface PeriodMetrics {
  total_payments: number;
  successful_payments: number;
  failed_payments: number;
  processing_payments: number;
  success_rate: number;
  total_amount: number;
  average_amount: number;
}

interface Alert {
  type: string;
  severity: 'low' | 'medium' | 'high';
  message: string;
  metrics?: Record<string, any>;
}

interface AlertsResponse {
  timestamp: string;
  alert_count: number;
  alerts: Alert[];
}

export function PaymentHealthDashboard() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds

  // Health check query
  const { data: health, refetch: refetchHealth, isLoading: healthLoading } = useQuery({
    queryKey: ['payment-health'],
    queryFn: () => apiClient.get<HealthStatus>('/api/payments/health/'),
    refetchInterval: autoRefresh ? refreshInterval : false,
    retry: 2,
  });

  // Metrics query
  const { data: metrics, refetch: refetchMetrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['payment-metrics'],
    queryFn: () => apiClient.get<PaymentMetrics>('/api/payments/metrics/'),
    refetchInterval: autoRefresh ? refreshInterval : false,
    retry: 2,
  });

  // Alerts query
  const { data: alerts, refetch: refetchAlerts, isLoading: alertsLoading } = useQuery({
    queryKey: ['payment-alerts'],
    queryFn: () => apiClient.get<AlertsResponse>('/api/payments/alerts/'),
    refetchInterval: autoRefresh ? refreshInterval : false,
    retry: 2,
  });

  const refreshAll = () => {
    refetchHealth();
    refetchMetrics();
    refetchAlerts();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'unhealthy':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'skipped':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return <Badge className="bg-green-100 text-green-800">Healthy</Badge>;
      case 'unhealthy':
        return <Badge className="bg-red-100 text-red-800">Unhealthy</Badge>;
      case 'skipped':
        return <Badge className="bg-yellow-100 text-yellow-800">Skipped</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Unknown</Badge>;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(amount);
  };

  const formatPercentage = (rate: number) => {
    return (rate * 100).toFixed(1) + '%';
  };

  if (healthLoading && metricsLoading && alertsLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Payment System Health</h2>
          <p className="text-muted-foreground">
            Real-time monitoring of payment infrastructure and services
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={refreshAll}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <Clock className="h-4 w-4 mr-2" />
            Auto Refresh
          </Button>
        </div>
      </div>

      {/* Overall Health Status */}
      {health && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center space-x-2">
                {getStatusIcon(health.status)}
                <span>System Health Overview</span>
              </CardTitle>
              <div className="flex items-center space-x-2">
                {getStatusBadge(health.status)}
                <Badge variant="outline">{health.environment}</Badge>
              </div>
            </div>
            <CardDescription>
              Last updated: {new Date(health.timestamp).toLocaleString()}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {Object.entries(health.checks).map(([key, check]) => (
                <div key={key} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(check.status)}
                    <div>
                      <p className="font-medium capitalize">{key.replace('_', ' ')}</p>
                      <p className="text-sm text-muted-foreground">{check.message}</p>
                    </div>
                  </div>
                  {getStatusBadge(check.status)}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Alerts */}
      {alerts && alerts.alert_count > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              <span>Active Alerts ({alerts.alert_count})</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {alerts.alerts.map((alert, index) => (
                <Alert key={index} className={getSeverityColor(alert.severity)}>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <div className="flex items-center justify-between">
                      <span>{alert.message}</span>
                      <Badge variant="outline" className="capitalize">
                        {alert.severity}
                      </Badge>
                    </div>
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Metrics Dashboard */}
      {metrics && (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Current Status */}
          <Card>
            <CardHeader>
              <CardTitle>Current Status</CardTitle>
              <CardDescription>Real-time system status</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Users className="h-4 w-4 text-green-500" />
                  <span>Active Subscriptions</span>
                </div>
                <span className="font-bold text-2xl text-green-600">
                  {metrics.current_status.active_subscriptions}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-blue-500" />
                  <span>Trial Subscriptions</span>
                </div>
                <span className="font-bold text-2xl text-blue-600">
                  {metrics.current_status.trial_subscriptions}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="h-4 w-4 text-red-500" />
                  <span>Failed Webhooks</span>
                </div>
                <span className="font-bold text-2xl text-red-600">
                  {metrics.current_status.failed_webhooks_pending}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Payment Metrics */}
          <Card>
            <CardHeader>
              <CardTitle>Payment Metrics</CardTitle>
              <CardDescription>Payment processing statistics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Last Hour */}
                <div className="border-b pb-3">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-medium">Last Hour</h4>
                    <div className="flex items-center space-x-2">
                      {metrics.periods.last_hour.success_rate >= 0.95 ? (
                        <TrendingUp className="h-4 w-4 text-green-500" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-500" />
                      )}
                      <span className="font-bold">
                        {formatPercentage(metrics.periods.last_hour.success_rate)}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Total: </span>
                      <span className="font-medium">{metrics.periods.last_hour.total_payments}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Failed: </span>
                      <span className="font-medium text-red-600">{metrics.periods.last_hour.failed_payments}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Amount: </span>
                      <span className="font-medium">{formatCurrency(metrics.periods.last_hour.total_amount)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Avg: </span>
                      <span className="font-medium">{formatCurrency(metrics.periods.last_hour.average_amount)}</span>
                    </div>
                  </div>
                </div>

                {/* Last 24h */}
                <div className="border-b pb-3">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-medium">Last 24 Hours</h4>
                    <div className="flex items-center space-x-2">
                      {metrics.periods.last_24h.success_rate >= 0.95 ? (
                        <TrendingUp className="h-4 w-4 text-green-500" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-500" />
                      )}
                      <span className="font-bold">
                        {formatPercentage(metrics.periods.last_24h.success_rate)}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Total: </span>
                      <span className="font-medium">{metrics.periods.last_24h.total_payments}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Failed: </span>
                      <span className="font-medium text-red-600">{metrics.periods.last_24h.failed_payments}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Amount: </span>
                      <span className="font-medium">{formatCurrency(metrics.periods.last_24h.total_amount)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Avg: </span>
                      <span className="font-medium">{formatCurrency(metrics.periods.last_24h.average_amount)}</span>
                    </div>
                  </div>
                </div>

                {/* Last Week */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-medium">Last Week</h4>
                    <div className="flex items-center space-x-2">
                      {metrics.periods.last_week.success_rate >= 0.95 ? (
                        <TrendingUp className="h-4 w-4 text-green-500" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-500" />
                      )}
                      <span className="font-bold">
                        {formatPercentage(metrics.periods.last_week.success_rate)}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Total: </span>
                      <span className="font-medium">{metrics.periods.last_week.total_payments}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Failed: </span>
                      <span className="font-medium text-red-600">{metrics.periods.last_week.failed_payments}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Amount: </span>
                      <span className="font-medium">{formatCurrency(metrics.periods.last_week.total_amount)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Avg: </span>
                      <span className="font-medium">{formatCurrency(metrics.periods.last_week.average_amount)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export default PaymentHealthDashboard;