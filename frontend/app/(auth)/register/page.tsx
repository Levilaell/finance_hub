'use client';

import { useState, Suspense, useEffect } from 'react';
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
import { RegisterData } from '@/types';
import { EyeIcon, EyeSlashIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';
import { CheckIcon } from 'lucide-react';
import { validatePhone, phoneMask } from '@/utils/validation';
import { trackLead, trackViewContent, trackCompleteRegistration } from '@/lib/tracking';
import { AuthHeader } from '@/components/landing-v2/AuthHeader';
import { Footer } from '@/components/landing-v2/Footer';
import { startStripeCheckout, getPriceIdFromUrl } from '@/utils/checkout';
import { getAcquisitionAngle, clearAcquisitionAngle } from '@/hooks/use-acquisition-tracking';

function RegisterContent() {
  const router = useRouter();
  const { register: registerUser, isLoading } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [phoneValue, setPhoneValue] = useState('');
  const [priceId, setPriceId] = useState<string | null>(null);

  useEffect(() => {
    trackViewContent({
      content_name: 'Register Page',
      content_category: 'Registration',
    });

    // Captura price_id da URL para teste A/B de preços
    const urlPriceId = getPriceIdFromUrl();
    if (urlPriceId) {
      setPriceId(urlPriceId);
      // Armazena em sessionStorage para usar no checkout
      sessionStorage.setItem('checkout_price_id', urlPriceId);
    }
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
      // Recupera o ângulo de aquisição do localStorage
      const acquisitionAngle = getAcquisitionAngle();

      // Inclui price_id e acquisition_angle nos dados de registro para salvar no perfil
      const registerData = {
        ...data,
        price_id: priceId || sessionStorage.getItem('checkout_price_id') || undefined,
        acquisition_angle: acquisitionAngle || undefined,
      };
      await registerUser(registerData);

      // Limpa o acquisition_angle após registro bem-sucedido
      clearAcquisitionAngle();

      trackLead({
        content_name: 'Registration Form',
        value: 0,
        currency: 'BRL'
      });

      // Evento de cadastro completo
      trackCompleteRegistration({ status: 'success' });

      toast.success('Cadastro realizado com sucesso!', {
        description: 'Redirecionando para checkout...',
        duration: 3000,
      });

      // Redirecionar direto para o checkout da Stripe
      // Usa price_id da URL (teste A/B) ou sessionStorage se disponível
      const checkoutPriceId = priceId || sessionStorage.getItem('checkout_price_id') || undefined;
      await startStripeCheckout({
        priceId: checkoutPriceId,
        onError: () => {
          // Em caso de erro no checkout, redireciona para dashboard
          router.push('/dashboard');
        }
      });
    } catch (error: any) {
      console.error('Erro no registro:', error.response?.data);

      if (error.response?.status === 400) {
        const errors = error.response.data;

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
    <div className="min-h-screen bg-background flex flex-col">
      <AuthHeader />

      <main className="container mx-auto px-4 pt-24 pb-20 flex-1">
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

        <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 max-w-6xl mx-auto">
          {/* Coluna Esquerda - Reforço de Valor */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="lg:pr-8 flex flex-col justify-center"
          >
            <div className="bg-muted/30 rounded-2xl p-8 lg:p-10 border border-border/50">
              <h2 className="text-3xl lg:text-4xl font-bold mb-8">
                Falta pouco para organizar seu financeiro
              </h2>



              <div className="inline-flex items-center gap-2 px-4 py-3 bg-primary/10 rounded-full">
                <p className="text-sm font-semibold">
                  7 dias grátis. Cancele quando quiser.
                </p>
              </div>
            </div>
          </motion.div>

          {/* Coluna Direita - Formulário */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <Card className="p-8 lg:p-10">
              <div className="mb-8">
                <h1 className="text-3xl lg:text-4xl font-bold mb-3">
                  Criar uma Conta
                </h1>
                <p className="text-muted-foreground text-lg mb-4">
                  Inicie seu teste gratuito de 7 dias
                </p>
              </div>

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                <div className="space-y-2">
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

                <div className="space-y-2">
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

                <div className="space-y-2">
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

                <div className="space-y-2">
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

                <Button
                  type="submit"
                  size="lg"
                  className="w-full bg-primary hover:bg-primary/90 text-primary-foreground text-lg py-6"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <LoadingSpinner />
                  ) : (
                    'Começar Agora - É Grátis'
                  )}
                </Button>

                <p className="text-center text-xs text-muted-foreground pt-2">
                  Ao se cadastrar, você concorda com nossos{' '}
                  <Link href="/terms" className="text-primary hover:underline">
                    Termos de Serviço
                  </Link>{' '}
                  e{' '}
                  <Link href="/privacy" className="text-primary hover:underline">
                    Política de Privacidade
                  </Link>
                </p>

                <div className="text-center pt-4 border-t border-border">
                  <p className="text-muted-foreground text-sm">
                    Já tem uma conta?{' '}
                    <Link href="/login" className="text-primary hover:underline font-medium">
                      Entrar
                    </Link>
                  </p>
                </div>
              </form>
            </Card>
          </motion.div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md p-8">
          <div className="flex flex-col items-center space-y-4">
            <LoadingSpinner />
            <p className="text-sm text-muted-foreground">Carregando...</p>
          </div>
        </Card>
      </div>
    }>
      <RegisterContent />
    </Suspense>
  );
}
