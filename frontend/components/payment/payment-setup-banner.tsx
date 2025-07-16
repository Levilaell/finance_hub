import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ExclamationTriangleIcon, XMarkIcon, CreditCardIcon } from '@heroicons/react/24/outline';
import { useAuthStore } from '@/store/auth-store';
import { subscriptionService, SubscriptionStatus } from '@/services/subscription.service';

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

  const bannerColor = isUrgent ? 'border-red-200 bg-red-50' : isWarning ? 'border-orange-200 bg-orange-50' : 'border-yellow-200 bg-yellow-50';
  const iconColor = isUrgent ? 'text-red-600' : isWarning ? 'text-orange-600' : 'text-yellow-600';
  const textColor = isUrgent ? 'text-red-900' : isWarning ? 'text-orange-900' : 'text-yellow-900';
  const subtextColor = isUrgent ? 'text-red-700' : isWarning ? 'text-orange-700' : 'text-yellow-700';

  return (
    <Card className={`mb-6 ${bannerColor} relative`}>
      <button
        onClick={handleDismiss}
        className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
        aria-label="Fechar banner"
      >
        <XMarkIcon className="h-5 w-5" />
      </button>
      
      <CardContent className="flex items-center justify-between p-4">
        <div className="flex items-center space-x-3 flex-1">
          {isUrgent ? (
            <ExclamationTriangleIcon className={`h-6 w-6 ${iconColor}`} />
          ) : (
            <CreditCardIcon className={`h-6 w-6 ${iconColor}`} />
          )}
          <div>
            <p className={`font-medium ${textColor}`}>
              {isUrgent 
                ? `Atenção: Seu período de teste expira em ${status.trial_days_left} dia${status.trial_days_left > 1 ? 's' : ''}!`
                : isWarning
                ? `Seu período de teste expira em ${status.trial_days_left} dias`
                : 'Configure seu método de pagamento'}
            </p>
            <p className={`text-sm ${subtextColor}`}>
              {isUrgent
                ? 'Configure o pagamento agora para não perder acesso ao sistema.'
                : `Você está testando o plano ${status.plan?.name || 'Starter'}. Configure o pagamento para continuar após o trial.`}
            </p>
          </div>
        </div>
        <div className="flex space-x-2 ml-4">
          <Button 
            size="sm" 
            onClick={handleSetupPayment}
            variant={isUrgent ? 'destructive' : 'default'}
          >
            Configurar Agora
          </Button>
          {!isUrgent && (
            <Button 
              size="sm" 
              variant="ghost" 
              onClick={handleDismiss}
            >
              Depois
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}