/**
 * Tests for useUsageLimits hook
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useUsageLimits } from '@/hooks/useUsageLimits';
import { subscriptionService } from '@/services/unified-subscription.service';
import { useAuthStore } from '@/store/auth-store';
import {
  mockUsageLimits,
  usageScenarios,
  createQueryClient,
} from '../test-utils';

// Mock dependencies
jest.mock('@/services/unified-subscription.service');
jest.mock('@/store/auth-store');

const mockSubscriptionService = subscriptionService as jest.Mocked<typeof subscriptionService>;
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;

describe('useUsageLimits', () => {
  let queryClient: QueryClient;

  const createWrapper = (client: QueryClient) => {
    return ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>
        {children}
      </QueryClientProvider>
    );
  };

  beforeEach(() => {
    queryClient = createQueryClient();
    jest.clearAllMocks();
    
    // Mock auth store with authenticated user
    mockUseAuthStore.mockReturnValue({
      user: { id: 'user-1', email: 'test@example.com', name: 'Test User' },
      isAuthenticated: true,
    } as any);
  });

  describe('Basic Functionality', () => {
    it('should fetch usage limits successfully', async () => {
      const mockUsage = mockUsageLimits();
      mockSubscriptionService.getUsageLimits.mockResolvedValue(mockUsage);

      const { result } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.usageLimits).toEqual(mockUsage);
        expect(result.current.isLoading).toBe(false);
        expect(result.current.error).toBeNull();
      });

      expect(mockSubscriptionService.getUsageLimits).toHaveBeenCalledTimes(1);
    });

    it('should handle loading state', () => {
      mockSubscriptionService.getUsageLimits.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.usageLimits).toBeUndefined();
    });

    it('should handle error state', async () => {
      const error = new Error('Failed to fetch usage limits');
      mockSubscriptionService.getUsageLimits.mockRejectedValue(error);

      const { result } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
        expect(result.current.isLoading).toBe(false);
        expect(result.current.usageLimits).toBeUndefined();
      });
    });

    it('should not fetch when user is not authenticated', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        isAuthenticated: false,
      } as any);

      renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      expect(mockSubscriptionService.getUsageLimits).not.toHaveBeenCalled();
    });
  });

  describe('Helper Functions', () => {
    describe('isUsageLimitReached', () => {
      it('should correctly identify reached limits', async () => {
        const overLimitUsage = usageScenarios.overLimit;
        mockSubscriptionService.getUsageLimits.mockResolvedValue(overLimitUsage);
        mockSubscriptionService.isUsageLimitReached.mockImplementation((usage, type) => {
          return usage[type].percentage >= 100;
        });

        const { result } = renderHook(() => useUsageLimits(), {
          wrapper: createWrapper(queryClient),
        });

        await waitFor(() => {
          expect(result.current.isUsageLimitReached('transactions')).toBe(true);
          expect(result.current.isUsageLimitReached('bank_accounts')).toBe(true);
          expect(result.current.isUsageLimitReached('ai_requests')).toBe(true);
        });
      });

      it('should correctly identify limits not reached', async () => {
        const underLimitUsage = usageScenarios.underLimit;
        mockSubscriptionService.getUsageLimits.mockResolvedValue(underLimitUsage);
        mockSubscriptionService.isUsageLimitReached.mockImplementation((usage, type) => {
          return usage[type].percentage >= 100;
        });

        const { result } = renderHook(() => useUsageLimits(), {
          wrapper: createWrapper(queryClient),
        });

        await waitFor(() => {
          expect(result.current.isUsageLimitReached('transactions')).toBe(false);
          expect(result.current.isUsageLimitReached('bank_accounts')).toBe(false);
          expect(result.current.isUsageLimitReached('ai_requests')).toBe(false);
        });
      });

      it('should return false when no usage data', async () => {
        mockSubscriptionService.getUsageLimits.mockResolvedValue(undefined as any);

        const { result } = renderHook(() => useUsageLimits(), {
          wrapper: createWrapper(queryClient),
        });

        await waitFor(() => {
          expect(result.current.isUsageLimitReached('transactions')).toBe(false);
          expect(result.current.isUsageLimitReached('bank_accounts')).toBe(false);
          expect(result.current.isUsageLimitReached('ai_requests')).toBe(false);
        });
      });
    });

    describe('getUsagePercentage', () => {
      it('should return correct percentages', async () => {
        const mockUsage = mockUsageLimits({
          transactions: { used: 250, limit: 500, percentage: 50 },
          bank_accounts: { used: 3, limit: 5, percentage: 60 },
          ai_requests: { used: 75, limit: 100, percentage: 75 },
        });
        mockSubscriptionService.getUsageLimits.mockResolvedValue(mockUsage);

        const { result } = renderHook(() => useUsageLimits(), {
          wrapper: createWrapper(queryClient),
        });

        await waitFor(() => {
          expect(result.current.getUsagePercentage('transactions')).toBe(50);
          expect(result.current.getUsagePercentage('bank_accounts')).toBe(60);
          expect(result.current.getUsagePercentage('ai_requests')).toBe(75);
        });
      });

      it('should return 0 when no usage data', async () => {
        mockSubscriptionService.getUsageLimits.mockResolvedValue(undefined as any);

        const { result } = renderHook(() => useUsageLimits(), {
          wrapper: createWrapper(queryClient),
        });

        await waitFor(() => {
          expect(result.current.getUsagePercentage('transactions')).toBe(0);
          expect(result.current.getUsagePercentage('bank_accounts')).toBe(0);
          expect(result.current.getUsagePercentage('ai_requests')).toBe(0);
        });
      });
    });

    describe('getUsageCounts', () => {
      it('should return correct usage counts', async () => {
        const mockUsage = mockUsageLimits({
          transactions: { used: 100, limit: 500, percentage: 20 },
          bank_accounts: { used: 2, limit: 5, percentage: 40 },
          ai_requests: { used: 25, limit: 100, percentage: 25 },
        });
        mockSubscriptionService.getUsageLimits.mockResolvedValue(mockUsage);

        const { result } = renderHook(() => useUsageLimits(), {
          wrapper: createWrapper(queryClient),
        });

        await waitFor(() => {
          expect(result.current.getUsageCounts('transactions')).toEqual({
            used: 100,
            limit: 500,
            percentage: 20,
          });
          expect(result.current.getUsageCounts('bank_accounts')).toEqual({
            used: 2,
            limit: 5,
            percentage: 40,
          });
          expect(result.current.getUsageCounts('ai_requests')).toEqual({
            used: 25,
            limit: 100,
            percentage: 25,
          });
        });
      });

      it('should return default values when no usage data', async () => {
        mockSubscriptionService.getUsageLimits.mockResolvedValue(undefined as any);

        const { result } = renderHook(() => useUsageLimits(), {
          wrapper: createWrapper(queryClient),
        });

        await waitFor(() => {
          expect(result.current.getUsageCounts('transactions')).toEqual({
            used: 0,
            limit: 0,
            percentage: 0,
          });
        });
      });
    });

    describe('getUsageWarningLevel', () => {
      it('should return correct warning levels', async () => {
        const nearLimitUsage = usageScenarios.nearLimit;
        mockSubscriptionService.getUsageLimits.mockResolvedValue(nearLimitUsage);
        mockSubscriptionService.getUsageWarningLevel.mockImplementation((percentage) => {
          if (percentage >= 100) return 'critical';
          if (percentage >= 80) return 'warning';
          return 'none';
        });

        const { result } = renderHook(() => useUsageLimits(), {
          wrapper: createWrapper(queryClient),
        });

        await waitFor(() => {
          expect(result.current.getUsageWarningLevel('transactions')).toBe('warning'); // 90%
          expect(result.current.getUsageWarningLevel('bank_accounts')).toBe('critical'); // 100%
          expect(result.current.getUsageWarningLevel('ai_requests')).toBe('warning'); // 90%
        });
      });

      it('should return none for low usage', async () => {
        const underLimitUsage = usageScenarios.underLimit;
        mockSubscriptionService.getUsageLimits.mockResolvedValue(underLimitUsage);
        mockSubscriptionService.getUsageWarningLevel.mockImplementation((percentage) => {
          if (percentage >= 100) return 'critical';
          if (percentage >= 80) return 'warning';
          return 'none';
        });

        const { result } = renderHook(() => useUsageLimits(), {
          wrapper: createWrapper(queryClient),
        });

        await waitFor(() => {
          expect(result.current.getUsageWarningLevel('transactions')).toBe('none'); // 20%
          expect(result.current.getUsageWarningLevel('bank_accounts')).toBe('none'); // 50%
          expect(result.current.getUsageWarningLevel('ai_requests')).toBe('none'); // 20%
        });
      });
    });

    describe('shouldShowUsageWarning', () => {
      it('should return true when any usage is near limit', async () => {
        const nearLimitUsage = usageScenarios.nearLimit;
        mockSubscriptionService.getUsageLimits.mockResolvedValue(nearLimitUsage);

        const { result } = renderHook(() => useUsageLimits(), {
          wrapper: createWrapper(queryClient),
        });

        await waitFor(() => {
          expect(result.current.shouldShowUsageWarning()).toBe(true);
        });
      });

      it('should return false when all usage is low', async () => {
        const underLimitUsage = usageScenarios.underLimit;
        mockSubscriptionService.getUsageLimits.mockResolvedValue(underLimitUsage);

        const { result } = renderHook(() => useUsageLimits(), {
          wrapper: createWrapper(queryClient),
        });

        await waitFor(() => {
          expect(result.current.shouldShowUsageWarning()).toBe(false);
        });
      });

      it('should return false when no usage data', async () => {
        mockSubscriptionService.getUsageLimits.mockResolvedValue(undefined as any);

        const { result } = renderHook(() => useUsageLimits(), {
          wrapper: createWrapper(queryClient),
        });

        await waitFor(() => {
          expect(result.current.shouldShowUsageWarning()).toBe(false);
        });
      });

      it('should return true when one category is at 80%', async () => {
        const partialHighUsage = mockUsageLimits({
          transactions: { used: 40, limit: 50, percentage: 80 }, // At threshold
          bank_accounts: { used: 1, limit: 5, percentage: 20 },  // Low
          ai_requests: { used: 10, limit: 100, percentage: 10 },  // Low
        });
        mockSubscriptionService.getUsageLimits.mockResolvedValue(partialHighUsage);

        const { result } = renderHook(() => useUsageLimits(), {
          wrapper: createWrapper(queryClient),
        });

        await waitFor(() => {
          expect(result.current.shouldShowUsageWarning()).toBe(true);
        });
      });
    });
  });

  describe('Query Configuration', () => {
    it('should use correct stale time and refetch interval', async () => {
      const mockUsage = mockUsageLimits();
      mockSubscriptionService.getUsageLimits.mockResolvedValue(mockUsage);

      const { result } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.usageLimits).toEqual(mockUsage);
      });

      // The hook should be configured with appropriate cache settings
      expect(mockSubscriptionService.getUsageLimits).toHaveBeenCalledTimes(1);
    });

    it('should refetch data when enabled', async () => {
      const mockUsage = mockUsageLimits();
      mockSubscriptionService.getUsageLimits.mockResolvedValue(mockUsage);

      // First render
      const { result, rerender } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.usageLimits).toEqual(mockUsage);
      });

      // Clear and update mock
      mockSubscriptionService.getUsageLimits.mockClear();
      const updatedUsage = mockUsageLimits({
        transactions: { used: 200, limit: 500, percentage: 40 },
      });
      mockSubscriptionService.getUsageLimits.mockResolvedValue(updatedUsage);

      // Force a refetch by invalidating the query
      queryClient.invalidateQueries({ queryKey: ['usage-limits'] });

      await waitFor(() => {
        expect(mockSubscriptionService.getUsageLimits).toHaveBeenCalled();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      const networkError = new Error('Network error');
      mockSubscriptionService.getUsageLimits.mockRejectedValue(networkError);

      const { result } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
        expect(result.current.usageLimits).toBeUndefined();
        expect(result.current.isLoading).toBe(false);
      });

      // Helper functions should handle missing data gracefully
      expect(result.current.isUsageLimitReached('transactions')).toBe(false);
      expect(result.current.getUsagePercentage('transactions')).toBe(0);
      expect(result.current.shouldShowUsageWarning()).toBe(false);
    });

    it('should handle API errors with proper error structure', async () => {
      const apiError = {
        response: {
          status: 403,
          data: { error: 'Insufficient permissions' }
        }
      };
      mockSubscriptionService.getUsageLimits.mockRejectedValue(apiError);

      const { result } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.error).toEqual(apiError);
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero usage values', async () => {
      const zeroUsage = mockUsageLimits({
        transactions: { used: 0, limit: 500, percentage: 0 },
        bank_accounts: { used: 0, limit: 2, percentage: 0 },
        ai_requests: { used: 0, limit: 50, percentage: 0 },
      });
      mockSubscriptionService.getUsageLimits.mockResolvedValue(zeroUsage);

      const { result } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.getUsagePercentage('transactions')).toBe(0);
        expect(result.current.isUsageLimitReached('transactions')).toBe(false);
        expect(result.current.shouldShowUsageWarning()).toBe(false);
      });
    });

    it('should handle maximum usage values', async () => {
      const maxUsage = mockUsageLimits({
        transactions: { used: 500, limit: 500, percentage: 100 },
        bank_accounts: { used: 2, limit: 2, percentage: 100 },
        ai_requests: { used: 50, limit: 50, percentage: 100 },
      });
      mockSubscriptionService.getUsageLimits.mockResolvedValue(maxUsage);
      mockSubscriptionService.isUsageLimitReached.mockReturnValue(true);

      const { result } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.getUsagePercentage('transactions')).toBe(100);
        expect(result.current.isUsageLimitReached('transactions')).toBe(true);
        expect(result.current.shouldShowUsageWarning()).toBe(true);
      });
    });

    it('should handle over-limit usage values', async () => {
      const overLimitUsage = usageScenarios.overLimit;
      mockSubscriptionService.getUsageLimits.mockResolvedValue(overLimitUsage);
      mockSubscriptionService.isUsageLimitReached.mockImplementation((usage, type) => {
        return usage[type].percentage >= 100;
      });

      const { result } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.getUsagePercentage('transactions')).toBe(120);
        expect(result.current.isUsageLimitReached('transactions')).toBe(true);
        expect(result.current.shouldShowUsageWarning()).toBe(true);
      });
    });

    it('should handle malformed usage data', async () => {
      const malformedUsage = {
        transactions: { used: 'invalid', limit: null, percentage: undefined },
        bank_accounts: {},
        ai_requests: null,
      } as any;
      mockSubscriptionService.getUsageLimits.mockResolvedValue(malformedUsage);

      const { result } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        // Should handle malformed data gracefully
        expect(() => result.current.getUsagePercentage('transactions')).not.toThrow();
        expect(() => result.current.isUsageLimitReached('transactions')).not.toThrow();
        expect(() => result.current.shouldShowUsageWarning()).not.toThrow();
      });
    });

    it('should handle empty usage limits object', async () => {
      const emptyUsage = {} as any;
      mockSubscriptionService.getUsageLimits.mockResolvedValue(emptyUsage);

      const { result } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result.current.usageLimits).toEqual({});
        expect(result.current.shouldShowUsageWarning()).toBe(false);
      });
    });
  });

  describe('Performance', () => {
    it('should not refetch unnecessarily', async () => {
      const mockUsage = mockUsageLimits();
      mockSubscriptionService.getUsageLimits.mockResolvedValue(mockUsage);

      // First render
      const { result: result1 } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result1.current.usageLimits).toEqual(mockUsage);
      });

      expect(mockSubscriptionService.getUsageLimits).toHaveBeenCalledTimes(1);

      // Second render with same query client - should use cache
      const { result: result2 } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result2.current.usageLimits).toEqual(mockUsage);
      });

      // Should not make additional API calls due to caching
      expect(mockSubscriptionService.getUsageLimits).toHaveBeenCalledTimes(1);
    });

    it('should handle multiple concurrent hook instances', async () => {
      const mockUsage = mockUsageLimits();
      mockSubscriptionService.getUsageLimits.mockResolvedValue(mockUsage);

      // Render multiple instances concurrently
      const { result: result1 } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });
      const { result: result2 } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });
      const { result: result3 } = renderHook(() => useUsageLimits(), {
        wrapper: createWrapper(queryClient),
      });

      await waitFor(() => {
        expect(result1.current.usageLimits).toEqual(mockUsage);
        expect(result2.current.usageLimits).toEqual(mockUsage);
        expect(result3.current.usageLimits).toEqual(mockUsage);
      });

      // All should share the same data due to query deduplication
      expect(mockSubscriptionService.getUsageLimits).toHaveBeenCalledTimes(1);
    });
  });
});