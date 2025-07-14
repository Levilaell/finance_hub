'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  ChartBarIcon, 
  BanknotesIcon, 
  UserGroupIcon,
  SparklesIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { UsageLimits } from '@/types';
import { subscriptionService } from '@/services/subscription.service';
import { useAuthStore } from '@/store/auth-store';

export function UsageLimitsCard() {
  const { user } = useAuthStore();
  
  const { data: limits, isLoading } = useQuery({
    queryKey: ['usage-limits'],
    queryFn: () => subscriptionService.getUsageLimits(),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  });

  if (isLoading || !limits) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 80) return 'bg-orange-500';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  const getUsageStatus = (percentage: number) => {
    if (percentage >= 100) return { label: 'Limite Atingido', color: 'bg-red-100 text-red-800' };
    if (percentage >= 90) return { label: 'Quase no Limite', color: 'bg-orange-100 text-orange-800' };
    if (percentage >= 80) return { label: 'Uso Alto', color: 'bg-yellow-100 text-yellow-800' };
    return { label: 'Normal', color: 'bg-green-100 text-green-800' };
  };

  const usageItems = [
    {
      icon: ChartBarIcon,
      title: 'Transações',
      used: limits.transactions.used,
      limit: limits.transactions.limit,
      percentage: limits.transactions.percentage,
      unit: 'transações',
    },
    {
      icon: BanknotesIcon,
      title: 'Contas Bancárias',
      used: limits.bank_accounts.used,
      limit: limits.bank_accounts.limit,
      percentage: limits.bank_accounts.percentage,
      unit: 'contas',
    },
    {
      icon: UserGroupIcon,
      title: 'Usuários',
      used: limits.users.used,
      limit: limits.users.limit,
      percentage: limits.users.percentage,
      unit: 'usuários',
    },
    {
      icon: SparklesIcon,
      title: 'Requisições IA',
      used: limits.ai_requests.used,
      limit: limits.ai_requests.limit,
      percentage: limits.ai_requests.percentage,
      unit: 'requisições',
    },
  ];

  const hasAnyLimitWarning = usageItems.some(item => item.percentage >= 80);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Uso do Plano</CardTitle>
          {hasAnyLimitWarning && (
            <Badge variant="outline" className="bg-orange-50">
              <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
              Atenção aos Limites
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {usageItems.map((item) => {
            const Icon = item.icon;
            const status = getUsageStatus(item.percentage);
            
            return (
              <div key={item.title} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    <Icon className="h-4 w-4 text-gray-500" />
                    <span className="font-medium">{item.title}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-600">
                      {item.used.toLocaleString()} / {item.limit === 999999 ? '∞' : item.limit.toLocaleString()} {item.unit}
                    </span>
                    <Badge className={`text-xs ${status.color}`}>
                      {status.label}
                    </Badge>
                  </div>
                </div>
                <Progress 
                  value={Math.min(item.percentage, 100)} 
                  className="h-2"
                  indicatorClassName={getUsageColor(item.percentage)}
                />
              </div>
            );
          })}
        </div>
        
        {hasAnyLimitWarning && (
          <div className="mt-4 pt-4 border-t">
            <p className="text-sm text-gray-600 mb-3">
              Você está se aproximando dos limites do seu plano. 
              Considere fazer upgrade para continuar crescendo sem interrupções.
            </p>
            <Button size="sm" className="w-full">
              Fazer Upgrade
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}