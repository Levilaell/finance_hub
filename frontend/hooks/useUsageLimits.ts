/**
 * Usage Limits Hook - Separate from subscription data
 * 
 * Handles usage tracking and limits checking for the current company.
 * Usage data comes from /api/companies/usage-limits/ endpoint.
 */
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth-store';
import { subscriptionService, UsageLimits } from '@/services/unified-subscription.service';

export function useUsageLimits() {
  const { user } = useAuthStore();

  // Get usage limits
  const { data: usageLimits, isLoading, error } = useQuery({
    queryKey: ['usage-limits'],
    queryFn: subscriptionService.getUsageLimits,
    enabled: !!user,
    staleTime: 1000 * 60 * 2, // 2 minutes (more frequent than subscription status)
    refetchInterval: 1000 * 60 * 5, // Refetch every 5 minutes
  });

  // Helper functions
  const isUsageLimitReached = (type: keyof UsageLimits): boolean => {
    if (!usageLimits) return false;
    return subscriptionService.isUsageLimitReached(usageLimits, type);
  };

  const getUsagePercentage = (type: keyof UsageLimits): number => {
    if (!usageLimits) return 0;
    return usageLimits[type].percentage;
  };

  const getUsageCounts = (type: keyof UsageLimits) => {
    if (!usageLimits) return { used: 0, limit: 0, percentage: 0 };
    return usageLimits[type];
  };

  const getUsageWarningLevel = (type: keyof UsageLimits): 'none' | 'warning' | 'critical' => {
    const percentage = getUsagePercentage(type);
    return subscriptionService.getUsageWarningLevel(percentage);
  };

  const shouldShowUsageWarning = (): boolean => {
    if (!usageLimits) return false;
    
    const types: Array<keyof UsageLimits> = ['transactions', 'bank_accounts', 'ai_requests'];
    return types.some(type => getUsagePercentage(type) >= 80);
  };

  return {
    usageLimits,
    isLoading,
    error,
    isUsageLimitReached,
    getUsagePercentage,
    getUsageCounts,
    getUsageWarningLevel,
    shouldShowUsageWarning,
  };
}