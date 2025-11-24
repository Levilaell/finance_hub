'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { useAuthStore } from '@/store/auth-store';
import type { LoginCredentials } from '@/types';
import { EyeIcon, EyeSlashIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';
import { AuthHeader } from '@/components/landing-v2/AuthHeader';
import { Footer } from '@/components/landing-v2/Footer';

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
    console.error('Login error:', error.response?.data);

    let errorMessage = 'Credenciais inválidas';

    if (error.response?.status === 400) {
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
    <div className="min-h-screen bg-background">
      <AuthHeader />

      <main className="container mx-auto px-4 pt-32 pb-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-2xl mx-auto"
        >
          <Button
            variant="ghost"
            asChild
            className="mb-8"
          >
            <Link href="/" className="flex items-center gap-2">
              <ArrowLeftIcon className="w-4 h-4" />
              Voltar
            </Link>
          </Button>

          <Card className="p-8 lg:p-12">
            <div className="text-center mb-8">
              <h1 className="text-3xl lg:text-4xl font-bold mb-4">
                Entrar na sua Conta
              </h1>
              <p className="text-muted-foreground text-lg">
                Acesse o CaixaHub e organize seu caixa
              </p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
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

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Senha</Label>
                  <Link
                    href="/forgot-password"
                    className="text-sm text-primary hover:underline"
                  >
                    Esqueceu a senha?
                  </Link>
                </div>
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

              <Button
                type="submit"
                size="lg"
                className="w-full bg-primary hover:bg-primary/90 text-primary-foreground text-lg py-6"
                disabled={isLoading}
              >
                {isLoading ? <LoadingSpinner /> : 'Entrar'}
              </Button>

              <div className="text-center pt-4 border-t border-border">
                <p className="text-muted-foreground">
                  Não tem uma conta?{' '}
                  <Link
                    href="/register"
                    className="text-primary hover:underline font-medium"
                  >
                    Criar conta grátis
                  </Link>
                </p>
              </div>
            </form>
          </Card>

          <div className="mt-8 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full">
              <p className="text-sm font-medium">
                7 dias grátis • Cancele quando quiser
              </p>
            </div>
          </div>
        </motion.div>
      </main>

      <Footer />
    </div>
  );
}
