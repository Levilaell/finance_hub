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
import { ArrowLeftIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

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
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex justify-center mb-4">
            <CheckCircleIcon className="h-16 w-16 text-green-500" />
          </div>
          <CardTitle className="text-white text-center text-xl font-bold">Verifique seu E-mail</CardTitle>
          <CardDescription className="text-center text-muted-foreground">
            Enviamos um link de redefinição de senha. Verifique seu e-mail e
            siga as instruções para redefinir sua senha.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-sm text-center text-muted-foreground">
              O link expirará em 2 horas por questões de segurança.
            </p>
            <p className="text-sm text-center text-muted-foreground">
              Não recebeu o e-mail? Verifique sua pasta de spam ou{' '}
              <button
                onClick={() => setEmailSent(false)}
                className="text-white hover:text-white/80 hover:underline transition-colors font-medium"
              >
                tente novamente
              </button>
              .
            </p>
          </div>
        </CardContent>
        <CardFooter>
          <Link href="/login" className="w-full">
            <Button variant="outline" className="w-full hover:bg-muted/50 transition-colors">
              <ArrowLeftIcon className="h-4 w-4 mr-2" />
              Voltar ao Login
            </Button>
          </Link>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-white text-center text-2xl font-bold">Redefinir sua Senha</CardTitle>
        <CardDescription className="text-center text-muted-foreground">
          Digite seu endereço de e-mail e enviaremos um link para redefinir sua
          senha.
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent>
          <div className="space-y-4">
            <div>
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
          </div>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <Button
            type="submit"
            className="w-full bg-white hover:bg-white/90 text-black font-medium"
            disabled={forgotPasswordMutation.isPending}
          >
            {forgotPasswordMutation.isPending ? (
              <LoadingSpinner />
            ) : (
              'Enviar Link de Redefinição'
            )}
          </Button>
          <Link href="/login" className="w-full">
            <Button variant="ghost" className="w-full">
              <ArrowLeftIcon className="h-4 w-4 mr-2" />
              Voltar ao Login
            </Button>
          </Link>
        </CardFooter>
      </form>
    </Card>
  );
}