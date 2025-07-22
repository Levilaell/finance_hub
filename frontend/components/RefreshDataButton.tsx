'use client';

import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';
import { useAuthStore } from '@/store/auth-store';
import { useState } from 'react';
import { toast } from 'sonner';
import { useQueryClient } from '@tanstack/react-query';

export function RefreshDataButton() {
  const { fetchUser } = useAuthStore();
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      // Clear all local storage except auth tokens
      const authStorage = localStorage.getItem('auth-storage');
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      
      localStorage.clear();
      sessionStorage.clear();
      
      // Restore auth tokens
      if (authStorage) localStorage.setItem('auth-storage', authStorage);
      if (accessToken) localStorage.setItem('access_token', accessToken);
      if (refreshToken) localStorage.setItem('refresh_token', refreshToken);
      
      // Clear React Query cache
      await queryClient.invalidateQueries();
      
      // Force fetch fresh user data
      await fetchUser();
      
      // Dispatch custom event to notify all components
      window.dispatchEvent(new CustomEvent('subscription-updated'));
      
      toast.success('Dados atualizados com sucesso!');
      
      // Force reload after a short delay
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (error) {
      toast.error('Erro ao atualizar dados');
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleRefresh}
      disabled={isRefreshing}
      className="gap-2"
    >
      <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
      Atualizar Dados
    </Button>
  );
}