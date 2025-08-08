import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth-store';

export function useSubscriptionUpdates() {
  const queryClient = useQueryClient();
  const { fetchUser } = useAuthStore();

  useEffect(() => {
    // Only set up listeners on client side
    if (typeof window === 'undefined') return;
    
    const handleSubscriptionUpdate = async () => {
      try {
        // Invalidate specific queries instead of all
        queryClient.invalidateQueries({ queryKey: ['subscription-status'] });
        queryClient.invalidateQueries({ queryKey: ['dashboard'] });
        queryClient.invalidateQueries({ queryKey: ['company'] });
        
        // Fetch fresh user data (but don't await to avoid blocking)
        fetchUser().catch(console.error);
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