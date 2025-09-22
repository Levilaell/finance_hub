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
  TrashIcon
} from '@heroicons/react/24/outline';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
        <h1 className="text-3xl font-bold">Configurações</h1>
        <p className="text-gray-600">Gerencie suas configurações de conta e preferências</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList className="grid w-full grid-cols-2 gap-1">
          <TabsTrigger value="profile" className="text-xs sm:text-sm">Perfil</TabsTrigger>
          <TabsTrigger value="security" className="text-xs sm:text-sm">Segurança</TabsTrigger>
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