'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { authService } from '@/services/auth.service';
import { ArrowLeftIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { AuthHeader } from '@/components/landing-v2/AuthHeader';
import { Footer } from '@/components/landing-v2/Footer';

interface ForgotPasswordForm {
  email: string;
}

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [emailSent, setEmailSent] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordForm>();

  const forgotPasswordMutation = useMutation({
    mutationFn: async (data: ForgotPasswordForm) => {
      await authService.requestPasswordReset(data.email);
    },
    onSuccess: () => {
      setEmailSent(true);
      toast.success('E-mail de redefinição de senha enviado!');
    },
    onError: (error: any) => {
      toast.error(
        error.response?.data?.detail || 'Falha ao enviar e-mail de redefinição'
      );
    },
  });

  const onSubmit = (data: ForgotPasswordForm) => {
    forgotPasswordMutation.mutate(data);
  };

  if (emailSent) {
    return (
      <div className="min-h-screen bg-background">
        <AuthHeader />

        <main className="container mx-auto px-4 pt-24 pb-20">
          <Button
            variant="ghost"
            asChild
            className="mb-8"
          >
            <Link href="/login" className="flex items-center gap-2">
              <ArrowLeftIcon className="w-4 h-4" />
              Voltar
            </Link>
          </Button>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="max-w-md mx-auto"
          >
            <Card className="p-8 lg:p-10">
              <div className="flex justify-center mb-6">
                <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircleIcon className="h-10 w-10 text-green-600" />
                </div>
              </div>

              <h1 className="text-2xl lg:text-3xl font-bold text-center mb-3">
                Verifique seu E-mail
              </h1>
              <p className="text-center text-muted-foreground mb-6">
                Enviamos um link de redefinição de senha. Verifique seu e-mail e
                siga as instruções para redefinir sua senha.
              </p>

              <div className="space-y-4 mb-6">
                <p className="text-sm text-center text-muted-foreground">
                  O link expirará em 2 horas por questões de segurança.
                </p>
                <p className="text-sm text-center text-muted-foreground">
                  Não recebeu o e-mail? Verifique sua pasta de spam ou{' '}
                  <button
                    onClick={() => setEmailSent(false)}
                    className="text-primary hover:underline transition-colors font-medium"
                  >
                    tente novamente
                  </button>
                  .
                </p>
              </div>

              <Button
                variant="outline"
                className="w-full"
                asChild
              >
                <Link href="/login">
                  <ArrowLeftIcon className="h-4 w-4 mr-2" />
                  Voltar ao Login
                </Link>
              </Button>
            </Card>
          </motion.div>
        </main>

        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <AuthHeader />

      <main className="container mx-auto px-4 pt-24 pb-20">
        <Button
          variant="ghost"
          asChild
          className="mb-8"
        >
          <Link href="/login" className="flex items-center gap-2">
            <ArrowLeftIcon className="w-4 h-4" />
            Voltar
          </Link>
        </Button>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-md mx-auto"
        >
          <Card className="p-8 lg:p-10">
            <div className="mb-8">
              <h1 className="text-2xl lg:text-3xl font-bold text-center mb-3">
                Redefinir sua Senha
              </h1>
              <p className="text-center text-muted-foreground">
                Digite seu endereço de e-mail e enviaremos um link para redefinir sua
                senha.
              </p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="email">Endereço de E-mail</Label>
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
                  autoFocus
                />
                {errors.email && (
                  <p className="text-sm text-red-500 mt-1">
                    {errors.email.message}
                  </p>
                )}
              </div>

              <Button
                type="submit"
                size="lg"
                className="w-full bg-primary hover:bg-primary/90 text-primary-foreground text-lg py-6"
                disabled={forgotPasswordMutation.isPending}
              >
                {forgotPasswordMutation.isPending ? (
                  <LoadingSpinner />
                ) : (
                  'Enviar Link de Redefinição'
                )}
              </Button>

              <div className="text-center pt-4 border-t border-border">
                <p className="text-muted-foreground text-sm">
                  Lembrou sua senha?{' '}
                  <Link href="/login" className="text-primary hover:underline font-medium">
                    Voltar ao Login
                  </Link>
                </p>
              </div>
            </form>
          </Card>
        </motion.div>
      </main>

      <Footer />
    </div>
  );
}
