'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  ExclamationTriangleIcon, 
  CreditCardIcon,
  ClockIcon,
  CheckCircleIcon 
} from '@heroicons/react/24/outline';
import { useAuthStore } from '@/store/auth-store';
import { useSubscriptionCheck } from '@/hooks/use-subscription-check';

export default function SubscriptionBlockedPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { subscriptionStatus, isLoading } = useSubscriptionCheck();

  // Redirect if subscription is actually active
  useEffect(() => {
    if (!isLoading && subscriptionStatus) {
      if (subscriptionStatus.subscription_status === 'active' || 
          (subscriptionStatus.subscription_status === 'trial' && subscriptionStatus.trial_days_left > 0)) {
        router.push('/dashboard');
      }
    }
  }, [subscriptionStatus, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const isTrialExpired = subscriptionStatus?.subscription_status === 'expired' || 
                        (subscriptionStatus?.subscription_status === 'trial' && 
                         subscriptionStatus?.trial_days_left <= 0);

  const isCancelled = subscriptionStatus?.subscription_status === 'cancelled';
  const isPastDue = subscriptionStatus?.subscription_status === 'past_due';

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <Card className="max-w-2xl w-full">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-red-100 rounded-full">
              <ExclamationTriangleIcon className="h-12 w-12 text-red-600" />
            </div>
          </div>
          <CardTitle className="text-2xl text-red-800">
            {isTrialExpired && 'Período de Teste Expirado'}
            {isCancelled && 'Assinatura Cancelada'}
            {isPastDue && 'Pagamento em Atraso'}
            {!isTrialExpired && !isCancelled && !isPastDue && 'Acesso Bloqueado'}
          </CardTitle>
          <CardDescription className="mt-2 text-gray-600">
            {isTrialExpired && 'Seu período de teste gratuito expirou. Escolha um plano para continuar.'}
            {isCancelled && 'Sua assinatura foi cancelada. Reative para continuar usando o sistema.'}
            {isPastDue && 'Há um problema com seu pagamento. Atualize seu método de pagamento.'}
            {!isTrialExpired && !isCancelled && !isPastDue && 'Sua assinatura não está ativa.'}
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Status atual */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium mb-3 flex items-center">
              <ClockIcon className="h-5 w-5 mr-2" />
              Status Atual
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Plano:</span>
                <span className="font-medium">
                  {user?.company?.subscription_plan?.name || 'Período de Teste'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Status:</span>
                <span className={`font-medium ${
                  isTrialExpired ? 'text-red-600' : 
                  isCancelled ? 'text-orange-600' : 
                  isPastDue ? 'text-yellow-600' : 'text-gray-600'
                }`}>
                  {isTrialExpired && 'Trial Expirado'}
                  {isCancelled && 'Cancelada'}
                  {isPastDue && 'Pagamento Pendente'}
                  {!isTrialExpired && !isCancelled && !isPastDue && 'Inativa'}
                </span>
              </div>
              {subscriptionStatus?.trial_ends_at && (
                <div className="flex justify-between">
                  <span>Data de Expiração:</span>
                  <span className="font-medium">
                    {new Date(subscriptionStatus.trial_ends_at).toLocaleDateString('pt-BR')}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* O que você perdeu */}
          <div className="bg-red-50 p-4 rounded-lg border border-red-200">
            <h3 className="font-medium text-red-800 mb-3">Recursos Bloqueados:</h3>
            <ul className="text-sm text-red-700 space-y-1">
              <li>• Acesso ao dashboard e relatórios</li>
              <li>• Sincronização de transações bancárias</li>
              <li>• Categorização automática com IA</li>
              <li>• Relatórios avançados e insights</li>
              <li>• Gestão de contas e categorias</li>
            </ul>
          </div>

          {/* Benefícios de reativar */}
          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <h3 className="font-medium text-green-800 mb-3 flex items-center">
              <CheckCircleIcon className="h-5 w-5 mr-2" />
              Ao Reativar Você Terá:
            </h3>
            <ul className="text-sm text-green-700 space-y-1">
              <li>• Acesso imediato a todos os recursos</li>
              <li>• Seus dados salvos e íntegros</li>
              <li>• Sincronização automática restaurada</li>
              <li>• Suporte técnico prioritário</li>
            </ul>
          </div>

          {/* Botões de ação */}
          <div className="flex flex-col sm:flex-row gap-3">
            <Button 
              className="flex-1"
              onClick={() => router.push('/dashboard/subscription/upgrade')}
            >
              <CreditCardIcon className="h-4 w-4 mr-2" />
              {isTrialExpired ? 'Escolher Plano' : 'Reativar Assinatura'}
            </Button>
            
            {isPastDue && (
              <Button 
                variant="outline"
                className="flex-1"
                onClick={() => router.push('/settings?tab=billing')}
              >
                Atualizar Pagamento
              </Button>
            )}
            
            <Button 
              variant="outline"
              onClick={() => router.push('/dashboard/subscription/plans')}
            >
              Ver Planos
            </Button>
          </div>

          {/* Garantia */}
          <div className="text-center text-sm text-gray-500 border-t pt-4">
            <p>💡 <strong>Garantia:</strong> Seus dados estão seguros e serão restaurados imediatamente após a reativação.</p>
            <p className="mt-1">Tem dúvidas? <a href="mailto:suporte@financehub.com" className="text-blue-600 hover:underline">Entre em contato</a></p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}