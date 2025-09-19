'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { authService } from '@/services/auth.service';
import { useAuthStore } from '@/store/auth-store';
import type { LoginCredentials, LoginResponse } from '@/types';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [show2FA, setShow2FA] = useState(false);
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const [loginCredentials, setLoginCredentials] = useState<LoginCredentials | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginCredentials>();

  const loginMutation = useMutation<LoginResponse, Error, LoginCredentials>({
    mutationFn: async (data: LoginCredentials) => {
      return await authService.login(data);
    },
    onSuccess: (data) => {
      if (data.requires_2fa) {
        setShow2FA(true);
        toast.success('Por favor, insira seu código 2FA');
      } else {
        setAuth(data.user, data.tokens);
        toast.success('Login realizado com sucesso!');
        // Add a small delay to ensure cookies are set
        setTimeout(() => {
          router.push('/dashboard');
        }, 100);
      }
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          error.message || 
                          'Credenciais inválidas';
      toast.error(errorMessage);
    },
  });

  const verify2FAMutation = useMutation<LoginResponse, Error, void>({
    mutationFn: async () => {
      if (!loginCredentials) {
        throw new Error('No login credentials available');
      }
      return await authService.loginWith2FA(loginCredentials.email, loginCredentials.password, twoFactorCode);
    },
    onSuccess: (data) => {
      setAuth(data.user, data.tokens);
      toast.success('Login successful!');
      router.push('/dashboard');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || error.response?.data?.detail || 'Código 2FA inválido');
    },
  });

  const onSubmit = (data: LoginCredentials) => {
    setLoginCredentials(data); // Store credentials for 2FA
    loginMutation.mutate(data);
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSubmit(onSubmit)(e);
  };

  const handle2FASubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!twoFactorCode || twoFactorCode.length !== 6) {
      toast.error('Por favor, insira um código válido de 6 dígitos');
      return;
    }
    verify2FAMutation.mutate();
  };

  if (show2FA) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-white text-center text-xl font-bold">Autenticação de Dois Fatores</CardTitle>
          <CardDescription className="text-center text-muted-foreground">
            Insira o código de 6 dígitos do seu aplicativo autenticador
          </CardDescription>
        </CardHeader>
        <form onSubmit={handle2FASubmit}>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Label htmlFor="2fa-code">Código de Autenticação</Label>
                <Input
                  id="2fa-code"
                  type="text"
                  placeholder="000000"
                  maxLength={6}
                  value={twoFactorCode}
                  onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, ''))}
                  className="text-center text-2xl tracking-widest"
                  autoComplete="one-time-code"
                  autoFocus
                />
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button
              type="submit"
              className="w-full bg-white hover:bg-white/90 text-black font-medium"
              disabled={verify2FAMutation.isPending}
            >
              {verify2FAMutation.isPending ? (
                <LoadingSpinner />
              ) : (
                'Verificar Código'
              )}
            </Button>
            <Button
              type="button"
              variant="ghost"
              className="w-full text-muted-foreground hover:text-foreground"
              onClick={() => {
                setShow2FA(false);
                setTwoFactorCode('');
                setLoginCredentials(null);
              }}
            >
              Voltar ao Login
            </Button>
          </CardFooter>
        </form>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-white text-center text-2xl font-bold">Bem-vindo de Volta</CardTitle>
        <CardDescription className="text-center text-muted-foreground">
          Entre na sua conta para continuar
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleFormSubmit}>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="email">E-mail</Label>
              <Input
                id="email"
                type="email"
                placeholder="nome@exemplo.com"
                {...register('email', {
                  required: 'E-mail é obrigatório',
                  pattern: {
                    value: /\S+@\S+\.\S+/,
                    message: 'Endereço de e-mail inválido',
                  },
                })}
                autoComplete="email"
              />
              {errors.email && (
                <p className="text-sm text-red-500 mt-1">
                  {errors.email.message}
                </p>
              )}
            </div>
            <div>
              <Label htmlFor="password">Senha</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Digite sua senha"
                  {...register('password', {
                    required: 'Senha é obrigatória',
                    minLength: {
                      value: 8,
                      message: 'A senha deve ter pelo menos 8 caracteres',
                    },
                  })}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-5 w-5" />
                  ) : (
                    <EyeIcon className="h-5 w-5" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="text-sm text-red-500 mt-1">
                  {errors.password.message}
                </p>
              )}
            </div>
            <div className="flex items-center justify-between">
              <Link
                href="/forgot-password"
                className="text-sm text-white hover:text-white/80 hover:underline transition-colors"
              >
                Esqueceu a senha?
              </Link>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <Button
            type="submit"
            className="w-full hover-glow bg-primary hover:bg-primary/90 text-primary-foreground"
            disabled={loginMutation.isPending}
          >
            {loginMutation.isPending ? <LoadingSpinner /> : 'Entrar'}
          </Button>
          <p className="text-sm text-center text-muted-foreground">
            Não tem uma conta?{' '}
            <Link 
              href="/register" 
              className="text-white hover:text-white/80 hover:underline transition-colors font-medium"
            >
              Cadastre-se
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}