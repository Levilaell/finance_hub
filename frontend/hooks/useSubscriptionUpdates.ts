import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth-store';

export function useSubscriptionUpdates() {
  const queryClient = useQueryClient();
  const { fetchUser } = useAuthStore();

  useEffect(() => {
    const handleSubscriptionUpdate = async () => {
      try {
        // Invalidate all queries to force refetch
        await queryClient.invalidateQueries();
        
        // Fetch fresh user data
        await fetchUser();
        
        // Clear specific caches that might be holding old data
        queryClient.removeQueries({ queryKey: ['dashboard'] });
        queryClient.removeQueries({ queryKey: ['company'] });
        queryClient.removeQueries({ queryKey: ['subscription'] });
        queryClient.removeQueries({ queryKey: ['user'] });
      } catch (error) {
        console.error('Error handling subscription update:', error);
      }
    };

    // Listen for subscription update events
    window.addEventListener('subscription-updated', handleSubscriptionUpdate);

    return () => {
      window.removeEventListener('subscription-updated', handleSubscriptionUpdate);
    };
  }, [queryClient, fetchUser]);
}