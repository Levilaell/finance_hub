'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { authService } from '@/services/auth.service';
import { useAuthStore } from '@/store/auth-store';
import { RegisterData } from '@/types';
import { EyeIcon, EyeSlashIcon, CheckIcon, SparklesIcon, GiftIcon } from '@heroicons/react/24/outline';
import { validateCNPJ, validatePhone, cnpjMask, phoneMask } from '@/utils/validation';
import { testId, TEST_IDS } from '@/utils/test-helpers';

interface EarlyAccessFormData extends RegisterData {
  invite_code: string;
}

function EarlyAccessContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth, user } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [inviteCode, setInviteCode] = useState('');
  const [cnpjValue, setCnpjValue] = useState('');
  const [phoneValue, setPhoneValue] = useState('');

  useEffect(() => {
    // Get invite code from URL parameter
    const code = searchParams.get('code');
    if (code) {
      setInviteCode(code);
    }
    
    // If user is already authenticated, redirect to dashboard
    if (user) {
      router.push('/dashboard');
    }
  }, [searchParams, user, router]);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<EarlyAccessFormData>();

  const password = watch('password');

  // Early access registration mutation
  const registerMutation = useMutation({
    mutationFn: async (data: EarlyAccessFormData) => {
      const response = await fetch('/api/auth/early-access/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Falha no registro');
      }

      return response.json();
    },
    onSuccess: async (data) => {
      setAuth(data.user, data.tokens);
      
      // Show success message with early access info
      toast.success('Acesso Antecipado Ativado!', {
        description: `Você tem acesso completo até ${new Date(data.early_access.expires_at).toLocaleDateString('pt-BR')}. Verifique seu e-mail para confirmar sua conta.`,
        duration: 7000,
      });
      
      router.push('/dashboard');
    },
    onError: (error: any) => {
      console.error('Erro no registro early access:', error);
      toast.error(error.message || 'Falha no registro');
    },
  });

  const onSubmit = (data: EarlyAccessFormData) => {
    registerMutation.mutate({
      ...data,
      invite_code: inviteCode,
    });
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
        <div className="text-center">
          <div className="flex items-center justify-center mb-2">
            <SparklesIcon className="h-8 w-8 text-purple-500 mr-2" />
            <CardTitle className="text-white text-2xl font-bold">
              Acesso Antecipado
            </CardTitle>
          </div>
          <CardDescription className="text-center text-muted-foreground">
            Você foi convidado para testar nosso MVP gratuitamente
          </CardDescription>
        </div>
        
        {/* Early Access Special Banner */}
        <div className="mt-4 p-4 bg-gradient-to-r from-purple-600/20 to-blue-600/20 rounded-lg border border-purple-500/30">
          <div className="flex items-center justify-center mb-2">
            <Badge className="bg-gradient-to-r from-purple-600 to-blue-600 text-white border-none">
              🚀 MVP Early Access
            </Badge>
          </div>
          <p className="text-sm text-center text-muted-foreground">
            <strong className="text-white">Acesso gratuito por tempo limitado</strong><br/>
            Teste todas as funcionalidades sem restrições
          </p>
        </div>

        {/* Benefits */}
        <Alert className="mt-4 border-green-500/30 bg-green-500/10">
          <GiftIcon className="h-4 w-4 text-green-400" />
          <AlertDescription className="text-green-200">
            <strong>Benefícios exclusivos:</strong> Suporte prioritário, feedback direto com o time, 
            e desconto especial quando lançarmos oficialmente.
          </AlertDescription>
        </Alert>
      </CardHeader>
      
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent>
          <div className="space-y-4">
            {/* Invite Code Field */}
            <div>
              <Label htmlFor="invite_code" className="text-purple-200">
                Código de Convite <span className="text-red-400">*</span>
              </Label>
              <Input
                id="invite_code"
                type="text"
                placeholder="MVP-XXXXXXXX"
                value={inviteCode}
                className="font-mono bg-purple-900/20 border-purple-500/30"
                {...register('invite_code', {
                  required: 'Código de convite é obrigatório',
                  pattern: {
                    value: /^[A-Z0-9-]+$/,
                    message: 'Código de convite inválido'
                  }
                })}
                onChange={(e) => {
                  const code = e.target.value.toUpperCase();
                  setInviteCode(code);
                  setValue('invite_code', code);
                }}
              />
              {errors.invite_code && (
                <p className="text-sm text-red-500 mt-1">
                  {errors.invite_code.message}
                </p>
              )}
            </div>

            {/* Personal Information */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="firstName">Nome</Label>
                <Input
                  id="firstName"
                  type="text"
                  placeholder="João"
                  {...testId(TEST_IDS.auth.firstNameInput)}
                  {...register('first_name', {
                    required: 'Nome é obrigatório',
                  })}
                  autoComplete="given-name"
                />
                {errors.first_name && (
                  <p className="text-sm text-red-500 mt-1">
                    {errors.first_name.message}
                  </p>
                )}
              </div>
              <div>
                <Label htmlFor="lastName">Sobrenome</Label>
                <Input
                  id="lastName"
                  type="text"
                  placeholder="Silva"
                  {...testId(TEST_IDS.auth.lastNameInput)}
                  {...register('last_name', {
                    required: 'Sobrenome é obrigatório',
                  })}
                  autoComplete="family-name"
                />
                {errors.last_name && (
                  <p className="text-sm text-red-500 mt-1">
                    {errors.last_name.message}
                  </p>
                )}
              </div>
            </div>

            <div>
              <Label htmlFor="email">E-mail</Label>
              <Input
                id="email"
                type="email"
                placeholder="nome@exemplo.com"
                {...testId(TEST_IDS.auth.emailInput)}
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
              <Label htmlFor="companyName">Nome da Empresa</Label>
              <Input
                id="companyName"
                type="text"
                placeholder="Minha Empresa Ltda"
                {...testId(TEST_IDS.auth.companyNameInput)}
                {...register('company_name', {
                  required: 'Nome da empresa é obrigatório',
                })}
                autoComplete="organization"
              />
              {errors.company_name && (
                <p className="text-sm text-red-500 mt-1">
                  {errors.company_name.message}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="companyCnpj">CNPJ</Label>
                <Input
                  id="companyCnpj"
                  type="text"
                  placeholder="00.000.000/0000-00"
                  value={cnpjValue}
                  {...testId(TEST_IDS.auth.companyCnpjInput)}
                  {...register('company_cnpj', {
                    required: 'CNPJ é obrigatório',
                    validate: (value) => validateCNPJ(value) || 'CNPJ inválido',
                  })}
                  onChange={(e) => {
                    const masked = cnpjMask(e.target.value);
                    setCnpjValue(masked);
                    setValue('company_cnpj', masked);
                  }}
                  maxLength={18}
                />
                {errors.company_cnpj && (
                  <p className="text-sm text-red-500 mt-1">
                    {errors.company_cnpj.message}
                  </p>
                )}
              </div>
              <div>
                <Label htmlFor="phone">Telefone</Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="(11) 99999-9999"
                  value={phoneValue}
                  {...testId(TEST_IDS.auth.phoneInput)}
                  {...register('phone', {
                    required: 'Telefone é obrigatório',
                    validate: (value) => validatePhone(value) || 'Telefone inválido',
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
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="companyType">Tipo de Empresa</Label>
                <select
                  id="companyType"
                  {...testId(TEST_IDS.auth.companyTypeSelect)}
                  {...register('company_type', {
                    required: 'Tipo de empresa é obrigatório',
                  })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">Selecione o tipo</option>
                  <option value="mei">MEI</option>
                  <option value="me">Microempresa</option>
                  <option value="epp">Empresa de Pequeno Porte</option>
                  <option value="ltda">Limitada</option>
                  <option value="sa">Sociedade Anônima</option>
                  <option value="other">Outros</option>
                </select>
                {errors.company_type && (
                  <p className="text-sm text-red-500 mt-1">
                    {errors.company_type.message}
                  </p>
                )}
              </div>
              <div>
                <Label htmlFor="businessSector">Setor de Atividade</Label>
                <select
                  id="businessSector"
                  {...testId(TEST_IDS.auth.businessSectorInput)}
                  {...register('business_sector', {
                    required: 'Setor de atividade é obrigatório',
                  })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">Selecione o setor</option>
                  <option value="retail">Comércio</option>
                  <option value="services">Serviços</option>
                  <option value="industry">Indústria</option>
                  <option value="technology">Tecnologia</option>
                  <option value="healthcare">Saúde</option>
                  <option value="education">Educação</option>
                  <option value="food">Alimentação</option>
                  <option value="construction">Construção</option>
                  <option value="automotive">Automotivo</option>
                  <option value="agriculture">Agricultura</option>
                  <option value="other">Outros</option>
                </select>
                {errors.business_sector && (
                  <p className="text-sm text-red-500 mt-1">
                    {errors.business_sector.message}
                  </p>
                )}
              </div>
            </div>

            <div>
              <Label htmlFor="password">Senha</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Crie uma senha forte"
                  {...testId(TEST_IDS.auth.passwordInput)}
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

            <div>
              <Label htmlFor="password2">Confirmar Senha</Label>
              <div className="relative">
                <Input
                  id="password2"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Confirme sua senha"
                  {...testId(TEST_IDS.auth.password2Input)}
                  {...register('password2', {
                    required: 'Por favor, confirme sua senha',
                    validate: (value) =>
                      value === password || 'As senhas não coincidem',
                  })}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showConfirmPassword ? (
                    <EyeSlashIcon className="h-5 w-5" />
                  ) : (
                    <EyeIcon className="h-5 w-5" />
                  )}
                </button>
              </div>
              {errors.password2 && (
                <p className="text-sm text-red-500 mt-1">
                  {errors.password2.message}
                </p>
              )}
            </div>
          </div>
        </CardContent>
        
        <CardFooter className="flex flex-col space-y-4">
          <Button
            type="submit"
            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium"
            disabled={registerMutation.isPending}
            {...testId(TEST_IDS.auth.registerSubmit)}
          >
            {registerMutation.isPending ? (
              <LoadingSpinner />
            ) : (
              <>
                <SparklesIcon className="h-4 w-4 mr-2" />
                Ativar Acesso Antecipado
              </>
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

export default function EarlyAccessPage() {
  return (
    <Suspense fallback={
      <Card className="w-full max-w-md">
        <CardContent className="flex flex-col items-center space-y-4 pt-6">
          <LoadingSpinner />
          <p className="text-sm text-muted-foreground">Carregando...</p>
        </CardContent>
      </Card>
    }>
      <EarlyAccessContent />
    </Suspense>
  );
}