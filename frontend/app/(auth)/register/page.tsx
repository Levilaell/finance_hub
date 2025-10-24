'use client';

import { useState, Suspense, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuthStore } from '@/store/auth-store';
import { RegisterData } from '@/types';
import { EyeIcon, EyeSlashIcon, CheckIcon, CreditCardIcon } from '@heroicons/react/24/outline';
import { validatePhone, phoneMask } from '@/utils/validation';
import { trackLead, trackViewContent } from '@/lib/meta-pixel';

function RegisterContent() {
  const router = useRouter();
  const { register: registerUser, isLoading } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [phoneValue, setPhoneValue] = useState('');

  useEffect(() => {
    trackViewContent({
      content_name: 'Register Page',
      content_category: 'Registration',
    });
  }, []);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<RegisterData>();

  const password = watch('password');

  const onSubmit = async (data: RegisterData) => {
    try {
      await registerUser(data);

      // Track lead conversion
      trackLead({
        content_name: 'Registration Form',
        value: 0,
        currency: 'BRL'
      });

      toast.success('Cadastro realizado com sucesso!', {
        description: 'Seu trial de 7 dias começou. Aproveite!',
        duration: 5000,
      });

      router.push('/dashboard');
    } catch (error: any) {
      console.error('Erro no registro:', error.response?.data);

      // Handle validation errors
      if (error.response?.status === 400) {
        const errors = error.response.data;

        // Show first error from each field
        const errorMessages = Object.entries(errors)
          .filter(([key]) => key !== 'message')
          .map(([field, fieldErrors]: [string, any]) => {
            const fieldName = field === 'email' ? 'E-mail' :
                           field === 'password' ? 'Senha' :
                           field === 'phone' ? 'WhatsApp' :
                           field === 'first_name' ? 'Nome completo' : field;

            const errorText = Array.isArray(fieldErrors) ? fieldErrors[0] : fieldErrors;
            return `${fieldName}: ${errorText}`;
          })
          .join('\n');

        if (errorMessages) {
          toast.error(errorMessages);
        } else {
          toast.error(error.response.data.message || 'Erro na validação dos dados');
        }
      } else if (error.response?.status === 500) {
        toast.error('Erro no servidor. Tente novamente ou entre em contato com o suporte.');
      } else {
        toast.error(error.message || 'Falha no cadastro');
      }
    }
  };

  const passwordRequirements = [
    { regex: /.{8,}/, text: 'Pelo menos 8 caracteres' },
    { regex: /[A-Z]/, text: 'Uma letra maiúscula' },
    { regex: /[a-z]/, text: 'Uma letra minúscula' },
    { regex: /[0-9]/, text: 'Um número' },
    { regex: /[^A-Za-z0-9]/, text: 'Um caractere especial' },
  ];

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-white text-center text-2xl font-bold">Criar uma Conta</CardTitle>
        <CardDescription className="text-center text-muted-foreground">
          Inicie seu trial gratuito de 7 dias
        </CardDescription>

        {/* Trial Notice */}
        <Alert className="mt-4">
          <CreditCardIcon className="h-4 w-4" />
          <AlertDescription>
            <strong>7 dias de trial grátis:</strong> Teste todos os recursos sem compromisso.
            Nenhum cartão de crédito necessário para começar.
          </AlertDescription>
        </Alert>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="firstName">Nome completo</Label>
              <Input
                id="firstName"
                type="text"
                placeholder="João Silva"
                {...register('first_name', {
                  required: 'Nome completo é obrigatório',
                })}
                autoComplete="name"
              />
              {errors.first_name && (
                <p className="text-sm text-red-500 mt-1">
                  {errors.first_name.message}
                </p>
              )}
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="nome@exemplo.com"
                {...register('email', {
                  required: 'Email é obrigatório',
                  pattern: {
                    value: /\S+@\S+\.\S+/,
                    message: 'Endereço de email inválido',
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
              <Label htmlFor="phone">WhatsApp</Label>
              <Input
                id="phone"
                type="tel"
                placeholder="(11) 99999-9999"
                value={phoneValue}
                {...register('phone', {
                  required: 'WhatsApp é obrigatório',
                  validate: (value) => validatePhone(value) || 'WhatsApp inválido',
                })}
                onChange={(e) => {
                  const masked = phoneMask(e.target.value);
                  setPhoneValue(masked);
                  setValue('phone', masked);
                }}
                maxLength={15}
                autoComplete="tel"
              />
              {errors.phone && (
                <p className="text-sm text-red-500 mt-1">
                  {errors.phone.message}
                </p>
              )}
            </div>
            <div>
              <Label htmlFor="password">Senha</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Crie uma senha forte"
                  {...register('password', {
                    required: 'Senha é obrigatória',
                    validate: (value) => {
                      const failedRequirements = passwordRequirements.filter(
                        (req) => !req.regex.test(value)
                      );
                      if (failedRequirements.length > 0) {
                        return `A senha deve ter: ${failedRequirements
                          .map((req) => req.text.toLowerCase())
                          .join(', ')}`;
                      }
                      return true;
                    },
                  })}
                  autoComplete="new-password"
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
              {password && (
                <div className="mt-2 space-y-1">
                  {passwordRequirements.map((req, index) => (
                    <div
                      key={index}
                      className={`flex items-center text-sm ${
                        req.regex.test(password)
                          ? 'text-green-600'
                          : 'text-gray-400'
                      }`}
                    >
                      <CheckIcon
                        className={`h-4 w-4 mr-1 ${
                          req.regex.test(password) ? 'visible' : 'invisible'
                        }`}
                      />
                      {req.text}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <Button
            type="submit"
            className="w-full bg-white hover:bg-white/90 text-black font-medium"
            disabled={isLoading}
          >
            {isLoading ? (
              <LoadingSpinner />
            ) : (
              'Iniciar Teste de 7 Dias'
            )}
          </Button>
          <p className="text-sm text-center text-muted-foreground">
            Ao se cadastrar, você concorda com nossos{' '}
            <Link href="/terms" className="text-white hover:text-white/80 hover:underline transition-colors">
              Termos de Serviço
            </Link>{' '}
            e{' '}
            <Link href="/privacy" className="text-white hover:text-white/80 hover:underline transition-colors">
              Política de Privacidade
            </Link>
          </p>
          <p className="text-sm text-center text-muted-foreground">
            Já tem uma conta?{' '}
            <Link href="/login" className="text-white hover:text-white/80 hover:underline transition-colors font-medium">
              Entrar
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={
      <Card className="w-full max-w-md">
        <CardContent className="flex flex-col items-center space-y-4 pt-6">
          <LoadingSpinner />
          <p className="text-sm text-muted-foreground">Carregando...</p>
        </CardContent>
      </Card>
    }>
      <RegisterContent />
    </Suspense>
  );
}