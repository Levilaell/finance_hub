'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { subscriptionService } from '@/services/subscription.service';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { startStripeCheckout } from '@/utils/checkout';

interface SubscriptionGuardProps {
  children: React.ReactNode;
}

export function SubscriptionGuard({ children }: SubscriptionGuardProps) {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [checking, setChecking] = useState(true);
  const [hasAccess, setHasAccess] = useState(false);

  useEffect(() => {
    checkSubscription();
  }, []);

  const checkSubscription = async () => {
    try {
      if (!isAuthenticated) {
        router.push('/login');
        return;
      }

      const status = await subscriptionService.getStatus();

      // Permite acesso se status for trialing ou active
      if (status.status === 'trialing' || status.status === 'active') {
        setHasAccess(true);
      } else if (status.requires_action) {
        // Payment requires action (3D Secure, etc)
        router.push('/subscription/requires-action');
      } else if (status.status === 'none') {
        // Verifica se já usou o trial
        if (status.has_used_trial) {
          // Trial já foi usado - não pode usar novamente
          router.push('/subscription/trial-used');
        } else {
          // Sem subscription e trial disponível - inicia checkout direto
          await startStripeCheckout();
        }
      } else {
        // Subscription expirada/cancelada - redireciona para página de reativação
        router.push('/subscription/expired');
      }
    } catch (error) {
      console.error('Error checking subscription:', error);
      // Em caso de erro, inicia checkout direto
      await startStripeCheckout();
    } finally {
      setChecking(false);
    }
  };

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (!hasAccess) {
    return null;
  }

  return <>{children}</>;
}
