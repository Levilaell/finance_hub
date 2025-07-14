'use client';

import { useState } from 'react';
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
  const { user, updateUser } = useAuthStore();
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

  const profileForm = useForm<ProfileForm>({
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      email: user?.email || '',
    },
  });

  const passwordForm = useForm<PasswordForm>();
  const deleteAccountForm = useForm<DeleteAccountForm>();

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
  const showUpgradePrompt = shouldShowUpgradePrompt(user?.company?.subscription_status || 'trialing', trialInfo);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Configurações</h1>
        <p className="text-gray-600">Gerencie suas configurações de conta e preferências</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="profile">Perfil</TabsTrigger>
          <TabsTrigger value="security">Segurança</TabsTrigger>
          <TabsTrigger value="billing">Faturamento</TabsTrigger>
          <TabsTrigger value="notifications">Notificações (Em Breve)</TabsTrigger>
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
                            ? `${formatCurrency(user.company.subscription_plan.price_monthly)}/mês`
                            : 'Sem cobrança durante o período de teste'
                          }
                        </p>
                      </div>
                      <div className="text-right">
                        <span className={`px-2 py-1 text-xs rounded-full ${subscriptionStatusInfo.color}`}>
                          {subscriptionStatusInfo.label}
                        </span>
                        <p className="text-xs text-gray-500 mt-1">
                          {subscriptionStatusInfo.description}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Trial Information */}
                {trialInfo.isActive && (
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
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Limite de Contas Bancárias</p>
                      <p className="font-medium">
                        {user?.company?.subscription_plan?.max_bank_accounts || 'Ilimitado'}
                      </p>
                    </div>

                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Limite de Usuários</p>
                      <p className="font-medium">
                        {user?.company?.subscription_plan?.max_users || 'Ilimitado'}
                      </p>
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
                          Até {user.company.subscription_plan.max_transactions} transações/mês
                        </li>
                        <li className="flex items-center text-sm text-gray-700">
                          <svg className="h-4 w-4 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          {user.company.subscription_plan.max_bank_accounts} contas bancárias
                        </li>
                        <li className="flex items-center text-sm text-gray-700">
                          <svg className="h-4 w-4 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          {user.company.subscription_plan.max_users} usuários
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
                  <Button 
                    className="w-full sm:w-auto"
                    onClick={() => setUpgradePlanDialogOpen(true)}
                  >
                    Fazer Upgrade
                  </Button>
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
                <img src={qrCode} alt="2FA QR Code" className="w-48 h-48" />
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