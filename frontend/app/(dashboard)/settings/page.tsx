'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { authService } from '@/services/auth.service';
import { useAuthStore } from '@/store/auth-store';
import { User } from '@/types';
import { 
  UserIcon,
  ShieldCheckIcon,
  CreditCardIcon,
  BellIcon,
  EyeIcon,
  EyeSlashIcon,
  KeyIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { analyticsService, SummaryMetrics } from '@/services/analytics.service';
import { 
  calculateTrialInfo, 
  calculateBillingInfo, 
  getSubscriptionStatusInfo, 
  formatCurrency,
  formatDate,
  shouldShowUpgradePrompt 
} from '@/utils/billing.utils';
import { UpgradePlanDialog } from '@/components/billing/upgrade-plan-dialog';
import { UsageLimitsCard } from '@/components/billing/usage-limits';
import { useSubscriptionCheck } from '@/hooks/use-subscription-check';
import { subscriptionService } from '@/services/unified-subscription.service';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  CheckCircleIcon,
  ClockIcon,
  ExclamationCircleIcon,
  ChartBarIcon,
  BanknotesIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { useSubscriptionUpdates } from '@/hooks/useSubscriptionUpdates';

interface ProfileForm {
  first_name: string;
  last_name: string;
}

interface PasswordForm {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

interface DeleteAccountForm {
  password: string;
  confirmation: string;
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { user, updateUser, fetchUser } = useAuthStore();
  
  // Listen for subscription updates
  useSubscriptionUpdates();
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [deleteAccountDialogOpen, setDeleteAccountDialogOpen] = useState(false);
  

  // Billing dialogs state
  const [upgradePlanDialogOpen, setUpgradePlanDialogOpen] = useState(false);
  const [billingHistoryDialogOpen, setBillingHistoryDialogOpen] = useState(false);
  const [paymentMethodsDialogOpen, setPaymentMethodsDialogOpen] = useState(false);
  const [cancelSubscriptionDialogOpen, setCancelSubscriptionDialogOpen] = useState(false);

  const profileForm = useForm<ProfileForm>({
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
    },
  });

  const passwordForm = useForm<PasswordForm>();
  const deleteAccountForm = useForm<DeleteAccountForm>();

  // Subscription check hook
  const { subscriptionStatus, isLoading: isLoadingSubscription } = useSubscriptionCheck();

  // Usage limits query
  const { data: usageLimits, isLoading: isLoadingLimits, refetch: refetchLimits } = useQuery({
    queryKey: ['usage-limits'],
    queryFn: () => subscriptionService.getUsageLimits(),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  });
  
  // Listen for subscription update events
  useEffect(() => {
    const handleSubscriptionUpdate = async () => {
      await fetchUser();
      await refetchLimits();
      queryClient.invalidateQueries({ queryKey: ['subscription-status'] });
      queryClient.invalidateQueries({ queryKey: ['performance-metrics'] });
    };
    
    window.addEventListener('subscription-updated', handleSubscriptionUpdate);
    return () => window.removeEventListener('subscription-updated', handleSubscriptionUpdate);
  }, [fetchUser, refetchLimits, queryClient]);

  // Performance metrics query
  const { data: performanceMetrics, isLoading: isLoadingMetrics } = useQuery({
    queryKey: ['performance-metrics'],
    queryFn: () => analyticsService.getSummaryMetrics(30),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });

  const updateProfileMutation = useMutation({
    mutationFn: (data: Partial<User>) => authService.updateProfile(data),
    onSuccess: (updatedUser) => {
      updateUser(updatedUser);
      toast.success('Perfil atualizado com sucesso');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Falha ao atualizar perfil');
    },
  });

  const changePasswordMutation = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      authService.changePassword(data),
    onSuccess: () => {
      passwordForm.reset();
      toast.success('Senha alterada com sucesso');
    },
    onError: (error: any) => {
      // Trata erros específicos do backend
      let errorMessage = 'Falha ao alterar senha';
      
      if (error.response?.data) {
        const data = error.response.data;
        // Verifica diferentes formatos de erro
        if (typeof data === 'string') {
          errorMessage = data;
        } else if (data.old_password?.[0]) {
          errorMessage = data.old_password[0];
        } else if (data.new_password?.[0]) {
          errorMessage = data.new_password[0];
        } else if (data.detail) {
          errorMessage = typeof data.detail === 'string' ? data.detail : data.detail.message || 'Falha ao alterar senha';
        } else if (data.error) {
          errorMessage = typeof data.error === 'string' ? data.error : 'Falha ao alterar senha';
        } else if (data.message) {
          errorMessage = data.message;
        }
      }
      
      toast.error(errorMessage);
    },
  });





  const deleteAccountMutation = useMutation({
    mutationFn: authService.deleteAccount,
    onSuccess: () => {
      toast.success('Conta deletada com sucesso');
      // Redirect to login or home page
      window.location.href = '/login';
    },
    onError: (error: any) => {
      // Trata erros específicos do backend
      let errorMessage = 'Falha ao deletar conta';
      
      if (error.response?.data) {
        const data = error.response.data;
        // Verifica diferentes formatos de erro
        if (typeof data === 'string') {
          errorMessage = data;
        } else if (data.password?.[0]) {
          errorMessage = data.password[0];
        } else if (data.confirmation?.[0]) {
          errorMessage = data.confirmation[0];
        } else if (data.detail) {
          errorMessage = typeof data.detail === 'string' ? data.detail : data.detail.message || 'Falha ao deletar conta';
        } else if (data.error) {
          errorMessage = typeof data.error === 'string' ? data.error : 'Falha ao deletar conta';
        } else if (data.message) {
          errorMessage = data.message;
        }
      }
      
      toast.error(errorMessage);
    },
  });

  const cancelSubscriptionMutation = useMutation({
    mutationFn: () => subscriptionService.cancelSubscription(),
    onSuccess: () => {
      toast.success('Assinatura cancelada com sucesso');
      setCancelSubscriptionDialogOpen(false);
      // Refresh user data and invalidate queries
      fetchUser();
      queryClient.invalidateQueries({ queryKey: ['subscription-status'] });
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Falha ao cancelar assinatura');
    },
  });

  const onProfileSubmit = (data: ProfileForm) => {
    updateProfileMutation.mutate(data);
  };

  const onPasswordSubmit = (data: PasswordForm) => {
    if (data.new_password !== data.confirm_password) {
      toast.error('As senhas não coincidem');
      return;
    }
    changePasswordMutation.mutate({
      current_password: data.current_password,
      new_password: data.new_password,
    });
  };


  const onDeleteAccountSubmit = (data: DeleteAccountForm) => {
    if (data.confirmation.toLowerCase() !== 'deletar') {
      toast.error('Por favor, digite "deletar" para confirmar');
      return;
    }
    deleteAccountMutation.mutate(data);
  };

  // Calculate billing information
  const trialInfo = calculateTrialInfo(user?.company?.trial_ends_at || null);
  const billingInfo = calculateBillingInfo(
    user?.company?.next_billing_date || null,
    user?.company?.subscription_start_date || null,
    user?.company?.subscription_end_date || null
  );
  const subscriptionStatusInfo = getSubscriptionStatusInfo(user?.company?.subscription_status || 'trialing');
  
  // Don't show trial info if user has active paid subscription or cancelled/expired
  const isActiveSubscription = user?.company?.subscription_status === 'active' && 
                              user?.company?.subscription_plan?.price_monthly && 
                              Number(user?.company?.subscription_plan?.price_monthly) > 0;
  
  const isCancelledOrExpired = ['cancelled', 'canceled', 'cancelling', 'expired', 'suspended'].includes(
    user?.company?.subscription_status || ''
  );
  
  const showTrialInfo = !isActiveSubscription && !isCancelledOrExpired && trialInfo.isActive;
  const showUpgradePrompt = !isActiveSubscription && !isCancelledOrExpired && shouldShowUpgradePrompt(user?.company?.subscription_status || 'trialing', trialInfo);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Configurações</h1>
        <p className="text-gray-600">Gerencie suas configurações de conta e preferências</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList className="grid w-full grid-cols-2 sm:grid-cols-4 gap-1">
          <TabsTrigger value="profile" className="text-xs sm:text-sm">Perfil</TabsTrigger>
          <TabsTrigger value="security" className="text-xs sm:text-sm">Segurança</TabsTrigger>
          <TabsTrigger value="status" className="text-xs sm:text-sm">Status & Limites</TabsTrigger>
          <TabsTrigger value="billing" className="text-xs sm:text-sm">Assinatura</TabsTrigger>
        </TabsList>

        {/* Profile Settings */}
        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <UserIcon className="h-5 w-5 mr-2" />
                Informações do Perfil
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="first_name">Nome</Label>
                    <Input
                      id="first_name"
                      {...profileForm.register('first_name', { required: true })}
                    />
                  </div>
                  <div>
                    <Label htmlFor="last_name">Sobrenome</Label>
                    <Input
                      id="last_name"
                      {...profileForm.register('last_name', { required: true })}
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="bg-white/5 cursor-not-allowed"
                  />
                  <p className="text-xs text-gray-500 mt-1">O email não pode ser alterado</p>
                </div>
                <div className="pt-4">
                  <Button
                    type="submit"
                    disabled={updateProfileMutation.isPending}
                  >
                    {updateProfileMutation.isPending ? (
                      <LoadingSpinner />
                    ) : (
                      'Atualizar Perfil'
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Settings */}
        <TabsContent value="security" className="space-y-4">
          {/* Change Password */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <KeyIcon className="h-5 w-5 mr-2" />
                Alterar Senha
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-4">
                <div>
                  <Label htmlFor="current_password">Senha Atual</Label>
                  <div className="relative">
                    <Input
                      id="current_password"
                      type={showCurrentPassword ? 'text' : 'password'}
                      {...passwordForm.register('current_password', { 
                        required: 'Senha atual é obrigatória'
                      })}
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500"
                    >
                      {showCurrentPassword ? (
                        <EyeSlashIcon className="h-5 w-5" />
                      ) : (
                        <EyeIcon className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                  {passwordForm.formState.errors.current_password && (
                    <p className="text-sm text-red-500 mt-1">
                      {typeof passwordForm.formState.errors.current_password.message === 'string' 
                        ? passwordForm.formState.errors.current_password.message 
                        : 'Campo obrigatório'}
                    </p>
                  )}
                </div>
                <div>
                  <Label htmlFor="new_password">Nova Senha</Label>
                  <div className="relative">
                    <Input
                      id="new_password"
                      type={showNewPassword ? 'text' : 'password'}
                      {...passwordForm.register('new_password', {
                        required: 'Nova senha é obrigatória',
                        minLength: {
                          value: 8,
                          message: 'A senha deve ter pelo menos 8 caracteres'
                        }
                      })}
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500"
                    >
                      {showNewPassword ? (
                        <EyeSlashIcon className="h-5 w-5" />
                      ) : (
                        <EyeIcon className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                  {passwordForm.formState.errors.new_password && (
                    <p className="text-sm text-red-500 mt-1">
                      {typeof passwordForm.formState.errors.new_password.message === 'string' 
                        ? passwordForm.formState.errors.new_password.message 
                        : 'Campo obrigatório'}
                    </p>
                  )}
                </div>
                <div>
                  <Label htmlFor="confirm_password">Confirmar Nova Senha</Label>
                  <div className="relative">
                    <Input
                      id="confirm_password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      {...passwordForm.register('confirm_password', { 
                        required: 'Confirmação de senha é obrigatória'
                      })}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500"
                    >
                      {showConfirmPassword ? (
                        <EyeSlashIcon className="h-5 w-5" />
                      ) : (
                        <EyeIcon className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                  {passwordForm.formState.errors.confirm_password && (
                    <p className="text-sm text-red-500 mt-1">
                      {typeof passwordForm.formState.errors.confirm_password.message === 'string' 
                        ? passwordForm.formState.errors.confirm_password.message 
                        : 'Campo obrigatório'}
                    </p>
                  )}
                </div>
                <div className="pt-4">
                  <Button
                    type="submit"
                    disabled={changePasswordMutation.isPending}
                  >
                    {changePasswordMutation.isPending ? (
                      <LoadingSpinner />
                    ) : (
                      'Alterar Senha'
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Two-Factor Authentication */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <ShieldCheckIcon className="h-5 w-5 mr-2" />
                Autenticação de Dois Fatores
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-sm text-gray-600">
                  Adicione uma camada extra de segurança à sua conta habilitando a autenticação de dois fatores.
                </p>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">
                      Autenticação de Dois Fatores
                    </p>
                    <p className="text-sm text-gray-600">
                      Em breve - Estamos trabalhando para implementar esta funcionalidade
                    </p>
                  </div>
                  <Button
                    disabled
                    variant="outline"
                  >
                    Em Breve
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Danger Zone */}
          <Card className="border-red-200">
            <CardHeader>
              <CardTitle className="flex items-center text-red-600">
                <TrashIcon className="h-5 w-5 mr-2" />
                Zona de Perigo
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="font-medium text-red-600">Excluir Conta</p>
                  <p className="text-sm text-gray-600">
                    Excluir permanentemente sua conta e todos os dados associados. Esta ação não pode ser desfeita.
                  </p>
                </div>
                <Button 
                  variant="destructive"
                  onClick={() => setDeleteAccountDialogOpen(true)}
                >
                  Excluir Conta
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Status & Limits Tab */}
        <TabsContent value="status" className="space-y-6">
          {/* Subscription Status Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <ChartBarIcon className="h-5 w-5 mr-2" />
                Status da Assinatura
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoadingSubscription ? (
                <div className="space-y-4">
                  <div className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                    <div className="h-8 bg-gray-200 rounded"></div>
                  </div>
                </div>
              ) : subscriptionStatus ? (
                <div className="space-y-4">
                  {/* Status Row */}
                  <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                    <div>
                      <p className="text-sm text-gray-600">Status Atual</p>
                      <div className="flex items-center mt-1">
                        {subscriptionStatus.subscription_status === 'active' && (
                          <>
                            <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                            <span className="text-lg font-semibold text-green-700">Ativo</span>
                          </>
                        )}
                        {subscriptionStatus.subscription_status === 'trial' && (
                          <>
                            <ClockIcon className="h-5 w-5 text-blue-500 mr-2" />
                            <span className="text-lg font-semibold text-blue-700">Período de Teste</span>
                          </>
                        )}
                        {subscriptionStatus.subscription_status === 'expired' && (
                          <>
                            <ExclamationCircleIcon className="h-5 w-5 text-red-500 mr-2" />
                            <span className="text-lg font-semibold text-red-700">Expirado</span>
                          </>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      {subscriptionStatus.plan && (
                        <div>
                          <p className="text-sm text-gray-600">Plano</p>
                          <p className="text-lg font-semibold">{subscriptionStatus.plan.name}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Trial Info - only show if trial and not cancelled */}
                  {subscriptionStatus.subscription_status === 'trial' && 
                   !isCancelledOrExpired && (
                    <div className="p-4 bg-blue-500/10 rounded-lg">
                      <p className="text-sm text-blue-800">
                        {subscriptionStatus.trial_days_left > 0 ? (
                          <>Período de teste expira em <strong>{subscriptionStatus.trial_days_left} dias</strong></>
                        ) : (
                          <>Período de teste <strong>expirado</strong></>
                        )}
                      </p>
                      {subscriptionStatus.trial_ends_at && (
                        <p className="text-xs text-blue-600 mt-1">
                          Data de expiração: {new Date(subscriptionStatus.trial_ends_at).toLocaleDateString('pt-BR')}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Cancelled subscription info */}
                  {isCancelledOrExpired && (
                    <div className="p-4 bg-orange-500/10 rounded-lg border border-orange-500/20">
                      <p className="text-sm text-orange-800">
                        <strong>
                          {user?.company?.subscription_status === 'cancelling' 
                            ? 'Cancelamento em processo' 
                            : 'Assinatura cancelada'
                          }
                        </strong>
                      </p>
                      <p className="text-xs text-orange-600 mt-1">
                        {user?.company?.subscription_status === 'cancelling' 
                          ? 'Suas cobranças futuras foram interrompidas'
                          : 'Você pode reativar sua assinatura a qualquer momento'
                        }
                      </p>
                    </div>
                  )}

                  {/* Payment Method Status */}
                  <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                    <div>
                      <p className="text-sm text-gray-600">Método de Pagamento</p>
                      <p className="mt-1">
                        {subscriptionStatus.has_payment_method ? (
                          <span className="text-green-600 font-medium">Configurado</span>
                        ) : (
                          <span className="text-orange-600 font-medium">Não configurado</span>
                        )}
                      </p>
                    </div>
                    {/* Next billing date not available in current API */}
                  </div>

                  {/* Action Buttons */}
                  {subscriptionStatus.requires_payment_setup && (
                    <div className="pt-4 space-y-2">
                      <Button 
                        onClick={() => setUpgradePlanDialogOpen(true)}
                        className="w-full"
                      >
                        Escolher Plano e Configurar Pagamento
                      </Button>
                      <Button 
                        onClick={() => setPaymentMethodsDialogOpen(true)}
                        className="w-full"
                        variant="outline"
                      >
                        Apenas Adicionar Método de Pagamento
                      </Button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center text-gray-500">
                  Não foi possível carregar o status da assinatura
                </div>
              )}
            </CardContent>
          </Card>

          {/* Usage Limits Card */}
          <UsageLimitsCard />
        </TabsContent>

        {/* Billing Settings */}
        <TabsContent value="billing">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <CreditCardIcon className="h-5 w-5 mr-2" />
                Faturamento e Assinatura
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Current Plan Section */}
                <div>
                  <h3 className="font-medium mb-2">Plano Atual</h3>
                  <div className="border rounded-lg p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium">{user?.company?.subscription_plan?.name || 'Período de Teste'}</p>
                        <p className="text-sm text-gray-600">
                          {user?.company?.subscription_plan?.price_monthly 
                            ? `${formatCurrency(Number(user.company.subscription_plan.price_monthly))}/mês`
                            : 'Sem cobrança durante o período de teste'
                          }
                        </p>
                      </div>
                      <div className="text-right">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          isActiveSubscription ? 'bg-green-100 text-green-800' : subscriptionStatusInfo.color
                        }`}>
                          {isActiveSubscription ? 'Ativa' : subscriptionStatusInfo.label}
                        </span>
                        <p className="text-xs text-gray-500 mt-1">
                          {isActiveSubscription ? 'Assinatura paga ativa' : subscriptionStatusInfo.description}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Trial Information */}
                {showTrialInfo && (
                  <div className={`border p-4 rounded-lg ${
                    trialInfo.isExpiringSoon 
                      ? 'bg-orange-500/10 border-orange-500/20' 
                      : 'bg-blue-500/10 border-blue-500/20'
                  }`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className={`font-medium ${
                          trialInfo.isExpiringSoon ? 'text-orange-800' : 'text-blue-800'
                        }`}>
                          {trialInfo.isExpiringSoon ? 'Período de Teste Expirando' : 'Período de Teste Ativo'}
                        </p>
                        <p className={`text-sm ${
                          trialInfo.isExpiringSoon ? 'text-orange-700' : 'text-blue-700'
                        }`}>
                          Seu trial termina em {formatDate(trialInfo.endDate!)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className={`text-2xl font-bold ${
                          trialInfo.isExpiringSoon ? 'text-orange-800' : 'text-blue-800'
                        }`}>
                          {trialInfo.daysRemaining}
                        </p>
                        <p className={`text-sm ${
                          trialInfo.isExpiringSoon ? 'text-orange-600' : 'text-blue-600'
                        }`}>
                          {trialInfo.daysRemaining === 1 ? 'dia restante' : 'dias restantes'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Expired Trial Warning */}
                {trialInfo.isExpired && (
                  <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-red-800">Período de Teste Expirado</p>
                        <p className="text-sm text-red-700">
                          Seu trial expirou em {formatDate(trialInfo.endDate!)}. Faça upgrade para continuar.
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-red-800">0</p>
                        <p className="text-sm text-red-600">dias restantes</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Payment Method Status */}
                {isActiveSubscription && (
                  <div className="bg-green-500/10 border border-green-500/20 p-4 rounded-lg mb-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <CheckCircleIcon className="h-5 w-5 text-green-600 mr-2" />
                        <div>
                          <p className="font-medium text-green-800">Método de Pagamento Configurado</p>
                          <p className="text-sm text-green-700">Sua cobrança está configurada e ativa</p>
                        </div>
                      </div>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => setPaymentMethodsDialogOpen(true)}
                        className="text-green-700 border-green-300 hover:bg-green-100"
                      >
                        Gerenciar
                      </Button>
                    </div>
                  </div>
                )}

                {/* Billing Information - Hide for cancelled subscriptions */}
                {!isCancelledOrExpired && (
                  <div>
                    <h3 className="font-medium mb-3">Informações de Cobrança</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Next Billing Date */}
                      {billingInfo.nextBillingDate && (
                        <div className="bg-white/5 p-4 rounded-lg">
                          <p className="text-sm text-gray-600">Próxima Cobrança</p>
                          <p className="font-medium">
                            {formatDate(billingInfo.nextBillingDate)}
                          </p>
                          {billingInfo.daysUntilNextBilling && billingInfo.daysUntilNextBilling > 0 && (
                            <p className="text-xs text-gray-500 mt-1">
                              em {billingInfo.daysUntilNextBilling} {billingInfo.daysUntilNextBilling === 1 ? 'dia' : 'dias'}
                            </p>
                          )}
                        </div>
                      )}

                      {/* Subscription Start Date */}
                      {billingInfo.subscriptionStartDate && (
                        <div className="bg-white/5 p-4 rounded-lg">
                          <p className="text-sm text-gray-600">Assinatura Iniciada</p>
                          <p className="font-medium">
                            {formatDate(billingInfo.subscriptionStartDate)}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-2">

                  <Button 
                    variant="outline" 
                    className="w-full sm:w-auto"
                    onClick={() => setBillingHistoryDialogOpen(true)}
                  >
                    Torne-se Pro
                  </Button>

                  {/* Show cancel button only for active paid subscriptions */}
                  {isActiveSubscription && (
                    <Button 
                      variant="destructive" 
                      className="w-full sm:w-auto"
                      onClick={() => setCancelSubscriptionDialogOpen(true)}
                    >
                      Cancelar Assinatura
                    </Button>
                  )}
                  
                  {/* Show reactivate button for cancelled subscriptions */}
                  {isCancelledOrExpired && (
                    <Button 
                      className="w-full sm:w-auto bg-green-600 hover:bg-green-700"
                      onClick={() => setUpgradePlanDialogOpen(true)}
                    >
                      Reativar Assinatura
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

      </Tabs>

      {/* Billing Dialogs */}
      <UpgradePlanDialog
        open={upgradePlanDialogOpen}
        onOpenChange={setUpgradePlanDialogOpen}
        currentPlan={undefined}
      />

      {/* Cancel Subscription Dialog */}
      <Dialog open={cancelSubscriptionDialogOpen} onOpenChange={setCancelSubscriptionDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="text-red-600">Cancelar Assinatura</DialogTitle>
            <DialogDescription>
              Você está prestes a cancelar sua assinatura. Esta ação não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="bg-yellow-500/10 border border-yellow-500/20 p-4 rounded-lg">
              <h4 className="font-medium text-yellow-800 mb-2">O que acontecerá:</h4>
              <ul className="text-sm text-yellow-700 space-y-1">
                <li>• Sua assinatura será cancelada imediatamente</li>
                <li>• Você perderá acesso aos recursos premium</li>
                <li>• Seus dados serão mantidos por 30 dias</li>
                <li>• Você pode reativar a qualquer momento</li>
              </ul>
            </div>
            <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
              <p className="text-sm text-red-800">
                <strong>Importante:</strong> Esta ação cancelará imediatamente sua assinatura e você perderá acesso 
                aos recursos premium. Você pode reativar sua assinatura a qualquer momento.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCancelSubscriptionDialogOpen(false)}
              disabled={cancelSubscriptionMutation.isPending}
            >
              Manter Assinatura
            </Button>
            <Button
              variant="destructive"
              onClick={() => cancelSubscriptionMutation.mutate()}
              disabled={cancelSubscriptionMutation.isPending}
            >
              {cancelSubscriptionMutation.isPending ? <LoadingSpinner /> : 'Confirmar Cancelamento'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Account Dialog */}
      <Dialog open={deleteAccountDialogOpen} onOpenChange={setDeleteAccountDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="text-red-600">Excluir Conta</DialogTitle>
            <DialogDescription>
              Esta ação excluirá permanentemente sua conta e todos os dados associados. Isso não pode ser desfeito.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={deleteAccountForm.handleSubmit(onDeleteAccountSubmit)} className="space-y-4 py-4">
            <div>
              <Label htmlFor="delete-password">Confirme sua senha</Label>
              <Input
                id="delete-password"
                type="password"
                placeholder="Digite sua senha"
                {...deleteAccountForm.register('password', { 
                  required: 'Senha é obrigatória para confirmar exclusão'
                })}
              />
              {deleteAccountForm.formState.errors.password && (
                <p className="text-sm text-red-500 mt-1">
                  {typeof deleteAccountForm.formState.errors.password.message === 'string' 
                    ? deleteAccountForm.formState.errors.password.message 
                    : 'Campo obrigatório'}
                </p>
              )}
            </div>
            <div>
              <Label htmlFor="delete-confirmation">
                Digite <strong>deletar</strong> para confirmar
              </Label>
              <Input
                id="delete-confirmation"
                type="text"
                placeholder="deletar"
                {...deleteAccountForm.register('confirmation', { 
                  required: 'Digite "deletar" para confirmar',
                  validate: value => value.toLowerCase() === 'deletar' || 'Digite "deletar" para confirmar'
                })}
              />
              {deleteAccountForm.formState.errors.confirmation && (
                <p className="text-sm text-red-500 mt-1">
                  {typeof deleteAccountForm.formState.errors.confirmation.message === 'string' 
                    ? deleteAccountForm.formState.errors.confirmation.message 
                    : 'Digite "deletar" para confirmar'}
                </p>
              )}
            </div>
            <div className="bg-red-500/10 border border-red-500/20 p-3 rounded-lg">
              <p className="text-sm text-red-800">
                ⚠️ <strong>Aviso:</strong> Isso excluirá permanentemente sua conta, dados da empresa, transações, categorias e todas as outras informações associadas. Esta ação não pode ser desfeita.
              </p>
            </div>
          </form>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setDeleteAccountDialogOpen(false);
                deleteAccountForm.reset();
              }}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={deleteAccountForm.handleSubmit(onDeleteAccountSubmit)}
              disabled={deleteAccountMutation.isPending}
            >
              {deleteAccountMutation.isPending ? <LoadingSpinner /> : 'Excluir Conta'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}