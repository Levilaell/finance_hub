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
  EyeIcon,
  EyeSlashIcon,
  KeyIcon,
  TrashIcon,
  CreditCardIcon,
  CogIcon,
  LinkIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { SubscriptionManagement } from '@/components/subscription/SubscriptionManagement';
import { settingsService } from '@/services/settings.service';
import { bankingService } from '@/services/banking.service';
import { UserSettings, CategoryRule } from '@/types/banking';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

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
  
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [deleteAccountDialogOpen, setDeleteAccountDialogOpen] = useState(false);
  const [userSettings, setUserSettings] = useState<UserSettings | null>(null);
  const [isLoadingSettings, setIsLoadingSettings] = useState(true);
  const [isUpdatingSettings, setIsUpdatingSettings] = useState(false);

  // Category Rules state
  const [categoryRules, setCategoryRules] = useState<CategoryRule[]>([]);
  const [isLoadingRules, setIsLoadingRules] = useState(true);
  const [deletingRuleId, setDeletingRuleId] = useState<string | null>(null);
  const [togglingRuleId, setTogglingRuleId] = useState<string | null>(null);

  // Fetch user settings on mount
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const settings = await settingsService.getSettings();
        setUserSettings(settings);
      } catch (error) {
        console.error('Error fetching settings:', error);
      } finally {
        setIsLoadingSettings(false);
      }
    };
    fetchSettings();
  }, []);

  // Fetch category rules
  useEffect(() => {
    const fetchRules = async () => {
      try {
        const rules = await bankingService.getCategoryRules();
        setCategoryRules(rules);
      } catch (error) {
        console.error('Error fetching category rules:', error);
      } finally {
        setIsLoadingRules(false);
      }
    };
    fetchRules();
  }, []);

  const handleToggleRule = async (ruleId: string, isActive: boolean) => {
    setTogglingRuleId(ruleId);
    try {
      const updated = await bankingService.updateCategoryRule(ruleId, { is_active: isActive });
      setCategoryRules(prev =>
        prev.map(r => r.id === ruleId ? updated : r)
      );
      toast.success(isActive ? 'Regra ativada' : 'Regra desativada');
    } catch (error) {
      console.error('Error toggling rule:', error);
      toast.error('Erro ao atualizar regra');
    } finally {
      setTogglingRuleId(null);
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    setDeletingRuleId(ruleId);
    try {
      await bankingService.deleteCategoryRule(ruleId);
      setCategoryRules(prev => prev.filter(r => r.id !== ruleId));
      toast.success('Regra excluída');
    } catch (error) {
      console.error('Error deleting rule:', error);
      toast.error('Erro ao excluir regra');
    } finally {
      setDeletingRuleId(null);
    }
  };

  const getMatchTypeLabel = (matchType: string) => {
    switch (matchType) {
      case 'prefix': return 'Prefixo';
      case 'contains': return 'Contém';
      case 'fuzzy': return 'Similar';
      default: return matchType;
    }
  };

  const handleAutoMatchToggle = async (enabled: boolean) => {
    setIsUpdatingSettings(true);
    try {
      const updated = await settingsService.updateSettings({ auto_match_transactions: enabled });
      setUserSettings(updated);
      toast.success(enabled ? 'Vinculação automática ativada' : 'Vinculação automática desativada');
    } catch (error) {
      console.error('Error updating settings:', error);
      toast.error('Erro ao atualizar configuração');
    } finally {
      setIsUpdatingSettings(false);
    }
  };

  const profileForm = useForm<ProfileForm>({
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
    },
  });

  const passwordForm = useForm<PasswordForm>();
  const deleteAccountForm = useForm<DeleteAccountForm>();

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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Configurações</h1>
        <p className="text-muted-foreground">Gerencie suas configurações de conta e preferências</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4 gap-1">
          <TabsTrigger value="profile" className="text-xs sm:text-sm">Perfil</TabsTrigger>
          <TabsTrigger value="security" className="text-xs sm:text-sm">Segurança</TabsTrigger>
          <TabsTrigger value="automation" className="text-xs sm:text-sm">Automação</TabsTrigger>
          <TabsTrigger value="subscription" className="text-xs sm:text-sm">Assinatura</TabsTrigger>
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
                  <p className="text-xs text-muted-foreground mt-1">O email não pode ser alterado</p>
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
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
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
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
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
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
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
                <p className="text-sm text-muted-foreground">
                  Adicione uma camada extra de segurança à sua conta habilitando a autenticação de dois fatores.
                </p>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">
                      Autenticação de Dois Fatores
                    </p>
                    <p className="text-sm text-muted-foreground">
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
                  <p className="text-sm text-muted-foreground">
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

        {/* Automation Settings */}
        <TabsContent value="automation">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <CogIcon className="h-5 w-5 mr-2" />
                Configurações de Automação
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoadingSettings ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner />
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Auto-match transactions */}
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <LinkIcon className="h-5 w-5 text-muted-foreground" />
                        <Label className="text-base font-medium">
                          Vinculação Automática de Transações
                        </Label>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Quando ativado, novas transações do extrato bancário serão automaticamente
                        vinculadas a contas a pagar/receber com o mesmo valor. A vinculação só
                        ocorre quando há uma única conta compatível.
                      </p>
                    </div>
                    <Switch
                      checked={userSettings?.auto_match_transactions ?? true}
                      onCheckedChange={handleAutoMatchToggle}
                      disabled={isUpdatingSettings}
                    />
                  </div>

                  <div className="border-t border-white/10 pt-4">
                    <p className="text-sm text-muted-foreground">
                      <strong>Dica:</strong> Quando uma transação é vinculada a uma conta,
                      a conta é automaticamente marcada como paga. Você pode desvincular
                      manualmente a qualquer momento nas páginas de Contas ou Transações.
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Category Rules Section */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="flex items-center">
                <SparklesIcon className="h-5 w-5 mr-2" />
                Regras de Categorização Automática
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                As regras de categorização aplicam automaticamente categorias a novas transações
                com base em padrões definidos. Você pode criar regras ao categorizar uma transação
                manualmente na página de Transações.
              </p>

              {isLoadingRules ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner />
                </div>
              ) : categoryRules.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground border rounded-lg border-dashed">
                  <SparklesIcon className="h-10 w-10 mx-auto mb-2 opacity-50" />
                  <p>Nenhuma regra de categorização criada.</p>
                  <p className="text-sm mt-1">
                    Categorize uma transação manualmente para criar sua primeira regra.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {categoryRules.map((rule) => (
                    <div
                      key={rule.id}
                      className={`
                        flex items-center justify-between p-4 rounded-lg border transition-colors
                        ${rule.is_active
                          ? 'bg-background border-border'
                          : 'bg-muted/30 border-muted opacity-60'
                        }
                      `}
                    >
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        <div
                          className="w-8 h-8 rounded flex items-center justify-center text-sm flex-shrink-0"
                          style={{ backgroundColor: rule.category_color }}
                        >
                          {rule.category_icon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium">{rule.category_name}</span>
                            <span className="text-xs bg-muted px-2 py-0.5 rounded">
                              {getMatchTypeLabel(rule.match_type)}
                            </span>
                          </div>
                          <div className="text-sm text-muted-foreground truncate">
                            Padrão: <code className="bg-muted px-1 rounded">{rule.pattern}</code>
                          </div>
                          {rule.applied_count > 0 && (
                            <div className="text-xs text-muted-foreground mt-1">
                              Aplicada {rule.applied_count}x
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-3 flex-shrink-0">
                        <Switch
                          checked={rule.is_active}
                          onCheckedChange={(checked) => handleToggleRule(rule.id, checked)}
                          disabled={togglingRuleId === rule.id || deletingRuleId === rule.id}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteRule(rule.id)}
                          disabled={deletingRuleId === rule.id}
                          className="text-red-500 hover:text-red-600 hover:bg-red-500/10"
                        >
                          {deletingRuleId === rule.id ? (
                            <LoadingSpinner className="w-4 h-4" />
                          ) : (
                            <TrashIcon className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Subscription Settings */}
        <TabsContent value="subscription">
          <SubscriptionManagement />
        </TabsContent>
      </Tabs>

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
              <p className="text-sm text-red-400">
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