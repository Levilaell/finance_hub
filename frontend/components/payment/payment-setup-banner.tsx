import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ExclamationTriangleIcon, CreditCardIcon } from '@heroicons/react/24/outline';
import { useAuthStore } from '@/store/auth-store';
import { subscriptionService, SubscriptionStatus } from '@/services/unified-subscription.service';
import { 
  ResponsiveBannerContainer, 
  ResponsiveBannerContent, 
  ResponsiveButtonGroup,
  ResponsiveDismissButton 
} from '@/components/ui/responsive-banner';

export function PaymentSetupBanner() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [isDismissed, setIsDismissed] = useState(false);
  const [localDismissed, setLocalDismissed] = useState(false);

  // Check subscription status using the service
  const { data: status } = useQuery<SubscriptionStatus>({
    queryKey: ['subscription-status-banner'],
    queryFn: () => subscriptionService.getSubscriptionStatus(),
    enabled: !!user,
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    retry: 1,
  });

  useEffect(() => {
    // Check if banner was dismissed
    const dismissed = localStorage.getItem('payment_banner_dismissed');
    const dismissedDate = localStorage.getItem('payment_banner_dismissed_date');
    
    if (dismissed && dismissedDate) {
      // Reset dismissal after 24 hours
      const dismissedTime = new Date(dismissedDate).getTime();
      const now = new Date().getTime();
      const hoursSinceDismissed = (now - dismissedTime) / (1000 * 60 * 60);
      
      if (hoursSinceDismissed < 24) {
        setLocalDismissed(true);
      } else {
        localStorage.removeItem('payment_banner_dismissed');
        localStorage.removeItem('payment_banner_dismissed_date');
      }
    }
  }, []);

  const handleSetupPayment = () => {
    const selectedPlan = localStorage.getItem('selected_plan') || 'starter';
    router.push(`/dashboard/subscription/upgrade?plan=${selectedPlan}`);
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    setLocalDismissed(true);
    localStorage.setItem('payment_banner_dismissed', 'true');
    localStorage.setItem('payment_banner_dismissed_date', new Date().toISOString());
  };

  // Don't show if dismissed or no data
  if (localDismissed || isDismissed || !status) return null;

  // Don't show if payment is already setup or not in trial
  if (status.has_payment_method || status.subscription_status !== 'trial') return null;

  // Determine urgency level
  const isUrgent = status.trial_days_left <= 3;
  const isWarning = status.trial_days_left <= 7;

  const getBannerVariant = (): 'warning' | 'critical' => {
    return isUrgent ? 'critical' : 'warning';
  };

  const getTitle = (): string => {
    if (isUrgent) {
      return `Período de teste expira em ${status.trial_days_left} dia${status.trial_days_left > 1 ? 's' : ''}!`;
    }
    return 'Configure seu método de pagamento';
  };

  const getDescription = (): string => {
    if (isUrgent) {
      return 'Configure o pagamento agora para não perder acesso ao sistema.';
    }
    return `Teste do plano ${status.plan?.name || 'Starter'} expira em ${status.trial_days_left} dias. Configure o pagamento para continuar.`;
  };

  const getIconColor = (): string => {
    return isUrgent ? 'text-red-600' : 'text-orange-600';
  };

  return (
    <ResponsiveBannerContainer variant={getBannerVariant()}>
      <ResponsiveBannerContent
        icon={
          isUrgent ? (
            <ExclamationTriangleIcon className={`h-4 w-4 sm:h-5 sm:w-5 ${getIconColor()}`} />
          ) : (
            <CreditCardIcon className={`h-4 w-4 sm:h-5 sm:w-5 ${getIconColor()}`} />
          )
        }
        title={getTitle()}
        description={getDescription()}
        dismissButton={<ResponsiveDismissButton onClick={handleDismiss} />}
        actions={
          <ResponsiveButtonGroup
            primary={{
              label: "Configurar",
              onClick: handleSetupPayment,
              variant: isUrgent ? 'destructive' : 'default'
            }}
            secondary={!isUrgent ? {
              label: "Depois",
              onClick: handleDismiss
            } : undefined}
          />
        }
      />
    </ResponsiveBannerContainer>
  );
}