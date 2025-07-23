'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
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
import { RulesList } from '@/components/rules/rules-list';
import { RuleDialog } from '@/components/rules/rule-dialog';
import { CreateRuleRequest, rulesService } from '@/services/rules.service';
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
import { BillingHistoryDialog } from '@/components/billing/billing-history-dialog';
import { PaymentMethodsDialog } from '@/components/billing/payment-methods-dialog';
import { UsageLimitsCard } from '@/components/billing/usage-limits';
import { useSubscriptionCheck } from '@/hooks/use-subscription-check';
import { subscriptionService } from '@/services/subscription.service';
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
  email: string;
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
  const [is2FADialogOpen, setIs2FADialogOpen] = useState(false);
  const [qrCode, setQrCode] = useState<string>('');
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const [backupCodesDialogOpen, setBackupCodesDialogOpen] = useState(false);
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [deleteAccountDialogOpen, setDeleteAccountDialogOpen] = useState(false);
  
  // AI & Rules settings state
  const [aiEnabled, setAiEnabled] = useState(true);
  const [autoApplyHighConfidence, setAutoApplyHighConfidence] = useState(true);
  const [learningEnabled, setLearningEnabled] = useState(true);
  const [createRuleDialogOpen, setCreateRuleDialogOpen] = useState(false);
  
  // Notification settings state
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [transactionAlerts, setTransactionAlerts] = useState(true);
  const [lowBalanceWarnings, setLowBalanceWarnings] = useState(true);
  const [monthlyReports, setMonthlyReports] = useState(true);

  // Billing dialogs state
  const [upgradePlanDialogOpen, setUpgradePlanDialogOpen] = useState(false);
  const [billingHistoryDialogOpen, setBillingHistoryDialogOpen] = useState(false);
  const [paymentMethodsDialogOpen, setPaymentMethodsDialogOpen] = useState(false);
  const [cancelSubscriptionDialogOpen, setCancelSubscriptionDialogOpen] = useState(false);

  const profileForm = useForm<ProfileForm>({
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      email: user?.email || '',
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
      toast.success('Profile updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    },
  });

  const changePasswordMutation = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      authService.changePassword(data),
    onSuccess: () => {
      passwordForm.reset();
      toast.success('Password changed successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to change password');
    },
  });

  const setup2FAMutation = useMutation({
    mutationFn: () => authService.setup2FA(),
    onSuccess: (data) => {
      setQrCode(data.qr_code);
      setIs2FADialogOpen(true);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to setup 2FA');
    },
  });

  const enable2FAMutation = useMutation({
    mutationFn: (token: string) => authService.enable2FA(token),
    onSuccess: (data) => {
      // Update user in store immediately
      updateUser({ is_two_factor_enabled: true });
      
      // Invalidate queries to refresh from server
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      
      setIs2FADialogOpen(false);
      setTwoFactorCode('');
      toast.success('Two-factor authentication enabled successfully');
      
      // Show backup codes dialog
      if (data.backup_codes) {
        setBackupCodes(data.backup_codes);
        setBackupCodesDialogOpen(true);
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Invalid verification code');
    },
  });

  const disable2FAMutation = useMutation({
    mutationFn: (password: string) => authService.disable2FA({ password }),
    onSuccess: () => {
      // Update user in store immediately
      updateUser({ is_two_factor_enabled: false });
      
      // Invalidate queries to refresh from server
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      
      toast.success('Two-factor authentication disabled');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to disable 2FA');
    },
  });

  const createRuleMutation = useMutation({
    mutationFn: rulesService.createRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] });
      toast.success('Rule created successfully');
      setCreateRuleDialogOpen(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create rule');
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
      toast.error(error.response?.data?.error || 'Falha ao deletar conta');
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
      toast.error('Passwords do not match');
      return;
    }
    changePasswordMutation.mutate({
      current_password: data.current_password,
      new_password: data.new_password,
    });
  };

  const handleCreateRule = async (data: CreateRuleRequest) => {
    await createRuleMutation.mutateAsync(data);
  };

  const onDeleteAccountSubmit = (data: DeleteAccountForm) => {
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
  
  // Don't show trial info if user has active paid subscription
  const isActiveSubscription = user?.company?.subscription_status === 'active' && 
                              user?.company?.subscription_plan?.price_monthly && 
                              Number(user?.company?.subscription_plan?.price_monthly) > 0;
  
  const showTrialInfo = !isActiveSubscription && trialInfo.isActive;
  const showUpgradePrompt = !isActiveSubscription && shouldShowUpgradePrompt(user?.company?.subscription_status || 'trialing', trialInfo);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Configurações</h1>
        <p className="text-gray-600">Gerencie suas configurações de conta e preferências</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList className="grid w-full grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-1">
          <TabsTrigger value="profile" className="text-xs sm:text-sm">Perfil</TabsTrigger>
          <TabsTrigger value="security" className="text-xs sm:text-sm">Segurança</TabsTrigger>
          <TabsTrigger value="status" className="text-xs sm:text-sm col-span-2 sm:col-span-1">Status & Limites</TabsTrigger>
          <TabsTrigger value="billing" className="text-xs sm:text-sm">Faturamento</TabsTrigger>
          <TabsTrigger value="notifications" className="text-xs sm:text-sm col-span-2 sm:col-span-1 lg:col-span-1">Notificações (Em Breve)</TabsTrigger>
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
                    {...profileForm.register('email', { required: true })}
                  />
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
                      {...passwordForm.register('current_password', { required: true })}
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
                </div>
                <div>
                  <Label htmlFor="new_password">Nova Senha</Label>
                  <div className="relative">
                    <Input
                      id="new_password"
                      type={showNewPassword ? 'text' : 'password'}
                      {...passwordForm.register('new_password', {
                        required: true,
                        minLength: 8,
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
                </div>
                <div>
                  <Label htmlFor="confirm_password">Confirmar Nova Senha</Label>
                  <div className="relative">
                    <Input
                      id="confirm_password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      {...passwordForm.register('confirm_password', { required: true })}
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
                      A Autenticação de Dois Fatores está {user?.is_two_factor_enabled ? 'habilitada' : 'desabilitada'}
                    </p>
                    <p className="text-sm text-gray-600">
                      {user?.is_two_factor_enabled
                        ? 'Sua conta está protegida com 2FA'
                        : 'Enable 2FA to secure your account'}
                    </p>
                  </div>
                  {user?.is_two_factor_enabled ? (
                    <Button
                      variant="outline"
                      onClick={() => {
                        const password = prompt('Enter your password to disable 2FA:');
                        if (password) {
                          disable2FAMutation.mutate(password);
                        }
                      }}
                      disabled={disable2FAMutation.isPending}
                    >
                      Desabilitar 2FA
                    </Button>
                  ) : (
                    <Button
                      onClick={() => setup2FAMutation.mutate()}
                      disabled={setup2FAMutation.isPending}
                    >
                      {setup2FAMutation.isPending ? <LoadingSpinner /> : 'Enable 2FA'}
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI & Categorization Rules */}
        <TabsContent value="ai" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                </svg>
                AI Categorization Settings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h3 className="font-medium mb-4">Categorização Automática</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Habilitar Categorização por IA</p>
                        <p className="text-sm text-gray-600">
                          Categorizar transações automaticamente usando IA
                        </p>
                      </div>
                      <Switch 
                        checked={aiEnabled}
                        onCheckedChange={setAiEnabled}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Aplicar automaticamente sugestões de alta confiança</p>
                        <p className="text-sm text-gray-600">
                          Aplicar categorias automaticamente quando a confiança da IA estiver acima de 90%
                        </p>
                      </div>
                      <Switch 
                        checked={autoApplyHighConfidence}
                        onCheckedChange={setAutoApplyHighConfidence}
                        disabled={!aiEnabled}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Aprender com correções</p>
                        <p className="text-sm text-gray-600">
                          Melhorar a precisão da IA aprendendo com correções manuais
                        </p>
                      </div>
                      <Switch 
                        checked={learningEnabled}
                        onCheckedChange={setLearningEnabled}
                        disabled={!aiEnabled}
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="font-medium mb-4">Métricas de Desempenho</h3>
                  {isLoadingMetrics ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="bg-gray-50 p-4 rounded-lg animate-pulse">
                          <div className="h-4 bg-gray-300 rounded mb-2"></div>
                          <div className="h-8 bg-gray-300 rounded"></div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-sm text-gray-600">Precisão</p>
                        <p className="text-2xl font-bold text-green-600">
                          {performanceMetrics?.overall_accuracy 
                            ? `${(performanceMetrics.overall_accuracy * 100).toFixed(1)}%` 
                            : '0%'
                          }
                        </p>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-sm text-gray-600">Auto-categorizadas</p>
                        <p className="text-2xl font-bold text-blue-600">
                          {performanceMetrics?.auto_categorized?.toLocaleString() || '0'}
                        </p>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-sm text-gray-600">Revisões manuais</p>
                        <p className="text-2xl font-bold text-orange-600">
                          {performanceMetrics?.manual_reviews?.toLocaleString() || '0'}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                <div>
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="font-medium">Regras Personalizadas</h3>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setCreateRuleDialogOpen(true)}
                    >
                      Adicionar Regra
                    </Button>
                  </div>
                  <RulesList onCreateRule={() => setCreateRuleDialogOpen(true)} />
                </div>

                <div className="pt-4">
                  <Button
                    onClick={() => {
                      toast.success('AI settings saved successfully');
                    }}
                  >
                    Salvar Configurações de IA
                  </Button>
                </div>
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
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
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

                  {/* Trial Info - only show if not active subscription */}
                  {subscriptionStatus.subscription_status === 'trial' && (
                    <div className="p-4 bg-blue-50 rounded-lg">
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

                  {/* Payment Method Status */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
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
                    {subscriptionStatus.next_billing_date && (
                      <div className="text-right">
                        <p className="text-sm text-gray-600">Próxima cobrança</p>
                        <p className="text-sm font-medium">
                          {new Date(subscriptionStatus.next_billing_date).toLocaleDateString('pt-BR')}
                        </p>
                      </div>
                    )}
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
                      ? 'bg-orange-50 border-orange-200' 
                      : 'bg-blue-50 border-blue-200'
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
                  <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
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
                  <div className="bg-green-50 border border-green-200 p-4 rounded-lg mb-6">
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

                {/* Billing Information */}
                <div>
                  <h3 className="font-medium mb-3">Informações de Cobrança</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Next Billing Date */}
                    {billingInfo.nextBillingDate && (
                      <div className="bg-gray-50 p-4 rounded-lg">
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
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-sm text-gray-600">Assinatura Iniciada</p>
                        <p className="font-medium">
                          {formatDate(billingInfo.subscriptionStartDate)}
                        </p>
                      </div>
                    )}

                    {/* Plan Limits */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-sm text-gray-600">Limite de Transações</p>
                        <p className="font-medium">
                          {!user?.company?.subscription_plan?.max_transactions || 
                           user?.company?.subscription_plan?.max_transactions >= 100000 
                            ? 'Ilimitado' 
                            : `${user?.company?.subscription_plan?.max_transactions?.toLocaleString()}/mês`}
                        </p>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-sm text-gray-600">Limite de Contas Bancárias</p>
                        <p className="font-medium">
                          {!user?.company?.subscription_plan?.max_bank_accounts ||
                           user?.company?.subscription_plan?.max_bank_accounts >= 100 
                            ? 'Ilimitado' 
                            : user?.company?.subscription_plan?.max_bank_accounts}
                        </p>
                      </div>
                      {user?.company?.subscription_plan?.enable_ai_insights && (
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <p className="text-sm text-gray-600">Limite de IA</p>
                          <p className="font-medium">
                            {!user?.company?.subscription_plan?.max_ai_requests_per_month ||
                             user?.company?.subscription_plan?.max_ai_requests_per_month >= 100000 
                              ? 'Ilimitado' 
                              : `${user?.company?.subscription_plan?.max_ai_requests_per_month}/mês`}
                          </p>
                        </div>
                      )}
                    </div>


                  </div>
                </div>

                {/* Plan Features */}
                {user?.company?.subscription_plan && (
                  <div>
                    <h3 className="font-medium mb-3">Recursos do Plano</h3>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <ul className="space-y-2">
                        <li className="flex items-center text-sm text-gray-700">
                          <svg className="h-4 w-4 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          {!user.company.subscription_plan.max_transactions || 
                           user.company.subscription_plan.max_transactions >= 100000
                            ? 'Transações ilimitadas'
                            : `Até ${user.company.subscription_plan.max_transactions.toLocaleString()} transações/mês`}
                        </li>
                        <li className="flex items-center text-sm text-gray-700">
                          <svg className="h-4 w-4 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          {!user.company.subscription_plan.max_bank_accounts ||
                           user.company.subscription_plan.max_bank_accounts >= 100
                            ? 'Contas bancárias ilimitadas'
                            : `${user.company.subscription_plan.max_bank_accounts} contas bancárias`}
                        </li>

                        {user.company.subscription_plan.has_ai_categorization && (
                          <li className="flex items-center text-sm text-gray-700">
                            <svg className="h-4 w-4 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Categorização automática com IA
                          </li>
                        )}
                        {user.company.subscription_plan.has_advanced_reports && (
                          <li className="flex items-center text-sm text-gray-700">
                            <svg className="h-4 w-4 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Relatórios avançados
                          </li>
                        )}
                        {user.company.subscription_plan.has_api_access && (
                          <li className="flex items-center text-sm text-gray-700">
                            <svg className="h-4 w-4 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Acesso à API
                          </li>
                        )}
                        {user.company.subscription_plan.has_accountant_access && (
                          <li className="flex items-center text-sm text-gray-700">
                            <svg className="h-4 w-4 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Acesso para contador
                          </li>
                        )}
                      </ul>
                    </div>
                  </div>
                )}

                {/* Upgrade Prompt */}
                {showUpgradePrompt && (
                  <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-blue-900">Hora de fazer upgrade!</p>
                        <p className="text-sm text-blue-700">
                          Seu período de teste {trialInfo.isExpired ? 'expirou' : 'está expirando'}. 
                          Escolha um plano para continuar aproveitando todos os recursos.
                        </p>
                      </div>
                      <Button 
                        size="sm"
                        onClick={() => setUpgradePlanDialogOpen(true)}
                      >
                        Fazer Upgrade
                      </Button>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-2">
                  {/* Only show upgrade button if not on enterprise plan */}
                  {user?.company?.subscription_plan?.plan_type !== 'enterprise' && (
                    <Button 
                      className="w-full sm:w-auto"
                      onClick={() => setUpgradePlanDialogOpen(true)}
                    >
                      Fazer Upgrade
                    </Button>
                  )}
                  <Button 
                    variant="outline" 
                    className="w-full sm:w-auto"
                    onClick={() => setBillingHistoryDialogOpen(true)}
                  >
                    Histórico de Cobrança
                  </Button>
                  <Button 
                    variant="outline" 
                    className="w-full sm:w-auto"
                    onClick={() => setPaymentMethodsDialogOpen(true)}
                  >
                    Gerenciar Pagamentos
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
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notification Settings */}
        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <BellIcon className="h-5 w-5 mr-2" />
                Preferências de Notificação
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Notificações por E-mail</p>
                      <p className="text-sm text-gray-600">
                        Receba atualizações por e-mail sobre a atividade da sua conta
                      </p>
                    </div>
                    <Switch 
                      checked={emailNotifications}
                      onCheckedChange={setEmailNotifications}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Alertas de Transação</p>
                      <p className="text-sm text-gray-600">
                        Seja notificado sobre novas transações
                      </p>
                    </div>
                    <Switch 
                      checked={transactionAlerts}
                      onCheckedChange={setTransactionAlerts}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Avisos de Saldo Baixo</p>
                      <p className="text-sm text-gray-600">
                        Alerte quando o saldo da conta estiver baixo
                      </p>
                    </div>
                    <Switch 
                      checked={lowBalanceWarnings}
                      onCheckedChange={setLowBalanceWarnings}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Relatórios Mensais</p>
                      <p className="text-sm text-gray-600">
                        Receba resumos financeiros mensais
                      </p>
                    </div>
                    <Switch 
                      checked={monthlyReports}
                      onCheckedChange={setMonthlyReports}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Alertas de Segurança</p>
                      <p className="text-sm text-gray-600">
                        Notificações importantes de segurança e conta
                      </p>
                    </div>
                    <Switch defaultChecked disabled />
                  </div>
                </div>

                <div className="pt-4">
                  <Button
                    onClick={() => {
                      toast.success('Notification preferences saved successfully');
                    }}
                  >
                    Salvar Preferências
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
      </Tabs>

      {/* 2FA Setup Dialog */}
      <Dialog open={is2FADialogOpen} onOpenChange={setIs2FADialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Enable Two-Factor Authentication</DialogTitle>
            <DialogDescription>
              Scan the QR code with your authenticator app and enter the verification code
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {qrCode && (
              <div className="flex justify-center">
                <Image src={qrCode} alt="2FA QR Code" width={192} height={192} />
              </div>
            )}
            <div>
              <Label htmlFor="2fa-code">Verification Code</Label>
              <Input
                id="2fa-code"
                type="text"
                placeholder="000000"
                maxLength={6}
                value={twoFactorCode}
                onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, ''))}
                className="text-center text-2xl tracking-widest"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIs2FADialogOpen(false);
                setTwoFactorCode('');
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={() => enable2FAMutation.mutate(twoFactorCode)}
              disabled={enable2FAMutation.isPending || twoFactorCode.length !== 6}
            >
              {enable2FAMutation.isPending ? <LoadingSpinner /> : 'Verify & Enable'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Backup Codes Dialog */}
      <Dialog open={backupCodesDialogOpen} onOpenChange={setBackupCodesDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Your Backup Codes</DialogTitle>
            <DialogDescription>
              Save these backup codes in a safe place. Each code can only be used once to access your account if you lose your authenticator device.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="grid grid-cols-2 gap-2 font-mono text-sm">
                {backupCodes.map((code, index) => (
                  <div key={index} className="p-2 bg-white rounded border text-center">
                    {code}
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-lg">
              <p className="text-sm text-yellow-800">
                ⚠️ <strong>Important:</strong> These codes will not be shown again. Save them now!
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              onClick={() => {
                navigator.clipboard.writeText(backupCodes.join('\n'));
                toast.success('Backup codes copied to clipboard');
              }}
              variant="outline"
            >
              Copy Codes
            </Button>
            <Button
              onClick={() => {
                setBackupCodesDialogOpen(false);
                setBackupCodes([]);
              }}
            >
              I&apos;ve Saved My Codes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Rule Dialog */}
      <RuleDialog
        open={createRuleDialogOpen}
        onOpenChange={setCreateRuleDialogOpen}
        onSave={handleCreateRule}
      />

      {/* Billing Dialogs */}
      <UpgradePlanDialog
        open={upgradePlanDialogOpen}
        onOpenChange={setUpgradePlanDialogOpen}
        currentPlan={user?.company?.subscription_plan}
      />

      <BillingHistoryDialog
        open={billingHistoryDialogOpen}
        onOpenChange={setBillingHistoryDialogOpen}
      />

      <PaymentMethodsDialog
        open={paymentMethodsDialogOpen}
        onOpenChange={setPaymentMethodsDialogOpen}
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
            <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
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
              This action will permanently delete your account and all associated data. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={deleteAccountForm.handleSubmit(onDeleteAccountSubmit)} className="space-y-4 py-4">
            <div>
              <Label htmlFor="delete-password">Confirm your password</Label>
              <Input
                id="delete-password"
                type="password"
                placeholder="Enter your password"
                {...deleteAccountForm.register('password', { required: true })}
              />
            </div>
            <div>
              <Label htmlFor="delete-confirmation">
                Type <strong>deletar</strong> to confirm
              </Label>
              <Input
                id="delete-confirmation"
                type="text"
                placeholder="deletar"
                {...deleteAccountForm.register('confirmation', { required: true })}
              />
            </div>
            <div className="bg-red-50 border border-red-200 p-3 rounded-lg">
              <p className="text-sm text-red-800">
                ⚠️ <strong>Warning:</strong> This will permanently delete your account, company data, transactions, categories, and all other associated information. This action cannot be undone.
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
              Cancel
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