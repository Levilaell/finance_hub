// frontend/components/UsageIndicators.tsx
'use client';

import { useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Brain, 
  CreditCard, 
  Users, 
  FileText,
  AlertTriangle,
  TrendingUp,
  Zap
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import type { Company } from '@/types';

interface UsageIndicatorProps {
  company: Company;
}

export function AIUsageIndicator({ company }: UsageIndicatorProps) {
  const router = useRouter();
  
  if (!company.subscription_plan) {
    return null;
  }
  
  if (company.subscription_plan.plan_type === 'starter') {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-4">
            <Brain className="h-8 w-8 mx-auto text-gray-400 mb-2" />
            <p className="text-sm text-gray-600">
              Insights com IA disponíveis no plano Professional
            </p>
            <Button 
              size="sm" 
              variant="outline" 
              className="mt-2"
              onClick={() => router.push('/pricing')}
            >
              Fazer Upgrade
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  if (company.subscription_plan.plan_type === 'professional') {
    const usage = company.current_month_ai_requests || 0;
    const limit = company.subscription_plan.max_ai_requests_per_month || 1000;
    const percentage = (usage / limit) * 100;
    const remaining = limit - usage;
    
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Brain className="h-4 w-4" />
            Uso de IA
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Requisições este mês</span>
              <span className="font-medium">{usage} / {limit}</span>
            </div>
            <Progress value={percentage} className="h-2" />
            
            {percentage >= 90 && (
              <div className="flex items-center gap-2 text-xs text-red-600">
                <AlertTriangle className="h-3 w-3" />
                <span>Apenas {remaining} requisições restantes!</span>
              </div>
            )}
            {percentage >= 80 && percentage < 90 && (
              <p className="text-xs text-orange-600">
                Considere upgrade para Enterprise para IA ilimitada
              </p>
            )}
            {percentage < 80 && (
              <p className="text-xs text-muted-foreground">
                {remaining} requisições restantes este mês
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }
  
  // Enterprise
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Brain className="h-4 w-4" />
          Uso de IA
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-green-600" />
            <span className="text-sm font-medium">IA Ilimitada</span>
          </div>
          <Badge variant="secondary" className="bg-green-100 text-green-700">
            Enterprise
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

export function TransactionUsageIndicator({ company }: UsageIndicatorProps) {
  const router = useRouter();
  
  if (!company.subscription_plan) {
    return null;
  }
  
  const usage = company.current_month_transactions || 0;
  const limit = company.subscription_plan.max_transactions || 0;
  const percentage = limit > 0 ? (usage / limit) * 100 : 0;
  const remaining = limit - usage;
  
  // Enterprise tem transações ilimitadas
  if (company.subscription_plan.plan_type === 'enterprise') {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Transações
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <span className="text-sm">Este mês: {usage}</span>
            <Badge variant="secondary" className="bg-green-100 text-green-700">
              Ilimitado
            </Badge>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <FileText className="h-4 w-4" />
          Transações
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Este mês</span>
            <span className="font-medium">{usage} / {limit}</span>
          </div>
          <Progress value={percentage} className="h-2" />
          
          {percentage >= 100 && (
            <div className="flex items-center gap-2 text-xs text-red-600">
              <AlertTriangle className="h-3 w-3" />
              <span>Limite atingido! Faça upgrade para continuar.</span>
            </div>
          )}
          {percentage >= 90 && percentage < 100 && (
            <div className="flex items-center gap-2 text-xs text-orange-600">
              <AlertTriangle className="h-3 w-3" />
              <span>Apenas {remaining} transações restantes!</span>
            </div>
          )}
          {percentage >= 80 && percentage < 90 && (
            <p className="text-xs text-orange-600">
              Você está próximo do limite mensal
            </p>
          )}
          {percentage < 80 && (
            <p className="text-xs text-muted-foreground">
              {remaining} transações restantes
            </p>
          )}
          
          {percentage >= 80 && (
            <Button 
              size="sm" 
              variant="outline" 
              className="w-full mt-2"
              onClick={() => router.push('/pricing')}
            >
              <TrendingUp className="h-3 w-3 mr-1" />
              Fazer Upgrade
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function BankAccountUsageIndicator({ company }: UsageIndicatorProps) {
  const router = useRouter();
  
  if (!company.subscription_plan) {
    return null;
  }
  
  const usage = company.active_bank_accounts_count || 0;
  const limit = company.subscription_plan.max_bank_accounts || 0;
  const percentage = limit > 0 ? (usage / limit) * 100 : 0;
  const remaining = limit - usage;
  
  // Enterprise tem contas ilimitadas
  if (company.subscription_plan.plan_type === 'enterprise') {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <CreditCard className="h-4 w-4" />
            Contas Bancárias
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <span className="text-sm">Ativas: {usage}</span>
            <Badge variant="secondary" className="bg-green-100 text-green-700">
              Ilimitado
            </Badge>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <CreditCard className="h-4 w-4" />
          Contas Bancárias
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Contas ativas</span>
            <span className="font-medium">{usage} / {limit}</span>
          </div>
          <Progress value={percentage} className="h-2" />
          
          {percentage >= 100 && (
            <div className="flex items-center gap-2 text-xs text-red-600">
              <AlertTriangle className="h-3 w-3" />
              <span>Limite atingido!</span>
            </div>
          )}
          {percentage < 100 && remaining > 0 && (
            <p className="text-xs text-muted-foreground">
              Você pode adicionar mais {remaining} {remaining === 1 ? 'conta' : 'contas'}
            </p>
          )}
          
          {percentage >= 100 && (
            <Button 
              size="sm" 
              variant="outline" 
              className="w-full mt-2"
              onClick={() => router.push('/pricing')}
            >
              <TrendingUp className="h-3 w-3 mr-1" />
              Aumentar Limite
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// UserUsageIndicator removed - not implemented feature

// Componente combinado para mostrar todos os indicadores
export function UsageIndicators({ company: initialCompany }: UsageIndicatorProps) {
  const { user, fetchUser } = useAuthStore();
  
  // Use the most up-to-date company data
  const company = user?.company || initialCompany;
  
  useEffect(() => {
    // Listen for subscription updates
    const handleSubscriptionUpdate = async () => {
      try {
        await fetchUser();
      } catch (error) {
        console.error('Error fetching updated user data:', error);
      }
    };
    
    window.addEventListener('subscription-updated', handleSubscriptionUpdate);
    
    return () => {
      window.removeEventListener('subscription-updated', handleSubscriptionUpdate);
    };
  }, [fetchUser]);
  
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <TransactionUsageIndicator company={company} />
      <BankAccountUsageIndicator company={company} />
      <AIUsageIndicator company={company} />
    </div>
  );
}