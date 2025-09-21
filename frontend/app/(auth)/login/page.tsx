'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { useAuthStore } from '@/store/auth-store';
import type { LoginCredentials } from '@/types';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginCredentials>();

  const onSubmit = async (data: LoginCredentials) => {
    try {
      await login(data.email, data.password);
      toast.success('Login realizado com sucesso!');
      router.push('/dashboard');
    } catch (error: any) {
    console.error('Login error:', error.response?.data); // Debug
    
    let errorMessage = 'Credenciais inválidas';
    
    if (error.response?.status === 400) {
      // Erro de validação - extrair mensagem específica
      const data = error.response.data;
      
      if (typeof data === 'string') {
        errorMessage = data;
      } else if (data.detail) {
        errorMessage = data.detail;
      } else if (data.message) {
        errorMessage = data.message;
      } else if (data.error) {
        errorMessage = data.error;
      } else {
        // Se há erros de campo, mostrar o primeiro
        const fieldErrors = Object.values(data).flat();
        if (fieldErrors.length > 0) {
          errorMessage = fieldErrors[0] as string;
        }
      }
    } else if (error.response?.status === 401) {
      errorMessage = 'Email ou senha incorretos';
    } else if (error.response?.status === 500) {
      errorMessage = 'Erro no servidor. Tente novamente.';
    } else if (error.message === 'Network Error') {
      errorMessage = 'Erro de rede. Verifique sua conexão.';
    }
    
    toast.error(errorMessage);
  }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-white text-center text-2xl font-bold">Bem-vindo de Volta</CardTitle>
        <CardDescription className="text-center text-muted-foreground">
          Entre na sua conta para continuar
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
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
            disabled={isLoading}
          >
            {isLoading ? <LoadingSpinner /> : 'Entrar'}
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