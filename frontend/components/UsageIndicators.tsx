/**
 * Simplified Usage Indicators Component
 */
import { useQuery } from '@tanstack/react-query';
import { subscriptionService } from '@/services/unified-subscription.service';
import { Progress } from '@/components/ui/progress';
import { 
  ChartBarIcon,
  BanknotesIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

export function UsageIndicators() {
  const { data: limits, isLoading } = useQuery({
    queryKey: ['usage-limits'],
    queryFn: () => subscriptionService.getUsageLimits(),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  });

  if (isLoading || !limits) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1, 2].map(i => (
          <div key={i} className="bg-gray-50 p-4 rounded-lg animate-pulse">
            <div className="h-4 bg-gray-300 rounded w-1/2 mb-2" />
            <div className="h-2 bg-gray-300 rounded" />
          </div>
        ))}
      </div>
    );
  }

  const usageItems = [
    {
      name: 'Transações',
      icon: ChartBarIcon,
      data: limits.transactions,
      color: 'blue',
    },
    {
      name: 'Contas Bancárias',
      icon: BanknotesIcon,
      data: limits.bank_accounts,
      color: 'green',
    },
    // Requisições IA será implementado em breve
    // {
    //   name: 'Requisições IA',
    //   icon: SparklesIcon,
    //   data: limits.ai_requests,
    //   color: 'purple',
    // },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {usageItems.map(item => {
        const Icon = item.icon;
        const percentage = Math.min(100, item.data.percentage);
        const isNearLimit = percentage >= 80;
        const isAtLimit = percentage >= 100;
        
        return (
          <div
            key={item.name}
            className={`p-4 rounded-lg border ${
              isAtLimit 
                ? 'bg-red-50 border-red-200' 
                : isNearLimit 
                ? 'bg-orange-50 border-orange-200' 
                : 'bg-white border-gray-200'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <Icon className={`h-5 w-5 mr-2 ${
                  isAtLimit 
                    ? 'text-red-600' 
                    : isNearLimit 
                    ? 'text-orange-600' 
                    : `text-${item.color}-600`
                }`} />
                <span className="text-sm font-medium text-gray-700">
                  {item.name}
                </span>
              </div>
              <span className={`text-sm font-bold ${
                isAtLimit 
                  ? 'text-red-600' 
                  : isNearLimit 
                  ? 'text-orange-600' 
                  : 'text-gray-600'
              }`}>
                {item.data.used}/{item.data.limit}
              </span>
            </div>
            <Progress 
              value={percentage} 
              className={`h-2 ${
                isAtLimit 
                  ? 'bg-red-200' 
                  : isNearLimit 
                  ? 'bg-orange-200' 
                  : ''
              }`}
              indicatorClassName={
                isAtLimit 
                  ? 'bg-red-500' 
                  : isNearLimit 
                  ? 'bg-orange-500' 
                  : `bg-${item.color}-500`
              }
            />
            <div className="mt-1 text-xs text-gray-500">
              {percentage.toFixed(0)}% usado
            </div>
          </div>
        );
      })}
    </div>
  );
}