'use client';

import { useState, Suspense } from 'react';
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
import { validateCNPJ, validatePhone, cnpjMask, phoneMask } from '@/utils/validation';
import { trackLead } from '@/lib/meta-pixel';

interface RegisterFormData extends RegisterData {
  password2: string;
}

function RegisterContent() {
  const router = useRouter();
  const { register: registerUser, isLoading } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [cnpjValue, setCnpjValue] = useState('');
  const [phoneValue, setPhoneValue] = useState('');

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<RegisterFormData>();

  const password = watch('password');

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await registerUser(data);

      // Track lead conversion
      trackLead({
        content_name: 'Registration Form',
        value: 0,
        currency: 'BRL'
      });

      toast.success('Cadastro realizado com sucesso!', {
        description: 'Agora vamos configurar seu pagamento.',
        duration: 5000,
      });

      router.push('/checkout');
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
                           field === 'company_cnpj' ? 'CNPJ' :
                           field === 'phone' ? 'Telefone' :
                           field === 'first_name' ? 'Nome' :
                           field === 'last_name' ? 'Sobrenome' :
                           field === 'company_name' ? 'Empresa' :
                           field === 'company_type' ? 'Tipo de empresa' :
                           field === 'business_sector' ? 'Setor' : field;
            
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
            Após o cadastro, você adicionará um cartão de crédito para ativar o trial.
          </AlertDescription>
        </Alert>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="firstName">Nome</Label>
                <Input
                  id="firstName"
                  type="text"
                  placeholder="João"
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
            className="w-full bg-white hover:bg-white/90 text-black font-medium"
            disabled={isLoading}
          >
            {isLoading ? (
              <LoadingSpinner />
            ) : (
              'Criar Conta e Iniciar Trial'
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